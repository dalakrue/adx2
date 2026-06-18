from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import pytest

import core.research_calibration_20260618 as research
from core.canonical_runtime_20260617 import build_shared_adapter
from core.operational_sync_20260618 import synchronize_published_generation


def market(rows: int = 240, *, shifted_tail: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(20260618)
    times = pd.date_range("2026-05-01", periods=rows, freq="h", tz="UTC")
    returns = rng.normal(0.0, 0.00012, rows)
    returns[140:190] *= 1.9
    returns[300:330] *= 2.8
    if shifted_tail:
        returns[-36:] = rng.normal(0.00018, 0.00042, 36)
    close = 1.16 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({
        "time": times,
        "open": open_,
        "high": np.maximum(open_, close) + 0.00010,
        "low": np.minimum(open_, close) - 0.00010,
        "close": close,
    })


def bundle(frame: pd.DataFrame, *, agreement: float = 72.0) -> dict:
    anchor = float(frame.close.iloc[-1])
    future = pd.date_range(frame.time.iloc[-1] + pd.Timedelta(hours=1), periods=6, freq="h")
    main = pd.DataFrame({
        "step": range(1, 7),
        "time": future,
        "main_path": anchor + np.arange(1, 7) * 0.000035,
        "upper_band": anchor + np.arange(1, 7) * 0.00014,
        "lower_band": anchor - np.arange(1, 7) * 0.00012,
        "band_width": np.arange(1, 7) * 0.00014,
        "source_spread": 0.00004,
    })
    rng = np.random.default_rng(29)
    audit = {"horizon_residual_samples": {}}
    for path, scale in (("red", 0.00009), ("yellow", 0.00011), ("blue", 0.00013)):
        for h in range(1, 7):
            audit["horizon_residual_samples"][f"{path}_H+{h}"] = rng.normal(0, scale * h ** 0.5, 80).tolist()
    return {"ok": True, "main": main, "summary": {"path_agreement_pct": agreement}, "audit": audit}


def canonical(frame: pd.DataFrame, *, nlp_importance: float = 0.15, reliability: float = 74.0) -> dict:
    anchor = float(frame.close.iloc[-1])
    horizons = {
        f"{h}h": {"horizon_hours": h, "point_forecast": anchor + h * 0.000035, "direction": "BUY"}
        for h in range(1, 7)
    }
    return {
        "schema_version": "2.0.0",
        "run_id": "RUN-RESEARCH",
        "calculation_generation": 1,
        "created_at": "2026-06-18T00:00:00+00:00",
        "expires_at": "2026-06-18T01:00:00+00:00",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "source": "TEST",
        "latest_completed_candle_time": frame.time.iloc[-1].isoformat(),
        "data_signature": "sig-research",
        "calculation_version": "decision-product-20260617-v1",
        "calculation_status": "COMPLETED",
        "market": {"latest_completed_candle_time": frame.time.iloc[-1].isoformat(), "current_price": anchor, "row_count": len(frame)},
        "regime": {"major_regime": "BULL_NORMAL", "alpha": 0.35, "delta": 0.08},
        "multiscale_regime": {"current_volatility_regime": "CALM"},
        "forecasts": {"selected_horizon": 3, "horizons": horizons},
        "reliability": {"score": reliability, "label": "HIGH"},
        "nlp": {"direction": "BUY", "importance": nlp_importance, "reliability": 68},
        "final_decision": {
            "final_decision": "BUY", "directional_market_view": "BUY",
            "tradeability_decision": "BUY", "less_risky_decision": "BUY",
            "selected_horizon": 3, "calibrated_confidence": reliability, "blocking_reasons": [],
        },
        "master_score": 6.4,
        "entry_score": 6.1,
        "hold_safety": 5.8,
        "tp_quality": 5.5,
        "exit_risk": 4.0,
        "full_metric_direction": "BUY",
        "meta_labels": {},
        "metadata": {},
        "layer_execution_metadata": [],
    }


def completed_prediction_history(frame: pd.DataFrame, origins: int = 18) -> pd.DataFrame:
    rng = np.random.default_rng(77)
    rows = []
    start = len(frame) - origins - 12
    for origin in range(start, start + origins):
        origin_time = frame.time.iloc[origin]
        current = float(frame.close.iloc[origin])
        for horizon in range(1, 7):
            actual = float(frame.close.iloc[origin + horizon])
            residual = rng.normal(0, 0.000035 * horizon ** 0.5)
            predicted = actual - residual
            width = 0.00010 * horizon ** 0.5
            rows.append({
                "run_id": f"RUN-{origin}",
                "prediction_time": origin_time,
                "target_time": frame.time.iloc[origin + horizon],
                "horizon": horizon,
                "predicted_close": predicted,
                "actual_close": actual,
                "current_price": current,
                "predicted_direction": "BUY" if predicted >= current else "SELL",
                "predicted_lower_band": predicted - width,
                "predicted_upper_band": predicted + width,
                "major_regime": "BULL_NORMAL",
                "volatility_regime": "CALM",
                "transition_risk": 25.0,
                "path_disagreement": 12.0,
                "reliability": 72.0,
                "realized_volatility": 0.00012,
            })
    return pd.DataFrame(rows)



def fast_previous_cache() -> dict:
    names = (
        "prediction_residuals", "direction_accuracy", "reliability_calibration", "model_performance",
        "session_performance", "volatility_estimation", "feature_importance", "knn_candidate_history",
        "nlp_impact_relationship",
    )
    return {"adaptive_windows": {"states": {name: {"current_window_size": 36, "last_update_timestamp": "old"} for name in names}}}

def build(frame: pd.DataFrame | None = None, **kwargs):
    frame = frame if frame is not None else market()
    return research.build_and_apply_research_layer(
        canonical(frame),
        ohlc=frame,
        calibrated_bundle=bundle(frame),
        settled_predictions=completed_prediction_history(frame),
        previous_cache=kwargs.pop("previous_cache", fast_previous_cache()),
        **kwargs,
    )


def test_completed_candle_cutoff_excludes_future_rows():
    frame = market()
    future = frame.copy()
    extra_time = frame.time.iloc[-1] + pd.Timedelta(hours=1)
    extra = pd.DataFrame([{"time": extra_time, "open": 9.0, "high": 10.0, "low": 8.0, "close": 9.5}])
    future = pd.concat([future, extra], ignore_index=True)
    cutoff = frame.time.iloc[-1]
    clean = research.normalize_completed_ohlc(future, latest_completed=cutoff)
    assert len(clean) == len(frame)
    assert clean.time.max() == cutoff
    assert float(clean.close.iloc[-1]) == pytest.approx(float(frame.close.iloc[-1]))


def test_active_python_has_no_negative_shift_centered_window_or_future_backfill():
    root = Path(__file__).resolve().parents[1]
    forbidden = [".shift(" + "-", "center" + "=True", "." + "bfill("]
    violations = []
    for path in root.rglob("*.py"):
        relative = path.relative_to(root).as_posix()
        if "legacy_impl/" in relative or "tabs/home_parts/" in relative or relative.startswith("tests/"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if text.lstrip().startswith("SOURCE ="):
            continue
        compact = text.replace(" ", "")
        for token in forbidden:
            if token in compact:
                violations.append((relative, token))
    assert not violations


def test_research_layer_uses_no_random_split_or_full_sample_scaler():
    text = Path(research.__file__).read_text(encoding="utf-8")
    assert "train_test_split" not in text
    assert "StandardScaler" not in text
    assert "MinMaxScaler" not in text
    assert "expanding(min_periods=8).mean().shift(1)" in text


def test_purged_walk_forward_has_nonoverlap_and_embargo_at_least_horizon():
    splits = research.purged_walk_forward_splits(420, maximum_horizon=6, validation_size=24, embargo=6)
    assert splits
    for split in splits:
        assert split["train_end_exclusive"] + split["purging_period"] <= split["validation_start"]
        assert split["embargo_period"] >= split["maximum_forecast_horizon"]
        assert split["targets_overlap"] is False


def test_same_input_is_deterministic_for_id_seed_hash_and_output():
    frame = market(); history = completed_prediction_history(frame)
    a_payload, a, _ = research.build_and_apply_research_layer(canonical(frame), ohlc=frame, calibrated_bundle=bundle(frame), settled_predictions=history, previous_cache=fast_previous_cache())
    b_payload, b, _ = research.build_and_apply_research_layer(canonical(frame), ohlc=frame, calibrated_bundle=bundle(frame), settled_predictions=history, previous_cache=fast_previous_cache())
    assert a["canonical_calculation_id"] == b["canonical_calculation_id"]
    assert a["input_hash"] == b["input_hash"]
    assert a["output_hash"] == b["output_hash"]
    assert a["conformal_prediction"]["deterministic_seed"] == b["conformal_prediction"]["deterministic_seed"]
    assert a_payload["final_decision"] == b_payload["final_decision"]


def test_same_cutoff_ignores_appended_future_ohlc():
    frame = market(); c = canonical(frame); history = completed_prediction_history(frame)
    future = pd.concat([frame, pd.DataFrame([{
        "time": frame.time.iloc[-1] + pd.Timedelta(hours=1), "open": 5.0, "high": 6.0, "low": 4.0, "close": 5.5,
    }])], ignore_index=True)
    _, a, _ = research.build_and_apply_research_layer(c, ohlc=frame, calibrated_bundle=bundle(frame), settled_predictions=history, previous_cache=fast_previous_cache())
    _, b, _ = research.build_and_apply_research_layer(c, ohlc=future, calibrated_bundle=bundle(frame), settled_predictions=history, previous_cache=fast_previous_cache())
    assert a["canonical_calculation_id"] == b["canonical_calculation_id"]
    assert a["output_hash"] == b["output_hash"]


def test_new_completed_h1_invalidates_calculation_id():
    frame = market()
    _, old, _ = build(frame)
    last = frame.iloc[-1]
    new_row = pd.DataFrame([{
        "time": frame.time.iloc[-1] + pd.Timedelta(hours=1),
        "open": last.close, "high": last.close + 0.0002, "low": last.close - 0.0001, "close": last.close + 0.00008,
    }])
    newer = pd.concat([frame, new_row], ignore_index=True)
    _, new, _ = research.build_and_apply_research_layer(canonical(newer), ohlc=newer, calibrated_bundle=bundle(newer), settled_predictions=completed_prediction_history(newer), previous_cache=fast_previous_cache())
    assert old["canonical_calculation_id"] != new["canonical_calculation_id"]
    assert old["data_hash"] != new["data_hash"]


def test_nlp_only_change_preserves_data_hash_but_invalidates_relevant_output():
    frame = market(); history = completed_prediction_history(frame)
    _, low, _ = research.build_and_apply_research_layer(canonical(frame, nlp_importance=0.05), ohlc=frame, calibrated_bundle=bundle(frame), settled_predictions=history, previous_cache=fast_previous_cache())
    _, high, _ = research.build_and_apply_research_layer(canonical(frame, nlp_importance=0.95), ohlc=frame, calibrated_bundle=bundle(frame), settled_predictions=history, previous_cache=fast_previous_cache())
    assert low["data_hash"] == high["data_hash"]
    assert low["input_hash"] != high["input_hash"]
    assert low["canonical_calculation_id"] != high["canonical_calculation_id"]
    assert low["uncertainty"]["aleatoric_uncertainty_0_100"] < high["uncertainty"]["aleatoric_uncertainty_0_100"]


def test_residual_vectors_are_coherent_and_conditioned_as_whole_vectors():
    frame = market()
    bank = research.build_residual_vectors(frame, settled_predictions=completed_prediction_history(frame))
    vectors = np.asarray(bank["vectors"])
    assert bank["coherent"] is True
    assert vectors.ndim == 2 and vectors.shape[1] == 6
    assert len(bank["vector_metadata"]) == len(vectors)
    central = bundle(frame)["main"]["main_path"].to_numpy()
    adaptive = research.update_adaptive_coverage(None, bank["scalar_bank"], current_volatility_regime="CALM", current_session="LONDON", transition_state="LOW_TRANSITION_RISK")
    result = research.conformal_scenarios(
        central, bank, seed_material="coherence", adaptive_coverage=adaptive,
        current_volatility_regime="CALM", current_session="LONDON",
        transition_state="LOW_TRANSITION_RISK", anchor=float(frame.close.iloc[-1]), current_direction="BUY",
        current_realized_volatility=0.00012,
    )
    assert result["coherent_residual_vector_sampling"] is True
    assert result["fallback_hierarchy_level"].startswith("LEVEL_")
    assert result["conditioned_vector_sample_size"] >= 12


def test_quantile_ordering_and_band_monotonicity():
    _, result, upgraded = build()
    for row in result["conformal_prediction"]["horizons"]:
        assert row["p10"] <= row["p25"] <= row["p50"] <= row["p75"] <= row["p90"]
        assert row["lower_band"] <= row["central"] <= row["upper_band"]
    main = upgraded["main"]
    assert np.all(main.lower_band <= main.main_path)
    assert np.all(main.main_path <= main.upper_band)
    assert upgraded["summary"]["central_path_preserved"] is True


def test_adaptive_coverage_widens_after_undercoverage_and_narrows_after_overcoverage():
    under = pd.DataFrame({"horizon": [1] * 30, "inside_interval": [0] * 30})
    over = pd.DataFrame({"horizon": [1] * 30, "inside_interval": [1] * 30})
    a = research.update_adaptive_coverage(None, under, current_volatility_regime="CALM", current_session="ASIAN", transition_state="LOW_TRANSITION_RISK")
    b = research.update_adaptive_coverage(None, over, current_volatility_regime="CALM", current_session="ASIAN", transition_state="LOW_TRANSITION_RISK")
    key = "H+1|CALM|ASIAN|LOW_TRANSITION_RISK"
    assert a["states"][key]["adaptive_correction"] > 1.0
    assert b["states"][key]["adaptive_correction"] < 1.0
    assert 0.65 <= a["states"][key]["adaptive_correction"] <= 2.50
    assert 0.65 <= b["states"][key]["adaptive_correction"] <= 2.50


def test_adaptive_coverage_is_idempotent_for_same_completed_outcomes():
    observations = pd.DataFrame({"horizon": [1] * 20, "inside_interval": [1, 0] * 10})
    first = research.update_adaptive_coverage(None, observations, current_volatility_regime="CALM", current_session="ASIAN", transition_state="LOW_TRANSITION_RISK")
    second = research.update_adaptive_coverage(first, observations, current_volatility_regime="CALM", current_session="ASIAN", transition_state="LOW_TRANSITION_RISK")
    key = "H+1|CALM|ASIAN|LOW_TRANSITION_RISK"
    assert first["states"][key] == second["states"][key]


def test_changepoint_probabilities_and_run_length_distribution_are_valid():
    result = research.bayesian_online_changepoint(market(500, shifted_tail=True))
    assert result["status"] == "VALID"
    for key in ("probability_change_now", "probability_change_last_3", "probability_change_last_6", "probability_structure_continues_one_more"):
        assert 0 <= result[key] <= 1
    assert result["most_likely_run_length"] >= 0
    assert result["expected_run_length"] >= 0
    assert result["probability_sum"] == pytest.approx(1.0, abs=1e-9)
    assert "completed H1 candles" in result["estimated_transition_window"]


def test_adaptive_windows_grow_in_stability_shrink_on_drift_and_reuse_same_candle():
    stable = market(360)
    low_change = {"transition_risk_0_100": 0}
    previous = {"states": {name: {"current_window_size": 100, "last_update_timestamp": "old"} for name in (
        "prediction_residuals", "direction_accuracy", "reliability_calibration", "model_performance",
        "session_performance", "volatility_estimation", "feature_importance", "knn_candidate_history", "nlp_impact_relationship",
    )}}
    grown = research.update_adaptive_windows(previous, stable, low_change)
    assert grown["states"]["prediction_residuals"]["current_window_size"] > 100
    reused = research.update_adaptive_windows(grown, stable, low_change)
    assert reused["cache_status"] == "REUSED_SAME_COMPLETED_H1"
    shrunk = research.update_adaptive_windows(previous, market(360, shifted_tail=True), {"transition_risk_0_100": 95})
    assert shrunk["states"]["prediction_residuals"]["current_window_size"] < 100
    assert shrunk["states"]["prediction_residuals"]["change_detected"] is True


def test_conditional_model_set_falls_back_without_claiming_superiority():
    error_map = {"a": {3: np.array([0.1, 0.2])}, "b": {3: np.array([0.2])}}
    result = research.conditional_method_confidence_set(error_map, horizon=3, condition="CALM|LONDON", minimum_sample=12)
    assert result["status"] == "INSUFFICIENT DATA"
    assert result["fallback_used"] is True
    assert result["accepted_models"] == []
    assert all(row["insufficient_data"] for row in result["records"])


def test_dynamic_model_weights_sum_to_one_and_respect_bounds():
    rng = np.random.default_rng(4)
    error_map = {
        "good": {3: rng.normal(0, 0.1, 80)},
        "middle": {3: rng.normal(0, 0.2, 80)},
        "bad": {3: rng.normal(0, 0.8, 80)},
    }
    cset = research.conditional_method_confidence_set(error_map, horizon=3, condition="CALM", minimum_sample=12)
    dma = research.dynamic_model_averaging(cset, error_map, horizon=3)
    assert sum(dma["weights"].values()) == pytest.approx(1.0, abs=1e-8)
    assert all(0.0 <= value <= 0.78 + 1e-8 for value in dma["weights"].values())
    assert all(value >= 0.03 - 1e-8 for value in dma["weights"].values())


def test_dynamic_occam_suppression_and_reactivation_are_recorded():
    good = np.repeat(0.01, 50); terrible = np.repeat(5.0, 50)
    error_map = {"good": {3: good}, "recovering": {3: terrible}}
    cset = {"accepted_models": ["good", "recovering"], "condition": "CALM"}
    first = research.dynamic_model_averaging(cset, error_map, horizon=3)
    recovering = next(row for row in first["records"] if row["model_name"] == "recovering")
    assert recovering["suppressed"] is True
    improved_map = {"good": {3: np.repeat(0.02, 50)}, "recovering": {3: np.repeat(0.015, 50)}}
    second = research.dynamic_model_averaging(cset, improved_map, horizon=3, previous=first)
    recovering2 = next(row for row in second["records"] if row["model_name"] == "recovering")
    assert recovering2["suppressed"] is False
    assert recovering2["reactivated"] is True


def test_all_six_horizons_have_conditional_sets_and_weights():
    _, result, _ = build()
    assert set(result["conditional_method_confidence_set"]["by_horizon"]) == {f"H+{h}" for h in range(1, 7)}
    assert set(result["dynamic_model_averaging"]["by_horizon"]) == {f"H+{h}" for h in range(1, 7)}
    for item in result["dynamic_model_averaging"]["by_horizon"].values():
        if item.get("weights"):
            assert sum(item["weights"].values()) == pytest.approx(1.0, abs=1e-8)


def test_pbo_unavailable_and_valid_cases():
    unavailable = research.probability_backtest_overfitting(np.zeros((3, 3)))
    assert unavailable["value"] is None and unavailable["status"] == "UNAVAILABLE"
    matrix = np.array([
        [1.0, 0.8, 0.2, -0.1], [0.9, 0.7, 0.3, 0.0],
        [-0.3, 0.5, 0.7, 0.4], [-0.2, 0.4, 0.8, 0.5],
        [0.1, 0.2, 0.6, 0.9], [0.0, 0.3, 0.5, 1.0],
    ])
    valid = research.probability_backtest_overfitting(matrix)
    assert valid["status"] == "VALID"
    assert 0 <= valid["value"] <= 1
    assert valid["split_count"] > 0


def test_dsr_unavailable_without_real_returns_and_valid_with_required_inputs():
    unavailable = research.deflated_sharpe_ratio(None, number_of_trials=None, sharpe_trials=None)
    assert unavailable["validation_label"] == "UNAVAILABLE"
    rng = np.random.default_rng(8)
    returns = rng.normal(0.001, 0.01, 260)
    valid = research.deflated_sharpe_ratio(returns, number_of_trials=8, sharpe_trials=np.linspace(0.1, 1.1, 8))
    assert valid["unavailable_reason"] is None
    assert 0 <= valid["deflated_sharpe_probability"] <= 1
    assert valid["sample_size"] == 260


def test_baseline_skill_is_calculated_by_horizon_when_system_history_exists():
    _, result, _ = build()
    rows = result["baseline_skill"]["rows"]
    assert {row["horizon"] for row in rows} == set(range(1, 7))
    assert {row["baseline_name"] for row in rows} >= {"naive_last_close", "drift", "session_linear", "dlinear_style"}
    assert any(row["validation_status"] == "VALID" for row in rows)


def test_aleatoric_and_epistemic_uncertainty_are_separate():
    frame = market()
    conformal = {"horizons": [{"lower_band": 1.0, "upper_band": 1.02}] * 6, "residual_vector_count": 100}
    low_epi = research.uncertainty_scores(
        frame, conformal, {"summary": {"path_agreement_pct": 95}},
        {"accepted_models": ["a", "b", "c", "d"]}, {"weights": {"a": .25, "b": .25, "c": .25, "d": .25}},
        {"transition_risk_0_100": 10}, {"importance": 0.1},
    )
    high_epi = research.uncertainty_scores(
        frame, conformal, {"summary": {"path_agreement_pct": 5}},
        {"accepted_models": []}, {"weights": {}},
        {"transition_risk_0_100": 90}, {"importance": 0.1},
    )
    assert high_epi["epistemic_uncertainty_0_100"] > low_epi["epistemic_uncertainty_0_100"]
    assert low_epi["aleatoric_uncertainty_0_100"] == pytest.approx(high_epi["aleatoric_uncertainty_0_100"])


def test_reliability_is_bounded_and_downgrades_under_joint_weakness():
    c = canonical(market(), reliability=90)
    good = research._research_reliability(
        c, {}, {"mean_coverage_quality_0_100": 95},
        {"epistemic_uncertainty_0_100": 10, "aleatoric_uncertainty_0_100": 15},
        {"transition_risk_0_100": 10}, {"accepted_models": ["a", "b", "c", "d"]},
        {"mean_skill_score": 0.2}, {"value": 0.1}, {"deflated_sharpe_probability": 0.97},
    )
    weak = research._research_reliability(
        c, {}, {"mean_coverage_quality_0_100": 15},
        {"epistemic_uncertainty_0_100": 95, "aleatoric_uncertainty_0_100": 85},
        {"transition_risk_0_100": 95}, {"accepted_models": []},
        {"mean_skill_score": -0.5}, {"value": 0.9}, {"deflated_sharpe_probability": 0.1},
    )
    assert weak["calibrated_score_0_100"] < good["calibrated_score_0_100"]
    assert weak["bounded_adjustment"] >= -8
    assert good["bounded_adjustment"] <= 6


def test_protected_scores_and_central_paths_are_preserved_while_reliability_is_calibrated():
    frame = market(); c = canonical(frame)
    original = {key: c.get(key) for key in ("master_score", "entry_score", "hold_safety", "tp_quality", "exit_risk")}
    raw_bundle = bundle(frame); central = raw_bundle["main"]["main_path"].copy()
    payload, result, upgraded = research.build_and_apply_research_layer(c, ohlc=frame, calibrated_bundle=raw_bundle, settled_predictions=completed_prediction_history(frame), previous_cache=fast_previous_cache())
    assert {key: payload.get(key) for key in original} == original
    assert np.allclose(central, upgraded["main"]["main_path"])
    assert result["protected_full_metric_preserved"] is True
    assert payload["reliability"]["existing_score_before_research"] == 74.0
    assert 0 <= payload["reliability"]["score"] <= 100


def test_short_history_and_missing_outcome_fallback_are_safe():
    frame = market(100)
    payload, result, _ = research.build_and_apply_research_layer(canonical(frame), ohlc=frame, calibrated_bundle=bundle(frame), settled_predictions=pd.DataFrame(), previous_cache=fast_previous_cache())
    assert result["conformal_prediction"]["residual_vector_source"] == "DLINEAR_WALK_FORWARD_FALLBACK"
    assert result["validation_status"] in {"VALID", "LIMITED DATA"}
    assert payload["final_decision"]["final_decision"] in {"BUY", "SELL", "WAIT"}


def test_optional_layer_failure_returns_previous_payload_and_bundle():
    c = canonical(market()); b = bundle(market())
    def fail(*args, **kwargs):
        raise RuntimeError("deliberate optional failure")
    payload, result, returned_bundle, status = research.build_research_layer_fail_safe(c, builder=fail, ohlc=market(), calibrated_bundle=b)
    assert result == {}
    assert status["status"] == "FAILED SAFELY"
    assert payload["master_score"] == c["master_score"]
    assert payload["metadata"]["research_calibration_status"] == "FAILED SAFELY"
    assert np.allclose(returned_bundle["main"]["main_path"], b["main"]["main_path"])


def test_database_persistence_and_completed_target_settlement():
    frame = market(); _, result, _ = build(frame)
    with tempfile.TemporaryDirectory() as td:
        store = research.ResearchStore(Path(td) / "research.sqlite3")
        saved = store.persist_result(result)
        assert saved["ok"] is True and saved["horizon_rows"] == 6
        last = frame.iloc[-1]
        future_rows = []
        for h in range(1, 7):
            future_rows.append({
                "time": frame.time.iloc[-1] + pd.Timedelta(hours=h),
                "open": last.close, "high": last.close + 0.0001, "low": last.close - 0.0001, "close": last.close,
            })
        completed = pd.concat([frame, pd.DataFrame(future_rows)], ignore_index=True)
        settled = store.settle_conformal_predictions(completed)
        outcomes = store.completed_conformal_outcomes()
        assert settled["settled"] == 6
        assert len(outcomes) == 6
        assert set(outcomes["inside_interval"].unique()).issubset({0, 1})
        assert outcomes["actual_completed_close"].notna().all()


def test_experiment_registry_builds_pbo_performance_matrix():
    with tempfile.TemporaryDirectory() as td:
        store = research.ResearchStore(Path(td) / "experiments.sqlite3")
        for config in range(4):
            store.register_experiment({
                "experiment_id": f"E{config}", "parameters": {"x": config},
                "purging_period": 6, "embargo_period": 6,
                "period_performance": [
                    {"period_label": f"P{period}", "chronological_index": period, "performance": float((config + 1) * (period + 1) % 7)}
                    for period in range(6)
                ],
            })
        matrix, periods, configs = store.performance_matrix()
        assert matrix.shape == (6, 4)
        assert len(periods) == 6 and len(configs) == 4
        assert research.probability_backtest_overfitting(matrix)["status"] == "VALID"


def test_lunch_and_dinner_receive_one_shared_research_generation():
    frame = market(); payload, result, _ = build(frame)
    adapter = build_shared_adapter({}, payload, priority_table=pd.DataFrame())
    state = {}
    synchronize_published_generation(state, payload, adapter, pd.DataFrame())
    lunch = state["lunch_synced_snapshot_20260618"]
    dinner = state["dinner_synced_snapshot_20260618"]
    assert lunch is dinner
    assert lunch["run_id"] == dinner["run_id"]
    assert adapter["research_calculation_id"] == result["canonical_calculation_id"]
    assert adapter["powerbi"]["research_calculation_id"] == result["canonical_calculation_id"]
    assert adapter["ai_grounding"]["research_calibration_id"] == result["canonical_calculation_id"]


def test_tab_adapter_build_does_not_recalculate_research(monkeypatch):
    frame = market(); payload, _, _ = build(frame)
    monkeypatch.setattr(research, "build_and_apply_research_layer", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not recalculate")))
    adapter = build_shared_adapter({}, payload, priority_table=pd.DataFrame())
    assert adapter["research_calibration"]
    assert adapter["current"]["research_calculation_id"]


def test_probability_and_score_bounds_and_all_invariants():
    payload, result, _ = build()
    assert all(result["invariants"].values())
    uncertainty = result["uncertainty"]
    assert all(0 <= uncertainty[key] <= 100 for key in ("aleatoric_uncertainty_0_100", "epistemic_uncertainty_0_100", "combined_uncertainty_0_100"))
    assert 0 <= payload["reliability"]["score"] <= 100
    assert 0 <= result["conformal_prediction"]["tp_touch_probability"] <= 1
    assert 0 <= result["conformal_prediction"]["sl_touch_probability"] <= 1
    for key in ("master_score", "entry_score", "hold_safety", "tp_quality", "exit_risk"):
        if payload.get(key) is not None:
            assert 0 <= float(payload[key]) <= 10


def test_requirements_compatibility_imports_lightweight_stack():
    import numpy  # noqa: F401
    import pandas  # noqa: F401
    import scipy  # noqa: F401
    import sklearn  # noqa: F401
    import streamlit  # noqa: F401


def test_versioned_contract_metadata_and_priority_research_inputs_are_exposed():
    payload, result, _ = build()
    for key in (
        "canonical_calculation_id", "calculation_timestamp", "last_completed_h1_timestamp",
        "data_source_identity", "data_hash", "input_hash", "output_hash", "cache_version",
        "schema_version", "layer_status", "layer_execution_metadata", "execution_duration_ms",
        "row_count", "error_message", "stale", "stale_status",
    ):
        assert key in result
    adapter = build_shared_adapter({}, payload, priority_table=pd.DataFrame())
    assert adapter["priority"]["research_refinements"] == payload["research_score_refinements"]
    assert adapter["priority"]["knn_neighbor_quality"]
    assert adapter["priority"]["greedy_calibration_inputs"]
