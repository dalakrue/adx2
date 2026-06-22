from __future__ import annotations

import hashlib
import sys
import tempfile
import types
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from core.canonical_runtime_20260617 import (
    build_shared_adapter,
    publish_canonical_atomically,
    validate_operational_component,
)
from core.decision_product_engine_20260617 import build_decision_result, serialize_result
from core.full_metric_canonical_adapter_20260618 import (
    apply_canonical_confirmations,
    build_full_metric_authority,
    enrich_canonical_payload,
)
from core.prediction_ledger_20260617 import PredictionLedger
from core.research_causality_20260618 import causal_binary_target, causal_news_asof, purged_time_order_split


PROTECTED_FULL_METRIC_SHA256 = "fe0797ab30f469f3ea748bc66a690b18a68aaf91306ac33c797bdcdcf6e60682"


def make_ohlc(n: int = 700, *, trend: float = 0.000025) -> pd.DataFrame:
    end = pd.Timestamp("2026-06-18T02:00:00Z")
    time = pd.date_range(end=end, periods=n, freq="h", tz="UTC")
    rng = np.random.default_rng(20260618)
    close = 1.15 + np.cumsum(rng.normal(trend, 0.00008, n))
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + 0.00009
    low = np.minimum(open_, close) - 0.00009
    return pd.DataFrame({"time": time, "open": open_, "high": high, "low": low, "close": close, "volume": 100})


def import_full_metric_module():
    # The calculation module only needs Streamlit at render time. A minimal stub
    # keeps this pure calculation test runnable in clean CI environments.
    if "streamlit" not in sys.modules:
        stub = types.ModuleType("streamlit")
        stub.session_state = {}
        sys.modules["streamlit"] = stub
    import tabs.eurusd_h1_matrix as module
    return module


class FullMetricCanonicalSyncTests(unittest.TestCase):
    def test_protected_full_metric_file_is_byte_unchanged(self):
        path = Path(__file__).resolve().parents[1] / "tabs" / "eurusd_h1_matrix.py"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), PROTECTED_FULL_METRIC_SHA256)

    def test_adapter_preserves_full_metric_values_and_complete_history(self):
        module = import_full_metric_module()
        h1 = make_ohlc()
        result = module.build_tables(h1, pd.DataFrame())
        self.assertTrue(result["ok"])
        authority = build_full_metric_authority(
            result, h1, legacy_shared={"reliability": {"score": 72}, "regime": {"current": "BULL_NORMAL"}},
            data_quality_status="PASS",
        )
        snapshot = authority["snapshot"]
        scores = result["scores"]
        self.assertEqual(snapshot["master_score"], scores["Master /10"])
        self.assertEqual(snapshot["entry_score"], scores["Entry /10"])
        self.assertEqual(snapshot["full_metric_direction"], scores["Direction"])
        self.assertEqual(snapshot["full_metric_current_row"]["Decision"], scores["Decision"])
        self.assertEqual(len(snapshot["full_metric_history"]), len(result["history"]))
        self.assertEqual(len(snapshot["reverse_10_current"]), 10)
        self.assertEqual(set(snapshot["reverse_10_history"]), set(result["history_by_factor"]))

    def test_priority_base_uses_requested_full_metric_weighting(self):
        module = import_full_metric_module()
        h1 = make_ohlc()
        result = module.build_tables(h1, pd.DataFrame())
        authority = build_full_metric_authority(
            result, h1, legacy_shared={"reliability": {"score": 70}}, data_quality_status="PASS"
        )
        row = authority["priority_table"].iloc[0]
        expected = (
            row["Master /10"] * 10 * 0.30
            + row["Entry /10"] * 10 * 0.25
            + max(row["BUY /10"], row["SELL /10"]) * 10 * 0.15
            + row["Hold /10"] * 10 * 0.10
            + row["TP /10"] * 10 * 0.10
            + (10 - row["Exit Risk /10"]) * 10 * 0.10
        )
        self.assertAlmostEqual(row["Base Full Metric Score"], expected, places=8)
        self.assertLessEqual(len(authority["top_two_daily_candidates"]), 2)

    def test_current_candidate_qualifies_only_after_validated_confirmation(self):
        module = import_full_metric_module()
        h1 = make_ohlc(trend=0.00006)
        result = module.build_tables(h1, pd.DataFrame())
        # Force a valid protected current direction/decision in the test fixture;
        # this modifies only the returned fixture, never the protected formulas.
        direction = "BUY"
        result["scores"].update({"Direction": direction, "Decision": "STRONG"})
        result["history"].loc[result["history"].index[0], ["Direction", "Decision"]] = [direction, "STRONG"]
        authority = build_full_metric_authority(
            result, h1, legacy_shared={"reliability": {"score": 72}}, data_quality_status="PASS"
        )
        before = authority["priority_table"]
        latest_mask = pd.to_datetime(before["Time"], utc=True).eq(h1["time"].iloc[-1])
        self.assertNotIn("QUALIFIED ENTRY", set(before.loc[latest_mask, "Qualification Status"]))
        canonical = {
            "latest_completed_candle_time": h1["time"].iloc[-1].isoformat(),
            "final_decision": {
                "directional_market_view": direction,
                "tradeability_decision": direction,
                "final_decision": direction,
                "expected_value": 0.0002,
                "blocking_reasons": [],
            },
            "reliability": {"score": 72},
            "nlp": {"conflict_level": "NONE"},
            "data_quality": {"status": "PASS"},
        }
        after = apply_canonical_confirmations(authority, canonical)["priority_table"]
        current = after.loc[pd.to_datetime(after["Time"], utc=True).eq(h1["time"].iloc[-1])].iloc[0]
        self.assertEqual(current["Qualification Status"], "QUALIFIED ENTRY")
        self.assertEqual(current["Direction"], direction)

    def test_forecast_and_m1_cannot_reverse_full_metric_h1(self):
        h1 = make_ohlc()
        legacy = {
            "current": {"forecast_close": float(h1.close.iloc[-1] - 0.001), "prediction_direction": "SELL", "priority_score": 80},
            "regime": {"current": "BEAR_NORMAL"},
            "reliability": {"score": 70},
            "powerbi": {"forecast_close": float(h1.close.iloc[-1] - 0.001), "confidence": 75},
            "priority": {"best": {"Priority Score": 80}},
            "nlp": {"summary": {"nlp_direction": "SELL", "reliability": 80}},
        }
        with tempfile.TemporaryDirectory() as td:
            ledger = PredictionLedger(Path(td) / "ledger.sqlite3")
            result = build_decision_result(
                legacy_shared=legacy, ohlc=h1, symbol="EURUSD", timeframe="H1", source="TEST",
                ledger=ledger, calculation_generation=1,
                full_metric_snapshot={
                    "full_metric_direction": "BUY", "tradeability_decision": "BUY",
                    "blocking_reasons": [], "m1_timing_status": "WAIT FOR CONFIRMATION",
                    "current_major_regime": "BULL_NORMAL", "master_score": 8.1, "entry_score": 7.8,
                    "top_two_daily_candidates": [],
                },
                now=pd.Timestamp("2026-06-18T04:00:00Z"),
            )
        self.assertEqual(result.final_decision.directional_market_view, "BUY")
        self.assertEqual(result.final_decision.final_decision, "WAIT")
        self.assertNotEqual(result.final_decision.final_decision, "SELL")
        self.assertFalse(any("M1" in reason for reason in result.final_decision.blocking_reasons))
        self.assertTrue(any("M1" in reason for reason in result.final_decision.supporting_reasons))

    def test_all_operational_adapters_share_exact_identity(self):
        h1 = make_ohlc(300)
        with tempfile.TemporaryDirectory() as td:
            ledger = PredictionLedger(Path(td) / "ledger.sqlite3")
            result = build_decision_result(
                legacy_shared={"reliability": {"score": 65}, "current": {}, "priority": {}, "nlp": {}},
                ohlc=h1, symbol="EURUSD", timeframe="H1", source="TEST", ledger=ledger,
                calculation_generation=4,
                full_metric_snapshot={
                    "full_metric_direction": "WAIT", "tradeability_decision": "WAIT", "blocking_reasons": ["test"],
                    "m1_timing_status": "CONFIRM", "current_major_regime": "RANGE", "master_score": 5.0,
                    "entry_score": 5.0, "top_two_daily_candidates": [],
                },
                now=pd.Timestamp("2026-06-18T04:00:00Z"),
            )
        base = serialize_result(result)
        authority = {
            "snapshot": {
                "full_metric_direction": "WAIT", "tradeability_decision": "WAIT", "full_metric_current_row": {},
                "full_metric_history": [], "reverse_10_current": [], "reverse_10_history": {},
                "canonical_priority_table": [], "top_two_daily_candidates": [],
            },
            "priority_table": pd.DataFrame(), "top_two_daily_candidates": [],
        }
        canonical = enrich_canonical_payload(base, authority)
        state = {}
        adapter = publish_canonical_atomically(state, canonical, priority_table=pd.DataFrame())
        for name in ("decision", "regime", "priority", "reliability", "powerbi", "nlp", "data_mining", "ai_grounding"):
            ok, errors = validate_operational_component(adapter[name], canonical)
            self.assertTrue(ok, (name, errors))
        self.assertEqual(adapter["ai_grounding"]["first_decision"], canonical["final_decision"]["final_decision"])


class ResearchCausalityTests(unittest.TestCase):
    def test_future_target_final_row_is_unlabeled(self):
        target = causal_binary_target(pd.Series([1.0, 2.0, 1.5, 1.7]), horizon=1)
        self.assertEqual(target.iloc[:3].tolist(), [1, 0, 1])
        self.assertTrue(pd.isna(target.iloc[-1]))

    def test_walk_forward_split_is_ordered_and_purged(self):
        frame = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=120, freq="h"), "target": [0, 1] * 60})
        train, test = purged_time_order_split(frame, target_col="target", train_fraction=0.8, purge_rows=2, minimum_train=20)
        self.assertFalse(train.empty)
        self.assertFalse(test.empty)
        self.assertLess(train["time"].max(), test["time"].min())
        original_positions = frame.set_index("time").index
        gap = original_positions.get_loc(test["time"].min()) - original_positions.get_loc(train["time"].max()) - 1
        self.assertGreaterEqual(gap, 4)

    def test_news_join_never_uses_future_publication(self):
        decisions = pd.DataFrame({"time": pd.to_datetime(["2026-06-18T10:00Z", "2026-06-18T12:00Z"])})
        news = pd.DataFrame({
            "published_at": pd.to_datetime(["2026-06-18T09:00Z", "2026-06-18T11:00Z", "2026-06-18T13:00Z"]),
            "headline": ["old", "middle", "future"],
        })
        merged = causal_news_asof(decisions, news, news_time_candidates=("published_at",))
        self.assertEqual(merged["headline"].tolist(), ["old", "middle"])
        self.assertTrue((merged["_news_publication_time"] <= merged["time"]).all())


class StaticPerformanceAndRoutingTests(unittest.TestCase):
    def test_renderers_are_read_only_and_aliases_are_preserved(self):
        root = Path(__file__).resolve().parents[1]
        router = (root / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
        regime = (root / "core" / "regime_sync_20260617.py").read_text(encoding="utf-8")
        nav = (root / "ui" / "antd_navigation_20260615.py").read_text(encoding="utf-8")
        dinner = (root / "tabs" / "dinner_unified_center_20260617.py").read_text(encoding="utf-8")
        self.assertNotIn("ensure_shared_calculation_result(force=True)", router)
        self.assertIn('settings_calculation_lock_20260617', regime)
        for alias in ('"Home": "Lunch"', '"Regime": "Lunch"', '"Doo Prime": "Morning"', '"Data Visualization": "Lunch"'):
            self.assertIn(alias, nav)
        self.assertNotIn("for key in st.session_state.keys()", dinner)


if __name__ == "__main__":
    unittest.main(verbosity=2)
