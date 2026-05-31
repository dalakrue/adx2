import time
import streamlit as st
import pandas as pd
import numpy as np


DEFAULT_TABS = [
    "Home",
    "Engine",
    "Train Data",
    "Pre Original",
    "Database",
    "Profile",
]


def safe_float(v, default=0.0):
    try:
        if v is None:
            return float(default)

        if isinstance(v, str):
            v = v.strip().replace(",", "")
            if v == "":
                return float(default)

        value = float(v)

        if np.isnan(value) or np.isinf(value):
            return float(default)

        return value

    except Exception:
        return float(default)


def safe_int(v, default=0):
    try:
        return int(safe_float(v, default))
    except Exception:
        return int(default)


def init_state():
    defaults = {
        "tab_choice": "Home",
        "symbol": "XAUUSD",
        "phone_mode": False,

        "connected": False,
        "source": "DISCONNECTED",
        "last_df": None,
        "last_fetch": 0,
        "timeframe": "M1",

        "timer_end_time": None,
        "trade_end_time": None,
        "timer_minutes": 120,

        "activity_log": [],
        "notes": [],
        "trade_history": [],
        "profile_name": "Quant Trader",

        "twelve_api_key": "",
        "connector_mode": "fallback",
        "connector_bars": 5000,
        "refresh_seconds": 600,
        "doo_bridge_url": "",
        "doo_bridge_token": "",
        "ws_enabled": False,
        "ws_provider": "generic",
        "ws_url": "",
        "ws_symbol": "XAUUSD",
        "ws_ticks": pd.DataFrame(),
        "account_snapshot": {},
        "doo_positions": [],

        "training_rows": [],
        "guide_restored": True,

        "risk_mode": "Balanced",
        "setting_auto_entry": True,
        "setting_exit_alerts": True,
        "setting_risk_active": True,

        # 2026 system relationship / timing / API health layer.
        # These are additive session keys used by core.system_contract.
        "system_boot_id": "",
        "system_boot_time": "",
        "app_cycle": 0,
        "data_version": 0,
        "data_version_source": "startup",
        "system_events": [],
        "tab_timing": {},
        "tab_runtime_current": {},
        "api_health": {},
        "frontend_health": {},
        "backend_health": {},
        "last_connection_error": "",
        "last_connection_message": "",
        "last_connection_rows": 0,
        "last_connection_mode": "fallback",
        "last_connected_symbol": "XAUUSD",
        "last_connected_timeframe": "M1",
        "last_data_quality": {},
        "uiux_density": "wide",
        "system_snapshot_autosave": True,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Repair corrupted important states
    if not isinstance(st.session_state.get("activity_log"), list):
        st.session_state.activity_log = []

    if not isinstance(st.session_state.get("notes"), list):
        st.session_state.notes = []

    if not isinstance(st.session_state.get("trade_history"), list):
        st.session_state.trade_history = []

    if not isinstance(st.session_state.get("account_snapshot"), dict):
        st.session_state.account_snapshot = {}

    if not isinstance(st.session_state.get("doo_positions"), list):
        st.session_state.doo_positions = []

    if not isinstance(st.session_state.get("training_rows"), list):
        st.session_state.training_rows = []

    if not isinstance(st.session_state.get("system_events"), list):
        st.session_state.system_events = []

    for _dict_key in [
        "tab_timing", "tab_runtime_current", "api_health",
        "frontend_health", "backend_health", "last_data_quality",
    ]:
        if not isinstance(st.session_state.get(_dict_key), dict):
            st.session_state[_dict_key] = {}

    if not st.session_state.get("system_boot_id"):
        try:
            import uuid
            st.session_state.system_boot_id = uuid.uuid4().hex[:12]
        except Exception:
            st.session_state.system_boot_id = "boot"

    if not st.session_state.get("system_boot_time"):
        try:
            st.session_state.system_boot_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            st.session_state.system_boot_time = ""


def log_event(msg):
    try:
        if "activity_log" not in st.session_state or not isinstance(st.session_state.activity_log, list):
            st.session_state.activity_log = []

        st.session_state.activity_log.insert(
            0,
            {
                "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "event": str(msg),
            },
        )

        st.session_state.activity_log = st.session_state.activity_log[:500]

    except Exception:
        pass


def format_timer(seconds):
    try:
        seconds = max(0, int(seconds))
    except Exception:
        seconds = 0

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    return f"{h:02d}:{m:02d}:{s:02d}"


def remaining_time():
    end = st.session_state.get("timer_end_time")

    if not end:
        end = st.session_state.get("trade_end_time")

    if not end:
        return 0

    try:
        return max(0, int(float(end) - time.time()))
    except Exception:
        return 0


def remaining_seconds():
    return remaining_time()


def start_timer(minutes=None):
    if minutes is None:
        minutes = st.session_state.get("timer_minutes", 120)

    minutes = safe_float(minutes, 120)
    minutes = max(1, min(minutes, 1440))

    end_time = time.time() + minutes * 60

    st.session_state.timer_minutes = int(minutes)
    st.session_state.timer_end_time = end_time
    st.session_state.trade_end_time = end_time
    st.session_state.trade_timer_running = True

    log_event(f"Timer started: {minutes} minutes")

    return end_time


def stop_timer():
    st.session_state.timer_end_time = None
    st.session_state.trade_end_time = None
    st.session_state.trade_timer_running = False
    log_event("Timer stopped")


def synthetic_ohlc(symbol="XAUUSD", bars=1500):
    bars = max(50, safe_int(bars, 1500))
    symbol = str(symbol or "XAUUSD").upper()

    rng = np.random.default_rng(abs(hash(symbol)) % (2**32))

    if "XAU" in symbol:
        base = 2350
        scale = 0.70
    elif "JPY" in symbol:
        base = 150
        scale = 0.025
    elif "EUR" in symbol:
        base = 1.08
        scale = 0.00025
    elif "GBP" in symbol:
        base = 1.27
        scale = 0.00035
    elif "BTC" in symbol:
        base = 65000
        scale = 40
    elif "ETH" in symbol:
        base = 3500
        scale = 5
    else:
        base = 100
        scale = 0.10

    steps = rng.normal(0, scale, bars).cumsum()
    close = base + steps
    open_ = np.r_[close[0], close[:-1]]

    high = np.maximum(open_, close) + np.abs(rng.normal(0, scale * 0.5, bars))
    low = np.minimum(open_, close) - np.abs(rng.normal(0, scale * 0.5, bars))
    volume = rng.integers(100, 3000, size=bars)

    return pd.DataFrame(
        {
            "time": pd.date_range(
                end=pd.Timestamp.now(),
                periods=int(bars),
                freq="min",
            ),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def normalize_symbol(symbol="XAUUSD"):
    symbol = str(symbol or "XAUUSD").strip().upper()
    return symbol.replace(" ", "").replace("/", "")


def is_phone_mode():
    return bool(st.session_state.get("phone_mode", False))