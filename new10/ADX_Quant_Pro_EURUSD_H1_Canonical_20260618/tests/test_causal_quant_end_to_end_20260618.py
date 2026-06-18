from __future__ import annotations

import numpy as np
import pandas as pd

from core.causal_quant_support_20260618 import (
    apply_support_to_authority,
    apply_support_to_canonical,
    build_causal_support_bundle,
    build_regime_conditioned_distributions,
    build_transition_risk,
    public_support_view,
)
from core.powerbi_mmse_weighting_20260618 import upgrade_projection_bundle


def _fixture(n: int = 240) -> tuple[pd.DataFrame, pd.DataFrame]:
    time = pd.date_range("2026-06-08T00:00:00Z", periods=n, freq="h")
    wave = np.sin(np.arange(n) * 2 * np.pi / 24) * 0.00015
    close = 1.145 + np.arange(n) * 0.000018 + wave
    open_ = np.r_[close[0], close[:-1]]
    ohlc = pd.DataFrame({
        "time": time,
        "open": open_,
        "high": np.maximum(open_, close) + 0.00014,
        "low": np.minimum(open_, close) - 0.00008,
        "close": close,
        "volume": 100,
    })
    priority = pd.DataFrame({
        "Time": time,
        "Direction": "BUY",
        "Full Metric Decision": "STRONG",
        "Qualification Status": "QUALIFIED ENTRY",
        "Less Risky Bias": "BUY",
        "Regime": "BULL_NORMAL",
        "Master /10": 7.2,
        "Entry /10": 6.8,
        "Hold /10": 7.0,
        "TP /10": 7.1,
        "Exit Risk /10": 2.5,
        "BUY /10": 7.5,
        "SELL /10": 2.5,
        "Reliability %": 74.0,
        "Conflict Status": "NONE",
        "Alpha": 0.35,
        "Delta": 0.12,
        "Expected Value": 0.00025,
        "Priority Score": np.linspace(70, 90, n),
        "Current Day": pd.Series(time.date).eq(time[-1].date()).to_numpy(),
        "Blocking Reason": "Passed existing Full Metric gates",
    })
    return ohlc, priority


def test_causal_bundle_covers_all_horizons_and_uses_no_future_input():
    ohlc, priority = _fixture()
    support = build_causal_support_bundle(ohlc, priority)
    assert support["retained_rows"] <= 600
    assert support["data_quality"]["future_rows_used_as_current_input"] == 0
    assert support["pattern_memory"]["future_rows_used_for_current_input"] == 0
    history = pd.DataFrame(support["actionability"]["history"])
    assert {1, 2, 3, 6}.issubset(set(history["horizon"].astype(int)))
    assert pd.to_datetime(history["settled_at"], utc=True).max() <= pd.to_datetime(support["latest_completed_h1_time"], utc=True)


def test_cache_hit_and_one_hour_append_are_distinct_and_deterministic():
    ohlc, priority = _fixture()
    first = build_causal_support_bundle(ohlc, priority)
    second = build_causal_support_bundle(ohlc, priority, previous_cache=first)
    assert second["cache_status"] == "CACHE_HIT"
    assert second["source_signature"] == first["source_signature"]

    next_time = ohlc["time"].iloc[-1] + pd.Timedelta(hours=1)
    last_close = float(ohlc["close"].iloc[-1])
    ohlc2 = pd.concat([ohlc, pd.DataFrame([{
        "time": next_time, "open": last_close, "high": last_close + 0.0002,
        "low": last_close - 0.00005, "close": last_close + 0.0001, "volume": 100,
    }])], ignore_index=True)
    new_row = priority.iloc[-1].copy()
    new_row["Time"] = next_time
    priority2 = pd.concat([priority, pd.DataFrame([new_row])], ignore_index=True)
    third = build_causal_support_bundle(ohlc2, priority2, previous_cache=first)
    assert third["cache_status"] == "INCREMENTAL_APPEND"
    assert third["latest_completed_h1_time"] != first["latest_completed_h1_time"]
    assert "rolling moments" in third["incremental_components"]
    assert third["_incremental_cache"]["incremental_state"]["updated_incrementally"] is True
    assert third["actionability"].get("incremental_settlements_added", 0) > 0


def test_support_gate_never_reverses_protected_direction():
    payload = {
        "full_metric_direction": "BUY",
        "final_decision": {
            "directional_market_view": "BUY", "tradeability_decision": "BUY", "final_decision": "BUY",
            "less_risky_decision": "BUY", "blocking_reasons": [], "supporting_reasons": [], "uncertainty_pct": 20,
        },
    }
    confirm = {
        "pattern_memory": {"pattern_confirmation": "CONFIRM", "pattern_confidence": 0.8},
        "transition_risk": {"status": "STABLE", "value": 0.2},
        "actionability": {"current_label": "QUALIFIED ENTRY", "expected_value": 0.0002},
    }
    allowed = apply_support_to_canonical(payload, confirm)
    assert allowed["final_decision"]["tradeability_decision"] == "BUY"

    blocked = dict(confirm)
    blocked["transition_risk"] = {"status": "WAIT", "value": 0.8}
    protected = apply_support_to_canonical(payload, blocked)
    assert protected["final_decision"]["directional_market_view"] == "BUY"
    assert protected["final_decision"]["tradeability_decision"] == "WAIT"
    assert protected["final_decision"]["tradeability_decision"] != "SELL"


def test_two_candidate_records_are_single_canonical_records_not_forced_entries():
    ohlc, priority = _fixture(72)
    support = build_causal_support_bundle(ohlc, priority)
    authority = {"priority_table": priority.copy(), "snapshot": {}}
    enriched = apply_support_to_authority(authority, support)
    candidates = enriched["top_two_daily_candidates"]
    assert len(candidates) == 2
    required = {
        "Candidate Timestamp", "Direction", "Current Status", "Master Score", "Entry Score",
        "Pattern Confirmation", "Transition Risk", "Actionability Label", "Final Candidate Decision",
    }
    assert required.issubset(candidates[0])
    assert set(item["Final Candidate Decision"] for item in candidates).issubset({"ENTRY", "CONDITIONAL", "WATCH", "WAIT", "BLOCKED", "EXPIRED"})


def test_structural_break_and_probability_small_sample_fallbacks_are_conservative():
    tiny = pd.DataFrame()
    transition = build_transition_risk(tiny)
    assert transition == {"value": 0.5, "status": "WATCH", "fallback": "INSUFFICIENT SAMPLE", "version": transition["version"]}

    ohlc, priority = _fixture(12)
    support = build_causal_support_bundle(ohlc, priority)
    assert support["actionability"]["status"] == "INSUFFICIENT EVIDENCE"
    assert support["regime_conditioned_distributions"]["status"] == "INSUFFICIENT SAMPLE"


def test_regime_conditioned_distribution_shrinks_small_groups_without_unstable_probability():
    ohlc, priority = _fixture(80)
    support = build_causal_support_bundle(ohlc, priority)
    distributions = support["regime_conditioned_distributions"]
    assert set(distributions.get("horizons", {})) == {"1h", "2h", "3h", "6h"}
    assert all(item.get("scope") in {
        "REGIME_SESSION_DIRECTION", "REGIME_DIRECTION", "SESSION_DIRECTION", "DIRECTION",
        "EURUSD_H1_GLOBAL", "SMALL_SAMPLE_GLOBAL", "NONE",
    } for item in distributions["horizons"].values())


def test_mmse_weights_renormalize_existing_paths_and_preserve_audit():
    steps = np.arange(1, 7)
    raw = pd.DataFrame({
        "step": steps,
        "red_path": 1.15 + steps * 0.00010,
        "yellow_path": 1.15 + steps * 0.00008,
        "blue_path": 1.15 + steps * 0.00006,
    })
    main = pd.DataFrame({"step": steps, "main_path": 1.15 + steps * 0.00008, "lower_band": 1.149, "upper_band": 1.151})
    residuals = {}
    for step in steps:
        residuals[f"red_H+{step}"] = [0.00003, -0.00002] * 8
        residuals[f"yellow_H+{step}"] = [0.00005, -0.00004] * 8
        residuals[f"blue_H+{step}"] = [0.00008, -0.00007] * 8
    bundle = {
        "ok": True, "raw": raw, "main": main,
        "path_weights": pd.DataFrame({"step": steps, "red": 1/3, "yellow": 1/3, "blue": 1/3}),
        "summary": {"atr_price": 0.0004, "anchor_price": 1.15},
        "audit": {"horizon_residual_samples": residuals},
    }
    market = pd.DataFrame({"high": [1.151] * 30, "low": [1.149] * 30})
    upgraded = upgrade_projection_bundle(bundle, market_data=market, transition_state="STABLE")
    weights = upgraded["path_weights"][["red", "yellow", "blue"]].sum(axis=1)
    assert np.allclose(weights, 1.0)
    assert "pre_mmse_main" in upgraded["audit"]
    assert upgraded["summary"]["weighting_applied_before_visual_smoothing"] is True
    assert (upgraded["main"]["lower_band"] <= upgraded["main"]["main_path"]).all()
    assert (upgraded["main"]["upper_band"] >= upgraded["main"]["main_path"]).all()


def test_duplicate_evidence_control_excludes_full_metric_authority_from_competition():
    ohlc, priority = _fixture()
    support = build_causal_support_bundle(ohlc, priority)
    control = support["duplicate_evidence_control"]
    assert control["full_metric_authority_excluded_from_competition"] is True
    assert control["families"]["full_metric_scores"]["cap"] == 0.0


def test_public_support_view_keeps_canonical_payload_mobile_safe():
    ohlc, priority = _fixture()
    support = build_causal_support_bundle(ohlc, priority)
    public = public_support_view(support)
    assert "_incremental_cache" not in public
    assert "history" not in public["actionability"]
    assert public["actionability"]["settled_history_count"] > 0
    assert len(public["actionability"]["settled_history_preview"]) <= 24


def test_cache_invalidates_when_protected_metric_changes_on_same_candle():
    ohlc, priority = _fixture()
    first = build_causal_support_bundle(ohlc, priority)
    changed = priority.copy()
    changed.loc[changed.index[-1], "Master /10"] = 8.1
    rebuilt = build_causal_support_bundle(ohlc, changed, previous_cache=first)
    assert rebuilt["cache_status"] == "FULL_REBUILD"
    assert rebuilt["source_signature"] != first["source_signature"]
