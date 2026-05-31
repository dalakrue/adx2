# tabs/backtest_original.py
# Copy-paste ready Streamlit tab.
# This file does NOT need backtest_legacy_original.py.
# It only connects to MT5 or Twelve Data after you click a connect button.

import os
import traceback
from datetime import timedelta

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


# =========================================================
# OPTIONAL AUTO REFRESH FALLBACK
# =========================================================
try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None


# =========================================================
# SESSION KEYS
# =========================================================
RAW_KEY = "combined_original_backtest_raw_df"
SOURCE_KEY = "combined_original_backtest_source"
SYMBOL_KEY = "combined_original_backtest_symbol"
LAST_LOAD_KEY = "combined_original_backtest_last_load"
BT_RESULT_KEY = "combined_original_backtest_result"
LAST_RUN_KEY = "combined_original_backtest_last_run"


# =========================================================
# SAFE HELPERS
# =========================================================
def _safe_secrets_get(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def _clean_symbol_for_mt5(symbol: str) -> str:
    symbol = str(symbol or "XAUUSD").strip()
    return symbol.replace("/", "").replace(" ", "").upper()


def _clean_symbol_for_twelve(symbol: str) -> str:
    symbol = str(symbol or "XAU/USD").strip().upper()

    if symbol == "XAUUSD":
        return "XAU/USD"
    if symbol == "EURUSD":
        return "EUR/USD"
    if symbol == "GBPUSD":
        return "GBP/USD"
    if symbol == "USDJPY":
        return "USD/JPY"

    return symbol


def _normalize_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    if "datetime" in df.columns and "time" not in df.columns:
        df = df.rename(columns={"datetime": "time"})

    required = ["time", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Missing OHLC columns: {missing}")

    if np.issubdtype(df["time"].dtype, np.number):
        df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
    else:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")

    for col in ["open", "high", "low", "close", "volume", "tick_volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["time", "open", "high", "low", "close"])
    df = df.sort_values("time").drop_duplicates(subset=["time"]).reset_index(drop=True)

    if "volume" not in df.columns:
        if "tick_volume" in df.columns:
            df["volume"] = df["tick_volume"]
        else:
            df["volume"] = 0

    return df[["time", "open", "high", "low", "close", "volume"]].copy()


def _true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)

    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return tr.replace([np.inf, -np.inf], np.nan)


def _add_indicators(
    df: pd.DataFrame,
    adx_period: int = 20,
    atr_period: int = 14,
    prefix: str = "",
) -> pd.DataFrame:
    """
    Built-in ADX/ATR replacement.
    This avoids crashing when the ta package is missing.
    """
    df = df.copy().sort_values("time").reset_index(drop=True)

    adx_period = int(max(2, adx_period))
    atr_period = int(max(2, atr_period))

    tr = _true_range(df)
    atr = tr.rolling(atr_period, min_periods=1).mean()

    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = np.where(
        (up_move > down_move) & (up_move > 0),
        up_move,
        0.0,
    )

    minus_dm = np.where(
        (down_move > up_move) & (down_move > 0),
        down_move,
        0.0,
    )

    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    plus_di = (
        100
        * plus_dm.rolling(adx_period, min_periods=1).mean()
        / atr.replace(0, np.nan)
    )

    minus_di = (
        100
        * minus_dm.rolling(adx_period, min_periods=1).mean()
        / atr.replace(0, np.nan)
    )

    dx = (
        100
        * (plus_di - minus_di).abs()
        / (plus_di + minus_di).replace(0, np.nan)
    )

    adx = dx.rolling(adx_period, min_periods=1).mean()

    base = f"{prefix}_" if prefix else ""

    df[f"{base}adx"] = adx.replace([np.inf, -np.inf], np.nan).fillna(0)
    df[f"{base}plus_di"] = plus_di.replace([np.inf, -np.inf], np.nan).fillna(0)
    df[f"{base}minus_di"] = minus_di.replace([np.inf, -np.inf], np.nan).fillna(0)
    df[f"{base}atr"] = atr.replace([np.inf, -np.inf], np.nan).fillna(0)
    df[f"{base}pressure"] = df[f"{base}plus_di"] - df[f"{base}minus_di"]

    return df


def _merge_htf(
    base_df: pd.DataFrame,
    h1_df: pd.DataFrame,
    h4_df: pd.DataFrame,
    d1_df: pd.DataFrame,
) -> pd.DataFrame:
    base_df = base_df.copy().sort_values("time").reset_index(drop=True)

    for htf_df, prefix in [
        (h1_df, "h1"),
        (h4_df, "h4"),
        (d1_df, "d1"),
    ]:
        wanted = [f"{prefix}_adx", f"{prefix}_pressure"]

        if htf_df is None or htf_df.empty:
            for col in wanted:
                base_df[col] = 0
            continue

        temp = _normalize_ohlc(htf_df)
        temp = _add_indicators(temp, 16, 7, prefix=prefix)
        temp = temp[["time"] + wanted].sort_values("time").reset_index(drop=True)

        base_df = pd.merge_asof(
            base_df.sort_values("time"),
            temp,
            on="time",
            direction="backward",
        )

        for col in wanted:
            base_df[col] = base_df[col].ffill().fillna(0)

    return base_df.sort_values("time").reset_index(drop=True)


# =========================================================
# MT5 DATA LOADER
# =========================================================
@st.cache_data(ttl=300, show_spinner=False)
def _load_mt5_data(
    symbol: str,
    timeframe_name: str,
    bars: int,
) -> tuple[pd.DataFrame, str]:
    try:
        import MetaTrader5 as mt5
    except Exception as exc:
        return pd.DataFrame(), f"MetaTrader5 package is not installed: {exc}"

    symbol = _clean_symbol_for_mt5(symbol)

    try:
        if not mt5.initialize():
            mt5.shutdown()

            if not mt5.initialize():
                return (
                    pd.DataFrame(),
                    "MT5 initialize failed. Open your MT5 terminal and log in first.",
                )

        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M2": getattr(mt5, "TIMEFRAME_M2", mt5.TIMEFRAME_M1),
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
        }

        tf = tf_map.get(timeframe_name, mt5.TIMEFRAME_M1)

        selected = mt5.symbol_select(symbol, True)

        if not selected:
            return pd.DataFrame(), f"MT5 symbol not found or not selectable: {symbol}"

        rates = mt5.copy_rates_from_pos(symbol, tf, 0, int(bars))
        h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 3000)
        h4_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 1200)
        d1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 700)

        base = _normalize_ohlc(pd.DataFrame(rates))
        h1 = _normalize_ohlc(pd.DataFrame(h1_rates))
        h4 = _normalize_ohlc(pd.DataFrame(h4_rates))
        d1 = _normalize_ohlc(pd.DataFrame(d1_rates))

        if base.empty:
            return pd.DataFrame(), f"MT5 returned empty {timeframe_name} data for {symbol}."

        merged = _merge_htf(base, h1, h4, d1)

        return merged, ""

    except Exception as exc:
        return pd.DataFrame(), f"MT5 error: {exc}"


# =========================================================
# TWELVE DATA LOADER
# =========================================================
def _td_interval(timeframe_name: str) -> str:
    return {
        "M1": "1min",
        "M2": "1min",
        "M5": "5min",
        "M15": "15min",
        "H1": "1h",
        "H4": "4h",
        "D1": "1day",
    }.get(timeframe_name, "1min")


def _resample_to_m2(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    temp = df.copy().set_index("time").sort_index()

    out = pd.DataFrame()
    out["open"] = temp["open"].resample("2min").first()
    out["high"] = temp["high"].resample("2min").max()
    out["low"] = temp["low"].resample("2min").min()
    out["close"] = temp["close"].resample("2min").last()
    out["volume"] = temp["volume"].resample("2min").sum()

    out = out.dropna().reset_index()

    return out


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_twelve_interval(
    symbol: str,
    interval: str,
    outputsize: int,
    api_key: str,
) -> tuple[pd.DataFrame, str]:
    try:
        import requests
    except Exception as exc:
        return pd.DataFrame(), f"requests package is not installed: {exc}"

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": int(outputsize),
        "apikey": api_key,
        "format": "JSON",
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()

        payload = response.json()

        if payload.get("status") == "error":
            return pd.DataFrame(), payload.get(
                "message",
                "Twelve Data returned an error.",
            )

        values = payload.get("values", [])

        if not values:
            return pd.DataFrame(), "Twelve Data returned no candles."

        df = pd.DataFrame(values)
        df = _normalize_ohlc(df)

        return df, ""

    except Exception as exc:
        return pd.DataFrame(), f"Twelve Data error: {exc}"


@st.cache_data(ttl=300, show_spinner=False)
def _load_twelve_data(
    symbol: str,
    timeframe_name: str,
    bars: int,
    api_key: str,
) -> tuple[pd.DataFrame, str]:
    symbol = _clean_symbol_for_twelve(symbol)
    api_key = str(api_key or "").strip()

    if not api_key:
        return pd.DataFrame(), "Twelve Data API key is empty."

    base_interval = _td_interval(timeframe_name)

    base_fetch_size = int(bars) * 2 if timeframe_name == "M2" else int(bars)

    base, err = _fetch_twelve_interval(
        symbol,
        base_interval,
        min(base_fetch_size, 5000),
        api_key,
    )

    if err:
        return pd.DataFrame(), err

    if timeframe_name == "M2":
        base = _resample_to_m2(base).tail(int(bars)).reset_index(drop=True)

    h1, _ = _fetch_twelve_interval(symbol, "1h", 3000, api_key)
    h4, _ = _fetch_twelve_interval(symbol, "4h", 1200, api_key)
    d1, _ = _fetch_twelve_interval(symbol, "1day", 700, api_key)

    merged = _merge_htf(base, h1, h4, d1)

    return merged, ""


# =========================================================
# FEATURE ENGINEERING
# =========================================================
def _prepare_features(
    raw_df: pd.DataFrame,
    adx_period: int,
    atr_period: int,
    future_candles: int,
    ny_only: bool,
) -> tuple[pd.DataFrame, list[str]]:
    df = _normalize_ohlc(raw_df)

    for col in [
        "h1_adx",
        "h1_pressure",
        "h4_adx",
        "h4_pressure",
        "d1_adx",
        "d1_pressure",
    ]:
        if col in raw_df.columns:
            df[col] = pd.to_numeric(raw_df[col], errors="coerce").ffill().fillna(0)
        else:
            df[col] = 0

    df = _add_indicators(
        df,
        adx_period=adx_period,
        atr_period=atr_period,
        prefix="",
    )

    if ny_only:
        df["hour"] = df["time"].dt.hour
        df = df[(df["hour"] >= 15) & (df["hour"] <= 23)].copy()

    if len(df) < max(80, future_candles + 50):
        raise ValueError(
            "Not enough candles after filtering. Increase bars or turn off NY session only."
        )

    df["htf_score"] = (
        df["h1_pressure"].fillna(0) * 0.40
        + df["h4_pressure"].fillna(0) * 0.40
        + df["d1_pressure"].fillna(0) * 0.20
    )

    df["adx_slope"] = df["adx"].diff().fillna(0)
    df["atr_slope"] = df["atr"].diff().fillna(0)
    df["return"] = df["close"].pct_change().fillna(0)
    df["body"] = (df["close"] - df["open"]).abs()
    df["range"] = (df["high"] - df["low"]).replace(0, np.nan)

    df["wick_ratio"] = (
        (df["range"] - df["body"])
        / df["range"]
    ).replace([np.inf, -np.inf], np.nan).fillna(0)

    df["future_close"] = df["close"].shift(-int(future_candles))
    df["target"] = (df["future_close"] > df["close"]).astype(int)

    df = (
        df.replace([np.inf, -np.inf], np.nan)
        .ffill(limit=5)
        .fillna(0)
        .reset_index(drop=True)
    )

    features = [
        "adx",
        "plus_di",
        "minus_di",
        "atr",
        "pressure",
        "h1_adx",
        "h1_pressure",
        "htf_score",
        "h4_adx",
        "h4_pressure",
        "d1_adx",
        "d1_pressure",
        "adx_slope",
        "atr_slope",
        "return",
        "body",
        "wick_ratio",
    ]

    return df, features


# =========================================================
# ML MODEL
# =========================================================
@st.cache_resource(show_spinner=False)
def _train_rf_model(X: pd.DataFrame, y: pd.Series):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    split = int(len(X) * 0.80)

    if split < 50 or len(X) - split < 20:
        raise ValueError("Not enough rows for train/test split.")

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]
    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    if y_train.nunique() < 2:
        raise ValueError("Target has only one class. Need more history.")

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, pred)

    return model, float(accuracy)


def _build_ml(df: pd.DataFrame, features: list[str]):
    try:
        X = (
            df[features]
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
        )

        y = df["target"].fillna(0).astype(int)

        return _train_rf_model(X, y), ""

    except ModuleNotFoundError as exc:
        return None, f"Missing ML package: {exc.name}. Install scikit-learn."

    except Exception as exc:
        return None, str(exc)


# =========================================================
# DISPLAY HELPERS
# =========================================================
def _risk_label(
    value: float,
    good: float,
    danger: float,
    higher_is_better: bool = True,
) -> str:
    if higher_is_better:
        if value >= danger:
            return "VERY GOOD"
        if value >= good:
            return "GOOD"
        if value <= good * 0.5:
            return "DANGEROUS"
        return "BAD"

    if value <= good:
        return "VERY GOOD"
    if value <= danger:
        return "GOOD"
    if value >= danger * 1.5:
        return "DANGEROUS"

    return "BAD"


def _show_live_forecast(
    df: pd.DataFrame,
    features: list[str],
    model,
) -> None:
    latest = df.iloc[-1]

    st.markdown("## 🧠 Live AI Forecast")

    if model is None:
        st.warning("ML forecast is skipped because the model could not be trained.")
        return

    latest_x = pd.DataFrame(
        [latest[features].values],
        columns=features,
    ).replace([np.inf, -np.inf], np.nan).fillna(0)

    ai_pred = int(model.predict(latest_x)[0])

    if hasattr(model, "predict_proba"):
        prob = model.predict_proba(latest_x)[0]
    else:
        prob = [0.5, 0.5]

    direction = "BUY" if ai_pred == 1 else "SELL"
    confidence = float(max(prob) * 100)

    atr_avg = df["atr"].rolling(50, min_periods=1).mean().iloc[-1]
    atr_avg = atr_avg if pd.notna(atr_avg) and atr_avg > 0 else 1e-6

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Direction", direction)
    c2.metric("Confidence", f"{confidence:.2f}%")
    c3.metric(
        "ADX",
        f"{latest['adx']:.2f}",
        _risk_label(latest["adx"], 20, 35),
    )
    c4.metric(
        "ATR",
        f"{latest['atr']:.2f}",
        _risk_label(
            latest["atr"],
            atr_avg,
            atr_avg * 1.8,
            higher_is_better=False,
        ),
    )

    st.info(
        f"""
+DI: {latest['plus_di']:.2f}  
-DI: {latest['minus_di']:.2f}  
Pressure: {latest['pressure']:.2f}  
HTF Score: {latest['htf_score']:.2f}  
ADX Slope: {latest['adx_slope']:.4f}  
ATR Slope: {latest['atr_slope']:.4f}
"""
    )


def _show_crowd_psychology(df: pd.DataFrame) -> None:
    st.markdown("## 🧠 Crowd Psychology")

    latest = df.iloc[-1]

    atr_mean = df["atr"].rolling(50, min_periods=1).mean().iloc[-1]
    atr_mean = atr_mean if pd.notna(atr_mean) and atr_mean > 0 else 1e-6

    trend_aggression = min(float(latest["adx"]) / 50, 1)

    directional_control = min(
        abs(float(latest["plus_di"]) - float(latest["minus_di"])) / 30,
        1,
    )

    volatility_fear = min(float(latest["atr"]) / atr_mean, 2)

    candle_conviction = min(
        float(latest["body"]) / max(float(latest["range"]), 1e-6),
        1,
    )

    crowd_score = (
        trend_aggression * 30
        + directional_control * 30
        + volatility_fear * 20
        + candle_conviction * 20
    )

    crowd_score = max(0, min(crowd_score, 100))

    if crowd_score >= 80:
        crowd_state = "EUPHORIC TREND CROWD"
    elif crowd_score >= 60:
        crowd_state = "STRONG TREND PARTICIPATION"
    elif crowd_score >= 40:
        crowd_state = "BALANCED MARKET"
    elif crowd_score >= 25:
        crowd_state = "UNCERTAIN / HESITATION"
    else:
        crowd_state = "FEAR / LOW CONVICTION"

    contrarian_risk = 0

    if latest["adx"] > 40:
        contrarian_risk += 25

    if abs(latest["plus_di"] - latest["minus_di"]) > 25:
        contrarian_risk += 25

    if latest["atr_slope"] > 0:
        contrarian_risk += 20

    if crowd_score > 75:
        contrarian_risk += 30

    contrarian_risk = min(contrarian_risk, 100)

    c1, c2, c3 = st.columns(3)

    c1.metric("Crowd Score", f"{crowd_score:.2f}/100")
    c2.metric("Crowd State", crowd_state)
    c3.metric("Contrarian Risk", f"{contrarian_risk:.2f}%")


def _show_similar_daily_engine(
    df: pd.DataFrame,
    future_candles: int,
) -> pd.DataFrame:
    st.markdown("## 🧠 Professional Similar-Day Engine")

    work = df.copy()
    work["date"] = work["time"].dt.date

    daily = work.groupby("date").agg(
        adx=("adx", "mean"),
        atr=("atr", "mean"),
        pressure=("pressure", "mean"),
        h1_pressure=("h1_pressure", "mean"),
        h4_pressure=("h4_pressure", "mean"),
        d1_pressure=("d1_pressure", "mean"),
        close=("close", "last"),
    ).dropna()

    if len(daily) < 5:
        st.warning("Not enough different days for similar-day engine.")
        return pd.DataFrame()

    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics.pairwise import cosine_similarity
    except ModuleNotFoundError as exc:
        st.warning(f"Similar-day engine needs scikit-learn: {exc.name}")
        return pd.DataFrame()

    current_date = daily.index[-1]
    yesterday = current_date - timedelta(days=1)

    feature_cols = [
        "adx",
        "atr",
        "pressure",
        "h1_pressure",
        "h4_pressure",
        "d1_pressure",
    ]

    scaler = StandardScaler()
    scaled = scaler.fit_transform(daily[feature_cols])

    current_idx = list(daily.index).index(current_date)
    current_vec = scaled[current_idx].reshape(1, -1)

    sims = cosine_similarity(current_vec, scaled)[0]

    daily = daily.copy()
    daily["similarity"] = sims

    candidates = daily[
        (daily.index != current_date)
        & (daily.index != yesterday)
    ].copy()

    if candidates.empty:
        st.warning("No historical candidate days after excluding today and yesterday.")
        return pd.DataFrame()

    top_days = candidates.sort_values("similarity", ascending=False).head(10)

    rows = []

    for rank, date_idx in enumerate(top_days.index, start=1):
        day_rows = work[work["date"] == date_idx]

        if day_rows.empty:
            continue

        start_i = int(day_rows.index[0])
        future_i = min(start_i + int(future_candles), len(work) - 1)

        entry_price = float(work.iloc[start_i]["close"])
        future_price = float(work.iloc[future_i]["close"])

        if entry_price:
            future_move_pct = (future_price - entry_price) / entry_price * 100
        else:
            future_move_pct = 0

        rows.append(
            {
                "Rank": rank,
                "Date": str(date_idx),
                "Similarity %": round(float(top_days.loc[date_idx, "similarity"]) * 100, 2),
                "ADX": round(float(top_days.loc[date_idx, "adx"]), 2),
                "ATR": round(float(top_days.loc[date_idx, "atr"]), 3),
                "Pressure": round(float(top_days.loc[date_idx, "pressure"]), 2),
                "Future Move %": round(future_move_pct, 3),
                "Outcome": "BULLISH" if future_move_pct > 0 else "BEARISH",
            }
        )

    result = pd.DataFrame(rows)

    if not result.empty:
        st.dataframe(result, use_container_width=True, hide_index=True)

        bullish_count = int((result["Outcome"] == "BULLISH").sum())
        bearish_count = int((result["Outcome"] == "BEARISH").sum())

        regime_bias = (
            "BULLISH REGIME"
            if bullish_count > bearish_count
            else "BEARISH REGIME"
        )

        st.success(
            f"""
Current Market Regime: {regime_bias}  
Bullish Similar Days: {bullish_count}  
Bearish Similar Days: {bearish_count}
"""
        )

    return result


def _show_enhanced_regime_engine(
    df: pd.DataFrame,
    future_candles: int,
) -> pd.DataFrame:
    st.markdown("## 🧠 AI Enhanced Regime Intelligence")

    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA
        from sklearn.cluster import KMeans
        from sklearn.ensemble import IsolationForest
        from sklearn.metrics.pairwise import cosine_similarity
    except ModuleNotFoundError as exc:
        st.warning(f"Enhanced regime engine needs scikit-learn: {exc.name}")
        return pd.DataFrame()

    work = df.tail(10000).copy()

    if len(work) < 150:
        st.warning("Not enough data for enhanced regime engine.")
        return pd.DataFrame()

    atr_mean = work["atr"].rolling(50, min_periods=1).mean().replace(0, np.nan)

    work["volatility_regime"] = (
        work["atr"] / atr_mean
    ).replace([np.inf, -np.inf], np.nan).fillna(0)

    work["trend_power"] = work["adx"] * work["pressure"].abs()
    work["momentum_velocity"] = work["return"].rolling(5, min_periods=1).mean()

    work["range_expansion"] = (
        work["range"]
        / work["range"].rolling(20, min_periods=1).mean().replace(0, np.nan)
    ).replace([np.inf, -np.inf], np.nan).fillna(0)

    work["directional_conviction"] = (
        work["plus_di"] - work["minus_di"]
    ).abs()

    enhanced_features = [
        "adx",
        "plus_di",
        "minus_di",
        "atr",
        "pressure",
        "adx_slope",
        "atr_slope",
        "return",
        "body",
        "wick_ratio",
        "volatility_regime",
        "trend_power",
        "momentum_velocity",
        "range_expansion",
        "directional_conviction",
    ]

    work = (
        work.replace([np.inf, -np.inf], np.nan)
        .dropna(subset=enhanced_features)
        .copy()
    )

    if len(work) < 150:
        st.warning("Not enough clean rows for enhanced regime engine.")
        return pd.DataFrame()

    scaler = StandardScaler()
    scaled = scaler.fit_transform(work[enhanced_features])

    n_comp = min(6, len(enhanced_features), len(work))

    pca = PCA(n_components=n_comp, random_state=42)
    pca_features = pca.fit_transform(scaled)

    n_clusters = min(5, max(2, len(work) // 250))

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
    )

    work["cluster"] = kmeans.fit_predict(pca_features)

    iso = IsolationForest(
        contamination=0.03,
        random_state=42,
    )

    work["anomaly"] = iso.fit_predict(pca_features)

    latest_row = work.iloc[-1]

    future_gap = int(max(2, future_candles))

    if future_gap >= len(work) - 20:
        future_gap = max(2, len(work) // 5)

    history = work.iloc[:-future_gap].copy()
    clean_history = history[history["anomaly"] == 1].copy()

    if len(clean_history) < 10:
        clean_history = history.copy()

    if len(clean_history) < 10:
        st.warning("Not enough historical rows for enhanced regime matching.")
        return pd.DataFrame()

    clean_scaled = scaler.transform(clean_history[enhanced_features])
    clean_pca = pca.transform(clean_scaled)

    current_scaled = scaler.transform(
        pd.DataFrame(
            [latest_row[enhanced_features]],
            columns=enhanced_features,
        )
    )

    current_pca = pca.transform(current_scaled)

    similarities = cosine_similarity(current_pca, clean_pca)[0]

    clean_history["similarity"] = similarities

    top_matches = clean_history.sort_values(
        "similarity",
        ascending=False,
    ).head(10)

    rows = []
    bullish_prob = 0.0
    bearish_prob = 0.0
    move_abs = []

    for _, row in top_matches.iterrows():
        real_i = int(row.name)
        future_i = real_i + int(future_candles)

        if future_i >= len(df):
            continue

        entry = float(df.iloc[real_i]["close"])
        future = float(df.iloc[future_i]["close"])

        if entry:
            move_pct = (future - entry) / entry * 100
        else:
            move_pct = 0

        sim = float(row["similarity"])

        if move_pct > 0:
            outcome = "BULLISH CONTINUATION"
            bullish_prob += sim
        else:
            outcome = "BEARISH REVERSAL"
            bearish_prob += sim

        move_abs.append(abs(move_pct))

        rows.append(
            {
                "Date": row["time"],
                "Similarity %": round(sim * 100, 2),
                "Cluster": int(row["cluster"]),
                "ADX": round(float(row["adx"]), 2),
                "ATR": round(float(row["atr"]), 3),
                "Trend Power": round(float(row["trend_power"]), 2),
                "Volatility Regime": round(float(row["volatility_regime"]), 2),
                "Future Move %": round(float(move_pct), 3),
                "Outcome": outcome,
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        st.warning("No valid enhanced regime matches found.")
        return result

    st.dataframe(result, use_container_width=True, hide_index=True)

    total_prob = bullish_prob + bearish_prob

    if total_prob > 0:
        bullish_score = bullish_prob / total_prob * 100
        bearish_score = bearish_prob / total_prob * 100
    else:
        bullish_score = 50
        bearish_score = 50

    latest_ai = latest_row
    atr_avg = df["atr"].rolling(50, min_periods=1).mean().iloc[-1]

    if latest_ai["adx"] > 35 and latest_ai["atr_slope"] > 0:
        market_state = "HIGH MOMENTUM EXPANSION"
    elif latest_ai["adx"] > 25:
        market_state = "TRENDING ENVIRONMENT"
    elif latest_ai["atr"] > atr_avg:
        market_state = "VOLATILE TRANSITION"
    else:
        market_state = "RANGE / LOW ENERGY"

    dominant_side = "BULLISH" if bullish_score > bearish_score else "BEARISH"
    confidence_score = max(bullish_score, bearish_score)
    avg_continuation = float(np.mean(move_abs)) if move_abs else 0

    st.success(
        f"""
AI Market State: {market_state}  
Dominant Regime: {dominant_side}  
AI Confidence: {confidence_score:.2f}%  
Bullish Probability: {bullish_score:.2f}%  
Bearish Probability: {bearish_score:.2f}%  
Average Historical Future Move: {avg_continuation:.3f}%  
Matched Historical Regimes: {len(result)}
"""
    )

    return result


def _run_manual_backtest(
    df: pd.DataFrame,
    adx_threshold: int,
    future_candles: int,
    tp_mode: str,
) -> dict:
    signals = []

    tp_mult = 1.5 if tp_mode == "1:1.5" else 2.0
    max_i = len(df) - int(future_candles)

    rolling_atr = df["atr"].rolling(20, min_periods=1).mean()

    for i in range(50, max_i):
        row = df.iloc[i]
        prev = df.iloc[i - 1]

        adx_cross_up = (
            prev["adx"] <= adx_threshold
            and row["adx"] > adx_threshold
        )

        adx_retrace_buy = (
            prev["adx"] > adx_threshold
            and row["adx"] >= (adx_threshold - 3)
            and row["plus_di"] > row["minus_di"]
        )

        adx_retrace_sell = (
            prev["adx"] > adx_threshold
            and row["adx"] >= (adx_threshold - 3)
            and row["minus_di"] > row["plus_di"]
        )

        bull_candle = row["close"] > row["open"]
        bear_candle = row["close"] < row["open"]
        high_volatility = row["atr"] > rolling_atr.iloc[i]

        buy_signal = (
            (adx_cross_up or adx_retrace_buy)
            and row["plus_di"] > row["minus_di"]
            and (high_volatility or bull_candle)
        )

        sell_signal = (
            (adx_cross_up or adx_retrace_sell)
            and row["minus_di"] > row["plus_di"]
            and (high_volatility or bear_candle)
        )

        if buy_signal:
            entry = row["close"]
            tp = entry + row["atr"] * tp_mult
            future = df.iloc[i + int(future_candles)]["close"]

            signals.append("WIN" if future >= tp else "LOSS")

        elif sell_signal:
            entry = row["close"]
            tp = entry - row["atr"] * tp_mult
            future = df.iloc[i + int(future_candles)]["close"]

            signals.append("WIN" if future <= tp else "LOSS")

    total = len(signals)
    wins = signals.count("WIN")
    losses = signals.count("LOSS")

    winrate = wins / total * 100 if total > 0 else 0.0

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "winrate": winrate,
    }


def _show_backtest_result(result: dict) -> None:
    st.markdown("## 🚀 Last Backtest Result")

    if not result:
        st.warning("No backtest executed yet.")
        return

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Trades", result["total"])
    c2.metric("Wins", result["wins"])
    c3.metric("Losses", result["losses"])
    c4.metric("Win Rate", f"{result['winrate']:.2f}%")


def _show_feature_importance(model, features: list[str]) -> None:
    if model is None or not hasattr(model, "feature_importances_"):
        return

    st.markdown("## 📊 Feature Importance")

    importance = pd.DataFrame(
        {
            "Feature": features,
            "Importance": model.feature_importances_,
        }
    ).sort_values("Importance", ascending=False)

    st.dataframe(importance, use_container_width=True, hide_index=True)


def _show_charts(df: pd.DataFrame, symbol: str) -> None:
    st.markdown(f"## 📈 {symbol} Candle Chart")

    fig = go.Figure()

    tail = df.tail(300)

    fig.add_trace(
        go.Candlestick(
            x=tail["time"],
            open=tail["open"],
            high=tail["high"],
            low=tail["low"],
            close=tail["close"],
            name=symbol,
        )
    )

    fig.update_layout(
        height=650,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)


# =========================================================
# CONNECTION UI
# =========================================================
def _connection_ui() -> None:
    st.sidebar.markdown("## 🔌 Data Connection")

    default_td_key = _safe_secrets_get(
        "TWELVE_DATA_API_KEY",
        os.getenv("TWELVE_DATA_API_KEY", ""),
    )

    mt5_symbol = st.sidebar.text_input(
        "MT5 Symbol",
        value="XAUUSD",
        key="combined_mt5_symbol",
    )

    td_symbol = st.sidebar.text_input(
        "Twelve Data Symbol",
        value="XAU/USD",
        key="combined_td_symbol",
    )

    timeframe_name = st.sidebar.selectbox(
        "Base Timeframe",
        ["M1", "M2", "M5", "M15"],
        index=0,
        key="combined_base_timeframe",
    )

    bars = st.sidebar.slider(
        "Candles to load",
        min_value=500,
        max_value=30000,
        value=10000,
        step=500,
        key="combined_bars_to_load",
    )

    td_bars = min(int(bars), 5000)

    td_api_key = st.sidebar.text_input(
        "Twelve Data API Key",
        value=default_td_key,
        type="password",
        key="combined_td_api_key",
        help=(
            "Can also be stored as st.secrets['TWELVE_DATA_API_KEY'] "
            "or environment variable TWELVE_DATA_API_KEY."
        ),
    )

    col1, col2 = st.sidebar.columns(2)

    with col1:
        connect_mt5 = st.button(
            "🔌 Connect MT5",
            use_container_width=True,
            key="combined_connect_mt5",
        )

    with col2:
        connect_td = st.button(
            "🌐 Connect Twelve",
            use_container_width=True,
            key="combined_connect_td",
        )

    clear = st.sidebar.button(
        "🧹 Clear Data",
        use_container_width=True,
        key="combined_clear_data",
    )

    if clear:
        for key in [
            RAW_KEY,
            SOURCE_KEY,
            SYMBOL_KEY,
            LAST_LOAD_KEY,
            BT_RESULT_KEY,
            LAST_RUN_KEY,
        ]:
            st.session_state.pop(key, None)

        st.rerun()

    if connect_mt5:
        with st.spinner("Connecting to MT5 and loading candles..."):
            df, err = _load_mt5_data(
                mt5_symbol,
                timeframe_name,
                int(bars),
            )

        if err:
            st.sidebar.error(err)
        elif df.empty:
            st.sidebar.error("MT5 returned empty data.")
        else:
            st.session_state[RAW_KEY] = df
            st.session_state[SOURCE_KEY] = "MT5"
            st.session_state[SYMBOL_KEY] = _clean_symbol_for_mt5(mt5_symbol)
            st.session_state[LAST_LOAD_KEY] = pd.Timestamp.now()

            st.sidebar.success(f"MT5 connected: {len(df):,} candles")
            st.rerun()

    if connect_td:
        with st.spinner("Connecting to Twelve Data and loading candles..."):
            df, err = _load_twelve_data(
                td_symbol,
                timeframe_name,
                int(td_bars),
                td_api_key,
            )

        if err:
            st.sidebar.error(err)
        elif df.empty:
            st.sidebar.error("Twelve Data returned empty data.")
        else:
            st.session_state[RAW_KEY] = df
            st.session_state[SOURCE_KEY] = "Twelve Data"
            st.session_state[SYMBOL_KEY] = _clean_symbol_for_twelve(td_symbol)
            st.session_state[LAST_LOAD_KEY] = pd.Timestamp.now()

            st.sidebar.success(f"Twelve Data connected: {len(df):,} candles")
            st.rerun()
def _safe_save_backtest_result(row: dict) -> bool:
    try:
        from core.database import append_csv
        append_csv("backtest_results", row)
        return True
    except Exception as exc:
        st.warning(f"Could not save backtest result: {exc}")
        return False


def _safe_download_df(df: pd.DataFrame, label: str, filename: str):
    try:
        if df is not None and not df.empty:
            st.download_button(
                label,
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=filename,
                mime="text/csv",
                use_container_width=True,
            )
    except Exception as exc:
        st.warning(f"Download failed: {exc}")


def show():
    st.markdown("# 🤖 Combined AI Backtest + Regime Matcher — Upgraded")

    st.caption(
        "Safe upgraded version. It keeps your original MT5/Twelve connection, ML forecast, "
        "similar-day engine, regime matcher, and manual backtest logic."
    )

    if BT_RESULT_KEY not in st.session_state:
        st.session_state[BT_RESULT_KEY] = None

    if LAST_RUN_KEY not in st.session_state:
        st.session_state[LAST_RUN_KEY] = "Never"

    _connection_ui()

    st.sidebar.markdown("## ⚙️ Analysis Settings")

    adx_period = st.sidebar.slider(
        "ADX Period",
        min_value=5,
        max_value=50,
        value=20,
        step=1,
        key="combined_adx_period",
    )

    adx_threshold = st.sidebar.slider(
        "ADX Threshold",
        min_value=5,
        max_value=70,
        value=25,
        step=1,
        key="combined_adx_threshold",
    )

    atr_period = st.sidebar.slider(
        "ATR Period",
        min_value=5,
        max_value=50,
        value=14,
        step=1,
        key="combined_atr_period",
    )

    future_candles = st.sidebar.slider(
        "Prediction Horizon / Future Candles",
        min_value=1,
        max_value=240,
        value=120,
        step=1,
        key="combined_future_candles",
    )

    tp_mode = st.sidebar.selectbox(
        "TP Ratio",
        ["1:1.5", "1:2"],
        index=0,
        key="combined_tp_mode",
    )

    ny_only = st.sidebar.checkbox(
        "NY session only, server hour 15-23",
        value=True,
        key="combined_ny_only",
    )

    enable_autorefresh = st.sidebar.checkbox(
        "Auto refresh after connected",
        value=False,
        key="combined_enable_autorefresh",
    )

    if enable_autorefresh and RAW_KEY in st.session_state:
        st_autorefresh(
            interval=600000,
            key="combined_backtest_refresh",
        )

    raw_df = st.session_state.get(RAW_KEY)

    if raw_df is None or not isinstance(raw_df, pd.DataFrame) or raw_df.empty:
        st.info(
            "Choose your symbol/source in the sidebar, then click "
            "**Connect MT5** or **Connect Twelve Data**."
        )
        st.warning("No data loaded yet. This tab will not auto-connect before you click a connect button.")
        return

    source = st.session_state.get(SOURCE_KEY, "Unknown")
    symbol = st.session_state.get(SYMBOL_KEY, "Unknown")
    last_load = st.session_state.get(LAST_LOAD_KEY, "Unknown")

    st.success(
        f"Connected source: {source} | Symbol: {symbol} | "
        f"Raw candles: {len(raw_df):,} | Loaded: {last_load}"
    )

    try:
        df, features = _prepare_features(
            raw_df,
            adx_period=adx_period,
            atr_period=atr_period,
            future_candles=future_candles,
            ny_only=ny_only,
        )

        # Important upgrade:
        # Share prepared data with Mix / Engine / other tabs without deleting original data.
        st.session_state["last_df"] = df.copy()
        st.session_state["backtest_features"] = features

    except Exception as exc:
        st.error(f"Data preparation error: {exc}")
        with st.expander("Technical error"):
            st.code(traceback.format_exc())
        return

    st.markdown("## 📌 Data Snapshot")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prepared Candles", f"{len(df):,}")
    c2.metric("From", str(df["time"].iloc[0]))
    c3.metric("To", str(df["time"].iloc[-1]))
    c4.metric("Last Close", f"{df['close'].iloc[-1]:.3f}")

    _safe_download_df(df.tail(1000), "⬇️ Download Prepared Feature Data", "prepared_backtest_features.csv")

    ml_result, ml_err = _build_ml(df, features)

    model = None
    accuracy = 0.0

    if ml_result is not None:
        model, accuracy = ml_result
        st.success(f"ML Accuracy: {accuracy:.2%}")
    else:
        st.warning(f"ML model not available: {ml_err}")

    try:
        _show_live_forecast(df, features, model)
    except Exception as exc:
        st.warning(f"Live forecast skipped: {exc}")

    try:
        _show_crowd_psychology(df)
    except Exception as exc:
        st.warning(f"Crowd psychology skipped: {exc}")

    similar_df = pd.DataFrame()
    regime_df = pd.DataFrame()

    try:
        similar_df = _show_similar_daily_engine(df, future_candles)
    except Exception as exc:
        st.warning(f"Similar-day engine skipped: {exc}")

    try:
        regime_df = _show_enhanced_regime_engine(df, future_candles)
    except Exception as exc:
        st.warning(f"Enhanced regime engine skipped: {exc}")

    if similar_df is not None and not similar_df.empty:
        _safe_download_df(similar_df, "⬇️ Download Similar-Day Results", "similar_day_results.csv")

    if regime_df is not None and not regime_df.empty:
        _safe_download_df(regime_df, "⬇️ Download Regime Match Results", "regime_match_results.csv")

    st.markdown("## 🧪 Manual Backtest")

    run_bt = st.button(
        "🚀 RUN BACKTEST",
        key="combined_run_backtest",
        use_container_width=True,
    )

    if run_bt:
        result = _run_manual_backtest(
            df=df,
            adx_threshold=adx_threshold,
            future_candles=future_candles,
            tp_mode=tp_mode,
        )

        result["time"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        result["source"] = source
        result["symbol"] = symbol
        result["adx_period"] = adx_period
        result["adx_threshold"] = adx_threshold
        result["atr_period"] = atr_period
        result["future_candles"] = future_candles
        result["tp_mode"] = tp_mode
        result["ny_only"] = ny_only
        result["ml_accuracy"] = accuracy

        st.session_state[BT_RESULT_KEY] = result
        st.session_state[LAST_RUN_KEY] = pd.Timestamp.now()

        if _safe_save_backtest_result(result):
            st.success("Backtest result saved to backtest_results")

    _show_backtest_result(st.session_state.get(BT_RESULT_KEY))

    if st.session_state.get(LAST_RUN_KEY) != "Never":
        st.info(f"Last Backtest Run: {st.session_state.get(LAST_RUN_KEY)}")

    try:
        _show_feature_importance(model, features)
    except Exception as exc:
        st.warning(f"Feature importance skipped: {exc}")

    try:
        _show_charts(df, symbol)
    except Exception as exc:
        st.warning(f"Chart skipped: {exc}")

    st.markdown("## ✅ System Status")
    st.success(
        "Backtest tab is active. Prepared data is now also stored in "
        "`st.session_state['last_df']`, so your Mix tab can use the same data."
    )