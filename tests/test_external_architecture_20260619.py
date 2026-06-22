from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile

import pandas as pd
import pytest

from core.operational_sync_20260618 import ensure_generation_consistency, synchronize_published_generation
from core.performance_store_20260619 import persist_frame, query_frame
from core.snapshot_schema_20260619 import build_run_snapshot, canonical_checksum, verify_display_generation
from services.canonical_snapshot_store import commit_snapshot, latest_completed
from services.position_sizing import PositionSizingInputs, calculate_position_size, floor_to_lot_step
from services.canonical_exports import all_text as _all_text, short_text as _short_text

ROOT = Path(__file__).resolve().parents[1]


def canonical(run_id: str = "R-19", generation: int = 19) -> dict:
    candle = "2026-06-19T07:00:00+00:00"
    return {
        "schema_version": "2.0.0",
        "run_id": run_id,
        "canonical_calculation_id": run_id,
        "calculation_generation": generation,
        "created_at": "2026-06-19T08:00:00+00:00",
        "calculation_started_at": "2026-06-19T07:59:00+00:00",
        "calculation_completed_at": "2026-06-19T08:00:00+00:00",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "source": "TEST",
        "latest_completed_candle_time": candle,
        "data_signature": "sig-19",
        "calculation_status": "COMPLETED",
        "market": {"latest_completed_candle_time": candle, "current_price": 1.15},
        "final_decision": {
            "final_decision": "BUY",
            "directional_market_view": "BUY",
            "less_risky_decision": "BUY",
            "error_estimate_pct": 4.0,
            "blocking_reasons": [],
        },
        "regime": {"major_regime": "BULL_NORMAL"},
        "forecasts": {"selected_horizon": 3},
        "reliability": {"score": 72},
        "priority": {"score": 81, "label": "A"},
        "nlp": {"direction": "BUY"},
        "risk_plan": {"status": "SAFE", "recommended_lots": 0.03},
        "master_score": 6.1,
        "entry_score": 6.5,
        "hold_safety": 6.0,
        "tp_quality": 5.8,
        "exit_risk": 3.2,
    }


def summary(c: dict) -> dict:
    return {
        "identity": {
            "run_id": c["run_id"],
            "calculation_generation": c["calculation_generation"],
            "symbol": c["symbol"],
            "timeframe": c["timeframe"],
            "latest_completed_candle_time": c["latest_completed_candle_time"],
        },
        "decision": {"current_decision": "BUY", "less_risky_bias": "BUY", "main_reason": "Aligned"},
        "scores": {"master": 6.1, "entry": 6.5, "hold": 6.0, "tp": 5.8, "exit_risk": 3.2},
        "priority": {"opportunity_quality": "A", "current_rank": 2},
        "regime": {"directional_regime": "BULL_NORMAL", "regime_reliability": 72.0},
        "uncertainty": {"combined": 18.0},
    }


def test_position_sizing_600_one_percent_20_pips():
    result = calculate_position_size(PositionSizingInputs(balance=600, risk_pct=1, stop_loss_pips=20))
    assert result.risk_dollars == pytest.approx(6.0)
    assert result.recommended_lots == pytest.approx(0.03)
    assert result.planned_dollar_loss == pytest.approx(6.0)


def test_position_sizing_600_one_percent_15_pips_rounds_down():
    result = calculate_position_size(PositionSizingInputs(balance=600, risk_pct=1, stop_loss_pips=15))
    assert result.raw_lots == pytest.approx(0.04)
    assert result.recommended_lots == pytest.approx(0.04)


def test_lot_step_round_down_never_rounds_up():
    assert floor_to_lot_step(0.039999, 0.01) == pytest.approx(0.03)
    assert floor_to_lot_step(0.049, 0.01) == pytest.approx(0.04)
    assert floor_to_lot_step(0.019, 0.005) == pytest.approx(0.015)


def test_minimum_lot_skip():
    result = calculate_position_size(PositionSizingInputs(balance=600, risk_pct=0.5, stop_loss_pips=40, broker_minimum_lot=0.01))
    assert result.raw_lots == pytest.approx(0.0075)
    assert result.recommended_lots == 0
    assert result.minimum_lot_exceeds_allowance
    assert result.status == "BLOCK"
    assert "SKIP" in result.reason


def test_margin_estimate_001_lot_at_115_and_100_leverage():
    result = calculate_position_size(PositionSizingInputs(balance=600, current_eurusd_price=1.15, leverage=100, risk_pct=1, stop_loss_pips=60))
    assert result.recommended_lots == pytest.approx(0.01)
    assert result.margin_estimate == pytest.approx(11.50)


def test_related_entries_share_one_aggregate_budget():
    result = calculate_position_size(PositionSizingInputs(balance=600, risk_pct=1, stop_loss_pips=20, existing_combined_open_risk_pct=0.4))
    assert sum(result.scale_in_splits) == pytest.approx(result.recommended_lots)
    assert all(x <= result.recommended_lots for x in result.scale_in_splits)
    assert result.combined_open_risk_pct == pytest.approx(1.4)
    assert result.scale_in_splits != (0.03, 0.03, 0.03)


def test_snapshot_is_frozen_and_checksumed():
    c = canonical()
    c["checksum"] = canonical_checksum(c)
    snapshot = build_run_snapshot(c)
    assert snapshot.checksum == c["checksum"]
    assert snapshot.generation == 19
    with pytest.raises(FrozenInstanceError):
        snapshot.generation = 20  # type: ignore[misc]
    with pytest.raises(TypeError):
        snapshot.metrics["master"] = 99  # type: ignore[index]


def test_atomic_commit_and_rollback_keeps_previous_completed_snapshot():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "runtime.sqlite3"
        first = build_run_snapshot({**canonical("GOOD", 1), "checksum": canonical_checksum(canonical("GOOD", 1))})
        commit_snapshot(first, db_path=db)
        second_data = canonical("BAD", 2)
        second = build_run_snapshot({**second_data, "checksum": canonical_checksum(second_data)})
        with pytest.raises(RuntimeError):
            commit_snapshot(second, db_path=db, fail_after_stage=True)
        latest = latest_completed(db_path=db)
        assert latest["run_id"] == "GOOD"
        assert latest["generation"] == 1
        conn = sqlite3.connect(db)
        try:
            assert conn.execute("SELECT COUNT(*) FROM runs WHERE run_id='BAD'").fetchone()[0] == 0
        finally:
            conn.close()


def test_generation_consistency_repairs_all_read_only_page_aliases():
    c = canonical("SYNC", 7)
    adapter = {"run_id": "SYNC", "calculation_generation": 7, "current": {}, "nlp": {}, "data_mining": {}, "powerbi": {}, "regime": {}, "reliability": {}, "full_metric_snapshot": {"ok": True}}
    state = {"canonical_decision_result_20260617": c, "adx_shared_calc_result_20260615": adapter}
    sync = ensure_generation_consistency(state)
    assert sync["ok"]
    for key in (
        "lunch_synced_snapshot_20260618", "finder_synced_snapshot_20260618", "dinner_synced_snapshot_20260618",
        "morning_synced_snapshot_20260619", "data_visualization_synced_snapshot_20260619",
        "train_data_synced_snapshot_20260619", "backtest_synced_snapshot_20260619",
        "profile_synced_snapshot_20260619", "engine_synced_snapshot_20260619", "pre_original_synced_snapshot_20260619",
    ):
        assert state[key]["run_id"] == "SYNC"
        assert state[key]["calculation_generation"] == 7
    guard = verify_display_generation(state, state["finder_synced_snapshot_20260618"])
    assert guard["ok"]


def test_database_filter_pagination_and_projection():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "frames.sqlite3"
        frame = pd.DataFrame({
            "Time": pd.date_range("2026-06-18", periods=48, freq="h", tz="UTC").astype(str),
            "Hour": [f"{i % 24:02d}:00" for i in range(48)],
            "Direction": ["BUY" if i % 2 == 0 else "SELL" for i in range(48)],
            "Payload": range(48),
        })
        persist_frame("C1", "finder", frame, db_path=db)
        page = query_frame("C1", "finder", columns=["Time", "Direction"], limit=5, offset=5, order_by="Time", descending=False, where_equals={"Direction": "BUY"}, date_equals={"Time": "2026-06-18"}, db_path=db)
        assert list(page.columns) == ["Time", "Direction"]
        assert len(page) == 5
        assert set(page["Direction"]) == {"BUY"}
        assert all(str(x).startswith("2026-06-18") for x in page["Time"])


def test_copy_short_and_all_are_same_generation():
    c = canonical("COPY", 11)
    c["checksum"] = canonical_checksum(c)
    plan = calculate_position_size(PositionSizingInputs(balance=600, risk_pct=1, stop_loss_pips=20)).to_dict()
    short = _short_text(c, summary(c), plan)
    all_text = _all_text(c, summary(c), plan)
    assert "COPY / 11" in short
    assert '"run_id": "COPY"' in all_text
    assert '"generation": 11' in all_text
    assert c["checksum"] in short and c["checksum"] in all_text


def test_timezone_inputs_do_not_raise_or_mix_naive_aware_comparisons():
    aware = canonical_checksum({"at": datetime(2026, 6, 19, 8, tzinfo=timezone.utc)})
    naive = canonical_checksum({"at": datetime(2026, 6, 19, 8)})
    assert len(aware) == len(naive) == 64


def test_active_ui_wiring_and_mobile_controls():
    lunch = (ROOT / "tabs/final_lunch_upgrade_20260617.py").read_text(encoding="utf-8")
    finder = (ROOT / "tabs/antd_page_router_20260615.py").read_text(encoding="utf-8")
    train = (ROOT / "tabs/train_data.py").read_text(encoding="utf-8")
    risk = (ROOT / "ui/risk_position_panel_20260619.py").read_text(encoding="utf-8")
    runner = (ROOT / "core/app/runner.py").read_text(encoding="utf-8")
    assert "render_position_sizing_panel" in lunch
    assert "render_finder_canonical_view" in finder
    assert "render_train_data_overview" in train
    assert "min-height:44px" in risk
    assert "use_native_sidebar_fallback_20260619" in runner


def test_optional_heavy_dependencies_are_not_in_normal_startup_requirements():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    optional = (ROOT / "requirements-optional-heavy.txt").read_text(encoding="utf-8").lower()
    for package in ("torch", "transformers", "optuna", "catboost", "lightgbm", "hmmlearn"):
        assert package not in requirements
        assert package in optional
