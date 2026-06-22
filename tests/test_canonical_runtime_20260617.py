from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from core.canonical_runtime_20260617 import (
    CANONICAL_KEY,
    GENERATION_KEY,
    build_runtime_context,
    build_shared_adapter,
    component_matches_canonical,
    publish_canonical_atomically,
    validate_canonical_result,
)
from core.finnhub_validation_20260617 import classify_response, normalize_api_key, validate_key_format
from ui.mobile_low_heat_20260617 import LOW_HEAT_CSS, should_enable_full_autorefresh


def canonical_payload(run_id: str = "RUN-1", generation: int = 1) -> dict:
    candle = "2026-06-17T13:00:00+00:00"
    return {
        "schema_version": "2.0.0",
        "run_id": run_id,
        "calculation_generation": generation,
        "created_at": "2026-06-17T14:00:00+00:00",
        "expires_at": "2026-06-17T15:00:00+00:00",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "source": "TEST",
        "latest_completed_candle_time": candle,
        "data_signature": "sig-1",
        "model_version": "existing-models-v1",
        "calculation_version": "decision-product-20260617-v1",
        "calculation_status": "COMPLETED",
        "failure_reason": None,
        "market": {"latest_completed_candle_time": candle, "current_price": 1.15, "row_count": 600},
        "data_quality": {"status": "PASS", "score": 99},
        "regime": {"major_regime": "BULL_NORMAL", "alpha": 1.2, "delta": 0.3},
        "forecasts": {"selected_horizon": 3, "horizons": {"3h": {"direction": "BUY", "point_forecast": 1.151}}},
        "priority": {"score": 75, "label": "A"},
        "nlp": {"direction": "BUY", "reliability": 70},
        "reliability": {
            "score": 72,
            "validation_by_horizon": {"3h": {"status": "VALID"}},
            "calibration_by_horizon": {"3h": {"source": "TEST"}},
        },
        "drift": {"status": "STABLE"},
        "risk": {"risk_level": "MEDIUM"},
        "final_decision": {
            "final_decision": "BUY",
            "directional_market_view": "BUY",
            "less_risky_decision": "BUY",
            "selected_horizon": 3,
            "calibrated_confidence": 0.72,
        },
        "metadata": {},
    }


class CanonicalRuntimeTests(unittest.TestCase):
    def test_canonical_schema_validation(self):
        ok, errors = validate_canonical_result(canonical_payload())
        self.assertTrue(ok, errors)
        bad = canonical_payload()
        bad.pop("latest_completed_candle_time")
        self.assertFalse(validate_canonical_result(bad)[0])

    def test_atomic_publish_and_cross_tab_identity(self):
        state = {}
        table = pd.DataFrame([{
            "Time": pd.Timestamp("2026-06-17T13:00:00Z"), "Hour": "13:00",
            "Major Regime": "BULL_NORMAL", "Reliability %": 72,
            "Decision": "BUY", "KNN Priority": 2, "Greedy Priority": 3,
            "Priority Score": 81, "Less Risky Bias": "BUY",
        }])
        adapter = publish_canonical_atomically(state, canonical_payload(), priority_table=table)
        self.assertEqual(state[CANONICAL_KEY]["run_id"], adapter["run_id"])
        self.assertEqual(state[GENERATION_KEY], adapter["calculation_generation"])
        for component in (adapter["market"], adapter["ai_grounding"], adapter["priority"]["adapter_meta"]):
            self.assertEqual(component.get("run_id"), "RUN-1")
            self.assertEqual(component.get("calculation_generation"), 1)

    def test_failed_run_preserves_last_valid(self):
        state = {}
        publish_canonical_atomically(state, canonical_payload("GOOD", 1), priority_table=pd.DataFrame())
        bad = canonical_payload("BAD", 2)
        bad["calculation_status"] = "FAILED"
        with self.assertRaises(ValueError):
            publish_canonical_atomically(state, bad, priority_table=pd.DataFrame())
        self.assertEqual(state[CANONICAL_KEY]["run_id"], "GOOD")
        self.assertEqual(state[GENERATION_KEY], 1)

    def test_symbol_timeframe_source_and_signature_mismatch(self):
        canonical = canonical_payload()
        component = {"run_id": "RUN-1", "symbol": "XAUUSD", "timeframe": "H1", "source": "TEST", "data_signature": "sig-1"}
        ok, reasons = component_matches_canonical(component, canonical)
        self.assertFalse(ok)
        self.assertIn("symbol mismatch", reasons)

    def test_priority_table_has_required_canonical_columns(self):
        table = pd.DataFrame([{
            "Time": "2026-06-17T13:00:00Z", "Hour": "13:00", "Major Regime": "BULL_NORMAL",
            "Regime True / False": "TRUE", "Reliability %": 70, "Decision": "BUY",
            "KNN Priority": 2, "Greedy Priority": 4, "Priority Score": 80, "Less Risky Bias": "BUY",
        }])
        adapter = build_shared_adapter({}, canonical_payload(), priority_table=table)
        actual = adapter["hourly_priority_table"]
        required = {
            "run_id", "generation", "candle time", "hour", "regime", "regime reliability",
            "prediction direction", "KNN score", "Greedy score", "combined score",
            "priority rank", "priority label", "less-risky bias", "conflict status", "data-quality status",
        }
        self.assertTrue(required.issubset(set(actual.columns)), required - set(actual.columns))

    def test_runtime_context_keeps_same_generation(self):
        state = {}
        publish_canonical_atomically(state, canonical_payload("RUN-X", 7), priority_table=pd.DataFrame())
        context = build_runtime_context(state, active_page="Lunch", active_subpage="Finder", phone_mode=True)
        self.assertEqual(context["canonical_run_id"], "RUN-X")
        self.assertEqual(context["canonical_generation"], 7)
        self.assertEqual(context["active_subpage"], "Finder")

    def test_shared_sync_only_once_per_normal_rerun(self):
        import core.adx_shared_sync_20260615 as sync
        fake_st = SimpleNamespace(session_state={"app_rerun_identifier_20260617": 9})
        with patch.dict(sys.modules, {"streamlit": fake_st}), patch.object(sync, "build_shared_calculation_result", return_value={"run_id": "R"}) as build:
            one = sync.ensure_shared_calculation_result(force=False)
            fake_st.session_state[sync.SHARED_KEY] = one
            two = sync.ensure_shared_calculation_result(force=False)
        self.assertEqual(one, two)
        self.assertEqual(build.call_count, 1)
        self.assertEqual(fake_st.session_state["shared_sync_calls_this_rerun_20260617"], 1)

    def test_mobile_low_heat_css_and_refresh_policy(self):
        for declaration in ("animation: none", "transition: none", "filter: none", "backdrop-filter: none"):
            self.assertIn(declaration, LOW_HEAT_CSS)
        self.assertFalse(should_enable_full_autorefresh({"phone_mode": True}, "Lunch", ""))
        self.assertFalse(should_enable_full_autorefresh({"phone_mode": False}, "Research", ""))
        self.assertTrue(should_enable_full_autorefresh({"phone_mode": True, "live_data_mode": True}, "Lunch", "PowerBI Projection"))

    def test_hidden_inner_tabs_are_not_eagerly_imported(self):
        root = Path(__file__).resolve().parents[1]
        router = (root / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
        safe_component = router.split("def _safe_component", 1)[1].split("def _home_ns", 1)[0]
        self.assertNotIn("_sync_shared", safe_component)
        self.assertNotIn("merged_hourly_regime_nlp_priority(days=10)", router)
        self.assertIn("render_lunch_25day_backtest_expander", router)

    def test_lunch_and_research_regime_nlp_history_are_25_days(self):
        root = Path(__file__).resolve().parents[1]
        lunch = (root / "tabs" / "final_lunch_upgrade_20260617.py").read_text(encoding="utf-8")
        research = (root / "tabs" / "research.py").read_text(encoding="utf-8")
        self.assertIn("25-Day Regime + NLP + KNN/Greedy History Table", lunch)
        orchestrator = (root / "core" / "settings_run_orchestrator_20260617.py").read_text(encoding="utf-8")
        self.assertIn("REGIME_NLP_HISTORY_DAYS = 25", orchestrator)
        self.assertIn("merged_hourly_regime_nlp_priority(days=REGIME_NLP_HISTORY_DAYS)", orchestrator)
        self.assertIn("25-Day Regime Prediction History + NLP", research)
        self.assertIn("window_days=25", research)
        self.assertNotIn("merged_hourly_regime_nlp_priority(days=10)", lunch)
        self.assertNotIn("merged_hourly_regime_nlp_priority(days=10)", research)

    def test_ai_assistant_is_canonical_grounded(self):
        root = Path(__file__).resolve().parents[1]
        ai = (root / "tabs" / "ai_assistant_lite.py").read_text(encoding="utf-8")
        self.assertIn('current["decision"] = g.get("decision"', ai)
        self.assertIn('m3.metric("History Window", "25 DAYS / H1")', ai)
        self.assertNotIn("merged_hourly_regime_nlp_priority(days=10)", ai)

    def test_finnhub_pure_validation_without_streamlit_or_network(self):
        self.assertEqual(normalize_api_key(" token=abcDEF123456 "), "abcDEF123456")
        self.assertTrue(validate_key_format("abcDEF123456")["ok"])
        self.assertEqual(classify_response(401, "Invalid API key")["kind"], "AUTH_INVALID")
        self.assertEqual(classify_response(403, "Premium access required")["kind"], "ENTITLEMENT_DENIED")
        self.assertEqual(classify_response(429, "API limit reached")["kind"], "RATE_LIMITED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
