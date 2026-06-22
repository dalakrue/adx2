from __future__ import annotations

import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("ADX_TEST_PROFILE", "fast")

from core.bounded_quantile_monitoring_20260621 import BoundedDDSketch
from core.canonical_data_validation_20260621 import validate_canonical_payload, validate_source_frame
from core.conditional_predictive_ability_20260621 import evaluate_conditional_predictive_ability
from core.covariate_shift_conformal_20260621 import build_covariate_shift_conformal
from core.fixed_share_expert_tracker_20260621 import fixed_share_update
from core.research_validation_layer_20260621 import build_research_validation_transaction
from core.research_validation_store_20260621 import BUNDLE_KEY
from core.sliding_monitoring_statistics_20260621 import ExponentialHistogramCounter
from core.snapshot_schema_20260619 import build_run_snapshot
from core.superior_predictive_ability_20260621 import evaluate_superior_predictive_ability
from services.canonical_snapshot_store import commit_snapshot, latest_completed


class ResearchValidation20260621Tests(unittest.TestCase):
    @staticmethod
    def frame(rows: int = 160, *, now: pd.Timestamp | None = None) -> pd.DataFrame:
        now = now or pd.Timestamp("2026-06-21T10:30:00Z")
        idx = pd.date_range(end=now.floor("h") - pd.Timedelta(hours=1), periods=rows, freq="h", tz="UTC")
        base = 1.15 + np.linspace(0, 0.002, rows)
        return pd.DataFrame({
            "open": base, "high": base + 0.001, "low": base - 0.001,
            "close": base + 0.0001, "spread": 0.0001,
            "adx": np.linspace(15, 30, rows), "atr_percentile": np.linspace(20, 80, rows),
        }, index=idx)

    @staticmethod
    def settled(rows: int = 80) -> tuple[pd.DataFrame, pd.DataFrame]:
        idx = pd.date_range("2026-06-01T00:00:00Z", periods=rows, freq="h")
        canonical, methods = [], []
        for i, target in enumerate(idx):
            actual = 1.15 + i * 0.00001
            origin = actual - 0.00005
            canonical.append({
                "calculation_id": f"C{i}", "forecast_origin_time": target - pd.Timedelta(hours=1),
                "target_time": target, "settlement_timestamp": target, "horizon": 1,
                "predicted_close": actual + 0.00020, "actual_close": actual,
                "forecast_origin_price": origin, "record_status": "SETTLED",
                "lower_band": actual - 0.001, "upper_band": actual + 0.001,
                "session": "ASIA", "h1_regime": "RANGE", "event_risk_status": "LOW",
            })
            for model, error in (("canonical", 0.00020), ("challenger", 0.00010)):
                methods.append({
                    "calculation_id": f"C{i}", "forecast_origin_time": target - pd.Timedelta(hours=1),
                    "target_time": target, "settlement_timestamp": target, "horizon": 1,
                    "method": model, "predicted_close": actual + error, "actual_close": actual,
                    "absolute_error": error, "record_status": "SETTLED",
                })
        return pd.DataFrame(canonical), pd.DataFrame(methods)

    @staticmethod
    def canonical(candle: str, run_id: str = "RUN-1", generation: int = 1) -> dict:
        return {
            "schema_version": "2.0.0", "run_id": run_id, "canonical_calculation_id": run_id,
            "calculation_generation": generation, "created_at": "2026-06-21T10:00:00Z",
            "calculation_completed_at": "2026-06-21T10:00:01Z", "symbol": "EURUSD", "timeframe": "H1",
            "source": "TEST", "latest_completed_candle_time": candle, "data_signature": f"sig-{generation}",
            "calculation_version": "test", "calculation_status": "COMPLETED",
            "market": {"latest_completed_candle_time": candle, "current_price": 1.15},
            "forecasts": {"horizons": {}}, "regime": {"major_regime": "RANGE"},
            "reliability": {"score": 70}, "priority": {}, "nlp": {}, "risk_plan": {},
            "final_decision": {"final_decision": "BUY", "directional_market_view": "BUY", "less_risky_decision": "BUY"},
            "metadata": {},
        }

    def test_source_validation_determinism_and_domains(self):
        now = pd.Timestamp("2026-06-21T10:30:00Z")
        frame = self.frame(now=now)
        one = validate_source_frame(frame, now=now)
        two = validate_source_frame(frame, now=now)
        self.assertTrue(one.publication_allowed)
        self.assertEqual(one.generation_id, two.generation_id)
        self.assertEqual(one.source_hash, two.source_hash)
        self.assertEqual(one.failed_constraints, two.failed_constraints)

        duplicate = pd.concat([frame, frame.iloc[[-1]]])
        self.assertFalse(validate_source_frame(duplicate, now=now).publication_allowed)
        incomplete = frame.copy(); incomplete.index = list(incomplete.index[:-1]) + [now.floor("h")]
        self.assertFalse(validate_source_frame(incomplete, now=now).publication_allowed)
        nan_frame = frame.copy(); nan_frame.iloc[3, nan_frame.columns.get_loc("close")] = np.nan
        self.assertFalse(validate_source_frame(nan_frame, now=now).publication_allowed)
        inf_frame = frame.copy(); inf_frame.iloc[4, inf_frame.columns.get_loc("high")] = np.inf
        self.assertFalse(validate_source_frame(inf_frame, now=now).publication_allowed)

    def test_missing_candle_is_visible_without_silent_repair(self):
        now = pd.Timestamp("2026-06-21T10:30:00Z")
        frame = self.frame(now=now)
        removable = next(ts for ts in frame.index[2:-2] if 1 <= ts.weekday() <= 3 and 2 <= ts.hour <= 20)
        frame = frame.drop(removable)
        report = validate_source_frame(frame, now=now)
        item = next(row for row in report.constraints if row.constraint_name == "expected_h1_frequency")
        self.assertEqual(item.status, "FAIL")
        self.assertGreater(item.failed_rows, 0)
        self.assertTrue(report.publication_allowed)  # warning, not fabricated repair

    def test_canonical_temporal_and_probability_validation(self):
        canonical = self.canonical("2026-06-21T09:00:00Z")
        report = validate_canonical_payload(canonical, now="2026-06-21T10:30:00Z")
        self.assertTrue(report.publication_allowed, report.failed_constraints)
        bad = self.canonical("2026-06-21T10:00:00Z")
        bad["reliability"]["unsafe_probability"] = 140
        self.assertFalse(validate_canonical_payload(bad, now="2026-06-21T10:30:00Z").publication_allowed)

    def test_cpa_hac_determinism_future_append_invariance_and_sparse_history(self):
        canonical, methods = self.settled()
        combined = pd.concat([canonical.assign(method="canonical"), methods], ignore_index=True, sort=False)
        one = evaluate_conditional_predictive_ability(combined, minimum_samples=24, source_generation_id="G")
        two = evaluate_conditional_predictive_ability(combined, minimum_samples=24, source_generation_id="G")
        signature = lambda result: [(r["condition_name"], r["condition_value"], r["loss_name"], r["settled_sample_count"], r["mean_loss_difference"], r["p_value"], r["evidence_status"]) for r in result["rows"]]
        self.assertEqual(signature(one), signature(two))
        future = combined.iloc[[0]].copy(); future["record_status"] = "PENDING"; future["target_time"] = pd.Timestamp("2030-01-01T00:00:00Z")
        appended = evaluate_conditional_predictive_ability(pd.concat([combined, future], ignore_index=True), minimum_samples=24, source_generation_id="G")
        self.assertEqual(signature(one), signature(appended))
        sparse = evaluate_conditional_predictive_ability(combined.head(8), minimum_samples=24)
        self.assertTrue(all(r["evidence_status"] == "INSUFFICIENT_CONDITIONAL_EVIDENCE" for r in sparse["rows"]))

    def test_spa_bootstrap_determinism_empty_challenger_and_second_window_gate(self):
        panel = pd.DataFrame({"canonical": np.repeat(0.2, 80), "challenger": np.repeat(0.1, 80)})
        kwargs = dict(minimum_samples=24, bootstrap_iterations=49, source_generation_id="G", calibration_pass=True, regime_catastrophe_pass=True, resource_budget_pass=True, second_window_pass=True)
        one = evaluate_superior_predictive_ability(panel, **kwargs)
        two = evaluate_superior_predictive_ability(panel, **kwargs)
        self.assertEqual(one["row"]["spa_p_value"], two["row"]["spa_p_value"])
        self.assertTrue(one["promotion_allowed"])
        blocked = evaluate_superior_predictive_ability(panel, **{**kwargs, "second_window_pass": False})
        self.assertFalse(blocked["promotion_allowed"])
        empty = evaluate_superior_predictive_ability(pd.DataFrame({"canonical": [1, 2, 3]}))
        self.assertEqual(empty["status"], "INSUFFICIENT_EVIDENCE")

    def test_covariate_shift_ess_overlap_and_weight_concentration_safeguards(self):
        canonical, _ = self.settled()
        supported = build_covariate_shift_conformal(canonical, current_covariates={"session": "ASIA", "major_regime": "RANGE"}, minimum_rows=24, minimum_ess=20)
        self.assertEqual(supported["horizons"]["1h"]["status"], "SHADOW_WEIGHTED_CONFORMAL")
        poor = build_covariate_shift_conformal(canonical, current_covariates={"session": "MARS", "major_regime": "UNSEEN"}, minimum_rows=24, minimum_ess=20)
        self.assertEqual(poor["horizons"]["1h"]["status"], "FALLBACK_TO_CANONICAL_INTERVAL")
        concentrated = build_covariate_shift_conformal(canonical.head(5), current_covariates={"session": "ASIA", "major_regime": "RANGE"}, minimum_rows=24, minimum_ess=20)
        self.assertFalse(concentrated["horizons"]["1h"]["safeguards"]["minimum_rows_pass"])

    def test_fixed_share_normalization_caps_floors_chronology_and_idempotency(self):
        updated = fixed_share_update({}, {"a": 0.1, "b": 1.0, "c": 2.0}, settlement_id="S1", settled_at="2026-06-21T09:00:00Z", minimum_weight=0.05, maximum_weight=0.80, maximum_hourly_weight_change=0.10)
        self.assertAlmostEqual(sum(updated["weights"].values()), 1.0, places=10)
        self.assertTrue(all(0.05 <= value <= 0.80 for value in updated["weights"].values()))
        self.assertLessEqual(updated["comparison"]["maximum_absolute_change"], 0.1000001)
        duplicate = fixed_share_update(updated["state"], {"a": 0.1, "b": 1.0, "c": 2.0}, settlement_id="S1", settled_at="2026-06-21T09:00:00Z")
        self.assertEqual(duplicate["status"], "IDEMPOTENT_DUPLICATE_IGNORED")
        older = fixed_share_update(updated["state"], {"a": 0.1, "b": 1.0, "c": 2.0}, settlement_id="S0", settled_at="2026-06-21T08:00:00Z")
        self.assertEqual(older["status"], "NON_CHRONOLOGICAL_SETTLEMENT_IGNORED")

    def test_bounded_monitoring_statistics(self):
        counter = ExponentialHistogramCounter(window_size=128)
        exact = []
        for i in range(500):
            event = i % 3 == 0
            exact.append(event); counter.update(event)
        exact_window = sum(exact[-128:])
        self.assertLessEqual(abs(counter.estimate() - exact_window), 16)
        self.assertLess(len(counter.buckets), 32)

        sketch = BoundedDDSketch(relative_error=0.01, exact_threshold=32, recent_raw_limit=20)
        for value in range(1, 1001): sketch.add(value)
        q90 = sketch.quantile(0.90)
        self.assertIsNotNone(q90)
        self.assertLessEqual(abs(q90 - 900) / 900, 0.03)
        self.assertEqual(len(sketch.recent), 20)

    def test_atomic_custom_tables_idempotency_rollback_and_previous_valid_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "canonical.sqlite3"
            good = build_run_snapshot(self.canonical("2026-06-21T09:00:00Z", "GOOD", 1))
            bundle = {BUNDLE_KEY: {"ml_production_readiness_history": [{"evaluation_id": "E1", "evaluated_at": "2026-06-21T10:00:00Z", "overall_readiness_score": 70, "critical_failure_count": 0, "warning_count": 1, "promotion_allowed": False}]}}
            commit_snapshot(good, db_path=db, history_bundle=bundle)
            commit_snapshot(good, db_path=db, history_bundle=bundle)
            conn = sqlite3.connect(db)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM ml_production_readiness_history").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0], 1)
            conn.close()
            bad = build_run_snapshot(self.canonical("2026-06-21T10:00:00Z", "BAD", 2))
            with self.assertRaises(RuntimeError):
                commit_snapshot(bad, db_path=db, fail_after_stage=True, history_bundle=bundle)
            latest = latest_completed(db_path=db)
            self.assertEqual(latest.get("run_id"), "GOOD")
            conn = sqlite3.connect(db)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM runs WHERE run_id='BAD'").fetchone()[0], 0)
            conn.close()

    def test_end_to_end_layer_preserves_existing_direction_and_is_bounded(self):
        now = pd.Timestamp("2026-06-21T10:30:00Z")
        frame = self.frame(now=now)
        validation = validate_source_frame(frame, now=now)
        settled, methods = self.settled()
        canonical = self.canonical(frame.index[-1].isoformat())
        before = dict(canonical["final_decision"])
        start = time.perf_counter()
        output, bundle, summary = build_research_validation_transaction(canonical, completed_h1=frame, settled_predictions=settled, settled_method_predictions=methods, preflight_validation=validation, previous={})
        elapsed = time.perf_counter() - start
        self.assertEqual(output["final_decision"], before)
        self.assertFalse(output["research_validation_20260621"]["direction_reversal_allowed"])
        self.assertFalse(output["research_validation_20260621"]["promotion_allowed"])
        self.assertIn(BUNDLE_KEY, bundle)
        self.assertLess(elapsed, 5.0)
        self.assertFalse(summary["protected_calculation_changed"])

    def test_closed_tab_and_rerun_static_safety(self):
        root = Path(__file__).resolve().parents[1]
        orchestrator = (root / "core" / "settings_run_orchestrator_20260617.py").read_text(encoding="utf-8")
        self.assertEqual(orchestrator.count("build_research_validation_transaction("), 1)
        self.assertIn("before atomic canonical publication", orchestrator)
        for folder in (root / "tabs", root / "ui"):
            for path in folder.rglob("*.py"):
                self.assertNotIn("build_research_validation_transaction(", path.read_text(encoding="utf-8", errors="ignore"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
