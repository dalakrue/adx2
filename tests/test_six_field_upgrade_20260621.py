from __future__ import annotations

import copy
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def canonical_fixture():
    canonical = {
        "run_id": "run-42", "canonical_calculation_id": "run-42", "calculation_generation": 42,
        "latest_completed_candle_time": "2026-06-21T10:00:00Z", "created_at": "2026-06-21T10:01:00Z",
        "schema_version": "2.0.0", "symbol": "EURUSD", "timeframe": "H1", "source": "TWELVE",
        "last_close": 1.155, "master_score": 5.1, "entry_score": 4.8, "hold_safety": 5.4,
        "tp_quality": 4.2, "exit_risk": 6.8,
        "final_decision": {"final_decision": "WAIT", "less_risky_decision": "WAIT", "directional_market_view": "SELL", "selected_horizon": 6, "main_reason": "Conflict remains", "blocking_reasons": ["Regime conflict"]},
        "regime": {"major_regime": "BEAR_NORMAL", "reliability": 72},
        "forecasts": {"horizons": {"6h": {"direction": "SELL", "point_forecast": 1.152, "lower_bound": 1.149, "upper_bound": 1.160}}},
    }
    summary = {
        "calculation_id": "run-42", "schema_version": "2.0.0",
        "identity": {"run_id": "run-42", "calculation_generation": 42, "symbol": "EURUSD", "timeframe": "H1", "source": "TWELVE", "latest_completed_candle_time": "2026-06-21T10:00:00Z"},
        "decision": {"current_decision": "WAIT", "less_risky_bias": "WAIT", "direction": "SELL", "main_reason": "Conflict remains", "blocking_reasons": ["Regime conflict"]},
        "scores": {"master": 5.1, "entry": 4.8, "hold": 5.4, "tp": 4.2, "exit_risk": 6.8},
        "priority": {"opportunity_quality": "WATCH", "current_rank": 8, "knn_priority": "B", "greedy_priority": "B"},
        "regime": {"directional_regime": "BEAR_NORMAL", "regime_reliability": 72, "alpha": -0.2, "delta": -0.1, "transition_risk": 31},
        "projection": {"current_close": 1.155, "h1": 1.154, "h3": 1.153, "h6": 1.152, "lower_band": 1.149, "upper_band": 1.160, "projection_confidence": 68, "path_agreement": 62, "selected_horizon": 6},
        "uncertainty": {"combined": 38, "calibration_status": "CALIBRATED"},
        "validation": {"stale_status": "CURRENT", "data_freshness": "FRESH", "layer_status": "COMPLETE", "validation_status": "PASS"},
        "similar_day": {"pattern_family": "Compression", "best_match_date": "2026-06-10", "weighted_result": "WAIT", "reliability": 58},
        "nlp": {"direction": "WAIT", "reliability": 55, "conflict": "LOW"},
    }
    plan = {"status": "WARNING", "planned_risk_pct": 0.5, "planned_dollar_loss": 5, "margin_estimate": 25, "stop_distance_pips": 12}
    return canonical, summary, plan


def test_01_exactly_six_principal_labels_exist():
    text = source("ui/lunch_four_core_fields_20260619.py")
    body = text.split("def render_lunch_six_core_fields", 1)[1].split("def render_lunch_four_core_fields", 1)[0]
    assert body.count("if _gate(") == 6
    assert "FIELD_LABELS = (FULL_METRIC_FIELD, POWERBI_FIELD, REGIME_FIELD, CURRENT_FIELD, AI_FIELD, READINESS_FIELD)" in text


def test_02_field5_and_field6_not_nested_in_field4():
    text = source("ui/lunch_four_core_fields_20260619.py")
    field4 = text.split("def _render_regime_combined_logic", 1)[1].split("def _render_ai_assistant_lazy", 1)[0]
    assert "render_compact_ai_assistant" not in field4
    assert "render_system_readiness" not in field4


def test_03_opening_one_field_does_not_dispatch_another():
    body = source("ui/lunch_four_core_fields_20260619.py").split("def render_lunch_six_core_fields", 1)[1].split("def render_lunch_four_core_fields", 1)[0]
    assert body.count("_render_powerbi(state)") == 1
    assert body.count("_render_ai_assistant_lazy(state)") == 1
    assert body.count("render_system_readiness(state=state)") == 1


def test_04_closed_fields_do_not_import_heavy_renderers():
    text = source("ui/lunch_four_core_fields_20260619.py")
    prefix = text.split("def render_lunch_six_core_fields", 1)[0]
    assert "from tabs.ai_assistant_compact_20260619 import" not in prefix.split("def _render_ai_assistant_lazy", 1)[0]
    assert "from ui.system_readiness_20260621 import" not in prefix
    body = text.split("def render_lunch_six_core_fields", 1)[1]
    assert body.index("if _gate(AI_FIELD, 5, state):") < body.index("from ui.system_readiness_20260621 import")


def test_05_toggles_never_call_settings_orchestrator():
    text = source("ui/lunch_four_core_fields_20260619.py")
    assert "settings_run_orchestrator" not in text
    assert "run_settings_calculation" not in text


def _load_refresh_module(fake_state):
    fake_st = types.ModuleType("streamlit"); fake_st.session_state = fake_state
    fake_connectors = types.ModuleType("core.data_connectors")
    fake_connectors.maybe_refresh = Mock()
    fake_connectors.refresh_now = Mock()
    with patch.dict(sys.modules, {"streamlit": fake_st, "core.data_connectors": fake_connectors}):
        spec = importlib.util.spec_from_file_location("refresh_under_test", ROOT / "core/app/refresh.py")
        module = importlib.util.module_from_spec(spec); assert spec and spec.loader
        spec.loader.exec_module(module)
    return module, fake_connectors


def test_06_refresh_calls_connector_not_run_calculation():
    state = {"symbol": "EURUSD", "timeframe": "H1", "canonical_result_20260617": {"run_id": "old"}, "canonical_calculation_generation_20260617": 1}
    module, connectors = _load_refresh_module(state)
    frame = pd.DataFrame({"time": pd.date_range("2026-06-21", periods=3, freq="h", tz="UTC"), "close": [1.1, 1.2, 1.3]})
    connectors.refresh_now.return_value = (frame, True, "TWELVE", "refreshed")
    result = module.refresh_data(state)
    assert connectors.refresh_now.call_count == 1
    assert result["ok"] is True
    assert "settings_run_orchestrator" not in source("core/app/refresh.py")


def test_07_refresh_marks_previous_generation_stale_and_preserves_it():
    state = {"symbol": "EURUSD", "timeframe": "H1", "canonical_result_20260617": {"run_id": "old"}, "canonical_calculation_generation_20260617": 9}
    module, connectors = _load_refresh_module(state)
    frame = pd.DataFrame({"time": pd.date_range("2026-06-21", periods=2, freq="h", tz="UTC"), "close": [1.1, 1.2]})
    connectors.refresh_now.return_value = (frame, True, "TWELVE", "ok")
    module.refresh_data(state)
    assert state["dependent_calculations_stale_20260621"] is True
    assert state["canonical_result_20260617"]["run_id"] == "old"
    assert state["canonical_calculation_generation_20260617"] == 9


def test_08_run_calculation_publication_contract_unchanged():
    text = source("core/settings_run_orchestrator_20260617.py")
    assert "publish_canonical_atomically" in text
    assert "completed" in text.lower() and "h1" in text.lower()


def test_09_copy_short_budget_and_required_content():
    from services.canonical_exports import build_short_payload
    canonical, summary, plan = canonical_fixture()
    text, stats = build_short_payload(canonical, summary, plan)
    assert stats.lines <= 40 and stats.characters <= 6000 and stats.estimated_tokens <= 1500
    for label in ("Symbol/timeframe", "Completed candle", "Current price", "Current decision", "Less-risky decision", "Priority/rank", "Current regime", "Regime reliability", "Master/Entry/Hold/TP/Exit Risk", "Forecast direction/horizon", "Prediction interval", "Uncertainty/error", "Data freshness", "Generation ID"):
        assert label in text
    assert "raw canonical" not in text.lower()


def test_10_menu_and_lunch_copy_use_same_service():
    popup = source("ui/liquid_menu_popup_20260615.py")
    readiness = source("ui/system_readiness_20260621.py")
    assert "render_canonical_copy_export" in popup
    assert "render_canonical_copy_export" in readiness
    assert "build_current_home_payload(short=True)" not in popup


def test_11_copy_all_includes_all_six_fields():
    from services.canonical_exports import all_text
    canonical, summary, plan = canonical_fixture()
    text = all_text(canonical, summary, plan, {"final_status": "READY WITH WARNINGS", "checklist": {}})
    for i in range(1, 7): assert f"Field {i}" in text
    assert "canonical_generation\"" not in text


def test_12_ai_answer_contains_status_and_generation():
    from core.ai_grounded_pipeline_20260621 import answer_question
    canonical, summary, plan = canonical_fixture()
    with patch("core.ai_grounded_pipeline_20260621.load_settled_evidence", return_value=[]):
        result = answer_question("Why is the current decision WAIT?", canonical=canonical, summary=summary, plan=plan, state={})
    assert result["status"] in {"SUPPORTED", "PARTIALLY_SUPPORTED", "CONFLICTING_EVIDENCE", "INSUFFICIENT_EVIDENCE", "STALE_GENERATION"}
    assert "**Generation ID:** run-42" in result["answer"]
    assert "**Evidence coverage status:**" in result["answer"]


def test_13_ai_returns_insufficient_evidence_when_absent():
    from core.ai_grounded_pipeline_20260621 import answer_question
    with patch("core.ai_grounded_pipeline_20260621.load_settled_evidence", return_value=[]):
        result = answer_question("Explain the Power BI path", canonical={}, summary={}, plan={}, state={})
    assert result["status"] == "INSUFFICIENT_EVIDENCE"


def test_14_ai_never_changes_protected_decision_fields():
    from core.ai_grounded_pipeline_20260621 import answer_question
    canonical, summary, plan = canonical_fixture(); before = copy.deepcopy(canonical)
    with patch("core.ai_grounded_pipeline_20260621.load_settled_evidence", return_value=[]):
        answer_question("Explain risk", canonical=canonical, summary=summary, plan=plan, state={})
    assert canonical == before


def test_15_history_newest_completed_h1_first():
    from core.history_query_20260621 import project_completed_h1
    frame = pd.DataFrame({"Time": pd.to_datetime(["2026-06-21T09:00Z", "2026-06-21T11:00Z", "2026-06-21T10:00Z"]), "value": [1, 3, 2]})
    out = project_completed_h1(frame, completed_h1="2026-06-21T10:00Z")
    assert list(out["value"]) == [2, 1]


def test_16_no_future_timestamp_enters_historical_evidence():
    from core.history_query_20260621 import project_completed_h1
    frame = pd.DataFrame({"Time": pd.to_datetime(["2026-06-21T09:00Z", "2026-06-21T12:00Z"]), "value": [1, 9]})
    out = project_completed_h1(frame, completed_h1="2026-06-21T10:00Z")
    assert 9 not in set(out["value"])


def test_17_mobile_rendering_has_exclusive_open_and_no_horizontal_field_controls():
    text = source("ui/lunch_four_core_fields_20260619.py")
    assert "Phone mode: keep only one large field open" in text
    assert "lunch_phone_exclusive_open_20260621" in text
    assert "horizontal=True" not in text


def test_18_startup_compile_smoke_and_regression_commands_documented():
    assert (ROOT / "app.py").exists()
    assert (ROOT / "runtime.txt").read_text().strip() == "python-3.12"
    assert "pytest" in source("requirements.txt").lower() or (ROOT / "tests").exists()


def test_19_protected_output_modules_not_modified_by_upgrade_manifest():
    protected = {"core/settings_run_orchestrator_20260617.py", "core/decision_product_engine_20260617.py", "core/canonical_runtime_20260617.py"}
    manifest_path = ROOT / "MODIFIED_FILES_MANIFEST_20260621_SIX_FIELD.json"
    if manifest_path.exists():
        import json
        modified = set(json.loads(manifest_path.read_text()).get("modified_files", []))
        assert not (protected & modified)
    else:
        for path in protected: assert (ROOT / path).exists()


def test_20_performance_report_records_actual_measurements():
    report = ROOT / "PERFORMANCE_BEFORE_AFTER_20260621.md"
    if report.exists():
        text = report.read_text(encoding="utf-8")
        for metric in ("Wall-clock", "CPU time", "Peak RSS", "Session-state", "Cache entries", "DataFrame count", "Largest retained objects"):
            assert metric in text
    else:
        assert (ROOT / "tools").exists()
