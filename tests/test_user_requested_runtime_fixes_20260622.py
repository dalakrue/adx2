from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from core.ai_intent_router import detect_intent
from core.market_time_freshness_20260622 import latest_frame_time, market_time_snapshot
from core.prediction_ledger_20260617 import PredictionLedger

ROOT = Path(__file__).resolve().parents[1]


class UserRequestedRuntimeFixesTests(unittest.TestCase):
    def test_prediction_outcomes_table_self_heals(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "ledger.sqlite3"
            ledger = PredictionLedger(db)
            with sqlite3.connect(db) as conn:
                conn.execute("DROP TABLE prediction_outcomes")
            index = pd.date_range("2026-06-22 00:00", periods=3, freq="h", tz="UTC")
            frame = pd.DataFrame(
                {"open": [1.0] * 3, "high": [1.1] * 3, "low": [0.9] * 3, "close": [1.0] * 3},
                index=index,
            )
            result = ledger.settle_pending_outcomes(frame)
            with sqlite3.connect(db) as conn:
                exists = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='prediction_outcomes'"
                ).fetchone()[0]
            self.assertTrue(result["ok"])
            self.assertEqual(exists, 1)

    def test_index_time_and_separate_broker_myanmar_clocks(self):
        frame = pd.DataFrame(
            {"close": [1.1, 1.2]},
            index=pd.date_range("2026-06-22 00:00", periods=2, freq="h", tz="UTC"),
        )
        state = {
            "timeframe": "H1",
            "last_df": frame,
            "mt5_broker_utc_offset_hours_20260622": 10.0,
            "source": "MT5",
        }
        self.assertEqual(latest_frame_time(frame), pd.Timestamp("2026-06-22 01:00", tz="UTC"))
        snap = market_time_snapshot(state, frame=frame)
        self.assertIn("11:00:00", snap["latest_loaded_broker_display"])
        self.assertIn("07:30:00", snap["latest_loaded_myanmar_display"])
        self.assertIn("UTC+6:30", snap["current_myanmar_display"])

    def test_field1_rebuilds_hour_from_broker_clock(self):
        stub = types.ModuleType("streamlit")
        stub.session_state = {}
        path = ROOT / "ui" / "lunch_four_core_fields_20260619.py"
        spec = importlib.util.spec_from_file_location("_lunch_clock_test_module", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"streamlit": stub}):
            assert spec and spec.loader
            spec.loader.exec_module(module)
        frame = pd.DataFrame({
            "Time": [pd.Timestamp("2026-06-22 02:00", tz="UTC")],
            "Date": ["stale"], "Weekday": ["stale"], "Hour": ["02:00"], "Decision": ["WAIT"],
        })
        display = module._display_clock_frame(
            frame,
            state={"mt5_broker_utc_offset_hours_20260622": 10.0},
            broker_clock=True,
        )
        self.assertEqual(display.iloc[0]["Hour"], "12:00")
        self.assertIn("Broker Time (UTC+10)", display.columns)
        self.assertIn("Myanmar Time (UTC+6:30)", display.columns)

    def test_ai_intents_are_question_specific(self):
        cases = {
            "What is my broker time?": "market_time",
            "What TP and SL should I use?": "tp_sl_guidance",
            "Why is reliability low?": "reliability_explanation",
            "Which hour has best priority?": "priority_ranking",
            "What price is forecast in three hours?": "price_forecast",
        }
        for question, expected in cases.items():
            self.assertEqual(detect_intent(question)["intent"], expected)

    def test_menu_has_one_copy_owner_and_touchable_component(self):
        popup = (ROOT / "ui" / "liquid_menu_popup_20260615.py").read_text(encoding="utf-8")
        runtime = popup.split("def _render_runtime_actions", 1)[1].split("if hasattr(st, \"fragment\")", 1)[0]
        self.assertNotIn("render_direct_canonical_copy_buttons", runtime)
        self.assertIn("_render_copy_actions(key)", popup)
        copy_tools = (ROOT / "ui" / "copy_tools.py").read_text(encoding="utf-8")
        self.assertIn("pointer-events:auto!important", copy_tools)
        self.assertIn("touch-action:manipulation", copy_tools)
        self.assertIn("addEventListener('click'", copy_tools)


if __name__ == "__main__":
    unittest.main()
