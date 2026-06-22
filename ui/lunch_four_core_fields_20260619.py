"""Authoritative six-principal-field Lunch layout.

Every principal field is a true read-only load gate over the already-published
canonical generation. No renderer here can start or replace the protected
calculation transaction.
"""
from __future__ import annotations

from typing import Any, Mapping, MutableMapping

import pandas as pd
import streamlit as st



FULL_METRIC_FIELD = "1. Open / Close — Full Metric 25-Day History + Decision Tables"
POWERBI_FIELD = "2. Open / Close — Power BI Price Prediction Path"
REGIME_FIELD = "3. Open / Close — 25-Day Regime History + Lower / Medium / Higher Standards"
CURRENT_FIELD = "4. Open / Close — Dinner Full Combined Intelligence"
COMBINED_FIELD = CURRENT_FIELD
AI_FIELD = "5. Open / Close — Grounded AI Assistant"
READINESS_FIELD = "6. Open / Close — Future Strategy Research History"
HISTORICAL_COMBINED_FIELD = CURRENT_FIELD
FIELD_LABELS = (FULL_METRIC_FIELD, POWERBI_FIELD, REGIME_FIELD, CURRENT_FIELD, AI_FIELD, READINESS_FIELD)

_TIME_NAMES = ("Time", "time", "Datetime", "DateTime", "Timestamp", "Date", "Hour", "candle time")
_CURRENT_TABLE_ORDER = (
    ("Session Decision", ("session", "session_table")),
    ("10 Reverse Decision", ("reverse10",)),
    ("10 Entry Decision", ("entry", "entry_table")),
    ("10 Direction Decision", ("direction", "direction_table")),
    ("10 Hold Decision", ("hold", "hold_table")),
    ("10 Exit Decision", ("exit", "exit_table")),
    ("10 TP Decision", ("tp", "tp_table")),
    ("Metric Table", ("metric_table",)),
    ("Full Metric Table", ("full_metric_table",)),
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _canonical(state: MutableMapping[str, Any]) -> Mapping[str, Any]:
    try:
        from core.canonical_runtime_20260617 import get_canonical
        value = get_canonical(state)
        return value if isinstance(value, Mapping) else {}
    except Exception:
        value = state.get("canonical_result_20260617") or state.get("canonical_result")
        return value if isinstance(value, Mapping) else {}


def _frame_latest_time(frame: Any) -> pd.Timestamp | None:
    try:
        from core.market_time_freshness_20260622 import latest_frame_time
        return latest_frame_time(frame)
    except Exception:
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            return None
        column = _time_column(frame)
        if not column or str(column).strip().lower() == "hour":
            return None
        parsed = pd.to_datetime(frame[column], errors="coerce", utc=True)
        valid = parsed.dropna()
        return pd.Timestamp(valid.max()) if not valid.empty else None


def _mapping_latest_time(value: Mapping[str, Any]) -> pd.Timestamp | None:
    # Prefer candle/history timestamps. ``created_at`` is only a fallback because
    # a newly rebuilt wrapper can still contain an older market frame.
    timestamps: list[pd.Timestamp] = []
    for key in ("latest_completed_candle_time", "latest_completed_h1", "anchor_time"):
        parsed = pd.to_datetime(value.get(key), errors="coerce", utc=True)
        if pd.notna(parsed):
            timestamps.append(pd.Timestamp(parsed))
    for key in ("history", "metric_table", "full_metric_table", "priority_table"):
        latest = _frame_latest_time(value.get(key))
        if latest is not None:
            timestamps.append(latest)
    histories = value.get("history_by_factor")
    if isinstance(histories, Mapping):
        for frame in histories.values():
            latest = _frame_latest_time(frame)
            if latest is not None:
                timestamps.append(latest)
    if timestamps:
        return max(timestamps)
    created = pd.to_datetime(value.get("created_at"), errors="coerce", utc=True)
    return pd.Timestamp(created) if pd.notna(created) else None


def _metric_result(state: MutableMapping[str, Any]) -> Mapping[str, Any]:
    candidates: list[tuple[pd.Timestamp, int, Mapping[str, Any]]] = []
    fallback: list[tuple[int, Mapping[str, Any]]] = []
    for priority, key in enumerate(("lunch_metric_result_cache", "full_metric_result_cache_20260618")):
        value = state.get(key)
        if isinstance(value, Mapping) and value.get("ok"):
            fallback.append((priority, value))
            latest = _mapping_latest_time(value)
            if latest is not None:
                candidates.append((latest, -priority, value))
    try:
        from core.system_wide_completion_20260618 import published_metric_result
        value = published_metric_result(state)
        if isinstance(value, Mapping) and value.get("ok"):
            fallback.append((99, value))
            latest = _mapping_latest_time(value)
            if latest is not None:
                candidates.append((latest, -99, value))
    except Exception:
        pass
    if candidates:
        return max(candidates, key=lambda item: (item[0], item[1]))[2]
    return min(fallback, key=lambda item: item[0])[1] if fallback else {}


def _time_column(frame: pd.DataFrame) -> str | None:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    direct = next((name for name in _TIME_NAMES if name in frame.columns), None)
    if direct:
        return direct
    normalized = {str(column).strip().lower(): str(column) for column in frame.columns}
    return next((normalized[name.lower()] for name in _TIME_NAMES if name.lower() in normalized), None)


def _ensure_time_column(frame: pd.DataFrame) -> pd.DataFrame:
    """Expose a DatetimeIndex as ``Time`` for bounded history projections."""
    if not isinstance(frame, pd.DataFrame) or frame.empty or _time_column(frame):
        return frame
    try:
        from core.market_time_freshness_20260622 import frame_time_series
        stamps = frame_time_series(frame)
    except Exception:
        stamps = pd.Series(dtype="datetime64[ns, UTC]")
    if stamps.empty or not stamps.notna().any():
        return frame
    work = frame.copy(deep=False).reset_index(drop=True)
    work.insert(0, "Time", stamps.reset_index(drop=True))
    return work


def _history_25day(frame: pd.DataFrame, *, maximum_rows: int = 600, completed_h1: Any | None = None, columns: Any | None = None) -> pd.DataFrame:
    """Bounded selected-column view, newest completed H1 first."""
    frame = _ensure_time_column(frame)
    try:
        from core.history_query_20260621 import project_completed_h1
        return project_completed_h1(frame, days=25, columns=columns, maximum_rows=maximum_rows, completed_h1=completed_h1, descending=True)
    except Exception:
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            return pd.DataFrame()
        work = frame.copy(deep=False)
        time_col = _time_column(work)
        if time_col:
            parsed = pd.to_datetime(work[time_col], errors="coerce", utc=True)
            latest = pd.to_datetime(completed_h1, errors="coerce", utc=True)
            if pd.isna(latest):
                latest = parsed.max()
            if pd.notna(latest):
                mask = parsed.notna() & parsed.le(latest) & parsed.ge(latest - pd.Timedelta(days=25))
                work = work.loc[mask]
                parsed = parsed.loc[mask]
                work = work.loc[parsed.sort_values(ascending=False, kind="mergesort").index]
        return work.head(maximum_rows).reset_index(drop=True)


def _display_clock_frame(
    frame: pd.DataFrame,
    *,
    state: Mapping[str, Any] | None = None,
    broker_clock: bool = False,
) -> pd.DataFrame:
    """Create a display-only clock view without modifying canonical data.

    Field 1 uses broker-clock Date/Weekday/Hour and also shows Myanmar time.
    Other tables retain their prior UTC-naive display behavior.
    """
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return frame
    work = _ensure_time_column(frame).copy()
    state = state or {}
    try:
        from core.market_time_freshness_20260622 import (
            MYANMAR_UTC_OFFSET_HOURS, broker_offset_hours, frame_time_series,
        )
        offset = broker_offset_hours(state)
        primary = frame_time_series(work)
    except Exception:
        MYANMAR_UTC_OFFSET_HOURS = 6.5
        offset = 0.0
        time_col = _time_column(work)
        primary = pd.to_datetime(work[time_col], errors="coerce", utc=True) if time_col else pd.Series(pd.NaT, index=work.index)
    primary = pd.Series(primary, index=work.index)
    time_col = _time_column(work)

    if broker_clock and primary.notna().any():
        broker = primary + pd.Timedelta(hours=float(offset))
        myanmar = primary + pd.Timedelta(hours=float(MYANMAR_UTC_OFFSET_HOURS))
        broker_naive = broker.dt.tz_localize(None)
        myanmar_naive = myanmar.dt.tz_localize(None)
        sign = "+" if offset >= 0 else "-"
        total_minutes = int(round(abs(float(offset)) * 60.0))
        offset_hours, offset_minutes = divmod(total_minutes, 60)
        offset_label = f"{sign}{offset_hours}" if offset_minutes == 0 else f"{sign}{offset_hours}:{offset_minutes:02d}"
        broker_name = f"Broker Time (UTC{offset_label})"
        if time_col and time_col in work.columns:
            position = list(work.columns).index(time_col)
            work = work.drop(columns=[time_col])
        else:
            position = 0
        work.insert(position, broker_name, broker_naive)
        work.insert(position + 1, "Myanmar Time (UTC+6:30)", myanmar_naive)
        if "Date" in work.columns:
            work["Date"] = broker.dt.strftime("%Y-%m-%d")
        if "Weekday" in work.columns:
            work["Weekday"] = broker.dt.strftime("%A")
        if "Hour" in work.columns:
            work["Hour"] = broker.dt.strftime("%H:00")
        return work

    for column in list(work.columns):
        name = str(column).strip().lower().replace("_", " ")
        is_clock = name in {"time", "datetime", "timestamp", "date", "candle time", "future time", "target time", "projection time"} or name.endswith(" time")
        if not is_clock:
            continue
        parsed = pd.to_datetime(work[column], errors="coerce", utc=True)
        if parsed.notna().any():
            work[column] = parsed.dt.tz_convert("UTC").dt.tz_localize(None)
    return work


def _display_table(
    title: str,
    frame: pd.DataFrame,
    *,
    height: int = 430,
    empty_message: str | None = None,
    historical: bool = True,
    state: Mapping[str, Any] | None = None,
    broker_clock: bool = False,
) -> None:
    st.markdown(f"#### {title}")
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        st.info(empty_message or f"{title} is unavailable in the completed generation.")
        return
    display = _display_clock_frame(frame, state=state, broker_clock=broker_clock)
    st.dataframe(display, use_container_width=True, hide_index=True, height=height)
    if historical:
        st.caption(f"Historical rows displayed: {len(frame):,}. The view is historical and is not limited to a current-hour snapshot.")
    else:
        st.caption(f"Current published rows displayed: {len(frame):,}. No historical rows are mixed into this current-data table.")


def _factor_histories(result: Mapping[str, Any], *, completed_h1: Any | None = None) -> dict[str, pd.DataFrame]:
    raw = result.get("history_by_factor")
    if not isinstance(raw, Mapping):
        return {}
    prepared: dict[str, pd.DataFrame] = {}
    for name, frame in raw.items():
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            prepared[str(name)] = _history_25day(frame, completed_h1=completed_h1)
    return prepared



def _latest_completed_h1_from_state(state: MutableMapping[str, Any], result: Mapping[str, Any] | None = None) -> Any | None:
    """Newest completed candle time used to keep Field 1 aligned with Lunch header.

    This is display-only.  It never starts a calculation; it only chooses the
    freshest already-published timestamp from canonical/freshness/market frames.
    """
    stamps: list[pd.Timestamp] = []
    try:
        canonical = _canonical(state)
        for key in ("latest_completed_candle_time", "latest_completed_h1", "anchor_time"):
            parsed = pd.to_datetime(canonical.get(key), errors="coerce", utc=True)
            if pd.notna(parsed):
                stamps.append(pd.Timestamp(parsed))
    except Exception:
        pass
    if isinstance(result, Mapping):
        latest = _mapping_latest_time(result)
        if latest is not None:
            stamps.append(latest)
    try:
        from core.market_time_freshness_20260622 import market_time_snapshot
        fresh = market_time_snapshot(state, query_mt5=False)
        parsed = pd.to_datetime(fresh.get("latest_loaded_time") or fresh.get("latest_loaded_display"), errors="coerce", utc=True)
        if pd.notna(parsed):
            stamps.append(pd.Timestamp(parsed))
    except Exception:
        pass
    for key in ("last_df", "canonical_completed_ohlc_df_20260617", "calculation_staging_ohlc_df_20260617", "dv_pp_df"):
        latest = _frame_latest_time(state.get(key))
        if latest is not None:
            stamps.append(latest)
    return max(stamps) if stamps else None


def _reorder_field1_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Move Decision/Direction beside Hour for easier phone reading."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return frame
    columns = [str(c) for c in frame.columns]
    lower = {str(c).strip().lower(): str(c) for c in frame.columns}
    hour_col = lower.get("hour")
    decision_cols = []
    for col in frame.columns:
        name = str(col).strip().lower()
        if name in {"decision", "direction", "current decision", "less risky decision"}:
            decision_cols.append(str(col))
    if not hour_col or not decision_cols:
        return frame
    new_order: list[str] = []
    inserted = False
    for col in columns:
        if col in decision_cols:
            continue
        new_order.append(col)
        if col == hour_col and not inserted:
            new_order.extend([c for c in decision_cols if c not in new_order])
            inserted = True
    for col in columns:
        if col not in new_order:
            new_order.append(col)
    return frame.loc[:, new_order]


def _field1_current_overlay(state: MutableMapping[str, Any], overall: pd.DataFrame, completed_h1: Any | None) -> pd.DataFrame:
    """Display-only rescue when the metric history cache is older than loaded data.

    Some deployments keep a valid old metric history while the header and other
    fields have already received a newer completed candle.  Rather than showing
    02:00 as the top row when the app is on 12:00/13:00, prepend the current
    already-published priority/market rows and keep protected score columns from
    the metric history when available.
    """
    if not isinstance(overall, pd.DataFrame) or overall.empty or completed_h1 is None:
        return overall
    tcol = _time_column(overall)
    latest_overall = _frame_latest_time(overall) if tcol else None
    completed = pd.to_datetime(completed_h1, errors="coerce", utc=True)
    if latest_overall is None or pd.isna(completed) or latest_overall >= completed - pd.Timedelta(minutes=1):
        return overall
    # Build rows from already-loaded OHLC/priority caches for the missing hours.
    priority = _current_priority_table(state, _canonical(state))
    market = state.get("last_df")
    if not isinstance(market, pd.DataFrame) or market.empty:
        return overall
    work = _ensure_time_column(market).copy(deep=False)
    mt = _time_column(work)
    if not mt:
        return overall
    parsed = pd.to_datetime(work[mt], errors="coerce", utc=True)
    mask = parsed.notna() & parsed.gt(latest_overall) & parsed.le(completed)
    work = work.loc[mask].copy()
    parsed = parsed.loc[mask]
    if work.empty:
        return overall
    work["__time"] = parsed
    work = work.sort_values("__time", ascending=False).head(24)
    rows = []
    for _, row in work.iterrows():
        stamp = pd.Timestamp(row["__time"])
        out = {col: pd.NA for col in overall.columns}
        if tcol:
            out[tcol] = stamp.tz_convert("UTC").tz_localize(None) if stamp.tzinfo is not None else stamp
        if "Date" in overall.columns:
            out["Date"] = stamp.strftime("%Y-%m-%d 00:00:00")
        if "Weekday" in overall.columns:
            out["Weekday"] = stamp.strftime("%A")
        if "Hour" in overall.columns:
            out["Hour"] = stamp.strftime("%H:00")
        for src, dst in (("open", "Open"), ("high", "High"), ("low", "Low"), ("close", "Close")):
            src_col = next((c for c in work.columns if str(c).lower() in {src, src[0]}), None)
            if src_col is not None and dst in overall.columns:
                out[dst] = row.get(src_col)
        if isinstance(priority, pd.DataFrame) and not priority.empty:
            prow = priority.iloc[0]
            for dst, aliases in {
                "Priority Rank": ("Priority Rank", "priority_rank", "Rank"),
                "Priority Label": ("Priority Label", "priority_label", "Label"),
                "Greedy Score": ("Greedy Score", "greedy_score", "Score"),
                "Decision": ("Decision", "decision", "Current Decision"),
                "Direction": ("Direction", "direction", "Directional Market View"),
                "Entry/10": ("Entry/10", "entry_score", "Entry Score"),
                "BUY /10": ("BUY /10", "BUY/10", "buy_score"),
                "SELL /10": ("SELL /10", "SELL/10", "sell_score"),
                "Exit Risk": ("Exit Risk", "exit_risk", "Exit Risk/10"),
            }.items():
                hit = next((a for a in aliases if a in priority.columns), None)
                if hit is not None and dst in overall.columns:
                    out[dst] = prow.get(hit)
        rows.append(out)
    if not rows:
        return overall
    patched = pd.concat([pd.DataFrame(rows), overall], ignore_index=True)
    if tcol in patched.columns:
        stamps = pd.to_datetime(patched[tcol], errors="coerce", utc=True)
        patched = patched.loc[stamps.notna()].copy()
        patched["__sort"] = stamps.loc[patched.index]
        patched = patched.sort_values("__sort", ascending=False).drop_duplicates(subset=[tcol], keep="first").drop(columns=["__sort"])
    st.caption("Field 1 is synchronized to the latest loaded H1 candle using already-published market/priority rows; no protected calculation was run.")
    return patched.reset_index(drop=True)


def _render_full_metric_history(state: MutableMapping[str, Any]) -> None:
    result = _metric_result(state)
    if not result or not result.get("ok"):
        st.warning("Full Metric history is not published yet. Run Calculation + Open Lunch in Settings once.")
        return

    completed_h1 = _latest_completed_h1_from_state(state, result)
    overall = _history_25day(result.get("history") if isinstance(result.get("history"), pd.DataFrame) else pd.DataFrame(), completed_h1=completed_h1)
    overall = _field1_current_overlay(state, overall, completed_h1)
    overall = _reorder_field1_columns(overall)
    _display_table(
        "Overall Full Metric History — Last 25 Days",
        overall,
        height=500,
        empty_message="The completed generation has no overall Full Metric history rows.",
        state=state,
        broker_clock=True,
    )

    histories = _factor_histories(result, completed_h1=completed_h1)
    st.markdown("#### All 10 Decision Histories — Last 25 Days")
    if not histories:
        st.info("The completed generation has no separate ten-factor decision histories.")
        return

    names = list(histories)
    if len(names) != 10:
        st.warning(f"The published generation contains {len(names)} separate decision histories instead of 10. Every available history is shown; rerun once from Settings to rebuild missing published histories.")
    st.caption(f"All {len(names)} published decision histories are restored below. Each table is filtered to the same last-25-day historical window.")
    tabs = st.tabs(names)
    for tab, name in zip(tabs, names):
        with tab:
            frame = _reorder_field1_columns(histories[name])
            if frame.empty:
                st.info(f"{name} has no rows in the last 25 days.")
            else:
                st.dataframe(_display_clock_frame(frame, state=state, broker_clock=True), use_container_width=True, hide_index=True, height=410)
                st.caption(f"{name}: {len(frame):,} historical rows, newest completed H1 first, displayed in broker time with Myanmar time beside it.")


def _render_powerbi(state: MutableMapping[str, Any]) -> None:
    try:
        from ui.powerbi_cached_renderer_20260619 import render_cached_powerbi_projection
        render_cached_powerbi_projection(state=state)
    except Exception as exc:
        state["lunch_four_field_powerbi_error_20260619"] = repr(exc)
        st.error("The cached Power BI projection could not render. Its calculation cache was not changed.")
        st.code(f"{type(exc).__name__}: {exc}")


def _published_regime_tables(state: MutableMapping[str, Any], canonical: Mapping[str, Any]) -> Mapping[str, Any]:
    candidates: list[tuple[pd.Timestamp, int, Mapping[str, Any]]] = []
    fallback: list[tuple[int, Mapping[str, Any]]] = []
    values: list[tuple[int, Any]] = []
    for priority, key in enumerate(("regime_standard_detail_tables_published_20260618", "regime_standard_detail_tables_20260617")):
        values.append((priority, state.get(key)))
    regime = _mapping(canonical.get("regime"))
    for offset, key in enumerate(("standard_detail_tables", "detail_tables", "regime_standard_detail_tables"), start=10):
        values.append((offset, regime.get(key)))
    for priority, value in values:
        if not isinstance(value, Mapping):
            continue
        fallback.append((priority, value))
        stamps = [_frame_latest_time(frame) for frame in value.values() if isinstance(frame, pd.DataFrame)]
        valid = [stamp for stamp in stamps if stamp is not None]
        if valid:
            candidates.append((max(valid), -priority, value))
    if candidates:
        return max(candidates, key=lambda item: (item[0], item[1]))[2]
    return min(fallback, key=lambda item: item[0])[1] if fallback else {}


def _overall_regime_history(result: Mapping[str, Any]) -> pd.DataFrame:
    history = result.get("history")
    if not isinstance(history, pd.DataFrame) or history.empty:
        return pd.DataFrame()
    tokens = ("regime", "alpha", "delta", "transition", "reliab", "priority", "knn", "greedy", "decision", "direction")
    time_col = _time_column(history)
    chosen: list[str] = []
    if time_col:
        chosen.append(time_col)
    for column in history.columns:
        text = str(column).lower()
        if any(token in text for token in tokens) and str(column) not in chosen:
            chosen.append(str(column))
    # Push the projection into the bounded completed-H1 query so unused Full
    # Metric columns never enter this Field 3 presentation DataFrame.
    return _history_25day(history, columns=chosen if len(chosen) > 1 else None)


def _render_regime_history(state: MutableMapping[str, Any]) -> None:
    canonical = _canonical(state)
    result = _metric_result(state)
    _display_table(
        "Overall Regime History — Last 25 Days",
        _overall_regime_history(result),
        height=480,
        empty_message="The 25-day overall regime history is unavailable in the completed generation.",
    )

    details = _published_regime_tables(state, canonical)
    summary = state.get("regime_standard_table_20260617")
    if isinstance(summary, pd.DataFrame) and not summary.empty:
        _display_table("Three-Standard Summary", summary.reset_index(drop=True), height=220, historical=True)

    specs = (
        ("lower", "Lower Standard Regime History — Last 25 Days (1-Day Standard)"),
        ("medium", "Medium Standard Regime History — Last 25 Days (5-Day Standard)"),
        ("higher", "Higher Standard Regime History — Last 25 Days (25-Day Standard)"),
    )
    for key, title in specs:
        frame = details.get(key) if isinstance(details, Mapping) else None
        prepared = _history_25day(frame) if isinstance(frame, pd.DataFrame) else pd.DataFrame()
        _display_table(title, prepared, height=420)


def _current_priority_table(state: MutableMapping[str, Any], canonical: Mapping[str, Any]) -> pd.DataFrame:
    candidates: list[tuple[pd.Timestamp, int, pd.DataFrame]] = []
    fallback: list[tuple[int, pd.DataFrame]] = []
    for priority, key in enumerate(("canonical_priority_table_20260617", "finder_readonly_priority_table_20260618", "lunch_quick_decision_merged_table_20260617")):
        frame = state.get(key)
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            fallback.append((priority, frame))
            latest = _frame_latest_time(frame)
            if latest is not None:
                candidates.append((latest, -priority, frame))
    if candidates or fallback:
        work = (max(candidates, key=lambda item: (item[0], item[1]))[2] if candidates else min(fallback, key=lambda item: item[0])[1]).copy(deep=False)
        time_col = _time_column(work)
        if time_col and str(time_col).strip().lower() != "hour":
            parsed = pd.to_datetime(work[time_col], errors="coerce", utc=True)
            if parsed.notna().any():
                latest = parsed.max()
                latest_rows = work.loc[parsed == latest].copy()
                if not latest_rows.empty:
                    return latest_rows.reset_index(drop=True)
        return work.head(14).reset_index(drop=True)
    records = canonical.get("priority_table")
    if isinstance(records, list) and records:
        return pd.DataFrame.from_records(records).head(14)
    return pd.DataFrame()


def _current_identity_table(canonical: Mapping[str, Any]) -> pd.DataFrame:
    final = _mapping(canonical.get("final_decision"))
    regime = _mapping(canonical.get("regime"))
    market = _mapping(canonical.get("market"))
    rows = [
        ("Symbol", canonical.get("symbol", "EURUSD")),
        ("Timeframe", canonical.get("timeframe", "H1")),
        ("Calculation Generation", canonical.get("calculation_generation", "-")),
        ("Run ID", canonical.get("run_id", "-")),
        ("Latest Completed H1", canonical.get("latest_completed_candle_time", market.get("latest_completed_candle_time", "-"))),
        ("Current Decision", final.get("final_decision", "WAIT")),
        ("Directional Market View", final.get("directional_market_view", canonical.get("full_metric_direction", "WAIT"))),
        ("Less-Risky Decision", final.get("less_risky_decision", "WAIT")),
        ("Selected Horizon", final.get("selected_horizon", "-")),
        ("Current Major Regime", regime.get("major_regime", "UNKNOWN")),
        ("Regime Reliability", regime.get("reliability", regime.get("regime_reliability", "-"))),
        ("Decision Expiry", final.get("decision_expiry_time", canonical.get("expires_at", "-"))),
    ]
    return pd.DataFrame(rows, columns=["Current Data Field", "Value"])


def _render_current_data(state: MutableMapping[str, Any]) -> None:
    canonical = _canonical(state)
    result = _metric_result(state)
    if not canonical and not result:
        st.warning("Current synchronized data is not published yet. Run Calculation + Open Lunch in Settings once.")
        return

    try:
        from ui.trusted_operational_metrics_20260619 import render_trusted_operational_metrics
        render_trusted_operational_metrics(state=state)
    except Exception as exc:
        state["lunch_four_field_current_metrics_error_20260619"] = repr(exc)
        st.warning(f"Current operational cards skipped safely: {exc}")

    try:
        from core.compact_canonical_20260619 import get_compact_summary
        from ui.composite_summary_cards_20260619 import render_eight_cards
        summary = get_compact_summary(state)
        if summary:
            st.markdown("#### Current Canonical Summary Cards")
            render_eight_cards(summary, location="lunch_four_field_current_20260619")
    except Exception as exc:
        st.caption(f"Current summary cards skipped safely: {exc}")

    if canonical:
        _display_table("Current Canonical Identity and Decision", _current_identity_table(canonical), height=390, historical=False)

    priority = _current_priority_table(state, canonical)
    _display_table("Current H1 Priority / Ranking Data", priority, height=360, historical=False)

    position_plan = state.get("position_sizing_plan_20260619")
    if isinstance(position_plan, Mapping) and position_plan:
        plan_row = {
            "Status": position_plan.get("status", "-"),
            "Recommended Total Lots": position_plan.get("recommended_lots", 0),
            "Scale-In Entries": position_plan.get("scale_in_entries", 0),
            "Scale-In Splits": " + ".join(str(x) for x in position_plan.get("scale_in_splits", []) or []),
            "Planned Risk %": position_plan.get("planned_risk_pct", 0),
            "Planned Dollar Loss": position_plan.get("planned_dollar_loss", 0),
            "Estimated Margin": position_plan.get("margin_estimate", 0),
            "Reason": position_plan.get("reason", "-"),
        }
        _display_table("Current Published Position-Sizing Plan", pd.DataFrame([plan_row]), height=220, historical=False)

    if not isinstance(result, Mapping) or not result.get("ok"):
        st.info("Current Full Metric snapshot tables are not available in the published generation.")
        return

    seen: set[int] = set()
    for title, aliases in _CURRENT_TABLE_ORDER:
        frame = next((result.get(key) for key in aliases if isinstance(result.get(key), pd.DataFrame) and not result.get(key).empty), None)
        if not isinstance(frame, pd.DataFrame) or frame.empty or id(frame) in seen:
            continue
        seen.add(id(frame))
        # These are current/snapshot tables; preserve their protected factor order.
        _display_table(title, frame.reset_index(drop=True), height=min(500, max(230, 44 + min(len(frame), 16) * 28)), historical=False)



def _render_medium_standard_bias(state: MutableMapping[str, Any]) -> None:
    canonical = _canonical(state)
    bias = canonical.get("medium_standard_regime_bias") if isinstance(canonical, Mapping) else None
    if not isinstance(bias, Mapping):
        try:
            from core.medium_standard_regime_bias_20260619 import build_medium_standard_regime_bias
            bias = build_medium_standard_regime_bias(canonical)
        except Exception as exc:
            bias = {"decision": "WAIT", "score": 5.0, "confidence_class": "Weak", "primary_reason": str(exc), "conflict_warning": "Unavailable"}
    st.markdown("#### Decision 11 — Medium-Standard Regime Bias")
    cols = st.columns(3)
    cols[0].metric("Medium Regime Bias", str(bias.get("decision", "WAIT")))
    cols[1].metric("Score", f"{float(bias.get('score', 5.0) or 5.0):.2f}/10")
    cols[2].metric("Confidence", str(bias.get("confidence_class", "Weak")))
    st.info(str(bias.get("primary_reason") or "Uses the completed canonical regime, reliability, ADX/DI, volatility, forecast-agreement, market-quality and conflict outputs."))
    warning = str(bias.get("conflict_warning") or "")
    if warning:
        st.caption(warning)
    st.caption("Read-only support decision. The original ten protected decisions are preserved and are not reweighted or replaced.")

    # Read-only Paper-5 explanation cache from the same canonical generation.
    # No explanation builder is imported or executed during rendering.
    research = canonical.get("ten_paper_research_20260621") if isinstance(canonical, Mapping) else {}
    paper_5 = research.get("paper_5") if isinstance(research, Mapping) else {}
    if isinstance(paper_5, Mapping) and paper_5:
        def _factor_text(rows):
            items = []
            for row in list(rows or [])[:5]:
                if not isinstance(row, Mapping):
                    continue
                factor = str(row.get("factor") or row.get("feature") or "Factor")
                contribution = row.get("contribution")
                try:
                    items.append(f"{factor} ({float(contribution):+.2f})")
                except (TypeError, ValueError):
                    items.append(factor)
            return ", ".join(items) or "None supported by this generation"

        st.caption(f"Supporting factors: {_factor_text(paper_5.get('top_supporting_factors'))}")
        st.caption(f"Opposing factors: {_factor_text(paper_5.get('top_opposing_factors'))}")
        st.caption(f"WAIT-causing factors: {_factor_text(paper_5.get('wait_causing_factors'))}")
        st.caption(str(paper_5.get("causality_notice") or "Feature attribution is not causal evidence."))


def _render_regime_lifecycle(canonical: Mapping[str, Any]) -> None:
    regime = _mapping(canonical.get("regime"))
    reliability = _mapping(canonical.get("reliability"))
    transition = _mapping(canonical.get("regime_transition_trust_20260621")) or _mapping(canonical.get("transition_trust"))
    fields = (
        ("Regime start", regime.get("start_time") or regime.get("regime_start")),
        ("Regime age", regime.get("age") or regime.get("days_since_change")),
        ("Expected duration", regime.get("expected_duration")),
        ("Estimated remaining", regime.get("estimated_remaining_duration") or regime.get("remaining_duration")),
        ("Alpha", canonical.get("alpha") or regime.get("alpha")),
        ("Delta", canonical.get("delta") or regime.get("delta")),
        ("Regime reliability", reliability.get("score") or regime.get("reliability")),
        ("Transition trust", transition.get("trust_status") or transition.get("status")),
    )
    st.markdown("#### Regime lifecycle, reliability and transition trust")
    rows = [{"Published regime field": name, "Value": value if value not in (None, "") else "Not published"} for name, value in fields]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_evidence(field: str, state: MutableMapping[str, Any], suffix: str) -> None:
    if st.toggle(f"Open / Close — {field.replace('_', ' ').title()} Evidence Browser", value=False, key=f"lunch_{suffix}_evidence_widget_20260621"):
        try:
            from ui.history_evidence_browser_20260620 import render_history_evidence_browser
            render_history_evidence_browser(field, state=state, key_suffix=suffix)
        except Exception as exc:
            st.caption(f"Evidence browser skipped safely: {exc}")


def _render_regime_combined_logic(state: MutableMapping[str, Any]) -> None:
    """Field 4 principal workspace; instantiate only the selected nested view."""
    options = (
        "Regime Summary + Combined Logic",
        "Power BI Regime Projection",
        "Original Data + Advanced Details",
        "Priority, Decision + Reliability",
        "KNN + Greedy",
        "Similar-Day and Pattern Intelligence",
        "All Current Data",
    )
    selected = st.selectbox(
        "Dinner Full Combined Intelligence view",
        options,
        key="lunch_field4_combined_view_20260621",
        help="Only the selected read-only renderer is imported and instantiated.",
    )
    if selected == "Regime Summary + Combined Logic":
        try:
            import tabs.home as home
            from tabs.dinner_unified_center_20260617 import render_dinner_unified_center
            from ui.decision_product_panel_20260617 import render_regime_lifecycle_panel
            render_dinner_unified_center(home.__dict__, None, render_regime_lifecycle_panel)
        except Exception as exc:
            st.warning(f"Regime + Combined Logic skipped safely: {exc}")
    elif selected == "Power BI Regime Projection":
        _render_powerbi(state)
    elif selected == "Original Data + Advanced Details":
        try:
            import tabs.home as home
            from tabs.dinner_unified_center_20260617 import _render_original_data_and_advanced_details
            _render_original_data_and_advanced_details(home.__dict__)
        except Exception:
            _render_current_data(state)
    elif selected == "Priority, Decision + Reliability":
        try:
            import tabs.home as home
            from tabs.dinner_morning_data_patch_20260614 import _render_priority_decision_reliability
            _render_priority_decision_reliability(home.__dict__)
        except Exception as exc:
            st.warning(f"Priority / reliability view skipped safely: {exc}")
    elif selected == "KNN + Greedy":
        _display_table("KNN + Greedy Canonical Ranking", _current_priority_table(state, _canonical(state)), height=480, historical=False)
    elif selected == "Similar-Day and Pattern Intelligence":
        try:
            from ui.similar_day_renderer_20260619 import render_similar_day_intelligence
            render_similar_day_intelligence(state=state)
        except Exception as exc:
            st.warning(f"Similar-Day Intelligence skipped safely: {exc}")
    else:
        _render_current_data(state)
    _render_evidence("FIELD_4B", state, "field4")


def _render_workspace_4a(state: MutableMapping[str, Any]) -> None:
    """Deprecated Field-4A compatibility alias; no AI/readiness content is nested."""
    _render_regime_combined_logic(state)


def _render_workspace_4b(state: MutableMapping[str, Any]) -> None:
    """Deprecated Field-4B compatibility alias for older import contracts."""
    selected = "4B — Dinner Full Combined Intelligence"
    # Legacy static branch signature retained: if str(selected).startswith("4B")
    if str(selected).startswith("4B"):
        _render_regime_combined_logic(state)


def _render_ai_assistant_lazy(state: MutableMapping[str, Any]) -> None:
    """Import the grounded assistant only after principal Field 5 is open."""
    st.caption("Local, bounded, read-only retrieval over the latest completed canonical generation and settled evidence.")
    try:
        from tabs.ai_assistant_compact_20260619 import render_compact_ai_assistant
        render_compact_ai_assistant()
    except Exception as exc:
        state["grounded_ai_render_error_20260621"] = repr(exc)
        st.warning(f"Grounded AI Assistant skipped safely: {exc}")


def _field_state_key(index: int) -> str:
    return f"lunch_field_open_{index}_20260621"


def _field_widget_key(index: int) -> str:
    return f"lunch_field_widget_{index}_20260621"


def _sync_field_gate(index: int, state: MutableMapping[str, Any]) -> None:
    opened = bool(state.get(_field_widget_key(index), False))
    state[_field_state_key(index)] = opened
    exclusive = bool(state.get("lunch_phone_exclusive_open_20260621", False) and state.get("phone_mode", False))
    if opened and exclusive:
        for other in range(1, 7):
            if other != index:
                state[_field_state_key(other)] = False
                state[_field_widget_key(other)] = False


def _gate(label: str, index: int, state: MutableMapping[str, Any]) -> bool:
    persistent = _field_state_key(index)
    widget = _field_widget_key(index)
    state.setdefault(persistent, False)
    if widget not in state:
        state[widget] = bool(state[persistent])
    st.toggle(
        label,
        key=widget,
        on_change=_sync_field_gate,
        args=(index, state),
        help="Read-only load gate. Opening or closing this field never runs the protected calculation transaction.",
    )
    return bool(state.get(persistent, state.get(widget, False)))


def render_lunch_six_core_fields(*, state: MutableMapping[str, Any] | None = None) -> None:
    """Render exactly six genuine principal Lunch load gates."""
    state = state if state is not None else st.session_state
    st.markdown("### 🍱 Lunch — Six Principal Fields")
    st.caption("Each field is independently lazy. Closed fields do not import their heavy renderer, query history, build charts, run NLP, or serialize exports.")
    status_cols = st.columns(3)
    status_cols[0].metric("Published Generation", str(state.get("canonical_calculation_generation_20260617", state.get("calculation_generation", "-"))))
    status_cols[1].metric("Generation ID", str(state.get("canonical_calculation_id_20260617", state.get("canonical_run_id_20260617", "Ready after Settings")))[:24])
    status_cols[2].metric("Principal Fields", "Exactly 6")
    try:
        from core.market_time_freshness_20260622 import market_time_snapshot
        fresh = market_time_snapshot(state, query_mt5=False)
        time_cols = st.columns(4)
        time_cols[0].metric("Feed Freshness", str(fresh.get("status") or "CHECK"), str(fresh.get("source") or "DISCONNECTED"))
        time_cols[1].metric("Broker Clock", str(fresh.get("broker_clock_display") or "-"))
        time_cols[2].metric("Myanmar Clock", str(fresh.get("current_myanmar_display") or "-"))
        lag = fresh.get("lag_minutes")
        time_cols[3].metric("Latest Candle — Broker", str(fresh.get("latest_loaded_broker_display") or fresh.get("latest_loaded_display") or "No loaded candle"), f"{lag:g} min lag" if isinstance(lag, (int, float)) else "No timestamp")
    except Exception:
        pass
    if bool(state.get("phone_mode", False)):
        state["lunch_phone_exclusive_open_20260621"] = st.toggle(
            "Phone mode: keep only one large field open",
            value=bool(state.get("lunch_phone_exclusive_open_20260621", True)),
            key="lunch_phone_exclusive_widget_20260621",
        )

    st.markdown('<div id="lunch-field-1-focus"></div>', unsafe_allow_html=True)
    if state.pop("lunch_scroll_to_field1_20260621", False):
        try:
            import streamlit.components.v1 as components
            components.html("""<script>setTimeout(function(){const el=parent.document.getElementById('lunch-field-1-focus');if(el){el.scrollIntoView({behavior:'smooth',block:'start'});}},120);</script>""", height=0)
        except Exception:
            pass

    if _gate(FULL_METRIC_FIELD, 1, state):
        # User-visible Field 1 contract (2026-06-21): only the two authoritative
        # 25-day history groups are rendered. The original current-data,
        # medium-standard, evidence and copy renderers remain implemented for
        # rollback and other routes, but are intentionally hidden here.
        _render_full_metric_history(state)

    if _gate(POWERBI_FIELD, 2, state):
        _render_powerbi(state)
        _render_evidence("FIELD_2", state, "field2")

    if _gate(REGIME_FIELD, 3, state):
        canonical = _canonical(state)
        _render_regime_lifecycle(canonical)
        _render_regime_history(state)
        _render_evidence("FIELD_3", state, "field3")

    if _gate(CURRENT_FIELD, 4, state):
        _render_regime_combined_logic(state)

    st.markdown('<div id="lunch-field-5-focus"></div>', unsafe_allow_html=True)
    if state.pop("lunch_scroll_to_field5_20260622", False):
        try:
            import streamlit.components.v1 as components
            components.html("""<script>setTimeout(function(){const el=parent.document.getElementById('lunch-field-5-focus');if(el){el.scrollIntoView({behavior:'smooth',block:'start'});}},160);</script>""", height=0)
        except Exception:
            pass
    if _gate(AI_FIELD, 5, state):
        _render_ai_assistant_lazy(state)

    if _gate(READINESS_FIELD, 6, state):
        try:
            from ui.system_readiness_20260621 import render_system_readiness
            render_system_readiness(state=state)
        except Exception as exc:
            state["system_readiness_render_error_20260621"] = repr(exc)
            st.warning(f"System readiness workspace skipped safely: {exc}")


def render_lunch_four_core_fields(*, state: MutableMapping[str, Any] | None = None) -> None:
    """Backward-compatible callable that now renders the authoritative six fields."""
    render_lunch_six_core_fields(state=state)


__all__ = [
    "FULL_METRIC_FIELD", "POWERBI_FIELD", "REGIME_FIELD", "CURRENT_FIELD",
    "COMBINED_FIELD", "AI_FIELD", "READINESS_FIELD", "FIELD_LABELS",
    "HISTORICAL_COMBINED_FIELD", "render_lunch_six_core_fields",
    "render_lunch_four_core_fields", "_gate", "_sync_field_gate",
    "_render_workspace_4a", "_render_workspace_4b",
]
