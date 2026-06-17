"""Canonical runtime state, explicit adapters, and atomic publication.

This module contains no calculation formulas.  It enforces one successful
Settings calculation as the authoritative run and exposes one-way compatibility
adapters for legacy renderers.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Tuple

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None  # type: ignore

CANONICAL_KEY = "canonical_decision_result_20260617"
LAST_VALID_KEY = "last_valid_canonical_decision_result_20260617"
STAGING_KEY = "canonical_decision_staging_20260617"
RUNTIME_CONTEXT_KEY = "runtime_context_20260617"
SHARED_KEY = "adx_shared_calc_result_20260615"
LEGACY_SHARED_KEY = "shared_calc_result"
GENERATION_KEY = "successful_calculation_generation_20260617"

REQUIRED_CANONICAL_FIELDS = (
    "run_id", "calculation_generation", "data_signature", "symbol", "timeframe",
    "source", "latest_completed_candle_time", "created_at", "expires_at", "schema_version", "calculation_version",
    "calculation_status",
)

ADAPTER_SPECS: Dict[str, Dict[str, Any]] = {
    "market": {"accepted_legacy_source_keys": ("dv_pp_df", "lunch_5layer_powerbi_df", "last_df", "ohlc_df", "df")},
    "metric": {"accepted_legacy_source_keys": ("lunch_metric_result_cache", "last_result", "current_result")},
    "powerbi": {"accepted_legacy_source_keys": ("dv_pp_base_result", "lunch_5layer_powerbi_result", "lunch_prediction_export")},
    "regime": {"accepted_legacy_source_keys": ("dv_pp_regime_summary", "regime_context_20260614", "canonical_regime_snapshot_20260617")},
    "alpha_delta": {"accepted_legacy_source_keys": ("adx_regime_alpha_delta_20260615", "regime_alpha_delta")},
    "priority": {"accepted_legacy_source_keys": ("canonical_priority_table_20260617", "adx_hourly_priority_calibrated_20260615")},
    "knn_greedy": {"accepted_legacy_source_keys": ("canonical_priority_table_20260617", "three_center_priority_sorted_20260614")},
    "reliability": {"accepted_legacy_source_keys": ("reliability_control_center_20260614", "adx_reliability_calibrated_20260615")},
    "nlp": {"accepted_legacy_source_keys": ("nlp_market_intelligence_result", "regime_nlp_today_table", "nlp_ranked_news_df")},
    "data_mining": {"accepted_legacy_source_keys": ("research_pack_20260612", "final_synced_research_merge_pack_20260612")},
    "prediction_history": {"accepted_legacy_source_keys": ("dv_pp_bt_hist", "prediction_history_df", "prediction_vs_actual_history_df")},
    "ai_grounding": {"accepted_legacy_source_keys": ("adx_ai_grounding_20260615",)},
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_df(value: Any) -> bool:
    return pd is not None and isinstance(value, pd.DataFrame)


def proposed_generation(state: Mapping[str, Any]) -> int:
    """Return the next generation without mutating state."""
    current = state.get(GENERATION_KEY, 0)
    try:
        current = int(current or 0)
    except Exception:
        current = 0
    existing = state.get(CANONICAL_KEY) or state.get(LAST_VALID_KEY) or {}
    if isinstance(existing, dict):
        try:
            current = max(current, int(existing.get("calculation_generation", 0) or 0))
        except Exception:
            pass
    return current + 1


def validate_canonical_result(payload: Any) -> Tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return False, ["canonical result is not a dictionary"]
    for key in REQUIRED_CANONICAL_FIELDS:
        if key not in payload or payload.get(key) in (None, ""):
            errors.append(f"missing {key}")
    try:
        if int(payload.get("calculation_generation", 0) or 0) < 1:
            errors.append("calculation_generation must be positive")
    except Exception:
        errors.append("calculation_generation is invalid")
    status = str(payload.get("calculation_status", "")).upper()
    if not status.startswith("COMPLETED"):
        errors.append(f"calculation_status is not completed: {status or 'missing'}")
    market = payload.get("market") or {}
    if not isinstance(market, dict) or not market.get("latest_completed_candle_time"):
        errors.append("missing latest_completed_candle_time")
    if not isinstance(payload.get("final_decision"), dict):
        errors.append("missing final_decision object")
    return not errors, errors


def canonical_identity(payload: Mapping[str, Any] | None) -> Dict[str, Any]:
    p = payload if isinstance(payload, Mapping) else {}
    market = p.get("market") if isinstance(p.get("market"), Mapping) else {}
    return {
        "run_id": p.get("run_id"),
        "calculation_generation": p.get("calculation_generation"),
        "data_signature": p.get("data_signature"),
        "symbol": p.get("symbol"),
        "timeframe": p.get("timeframe"),
        "source": p.get("source"),
        "latest_completed_candle_time": p.get("latest_completed_candle_time") or market.get("latest_completed_candle_time"),
        "created_at": p.get("created_at"),
        "expires_at": p.get("expires_at"),
        "schema_version": p.get("schema_version"),
        "calculation_version": p.get("calculation_version"),
        "calculation_status": p.get("calculation_status"),
    }


def component_matches_canonical(component: Any, canonical: Mapping[str, Any]) -> Tuple[bool, list[str]]:
    """Validate identity fields for a synchronized component."""
    if not isinstance(component, Mapping):
        return False, ["component is not a mapping"]
    expected = canonical_identity(canonical)
    reasons: list[str] = []
    aliases = {"generation": "calculation_generation", "candle time": "latest_completed_candle_time"}
    for label, key in aliases.items():
        got = component.get(key, component.get(label))
        if got not in (None, "") and str(got) != str(expected.get(key)):
            reasons.append(f"{key} mismatch")
    for key in ("run_id", "symbol", "timeframe", "source", "data_signature"):
        got = component.get(key)
        if got not in (None, "") and str(got) != str(expected.get(key)):
            reasons.append(f"{key} mismatch")
    return not reasons, reasons


def _source_meta(canonical: Mapping[str, Any], component: str) -> Dict[str, Any]:
    meta = canonical_identity(canonical)
    meta.update({
        "adapter": component,
        "accepted_legacy_source_keys": list(ADAPTER_SPECS.get(component, {}).get("accepted_legacy_source_keys", ())),
        "source_timestamp": canonical.get("created_at"),
        "validation_status": "VALID",
    })
    return meta


def _canonical_priority_frame(priority_table: Any, canonical: Mapping[str, Any]):
    if not _is_df(priority_table):
        return pd.DataFrame() if pd is not None else priority_table
    table = priority_table
    identity = canonical_identity(canonical)
    stamp = {
        "run_id": identity["run_id"],
        "generation": identity["calculation_generation"],
        "calculation_generation": identity["calculation_generation"],
        "data_signature": identity["data_signature"],
        "symbol": identity["symbol"],
        "timeframe": identity["timeframe"],
        "source": identity["source"],
        "latest_completed_candle_time": identity["latest_completed_candle_time"],
        "data-quality status": (canonical.get("data_quality") or {}).get("status", "UNKNOWN"),
    }
    # One controlled copy prevents mutating the source table while avoiding many
    # renderer-level copies later.
    table = table.copy(deep=False)
    for key, value in stamp.items():
        table[key] = value

    def first_existing(*names: str):
        return next((table[name] for name in names if name in table.columns), None)

    aliases = {
        "candle time": first_existing("Time", "time", "latest_completed_candle_time"),
        "hour": first_existing("Hour", "hour"),
        "regime": first_existing("Major Regime", "Regime", "regime"),
        "regime reliability": first_existing("Reliability %", "Reliability", "regime reliability"),
        "prediction direction": first_existing("Decision", "Prediction Direction", "prediction direction"),
        "KNN score": first_existing("KNN Score /10", "KNN Score", "Priority Score"),
        "Greedy score": first_existing("Greedy Score /10", "Greedy Score", "Priority Score"),
        "combined score": first_existing("Priority Score", "Combined Score", "combined score"),
        "priority rank": first_existing("Ascending Priority", "KNN Priority", "priority rank"),
        "less-risky bias": first_existing("Less Risky Bias", "Decision", "less-risky bias"),
    }
    for name, values in aliases.items():
        if values is not None:
            table[name] = values
    if "priority label" not in table.columns:
        rank_source = table["priority rank"] if "priority rank" in table.columns else pd.Series(14.0, index=table.index, dtype=float)
        ranks = pd.to_numeric(rank_source, errors="coerce").fillna(14)
        table["priority label"] = ranks.map(lambda rank: "A+" if rank <= 3 else "A" if rank <= 6 else "B" if rank <= 9 else "C" if rank <= 12 else "AVOID")
    if "conflict status" not in table.columns:
        canonical_direction = str((canonical.get("final_decision") or {}).get("directional_market_view") or "WAIT").upper()
        row_direction = table.get("prediction direction", pd.Series("WAIT", index=table.index)).astype(str).str.upper()
        table["conflict status"] = row_direction.map(lambda value: "ALIGNED" if value in {canonical_direction, "WAIT"} or canonical_direction == "WAIT" else "CONFLICT")
    return table


def build_shared_adapter(
    state: Mapping[str, Any], canonical: Mapping[str, Any], legacy_shared: Optional[Mapping[str, Any]] = None,
    priority_table: Any = None,
) -> Dict[str, Any]:
    """Create one-way legacy views derived from the authoritative canonical run."""
    legacy = dict(legacy_shared or {})
    final = dict(canonical.get("final_decision") or {})
    market = dict(canonical.get("market") or {})
    regime = dict(canonical.get("regime") or {})
    reliability = dict(canonical.get("reliability") or {})
    nlp = dict(canonical.get("nlp") or {})
    priority = dict(canonical.get("priority") or {})
    forecasts = dict(canonical.get("forecasts") or {})
    horizons = dict(forecasts.get("horizons") or {})
    selected = int(final.get("selected_horizon") or forecasts.get("selected_horizon") or 3)
    selected_forecast = dict(horizons.get(f"{selected}h") or {})
    table = _canonical_priority_frame(priority_table, canonical)
    if not _is_df(table):
        existing = state.get("canonical_priority_table_20260617")
        table = _canonical_priority_frame(existing, canonical) if _is_df(existing) else (pd.DataFrame() if pd is not None else None)

    current = {
        "symbol": canonical.get("symbol"), "timeframe": canonical.get("timeframe"), "source": canonical.get("source"),
        "last_close": market.get("current_price"), "regime": regime.get("major_regime", "UNKNOWN"),
        "regime_direction": final.get("directional_market_view", "WAIT"),
        "prediction_direction": selected_forecast.get("direction", "WAIT"),
        "decision": final.get("final_decision", "DATA NOT READY"),
        "less_risky_decision": final.get("less_risky_decision", "WAIT"),
        "forecast_close": selected_forecast.get("point_forecast"),
        "forecast_confidence": final.get("calibrated_confidence"),
        "selected_horizon": selected,
        "decision_policy": final.get("main_reason", ""),
        "run_id": canonical.get("run_id"), "calculation_generation": canonical.get("calculation_generation"),
        "data_signature": canonical.get("data_signature"),
    }
    old_powerbi = legacy.get("powerbi") if isinstance(legacy.get("powerbi"), dict) else {}
    old_nlp = legacy.get("nlp") if isinstance(legacy.get("nlp"), dict) else {}
    old_data_mining = legacy.get("data_mining") if isinstance(legacy.get("data_mining"), dict) else {}
    old_history = legacy.get("history") if isinstance(legacy.get("history"), dict) else {}
    old_market = legacy.get("market") if isinstance(legacy.get("market"), dict) else {}

    adapter = {
        "version": "20260617_canonical_adapter_v1",
        "built_at": canonical.get("created_at"),
        "signature": canonical.get("data_signature"),
        "canonical": dict(canonical),
        **canonical_identity(canonical),
        "current": current,
        "market": {**old_market, **current, "latest_completed_candle_time": market.get("latest_completed_candle_time"), "row_count": market.get("row_count"), "adapter_meta": _source_meta(canonical, "market")},
        "decision": {"central_decision": final.get("final_decision"), "less_risky_decision": final.get("less_risky_decision"), "selected_horizon": selected, "adapter_meta": _source_meta(canonical, "metric")},
        "regime": {"current": regime.get("major_regime"), "direction": final.get("directional_market_view"), "alpha_delta": {"alpha": regime.get("alpha"), "delta": regime.get("delta"), "delta_acceleration": regime.get("delta_acceleration")}, "standards": {"lower": regime.get("lower_standard_regime"), "middle": regime.get("middle_standard_regime"), "higher": regime.get("higher_standard_regime")}, "adapter_meta": _source_meta(canonical, "regime")},
        "priority": {"table": table, "best": table.iloc[0].to_dict() if _is_df(table) and not table.empty else priority, "summary": priority, "adapter_meta": _source_meta(canonical, "priority")},
        "hourly_priority_table": table,
        "reliability": {**reliability, "selected_horizon": selected, "selected_horizon_validation": (reliability.get("validation_by_horizon") or {}).get(f"{selected}h", {}), "selected_horizon_calibration": (reliability.get("calibration_by_horizon") or {}).get(f"{selected}h", {}), "adapter_meta": _source_meta(canonical, "reliability")},
        "reliability_calibration": reliability,
        "powerbi": {**old_powerbi, "forecast_close": selected_forecast.get("point_forecast"), "lower_bound": selected_forecast.get("lower_bound"), "upper_bound": selected_forecast.get("upper_bound"), "direction": selected_forecast.get("direction"), "selected_horizon": selected, "adapter_meta": _source_meta(canonical, "powerbi")},
        "nlp": {**old_nlp, "summary": {**(old_nlp.get("summary") or {}), "nlp_direction": nlp.get("direction", "WAIT"), "reliability": nlp.get("reliability", 0), "conflict_level": nlp.get("conflict_level", "NONE"), "latest_rank_1_news": nlp.get("latest_headline", "No relevant news"), "news_time": nlp.get("latest_time"), "less_risky_decision": final.get("less_risky_decision", "WAIT")}, "adapter_meta": _source_meta(canonical, "nlp")},
        "data_mining": {**old_data_mining, "adapter_meta": _source_meta(canonical, "data_mining")},
        "history": {**old_history, "priority": table, "adapter_meta": _source_meta(canonical, "prediction_history")},
        "prediction_feedback": legacy.get("prediction_feedback", {}),
        "regime_alpha_delta": {"alpha": regime.get("alpha"), "delta": regime.get("delta"), "delta_acceleration": regime.get("delta_acceleration")},
        "ai_grounding": {"decision": final.get("final_decision"), "less_risky_decision": final.get("less_risky_decision"), "regime": regime.get("major_regime"), "prediction_direction": selected_forecast.get("direction"), "selected_horizon": selected, "reliability_score": reliability.get("score", 0), "data_quality_score": (canonical.get("data_quality") or {}).get("score", 0), "run_id": canonical.get("run_id"), "calculation_generation": canonical.get("calculation_generation"), "adapter_meta": _source_meta(canonical, "ai_grounding")},
        "adapter_specs": deepcopy(ADAPTER_SPECS),
        "metadata": {"calculation_source": "canonical_decision_result_20260617", "one_way_legacy_adapter": True, **canonical_identity(canonical)},
    }
    return adapter


def publish_canonical_atomically(
    state: MutableMapping[str, Any], canonical: Dict[str, Any], *, legacy_shared: Optional[Mapping[str, Any]] = None,
    priority_table: Any = None,
) -> Dict[str, Any]:
    """Validate staging data and publish all synchronized keys as one generation.

    The last valid canonical run remains untouched if validation fails.
    """
    ok, errors = validate_canonical_result(canonical)
    if not ok:
        state["canonical_publish_error_20260617"] = errors
        state.pop(STAGING_KEY, None)
        raise ValueError("Canonical validation failed: " + "; ".join(errors))
    generation = int(canonical["calculation_generation"])
    table = _canonical_priority_frame(priority_table, canonical)
    canonical = deepcopy(canonical)
    if _is_df(table):
        canonical["priority_table"] = table.to_dict("records")
    adapter = build_shared_adapter(state, canonical, legacy_shared=legacy_shared, priority_table=table)
    staging = {"canonical": canonical, "adapter": adapter, "priority_table": table, "published_at": _utc_now_iso()}
    state[STAGING_KEY] = staging

    # Compatibility values are references to the same validated objects; they are
    # not separately recalculated copies.
    state["canonical_priority_table_20260617"] = table
    state["adx_hourly_priority_calibrated_20260615"] = table
    state["three_center_priority_sorted_20260614"] = table
    state["reliability_dynamic_priority_table_20260614"] = table
    state[SHARED_KEY] = adapter
    state[LEGACY_SHARED_KEY] = adapter
    state["canonical_decision_result"] = canonical
    state[LAST_VALID_KEY] = canonical
    state[GENERATION_KEY] = generation
    # Authoritative pointer is written last.
    state[CANONICAL_KEY] = canonical
    state["canonical_publish_error_20260617"] = []
    state.pop(STAGING_KEY, None)
    return adapter


def get_canonical(state: Mapping[str, Any]) -> Dict[str, Any]:
    current = state.get(CANONICAL_KEY)
    if isinstance(current, dict) and validate_canonical_result(current)[0]:
        return current
    previous = state.get(LAST_VALID_KEY)
    return previous if isinstance(previous, dict) and validate_canonical_result(previous)[0] else {}


def begin_rerun(state: MutableMapping[str, Any]) -> int:
    try:
        value = int(state.get("app_rerun_identifier_20260617", 0) or 0) + 1
    except Exception:
        value = 1
    state["app_rerun_identifier_20260617"] = value
    state["shared_sync_calls_this_rerun_20260617"] = 0
    state["navigation_authoritative_20260617"] = False
    return value


def build_runtime_context(state: MutableMapping[str, Any], *, active_page: str, active_subpage: str, phone_mode: bool) -> Dict[str, Any]:
    canonical = get_canonical(state)
    identity = canonical_identity(canonical)
    context = {
        "rerun_identifier": state.get("app_rerun_identifier_20260617", 0),
        "active_page": active_page,
        "active_subpage": active_subpage,
        "phone_mode": bool(phone_mode),
        "canonical_result": canonical,
        "canonical_run_id": identity.get("run_id"),
        "canonical_generation": identity.get("calculation_generation"),
        "data_signature": identity.get("data_signature"),
        "symbol": identity.get("symbol") or state.get("symbol"),
        "timeframe": identity.get("timeframe") or state.get("timeframe"),
        "source": identity.get("source") or state.get("source"),
        "canonical_status": "READY" if canonical else "DATA NOT READY",
    }
    state[RUNTIME_CONTEXT_KEY] = context
    state["navigation_authoritative_20260617"] = True
    return context


def shared_from_runtime(state: Mapping[str, Any]) -> Dict[str, Any]:
    value = state.get(SHARED_KEY) or state.get(LEGACY_SHARED_KEY)
    return value if isinstance(value, dict) else {}
