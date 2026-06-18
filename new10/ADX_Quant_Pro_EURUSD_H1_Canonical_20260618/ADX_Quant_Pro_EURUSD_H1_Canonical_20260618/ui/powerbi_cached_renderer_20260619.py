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


def _first_dataframe(state: Mapping[str, Any], keys: Iterable[str]) -> pd.DataFrame:
    for key in keys:
        value = state.get(key)
        if isinstance(value, pd.DataFrame) and not value.empty:
            return value
    return pd.DataFrame()


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
    if group is None:
        return [work[["__time", "__path"]].rename(columns={"__time": "time", "__path": "path"}).sort_values("time").tail(80)]
    grouped: list[pd.DataFrame] = []
    for _, item in list(work.groupby(group, sort=False))[-max_paths:]:
        path = item[["__time", "__path"]].rename(columns={"__time": "time", "__path": "path"}).sort_values("time")
        if not path.empty:
            grouped.append(path.tail(48))
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
        upper_col = _column(main, ("upper band", "upper_band"))
        lower_col = _column(main, ("lower band", "lower_band"))
        if time_col and main_col:
            main_view = pd.DataFrame({
                "time": pd.to_datetime(main[time_col], errors="coerce", utc=True),
                "main": pd.to_numeric(main[main_col], errors="coerce"),
                "upper": pd.to_numeric(main[upper_col], errors="coerce") if upper_col else pd.NA,
                "lower": pd.to_numeric(main[lower_col], errors="coerce") if lower_col else pd.NA,
            }).dropna(subset=["time", "main"])

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=actual["time"], open=actual["open"], high=actual["high"], low=actual["low"], close=actual["close"],
        name="Completed H1 candles",
    ))
    if not main_view.empty:
        if main_view["upper"].notna().any() and main_view["lower"].notna().any():
            fig.add_trace(go.Scatter(x=main_view["time"], y=main_view["upper"], mode="lines", line={"width": 1, "color": "rgba(90,140,255,0.55)"}, name="Upper band"))
            fig.add_trace(go.Scatter(x=main_view["time"], y=main_view["lower"], mode="lines", line={"width": 1, "color": "rgba(90,140,255,0.55)"}, fill="tonexty", fillcolor="rgba(90,140,255,0.12)", name="Lower band"))
        fig.add_trace(go.Scatter(x=main_view["time"], y=main_view["main"], mode="lines+markers", line={"width": 3, "color": "#f4f7ff"}, marker={"size": 5}, name="Calibrated main path"))
    if show_paths:
        for path, name, color, dash in (
            (red, "Red path", "#ff4b4b", "solid"),
            (yellow, "Yellow latest path", "#f4d03f", "solid"),
            (blue, "Blue previous/future path", "#4ea3ff", "dot"),
        ):
            if not path.empty:
                fig.add_trace(go.Scatter(x=path["time"], y=path["path"], mode="lines+markers", line={"width": 2, "color": color, "dash": dash}, marker={"size": 4}, name=name))
    if show_history:
        for idx, path in enumerate(_historical_paths(projection_history, pd.Timestamp(actual["time"].iloc[-1]))):
            fig.add_trace(go.Scatter(
                x=path["time"], y=path["path"], mode="lines",
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
                x=pd.to_datetime(future_candles[tf], errors="coerce", utc=True),
                open=pd.to_numeric(future_candles[of], errors="coerce"),
                high=pd.to_numeric(future_candles[hf], errors="coerce"),
                low=pd.to_numeric(future_candles[lf], errors="coerce"),
                close=pd.to_numeric(future_candles[cf], errors="coerce"),
                increasing_line_color="#4ea3ff", decreasing_line_color="#4ea3ff", name="Blue future candles",
            ))
    fig.update_layout(
        height=500 if phone else 610,
        margin={"l": 8, "r": 8, "t": 30, "b": 8},
        xaxis_rangeslider_visible=False,
        legend={"orientation": "h", "y": 1.02, "x": 0},
        hovermode="x unified",
        uirevision=str(canonical.get("run_id", "powerbi-cache")),
    )
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "responsive": True, "scrollZoom": False})

    if st.toggle("Show cached prediction-vs-actual history", value=False, key="powerbi_cached_backtest_toggle_20260619"):
        stats = st.columns(3)
        stats[0].metric("Tested Forecasts", str(bt_summary.get("tested_candles", len(bt_history) if isinstance(bt_history, pd.DataFrame) else 0)))
        stats[1].metric("Direction Accuracy", f"{bt_summary.get('direction_accuracy_pct', '-')}%")
        stats[2].metric("Average Close Error", f"{bt_summary.get('avg_abs_close_error_pct', '-')}%")
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
        "Cached completed generation only. Chart controls rerun this display fragment and never rebuild the trading system."
    )
    if not bundle.get("ok"):
        st.error("Power BI projection could not be published for this calculation.")
        messages = _powerbi_error_context(state, bundle)
        with st.expander("Open / Close — Power BI error details", expanded=True):
            if messages:
                for message in messages:
                    st.code(message)
            else:
                st.code("No calibrated Power BI bundle was stored. Check Settings → Errors / Fix Fast.")
        return

    main = bundle.get("main") if isinstance(bundle.get("main"), pd.DataFrame) else pd.DataFrame()
    summary = _mapping(bundle.get("summary"))
    valid, issues = _validation(market, main, future_candles, summary, canonical)
    if not valid:
        st.error("Power BI projection integrity validation failed. The chart is not silently replaced with stale data.")
        with st.expander("Open / Close — Projection integrity details", expanded=True):
            for issue in issues:
                st.code(issue)
        return

    alpha, delta = _regime_alpha_delta(state, canonical)
    last_main = None
    if not main.empty:
        main_col = _column(main, ("main path", "main_path"))
        if main_col:
            values = pd.to_numeric(main[main_col], errors="coerce").dropna()
            last_main = float(values.iloc[-1]) if not values.empty else None
    metrics = st.columns(4)
    metrics[0].metric("Prediction Confidence / Reliability", f"{float(summary.get('reliability_pct', 0) or 0):.1f}%")
    metrics[1].metric("Direction Accuracy", f"{summary.get('direction_accuracy_pct', bt_summary.get('direction_accuracy_pct', '-'))}%")
    metrics[2].metric("Prediction Error", f"{float(summary.get('median_abs_error_pct', bt_summary.get('avg_abs_close_error_pct', 0)) or 0):.5f}%")
    metrics[3].metric("6-Hour Predicted Price", f"{last_main:.5f}" if last_main is not None else "-")
    metrics2 = st.columns(4)
    metrics2[0].metric("Alpha", str(alpha))
    metrics2[1].metric("Delta", str(delta))
    metrics2[2].metric("Band Coverage", f"{float(summary.get('estimated_band_coverage_pct', 0) or 0):.1f}%")
    metrics2[3].metric("Regime", str(summary.get("current_regime", _mapping(canonical.get("regime")).get("major_regime", "-"))))
    st.caption(
        f"Run {str(canonical.get('run_id', '-'))[:18]} • Generation {canonical.get('calculation_generation', '-')} • "
        f"Latest completed H1 {str(canonical.get('latest_completed_candle_time', summary.get('anchor_time', '-')))[:25]}"
    )
    _render_cached_chart(market, bundle, future_candles, projection_history, bt_history, bt_summary, canonical)


__all__ = ["render_cached_powerbi_projection"]
