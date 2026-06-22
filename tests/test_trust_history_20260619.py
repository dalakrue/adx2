from __future__ import annotations

import sqlite3

import pandas as pd

from core.trust_history_20260619 import TrustHistoryStore, aggregate_trust


def _ohlc() -> pd.DataFrame:
    times = pd.date_range("2026-06-18 00:00", periods=30, freq="h", tz="UTC")
    closes = [1.1500 + i * 0.00001 for i in range(30)]
    return pd.DataFrame({
        "time": times,
        "open": closes,
        "high": [x + 0.0005 for x in closes],
        "low": [x - 0.0005 for x in closes],
        "close": [x + 0.0001 for x in closes],
    })


def _canonical() -> dict:
    origin = pd.Timestamp("2026-06-18 10:00", tz="UTC")
    horizons = {}
    for h in (1, 2, 3, 6):
        horizons[f"{h}h"] = {
            "direction": "BUY",
            "point_forecast": 1.1510 + h * 0.0001,
            "lower_bound": 1.1490,
            "upper_bound": 1.1530,
            "buy_probability_raw": 0.68,
            "sell_probability_raw": 0.22,
            "wait_probability_raw": 0.10,
            "buy_probability_calibrated": 0.62,
            "sell_probability_calibrated": 0.27,
            "wait_probability_calibrated": 0.11,
            "threshold": 0.58,
            "expected_value": 0.0003,
            "expected_gain": 0.0008,
            "expected_loss": 0.0004,
            "priority_score": 70,
            "knn_score": 68,
            "greedy_score": 2,
            "due_time": (origin + pd.Timedelta(hours=h)).isoformat(),
            "blocking_reasons": [],
        }
    return {
        "canonical_calculation_id": "trust-test-1",
        "run_id": "trust-test-1",
        "created_at": origin.isoformat(),
        "latest_completed_candle_time": origin.isoformat(),
        "last_close": 1.1510,
        "source": "TEST",
        "calculation_version": "test-v1",
        "full_metric_direction": "BUY",
        "final_decision": {
            "directional_market_view": "BUY",
            "final_decision": "BUY",
            "tradeability_decision": "BUY",
            "main_reason": "test",
            "blocking_reasons": [],
        },
        "forecasts": {"horizons": horizons, "agreement_score": 0.8, "selected_horizon": 3},
        "regime": {"major_regime": "BULL_NORMAL", "age_hours": 12, "transition_probability_3h": 0.2},
        "data_quality": {"status": "PASS"},
        "drift": {"status": "STABLE"},
        "nlp": {"conflict_level": "LOW"},
        "priority": {"score": 70, "knn_score": 68, "greedy_score": 2},
        "risk": {"estimated_cost": 0.00012},
    }


def test_forecasts_are_pending_then_settled_without_prediction_overwrite(tmp_path):
    db = tmp_path / "ledger.sqlite3"
    store = TrustHistoryStore(db)
    result = store.record_forecasts(_canonical(), _ohlc())
    assert result["inserted"] == 4
    before = store.frame(limit=10).sort_values("horizon")
    original_predictions = before["predicted_close"].tolist()
    assert set(before["record_status"]) == {"PENDING"}

    settled = store.settle_pending(_ohlc())
    assert settled["settled"] == 4
    after = store.frame(limit=10).sort_values("horizon")
    assert set(after["record_status"]) == {"SETTLED"}
    assert after["predicted_close"].tolist() == original_predictions
    assert after["actual_close"].notna().all()


def test_schema_indexes_and_honest_insufficient_status(tmp_path):
    db = tmp_path / "ledger.sqlite3"
    store = TrustHistoryStore(db)
    summary = aggregate_trust(store)
    assert summary["trust_classification"] == "INSUFFICIENT"
    assert "insufficient settled samples" in summary["message"].lower()
    with sqlite3.connect(db) as conn:
        indexes = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert "idx_trust_origin" in indexes
    assert "idx_trust_status_target" in indexes
