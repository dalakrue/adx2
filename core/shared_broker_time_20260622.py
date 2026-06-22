"""Single authoritative broker-candle display clock.

This module never creates a market timestamp from wall-clock time.  It selects
one already-published completed candle, keeps that value in UTC for identity and
persistence, and projects it into the configured broker clock only for display.
No protected calculation, prediction, strategy, or source dataframe is changed.
"""
from __future__ import annotations

from datetime import timedelta, timezone
from typing import Any, Mapping, MutableMapping

import pandas as pd

_TIME_COLUMNS = (
    "time", "Time", "Datetime", "DateTime", "Timestamp", "timestamp",
    "candle time", "Candle Time", "latest_completed_h1", "latest_completed_candle_time",
)


def _as_utc(value: Any) -> pd.Timestamp | None:
    if value in (None, ""):
        return None
    try:
        parsed = pd.to_datetime(value, errors="coerce", utc=True)
        if isinstance(parsed, pd.DatetimeIndex):
            parsed = parsed.max()
        return None if pd.isna(parsed) else pd.Timestamp(parsed)
    except Exception:
        return None


def _canonical_from_state(state: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        from core.canonical_runtime_20260617 import get_canonical
        current = get_canonical(state)
        if isinstance(current, Mapping):
            return current
    except Exception:
        pass
    for key in (
        "canonical_result_20260617", "canonical_decision_result_20260617",
        "canonical_decision_result", "last_valid_canonical_decision_result_20260617",
    ):
        value = state.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _frame_latest_utc(frame: Any) -> pd.Timestamp | None:
    try:
        from core.market_time_freshness_20260622 import latest_frame_time
        return latest_frame_time(frame)
    except Exception:
        pass
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    for name in _TIME_COLUMNS:
        if name in frame.columns:
            parsed = pd.to_datetime(frame[name], errors="coerce", utc=True)
            valid = parsed.dropna()
            return pd.Timestamp(valid.max()) if not valid.empty else None
    if isinstance(frame.index, pd.DatetimeIndex):
        parsed = pd.to_datetime(frame.index, errors="coerce", utc=True)
        return pd.Timestamp(parsed.max()) if len(parsed) else None
    return None


def _broker_offset_hours(state: Mapping[str, Any]) -> float:
    try:
        from core.market_time_freshness_20260622 import broker_offset_hours
        return float(broker_offset_hours(state))
    except Exception:
        pass
    for key in (
        "mt5_broker_utc_offset_hours_20260622", "broker_utc_offset_hours",
        "mt5_server_utc_offset_hours",
    ):
        try:
            value = float(state.get(key))
            if -12.0 <= value <= 14.0:
                return value
        except Exception:
            continue
    return 0.0


def _offset_label(offset: float) -> str:
    sign = "+" if offset >= 0 else "-"
    total_minutes = int(round(abs(offset) * 60.0))
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}{hours}" if minutes == 0 else f"{sign}{hours}:{minutes:02d}"


def _fixed_timezone(offset: float):
    return timezone(timedelta(minutes=int(round(float(offset) * 60.0))))


def _canonical_completed_utc(canonical: Mapping[str, Any]) -> pd.Timestamp | None:
    market = canonical.get("market") if isinstance(canonical.get("market"), Mapping) else {}
    for value in (
        canonical.get("latest_completed_candle_time"),
        canonical.get("latest_completed_h1"),
        canonical.get("anchor_time"),
        market.get("latest_completed_candle_time"),
        market.get("latest_completed_h1"),
    ):
        parsed = _as_utc(value)
        if parsed is not None:
            return parsed
    return None


def shared_broker_time_provider(
    state: Mapping[str, Any],
    *,
    frame: Any | None = None,
    canonical: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the one shared completed-candle identity and broker display time.

    Precedence is deliberately canonical-first.  A newer connector dataframe is
    not silently presented as if it were already calculated and published.
    """
    canonical = canonical if isinstance(canonical, Mapping) else _canonical_from_state(state)
    completed_utc = _canonical_completed_utc(canonical)
    source = "canonical_completed_h1"
    if completed_utc is None:
        active = frame if isinstance(frame, pd.DataFrame) else state.get("last_df")
        completed_utc = _frame_latest_utc(active)
        source = "loaded_candle_fallback" if completed_utc is not None else "unavailable"

    offset = _broker_offset_hours(state)
    broker_time = completed_utc.tz_convert(_fixed_timezone(offset)) if completed_utc is not None else None
    label = _offset_label(offset)
    return {
        "shared_broker_time": broker_time,
        "shared_broker_time_iso": broker_time.isoformat() if broker_time is not None else None,
        "shared_broker_time_display": broker_time.strftime("%Y-%m-%d %H:%M:%S") + f" (Broker UTC{label})" if broker_time is not None else "Not available",
        "latest_broker_candle_timestamp": broker_time,
        "latest_broker_candle_utc": completed_utc,
        "latest_broker_candle_utc_iso": completed_utc.isoformat() if completed_utc is not None else None,
        "broker_offset_hours": offset,
        "broker_offset_label": label,
        "timestamp_source": source,
        "calculation_id": canonical.get("canonical_calculation_id") or canonical.get("run_id"),
        "calculation_generation": canonical.get("calculation_generation"),
    }


def frame_to_shared_broker_clock(
    frame: pd.DataFrame,
    state: Mapping[str, Any],
    *,
    canonical: Mapping[str, Any] | None = None,
    include_myanmar: bool = True,
) -> pd.DataFrame:
    """Return a display-only frame whose time columns use one broker clock.

    The underlying frame is never mutated.  UTC identity remains unchanged in
    persistence; only the presented columns are converted.
    """
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return frame
    work = frame.copy(deep=False)
    time_col = next((name for name in _TIME_COLUMNS if name in work.columns), None)
    if time_col is None and isinstance(work.index, pd.DatetimeIndex):
        work = work.reset_index().rename(columns={work.index.name or "index": "Time"})
        time_col = "Time"
    if time_col is None:
        return work

    parsed = pd.to_datetime(work[time_col], errors="coerce", utc=True)
    if not parsed.notna().any():
        return work
    clock = shared_broker_time_provider(state, canonical=canonical)
    offset = float(clock.get("broker_offset_hours") or 0.0)
    broker = parsed.dt.tz_convert(_fixed_timezone(offset))
    broker_naive = broker.dt.tz_localize(None)
    label = str(clock.get("broker_offset_label") or _offset_label(offset))
    position = list(work.columns).index(time_col)
    work = work.drop(columns=[time_col])
    work.insert(position, f"Broker Time (UTC{label})", broker_naive)

    if include_myanmar:
        myanmar = parsed.dt.tz_convert(_fixed_timezone(6.5)).dt.tz_localize(None)
        work.insert(position + 1, "Myanmar Time (UTC+6:30)", myanmar)
    if "Date" in work.columns:
        work["Date"] = broker.dt.strftime("%Y-%m-%d")
    if "Weekday" in work.columns:
        work["Weekday"] = broker.dt.strftime("%A")
    if "Hour" in work.columns:
        work["Hour"] = broker.dt.strftime("%H:00")
    return work


def latest_history_utc(frame: Any) -> pd.Timestamp | None:
    return _frame_latest_utc(frame)


def history_sync_status(
    state: Mapping[str, Any],
    *,
    history_frame: Any | None = None,
    canonical: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    clock = shared_broker_time_provider(state, canonical=canonical)
    broker_utc = clock.get("latest_broker_candle_utc")
    history_utc = latest_history_utc(history_frame)
    difference = None
    synced = False
    if isinstance(broker_utc, pd.Timestamp) and isinstance(history_utc, pd.Timestamp):
        difference = abs(float((history_utc - broker_utc).total_seconds())) / 60.0
        synced = difference < 1.0
    offset = float(clock.get("broker_offset_hours") or 0.0)
    history_broker = history_utc.tz_convert(_fixed_timezone(offset)) if history_utc is not None else None
    return {
        **clock,
        "status": "SYNCED" if synced else "OUT OF SYNC",
        "synced": synced,
        "latest_history_record_utc": history_utc,
        "latest_history_record_utc_iso": history_utc.isoformat() if history_utc is not None else None,
        "latest_history_record": history_broker,
        "latest_history_record_display": history_broker.strftime("%Y-%m-%d %H:%M:%S") + f" (Broker UTC{clock.get('broker_offset_label')})" if history_broker is not None else "Not available",
        "difference_minutes": round(difference, 2) if difference is not None else None,
    }


__all__ = [
    "shared_broker_time_provider", "frame_to_shared_broker_clock",
    "history_sync_status", "latest_history_utc",
]
