from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.connector_state_machine_20260621 import (
    CONNECTED, CONNECTING, DISCONNECTED, ERROR, begin, disconnect, fail, snapshot, succeed,
)
from core.lunch_search_20260621 import remember_search, search_cached_lunch

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def search_state():
    return {
        "canonical_decision_result": {
            "run_id": "R-SEARCH",
            "calculation_generation": 4,
            "regime": {"major_regime": "BEAR_NORMAL", "reliability": 39},
            "final_decision": {"final_decision": "WAIT", "less_risky_decision": "WAIT"},
            "risk": {"exit_risk": 7.8},
            "forecasts": {"models": {"XGBoost": {"disagreement": 63}}},
            "warning": "Wrong prediction occurred in the prior settled row",
        }
    }


def test_lunch_search_examples_rank_cached_results():
    state = search_state()
    for query in ("last BEAR_NORMAL", "exit risk above 7", "wrong prediction", "low reliability", "XGBoost disagreement"):
        result = search_cached_lunch(query, state)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty, query
        assert {"Score", "Source", "Field / Path", "Value"} <= set(result.columns)


def test_search_does_not_import_or_call_heavy_calculator():
    search_code = source("core/lunch_search_20260621.py")
    ui_code = source("ui/lunch_search_20260621.py")
    forbidden = ("run_settings_calculation", "build_similar_day_intelligence", "heavy_calculation", "manual_connect")
    assert all(token not in search_code for token in forbidden)
    assert all(token not in ui_code for token in forbidden)
    assert "st.form(" in ui_code and "st.form_submit_button" in ui_code


def test_recent_search_history_is_small_and_bounded():
    state = {}
    for i in range(20):
        remember_search(state, f"query {i}")
    assert len(state["lunch_recent_searches_20260621"]) == 8
    assert state["lunch_recent_searches_20260621"][0] == "query 19"


def test_successful_run_navigation_opens_lunch_and_ai_without_second_calculation():
    router = source("tabs/antd_page_router_20260615.py")
    success = router.split("def _open_lunch_ai_after_settings_run", 1)[1].split("def _render_settings", 1)[0]
    assert '"active_page": "Lunch"' in success
    assert '"lunch_field_open_1_20260621": True' in success
    assert '"lunch_field_open_5_20260621": True' in success
    assert '"lunch_scroll_to_field5_20260622": True' in success
    assert '"lunch_calculation_completed_notice_20260621": True' in success
    assert "run_settings_calculation" not in success


def test_tab_switch_open_close_and_search_are_calculation_free():
    for path in (
        "ui/lunch_four_core_fields_20260619.py",
        "ui/lunch_search_20260621.py",
        "ui/regime_transition_trust_center_20260621.py",
        "tabs/dinner_unified_center_20260617.py",
    ):
        code = source(path)
        assert "run_settings_calculation" not in code
        assert "build_regime_transition_trust(" not in code


def test_connector_state_machine_is_explicit_idempotent_and_persistent():
    state = {}
    assert snapshot(state, "x")["state"] == DISCONNECTED
    assert begin(state, "x") is True
    assert snapshot(state, "x")["state"] == CONNECTING
    assert begin(state, "x") is False
    succeed(state, "x", "done")
    assert snapshot(state, "x")["state"] == CONNECTED
    fail(state, "x", "bad")
    assert snapshot(state, "x")["state"] == ERROR
    disconnect(state, "x")
    assert snapshot(state, "x")["state"] == DISCONNECTED


def test_all_live_connector_buttons_use_callbacks_and_one_click_labels():
    sidebar = source("ui/sidebar_fallback_panel.py")
    finnhub = source("core/finnhub_connector.py")
    router = source("tabs/antd_page_router_20260615.py")
    assert "on_click=_market_connect_callback" in sidebar
    assert "Connect Once Using Saved Settings" in sidebar and "Refresh Connected Feed" in sidebar
    assert "on_click=_connect_button_callback" in finnhub
    assert "Save + Validate + Connect (One Click)" in finnhub
    assert "Test & Connect" not in finnhub
    assert "Save Key + Auto-Connect (One Click)" in router
    assert "on_click=_save_and_connect_twelve_callback" in router


def test_api_keys_are_redacted_and_not_part_of_history_or_search_results():
    search_code = source("core/lunch_search_20260621.py")
    finnhub = source("core/finnhub_connector.py")
    store = source("core/regime_trust_store_20260621.py").lower()
    assert '"api_key"' in search_code and "_redacted_path" in search_code
    assert "_redact(" in finnhub
    assert "_SENSITIVE" in search_code and "secret" in search_code.lower()
    assert "api_key varchar" not in store and "secret varchar" not in store


def test_lunch_has_exactly_six_principal_fields_and_field4_views():
    lunch = source("ui/lunch_four_core_fields_20260619.py")
    body = lunch.split("def render_lunch_six_core_fields", 1)[1].split("def render_lunch_four_core_fields", 1)[0]
    assert body.count("if _gate(") == 6
    assert 'CURRENT_FIELD = "4. Open / Close — Dinner Full Combined Intelligence"' in lunch
    for view in ("Regime Summary + Combined Logic", "Power BI Regime Projection", "Original Data + Advanced Details", "Priority, Decision + Reliability", "KNN + Greedy", "Similar-Day and Pattern Intelligence", "All Current Data"):
        assert view in lunch
    similar = source("ui/similar_day_renderer_20260619.py")
    markers = ["#### 1. Similar-Day Intelligence Summary", "#### 2. Summary Cards", "#### 3. Top-Five Similar Results", "#### 4. Complete Descending 25-Day History Table", "#### 5. Similarity Explanation and Reliability Warning"]
    assert [similar.index(marker) for marker in markers] == sorted(similar.index(marker) for marker in markers)

def test_mobile_primary_controls_have_no_forced_horizontal_layout():
    search_ui = source("ui/lunch_search_20260621.py")
    lunch = source("ui/lunch_four_core_fields_20260619.py")
    assert "use_container_width=True" in search_ui
    body = lunch.split("def render_lunch_six_core_fields", 1)[1]
    assert 'horizontal=not bool(state.get("phone_mode"' not in body
    assert "Phone mode: keep only one large field open" in body

