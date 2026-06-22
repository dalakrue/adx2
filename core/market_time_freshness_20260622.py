"""Low-cost market/feed time and dataframe freshness diagnostics.

The helper is display-only. It never starts a calculation and never fabricates
broker time. MetaTrader exposes tick timestamps in UTC; an optional user-set
broker UTC offset is applied only to the displayed broker-clock value.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time
from typing import Any, Mapping, MutableMapping

import pandas as pd

_TIME_COLUMNS = ("time", "Time", "Datetime", "DateTime", "Timestamp", "timestamp", "date", "Date")
_INTERVAL_SECONDS = {
    "M1": 60, "M2": 120, "M3": 180, "M4": 240, "M5": 300,
    "M10": 600, "M15": 900, "M30": 1800, "H1": 3600,
    "H4": 14400, "D1": 86400, "CUSTOM": 3600,
}


def _as_utc(value: Any) -> pd.Timestamp | None:
    try:
        parsed = pd.to_datetime(value, errors="coerce", utc=True)
        if isinstance(parsed, pd.DatetimeIndex):
            parsed = parsed.max()
        if pd.isna(parsed):
            return None
        return pd.Timestamp(parsed)
    except Exception:
        return None


def latest_frame_time(frame: Any) -> pd.Timestamp | None:
    """Return the latest valid dataframe timestamp normalized to UTC."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    column = next((name for name in _TIME_COLUMNS if name in frame.columns), None)
    if column is None:
        normalized = {str(c).strip().lower(): c for c in frame.columns}
        column = next((normalized.get(name.lower()) for name in _TIME_COLUMNS if normalized.get(name.lower()) is not None), None)
    if column is None:
        return None
    try:
        parsed = pd.to_datetime(frame[column], errors="coerce", utc=True)
        valid = parsed.dropna()
        return pd.Timestamp(valid.max()) if not valid.empty else None
    except Exception:
        return None


def _floor_interval(now: pd.Timestamp, seconds: int) -> pd.Timestamp:
    epoch = int(now.timestamp())
    return pd.Timestamp((epoch // seconds) * seconds, unit="s", tz="UTC")


def _query_mt5_tick_time(state: MutableMapping[str, Any], *, ttl_seconds: int = 15) -> pd.Timestamp | None:
    """Read one MT5 tick timestamp with a tiny TTL; failures are non-fatal."""
    source = str(state.get("source") or "").upper()
    mode = str(state.get("connector_mode") or "").lower()
    if "MT5" not in source and mode != "mt5":
        return _as_utc(state.get("mt5_latest_tick_time_utc_20260622"))
    now = time.time()
    cached_at = float(state.get("mt5_tick_probe_at_20260622", 0.0) or 0.0)
    cached = _as_utc(state.get("mt5_latest_tick_time_utc_20260622"))
    if cached is not None and now - cached_at < max(5, int(ttl_seconds)):
        return cached
    state["mt5_tick_probe_at_20260622"] = now
    try:
        import MetaTrader5 as mt5  # type: ignore
        initialized_here = False
        try:
            terminal = mt5.terminal_info()
        except Exception:
            terminal = None
        if terminal is None:
            initialized_here = bool(mt5.initialize())
        symbol = str(state.get("symbol") or "EURUSD")
        tick = mt5.symbol_info_tick(symbol)
        raw = getattr(tick, "time_msc", 0) or getattr(tick, "time", 0)
        if raw:
            seconds = float(raw) / 1000.0 if float(raw) > 10_000_000_000 else float(raw)
            value = pd.Timestamp(seconds, unit="s", tz="UTC")
            state["mt5_latest_tick_time_utc_20260622"] = value.isoformat()
            state["mt5_tick_probe_error_20260622"] = ""
            if initialized_here:
                try:
                    mt5.shutdown()
                except Exception:
                    pass
            return value
        state["mt5_tick_probe_error_20260622"] = "No MT5 tick is available for the selected symbol."
        if initialized_here:
            try:
                mt5.shutdown()
            except Exception:
                pass
    except Exception as exc:
        state["mt5_tick_probe_error_20260622"] = f"{type(exc).__name__}: {exc}"[:240]
    return cached


def market_time_snapshot(
    state: MutableMapping[str, Any] | Mapping[str, Any],
    *,
    frame: Any | None = None,
    query_mt5: bool = False,
) -> dict[str, Any]:
    """Return truthful, low-cost UTC/broker/feed freshness values."""
    mutable = state if isinstance(state, MutableMapping) else dict(state)
    now = pd.Timestamp.now(tz="UTC")
    timeframe = str(state.get("timeframe") or "H1").upper()
    seconds = int(_INTERVAL_SECONDS.get(timeframe, 3600))
    active_frame = frame if isinstance(frame, pd.DataFrame) else state.get("last_df")
    latest = latest_frame_time(active_frame)
    current_bar_open = _floor_interval(now, seconds)
    expected_completed_open = current_bar_open - pd.Timedelta(seconds=seconds)
    lag_seconds = None
    lag_bars = None
    if latest is not None:
        lag_seconds = max(0.0, float((current_bar_open - latest).total_seconds()))
        lag_bars = max(0.0, lag_seconds / seconds)
    if latest is None:
        status = "NO DATA"
    elif latest >= expected_completed_open:
        status = "CURRENT"
    elif lag_bars is not None and lag_bars <= 2.0:
        status = "WATCH"
    else:
        status = "LATE"

    last_fetch = state.get("last_fetch")
    try:
        fetch_age_seconds = max(0.0, time.time() - float(last_fetch)) if last_fetch else None
    except Exception:
        fetch_age_seconds = None

    tick = _query_mt5_tick_time(mutable) if query_mt5 else _as_utc(state.get("mt5_latest_tick_time_utc_20260622"))
    try:
        broker_offset = float(state.get("mt5_broker_utc_offset_hours_20260622", 0.0) or 0.0)
    except Exception:
        broker_offset = 0.0
    broker_clock = (tick or now) + pd.Timedelta(hours=broker_offset)

    return {
        "status": status,
        "timeframe": timeframe,
        "current_utc": now.isoformat(),
        "current_utc_display": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "latest_loaded_time": latest.isoformat() if latest is not None else None,
        "latest_loaded_display": latest.strftime("%Y-%m-%d %H:%M:%S UTC") if latest is not None else "No loaded candle",
        "expected_completed_open": expected_completed_open.isoformat(),
        "expected_completed_display": expected_completed_open.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "lag_seconds": lag_seconds,
        "lag_minutes": round(lag_seconds / 60.0, 1) if lag_seconds is not None else None,
        "lag_bars": round(lag_bars, 2) if lag_bars is not None else None,
        "last_fetch_age_seconds": fetch_age_seconds,
        "mt5_tick_time_utc": tick.isoformat() if tick is not None else None,
        "mt5_tick_display": tick.strftime("%Y-%m-%d %H:%M:%S UTC") if tick is not None else "Not available",
        "broker_offset_hours": broker_offset,
        "broker_clock_display": broker_clock.strftime("%Y-%m-%d %H:%M:%S") + f" (UTC{broker_offset:+g})",
        "source": str(state.get("source") or "DISCONNECTED"),
        "rows": int(len(active_frame)) if isinstance(active_frame, pd.DataFrame) else 0,
    }


__all__ = ["latest_frame_time", "market_time_snapshot"]
