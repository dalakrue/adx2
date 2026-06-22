from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from core.decision_contract_20260617 import DecisionResult, DriftResult, PriorityResult, RegimeResult
from core.decision_product_engine_20260617 import (
    build_decision_result, calibrate_probabilities, dynamic_threshold,
    serialize_result, validate_data_quality, _purged_walk_forward_direction_metrics,
)
from core.prediction_ledger_20260617 import PredictionLedger


class DecisionProductTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = PredictionLedger(Path(self.temp.name) / "ledger.sqlite3")
        self.now = pd.Timestamp("2026-06-17T14:00:00Z")
        self.df = self.make_ohlc(600, end=self.now - pd.Timedelta(hours=1))
        self.legacy = {
            "current": {
                "regime": "BULL_NORMAL", "forecast_close": float(self.df.close.iloc[-1] + 0.00055),
                "forecast_confidence": 70, "prediction_direction": "BUY", "priority_score": 74,
            },
            "regime": {"current": "BULL_NORMAL"},
            "reliability": {"score": 68},
            "powerbi": {"forecast_close": float(self.df.close.iloc[-1] + 0.00055), "confidence": 70},
            "priority": {"best": {"Priority Score": 74, "KNN Score": 78, "Greedy Score": 70}},
            "nlp": {"summary": {}},
        }

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def make_ohlc(n=300, end=None):
        end = end or pd.Timestamp.now(tz="UTC").floor("h") - pd.Timedelta(hours=1)
        time = pd.date_range(end=end, periods=n, freq="h", tz="UTC")
        rng = np.random.default_rng(20260617)
        close = 1.10 + np.cumsum(rng.normal(0, 0.00013, n))
        open_ = np.r_[close[0], close[:-1]]
        high = np.maximum(open_, close) + rng.uniform(0.00004, 0.00018, n)
        low = np.minimum(open_, close) - rng.uniform(0.00004, 0.00018, n)
        return pd.DataFrame({"time": time, "open": open_, "high": high, "low": low, "close": close, "volume": 100})

    def build(self):
        return build_decision_result(
            legacy_shared=self.legacy, ohlc=self.df, symbol="EURUSD", timeframe="H1",
            source="TEST", ledger=self.ledger, now=self.now,
        )

    def test_data_quality_pass(self):
        quality, clean = validate_data_quality(self.df, symbol="EURUSD", timeframe="H1", source="TEST", now=self.now)
        self.assertEqual(quality.status, "PASS")
        self.assertEqual(len(clean), 600)

    def test_empty_data_fail_all(self):
        quality, _ = validate_data_quality(pd.DataFrame(), symbol="EURUSD", timeframe="H1", source="TEST", now=self.now)
        self.assertEqual(quality.status, "FAIL_ALL")

    def test_malformed_ohlc_blocks_models(self):
        bad = self.df.copy()
        bad.loc[10, "high"] = bad.loc[10, "low"] - 0.1
        quality, _ = validate_data_quality(bad, symbol="EURUSD", timeframe="H1", source="TEST", now=self.now)
        self.assertIn(quality.status, {"FAIL_MODEL", "FAIL_ALL"})
        self.assertTrue(any("High below" in x for x in quality.blocking_reasons))

    def test_duplicate_timestamp_detected(self):
        bad = pd.concat([self.df, self.df.tail(1)], ignore_index=True)
        quality, _ = validate_data_quality(bad, symbol="EURUSD", timeframe="H1", source="TEST", now=self.now)
        self.assertEqual(quality.status, "FAIL_MODEL")
        self.assertTrue(any("Duplicate" in x for x in quality.blocking_reasons))

    def test_incomplete_latest_candle_excluded(self):
        df = self.make_ohlc(300, end=self.now)
        quality, clean = validate_data_quality(df, symbol="EURUSD", timeframe="H1", source="TEST", now=self.now)
        self.assertEqual(quality.status, "PASS_WITH_WARNING")
        self.assertEqual(len(clean), 299)
        self.assertFalse(quality.latest_candle_completed)

    def test_future_rows_are_safely_excluded_without_fail_model(self):
        last = self.df.iloc[-1].copy()
        last["time"] = self.now + pd.Timedelta(hours=2)
        with_future = pd.concat([self.df, pd.DataFrame([last])], ignore_index=True)
        quality, clean = validate_data_quality(
            with_future, symbol="EURUSD", timeframe="H1", source="TEST", now=self.now
        )
        self.assertEqual(quality.status, "PASS_WITH_WARNING")
        self.assertEqual(len(clean), len(self.df))
        self.assertFalse(quality.blocking_reasons)
        self.assertFalse(quality.model_disabled)
        self.assertTrue(any("safely excluded" in item for item in quality.warnings))
        self.assertLessEqual(clean["time"].max(), self.now)

    def test_canonical_serialization_and_unique_run(self):
        one = self.build()
        two = self.build()
        self.assertNotEqual(one.run_id, two.run_id)
        payload = serialize_result(one)
        json.dumps(payload)
        restored = DecisionResult.from_dict(payload)
        self.assertEqual(restored.run_id, one.run_id)
        self.assertEqual(set(restored.forecasts.horizons), {"1h", "2h", "3h", "6h"})

    def test_ledger_write_and_read(self):
        payload = serialize_result(self.build())
        self.assertTrue(self.ledger.record_result(payload)["ok"])
        health = self.ledger.health()
        self.assertEqual(health["counts"]["calculation_runs"], 1)
        self.assertEqual(health["counts"]["predictions"], 4)
        self.assertEqual(health["counts"]["prediction_outcomes"], 4)

    def test_pending_outcome_settlement(self):
        payload = serialize_result(self.build())
        self.ledger.record_result(payload)
        early = self.ledger.settle_pending_outcomes(self.df)
        self.assertEqual(early["settled"], 0)
        created = pd.Timestamp(payload["created_at"]).floor("h")
        last = float(self.df.close.iloc[-1])
        future = []
        for h in range(1, 8):
            close = last + h * 0.00008
            future.append({"time": created + pd.Timedelta(hours=h), "open": last, "high": close + 0.0001, "low": last - 0.0001, "close": close})
        settled = self.ledger.settle_pending_outcomes(pd.concat([self.df, pd.DataFrame(future)], ignore_index=True))
        self.assertEqual(settled["settled"], 4)
        self.assertEqual(len(self.ledger.settled_predictions(symbol="EURUSD", timeframe="H1")), 4)

    def test_calibration_fallback_is_explicit(self):
        probs, source, metrics = calibrate_probabilities(
            self.ledger, symbol="EURUSD", timeframe="H1", horizon=3,
            regime="BULL_NORMAL", raw=(0.6, 0.2, 0.2),
        )
        self.assertEqual(probs, (0.6, 0.2, 0.2))
        self.assertIn("EXISTING_RELIABILITY_PROXY", source)
        self.assertEqual(metrics["sample_count"], 0)

    def test_dynamic_threshold_negative_ev_forces_wait_gate(self):
        threshold, version, reasons = dynamic_threshold(
            horizon=3, regime=RegimeResult(major_regime="BULL_NORMAL", confidence=0.8),
            drift=DriftResult(), quality=validate_data_quality(self.df, symbol="EURUSD", timeframe="H1", source="TEST", now=self.now)[0],
            expected_value=-0.0001, interval_width_ratio=0.001, agreement=1.0,
            priority=PriorityResult(score=80), actionability=0.8, session="LONDON", history=pd.DataFrame(),
        )
        self.assertGreaterEqual(threshold, 0.99)
        self.assertIn("negative expected value", reasons)
        self.assertTrue(version)

    def test_expected_value_and_actionability_fields_exist(self):
        result = serialize_result(self.build())
        for item in result["forecasts"]["horizons"].values():
            self.assertIn("estimated_cost", item)
            self.assertIn("expected_value", item)
            self.assertIn("actionability_probability", item)
            self.assertIn(item["decision"], {"BUY", "SELL", "WAIT"})

    def test_regime_transition_fields_exist(self):
        regime = serialize_result(self.build())["regime"]
        for key in ("transition_probability_1h", "transition_probability_3h", "transition_probability_6h", "persistence_score"):
            self.assertIn(key, regime)
            self.assertGreaterEqual(float(regime[key]), 0)
            self.assertLessEqual(float(regime[key]), 1)

    def test_adaptive_intervals_are_horizon_specific(self):
        horizons = serialize_result(self.build())["forecasts"]["horizons"]
        widths = [horizons[f"{h}h"]["interval_width"] for h in (1,2,3,6)]
        self.assertTrue(all(x is not None and x > 0 for x in widths))
        self.assertGreater(widths[-1], widths[0])

    def test_drift_status_valid(self):
        drift = serialize_result(self.build())["drift"]
        self.assertIn(drift["status"], {"STABLE", "WATCH", "DEGRADED", "CRITICAL"})

    def test_no_finnhub_key_required(self):
        from core.finnhub_connector import validate_connection
        result = validate_connection("")
        self.assertFalse(result["ok"])
        self.assertIn("key", result["message"].lower())

    def test_invalid_finnhub_key_format_is_rejected_without_network(self):
        from core.finnhub_connector import validate_connection
        result = validate_connection("abc")
        self.assertFalse(result["ok"])
        self.assertEqual(result["availability"], "UNAVAILABLE")

    def test_purged_walk_forward_uses_chronology_and_gap(self):
        n = 120
        rows = pd.DataFrame({
            "created_at": pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC"),
            "actual_direction": np.where(np.arange(n) % 3 == 0, "BUY", "SELL"),
            "predicted_direction": np.where(np.arange(n) % 4 == 0, "BUY", "SELL"),
        })
        metrics = _purged_walk_forward_direction_metrics(rows, 6)
        self.assertEqual(metrics["status"], "VALID")
        self.assertGreater(metrics["fold_count"], 0)
        self.assertGreaterEqual(metrics["purge_gap_rows"], 6)
        self.assertEqual(metrics["embargo_rows"], 1)

    def test_ui_integration_static_guards(self):
        root = Path(__file__).resolve().parents[1]
        research = (root / "ui" / "nlp_research_panel.py").read_text(encoding="utf-8")
        lunch = (root / "tabs" / "final_lunch_upgrade_20260617.py").read_text(encoding="utf-8")
        router = (root / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
        self.assertIn("Finnhub API Connector for NLP", research)
        self.assertIn("render_lunch_canonical_panel", lunch)
        self.assertIn("render_powerbi_canonical_details", router)
        self.assertIn("render_regime_lifecycle_panel", router)
        self.assertEqual(router.count("run_settings_calculation(ns)"), 1)
        self.assertIn('if bool((calculation_status.get("canonical") or {}).get("ok"))', router)


if __name__ == "__main__":
    unittest.main(verbosity=2)
