from __future__ import annotations

import numpy as np
import pandas as pd

from core.canonical_runtime_20260617 import build_shared_adapter, validate_canonical_result
from core.multiscale_probabilistic_upgrade_20260618 import (
    build_and_apply_upgrade,
    enrich_existing_regime_tables,
    invariant_report,
)


def market(rows: int = 960) -> pd.DataFrame:
    rng = np.random.default_rng(41)
    times = pd.date_range("2026-04-01", periods=rows, freq="h", tz="UTC")
    returns = rng.standard_t(7, rows) * 0.00011
    # Add deterministic volatility clusters without introducing any future input.
    returns[300:380] *= 2.0
    returns[700:740] *= 3.2
    close = 1.15 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({
        "time": times,
        "open": open_,
        "high": np.maximum(open_, close) + 0.00008,
        "low": np.minimum(open_, close) - 0.00008,
        "close": close,
    })


def bundle(frame: pd.DataFrame) -> dict:
    anchor = float(frame.close.iloc[-1])
    times = pd.date_range(frame.time.iloc[-1] + pd.Timedelta(hours=1), periods=6, freq="h")
    main = pd.DataFrame({
        "step": range(1, 7), "time": times,
        "main_path": anchor + np.arange(1, 7) * 0.000025,
        "upper_band": anchor + np.arange(1, 7) * 0.00008,
        "lower_band": anchor - np.arange(1, 7) * 0.00006,
        "band_width": np.arange(1, 7) * 0.00008,
        "source_spread": 0.00002,
    })
    return {"ok": True, "main": main, "summary": {}, "audit": {}}


def history(frame: pd.DataFrame, rows: int = 140) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    out = []
    for i in range(rows):
        actual = 1.145 + i * 0.000003
        out.append({
            "target time": frame.time.iloc[-rows - 20 + i],
            "Predicted Close": actual + rng.standard_t(7) * 0.00004,
            "Actual Close": actual,
            "horizon": i % 6 + 1,
            "regime": "BULL_NORMAL",
        })
    return pd.DataFrame(out)


def canonical(frame: pd.DataFrame) -> dict:
    anchor = float(frame.close.iloc[-1])
    horizons = {
        f"{h}h": {"horizon_hours": h, "point_forecast": anchor + h * 0.000025, "direction": "BUY"}
        for h in (1, 2, 3, 6)
    }
    return {
        "schema_version": "2.0.0", "run_id": "RUN-X", "calculation_generation": 1,
        "created_at": "2026-06-18T00:00:00+00:00", "expires_at": "2026-06-18T01:00:00+00:00",
        "symbol": "EURUSD", "timeframe": "H1", "source": "TEST",
        "latest_completed_candle_time": frame.time.iloc[-1].isoformat(), "data_signature": "sig-x",
        "model_version": "existing-models-v1", "calculation_version": "decision-product-20260617-v1",
        "calculation_status": "COMPLETED", "failure_reason": None,
        "market": {"latest_completed_candle_time": frame.time.iloc[-1].isoformat(), "current_price": anchor, "row_count": len(frame)},
        "data_quality": {"status": "PASS", "score": 98},
        "regime": {"major_regime": "BULL_NORMAL", "alpha": 0.4, "delta": 0.1},
        "forecasts": {"selected_horizon": 3, "agreement_score": 72, "horizons": horizons},
        "priority": {"score": 75, "label": "A"},
        "nlp": {"direction": "BUY", "importance": 25, "reliability": 65},
        "reliability": {"score": 70, "sample_count": 140, "direction_accuracy": 0.57, "brier_score": 0.22, "expected_calibration_error": 0.08, "interval_coverage": 0.88},
        "drift": {"status": "STABLE"}, "risk": {"risk_level": "MEDIUM"},
        "final_decision": {"final_decision": "BUY", "directional_market_view": "BUY", "tradeability_decision": "BUY", "less_risky_decision": "BUY", "selected_horizon": 3, "blocking_reasons": []},
        "entry_score": 6.2, "hold_safety": 5.8, "exit_risk": 4.1, "full_metric_direction": "BUY",
        "metadata": {},
    }


def test_multiscale_probabilities_quantiles_decomposition_and_central_path():
    frame = market(); raw_bundle = bundle(frame)
    original_central = raw_bundle["main"]["main_path"].to_numpy().copy()
    upgraded, _, upgraded_bundle = build_and_apply_upgrade(
        canonical(frame), ohlc=frame, calibrated_bundle=raw_bundle, prediction_history=history(frame)
    )
    assert all(invariant_report(upgraded).values())
    assert np.allclose(upgraded_bundle["main"]["main_path"].to_numpy(), original_central)
    assert np.all(upgraded_bundle["main"]["lower_band"] <= upgraded_bundle["main"]["main_path"])
    assert np.all(upgraded_bundle["main"]["main_path"] <= upgraded_bundle["main"]["upper_band"])
    assert len(upgraded["multiscale_regime"]["joint_27_state_probabilities"]) == 27
    assert upgraded["metadata"]["full_metric_formulas_preserved"] is True


def test_same_completed_input_is_deterministic_and_future_history_is_ignored():
    frame = market(); c = canonical(frame); h = history(frame)
    future = pd.DataFrame([{
        "target time": frame.time.iloc[-1] + pd.Timedelta(hours=2),
        "Predicted Close": 1.0, "Actual Close": 99.0, "horizon": 1,
    }])
    a, _, _ = build_and_apply_upgrade(c, ohlc=frame, calibrated_bundle=bundle(frame), prediction_history=h)
    b, _, _ = build_and_apply_upgrade(c, ohlc=frame, calibrated_bundle=bundle(frame), prediction_history=pd.concat([h, future], ignore_index=True))
    assert a["canonical_calculation_id"] == b["canonical_calculation_id"]
    assert a["probabilistic_projection"]["deterministic_seed"] == b["probabilistic_projection"]["deterministic_seed"]
    assert a["probabilistic_projection"]["horizons"] == b["probabilistic_projection"]["horizons"]


def test_cache_reuse_and_short_history_fallback_are_safe():
    frame = market(150); c = canonical(frame)
    first, cache, _ = build_and_apply_upgrade(c, ohlc=frame, calibrated_bundle=bundle(frame), prediction_history=pd.DataFrame())
    second, reused, _ = build_and_apply_upgrade(c, ohlc=frame, calibrated_bundle=bundle(frame), prediction_history=pd.DataFrame(), previous_cache=cache)
    assert reused["canonical_calculation_id"] == cache["canonical_calculation_id"]
    assert second["metadata"]["multiscale_cache_status"] == "REUSED"
    assert first["probabilistic_projection"]["scenario_method"] == "Student-t short-history fallback"
    assert all(invariant_report(second).values())


def test_existing_regime_tables_are_enriched_without_new_section():
    frame = market(); upgraded, _, _ = build_and_apply_upgrade(canonical(frame), ohlc=frame, calibrated_bundle=bundle(frame), prediction_history=history(frame))
    details = {"lower": pd.DataFrame([{"Major Regime": "BULL_NORMAL"}]), "medium": pd.DataFrame([{"Major Regime": "BULL_NORMAL"}]), "higher": pd.DataFrame([{"Major Regime": "BULL_NORMAL"}])}
    summary = pd.DataFrame([{"Standard": "Lower Standard"}])
    d2, s2 = enrich_existing_regime_tables(details, summary, upgraded["multiscale_regime"], upgraded["canonical_calculation_id"])
    required = {"Volatility Regime", "Regime Entropy", "Regime Stability %", "Regime Change Risk %", "Canonical Calculation ID"}
    assert required.issubset(d2["lower"].columns)
    assert required.issubset(s2.columns)


def test_adapter_carries_one_shared_calculation_to_all_consumers():
    frame = market(); upgraded, _, _ = build_and_apply_upgrade(canonical(frame), ohlc=frame, calibrated_bundle=bundle(frame), prediction_history=history(frame))
    ok, errors = validate_canonical_result(upgraded)
    assert ok, errors
    adapter = build_shared_adapter({}, upgraded, priority_table=pd.DataFrame())
    calc_id = upgraded["canonical_calculation_id"]
    assert adapter["canonical_calculation_id"] == calc_id
    assert adapter["current"]["canonical_calculation_id"] == calc_id
    assert adapter["regime"]["volatility_regime"] == upgraded["multiscale_regime"]["current_volatility_regime"]
    assert adapter["powerbi"]["probabilistic_projection"]["calculation_id"] == calc_id
    assert adapter["ai_grounding"]["probabilistic_projection"]["calculation_id"] == calc_id
