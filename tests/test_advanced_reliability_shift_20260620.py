from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import time
import tracemalloc

import numpy as np
import pandas as pd
import pytest

import core.advanced_reliability_shift_20260620 as advanced
from core.canonical_runtime_20260617 import build_shared_adapter, validate_canonical_result

ROOT = Path(__file__).resolve().parents[1]


def market(rows: int = 300, *, seed: int = 20260620, tail_shift: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    times = pd.date_range("2026-05-01", periods=rows, freq="h", tz="UTC")
    returns = rng.normal(0.0, 0.00012, rows)
    if tail_shift:
        returns[-48:] = rng.normal(0.00055, 0.00045, 48)
    close = 1.16 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    spread = 0.00008 + np.abs(returns) * 0.30
    return pd.DataFrame({
        "time": times,
        "open": open_,
        "high": np.maximum(open_, close) + spread,
        "low": np.minimum(open_, close) - spread,
        "close": close,
        "volume": rng.integers(80, 450, rows),
        "adx": 20 + rng.normal(0, 3, rows),
        "plus_di": 24 + rng.normal(0, 4, rows),
        "minus_di": 21 + rng.normal(0, 4, rows),
    })


def canonical(frame: pd.DataFrame, *, decision: str = "BUY", generation: int = 7) -> dict:
    latest = frame.time.iloc[-1].isoformat()
    anchor = float(frame.close.iloc[-1])
    direction = decision if decision in {"BUY", "SELL"} else "WAIT"
    horizons = {}
    for horizon in (1, 2, 3, 6):
        horizons[f"{horizon}h"] = {
            "point_forecast": anchor + (0.00004 * horizon if direction == "BUY" else -0.00004 * horizon),
            "direction": direction,
            "buy_probability_raw": 0.62 if direction == "BUY" else 0.18,
            "sell_probability_raw": 0.62 if direction == "SELL" else 0.18,
            "wait_probability_raw": 0.20,
            "buy_probability_calibrated": 0.62 if direction == "BUY" else 0.18,
            "sell_probability_calibrated": 0.62 if direction == "SELL" else 0.18,
            "wait_probability_calibrated": 0.20,
        }
    current_row = {"Time": latest, "Master /10": 6.2, "Entry /10": 6.0}
    return {
        "run_id": "RUN-ADVANCED-7",
        "canonical_calculation_id": "RUN-ADVANCED-7",
        "calculation_generation": generation,
        "data_signature": "signature-advanced-7",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "source": "TEST",
        "latest_completed_candle_time": latest,
        "created_at": latest,
        "expires_at": (frame.time.iloc[-1] + pd.Timedelta(hours=1)).isoformat(),
        "schema_version": "2.0.0",
        "calculation_version": "decision-product-20260617-v1",
        "calculation_status": "COMPLETED",
        "market": {"latest_completed_candle_time": latest, "current_price": anchor, "row_count": len(frame)},
        "regime": {"major_regime": "BULL_NORMAL", "h1_regime": "BULL_NORMAL", "h4_regime": "BULL_NORMAL", "d1_regime": "BULL_NORMAL", "alpha": 0.3, "delta": 0.1},
        "multiscale_regime": {"current_volatility_regime": "NORMAL", "multi_scale_transition_risk_pct": 24.0},
        "nlp": {"event_risk_status": "LOW", "direction": direction},
        "forecasts": {"selected_horizon": 3, "horizons": horizons},
        "reliability": {"score": 76.0},
        "priority": {"score": 78.0, "model_agreement": 0.75},
        "final_decision": {
            "final_decision": decision,
            "directional_market_view": direction,
            "tradeability_decision": decision,
            "less_risky_decision": decision,
            "selected_horizon": 3,
            "calibrated_confidence": 0.76,
            "blocking_reasons": [],
        },
        "full_metric_direction": direction,
        "full_metric_snapshot": {"latest_completed_h1_time": latest},
        "tradeability_decision": decision,
        "full_metric_current_row": current_row,
        "full_metric_history": [current_row],
        "reverse_10_current": [],
        "reverse_10_history": {},
        "canonical_priority_table": [],
        "top_two_daily_candidates": [],
        "master_score": 6.2,
        "entry_score": 6.0,
        "buy_score": 6.5,
        "sell_score": 3.0,
        "hold_safety": 5.8,
        "tp_quality": 5.5,
        "exit_risk": 4.0,
        "metadata": {"primary_calculation_authority": "Full Metric Detail + History"},
    }


def settled(rows: int = 300, *, seed: int = 77, shifted_current_priors: bool = False, singular: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    origin = pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC")
    labels = np.array(["BUY", "SELL", "WAIT"])
    actual = np.resize(labels, rows)
    if shifted_current_priors:
        split = int(rows * 0.70)
        tail_n = rows - split
        actual[split:] = np.resize(np.array(["BUY"] * 6 + ["SELL"] * 2 + ["WAIT"] * 2), tail_n)
    predicted = actual.copy()
    if singular:
        predicted[:] = "BUY"
    else:
        # Stable, invertible deterministic confusion mechanism.
        for i in range(rows):
            if i % 10 == 0:
                predicted[i] = labels[(np.where(labels == actual[i])[0][0] + 1) % 3]
            elif i % 17 == 0:
                predicted[i] = labels[(np.where(labels == actual[i])[0][0] + 2) % 3]
    origin_price = 1.15 + np.arange(rows) * 1e-7
    delta = np.where(actual == "BUY", 0.00012, np.where(actual == "SELL", -0.00012, 0.0))
    actual_close = origin_price + delta
    p_buy = np.where(predicted == "BUY", 0.72, np.where(predicted == "WAIT", 0.14, 0.10)).astype(float)
    p_sell = np.where(predicted == "SELL", 0.72, np.where(predicted == "WAIT", 0.14, 0.10)).astype(float)
    p_wait = 1.0 - p_buy - p_sell
    correct = (predicted == actual).astype(int)
    frame = pd.DataFrame({
        "calculation_id": [f"C{i}" for i in range(rows)],
        "record_status": "SETTLED",
        "forecast_origin_time": origin,
        "target_time": origin + pd.Timedelta(hours=3),
        "settlement_timestamp": origin + pd.Timedelta(hours=4),
        "horizon": 3,
        "predicted_direction": predicted,
        "direction_correct": correct,
        "forecast_origin_price": origin_price,
        "actual_close": actual_close,
        "raw_buy_probability": p_buy,
        "raw_sell_probability": p_sell,
        "raw_wait_probability": p_wait,
        "calibrated_buy_probability": np.clip(p_buy + np.where(actual == "BUY", 0.04, -0.02), 0.01, 0.98),
        "calibrated_sell_probability": np.clip(p_sell + np.where(actual == "SELL", 0.04, -0.02), 0.01, 0.98),
        "calibrated_wait_probability": np.clip(p_wait + np.where(actual == "WAIT", 0.04, -0.02), 0.01, 0.98),
        "tp_touched": ((correct == 1) & (predicted != "WAIT")).astype(int),
        "sl_touched": ((correct == 0) & (predicted != "WAIT")).astype(int),
        "absolute_error_pips": np.abs(rng.normal(4.0, 1.2, rows)),
        "squared_error": np.square(rng.normal(0.00005, 0.000015, rows)),
        "maximum_favorable_excursion": np.abs(rng.normal(0.00018, 0.00006, rows)),
        "maximum_adverse_excursion": np.abs(rng.normal(0.00012, 0.00004, rows)),
        "h1_regime": np.where(np.arange(rows) % 2 == 0, "BULL_NORMAL", "BEAR_NORMAL"),
        "h4_regime": "BULL_NORMAL",
        "d1_regime": "BULL_NORMAL",
        "volatility_state": np.where(np.arange(rows) % 4 == 0, "HIGH", "NORMAL"),
        "event_risk_status": np.where(np.arange(rows) % 5 == 0, "HIGH", "LOW"),
        "conflict_status": np.where(np.arange(rows) % 7 == 0, "CONFLICT", "NONE"),
        "counter_trend": np.where(np.arange(rows) % 11 == 0, "counter", "aligned"),
        "regime_transition_risk": np.resize([0.2, 0.5, 0.8], rows),
        "raw_confidence": np.maximum.reduce([p_buy, p_sell, p_wait]),
        "calibrated_confidence": np.maximum.reduce([p_buy, p_sell, p_wait]) + 0.02,
        "priority": 70 + rng.normal(0, 4, rows),
        "knn_score": 7 + rng.normal(0, 0.5, rows),
        "greedy_rank": 4 + rng.normal(0, 0.5, rows),
        "model_agreement": 0.75 + rng.normal(0, 0.03, rows),
        "expected_value_after_costs": rng.normal(0.15, 0.04, rows),
        "upper_band": 1.151,
        "lower_band": 1.149,
    })
    return advanced.normalize_settled_predictions(frame, origin[-1] + pd.Timedelta(hours=8))


def identity(direction: str = "BUY") -> dict:
    return {
        "direction": direction,
        "horizon": 3,
        "session": "LONDON",
        "hour": 9,
        "h1_regime": "BULL_NORMAL",
        "h4_regime": "BULL_NORMAL",
        "d1_regime": "BULL_NORMAL",
        "volatility_state": "NORMAL",
        "event_risk": "LOW",
        "conflict": False,
        "counter_trend": False,
        "transition_risk": 24.0,
    }


def stable_result(result: dict) -> dict:
    value = deepcopy(result)
    value.pop("created_at", None)
    value.pop("persistence", None)
    value.pop("performance", None)
    return value


def test_01_static_no_future_leakage_contract():
    source = Path(advanced.__file__).read_text(encoding="utf-8").replace(" ", "")
    for forbidden in (".shift(-", "center=True", ".bfill(", "train_test_split", "StandardScaler", "MinMaxScaler"):
        assert forbidden not in source
    assert "sort_values(\"__order\")" in source
    assert "chronological_purged_splits" in source


def test_02_appended_future_row_invariance():
    frame = market(240)
    c = canonical(frame)
    future = pd.concat([frame, pd.DataFrame([{
        "time": frame.time.iloc[-1] + pd.Timedelta(hours=1), "open": 9.0, "high": 10.0,
        "low": 8.0, "close": 9.5, "volume": 99999,
    }])], ignore_index=True)
    a_payload, a, _ = advanced.build_advanced_reliability_transaction(c, completed_h1=frame, settled_predictions=settled(180), persist_stage=False)
    b_payload, b, _ = advanced.build_advanced_reliability_transaction(c, completed_h1=future, settled_predictions=settled(180), persist_stage=False)
    assert a["identity"]["data_hash"] == b["identity"]["data_hash"]
    assert stable_result(a) == stable_result(b)
    assert a_payload["final_decision"] == b_payload["final_decision"]


def test_03_same_input_deterministic_output():
    frame = market(220); c = canonical(frame); evidence = settled(210)
    _, a, _ = advanced.build_advanced_reliability_transaction(c, completed_h1=frame, settled_predictions=evidence, persist_stage=False)
    _, b, _ = advanced.build_advanced_reliability_transaction(c, completed_h1=frame, settled_predictions=evidence, persist_stage=False)
    assert stable_result(a) == stable_result(b)


def test_04_completed_candle_cutoff():
    frame = market(120)
    cutoff = frame.time.iloc[-2]
    clean = advanced.normalize_completed_h1(frame, cutoff)
    assert clean.time.max() == cutoff
    assert len(clean) == len(frame) - 1


def test_05_chronological_purge_and_embargo():
    splits = advanced.chronological_purged_splits(240, purge=6, embargo=8, n_splits=3)
    assert splits
    for train, test in splits:
        assert train.max() <= test.min() - 8 - 1
        assert np.intersect1d(train, test).size == 0


def test_06_small_sample_hierarchical_fallbacks():
    tiny = settled(18)
    crc = advanced.conformal_risk_control(tiny, identity())
    multi = advanced.multicalibrate_probability(tiny, identity(), 0.7)
    assert crc["status"] == "INSUFFICIENT_EVIDENCE"
    assert multi["status"] == "INSUFFICIENT_EVIDENCE"


def test_07_missing_columns_and_optional_failure_are_safe():
    bad = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=3, freq="h")})
    assert advanced.normalize_completed_h1(bad).empty
    result = advanced.build_revin_evidence(pd.DataFrame(), pd.DataFrame(), {})
    assert result["status"] == "UNAVAILABLE"
    deferred = advanced.build_dml_event_effects(pd.DataFrame(), maintenance=False)
    assert deferred["status"] == "DEFERRED_OFFLINE"


def test_08_mmd_no_shift_and_synthetic_shift_detection():
    rng = np.random.default_rng(5)
    reference = rng.normal(0, 1, (128, 4))
    same = rng.normal(0, 1, (128, 4))
    shifted = rng.normal(3.0, 1, (128, 4))
    null = advanced.mmd_block_test(reference, same, seed=11, permutations=96)
    alt = advanced.mmd_block_test(reference, shifted, seed=11, permutations=96)
    assert null["status"] == "VALID" and alt["status"] == "VALID"
    assert alt["statistic"] > null["statistic"]
    assert alt["significant"] is True
    assert alt["severity"] in {"MEDIUM", "HIGH"}


def test_09_random_cut_forest_normal_and_injected_anomaly():
    rng = np.random.default_rng(8)
    history = rng.normal(0, 1, (180, 6))
    normal = advanced.random_cut_forest_score(history, np.zeros(6), seed=4)
    anomaly = advanced.random_cut_forest_score(history, np.full(6, 9.0), seed=4)
    assert 0 <= normal <= 1 and 0 <= anomaly <= 1
    assert anomaly > normal


def test_10_bbse_known_prior_shift_recovery():
    evidence = settled(360, shifted_current_priors=True)
    result = advanced.bbse_label_shift(evidence, {"strong_feature_drift": False})
    assert result["valid"] is True
    estimated = result["direction"]["estimated_current_priors"]
    assert estimated["BUY"] > estimated["SELL"]
    assert estimated["BUY"] > estimated["WAIT"]


def test_11_bbse_rejects_ill_conditioned_confusion_matrix():
    result = advanced.bbse_label_shift(settled(300, singular=True), {"strong_feature_drift": False})
    assert result["valid"] is False
    assert result["status"] == "REJECTED"
    assert "condition" in result["reason"].lower() or "support" in result["reason"].lower()


def test_12_multicalibration_improves_supported_subgroup_gap():
    evidence = settled(360)
    # Deliberately under-confident BUY probabilities in a supported group.
    mask = evidence["predicted_direction"].eq("BUY")
    evidence.loc[mask, "raw_buy_probability"] = 0.35
    before = abs(1.0 - 0.35)
    result = advanced.multicalibrate_probability(evidence, identity(), 0.35, min_support=20)
    after = abs(1.0 - result["calibrated_probability"])
    assert result["status"] in {"VALID", "VALID_GLOBAL_FALLBACK"}
    assert after < before
    assert abs(result["calibration_gap"]) <= 0.15 + 1e-12


def test_13_crc_risk_control_and_monotonicity():
    result = advanced.conformal_risk_control(settled(360), identity())
    assert result["status"] in {"VALID", "RISK_NOT_CONTROLLED"}
    assert result["monotone_loss_verified"] is True
    curve = result["curve"]
    assert all(0 <= row["observed_risk"] <= 1 for row in curve)
    assert all(curve[i]["observed_risk"] + 1e-12 >= curve[i + 1]["observed_risk"] for i in range(len(curve) - 1))


def test_14_revin_inverse_transform_and_input_window_only():
    values = np.array([1.1, 1.2, 1.3, 1.4])
    normalized, mean, std = advanced.revin_normalize(values)
    assert np.allclose(advanced.revin_inverse(normalized, mean, std), values)
    frame = market(120); c = canonical(frame)
    a = advanced.build_revin_evidence(frame, settled(120), c)
    altered = frame.copy(); altered.loc[0, "close"] = 99.0
    b = advanced.build_revin_evidence(altered, settled(120), c)
    # Only the available tail-96 input window determines current normalization.
    assert a["window_mean"] == pytest.approx(b["window_mean"])
    assert a["influence_enabled"] is False


def test_15_irm_environment_stability_diagnostic():
    result = advanced.irm_diagnostics(settled(360), min_environment_support=15)
    assert result["status"] == "VALID"
    assert 0 <= result["invariance_score"] <= 1
    assert result["environment_count"] >= 3
    assert all(row["status"] in {"STABLE", "ENVIRONMENT_SPECIFIC", "UNSUPPORTED"} for row in result["features"].values())


def test_16_group_dro_worst_group_selection():
    result = advanced.group_dro_validation(settled(360), min_group_support=8)
    assert result["status"] == "VALID"
    assert result["weights_changed"] is False
    selected = result["selected_candidate"]
    assert selected in result["candidates"]
    for row in result["candidates"].values():
        assert 0 <= row["average_loss"] <= 1
        assert 0 <= row["worst_group_loss"] <= 1
        assert row["worst_group"]
        assert 0 <= row["robust_selection_score"] <= 1


def test_17_dml_placebo_and_synthetic_treatment():
    rng = np.random.default_rng(12)
    n = 420
    x = rng.normal(size=(n, 4))
    propensity = 1 / (1 + np.exp(-(0.4 * x[:, 0] - 0.3 * x[:, 1])))
    d = (rng.random(n) < propensity).astype(float)
    effect = 0.45
    y = effect * d + 0.6 * x[:, 0] - 0.2 * x[:, 2] + rng.normal(0, 0.12, n)
    treated = advanced.double_ml_partial_linear(y, d, x, purge=6, embargo=6)
    placebo = advanced.double_ml_partial_linear(0.6 * x[:, 0] - 0.2 * x[:, 2] + rng.normal(0, 0.12, n), d, x, purge=6, embargo=6)
    assert treated["status"] == "VALID" and placebo["status"] == "VALID"
    assert treated["effect"] > 0.25
    assert abs(placebo["effect"]) < 0.20


def test_18_signature_composition_and_dimension_bound():
    rng = np.random.default_rng(9)
    raw = rng.normal(size=(20, 6)).cumsum(axis=0)
    path = advanced.lead_lag_path(raw)
    result = advanced.truncated_signature(path, level=2, max_dimensions=260)
    assert result["status"] == "VALID"
    assert result["dimension"] == 156
    bounded = advanced.truncated_signature(path, level=3, max_dimensions=260)
    assert bounded["status"] == "DIMENSION_BOUND"
    assert result["composition"].startswith("Chen")


def test_19_canonical_calculation_id_and_generation_sync(tmp_path):
    frame = market(180); c = canonical(frame)
    store = advanced.AdvancedReliabilityStore(tmp_path / "research.sqlite3")
    payload, result, stage = advanced.build_advanced_reliability_transaction(c, completed_h1=frame, settled_predictions=settled(180), store=store, persist_stage=True)
    assert stage["status"] == "STAGED"
    assert result["identity"]["calculation_id"] == c["canonical_calculation_id"]
    assert result["identity"]["generation"] == c["calculation_generation"]
    assert result["identity"]["latest_completed_h1_time"] == c["latest_completed_candle_time"]
    ok, errors = validate_canonical_result(payload)
    assert ok, errors
    assert store.mark_published(c["canonical_calculation_id"])["status"] == "PUBLISHED"


def test_20_tab_navigation_has_no_recalculation_path():
    orchestrator = (ROOT / "core/settings_run_orchestrator_20260617.py").read_text(encoding="utf-8")
    assert orchestrator.index("build_advanced_reliability_transaction") < orchestrator.index("publish_canonical_atomically(")
    assert orchestrator.index("publish_canonical_atomically(") < orchestrator.index("mark_advanced_reliability_published")
    renderer_hits = []
    for folder in (ROOT / "tabs", ROOT / "pages"):
        if not folder.exists():
            continue
        for path in folder.rglob("*.py"):
            if "build_advanced_reliability_transaction" in path.read_text(encoding="utf-8", errors="ignore"):
                renderer_hits.append(path.relative_to(ROOT).as_posix())
    assert not renderer_hits


def test_21_streamlit_cloud_import_and_startup_preflight():
    assert advanced.VERSION.endswith("v2")
    compile((ROOT / "app.py").read_text(encoding="utf-8"), "app.py", "exec")
    assert (ROOT / "runtime.txt").read_text(encoding="utf-8").strip() == "python-3.12"
    assert "tensorflow" not in (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "torch" not in (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()


def test_22_mobile_and_closed_field_visible_structure_unchanged():
    module_source = Path(advanced.__file__).read_text(encoding="utf-8")
    assert "import streamlit" not in module_source
    lunch = (ROOT / "tabs/lunch_tab.py").read_text(encoding="utf-8", errors="ignore") if (ROOT / "tabs/lunch_tab.py").exists() else ""
    router = (ROOT / "tabs/antd_page_router_20260615.py").read_text(encoding="utf-8", errors="ignore")
    assert "advanced_reliability_shift" not in lunch.lower()
    assert "advanced_reliability_shift" not in router.lower()
    assert "Open / Close" in router


def test_23_memory_and_runtime_bounded_benchmark():
    frame = market(180); c = canonical(frame); evidence = settled(180)
    tracemalloc.start()
    started = time.perf_counter()
    _, result, _ = advanced.build_advanced_reliability_transaction(c, completed_h1=frame, settled_predictions=evidence, persist_stage=False)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert elapsed < 15.0
    assert peak < 128 * 1024 * 1024
    assert result["input_contract"]["completed_h1_rows"] <= 720
    assert result["input_contract"]["settled_prediction_rows"] <= 6000


def test_24_complete_regression_suite_is_present_and_advanced_adapter_reuses_payload():
    existing = [path for path in (ROOT / "tests").glob("test_*.py") if path.name != Path(__file__).name]
    assert len(existing) >= 25
    frame = market(160); c = canonical(frame)
    payload, result, _ = advanced.build_advanced_reliability_transaction(c, completed_h1=frame, settled_predictions=settled(160), persist_stage=False)
    adapter = build_shared_adapter({}, payload, priority_table=pd.DataFrame())
    assert adapter["advanced_reliability_shift"]["identity"] == result["identity"]
    assert adapter["reliability"]["advanced_reliability_shift"]["identity"] == result["identity"]
    assert adapter["powerbi"]["advanced_reliability_shift"]["identity"] == result["identity"]
    assert adapter["data_mining"]["advanced_reliability_shift"]["identity"] == result["identity"]
    assert adapter["ai_grounding"]["advanced_reliability_shift"]["identity"] == result["identity"]
