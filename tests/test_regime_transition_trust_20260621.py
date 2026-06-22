from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from core.regime_transition_trust_20260621 import (
    DRIFT_LABELS,
    adaptive_window_detection,
    bayesian_online_changepoint,
    build_regime_transition_trust,
)
from core.regime_trust_store_20260621 import RegimeTrustStore, TABLE_COLUMNS

ROOT = Path(__file__).resolve().parents[1]


def fixture_payload():
    rng = np.random.default_rng(42)
    times = pd.date_range("2026-06-01", periods=300, freq="h", tz="UTC")
    returns = np.r_[rng.normal(0.0, 0.00008, 180), rng.normal(0.00004, 0.00022, 120)]
    close = 1.15 + np.cumsum(returns)
    frame = pd.DataFrame({"Time": times, "Open": close - 0.00003, "High": close + 0.0002, "Low": close - 0.0002, "Close": close})
    regimes = ["RANGE_NORMAL"] * 100 + ["BULL_COMPRESSION"] * 100 + ["BULL_EXPANSION"] * 100
    priority = pd.DataFrame({"Time": times, "Regime": regimes, "Priority Rank": np.tile(np.arange(1, 15), 22)[:300]})
    settled = pd.DataFrame({
        "confidence": np.linspace(0.55, 0.82, 80),
        "predicted_direction": ["BUY"] * 80,
        "actual_direction": ["BUY"] * 58 + ["SELL"] * 22,
        "actual_inside_interval": [1] * 69 + [0] * 11,
        "absolute_close_error": np.abs(rng.normal(0.00035, 0.00012, 80)),
    })
    canonical = {
        "run_id": "RUN-TRUST-1",
        "canonical_calculation_id": "RUN-TRUST-1",
        "calculation_generation": 17,
        "latest_completed_candle_time": times[-1],
        "shared_result_schema_version": "2.0.0",
        "regime": {"major_regime": "BULL_EXPANSION", "previous_regime": "BULL_COMPRESSION", "reliability": 79.0},
        "final_decision": {"final_decision": "BUY", "directional_market_view": "BUY", "less_risky_decision": "BUY"},
        "reliability": {"score": 76.0},
        "forecasts": {
            "selected": {"point_forecast": float(close[-1] + 0.0005), "lower_bound": float(close[-1] - 0.0006), "upper_bound": float(close[-1] + 0.0010), "confidence_pct": 74.0, "direction": "BUY"},
            "models": {
                "LSTM": {"forecast": float(close[-1] + 0.0007), "confidence": 75},
                "Transformer": {"forecast": float(close[-1] + 0.0004), "confidence": 72},
                "XGBoost": {"forecast": float(close[-1] + 0.0002), "confidence": 70},
                "Prophet": {"forecast": float(close[-1] + 0.0001), "confidence": 62},
            },
        },
        "similar_day_intelligence": {"history_25": [{"Historical Date": "2026-06-05", "Similarity Index": 82.0}]},
    }
    return canonical, frame, priority, settled


def test_detectors_are_bounded_and_return_evidence_only():
    stable = bayesian_online_changepoint([0.0] * 30)
    shifted = adaptive_window_detection([0.0] * 80 + [3.0] * 80)
    assert 0 <= stable["probability"] <= 100
    assert shifted["status"] in {"CHANGE", "STABLE"}
    assert shifted["window_size"] <= 160


def test_existing_regime_and_formula_outputs_remain_unchanged():
    canonical, frame, priority, settled = fixture_payload()
    before = deepcopy(canonical)
    output, evidence, _ = build_regime_transition_trust(
        canonical, completed_h1=frame, priority_table=priority, settled_predictions=settled,
    )
    for protected in ("regime", "final_decision", "reliability", "forecasts"):
        assert output[protected] == before[protected]
    assert evidence["mode"] == "EVIDENCE_ONLY"
    assert evidence["protected_regime_unchanged"] is True
    assert evidence["protected_decision_unchanged"] is True
    assert evidence["transition_summary"]["drift_type"] in DRIFT_LABELS


def test_all_required_trust_sections_and_fields_are_published():
    canonical, frame, priority, settled = fixture_payload()
    output, evidence, _ = build_regime_transition_trust(canonical, completed_h1=frame, priority_table=priority, settled_predictions=settled)
    assert output["regime_transition_trust_center"] == evidence
    assert set(("transition_summary", "change_evidence", "historical_transition_matches", "prediction_calibration", "system_trust_audit")) <= set(evidence)
    audit = evidence["system_trust_audit"]
    assert audit["canonical_run_id"] == canonical["run_id"]
    assert audit["calculation_generation"] == canonical["calculation_generation"]
    assert audit["all_visible_components_same_canonical_result"] is True


def test_normalized_history_tables_have_identity_and_required_columns():
    canonical, frame, priority, settled = fixture_payload()
    _, _, bundle = build_regime_transition_trust(canonical, completed_h1=frame, priority_table=priority, settled_predictions=settled)
    for table in (
        "regime_transition_history", "post_transition_outcome_history",
        "prediction_calibration_history", "drift_detector_history", "decision_audit_history",
    ):
        assert table in bundle
        for row in bundle[table]:
            assert row["timestamp"] is not None
            assert row["run_id"] == canonical["run_id"]
            assert row["calculation_generation"] == canonical["calculation_generation"]
        assert set(TABLE_COLUMNS[table]) >= {"timestamp", "run_id", "calculation_generation"}


def test_duckdb_history_updates_incrementally_and_deduplicates():
    canonical, frame, priority, settled = fixture_payload()
    _, _, bundle = build_regime_transition_trust(canonical, completed_h1=frame, priority_table=priority, settled_predictions=settled)
    with tempfile.TemporaryDirectory() as directory:
        store = RegimeTrustStore(Path(directory) / "trust.duckdb")
        first = store.append_bundle(bundle)
        second = store.append_bundle(bundle)
        assert first["tables"]["decision_audit_history"] == 1
        assert second["tables"]["decision_audit_history"] == 0
        assert len(store.query("decision_audit_history")) == 1
        assert len(store.query("regime_transition_history")) == 1



def test_post_transition_outcomes_mature_without_duplicate_event_rows():
    timestamp = pd.Timestamp("2026-06-20T10:00:00Z")
    base = {
        "timestamp": timestamp, "run_id": "R1", "calculation_generation": 1,
        "transition_time": timestamp, "new_regime": "BULL_NORMAL",
        "entry_reference_price": 1.15, "actual_close_1h": None,
        "actual_close_2h": None, "actual_close_3h": None, "actual_close_6h": None,
        "direction_correct_1h": None, "direction_correct_3h": None,
        "direction_correct_6h": None, "maximum_favorable_excursion": None,
        "maximum_adverse_excursion": None, "regime_still_active_6h": None,
    }
    mature = dict(base)
    mature.update({
        "timestamp": timestamp + pd.Timedelta(hours=6), "run_id": "R2",
        "calculation_generation": 2, "actual_close_1h": 1.151,
        "actual_close_2h": 1.152, "actual_close_3h": 1.153,
        "actual_close_6h": 1.154, "direction_correct_1h": True,
        "direction_correct_3h": True, "direction_correct_6h": True,
        "maximum_favorable_excursion": 0.004, "maximum_adverse_excursion": -0.001,
        "regime_still_active_6h": True,
    })
    with tempfile.TemporaryDirectory() as directory:
        store = RegimeTrustStore(Path(directory) / "trust.duckdb")
        first = store.append_bundle({"post_transition_outcome_history": [base]})
        second = store.append_bundle({"post_transition_outcome_history": [mature]})
        frame = store.query("post_transition_outcome_history")
        assert first["tables"]["post_transition_outcome_history"] == 1
        assert second["tables"]["post_transition_outcome_history"] == 0
        assert second["updates"]["post_transition_outcome_history"] >= 7
        assert len(frame) == 1
        assert frame.iloc[0]["actual_close_6h"] == mature["actual_close_6h"]
        assert frame.iloc[0]["run_id"] == "R2"

def test_regime_evidence_cannot_overwrite_original_engine_by_source_contract():
    orchestrator = (ROOT / "core/settings_run_orchestrator_20260617.py").read_text(encoding="utf-8")
    builder = (ROOT / "core/regime_transition_trust_20260621.py").read_text(encoding="utf-8")
    assert "EVIDENCE_ONLY" in builder
    assert 'output["regime_transition_trust_center"] = result' in builder
    assert 'output["regime"] =' not in builder
    assert 'output["final_decision"] =' not in builder
    assert orchestrator.index("build_regime_transition_trust(") < orchestrator.index("publish_canonical_atomically(")
