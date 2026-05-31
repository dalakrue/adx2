import time
import numpy as np
import pandas as pd
import streamlit as st

from core.data_connectors import manual_connect
from core.database import append_csv, read_csv


# ============================================================
# SAFE HELPERS
# ============================================================

def s(x, default=0.0):
    try:
        if x is None:
            return float(default)
        if isinstance(x, str) and x.strip() == "":
            return float(default)
        v = float(x)
        if not np.isfinite(v):
            return float(default)
        return v
    except Exception:
        return float(default)


def clamp(x, low=0.0, high=100.0):
    return max(low, min(high, s(x)))


def safe_append(name, row):
    try:
        append_csv(name, row)
    except Exception:
        pass


def normalize_ohlc(df):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()

    work = df.copy()
    work.columns = [str(c).strip() for c in work.columns]

    rename = {
        "datetime": "time",
        "date": "time",
        "timestamp": "time",
        "Time": "time",
        "Datetime": "time",
        "Date": "time",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "tick_volume": "volume",
        "real_volume": "volume",
    }

    for old, new in rename.items():
        if old in work.columns and new not in work.columns:
            work = work.rename(columns={old: new})

    work = work.rename(columns={c: str(c).lower() for c in work.columns})

    if "time" not in work.columns:
        work["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(work), freq="1min")

    if "close" not in work.columns:
        return pd.DataFrame()

    for col in ["open", "high", "low", "close"]:
        if col not in work.columns:
            work[col] = work["close"]
        work[col] = pd.to_numeric(work[col], errors="coerce").ffill().bfill()

    if "volume" not in work.columns:
        work["volume"] = 0

    work["volume"] = pd.to_numeric(work["volume"], errors="coerce").fillna(0)
    work["time"] = pd.to_datetime(work["time"], errors="coerce")

    work = work.dropna(subset=["time", "open", "high", "low", "close"])
    return work.sort_values("time").reset_index(drop=True)


def add_live_indicators(df):
    work = normalize_ohlc(df)

    if work.empty:
        return pd.DataFrame()

    high = work["high"]
    low = work["low"]
    close = work["close"]
    open_ = work["open"]
    prev_close = close.shift(1)

    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.rolling(14, min_periods=1).mean()

    up = high.diff()
    down = -low.diff()

    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=work.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=work.index)

    plus_di = 100 * plus_dm.rolling(14, min_periods=1).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.rolling(14, min_periods=1).mean() / atr.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(14, min_periods=1).mean()

    work["atr"] = atr
    work["plus_di"] = plus_di
    work["minus_di"] = minus_di
    work["adx"] = adx
    work["pressure"] = plus_di - minus_di
    work["adx_slope"] = work["adx"].diff().fillna(0)
    work["atr_slope"] = work["atr"].diff().fillna(0)

    work["ret"] = close.pct_change().fillna(0)
    work["log_ret"] = np.log(close.replace(0, np.nan) / close.shift(1).replace(0, np.nan))
    work["log_ret"] = work["log_ret"].replace([np.inf, -np.inf], 0).fillna(0)

    work["range"] = (high - low).replace(0, np.nan)
    work["body"] = (close - open_).abs()
    work["wick_ratio"] = ((work["range"] - work["body"]) / work["range"]).replace([np.inf, -np.inf], 0).fillna(0)
    work["candle_efficiency"] = (work["body"] / work["range"]).replace([np.inf, -np.inf], 0).fillna(0)

    work["momentum_5"] = close.diff(5).fillna(0)
    work["momentum_10"] = close.diff(10).fillna(0)
    work["momentum_20"] = close.diff(20).fillna(0)

    work["ema_20"] = close.ewm(span=20, adjust=False).mean()
    work["ema_50"] = close.ewm(span=50, adjust=False).mean()
    work["ema_gap"] = work["ema_20"] - work["ema_50"]

    work["volatility"] = work["ret"].rolling(30, min_periods=1).std().fillna(0)
    work["trend_power"] = work["adx"] * work["pressure"].abs()

    mean_120 = close.rolling(120, min_periods=20).mean()
    std_120 = close.rolling(120, min_periods=20).std().replace(0, np.nan)
    work["mean_z"] = ((close - mean_120) / std_120).replace([np.inf, -np.inf], 0).fillna(0)

    work["volume_z"] = (
        (work["volume"] - work["volume"].rolling(80, min_periods=10).mean())
        / work["volume"].rolling(80, min_periods=10).std().replace(0, np.nan)
    ).replace([np.inf, -np.inf], 0).fillna(0)

    work["spoofing_proxy"] = (
        work["wick_ratio"].clip(0, 1) * 45
        + (1 - work["candle_efficiency"].clip(0, 1)) * 35
        + work["volume_z"].abs().clip(0, 5) * 4
    ).fillna(0)

    return work.replace([np.inf, -np.inf], 0).fillna(0)


def calculate_engine(dfi, trade_direction="BUY", horizon_hours=2):
    if dfi is None or dfi.empty:
        return {}

    last = dfi.iloc[-1]
    prev = dfi.iloc[-2] if len(dfi) > 1 else last

    plus_now = s(last.get("plus_di"))
    minus_now = s(last.get("minus_di"))
    plus_prev = s(prev.get("plus_di"))
    minus_prev = s(prev.get("minus_di"))

    pressure = plus_now - minus_now
    prev_pressure = plus_prev - minus_prev
    pressure_accel = pressure - prev_pressure

    adx = s(last.get("adx"))
    atr = s(last.get("atr"))
    adx_slope = s(last.get("adx_slope"))
    atr_slope = s(last.get("atr_slope"))

    momentum_5 = s(last.get("momentum_5"))
    momentum_10 = s(last.get("momentum_10"))
    momentum_20 = s(last.get("momentum_20"))

    ema_gap = s(last.get("ema_gap"))
    wick_ratio = s(last.get("wick_ratio"))
    candle_efficiency = s(last.get("candle_efficiency"))
    mean_z = s(last.get("mean_z"))
    volatility = s(last.get("volatility"))
    trend_power = s(last.get("trend_power"))
    spoofing_proxy = s(last.get("spoofing_proxy"))

    direction_sign = 1 if trade_direction == "BUY" else -1
    direction_pressure = pressure * direction_sign
    direction_momentum = momentum_10 * direction_sign
    direction_ema = ema_gap * direction_sign

    dominance_ratio = plus_now / max(abs(minus_now), 1.0)
    if trade_direction == "SELL":
        dominance_ratio = minus_now / max(abs(plus_now), 1.0)

    dss = ((plus_now - minus_now) * 0.7) + ((plus_prev - minus_prev) * 0.3)
    dss_accel = 2 * (plus_now - minus_now) - (plus_prev - minus_prev)
    ns = abs(dss) / max(plus_now + minus_now, 1)
    stab = abs(plus_now - plus_prev) + abs(minus_now - minus_prev)
    cr = dominance_ratio
    momq = dss_accel * ns
    tci = (dss * ns * cr) / (1 + stab)
    esi = (abs(dss) + abs(dss_accel)) / (ns + 0.01)

    trend_score = clamp(adx / 35 * 100)
    pressure_score = clamp(abs(pressure) / 25 * 100)
    direction_score = clamp((direction_pressure + 20) / 40 * 100)
    momentum_score = clamp((direction_momentum / max(atr, 1e-9)) * 30 + 50)
    ema_score = clamp((direction_ema / max(atr, 1e-9)) * 25 + 50)
    candle_score = clamp(candle_efficiency * 100)
    wick_risk = clamp(wick_ratio * 100)
    spoof_risk = clamp(spoofing_proxy)
    mean_revert_risk = clamp(abs(mean_z) * 22)
    exhaustion_risk = clamp(max(0, adx - 35) * 2 + max(0, -adx_slope) * 8 + wick_risk * 0.25)

    alignment_count = 0
    alignment_count += 1 if direction_pressure > 0 else 0
    alignment_count += 1 if direction_momentum > 0 else 0
    alignment_count += 1 if direction_ema > 0 else 0
    alignment_count += 1 if adx >= 18 else 0

    horizon_factor = {2: 1.00, 4: 1.08, 6: 1.15, 8: 1.22, 12: 1.35}.get(int(horizon_hours), 1.0)

    continuation_probability = (
        direction_score * 0.24
        + trend_score * 0.18
        + momentum_score * 0.18
        + ema_score * 0.12
        + candle_score * 0.10
        + clamp(abs(tci) * 12) * 0.10
        + clamp(abs(momq) * 20) * 0.08
    )

    risk_score = (
        mean_revert_risk * 0.25
        + spoof_risk * 0.25
        + wick_risk * 0.18
        + exhaustion_risk * 0.20
        + clamp(volatility * 10000) * 0.12
    ) * horizon_factor

    final_quality = clamp(continuation_probability - risk_score * 0.35)
    exit_pressure = clamp(risk_score * 0.55 + exhaustion_risk * 0.30 + spoof_risk * 0.15)

    if final_quality >= 75:
        grade = "A+ EXCELLENT"
    elif final_quality >= 62:
        grade = "A GOOD"
    elif final_quality >= 48:
        grade = "B SELECTIVE"
    elif final_quality >= 35:
        grade = "C RISKY"
    else:
        grade = "NO TRADE"

    model_bias = "BUY" if pressure > 5 and momentum_10 > 0 else "SELL" if pressure < -5 and momentum_10 < 0 else "WAIT"
    user_align = "YES" if model_bias == trade_direction else "NO"

    return {
        "Trade Direction": trade_direction,
        "Horizon Hours": horizon_hours,
        "Model Bias": model_bias,
        "User Align": user_align,
        "Final Quality %": round(final_quality, 2),
        "Grade": grade,
        "Continuation Probability %": round(clamp(continuation_probability), 2),
        "Exit Pressure %": round(exit_pressure, 2),
        "Risk Score %": round(clamp(risk_score), 2),
        "Alignment Count /4": alignment_count,
        "ADX": round(adx, 2),
        "+DI": round(plus_now, 2),
        "-DI": round(minus_now, 2),
        "Pressure": round(pressure, 2),
        "Pressure Accel": round(pressure_accel, 2),
        "ATR": round(atr, 5),
        "ATR Slope": round(atr_slope, 5),
        "ADX Slope": round(adx_slope, 2),
        "Momentum 5": round(momentum_5, 5),
        "Momentum 10": round(momentum_10, 5),
        "Momentum 20": round(momentum_20, 5),
        "EMA Gap": round(ema_gap, 5),
        "DSS": round(dss, 4),
        "DSS Accel": round(dss_accel, 4),
        "NS": round(ns, 4),
        "STAB": round(stab, 4),
        "CR": round(cr, 4),
        "MOMQ": round(momq, 4),
        "TCI": round(tci, 4),
        "ESI": round(esi, 4),
        "Trend Score %": round(trend_score, 2),
        "Pressure Score %": round(pressure_score, 2),
        "Direction Score %": round(direction_score, 2),
        "Momentum Score %": round(momentum_score, 2),
        "EMA Score %": round(ema_score, 2),
        "Candle Efficiency %": round(candle_score, 2),
        "Wick Risk %": round(wick_risk, 2),
        "Spoofing Risk %": round(spoof_risk, 2),
        "Mean Revert Risk %": round(mean_revert_risk, 2),
        "Exhaustion Risk %": round(exhaustion_risk, 2),
        "Volatility": round(volatility, 8),
        "Trend Power": round(trend_power, 2),
        "Mean Z": round(mean_z, 4),
    }


def connect_data(source, symbol, api_key, bars, timeframe):
    try:
        with st.spinner(f"Connecting {source.upper()} {symbol} {timeframe}..."):
            try:
                manual_connect(source, symbol, api_key, bars=int(bars), timeframe=timeframe)
            except TypeError:
                manual_connect(source, symbol, api_key, bars=int(bars))

        df = st.session_state.get("last_df")
        if not isinstance(df, pd.DataFrame) or df.empty:
            st.error("Connected, but no dataframe returned in st.session_state['last_df'].")
            return False

        st.success(f"{source.upper()} loaded {len(df):,} candles.")
        return True

    except Exception as e:
        st.error(f"{source.upper()} connection error: {e}")
        return False


def show_metrics_grid(data, cols_count=4):
    items = list(data.items())
    for i in range(0, len(items), cols_count):
        cols = st.columns(cols_count)
        for col, (k, v) in zip(cols, items[i:i + cols_count]):
            col.metric(k, v)


def show():
    st.markdown("# 📡 Prelive Full Analysis Dashboard")
    st.caption("MT5 / Twelve Data connector + many metrics. You choose BUY/SELL and horizon; dashboard shows raw structure for your own analysis.")

    st.session_state.setdefault("symbol", "XAUUSD")
    st.session_state.setdefault("twelve_api_key", "")

    top = st.columns(5)

    with top[0]:
        symbol = st.text_input("Symbol", value=st.session_state.get("symbol", "XAUUSD"), key="prelive_symbol")
        st.session_state.symbol = str(symbol or "XAUUSD").upper().strip()

    with top[1]:
        timeframe = st.selectbox("Timeframe", ["M1", "M2", "M3", "M5", "M15", "M30", "H1", "H4"], index=0, key="prelive_tf")

    with top[2]:
        bars = st.number_input("Candles", min_value=100, max_value=100000, value=5000, step=100, key="prelive_bars")

    with top[3]:
        trade_direction = st.selectbox("Your Trade Decision", ["BUY", "SELL"], key="prelive_trade_direction")

    with top[4]:
        horizon_hours = st.selectbox("Prediction / Hold Horizon", [2, 4, 6, 8, 12], index=0, key="prelive_horizon")

    st.text_input("Twelve Data API Key", value=st.session_state.get("twelve_api_key", ""), type="password", key="twelve_api_key")

    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button("🔌 Connect MT5", use_container_width=True, key="prelive_connect_mt5"):
            if connect_data("mt5", st.session_state.symbol, st.session_state.twelve_api_key, bars, timeframe):
                st.rerun()

    with b2:
        if st.button("🌐 Connect Twelve Data", use_container_width=True, key="prelive_connect_twelve"):
            if connect_data("twelve", st.session_state.symbol, st.session_state.twelve_api_key, bars, timeframe):
                st.rerun()

    with b3:
        if st.button("🧪 Connect Fallback", use_container_width=True, key="prelive_connect_fallback"):
            if connect_data("fallback", st.session_state.symbol, st.session_state.twelve_api_key, bars, timeframe):
                st.rerun()

    df = st.session_state.get("last_df")

    if df is None:
        st.warning("Connect MT5, Twelve Data, or Fallback first.")
        return

    df = normalize_ohlc(df)

    if df.empty:
        st.error("Data loaded but OHLC columns are invalid.")
        return

    dfi = add_live_indicators(df)

    if dfi.empty:
        st.error("Indicator calculation failed.")
        return

    result = calculate_engine(dfi, trade_direction, int(horizon_hours))

    st.divider()
    st.markdown("## 🎯 Your Selected Trade Analysis")
    show_metrics_grid(
        {
            "Your Direction": result["Trade Direction"],
            "Horizon": f"{result['Horizon Hours']}H",
            "Model Bias": result["Model Bias"],
            "User Align": result["User Align"],
            "Final Quality": f"{result['Final Quality %']}%",
            "Grade": result["Grade"],
            "Continuation": f"{result['Continuation Probability %']}%",
            "Exit Pressure": f"{result['Exit Pressure %']}%",
        },
        4,
    )

    st.markdown("## 📊 Core Market Metrics")
    show_metrics_grid(
        {
            "ADX": result["ADX"],
            "+DI": result["+DI"],
            "-DI": result["-DI"],
            "Pressure": result["Pressure"],
            "Pressure Accel": result["Pressure Accel"],
            "ATR": result["ATR"],
            "ATR Slope": result["ATR Slope"],
            "ADX Slope": result["ADX Slope"],
            "Momentum 5": result["Momentum 5"],
            "Momentum 10": result["Momentum 10"],
            "Momentum 20": result["Momentum 20"],
            "EMA Gap": result["EMA Gap"],
        },
        4,
    )

    st.markdown("## 🧠 DSS / TCI / MOMQ Structure")
    show_metrics_grid(
        {
            "DSS": result["DSS"],
            "DSS Accel": result["DSS Accel"],
            "NS": result["NS"],
            "STAB": result["STAB"],
            "CR": result["CR"],
            "MOMQ": result["MOMQ"],
            "TCI": result["TCI"],
            "ESI": result["ESI"],
            "Alignment /4": result["Alignment Count /4"],
        },
        3,
    )

    st.markdown("## ⚠️ Risk / Quality Metrics")
    show_metrics_grid(
        {
            "Trend Score": f"{result['Trend Score %']}%",
            "Pressure Score": f"{result['Pressure Score %']}%",
            "Direction Score": f"{result['Direction Score %']}%",
            "Momentum Score": f"{result['Momentum Score %']}%",
            "EMA Score": f"{result['EMA Score %']}%",
            "Candle Efficiency": f"{result['Candle Efficiency %']}%",
            "Wick Risk": f"{result['Wick Risk %']}%",
            "Spoofing Risk": f"{result['Spoofing Risk %']}%",
            "Mean Revert Risk": f"{result['Mean Revert Risk %']}%",
            "Exhaustion Risk": f"{result['Exhaustion Risk %']}%",
            "Volatility": result["Volatility"],
            "Trend Power": result["Trend Power"],
            "Mean Z": result["Mean Z"],
            "Risk Score": f"{result['Risk Score %']}%",
        },
        4,
    )

    st.markdown("## 📈 Live Chart")
    chart_cols = [c for c in ["close", "adx", "pressure", "atr", "momentum_10", "ema_gap"] if c in dfi.columns]

    try:
        st.line_chart(dfi.tail(300).set_index("time")[chart_cols])
    except Exception:
        st.line_chart(dfi.tail(300)[chart_cols])

    st.markdown("## 🧾 Latest Data Table")
    show_cols = [
        "time", "open", "high", "low", "close",
        "adx", "plus_di", "minus_di", "pressure",
        "atr", "adx_slope", "atr_slope",
        "momentum_5", "momentum_10", "momentum_20",
        "ema_gap", "wick_ratio", "candle_efficiency",
        "mean_z", "spoofing_proxy",
    ]

    show_cols = [c for c in show_cols if c in dfi.columns]
    with st.expander("📋 Open latest Prelive dataframe", expanded=False):
        st.dataframe(dfi[show_cols].tail(300), use_container_width=True, height=480)

    safe_append(
        "prelive_snapshots",
        {
            "time": pd.Timestamp.now(),
            "symbol": st.session_state.symbol,
            "timeframe": timeframe,
            **result,
        },
    )

    with st.expander("Debug"):
        st.write("Rows:", len(dfi))
        st.write("Columns:", list(dfi.columns))
        st.json(result)