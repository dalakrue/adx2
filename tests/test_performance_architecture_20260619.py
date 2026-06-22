from __future__ import annotations

import ast
import hashlib
import json
import sys
import tempfile
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

from core.compact_canonical_20260619 import (
    BOUNDED_CACHE_KEY,
    FACT_PACK_KEY,
    MAX_GENERATIONS,
    SUMMARY_KEY,
    build_ai_fact_pack,
    build_compact_summary,
    calculation_id,
    publish_compact_runtime,
)
from core.performance_store_20260619 import (
    compact_adapter_frames,
    export_frame,
    frame_manifest,
    persist_frame,
    query_frame,
    session_dataframe_audit,
    spool_history_frames,
)


def canonical(generation: int = 1, candle: str = "2026-06-19T10:00:00+00:00") -> dict:
    return {
        "run_id": f"RUN-{generation}", "canonical_calculation_id": f"CID-{generation}",
        "calculation_generation": generation, "data_signature": f"SIG-{generation}",
        "symbol": "EURUSD", "timeframe": "H1", "source": "TEST",
        "created_at": "2026-06-19T10:01:00+00:00", "latest_completed_candle_time": candle,
        "last_close": 1.1542, "calculation_status": "COMPLETED",
        "master_score": 6.2, "entry_score": 6.8, "hold_safety": 5.9,
        "tp_quality": 6.1, "exit_risk": 3.4, "trend_capacity_remaining": 6.0,
        "final_decision": {"final_decision": "BUY", "directional_market_view": "BUY", "less_risky_decision": "BUY", "tradeability_decision": "BUY", "selected_horizon": 3, "calibrated_confidence": .73, "main_reason": "test"},
        "regime": {"major_regime": "BULL_NORMAL", "alpha": 1.2, "delta": .3},
        "multiscale_regime": {"current_volatility_regime": "NORMAL", "multi_scale_transition_risk_pct": 22},
        "reliability": {"score": 72, "status": "VALID", "sample_count": 120},
        "risk": {"risk_level": "MEDIUM"},
        "forecasts": {"selected_horizon": 3, "horizons": {
            "1h": {"point_forecast": 1.1545, "lower_bound": 1.1538, "upper_bound": 1.1552, "reliability": .75},
            "3h": {"point_forecast": 1.1550, "lower_bound": 1.1535, "upper_bound": 1.1565, "reliability": .73},
            "6h": {"point_forecast": 1.1560, "lower_bound": 1.1528, "upper_bound": 1.1580, "reliability": .70},
        }},
        "nlp": {"direction": "BUY", "reliability": 65, "conflict_level": "NONE", "latest_headline": "ECB test", "importance": "MEDIUM"},
        "research_calibration": {"uncertainty": {"aleatoric_uncertainty_0_100": 20, "epistemic_uncertainty_0_100": 15, "combined_uncertainty_0_100": 25}, "validation_status": "VALID"},
        "data_quality": {"status": "PASS", "score": 98, "freshness": "FRESH"},
        "top_two_daily_candidates": [{"Hour": "10:00", "Priority Rank 1-14": 2}, {"Hour": "12:00", "Priority Rank 1-14": 3}],
    }


def shared() -> dict:
    table = pd.DataFrame({"Time": pd.date_range("2026-01-01", periods=200, freq="h"), "KNN Priority": range(200)})
    return {"priority": {"table": table, "best": table.iloc[0].to_dict()}, "hourly_priority_table": table, "powerbi": {"summary": {"path_agreement_pct": 81}}}


def test_01_same_input_deterministic_output():
    assert build_compact_summary(canonical(), shared()) == build_compact_summary(canonical(), shared())


def test_02_lunch_dinner_canonical_sync_source():
    lunch = (ROOT / "tabs/final_lunch_upgrade_20260617.py").read_text()
    dinner = (ROOT / "tabs/dinner_unified_center_20260617.py").read_text()
    assert "get_compact_summary" in lunch and "get_compact_summary" in dinner
    assert "render_eight_cards" in lunch and "render_eight_cards" in dinner


def test_03_tab_navigation_no_recalculation():
    router = (ROOT / "tabs/antd_page_router_20260615.py").read_text()
    show = router.split("def show", 1)[1]
    assert "ensure_shared_calculation_result" not in show
    assert '_render_lunch({}, subpage)' in show and '_render_dinner({}, subpage)' in show


def test_04_dinner_opening_no_heavy_calculation():
    dinner = (ROOT / "tabs/dinner_unified_center_20260617.py").read_text()
    for forbidden in ("canonical_regime_snapshot", "ensure_shared_calculation_result", "build_decision_result", "sort_values"):
        assert forbidden not in dinner


def test_05_ai_tab_opening_no_analysis():
    ai = (ROOT / "tabs/ai_assistant_compact_20260619.py").read_text()
    render_body = ai.split("def render_compact_ai_assistant", 1)[1]
    before_submit = render_body.split('if not submitted or not question.strip():', 1)[0]
    assert "_legacy_answer(" not in before_submit
    assert "get_ai_fact_pack" in before_submit


def test_06_ai_send_is_lazy_and_stale_guarded():
    ai = (ROOT / "tabs/ai_assistant_compact_20260619.py").read_text()
    assert "from tabs import ai_assistant_lite as legacy" in ai
    assert "newer calculation replaced this request" in ai


def test_07_closed_section_no_query():
    lunch = (ROOT / "tabs/final_lunch_upgrade_20260617.py").read_text()
    fn = lunch.split("def render_lunch_25day_backtest_expander", 1)[1].split("def render_lunch_10day", 1)[0]
    assert fn.index("if not st.toggle") < fn.index("_canonical_history_table")


def test_08_closed_chart_no_construction():
    dinner = (ROOT / "tabs/dinner_unified_center_20260617.py").read_text()
    body = dinner.split("def render_dinner_unified_center", 1)[1]
    assert body.index('dinner_gate_chart_20260619') < body.index('_render_powerbi_regime_chart(ns)')


def test_09_new_h1_incremental_identity_invalidates():
    a = canonical(1, "2026-06-19T10:00:00+00:00")
    b = canonical(1, "2026-06-19T11:00:00+00:00"); b.pop("canonical_calculation_id")
    a.pop("canonical_calculation_id")
    assert calculation_id(a) != calculation_id(b)


def test_10_nlp_only_update_does_not_require_ohlc_rebuild():
    c = canonical(); s1 = build_compact_summary(c, shared())
    c2 = dict(c); c2["nlp"] = {**c["nlp"], "direction": "WAIT"}
    s2 = build_compact_summary(c2, shared())
    assert s1["scores"] == s2["scores"] and s1["projection"] == s2["projection"]
    assert s2["nlp"]["direction"] == "WAIT"


def test_11_canonical_cache_reuse_and_bound():
    state = {}
    for i in range(1, 5):
        publish_compact_runtime(state, canonical(i), shared())
    assert len(state[BOUNDED_CACHE_KEY]) == MAX_GENERATIONS == 2
    assert state[SUMMARY_KEY]["calculation_id"].startswith("CID-4")


def test_12_cache_key_correctness_static():
    ai = (ROOT / "tabs/ai_assistant_compact_20260619.py").read_text()
    assert 'f"{calculation_id}|{_normalize(question)}|{mode}"' in ai


def test_13_database_column_projection():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "x.sqlite"
        f = pd.DataFrame({"a": range(10), "b": range(10), "c": range(10)})
        persist_frame("c1", "history", f, db_path=db)
        out = query_frame("c1", "history", columns=["a", "c"], limit=3, db_path=db)
        assert list(out.columns) == ["a", "c"]


def test_14_database_row_limit():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "x.sqlite"
        persist_frame("c1", "history", pd.DataFrame({"a": range(50)}), db_path=db)
        assert len(query_frame("c1", "history", limit=7, db_path=db)) == 7


def test_15_no_full_history_dataframe_in_session_after_spool():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "x.sqlite"
        state = {"canonical_priority_table_20260617": pd.DataFrame({"Time": pd.date_range("2026-01-01", periods=500, freq="h"), "x": range(500)})}
        spool_history_frames(state, "c1", phone_mode=True, db_path=db)
        assert len(state["canonical_priority_table_20260617"]) <= 48
        assert frame_manifest("c1", "canonical_priority_table_20260617", db_path=db)["row_count"] == 500


def test_16_no_unbounded_cache():
    assert MAX_GENERATIONS == 2
    ai = (ROOT / "tabs/ai_assistant_compact_20260619.py").read_text()
    assert "MAX_CACHE = 32" in ai and "popitem(last=False)" in ai


def test_17_dataframe_copy_reduction_active_paths():
    new = sum((ROOT / f).read_text().count(".copy(") for f in ["tabs/final_lunch_upgrade_20260617.py", "tabs/dinner_unified_center_20260617.py"])
    old = sum((ROOT / f).read_text().count(".copy(") for f in ["tabs/final_lunch_upgrade_20260617_legacy.src", "tabs/dinner_unified_center_20260617_legacy.src"])
    assert new < old


def test_18_repeated_sort_reduction_active_paths():
    new = sum((ROOT / f).read_text().count("sort_values(") for f in ["tabs/final_lunch_upgrade_20260617.py", "tabs/dinner_unified_center_20260617.py"])
    old = sum((ROOT / f).read_text().count("sort_values(") for f in ["tabs/final_lunch_upgrade_20260617_legacy.src", "tabs/dinner_unified_center_20260617_legacy.src"])
    assert new < old


def test_19_mobile_row_limit():
    lunch = (ROOT / "tabs/final_lunch_upgrade_20260617.py").read_text()
    assert "48 if phone" in lunch or "48 if st.session_state.get" in lunch


def test_20_full_history_preservation():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "x.sqlite"
        f = pd.DataFrame({"a": range(123)})
        persist_frame("c", "h", f, db_path=db)
        assert frame_manifest("c", "h", db_path=db)["row_count"] == 123


def test_21_export_full_history():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "x.sqlite"
        persist_frame("c", "h", pd.DataFrame({"a": range(123)}), db_path=db)
        assert len(export_frame("c", "h", db_path=db)) == 123


def test_22_optional_query_failure_isolation():
    assert query_frame("missing", "missing", db_path=Path(tempfile.gettempdir()) / "missing-adx-test.sqlite").empty


def test_23_last_valid_result_preservation_source():
    runtime = (ROOT / "core/canonical_runtime_20260617.py").read_text()
    assert "The last valid canonical run remains untouched if validation fails" in runtime
    assert "state[LAST_VALID_KEY] = canonical" in runtime


def test_24_streamlit_startup_smoke_static():
    for name in ("app.py", "adx_dashpoard.py", "core/app_shell.py", "core/app/runner.py"):
        ast.parse((ROOT / name).read_text(), filename=name)
    assert "from adx_dashpoard import main" in (ROOT / "app.py").read_text()


def test_25_mobile_rendering_smoke_static():
    cards = (ROOT / "ui/composite_summary_cards_20260619.py").read_text()
    assert "@media(max-width:760px)" in cards and "grid-template-columns:1fr" in cards


def test_26_ai_fact_pack_size():
    s = build_compact_summary(canonical(), shared())
    evidence = [{"x": "y" * 1000, "i": i} for i in range(100)]
    p = build_ai_fact_pack(s, canonical=canonical(), evidence_rows=evidence)
    assert p["size_bytes"] <= 100_000


def test_27_calculation_id_consistency():
    state = {}
    summary, fact = publish_compact_runtime(state, canonical(), shared())
    assert summary["calculation_id"] == fact["calculation_id"] == state[FACT_PACK_KEY]["calculation_id"]


def test_28_composite_card_value_preservation():
    # Load pure card function with a minimal Streamlit stub.
    fake = SimpleNamespace(session_state={})
    sys.modules.setdefault("streamlit", fake)
    from ui.composite_summary_cards_20260619 import card_payload
    summary = build_compact_summary(canonical(), shared())
    cards = card_payload(summary)
    assert len(cards) == 8
    flat = json.dumps(cards, default=str)
    for expected in ("Master", "Entry", "Exit Risk", "H+6", "KNN", "Calculation ID"):
        assert expected in flat


def test_29_existing_score_scale_preservation():
    summary = build_compact_summary(canonical(), shared())
    assert summary["scores"] == {"master": 6.2, "entry": 6.8, "hold": 5.9, "tp": 6.1, "exit_risk": 3.4, "trend_capacity_remaining": 6.0}


def test_30_projection_paths_preserved():
    p = build_compact_summary(canonical(), shared())["projection"]
    assert p["red_path_preserved"] and p["yellow_path_preserved"] and p["blue_path_preserved"]
    legacy = (ROOT / "tabs/dinner_unified_center_20260617_legacy.src").read_text()
    assert "_render_powerbi_regime_chart" in legacy
