"""Canonical copy/export payload service.

Every visible copy location calls this module. Builders are pure and read only a
published canonical generation, compact summary and published risk plan. Copy
All is a structured six-field summary, not a raw canonical/database dump.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

MAX_SHORT_LINES = 40
MAX_SHORT_CHARS = 6_000
TARGET_SHORT_TOKENS = 1_500


def _m(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _text(value: Any, default: str = "-") -> str:
    if not _present(value):
        return default
    if isinstance(value, float):
        if math.isfinite(value):
            return f"{value:.5f}".rstrip("0").rstrip(".")
        return default
    return str(value).strip() or default


def _num(value: Any, digits: int = 2, suffix: str = "") -> str:
    try:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError
        return f"{number:.{digits}f}{suffix}"
    except Exception:
        return "-"



def _published_num(value: Any, digits: int = 2, suffix: str = "") -> str:
    text = _num(value, digits, suffix)
    return "Not published" if text == "-" else text

def _unique_strings(values: Iterable[Any], limit: int = 3, max_len: int = 180) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = " ".join(str(value or "").split())
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…")
        if len(out) >= limit:
            break
    return out


@dataclass(frozen=True)
class PayloadStats:
    characters: int
    lines: int
    estimated_tokens: int


def payload_stats(text: str) -> PayloadStats:
    raw = str(text or "")
    return PayloadStats(len(raw), len(raw.splitlines()), int(math.ceil(len(raw) / 4.0)))


def generation_identity(canonical: Mapping[str, Any]) -> str:
    return "|".join(str(canonical.get(k) or "") for k in ("run_id", "calculation_generation", "checksum", "latest_completed_candle_time"))


def _selected_forecast(canonical: Mapping[str, Any], summary: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]]:
    final = _m(canonical.get("final_decision"))
    selected = final.get("selected_horizon") or _m(summary.get("projection")).get("selected_horizon") or 6
    digits = "".join(ch for ch in str(selected) if ch.isdigit()) or "6"
    key = f"{digits}h"
    horizons = _m(_m(canonical.get("forecasts")).get("horizons"))
    raw = horizons.get(key)
    return key, _m(raw)


def _short_lines(canonical: Mapping[str, Any], summary: Mapping[str, Any], plan: Mapping[str, Any]) -> list[tuple[str, bool]]:
    identity = _m(summary.get("identity")); decision = _m(summary.get("decision")); scores = _m(summary.get("scores"))
    priority = _m(summary.get("priority")); regime = _m(summary.get("regime")); uncertainty = _m(summary.get("uncertainty"))
    projection = _m(summary.get("projection")); validation = _m(summary.get("validation")); final = _m(canonical.get("final_decision"))
    hkey, forecast = _selected_forecast(canonical, summary)
    lower = forecast.get("lower_bound", projection.get("lower_band"))
    upper = forecast.get("upper_bound", projection.get("upper_band"))
    direction = forecast.get("direction") or projection.get("direction") or final.get("directional_market_view")
    reasons = _unique_strings([
        decision.get("main_reason"),
        *list(final.get("supporting_reasons") or []),
        *list(canonical.get("top_reasons") or []),
    ], limit=3)
    warnings = _unique_strings([
        *list(final.get("blocking_reasons") or []),
        final.get("conflict_warning"),
        _m(summary.get("similar_day")).get("conflict_warning"),
        plan.get("reason") if str(plan.get("status", "")).upper() not in {"PASS", "READY", "OK"} else None,
    ], limit=3)
    generation_id = summary.get("calculation_id") or canonical.get("canonical_calculation_id") or canonical.get("run_id")
    run_id = canonical.get("run_id") or identity.get("run_id") or generation_id
    generation = canonical.get("calculation_generation") or identity.get("calculation_generation")
    checksum = canonical.get("checksum")
    completed = identity.get("latest_completed_candle_time") or canonical.get("latest_completed_candle_time")
    price = projection.get("current_close") or canonical.get("last_close") or _m(canonical.get("market")).get("current_price")
    reliability = regime.get("regime_reliability") or _m(canonical.get("regime")).get("reliability")
    freshness = validation.get("stale_status") or validation.get("data_freshness") or _m(canonical.get("data_quality")).get("freshness")
    error = final.get("error_estimate_pct") or uncertainty.get("error_estimate_pct")
    line_items: list[tuple[str, bool]] = [
        ("ADX Quant Pro — Copy Short", True),
        (f"Symbol/timeframe: {_text(identity.get('symbol') or canonical.get('symbol') or 'EURUSD', 'Not published')} {_text(identity.get('timeframe') or canonical.get('timeframe') or 'H1', 'Not published')}", True),
        (f"Completed candle: {_text(completed, 'Not published')}", True),
        (f"Current price: {_text(price, 'Not published')}", True),
        (f"Current decision: {_text(decision.get('current_decision') or final.get('final_decision') or 'WAIT')}", True),
        (f"Less-risky decision: {_text(decision.get('less_risky_bias') or final.get('less_risky_decision') or 'WAIT')}", True),
        (f"Priority/rank: {_text(priority.get('opportunity_quality') or priority.get('knn_priority') or 'WATCH')} / {_text(priority.get('current_rank') or priority.get('rank'), 'Not published')}", True),
        (f"Current regime: {_text(regime.get('directional_regime') or _m(canonical.get('regime')).get('major_regime') or 'UNKNOWN')}", True),
        (f"Regime reliability: {_published_num(reliability, 1, '%')}", True),
        ("Master/Entry/Hold/TP/Exit Risk: " + "/".join(_published_num(scores.get(k), 2) for k in ("master", "entry", "hold", "tp", "exit_risk")), True),
        (f"Forecast direction/horizon: {_text(direction)} / {hkey.upper()}", True),
        (f"Prediction interval: {_text(lower, 'Not published')} to {_text(upper, 'Not published')}", True),
        (f"Uncertainty/error: {_published_num(uncertainty.get('combined'), 1, '%')} / {_published_num(error, 1, '%')}", True),
        (f"Data freshness: {_text(freshness, 'Not published')}", True),
        (f"Generation ID: {_text(run_id, 'Not published')} / {_text(generation, 'Not published')} / {_text(checksum, 'Not published')}", True),
    ]
    for index, reason in enumerate(reasons, 1):
        line_items.append((f"Reason {index}: {reason}", index == 1))
    for index, warning in enumerate(warnings, 1):
        line_items.append((f"Warning {index}: {warning}", False))
    # Optional risk context is removed first when compression is required.
    if _present(plan.get("status")):
        line_items.append((f"Position-sizing status: {_text(plan.get('status'))}", False))
    if _present(plan.get("planned_risk_pct")) or _present(plan.get("planned_dollar_loss")):
        line_items.append((f"Planned risk: {_published_num(plan.get('planned_risk_pct'), 2, '%')} / ${_published_num(plan.get('planned_dollar_loss'), 2)}", False))
    if _present(plan.get("margin_estimate")):
        line_items.append((f"Estimated margin: ${_published_num(plan.get('margin_estimate'), 2)}", False))
    expiry = final.get("decision_expiry_time") or canonical.get("expires_at")
    if _present(expiry):
        line_items.append((f"Decision expiry: {_text(expiry)}", False))
    return line_items


def build_short_payload(canonical: Mapping[str, Any], summary: Mapping[str, Any], plan: Mapping[str, Any]) -> tuple[str, PayloadStats]:
    items = _short_lines(canonical, summary, plan)
    lines = [line for line, _ in items]
    compressed = False

    def over() -> bool:
        text = "\n".join(lines)
        stats = payload_stats(text)
        return stats.lines > MAX_SHORT_LINES or stats.characters > MAX_SHORT_CHARS or stats.estimated_tokens > TARGET_SHORT_TOKENS

    # Remove low-priority optional lines from the end, never slicing a value.
    optional = [line for line, required in reversed(items) if not required]
    while over() and optional:
        candidate = optional.pop(0)
        if candidate in lines:
            lines.remove(candidate)
            compressed = True
    # Shorten verbose reasons/warnings as a second bounded step.
    if over():
        for index, line in enumerate(list(lines)):
            if line.startswith(("Reason ", "Warning ")) and len(line) > 120:
                lines[index] = line[:119].rsplit(" ", 1)[0] + "…"
                compressed = True
    # Required fields alone are comfortably below limits, but enforce by removing
    # only remaining optional reason/warning lines if a pathological value exists.
    while over():
        removable = next((line for line in reversed(lines) if line.startswith(("Reason ", "Warning "))), None)
        if removable is None:
            break
        lines.remove(removable)
        compressed = True
    if compressed:
        lines.append("[Short export compressed to configured limit]")
    text = "\n".join(lines[:MAX_SHORT_LINES])
    # Last-resort whole-line removal; never character-truncate numeric values.
    while len(text) > MAX_SHORT_CHARS and len(lines) > 15:
        lines.pop(-2 if lines[-1].startswith("[") else -1)
        if "[Short export compressed to configured limit]" not in lines:
            lines.append("[Short export compressed to configured limit]")
        text = "\n".join(lines[:MAX_SHORT_LINES])
    return text, payload_stats(text)


def short_text(canonical: Mapping[str, Any], summary: Mapping[str, Any], plan: Mapping[str, Any]) -> str:
    return build_short_payload(canonical, summary, plan)[0]


def _section(title: str, rows: Iterable[tuple[str, Any]]) -> list[str]:
    lines = [f"## {title}"]
    for label, value in rows:
        if _present(value):
            lines.append(f"- {label}: {_text(value)}")
    return lines


def all_text(canonical: Mapping[str, Any], summary: Mapping[str, Any], plan: Mapping[str, Any], readiness: Mapping[str, Any] | None = None) -> str:
    """Structured summaries of all six fields; intentionally excludes raw rows."""
    readiness = _m(readiness)
    identity = _m(summary.get("identity")); decision = _m(summary.get("decision")); scores = _m(summary.get("scores"))
    regime = _m(summary.get("regime")); projection = _m(summary.get("projection")); priority = _m(summary.get("priority"))
    validation = _m(summary.get("validation")); similar = _m(summary.get("similar_day")); final = _m(canonical.get("final_decision"))
    evidence_rows = list(canonical.get("latest_relevant_evidence_rows") or _m(canonical.get("compact_ai_fact_pack")).get("latest_relevant_evidence_rows") or [])
    limitations = _unique_strings([
        *list(canonical.get("known_limitations") or []),
        "Historical summaries are bounded; complete machine-readable data remains in the on-demand JSON export.",
        "No copied summary is a guarantee of future market performance.",
    ], limit=8, max_len=260)
    identity_record = {
        "run_id": canonical.get("run_id") or identity.get("run_id"),
        "generation": canonical.get("calculation_generation") or identity.get("calculation_generation"),
        "checksum": canonical.get("checksum"),
    }
    lines = [
        "ADX Quant Pro — Copy All (Six-Field Structured Summary)",
        f"Generation ID: {_text(summary.get('calculation_id') or canonical.get('run_id'))}",
        "Generation identity JSON: " + json.dumps(identity_record, ensure_ascii=False),
        f"Completed candle: {_text(identity.get('latest_completed_candle_time') or canonical.get('latest_completed_candle_time'))}",
        "",
    ]
    lines += _section("Field 1 — Full Metric 25-Day History + Decision Tables", [
        ("Current decision", decision.get("current_decision")), ("Less-risky decision", decision.get("less_risky_bias")),
        ("Protected scores", "/".join(_num(scores.get(k), 2) for k in ("master", "entry", "hold", "tp", "exit_risk"))),
        ("Priority", priority.get("opportunity_quality")), ("Rank", priority.get("current_rank")),
        ("Position sizing", plan.get("status")), ("Decision 11", _m(canonical.get("medium_standard_regime_bias")).get("decision")),
        ("History summary", "25-day newest-completed-H1-first view; ten protected histories preserved"),
    ])
    lines += [""] + _section("Field 2 — Power BI Price Prediction Path", [
        ("Current price", projection.get("current_close")), ("H+1", projection.get("h1")), ("H+3", projection.get("h3")), ("H+6", projection.get("h6")),
        ("Lower band", projection.get("lower_band")), ("Upper band", projection.get("upper_band")),
        ("Projection confidence", projection.get("projection_confidence")), ("Validation", validation.get("validation_status")),
    ])
    lines += [""] + _section("Field 3 — Regime History + Standards", [
        ("Directional regime", regime.get("directional_regime")), ("Volatility regime", regime.get("volatility_regime")),
        ("Reliability", regime.get("regime_reliability")), ("Transition risk", regime.get("transition_risk")),
        ("Estimated transition window", regime.get("estimated_transition_window")), ("Alpha", regime.get("alpha")), ("Delta", regime.get("delta")),
        ("History summary", "Lower, medium and higher standard 25-day views preserved"),
    ])
    lines += [""] + _section("Field 4 — Dinner Full Combined Intelligence", [
        ("Combined decision", decision.get("current_decision")), ("Forecast agreement", final.get("forecast_agreement")),
        ("KNN priority", priority.get("knn_priority")), ("Greedy priority", priority.get("greedy_priority")),
        ("Similar-day pattern", similar.get("pattern_family")), ("Best historical match", similar.get("best_match_date")),
        ("Similar-day weighted result", similar.get("weighted_result")),
    ])
    lines += [""] + _section("Field 5 — Grounded AI Assistant", [
        ("Architecture", "local lexical RAG + controlled read-only routing + evidence critic + one revision pass"),
        ("Generation grounding", summary.get("calculation_id")), ("Evidence records available", len(evidence_rows)),
        ("External AI", "Not used"),
    ])
    lines += [""] + _section("Field 6 — Future Strategy Research History", [
        ("Evidence status", readiness.get("final_status")),
        ("Persisted research rows", readiness.get("persisted_research_rows")),
        ("Tables with evidence", readiness.get("available_history_tables")),
        ("Configured research tables", readiness.get("configured_history_tables")),
        ("Allowed strategy effect", readiness.get("strategy_influence")),
        ("Direction reversal allowed", readiness.get("direction_reversal_allowed")),
        ("Production influence default", readiness.get("production_influence_default")),
    ])
    lines += ["", "## Evidence and limitations"]
    for row in evidence_rows[:12]:
        if isinstance(row, Mapping):
            lines.append(f"- {_text(row.get('source_name') or row.get('table_name') or 'Evidence')}: {_text(row.get('metric_name') or row.get('condition'))} = {_text(row.get('metric_value') or row.get('value_text') or row.get('value_numeric'))}")
    for limitation in limitations:
        lines.append(f"- Limitation: {limitation}")
    return "\n".join(lines)


def machine_json(canonical: Mapping[str, Any], summary: Mapping[str, Any], plan: Mapping[str, Any]) -> str:
    """Complete machine-readable export, prepared only on explicit demand."""
    payload = {
        "canonical_generation": dict(canonical),
        "compact_display_summary": dict(summary),
        "risk_sizing_plan": dict(plan),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default)


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict("records")
        except Exception:
            try:
                return value.to_dict()
            except Exception:
                pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


__all__ = [
    "MAX_SHORT_LINES", "MAX_SHORT_CHARS", "TARGET_SHORT_TOKENS", "PayloadStats",
    "payload_stats", "generation_identity", "build_short_payload", "short_text", "all_text", "machine_json",
]
