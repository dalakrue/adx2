from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.ai_canonical_grounding_20260618 import format_grounded_answer
from core.operational_sync_20260618 import collect_sync_health, record_operational_error, synchronize_published_generation
from ui.nlp_research_panel import build_news_mining_summary

ROOT = Path(__file__).resolve().parents[1]


def test_one_generation_is_mirrored_to_all_operational_pages() -> None:
    state: dict = {}
    canonical = {
        "run_id": "R-18", "calculation_generation": 7, "data_signature": "SIG",
        "symbol": "EURUSD", "timeframe": "H1", "source": "test",
        "latest_completed_candle_time": "2026-06-18T08:00:00+00:00",
        "final_decision": {"final_decision": "BUY", "directional_market_view": "BUY", "less_risky_decision": "WAIT", "selected_horizon": 6},
    }
    adapter = {
        **{key: canonical[key] for key in ("run_id", "calculation_generation", "data_signature", "symbol", "timeframe", "source", "latest_completed_candle_time")},
        "current": {"decision": "BUY"},
        "nlp": {**{key: canonical[key] for key in ("run_id", "calculation_generation", "data_signature", "symbol", "timeframe", "source", "latest_completed_candle_time")}},
        "data_mining": {}, "powerbi": {}, "regime": {}, "reliability": {}, "full_metric_snapshot": {"regime_history": [1]},
    }
    table = pd.DataFrame([{"Time": canonical["latest_completed_candle_time"], "Priority Score": 8.0}])
    synchronize_published_generation(state, canonical, adapter, table)
    for key in ("lunch_synced_snapshot_20260618", "dinner_synced_snapshot_20260618", "finder_synced_snapshot_20260618", "research_synced_snapshot_20260618"):
        assert state[key]["run_id"] == "R-18"
        assert state[key]["calculation_generation"] == 7
    assert state["finder_readonly_priority_table_20260618"] is table


def test_error_ledger_is_bounded_and_deduplicates_repeated_rerun_faults() -> None:
    state: dict = {}
    record_operational_error(state, "Finder", RuntimeError("api_key=SECRET must not leak"))
    record_operational_error(state, "Finder", RuntimeError("api_key=SECRET must not leak"))
    rows = state["operational_error_ledger_20260618"]
    assert len(rows) == 1
    assert "SECRET" not in rows[0]["message"]


def test_question_aware_ai_keeps_local_answer_first_and_only_relevant_context() -> None:
    grounding = {
        "current_canonical_decision": "WAIT", "directional_market_view": "SELL", "less_risky_decision": "WAIT",
        "current_regime": "BEAR_NORMAL", "alpha": -0.2, "delta": -0.1, "entry_permission": "NO ENTRY / WAIT",
        "opportunity_rank": 2, "tp_sl_context": {"point": 1.15, "lower": 1.149, "upper": 1.152, "tp_quality": 6.5, "exit_risk": 4.0},
        "main_supporting_reasons": ["bear pressure"], "main_conflicts": ["news conflict"],
        "data_freshness": {"status": "CURRENT", "latest_completed_h1": "08:00", "generation": 7},
        "uncertainty_reliability": {"uncertainty_pct": 25, "error_estimate_pct": 0.04, "reliability_pct": 72},
    }
    answer = format_grounded_answer(grounding, "Use the 6H lower band as evidence, not a guaranteed TP.", question="What is my next 6 hour TP?")
    assert answer.startswith("Use the 6H lower band")
    assert "Canonical TP/SL evidence" in answer
    assert "1. Current canonical decision" not in answer


def test_news_mining_summary_is_shared_lightweight_and_ranked() -> None:
    table = pd.DataFrame([
        {"timestamp": "2026-06-18T08:00:00Z", "topic_name": "ECB", "nlp_direction": "SELL", "nlp_direction_score": -40, "nlp_reliability_score": 80, "eurusd_pair_relevance": 90},
        {"timestamp": "2026-06-18T07:00:00Z", "topic_name": "ECB", "nlp_direction": "SELL", "nlp_direction_score": -20, "nlp_reliability_score": 70, "eurusd_pair_relevance": 85},
        {"timestamp": "2026-06-17T07:00:00Z", "topic_name": "Fed", "nlp_direction": "BUY", "nlp_direction_score": 10, "nlp_reliability_score": 60, "eurusd_pair_relevance": 75},
    ])
    mined = build_news_mining_summary(table)
    assert mined["topic_summary"].iloc[0]["Topic"] == "ECB"
    assert int(mined["topic_summary"].iloc[0]["Articles"]) == 2
    assert set(mined) == {"topic_summary", "daily_summary", "direction_summary"}


def test_phone_and_menu_css_keep_metrics_and_popup_compact() -> None:
    mobile = (ROOT / "ui" / "mobile_css.py").read_text(encoding="utf-8")
    menu = (ROOT / "ui" / "liquid_menu_popup_20260615.py").read_text(encoding="utf-8")
    runner = (ROOT / "core" / "app" / "runner.py").read_text(encoding="utf-8")
    assert "min-height:76px" in mobile
    assert "overflow-wrap:anywhere" in mobile
    assert "width:clamp(124px,10vw,148px)" in menu.replace(" ", "") and "width:128px" in menu
    assert "if not phone_mode" in runner
    assert "logic_first_mobile_20260618" in runner


def test_copy_short_contract_is_decision_first_and_bounded() -> None:
    source = (ROOT / "ui" / "home_master_control_bar_20260615.py").read_text(encoding="utf-8")
    assert '"next_1_hour_tp_context"' in source
    assert '"next_6_hour_tp_context"' in source
    assert '"less_risky_6h_bias"' in source
    assert '"character_limit": 4000' in source and "return text[:" not in source
