from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from core.system_wide_completion_20260618 import (
    DETAIL_TABLES_KEY,
    MANIFEST_KEY,
    METRIC_KEY,
    READY_KEY,
    publish_system_wide_completion,
    readiness_message,
)

ROOT = Path(__file__).resolve().parents[1]
PROTECTED_FULL_METRIC_SHA256 = "fe0797ab30f469f3ea748bc66a690b18a68aaf91306ac33c797bdcdcf6e60682"


def _canonical() -> dict:
    return {
        "run_id": "RUN-ONE-CLICK",
        "calculation_generation": 11,
        "data_signature": "sig-11",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "source": "TEST",
        "latest_completed_candle_time": "2026-06-18T09:00:00+00:00",
        "regime": {"major_regime": "BULL_NORMAL", "alpha": 1.2, "delta": 0.3},
    }


def test_one_click_publication_aliases_every_workspace_to_one_generation():
    state: dict = {}
    canonical = _canonical()
    adapter = {
        "run_id": canonical["run_id"],
        "calculation_generation": canonical["calculation_generation"],
        "ai_grounding": {"decision": "BUY"},
    }
    priority = pd.DataFrame([
        {"Time": "2026-06-18T09:00:00Z", "Regime": "BULL_NORMAL", "Priority Rank": 1},
        {"Time": "2026-06-18T08:00:00Z", "Regime": "BULL_NORMAL", "Priority Rank": 2},
    ])
    history = priority.assign(**{"Master /10": [7.2, 6.8]})
    metric = {"ok": True, "history": history, "scores": {"Decision": "BUY"}}
    details = {
        "Lower Standard — 1 Day": priority.head(1),
        "Medium Standard — 5 Days": priority,
        "Higher Standard — 25 Days": priority,
    }
    articles = pd.DataFrame([{"timestamp": "2026-06-18T08:00:00Z", "title": "ECB update"}])
    nlp = {"articles": articles, "news_mining": {"daily_summary": pd.DataFrame([{"day": "2026-06-18", "count": 1}])}}
    research = {
        "all_inner_tabs_ready": True,
        "data_analysis": {"ok": True, "diagnostic_table": pd.DataFrame([{"metric": "x"}])},
        "data_mining": {"ok": True, "knn_priority": priority},
        "nlp": nlp,
    }

    manifest = publish_system_wide_completion(
        state,
        canonical=canonical,
        adapter=adapter,
        priority_table=priority,
        metric_result=metric,
        regime_detail_tables=details,
        nlp_result=nlp,
        research_pack=research,
        powerbi_status={"ok": True, "predicted_rows": 6},
    )

    assert manifest["ready"] is True
    assert state[READY_KEY] is True
    assert state[MANIFEST_KEY]["calculation_generation"] == 11
    assert state[METRIC_KEY] is metric
    assert state["lunch_metric_result_cache"] is metric
    assert state["full_metric_result_cache_20260618"] is metric
    assert state["canonical_priority_table_20260617"] is priority
    assert state["finder_readonly_priority_table_20260618"] is priority
    assert state["lunch_quick_decision_merged_table_20260617"] is priority
    assert state[DETAIL_TABLES_KEY] is details
    assert state["nlp_market_intelligence_result"] is nlp
    assert state["research_pack_20260612"] is research
    assert not state["full_metric_regime_history_df"].empty
    assert state["metric_run_calculate"] is True
    assert state["research_run_calculate"] is True
    assert state["other_run_calculate"] is True


def test_completed_partial_generation_never_tells_user_to_run_again():
    state = {
        "settings_run_complete_20260617": True,
        MANIFEST_KEY: {
            "calculation_generation": 3,
            "Full Metric": {"ready": False, "detail": "metric builder error"},
        },
    }
    message = readiness_message(state, "Full Metric")
    assert "Run Calculation" not in message
    assert "Errors / Fix Fast" in message
    assert "metric builder error" in message


def test_active_routes_have_one_settings_owner_and_no_second_load_gate():
    router = (ROOT / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
    menu = (ROOT / "ui" / "main_menu_drawer.py").read_text(encoding="utf-8")
    popup = (ROOT / "ui" / "liquid_menu_popup_20260615.py").read_text(encoding="utf-8")
    research = (ROOT / "tabs" / "research.py").read_text(encoding="utf-8")
    nlp = (ROOT / "ui" / "nlp_research_panel.py").read_text(encoding="utf-8")
    center = (ROOT / "tabs" / "final_three_center_upgrade_20260614.py").read_text(encoding="utf-8")

    assert "run_settings_calculation" in router
    assert "run_settings_calculation" in menu
    assert "run_settings_calculation" in popup
    assert "▶ Load Full Original Projection" not in router
    assert "Build / Refresh Research Pack" not in research
    assert "Optional NLP manual refresh / model tools" in nlp
    assert "Settings is the only calculation owner" in center
    assert 'st.button("▶ Run Calculation"' not in center
    assert 'st.button("⏸ Stop"' not in center


def test_api_secret_inputs_are_not_rendered_in_drawer_or_nlp():
    drawer = (ROOT / "ui" / "main_menu_drawer.py").read_text(encoding="utf-8")
    nlp = (ROOT / "ui" / "nlp_research_panel.py").read_text(encoding="utf-8")
    fallback = (ROOT / "ui" / "sidebar_fallback_panel.py").read_text(encoding="utf-8")
    popup = (ROOT / "ui" / "liquid_menu_popup_20260615.py").read_text(encoding="utf-8")
    assert "_render_connector_status_only" in drawer
    assert 'text_input("Finnhub API key"' not in nlp
    assert "API keys are entered once in Settings only" in fallback
    assert "render_finnhub_status_compact" in popup


def test_copy_short_and_mobile_low_heat_contracts():
    copy_source = (ROOT / "ui" / "home_master_control_bar_20260615.py").read_text(encoding="utf-8")
    mobile = (ROOT / "ui" / "mobile_css.py").read_text(encoding="utf-8")
    low_heat = (ROOT / "ui" / "mobile_low_heat_20260617.py").read_text(encoding="utf-8")
    popup = (ROOT / "ui" / "liquid_menu_popup_20260615.py").read_text(encoding="utf-8")
    assert "4000" in copy_source
    assert "next_1_hour_tp_context" in copy_source and "next_6_hour_tp_context" in copy_source
    assert "less_risky_6h_bias" in copy_source
    assert "overflow:visible" in mobile.replace(" ", "")
    assert "backdrop-filter: none !important" in low_heat
    assert "clamp(124px,10vw,148px)" in popup.replace(" ", "")


def test_ai_1000_question_focus_and_protected_formula_file():
    ai = (ROOT / "tabs" / "ai_assistant_lite.py").read_text(encoding="utf-8")
    dinner_ai = (ROOT / "tabs" / "dinner_morning_data_patch_20260614.py").read_text(encoding="utf-8")
    protected = ROOT / "tabs" / "eurusd_h1_matrix.py"
    assert "1000" in ai
    assert "apply_prepared_question_focus_20260618" in ai
    assert "prepared_item" in ai
    assert "apply_prepared_question_focus_20260618" in dinner_ai
    assert hashlib.sha256(protected.read_bytes()).hexdigest() == PROTECTED_FULL_METRIC_SHA256
