from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from core.ai_conversation_memory import MAX_ITEMS, MEMORY_KEY, remember
from core.ai_duplicate_guard_20260622 import prevent_duplicate_answer, similarity
from core.ai_intent_router import detect_intent
from core.history_sync_engine_20260622 import CORE_HISTORY_TABLES, ensure_core_history_rows, verify_core_history_commit
from core.shared_broker_time_20260622 import frame_to_shared_broker_clock, history_sync_status, shared_broker_time_provider
from services.canonical_exports import build_short_payload


def _canonical():
    return {
        "run_id": "run-v5",
        "canonical_calculation_id": "calc-v5",
        "calculation_generation": 5,
        "latest_completed_candle_time": "2026-06-22T07:00:00+00:00",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "master_score": 6.2,
        "entry_score": 6.8,
        "hold_safety": 5.9,
        "tp_quality": 6.1,
        "exit_risk": 3.4,
        "trend_capacity_remaining": 6.0,
        "regime": {"major_regime": "BULL_NORMAL"},
        "reliability": {"score": 74.0},
        "final_decision": {
            "final_decision": "BUY",
            "directional_market_view": "BUY",
            "calibrated_confidence": 72.0,
            "selected_tp": 1.165,
            "selected_sl": 1.158,
            "main_reason": "Current completed-generation evidence supports a cautious BUY.",
        },
        "forecasts": {
            "horizons": {
                "1h": {"point_forecast": 1.161, "direction": "BUY", "reliability": 70},
                "3h": {"point_forecast": 1.163, "direction": "BUY", "reliability": 72},
            }
        },
    }


def _summary():
    return {
        "calculation_id": "calc-v5",
        "identity": {
            "run_id": "run-v5",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "latest_completed_candle_time": "2026-06-22T07:00:00+00:00",
        },
        "decision": {"current_decision": "BUY", "direction": "BUY"},
        "scores": {
            "master": 6.2,
            "entry": 6.8,
            "hold": 5.9,
            "exit_risk": 3.4,
            "tp": 6.1,
            "trend_capacity_remaining": 6.0,
        },
        "regime": {"directional_regime": "BULL_NORMAL", "regime_reliability": 74.0},
        "projection": {"selected_horizon": 3, "projection_confidence": 72.0, "h3": 1.163},
        "priority": {
            "opportunity_quality": "A",
            "best_entry_hour": "07:00",
            "second_best_entry_hour": "08:00",
        },
    }


def test_shared_broker_time_is_canonical_first_and_not_wall_clock():
    state = {
        "mt5_broker_utc_offset_hours_20260622": 6,
        "last_df": pd.DataFrame({"time": ["2026-06-22T12:00:00Z"]}),
    }
    result = shared_broker_time_provider(state, canonical=_canonical())
    assert result["latest_broker_candle_utc_iso"] == "2026-06-22T07:00:00+00:00"
    assert result["shared_broker_time"].hour == 13
    assert result["timestamp_source"] == "canonical_completed_h1"


def test_history_display_and_sync_use_same_broker_clock():
    state = {"mt5_broker_utc_offset_hours_20260622": 6}
    frame = pd.DataFrame({"time": ["2026-06-22T06:00:00Z", "2026-06-22T07:00:00Z"], "value": [1, 2]})
    display = frame_to_shared_broker_clock(frame, state, canonical=_canonical())
    assert "Broker Time (UTC+6)" in display.columns
    assert display["Broker Time (UTC+6)"].iloc[-1].hour == 13
    sync = history_sync_status(state, history_frame=frame, canonical=_canonical())
    assert sync["synced"] is True
    assert sync["difference_minutes"] == 0.0


def test_core_history_fallback_rows_cover_all_required_histories():
    bundle = ensure_core_history_rows(_canonical(), {})
    assert set(CORE_HISTORY_TABLES).issubset(bundle)
    assert bundle["full_metric_overall_history"]
    assert bundle["reliability_conflict_history"]
    assert bundle["regime_overall_history"]
    assert len(bundle["powerbi_prediction_ledger"]) == 2


def test_commit_verification_reports_sync_and_missing_schema_safely(tmp_path: Path):
    db = tmp_path / "history.sqlite3"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE history_watermarks (table_name TEXT PRIMARY KEY, latest_completed_h1 TEXT, last_calculation_id TEXT, last_generation INTEGER, updated_at TEXT)"
    )
    for table in CORE_HISTORY_TABLES:
        conn.execute(
            "INSERT INTO history_watermarks VALUES (?,?,?,?,?)",
            (table, "2026-06-22T07:00:00+00:00", "calc-v5", 5, "2026-06-22T07:01:00+00:00"),
        )
    conn.commit(); conn.close()
    verified = verify_core_history_commit(_canonical(), db_path=db)
    assert verified["ok"] is True
    assert verified["status"] == "SYNCED"

    empty_db = tmp_path / "missing.sqlite3"
    missing = verify_core_history_commit(_canonical(), db_path=empty_db)
    assert missing["ok"] is False
    assert missing["status"] == "OUT OF SYNC"


def test_copy_short_has_exact_required_v5_fields_and_is_bounded():
    state = {
        "mt5_broker_utc_offset_hours_20260622": 6,
        "ai_assistant_last_answer_20260622": "BUY is supported, but reliability and exit risk still require caution.",
    }
    text, stats = build_short_payload(_canonical(), _summary(), {}, state)
    labels = (
        "Current Time:", "Decision:", "Direction:", "Regime:", "Reliability:", "Priority:",
        "Master Score:", "Entry Score:", "Hold Score:", "Exit Risk:", "TP Quality:",
        "Trend Capacity:", "PowerBI Projection:", "Best Entry Summary:", "Quick TP:",
        "Quick SL:", "Forecast Confidence:", "AI Summary:",
    )
    for label in labels:
        assert label in text
    assert stats.lines <= 40
    assert stats.characters <= 6000
    assert stats.estimated_tokens <= 1500
    assert "Broker UTC+6" in text


def test_ai_intents_restrict_relevant_modules():
    assert detect_intent("Should I buy now?")["intent"] == "entry_guidance"
    assert detect_intent("Should I exit now?")["intent"] == "exit_guidance"
    assert detect_intent("Which hour has best priority?")["intent"] == "priority_ranking"
    assert set(detect_intent("Should I buy now?")["required_sources"]) == {
        "decision", "scores", "regime", "reliability", "priority", "warnings"
    }


def test_duplicate_guard_uses_last_twenty_answers_and_regenerates_above_90_percent():
    state = {}
    base = "Current evidence supports WAIT because reliability is low and conflict is high."
    for index in range(25):
        remember(
            state,
            question=f"Question {index}",
            intent="decision_explanation",
            generation_id="calc-v5",
            evidence=[],
            status="PASS",
            answer=base if index == 24 else f"Distinct answer {index}",
        )
    assert MAX_ITEMS == 20
    assert len(state[MEMORY_KEY]) == 20
    assert similarity(base, base + " ") > 0.90
    guarded = prevent_duplicate_answer(
        state,
        question="What should I do now?",
        answer=base,
        intent="decision_explanation",
        evidence=[{"metric_name": "reliability", "metric_value": 41, "source_name": "Canonical reliability"}],
    )
    assert guarded["regenerated"] is True
    assert "Question-specific" in guarded["answer"] or "Focused evidence" in guarded["answer"] or "Current-generation" in guarded["answer"]
    assert "Reliability: 41" in guarded["answer"]


def test_copy_success_message_and_single_owner_guard_are_present():
    copy_source = Path("ui/copy_tools.py").read_text(encoding="utf-8")
    menu_source = Path("ui/liquid_menu_popup_20260615.py").read_text(encoding="utf-8")
    assert "Copied Successfully" in copy_source
    assert "navigator.clipboard.writeText" in copy_source
    assert "new7_main_menu_drawer_open" in menu_source
    assert "Copy Short and Copy Full are available in the open menu drawer" in menu_source
