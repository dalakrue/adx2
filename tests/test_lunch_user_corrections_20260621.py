from __future__ import annotations

from pathlib import Path
import importlib.util
import sqlite3
import sys
import types
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _load_with_streamlit_stub(name: str, relative_path: str):
    fake = types.ModuleType("streamlit")
    fake.session_state = {}
    with patch.dict(sys.modules, {"streamlit": fake}):
        spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
    return module


def test_field1_renders_only_requested_two_history_groups():
    body = source("ui/lunch_four_core_fields_20260619.py").split(
        "if _gate(FULL_METRIC_FIELD, 1, state):", 1
    )[1].split("if _gate(POWERBI_FIELD, 2, state):", 1)[0]
    assert body.count("_render_full_metric_history(state)") == 1
    assert "_render_current_data(state)" not in body
    assert "_render_medium_standard_bias(state)" not in body
    assert '_render_evidence("FIELD_1"' not in body
    assert "render_canonical_copy_export" not in body
    history = source("ui/lunch_four_core_fields_20260619.py").split(
        "def _render_full_metric_history", 1
    )[1].split("def _render_powerbi", 1)[0]
    assert "Overall Full Metric History — Last 25 Days" in history
    assert "All 10 Decision Histories — Last 25 Days" in history


def test_original_hidden_field1_renderers_remain_available_for_rollback():
    text = source("ui/lunch_four_core_fields_20260619.py")
    assert "def _render_current_data" in text
    assert "def _render_medium_standard_bias" in text
    assert "def _render_evidence" in text


def _minimal_valid_canonical() -> dict:
    return {
        "run_id": "run-ai-fix",
        "canonical_calculation_id": "run-ai-fix",
        "calculation_generation": 7,
        "data_signature": "abc123",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "source": "TEST",
        "latest_completed_candle_time": "2026-06-21T10:00:00+00:00",
        "created_at": "2026-06-21T10:01:00+00:00",
        "expires_at": "2026-06-21T12:00:00+00:00",
        "schema_version": "2.0.0",
        "calculation_version": "test-v1",
        "calculation_status": "COMPLETED",
        "market": {"latest_completed_candle_time": "2026-06-21T10:00:00+00:00", "current_price": 1.16},
        "final_decision": {"final_decision": "WAIT", "directional_market_view": "SELL", "less_risky_decision": "WAIT"},
        "regime": {"major_regime": "BEAR_NORMAL", "reliability": 70},
    }


def test_ai_fact_pack_recovers_from_successful_canonical_without_recalculation():
    from core.canonical_runtime_20260617 import CANONICAL_KEY
    from core.compact_canonical_20260619 import FACT_PACK_KEY
    module = _load_with_streamlit_stub("ai_assistant_compact_test_20260621", "tabs/ai_assistant_compact_20260619.py")

    state = {CANONICAL_KEY: _minimal_valid_canonical()}
    pack = module._recover_fact_pack(state)
    assert pack["calculation_id"] == "run-ai-fix"
    assert state[FACT_PACK_KEY]["calculation_id"] == "run-ai-fix"
    assert "settings_run_orchestrator" not in source("tabs/ai_assistant_compact_20260619.py")
    assert "run_settings_calculation" not in source("tabs/ai_assistant_compact_20260619.py")


def test_causal_direction_accuracy_uses_forecast_origin_not_target_candle_open():
    from tabs.powerbi_direction_accuracy_patch_20260621 import relabel_direction_accuracy

    rows = []
    for i in range(30):
        origin = 1.1000 + i * 0.00001
        rows.append({
            "time": pd.Timestamp("2026-06-01", tz="UTC") + pd.Timedelta(hours=i),
            "Actual Open": origin + 0.0015,  # candle body says DOWN
            "Actual High": origin + 0.0018,
            "Actual Low": origin - 0.0002,
            "Actual Close": origin + 0.0005,  # outcome from forecast origin says UP
            "Pred Open": origin,
            "Pred High": origin + 0.0012,
            "Pred Low": origin - 0.0001,
            "Pred Close": origin + 0.0010,  # forecast says UP
            "Actual Direction": "DOWN",
            "Pred Direction": "UP",
            "Direction Correct": False,
            "Close Error %": 0.01,
        })
    out, summary = relabel_direction_accuracy(pd.DataFrame(rows), {"direction_accuracy_pct": 0.0})
    assert summary["legacy_direction_accuracy_pct"] == 0.0
    assert summary["causal_actionable_direction_accuracy_pct"] == 100.0
    assert summary["actionable_forecasts"] == 30
    assert set(out["Validated Pred Direction"]) == {"UP"}
    assert set(out["Validated Actual Direction"]) == {"UP"}
    assert bool(out["Validated Direction Correct"].dropna().all())


def test_tiny_powerbi_moves_are_wait_not_actionable():
    from tabs.powerbi_direction_accuracy_patch_20260621 import relabel_direction_accuracy

    frame = pd.DataFrame({
        "time": pd.date_range("2026-06-01", periods=24, freq="h", tz="UTC"),
        "Actual High": [1.1005] * 24,
        "Actual Low": [1.0995] * 24,
        "Actual Close": [1.1001] * 24,
        "Pred Open": [1.1000] * 24,
        "Pred Close": [1.100001] * 24,
    })
    out, summary = relabel_direction_accuracy(frame, {})
    assert summary["actionable_forecasts"] == 0
    assert summary["direction_evidence_status"] == "INSUFFICIENT_EVIDENCE"
    assert set(out["Validated Pred Direction"]) == {"WAIT"}


def test_direction_evaluation_is_deterministic_and_does_not_change_point_forecasts():
    from tabs.powerbi_direction_accuracy_patch_20260621 import relabel_direction_accuracy

    frame = pd.DataFrame({
        "time": pd.date_range("2026-06-01", periods=25, freq="h", tz="UTC"),
        "Actual High": [1.101] * 25,
        "Actual Low": [1.099] * 25,
        "Actual Close": [1.1004] * 25,
        "Pred Open": [1.1000] * 25,
        "Pred Close": [1.1006] * 25,
    })
    first, first_summary = relabel_direction_accuracy(frame, {})
    second, second_summary = relabel_direction_accuracy(frame, {})
    pd.testing.assert_frame_equal(first, second)
    assert first_summary == second_summary
    pd.testing.assert_series_equal(first["Pred Close"], frame["Pred Close"], check_names=False)


def test_field6_is_future_strategy_history_not_generic_sections():
    text = source("ui/system_readiness_20260621.py")
    lunch = source("ui/lunch_four_core_fields_20260619.py")
    assert "Future Strategy Research & Historical Evidence" in text
    assert "Equation, theorem, concept and hypothesis registry" in text
    assert "Section A — Data readiness" not in text
    assert "Section F — Final preparation checklist" not in text
    assert 'READINESS_FIELD = "6. Open / Close — Future Strategy Research History"' in lunch
    for token in ("ml_production_readiness_history", "conditional_predictive_ability_history", "research_spa_results", "reject_option_history", "metamorphic_test_history"):
        assert token in text


def test_field6_database_reader_is_bounded_projected_and_read_only(tmp_path: Path):
    module = _load_with_streamlit_stub("system_readiness_test_20260621", "ui/system_readiness_20260621.py")

    db = tmp_path / "evidence.sqlite3"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE ml_production_readiness_history(evaluation_id TEXT PRIMARY KEY, evaluated_at TEXT, overall_readiness_score REAL, promotion_allowed INTEGER, payload_json TEXT)")
    conn.executemany(
        "INSERT INTO ml_production_readiness_history VALUES(?,?,?,?,?)",
        [(f"e{i}", f"2026-06-21T{i%24:02d}:00:00Z", float(i), 0, "secret-large-payload") for i in range(150)],
    )
    conn.commit(); conn.close()
    before = db.stat().st_size
    out = module.load_research_history("ml_production_readiness_history", db_path=db, limit=120)
    after = db.stat().st_size
    assert len(out) == 120
    assert "payload_json" not in out.columns
    assert before == after
    conn = sqlite3.connect(db)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert tables == {"ml_production_readiness_history"}


def test_ai_history_is_catalogued_in_field5_not_field6():
    text = source("core/history_evidence_store_20260620.py")
    assert 'HistorySpec("ai_assistant_history", "FIELD_5"' in text
    assert 'HistorySpec("ai_evidence_reference_history", "FIELD_5"' in text
    assert 'HistorySpec("ai_answer_consistency_history", "FIELD_5"' in text
