import time
import pandas as pd
import requests
import streamlit as st

from core.common import synthetic_ohlc, log_event

try:
    from core.system_contract import (
        mark_data_version,
        update_connection_health,
        update_data_quality_from_session,
        record_system_event,
    )
except Exception:  # keeps old connector usable even if upgrade file is missing
    mark_data_version = None
    update_connection_health = None
    update_data_quality_from_session = None
    record_system_event = None


MT5_TIMEFRAMES = {
    "M1": "TIMEFRAME_M1",
    "M2": "TIMEFRAME_M2",
    "M3": "TIMEFRAME_M3",
    "M4": "TIMEFRAME_M4",
    "M5": "TIMEFRAME_M5",
    "M10": "TIMEFRAME_M10",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}

TWELVE_INTERVALS = {
    "M1": "1min",
    "M2": "1min",
    "M3": "1min",
    "M4": "1min",
    "M5": "5min",
    "M10": "5min",
    "M15": "15min",
    "M30": "30min",
    "H1": "1h",
    "H4": "4h",
    "D1": "1day",
}


def _safe_log(msg):
    try:
        log_event(msg)
    except Exception:
        pass


def _import_mt5():
    try:
        import MetaTrader5 as mt5
        return mt5
    except Exception:
        return None


def _clean_symbol(symbol="XAUUSD"):
    return str(symbol or "XAUUSD").strip().upper().replace("/", "").replace(" ", "")


def _twelve_symbol(symbol="XAUUSD"):
    raw = _clean_symbol(symbol)

    mapping = {
        "XAUUSD": "XAU/USD",
        "XAGUSD": "XAG/USD",
        "EURUSD": "EUR/USD",
        "GBPUSD": "GBP/USD",
        "USDJPY": "USD/JPY",
        "AUDUSD": "AUD/USD",
        "USDCAD": "USD/CAD",
        "USDCHF": "USD/CHF",
        "NZDUSD": "NZD/USD",
        "BTCUSD": "BTC/USD",
        "ETHUSD": "ETH/USD",
    }

    return mapping.get(raw, raw)


def _normalize_ohlc(df):
    if df is None or len(df) == 0:
        return pd.DataFrame()

    df = df.copy()

    rename_map = {
        "datetime": "time",
        "date": "time",
        "timestamp": "time",
        "tick_volume": "volume",
        "real_volume": "volume",
    }

    for old, new in rename_map.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})

    if "time" not in df.columns:
        return pd.DataFrame()

    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    for c in ["open", "high", "low", "close"]:
        if c not in df.columns:
            return pd.DataFrame()
        df[c] = pd.to_numeric(df[c], errors="coerce")

    if "volume" not in df.columns:
        df["volume"] = 0

    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)

    df = df.dropna(subset=["time", "open", "high", "low", "close"])
    df = df.sort_values("time").drop_duplicates(subset=["time"]).reset_index(drop=True)

    if df.empty:
        return pd.DataFrame()

    return df[["time", "open", "high", "low", "close", "volume"]].copy()


def resample_ohlc(df, timeframe="M2"):
    df = _normalize_ohlc(df)

    if df.empty:
        return pd.DataFrame()

    tf = str(timeframe or "M1").strip().upper()

    if tf in ("M1", "1MIN", "1T"):
        return df.copy()

    minute_map = {
        "M2": "2min",
        "M3": "3min",
        "M4": "4min",
        "M5": "5min",
        "M10": "10min",
        "M15": "15min",
        "M30": "30min",
    }

    rule = minute_map.get(tf)

    if not rule:
        return df.copy()

    out = (
        df.set_index("time")
        .resample(rule, label="right", closed="right")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
        .reset_index()
    )

    return out[["time", "open", "high", "low", "close", "volume"]].copy()


def fetch_mt5(symbol="XAUUSD", timeframe="M1", bars=500):
    mt5 = _import_mt5()

    if mt5 is None:
        return None, False, "MetaTrader5 library not installed or unsupported here"

    try:
        if not mt5.initialize():
            mt5.shutdown()
            if not mt5.initialize():
                return None, False, "MT5 initialize failed. Open MT5 terminal and login first."

        symbol = _clean_symbol(symbol)
        timeframe = str(timeframe or "M1").upper()

        tf_name = MT5_TIMEFRAMES.get(timeframe, "TIMEFRAME_M1")
        tf = getattr(mt5, tf_name, getattr(mt5, "TIMEFRAME_M1"))

        mt5.symbol_select(symbol, True)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, int(bars))

        if rates is None or len(rates) < 30:
            if timeframe in ["M2", "M3", "M4", "M10"]:
                rates = mt5.copy_rates_from_pos(
                    symbol,
                    getattr(mt5, "TIMEFRAME_M1"),
                    0,
                    int(bars) * 5,
                )

                if rates is None or len(rates) < 30:
                    return None, False, f"No MT5 {timeframe}/M1 rates returned"

                df = pd.DataFrame(rates)
                df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
                df = _normalize_ohlc(df)
                return resample_ohlc(df, timeframe), True, f"MT5 M1 resampled to {timeframe}"

            return None, False, "No MT5 rates returned"

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
        df = _normalize_ohlc(df)

        return df, True, f"MT5 connected {timeframe}"

    except Exception as e:
        return None, False, f"MT5 error: {e}"


def fetch_twelve(symbol="XAUUSD", api_key="", interval="1min", bars=500):
    try:
        if not api_key:
            return None, False, "Missing Twelve Data API key"

        sym = _twelve_symbol(symbol)

        requested_bars = max(1, int(bars or 500))
        # Twelve Data rejects very large outputsize values. Keep the app fast and
        # prevent API Health from showing "Invalid outputsize" when the user
        # chooses 60,000+ candles for deep panels. Deep analysis can still use
        # the cached/shared dataframe, while Twelve requests stay valid.
        safe_bars = min(requested_bars, 5000)

        params = {
            "symbol": sym,
            "interval": interval,
            "outputsize": int(safe_bars),
            "apikey": api_key,
            "format": "JSON",
        }

        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params=params,
            timeout=20,
        )

        try:
            data = r.json()
        except Exception:
            return None, False, f"Twelve Data invalid response: HTTP {r.status_code}"

        if "values" not in data:
            return None, False, str(data)[:250]

        df = pd.DataFrame(data["values"]).iloc[::-1].reset_index(drop=True)

        if "datetime" in df.columns:
            df["time"] = pd.to_datetime(df["datetime"], errors="coerce")

        df = _normalize_ohlc(df)

        cap_note = f" capped {safe_bars:,}/{requested_bars:,}" if requested_bars > safe_bars else ""
        return df, True, f"Twelve Data connected {interval}{cap_note}"

    except Exception as e:
        return None, False, f"Twelve error: {e}"


def fetch_doo_bridge(
    symbol="XAUUSD",
    timeframe="M1",
    bars=500,
    bridge_url="",
    bridge_token="",
):
    try:
        bridge_url = str(bridge_url or "").strip()

        if not bridge_url:
            return None, False, "Missing Doo Bridge URL"

        headers = {}

        if bridge_token:
            headers["Authorization"] = f"Bearer {bridge_token}"

        params = {
            "symbol": _clean_symbol(symbol),
            "timeframe": str(timeframe or "M1").upper(),
            "bars": int(bars),
        }

        r = requests.get(bridge_url, params=params, headers=headers, timeout=25)

        try:
            data = r.json()
        except Exception:
            return None, False, f"Doo Bridge invalid response: HTTP {r.status_code}"

        if not data.get("ok", False):
            return None, False, str(data.get("message", data))[:250]

        candles = data.get("candles", [])

        if not candles:
            return None, False, "Doo Bridge returned no candles"

        df = pd.DataFrame(candles)
        df = _normalize_ohlc(df)

        if "account" in data:
            st.session_state.account_snapshot = data.get("account", {})

        if "positions" in data:
            st.session_state.doo_positions = data.get("positions", [])

        return df, True, "Doo Bridge connected"

    except Exception as e:
        return None, False, f"Doo Bridge error: {e}"


def manual_connect(
    mode="fallback",
    symbol="XAUUSD",
    api_key="",
    bars=500,
    timeframe="M1",
    bridge_url="",
    bridge_token="",
):
    timeframe = str(timeframe or "M1").upper()
    mode = str(mode or "fallback").lower()

    df = None
    ok = False
    msg = ""
    source = "UNKNOWN"

    if mode == "mt5":
        df, ok, msg = fetch_mt5(symbol, timeframe=timeframe, bars=bars)
        source = "MT5" if ok else "MT5_FAILED"

    elif mode == "doo_bridge":
        df, ok, msg = fetch_doo_bridge(
            symbol=symbol,
            timeframe=timeframe,
            bars=bars,
            bridge_url=bridge_url,
            bridge_token=bridge_token,
        )
        source = "DOO_BRIDGE" if ok else "DOO_BRIDGE_FAILED"

    elif mode == "twelve":
        raw_tf = TWELVE_INTERVALS.get(timeframe, "1min")

        raw_bars = int(bars)

        if timeframe in ["M2", "M3", "M4", "M10"]:
            raw_tf = "1min"
            raw_bars = int(bars) * 5

        df, ok, msg = fetch_twelve(symbol, api_key, interval=raw_tf, bars=raw_bars)

        if ok and timeframe in ["M2", "M3", "M4", "M10"]:
            df = resample_ohlc(df, timeframe)
            msg = f"{msg} → resampled to {timeframe}"

        source = "TWELVE" if ok else "TWELVE_FAILED"

    else:
        df, ok, msg = fetch_mt5(symbol, timeframe=timeframe, bars=bars)
        source = "MT5" if ok else "MT5_FAILED"

        if not ok and bridge_url:
            df, ok, msg = fetch_doo_bridge(
                symbol=symbol,
                timeframe=timeframe,
                bars=bars,
                bridge_url=bridge_url,
                bridge_token=bridge_token,
            )
            source = "DOO_BRIDGE" if ok else "DOO_BRIDGE_FAILED"

        if not ok:
            raw_tf = TWELVE_INTERVALS.get(timeframe, "1min")
            raw_bars = int(bars)

            if timeframe in ["M2", "M3", "M4", "M10"]:
                raw_tf = "1min"
                raw_bars = int(bars) * 5

            df, ok, msg = fetch_twelve(symbol, api_key, interval=raw_tf, bars=raw_bars)

            if ok and timeframe in ["M2", "M3", "M4", "M10"]:
                df = resample_ohlc(df, timeframe)
                msg = f"{msg} → resampled to {timeframe}"

            source = "TWELVE" if ok else "FALLBACK_FAILED"

    if not ok and st.session_state.get("last_df") is not None:
        cached = _normalize_ohlc(st.session_state.last_df)
        if not cached.empty:
            df = cached
            ok = True
            source = "CACHE"
            msg = f"{msg} | using last cached dataframe so tabs do not blank"

    if not ok:
        base_bars = int(bars or 1500)

        if timeframe in ["M2", "M3", "M4", "M10"]:
            base_bars *= 5

        df = synthetic_ohlc(symbol, max(base_bars, 1500))

        if timeframe in ["M2", "M3", "M4", "M10"]:
            df = resample_ohlc(df, timeframe)

        ok = True
        source = "SAFE_DEMO"
        msg = f"{msg} | using safe demo data so dashboard does not blank"

    df = _normalize_ohlc(df)

    if df.empty:
        df = synthetic_ohlc(symbol, 1500)
        if timeframe in ["M2", "M3", "M4", "M10"]:
            df = resample_ohlc(df, timeframe)
        df = _normalize_ohlc(df)
        source = "SAFE_DEMO"
        msg = f"{msg} | normalized data empty, replaced by safe demo"

    st.session_state.last_df = df
    st.session_state.connected = True
    st.session_state.source = source
    st.session_state.last_fetch = time.time()
    st.session_state.timeframe = timeframe
    st.session_state.symbol = _clean_symbol(symbol)

    # 2026 non-destructive relationship/timing upgrade:
    # every successful connector run increments one shared data version and
    # writes a compact API/connection health event for all tabs to read.
    try:
        if mark_data_version is not None:
            mark_data_version(source=source, rows=len(df))
        if update_connection_health is not None:
            update_connection_health(
                mode=mode,
                source=source,
                ok=bool(ok),
                message=msg,
                rows=len(df),
                symbol=_clean_symbol(symbol),
                timeframe=timeframe,
                persist=True,
            )
        if update_data_quality_from_session is not None:
            update_data_quality_from_session(persist=True)
    except Exception:
        pass

    _safe_log(f"Connected {source}: {_clean_symbol(symbol)} {timeframe}")

    return df, bool(ok), source, msg


def maybe_refresh(
    symbol="XAUUSD",
    api_key="",
    refresh_seconds=600,
    bridge_url="",
    bridge_token="",
):
    if not st.session_state.get("connected"):
        return st.session_state.get("last_df")

    last = st.session_state.get("last_fetch", 0)

    try:
        should_refresh = time.time() - float(last) >= float(refresh_seconds)
    except Exception:
        should_refresh = True

    if should_refresh:
        source = st.session_state.get("source", "")

        if source == "MT5":
            mode = "mt5"
        elif source == "TWELVE":
            mode = "twelve"
        elif source == "DOO_BRIDGE":
            mode = "doo_bridge"
        else:
            mode = "fallback"

        manual_connect(
            mode=mode,
            symbol=symbol,
            api_key=api_key,
            bars=int(st.session_state.get("connector_bars", 600)),
            timeframe=st.session_state.get("timeframe", "M1"),
            bridge_url=bridge_url,
            bridge_token=bridge_token,
        )

    return st.session_state.get("last_df")


def mt5_account_info():
    mt5 = _import_mt5()

    if mt5 is None:
        return {}, False, "MT5 unavailable"

    try:
        if not mt5.initialize():
            return {}, False, "MT5 init failed"

        info = mt5.account_info()
        positions = mt5.positions_get()

        account = info._asdict() if info else {}

        pos = []
        for p in positions or []:
            try:
                pos.append(p._asdict())
            except Exception:
                pass

        account["positions"] = pos

        return account, True, "Account read ok"

    except Exception as e:
        return {}, False, str(e)


def doo_bridge_account_info(bridge_url="", bridge_token=""):
    try:
        bridge_url = str(bridge_url or "").strip()

        if not bridge_url:
            return {}, False, "Missing Doo Bridge URL"

        headers = {}

        if bridge_token:
            headers["Authorization"] = f"Bearer {bridge_token}"

        r = requests.get(
            bridge_url,
            params={"account": "1"},
            headers=headers,
            timeout=25,
        )

        try:
            data = r.json()
        except Exception:
            return {}, False, f"Doo Bridge invalid response: HTTP {r.status_code}"

        if not data.get("ok", False):
            return {}, False, str(data.get("message", data))[:250]

        account = data.get("account", {})
        positions = data.get("positions", [])

        if not isinstance(account, dict):
            account = {}

        account["positions"] = positions if isinstance(positions, list) else []

        return account, True, "Doo Bridge account read ok"

    except Exception as e:
        return {}, False, f"Doo Bridge account error: {e}"


def connect_history_60d(
    mode="fallback",
    symbol="XAUUSD",
    api_key="",
    timeframe="M1",
    bridge_url="",
    bridge_token="",
):
    tf = str(timeframe or "M1").upper()

    if tf == "M1":
        bars = 120000
    elif tf in ["M2", "M3", "M4"]:
        bars = 80000
    elif tf in ["M5", "M10", "M15"]:
        bars = 30000
    elif tf in ["M30", "H1"]:
        bars = 10000
    else:
        bars = 5000

    return manual_connect(
        mode=mode,
        symbol=symbol,
        api_key=api_key,
        bars=bars,
        timeframe=tf,
        bridge_url=bridge_url,
        bridge_token=bridge_token,
    )


def get_mt5_account_snapshot(bridge_url="", bridge_token=""):
    if bridge_url:
        info, ok, msg = doo_bridge_account_info(
            bridge_url=bridge_url,
            bridge_token=bridge_token,
        )
    else:
        info, ok, msg = mt5_account_info()

    positions = info.get("positions", []) if isinstance(info, dict) else []
    account = dict(info) if isinstance(info, dict) else {}
    account.pop("positions", None)

    return {
        "ok": bool(ok),
        "message": msg,
        "account": account,
        "positions": positions,
    }