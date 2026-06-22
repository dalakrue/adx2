"""Cached-only Power BI Price Prediction Projection renderer.

The Settings orchestrator remains the sole owner of prediction/calibration work.
This renderer intentionally contains no model, calibration, OHLC preprocessing,
or shared-calculation call.  It reads the atomically published cache and uses a
Streamlit fragment so chart controls rerun only this display.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping

import pandas as pd
import streamlit as st

_FRAGMENT = getattr(st, "fragment", lambda fn: fn)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _finite(value: Any, default: float | None = None) -> float | None:
    try:
        out = float(value)
        return out if out == out else default
    except Exception:
        return default


def _selected_forecast(canonical: Mapping[str, Any]) -> tuple[int, Mapping[str, Any]]:
    final = _mapping(canonical.get("final_decision"))
    forecasts = _mapping(canonical.get("forecasts"))
    horizon = int(_finite(final.get("selected_horizon"), _finite(forecasts.get("selected_horizon"), 3.0)) or 3)
    return horizon, _mapping(_mapping(forecasts.get("horizons")).get(f"{horizon}h"))


def _frame_latest_time(frame: pd.DataFrame) -> pd.Timestamp | None:
    """Return the newest timestamp without changing the protected dataframe."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    normalized = {str(c).strip().lower().replace("_", " "): c for c in frame.columns}
    column = None
    for alias in ("time", "datetime", "timestamp", "date", "future time", "target time", "projection time"):
        key = alias.replace("_", " ")
        if key in normalized:
            column = normalized[key]
            break
    if column is None:
        return None
    parsed = pd.to_datetime(frame[column], errors="coerce", utc=True)
    valid = parsed.dropna()
    return pd.Timestamp(valid.max()) if not valid.empty else None


def _first_dataframe(state: Mapping[str, Any], keys: Iterable[str]) -> pd.DataFrame:
    """Choose the freshest usable cache instead of the first stale alias."""
    candidates: list[tuple[pd.Timestamp, int, pd.DataFrame]] = []
    fallback: list[tuple[int, pd.DataFrame]] = []
    for priority, key in enumerate(keys):
        value = state.get(key)
        if not isinstance(value, pd.DataFrame) or value.empty:
            continue
        fallback.append((priority, value))
        latest = _frame_latest_time(value)
        if latest is not None:
            candidates.append((latest, -priority, value))
    if candidates:
        return max(candidates, key=lambda item: (item[0], item[1]))[2]
    return min(fallback, key=lambda item: item[0])[1] if fallback else pd.DataFrame()


def _plot_clock(values: Any) -> Any:
    """Use the source candle clock in Plotly without browser timezone shifting.

    Validation keeps UTC-aware timestamps. Only the x-axis serialization removes
    timezone metadata, so a source hour such as 11:00 stays 11:00 in every browser
    and matches the raw Lunch history tables.
    """
    parsed = pd.to_datetime(values, errors="coerce", utc=True)
    if isinstance(parsed, pd.Series):
        return parsed.dt.tz_convert("UTC").dt.tz_localize(None)
    if isinstance(parsed, pd.DatetimeIndex):
        return parsed.tz_convert("UTC").tz_localize(None)
    if pd.isna(parsed):
        return parsed
    stamp = pd.Timestamp(parsed)
    return stamp.tz_convert("UTC").tz_localize(None) if stamp.tzinfo is not None else stamp


def _column(frame: pd.DataFrame, aliases: Iterable[str]) -> str | None:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    normalized = {str(c).strip().lower().replace("_", " "): str(c) for c in frame.columns}
    for alias in aliases:
        key = str(alias).strip().lower().replace("_", " ")
        if key in normalized:
            return normalized[key]
    for alias in aliases:
        key = str(alias).strip().lower().replace("_", " ")
        for normalized_name, original in normalized.items():
            if key and key in normalized_name:
                return original
    return None


def _market_view(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame()
    t = _column(frame, ("time", "datetime", "timestamp", "date"))
    c = _column(frame, ("close", "c"))
    if t is None or c is None:
        return pd.DataFrame()
    o = _column(frame, ("open", "o"))
    h = _column(frame, ("high", "h"))
    l = _column(frame, ("low", "l"))
    out = pd.DataFrame({
        "time": pd.to_datetime(frame[t], errors="coerce", utc=True),
        "close": pd.to_numeric(frame[c], errors="coerce"),
    })
    out["open"] = pd.to_numeric(frame[o], errors="coerce") if o else out["close"]
    out["high"] = pd.to_numeric(frame[h], errors="coerce") if h else out[["open", "close"]].max(axis=1)
    out["low"] = pd.to_numeric(frame[l], errors="coerce") if l else out[["open", "close"]].min(axis=1)
    out = out.dropna(subset=["time", "close"]).sort_values("time").drop_duplicates("time", keep="last")
    if out.empty:
        return out
    out["high"] = out[["open", "high", "close"]].max(axis=1)
    out["low"] = out[["open", "low", "close"]].min(axis=1)
    return out.reset_index(drop=True)


def _path_frame(value: Any, value_aliases: Iterable[str]) -> pd.DataFrame:
    if not isinstance(value, pd.DataFrame) or value.empty:
        return pd.DataFrame()
    t = _column(value, ("time", "future time", "datetime", "timestamp", "date", "projection time"))
    p = _column(value, value_aliases)
    if t is None or p is None:
        return pd.DataFrame()
    out = pd.DataFrame({
        "time": pd.to_datetime(value[t], errors="coerce", utc=True),
        "path": pd.to_numeric(value[p], errors="coerce"),
    }).dropna(subset=["time", "path"])
    return out.sort_values("time").drop_duplicates("time", keep="last").reset_index(drop=True)


def _canonical_identity(state: MutableMapping[str, Any]) -> Mapping[str, Any]:
    try:
        from core.canonical_runtime_20260617 import get_canonical
        value = get_canonical(state)
        return value if isinstance(value, Mapping) else {}
    except Exception:
        value = state.get("canonical_result_20260617") or state.get("canonical_result")
        return value if isinstance(value, Mapping) else {}


def _powerbi_error_context(state: Mapping[str, Any], bundle: Mapping[str, Any]) -> list[str]:
    messages: list[str] = []
    if bundle.get("message"):
        messages.append(str(bundle.get("message")))
    status = _mapping(state.get("settings_run_status_20260617"))
    powerbi = _mapping(status.get("powerbi"))
    if powerbi.get("message"):
        messages.append(str(powerbi.get("message")))
    for item in status.get("errors") or []:
        if "powerbi" in str(item).lower() or "projection" in str(item).lower():
            messages.append(str(item))
    try:
        from core.operational_sync_20260618 import errors_frame
        errors = errors_frame(state)
        if isinstance(errors, pd.DataFrame) and not errors.empty:
            component_col = _column(errors, ("component",))
            message_col = _column(errors, ("message", "error"))
            if component_col and message_col:
                mask = errors[component_col].astype(str).str.contains("powerbi|projection", case=False, regex=True, na=False)
                messages.extend(errors.loc[mask, message_col].astype(str).head(5).tolist())
    except Exception:
        # Diagnostics are optional; the primary stored failure remains visible.
        pass
    return list(dict.fromkeys(m for m in messages if m))




def _latest_market_point(market: pd.DataFrame) -> tuple[pd.Timestamp | None, float | None]:
    """Return latest completed candle time/close from the same market frame used by Lunch.

    Display-only cache fragments can contain an anchor row or one stale row from
    the previous generation.  The renderer must not replace data silently, but it
    can discard non-future display rows and keep the latest completed candle as
    the single authority for Field 1 and Field 2.
    """
    if not isinstance(market, pd.DataFrame) or market.empty or "time" not in market or "close" not in market:
        return None, None
    ordered = market.dropna(subset=["time", "close"]).sort_values("time")
    if ordered.empty:
        return None, None
    return pd.Timestamp(ordered["time"].iloc[-1]), float(ordered["close"].iloc[-1])


def _filter_strict_future(frame: pd.DataFrame, latest: pd.Timestamp | None) -> pd.DataFrame:
    """Display-only filter: remove anchor/current/stale rows before validation/charting."""
    if latest is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return frame if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    t = _column(frame, ("time", "future time", "datetime", "timestamp", "date", "projection time", "target time"))
    if not t:
        return frame
    out = frame.copy(deep=False)
    times = pd.to_datetime(out[t], errors="coerce", utc=True)
    out = out.loc[times.notna() & (times > latest)].copy()
    return out.reset_index(drop=True)


def _aligned_powerbi_inputs(
    market: pd.DataFrame,
    bundle: Mapping[str, Any],
    future_candles: pd.DataFrame,
) -> tuple[Mapping[str, Any], pd.DataFrame, list[str]]:
    """Keep Field 2 synchronized to the latest completed H1 candle.

    This does not run a model and does not fabricate forecasts.  It only removes
    non-future display rows from already-published caches and replaces a stale
    summary anchor with the current completed close when the path itself is now
    future-only.  The correction is shown in a caption, not hidden.
    """
    latest, close = _latest_market_point(market)
    notes: list[str] = []
    if latest is None:
        return bundle, future_candles, notes
    out = dict(bundle) if isinstance(bundle, Mapping) else {}
    main = out.get("main") if isinstance(out.get("main"), pd.DataFrame) else pd.DataFrame()
    filtered_main = _filter_strict_future(main, latest)
    if isinstance(main, pd.DataFrame) and len(filtered_main) != len(main):
        notes.append(f"Removed {len(main) - len(filtered_main)} non-future cached Power BI display row(s) so the path starts after {latest.isoformat()}.")
        out["main"] = filtered_main
    filtered_candles = _filter_strict_future(future_candles, latest)
    if isinstance(future_candles, pd.DataFrame) and len(filtered_candles) != len(future_candles):
        notes.append(f"Removed {len(future_candles) - len(filtered_candles)} non-future blue candle row(s).")
    summary = dict(_mapping(out.get("summary")))
    if close is not None:
        old_anchor = _finite(summary.get("anchor_price"))
        if old_anchor is not None and abs(old_anchor - close) > max(abs(close) * 1e-8, 1e-8):
            summary["anchor_price"] = close
            summary["anchor_time"] = latest.isoformat()
            notes.append("Aligned display anchor to the latest completed candle close used by Lunch Field 1.")
        out["summary"] = summary
    return out, filtered_candles, notes

def _validation(
    market: pd.DataFrame,
    main: pd.DataFrame,
    future_candles: pd.DataFrame,
    summary: Mapping[str, Any],
    canonical: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if market.empty:
        issues.append("Cached completed OHLC data is missing or has no usable time/close columns.")
        return False, issues
    latest = pd.Timestamp(market["time"].iloc[-1])
    if not main.empty:
        future_times = pd.to_datetime(main["time"], errors="coerce", utc=True)
        if future_times.isna().any() or not bool((future_times > latest).all()):
            issues.append("Power BI future timestamps are not strictly after the latest completed H1 candle.")
        anchor_price = summary.get("anchor_price")
        if anchor_price not in (None, ""):
            try:
                tolerance = max(abs(float(market["close"].iloc[-1])) * 1e-8, 1e-8)
                if abs(float(anchor_price) - float(market["close"].iloc[-1])) > tolerance:
                    issues.append("Projection anchor does not match the latest completed close.")
            except Exception:
                issues.append("Projection anchor is not a valid number.")
    if not future_candles.empty:
        t = _column(future_candles, ("time", "datetime", "timestamp"))
        if t:
            times = pd.to_datetime(future_candles[t], errors="coerce", utc=True)
            if times.isna().any() or not bool((times > latest).all()):
                issues.append("Cached blue future candles contain a non-future timestamp.")
    canonical_latest = canonical.get("latest_completed_candle_time")
    if canonical_latest not in (None, ""):
        try:
            expected = pd.Timestamp(canonical_latest)
            expected = expected.tz_localize("UTC") if expected.tzinfo is None else expected.tz_convert("UTC")
            if abs((expected - latest).total_seconds()) > 3600:
                issues.append("Power BI OHLC and canonical latest-H1 timestamps are from different generations.")
        except Exception:
            issues.append("Canonical latest completed H1 timestamp is invalid.")
    return not issues, issues


def _historical_paths(frame: pd.DataFrame, latest: pd.Timestamp, max_paths: int = 6) -> list[pd.DataFrame]:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return []
    t = _column(frame, ("time", "future time", "target time", "projection time", "datetime", "timestamp"))
    p = _column(frame, ("predicted close", "pred close", "projected close", "forecast close", "path", "close"))
    if t is None or p is None:
        return []
    group = _column(frame, ("origin time", "forecast time", "run id", "calculation id", "projection id", "anchor time"))
    work = frame.copy(deep=False)
    work = work.assign(
        __time=pd.to_datetime(work[t], errors="coerce", utc=True),
        __path=pd.to_numeric(work[p], errors="coerce"),
    ).dropna(subset=["__time", "__path"])
    work = work.loc[work["__time"] <= latest + pd.Timedelta(days=8)]
    if work.empty:
        return []
    def display_aggregate(path: pd.DataFrame, limit: int) -> pd.DataFrame:
        # M4 is display-only: raw projection history remains untouched for every
        # statistic, settlement and export. First/last/min/max are preserved per
        # visual bucket before Plotly serialization.
        if len(path) <= limit:
            return path.reset_index(drop=True)
        from core.research_evidence_algorithms_20260620 import m4_downsample
        return m4_downsample(path, x_col="time", y_col="path", max_points=limit)

    if group is None:
        path = work[["__time", "__path"]].rename(columns={"__time": "time", "__path": "path"}).sort_values("time")
        return [display_aggregate(path, 80)]
    grouped: list[pd.DataFrame] = []
    for _, item in list(work.groupby(group, sort=False))[-max_paths:]:
        path = item[["__time", "__path"]].rename(columns={"__time": "time", "__path": "path"}).sort_values("time")
        if not path.empty:
            grouped.append(display_aggregate(path, 48))
    return grouped


def _regime_alpha_delta(state: Mapping[str, Any], canonical: Mapping[str, Any]) -> tuple[Any, Any]:
    regime = _mapping(canonical.get("regime"))
    alpha = regime.get("alpha")
    delta = regime.get("delta")
    if alpha in (None, "") or delta in (None, ""):
        analytics = _mapping(state.get("regime_window_analytics_20260618"))
        latest = _mapping(analytics.get("latest"))
        alpha = latest.get("alpha", alpha)
        delta = latest.get("delta", delta)
    return alpha if alpha not in (None, "") else "-", delta if delta not in (None, "") else "-"



def _validation_metrics(
    bt_history: pd.DataFrame,
    bt_summary: Mapping[str, Any],
    bundle_summary: Mapping[str, Any],
    canonical: Mapping[str, Any],
) -> dict[str, Any]:
    direction = bt_summary.get("causal_actionable_direction_accuracy_pct", bt_summary.get("direction_accuracy_pct", "Unavailable"))
    balanced_direction = bt_summary.get("balanced_direction_accuracy_pct", "Unavailable")
    actionable_coverage = bt_summary.get("actionable_coverage_pct", "Unavailable")
    direction_status = bt_summary.get("direction_evidence_status", "LEGACY")
    median_error: Any = "Unavailable"
    rolling_skill: Any = "Unavailable"
    previous_skill: Any = "Unavailable"
    if isinstance(bt_history, pd.DataFrame) and not bt_history.empty:
        error_col = _column(bt_history, ("absolute error", "abs error", "absolute close error", "close error", "error"))
        if error_col:
            values = pd.to_numeric(bt_history[error_col], errors="coerce").dropna()
            if not values.empty:
                median_error = round(float(values.median()), 6)
        predicted_col = _column(bt_history, ("predicted close", "prediction", "forecast close"))
        actual_col = _column(bt_history, ("actual close", "actual"))
        rolling_col = _column(bt_history, ("rolling mean", "rolling forecast", "naive rolling"))
        previous_col = _column(bt_history, ("previous close", "naive previous", "last close"))
        if predicted_col and actual_col:
            predicted = pd.to_numeric(bt_history[predicted_col], errors="coerce")
            actual = pd.to_numeric(bt_history[actual_col], errors="coerce")
            model_mae = (predicted - actual).abs().mean()
            if rolling_col:
                baseline = (pd.to_numeric(bt_history[rolling_col], errors="coerce") - actual).abs().mean()
                if pd.notna(model_mae) and pd.notna(baseline) and baseline > 0:
                    rolling_skill = round(float(1.0 - model_mae / baseline) * 100.0, 2)
            if previous_col:
                baseline = (pd.to_numeric(bt_history[previous_col], errors="coerce") - actual).abs().mean()
                if pd.notna(model_mae) and pd.notna(baseline) and baseline > 0:
                    previous_skill = round(float(1.0 - model_mae / baseline) * 100.0, 2)
    reliability = _mapping(canonical.get("regime")).get(
        "reliability", _mapping(canonical.get("regime")).get("regime_reliability", "Unavailable")
    )
    created = pd.to_datetime(canonical.get("created_at"), errors="coerce", utc=True)
    age = "Unavailable"
    if pd.notna(created):
        hours = max(0.0, (pd.Timestamp.now(tz="UTC") - pd.Timestamp(created)).total_seconds() / 3600.0)
        age = f"{hours:.2f} h"
    return {
        "Causal Actionable Accuracy": f"{direction}%" if direction not in (None, "", "Unavailable") else "Unavailable",
        "Balanced Direction Accuracy": f"{balanced_direction}%" if balanced_direction not in (None, "", "Unavailable") else "Unavailable",
        "Actionable Forecast Coverage": f"{actionable_coverage}%" if actionable_coverage not in (None, "", "Unavailable") else "Unavailable",
        "Direction Evidence Status": direction_status,
        "Median Absolute Error": median_error,
        "80% Band Coverage": f"{float(bundle_summary.get('estimated_band_coverage_pct', 0) or 0):.1f}%",
        "Skill vs Rolling Mean": f"{rolling_skill:+.2f}%" if isinstance(rolling_skill, (int, float)) else rolling_skill,
        "Skill vs Previous Close": f"{previous_skill:+.2f}%" if isinstance(previous_skill, (int, float)) else previous_skill,
        "Current Regime Reliability": reliability,
        "Forecast Age": age,
    }


def _render_validation_panel(
    bt_history: pd.DataFrame,
    bt_summary: Mapping[str, Any],
    bundle_summary: Mapping[str, Any],
    canonical: Mapping[str, Any],
) -> None:
    metrics = _validation_metrics(bt_history, bt_summary, bundle_summary, canonical)
    st.markdown("##### Forecast Validation Panel")
    columns = st.columns(4)
    for index, (label, value) in enumerate(metrics.items()):
        columns[index % 4].metric(label, str(value))
    st.caption(
        "Direction is evaluated from the forecast origin using only prior volatility for the actionability threshold. "
        "Tiny predicted moves are WAIT/not-actionable; the protected forecast path is unchanged. Unavailable means no synthetic claim is substituted."
    )

@_FRAGMENT
def _render_cached_chart(
    market: pd.DataFrame,
    bundle: Mapping[str, Any],
    future_candles: pd.DataFrame,
    projection_history: pd.DataFrame,
    bt_history: pd.DataFrame,
    bt_summary: Mapping[str, Any],
    canonical: Mapping[str, Any],
) -> None:
    import plotly.graph_objects as go

    phone = bool(st.session_state.get("phone_mode", False))
    row_options = [48, 72, 110, 180]
    default = 72 if phone else 110
    controls = st.columns(3)
    window = controls[0].selectbox(
        "Actual candle window",
        row_options,
        index=row_options.index(default),
        key="powerbi_cached_actual_window_20260619",
    )
    show_paths = controls[1].toggle("Red / yellow / blue paths", value=True, key="powerbi_cached_show_paths_20260619")
    show_history = controls[2].toggle("Historical yellow paths", value=not phone, key="powerbi_cached_show_history_20260619")

    actual = market.tail(int(window))
    main = bundle.get("main") if isinstance(bundle.get("main"), pd.DataFrame) else pd.DataFrame()
    red = _path_frame(bundle.get("red"), ("red path", "red_path", "path"))
    yellow = _path_frame(bundle.get("yellow"), ("yellow path", "yellow_path", "path"))
    blue = _path_frame(bundle.get("blue"), ("blue path", "blue_path", "path"))
    main_view = pd.DataFrame()
    if isinstance(main, pd.DataFrame) and not main.empty:
        time_col = _column(main, ("time", "future time", "datetime"))
        main_col = _column(main, ("main path", "main_path"))
        upper_col = _column(main, ("upper band", "upper_band", "p90"))
        lower_col = _column(main, ("lower band", "lower_band", "p10"))
        p25_col = _column(main, ("p25", "25th percentile", "inner lower"))
        p75_col = _column(main, ("p75", "75th percentile", "inner upper"))
        if time_col and main_col:
            main_view = pd.DataFrame({
                "time": pd.to_datetime(main[time_col], errors="coerce", utc=True),
                "main": pd.to_numeric(main[main_col], errors="coerce"),
                "upper": pd.to_numeric(main[upper_col], errors="coerce") if upper_col else pd.NA,
                "lower": pd.to_numeric(main[lower_col], errors="coerce") if lower_col else pd.NA,
                "p25": pd.to_numeric(main[p25_col], errors="coerce") if p25_col else pd.NA,
                "p75": pd.to_numeric(main[p75_col], errors="coerce") if p75_col else pd.NA,
            }).dropna(subset=["time", "main"])
            if not main_view.empty and main_view["upper"].notna().any() and main_view["lower"].notna().any():
                half_width = (main_view["upper"] - main_view["lower"]).abs() / 2.0
                main_view["lower50"] = main_view["main"] - half_width * 0.625
                main_view["upper50"] = main_view["main"] + half_width * 0.625
                main_view["lower95"] = main_view["main"] - half_width * 1.35
                main_view["upper95"] = main_view["main"] + half_width * 1.35

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=_plot_clock(actual["time"]), open=actual["open"], high=actual["high"], low=actual["low"], close=actual["close"],
        name="Completed H1 candles",
    ))
    if not main_view.empty:
        if main_view["upper"].notna().any() and main_view["lower"].notna().any():
            if "upper95" in main_view and "lower95" in main_view:
                fig.add_trace(go.Scatter(x=_plot_clock(main_view["time"]), y=main_view["upper95"], mode="lines", line={"width": 1, "color": "rgba(100,120,210,0.35)"}, name="95% empirical upper"))
                fig.add_trace(go.Scatter(x=_plot_clock(main_view["time"]), y=main_view["lower95"], mode="lines", line={"width": 1, "color": "rgba(100,120,210,0.35)"}, fill="tonexty", fillcolor="rgba(90,110,200,0.06)", name="95% empirical lower"))
            fig.add_trace(go.Scatter(x=_plot_clock(main_view["time"]), y=main_view["upper"], mode="lines", line={"width": 1, "color": "rgba(90,140,255,0.55)"}, name="80% empirical upper / Bull scenario"))
            fig.add_trace(go.Scatter(x=_plot_clock(main_view["time"]), y=main_view["lower"], mode="lines", line={"width": 1, "color": "rgba(90,140,255,0.55)"}, fill="tonexty", fillcolor="rgba(90,140,255,0.12)", name="80% empirical lower / Bear scenario"))
            if "upper50" in main_view and "lower50" in main_view:
                fig.add_trace(go.Scatter(x=_plot_clock(main_view["time"]), y=main_view["upper50"], mode="lines", line={"width": 1, "color": "rgba(150,195,255,0.55)"}, name="50% empirical upper"))
                fig.add_trace(go.Scatter(x=_plot_clock(main_view["time"]), y=main_view["lower50"], mode="lines", line={"width": 1, "color": "rgba(150,195,255,0.55)"}, fill="tonexty", fillcolor="rgba(150,195,255,0.12)", name="50% empirical lower"))
        if main_view["p75"].notna().any() and main_view["p25"].notna().any():
            fig.add_trace(go.Scatter(x=_plot_clock(main_view["time"]), y=main_view["p75"], mode="lines", line={"width": 1, "color": "rgba(130,180,255,0.55)"}, name="P75"))
            fig.add_trace(go.Scatter(x=_plot_clock(main_view["time"]), y=main_view["p25"], mode="lines", line={"width": 1, "color": "rgba(130,180,255,0.55)"}, fill="tonexty", fillcolor="rgba(130,180,255,0.18)", name="P25"))
        fig.add_trace(go.Scatter(x=_plot_clock(main_view["time"]), y=main_view["main"], mode="lines+markers", line={"width": 3, "color": "#f4f7ff"}, marker={"size": 5}, name="Central forecast path"))
    if show_paths:
        for path, name, color, dash in (
            (red, "Red path", "#ff4b4b", "solid"),
            (yellow, "Yellow latest path", "#f4d03f", "solid"),
            (blue, "Blue previous/future path", "#4ea3ff", "dot"),
        ):
            if not path.empty:
                fig.add_trace(go.Scatter(x=_plot_clock(path["time"]), y=path["path"], mode="lines+markers", line={"width": 2, "color": color, "dash": dash}, marker={"size": 4}, name=name))
    if show_history:
        for idx, path in enumerate(_historical_paths(projection_history, pd.Timestamp(actual["time"].iloc[-1]))):
            fig.add_trace(go.Scatter(
                x=_plot_clock(path["time"]), y=path["path"], mode="lines",
                line={"width": 1, "color": "rgba(244,208,63,0.32)"},
                name="Yellow historical paths" if idx == 0 else f"Historical path {idx + 1}",
                showlegend=idx == 0,
            ))
    if isinstance(future_candles, pd.DataFrame) and not future_candles.empty:
        tf = _column(future_candles, ("time", "datetime", "timestamp"))
        of = _column(future_candles, ("open",))
        hf = _column(future_candles, ("high",))
        lf = _column(future_candles, ("low",))
        cf = _column(future_candles, ("close",))
        if all((tf, of, hf, lf, cf)):
            fig.add_trace(go.Candlestick(
                x=_plot_clock(future_candles[tf]),
                open=pd.to_numeric(future_candles[of], errors="coerce"),
                high=pd.to_numeric(future_candles[hf], errors="coerce"),
                low=pd.to_numeric(future_candles[lf], errors="coerce"),
                close=pd.to_numeric(future_candles[cf], errors="coerce"),
                increasing_line_color="#4ea3ff", decreasing_line_color="#4ea3ff", name="Blue future candles",
            ))
    current_price = float(actual["close"].iloc[-1])
    # One explicitly labelled historical similar-day scenario, derived only from
    # the already-published ranked outcomes. It is supporting evidence, not probability.
    similar = _mapping(canonical.get("similar_day_intelligence"))
    top_matches = similar.get("top_five") if isinstance(similar.get("top_five"), list) else []
    if top_matches:
        best = _mapping(top_matches[0])
        points = []
        anchor_time = pd.Timestamp(actual["time"].iloc[-1])
        for hour in (1, 3, 6):
            pips = _finite(best.get(f"H+{hour} Pips"))
            if pips is not None:
                points.append((anchor_time + pd.Timedelta(hours=hour), current_price + pips * 0.0001))
        if points:
            fig.add_trace(go.Scatter(x=_plot_clock([item[0] for item in points]), y=[item[1] for item in points], mode="lines+markers", line={"width": 2, "dash": "dash"}, name="Historical similar-day scenario"))
    fig.add_hline(y=current_price, line_width=1, line_dash="dash", annotation_text="Current price")
    horizon, selected_forecast = _selected_forecast(canonical)
    if not main_view.empty:
        for hour in (1, 2, 3, 6):
            if len(main_view) >= hour:
                row = main_view.iloc[min(hour - 1, len(main_view) - 1)]
                fig.add_trace(go.Scatter(
                    x=_plot_clock([row["time"]]), y=[row["main"]], mode="markers+text",
                    text=[f"H+{hour}"], textposition="top center",
                    marker={"size": 8}, name=f"H+{hour} marker", showlegend=False,
                ))
    for key, label, dash in (("selected_tp", "Selected TP", "dash"), ("selected_sl", "Selected SL", "dot")):
        level = _finite(selected_forecast.get(key), _finite(canonical.get(key)))
        if level is not None:
            fig.add_hline(y=level, line_width=1, line_dash=dash, annotation_text=label)
    trust = _mapping(canonical.get("trust_validation"))
    mfe_pips = _finite(trust.get("expected_mfe_pips"))
    mae_pips = _finite(trust.get("expected_mae_pips"))
    direction = str(_mapping(canonical.get("final_decision")).get("directional_market_view") or canonical.get("full_metric_direction") or "WAIT").upper()
    pip_size = 0.0001
    if direction in {"BUY", "SELL"}:
        sign = 1.0 if direction == "BUY" else -1.0
        if mfe_pips is not None:
            fig.add_hline(y=current_price + sign * mfe_pips * pip_size, line_width=1, line_dash="dot", annotation_text="Expected MFE")
        if mae_pips is not None:
            fig.add_hline(y=current_price - sign * mae_pips * pip_size, line_width=1, line_dash="dot", annotation_text="Expected MAE")

    fig.update_layout(
        height=500 if phone else 610,
        margin={"l": 8, "r": 8, "t": 30, "b": 8},
        xaxis_rangeslider_visible=False,
        legend={"orientation": "h", "y": 1.02, "x": 0},
        hovermode="x unified",
        uirevision=str(canonical.get("run_id", "powerbi-cache")),
        xaxis={"hoverformat": "%Y-%m-%d %H:%M", "tickformat": "%H:%M\n%b %d"},
    )
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "responsive": True, "scrollZoom": False})

    if st.toggle("Show cached prediction-vs-actual history", value=False, key="powerbi_cached_backtest_toggle_20260619"):
        stats = st.columns(4)
        stats[0].metric("Tested Forecasts", str(bt_summary.get("tested_candles", len(bt_history) if isinstance(bt_history, pd.DataFrame) else 0)))
        stats[1].metric("Causal Actionable Accuracy", f"{bt_summary.get('causal_actionable_direction_accuracy_pct', bt_summary.get('direction_accuracy_pct', '-'))}%")
        stats[2].metric("Actionable Coverage", f"{bt_summary.get('actionable_coverage_pct', '-')}%")
        stats[3].metric("Average Close Error", f"{bt_summary.get('avg_abs_close_error_pct', '-')}%")
        legacy = bt_summary.get("legacy_direction_accuracy_pct")
        if legacy not in (None, ""):
            st.caption(f"Legacy candle-body direction accuracy retained for audit: {legacy}%. New accuracy uses forecast-origin direction and selective WAIT filtering.")
        if isinstance(bt_history, pd.DataFrame) and not bt_history.empty:
            st.dataframe(bt_history.head(240), use_container_width=True, hide_index=True, height=360)

    if st.toggle("Prepare cached Power BI exports", value=False, key="powerbi_cached_exports_toggle_20260619"):
        if not main_view.empty:
            st.download_button(
                "Export Calibrated Projection CSV",
                data=main_view.to_csv(index=False).encode("utf-8"),
                file_name="eurusd_h1_powerbi_calibrated_projection.csv",
                mime="text/csv",
                key="powerbi_cached_main_export_20260619",
                use_container_width=True,
            )
        if isinstance(bt_history, pd.DataFrame) and not bt_history.empty:
            st.download_button(
                "Export Prediction vs Actual CSV",
                data=bt_history.to_csv(index=False).encode("utf-8"),
                file_name="eurusd_h1_powerbi_prediction_vs_actual.csv",
                mime="text/csv",
                key="powerbi_cached_bt_export_20260619",
                use_container_width=True,
            )


def render_cached_powerbi_projection(*, state: MutableMapping[str, Any] | None = None) -> None:
    """Render the completed Power BI cache immediately, with no second calculation."""
    state = state if state is not None else st.session_state
    bundle = _mapping(state.get("powerbi_calibrated_bundle_20260617"))
    market_raw = _first_dataframe(state, (
        "dv_pp_df", "canonical_completed_ohlc_df_20260617", "calculation_staging_ohlc_df_20260617",
        "lunch_5layer_powerbi_df", "last_df",
    ))
    market = _market_view(market_raw)
    future_candles = _first_dataframe(state, ("dv_pp_predicted_calibrated_20260617", "dv_pp_predicted"))
    projection_history = _first_dataframe(state, ("dv_pp_projection_history",))
    bt_history = _first_dataframe(state, ("dv_pp_bt_hist", "prediction_vs_actual_history_df", "prediction_history_df"))
    bt_summary = _mapping(state.get("dv_pp_bt_summary"))
    canonical = _canonical_identity(state)

    st.markdown("#### Power BI Price Prediction Projection")
    st.caption(
        "Cached completed generation only. Chart controls rerun this display fragment and never rebuild the trading system. "
        "All chart hours use the same source candle clock as the Lunch history tables."
    )
    if not bundle.get("ok"):
        st.error("Power BI projection could not be published for this calculation.")
        messages = _powerbi_error_context(state, bundle)
        st.markdown("##### Power BI error details")
        if messages:
            for message in messages:
                st.code(message)
        else:
            st.code("No calibrated Power BI bundle was stored. Check Settings → Errors / Fix Fast.")
        return

    bundle, future_candles, alignment_notes = _aligned_powerbi_inputs(market, bundle, future_candles)
    main = bundle.get("main") if isinstance(bundle.get("main"), pd.DataFrame) else pd.DataFrame()
    summary = _mapping(bundle.get("summary"))
    valid, issues = _validation(market, main, future_candles, summary, canonical)
    if not valid:
        st.error("Power BI projection integrity validation failed. The chart is not silently replaced with stale data.")
        st.markdown("##### Projection integrity details")
        for issue in issues:
            st.code(issue)
        return
    if alignment_notes:
        st.info("Power BI display synchronized to current completed H1 candle: " + " ".join(alignment_notes))

    alpha, delta = _regime_alpha_delta(state, canonical)
    last_main = None
    if not main.empty:
        main_col = _column(main, ("main path", "main_path"))
        if main_col:
            values = pd.to_numeric(main[main_col], errors="coerce").dropna()
            last_main = float(values.iloc[-1]) if not values.empty else None
    horizon, selected_forecast = _selected_forecast(canonical)
    final = _mapping(canonical.get("final_decision"))
    direction = str(final.get("directional_market_view") or canonical.get("full_metric_direction") or "WAIT").upper()
    above = _finite(selected_forecast.get("buy_probability_calibrated"))
    below = _finite(selected_forecast.get("sell_probability_calibrated"))
    research = _mapping(canonical.get("research_risk_stack"))
    research_summary = _mapping(research.get("current_summary"))
    tp_touch = _finite(selected_forecast.get("tp_touch_probability"), _finite(final.get("tp_first_probability"), _finite(research_summary.get("tp_first_probability"))))
    sl_touch = _finite(selected_forecast.get("sl_touch_probability"), _finite(final.get("sl_first_probability"), _finite(research_summary.get("sl_first_probability"))))
    metrics = st.columns(4)
    confidence = _finite(final.get("calibrated_confidence"), _finite(summary.get("reliability_pct"), 0.0)) or 0.0
    if confidence <= 1.0:
        confidence *= 100.0
    metrics[0].metric("Calibrated path confidence", f"{confidence:.1f}%")
    metrics[1].metric("Probability above current", f"{above * 100:.1f}%" if above is not None else "—")
    metrics[2].metric("Probability below current", f"{below * 100:.1f}%" if below is not None else "—")
    metrics[3].metric(f"H+{horizon} predicted price", f"{last_main:.5f}" if last_main is not None else "-")
    metrics2 = st.columns(4)
    metrics2[0].metric("TP-touch probability", f"{tp_touch * 100:.1f}%" if tp_touch is not None else "developing")
    metrics2[1].metric("SL-touch probability", f"{sl_touch * 100:.1f}%" if sl_touch is not None else "developing")
    metrics2[2].metric("Band Coverage", f"{float(summary.get('estimated_band_coverage_pct', 0) or 0):.1f}%")
    metrics2[3].metric("Regime", str(summary.get("current_regime", _mapping(canonical.get("regime")).get("major_regime", "-"))))
    robust = _mapping(research.get("robust_expectancy"))
    evt = _mapping(research.get("evt_tail"))
    proper = _mapping(research.get("proper_scoring"))
    intensity = _mapping(research.get("event_intensity"))
    weights = _mapping(bundle.get("research_bounded_weights"))
    risk_metrics = st.columns(4)
    risk_metrics[0].metric("Robust EV", f"{float(robust.get('robust_expected_value') or 0):+.2f} pips")
    risk_metrics[1].metric("Extreme risk", "BLOCK" if evt.get("extreme_risk_block") else "CLEAR", f"tail n={evt.get('evt_exceedance_count', 0)}")
    risk_metrics[2].metric("CRPS skill", f"{float(proper.get('skill_vs_naive') or 0):+.1%}", f"Energy {proper.get('joint_energy_score', '—')}")
    risk_metrics[3].metric("Event cluster", str(intensity.get("event_cluster_level") or "LOW"), "Bands widen only when risk rises")
    if weights:
        st.caption("Research-bounded model weights: " + " · ".join(f"{name} {float(value)*100:.1f}%" for name, value in list(weights.items())[:6]))
    st.caption(f"Forecast created {canonical.get('created_at', '—')} · expires {final.get('decision_expiry_time', canonical.get('expires_at', '—'))} · direction authority {direction} · Alpha {alpha} · Delta {delta}")
    st.caption(
        f"Run {str(canonical.get('run_id', '-'))[:18]} • Generation {canonical.get('calculation_generation', '-')} • "
        f"Latest completed H1 {str(canonical.get('latest_completed_candle_time', summary.get('anchor_time', '-')))[:25]}"
    )
    st.caption("Scenario labels are not probabilities. The central path, summary cards, intervals and future candles all come from the same published forecast generation.")
    _render_validation_panel(bt_history, bt_summary, summary, canonical)
    _render_cached_chart(market, bundle, future_candles, projection_history, bt_history, bt_summary, canonical)


__all__ = ["render_cached_powerbi_projection"]
