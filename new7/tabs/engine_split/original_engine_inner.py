import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================================
# SAFE IMPORTS
# ==========================================================

try:
    from core.quant_models import add_indicators, quant_stack
except Exception:
    add_indicators = None
    quant_stack = None

try:
    from core.data_connectors import manual_connect
except Exception:
    manual_connect = None

try:
    from core.database import append_csv
except Exception:
    append_csv = None

try:
    from tabs.backtest import advanced_last120_similarity_engine as _backtest_similarity_engine
except Exception:
    _backtest_similarity_engine = None


# ==========================================================
# SAFE BASIC HELPERS
# ==========================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        value = float(value)
        if not np.isfinite(value):
            return default
        return value
    except Exception:
        return default


def _safe_round(value, digits=2, default=0.0):
    try:
        return round(_safe_float(value, default), digits)
    except Exception:
        return default


def _safe_session_get(key, default=None):
    try:
        return st.session_state.get(key, default)
    except Exception:
        return default


def _safe_append_csv(name, row):
    if append_csv is None:
        return False, "append_csv is unavailable."

    try:
        append_csv(name, row)
        return True, "Saved."
    except Exception as exc:
        return False, f"Save failed: {exc}"


def _normalize_ohlc(df):
    """
    Make sure the dashboard has safe time/open/high/low/close columns.
    """
    if df is None:
        return pd.DataFrame()

    try:
        work = df.copy()
    except Exception:
        return pd.DataFrame()

    if work.empty:
        return pd.DataFrame()

    rename_map = {}
    for col in work.columns:
        lc = str(col).lower().strip()

        if lc in ["datetime", "date", "timestamp"]:
            rename_map[col] = "time"
        elif lc == "o":
            rename_map[col] = "open"
        elif lc == "h":
            rename_map[col] = "high"
        elif lc == "l":
            rename_map[col] = "low"
        elif lc == "c":
            rename_map[col] = "close"

    if rename_map:
        work = work.rename(columns=rename_map)

    if "time" not in work.columns:
        if isinstance(work.index, pd.DatetimeIndex):
            work = work.reset_index().rename(columns={"index": "time"})
        else:
            work["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(work), freq="1min")

    work["time"] = pd.to_datetime(work["time"], errors="coerce")

    if "close" not in work.columns:
        return pd.DataFrame()

    work["close"] = pd.to_numeric(work["close"], errors="coerce").ffill().bfill()

    if "open" not in work.columns:
        work["open"] = work["close"].shift(1).fillna(work["close"])

    if "high" not in work.columns:
        work["high"] = work[["open", "close"]].max(axis=1)

    if "low" not in work.columns:
        work["low"] = work[["open", "close"]].min(axis=1)

    for col in ["open", "high", "low", "close"]:
        work[col] = pd.to_numeric(work[col], errors="coerce").ffill().bfill()

    work = work.dropna(subset=["time", "open", "high", "low", "close"]).reset_index(drop=True)

    return work


def _safe_add_indicators(df):
    """
    Run your original add_indicators if available.
    If it fails, keep OHLC and add fallback indicator columns.
    """
    work = _normalize_ohlc(df)

    if work.empty:
        return pd.DataFrame()

    if add_indicators is not None:
        try:
            dfi = add_indicators(work)
            dfi = _normalize_ohlc(dfi)

            if not dfi.empty:
                work = dfi
        except Exception:
            pass

    work = work.replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0)

    # Fallback indicators if your core indicator engine misses any column
    close = pd.to_numeric(work["close"], errors="coerce").ffill().bfill()
    high = pd.to_numeric(work["high"], errors="coerce").ffill().bfill()
    low = pd.to_numeric(work["low"], errors="coerce").ffill().bfill()

    if "atr" not in work.columns:
        tr = (high - low).abs()
        work["atr"] = tr.rolling(14, min_periods=1).mean()

    if "volatility" not in work.columns:
        work["volatility"] = close.pct_change().rolling(30, min_periods=1).std().fillna(0)

    if "adx" not in work.columns:
        candle_range = (high - low).abs()
        avg_range = candle_range.rolling(14, min_periods=1).mean()
        work["adx"] = np.clip((avg_range / close.abs().replace(0, np.nan) * 10000).fillna(0), 0, 60)

    if "plus_di" not in work.columns:
        work["plus_di"] = np.where(close.diff().fillna(0) > 0, 25, 10)

    if "minus_di" not in work.columns:
        work["minus_di"] = np.where(close.diff().fillna(0) < 0, 25, 10)

    if "pressure" not in work.columns:
        work["pressure"] = pd.to_numeric(work["plus_di"], errors="coerce").fillna(0) - pd.to_numeric(work["minus_di"], errors="coerce").fillna(0)

    if "mean_dist" not in work.columns:
        ma = close.rolling(50, min_periods=1).mean()
        atr = pd.to_numeric(work["atr"], errors="coerce").replace(0, np.nan).ffill().bfill().fillna(1)
        work["mean_dist"] = ((close - ma) / atr).fillna(0)

    if "fat_tail" not in work.columns:
        ret = close.pct_change().fillna(0)
        work["fat_tail"] = np.clip(ret.abs().rolling(30, min_periods=1).mean() * 10000, 0, 100)

    if "adx_slope" not in work.columns:
        work["adx_slope"] = pd.to_numeric(work["adx"], errors="coerce").diff().fillna(0)

    if "momentum" not in work.columns:
        work["momentum"] = close.diff(10).fillna(0)

    if "vol_decay" not in work.columns:
        vol = pd.to_numeric(work["volatility"], errors="coerce").fillna(0)
        work["vol_decay"] = vol.diff().fillna(0) * -1

    for col in work.columns:
        if col != "time":
            try:
                work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)
            except Exception:
                pass

    return work.reset_index(drop=True)


# ==========================================================
# SAFE QUANT STACK
# ==========================================================

def _fallback_quant_stack(dfi):
    """
    Backup decision engine if core.quant_stack crashes.
    This keeps the dashboard alive.
    """
    if dfi is None or dfi.empty:
        return {
            "bias": "WAIT",
            "scale10": 0,
            "safe_pct": 0,
            "adx": 0,
            "pressure": 0,
            "ml_conf_pct": 0,
            "history_match_pct": 0,
            "mean_revert_risk_pct": 100,
            "fat_tail_risk_pct": 100,
            "spoofing_risk_pct": 100,
            "ergodicity_pct": 0,
            "monte_carlo_pct": 0,
        }

    last = dfi.iloc[-1]

    adx = _safe_float(last.get("adx", 0))
    pressure = _safe_float(last.get("pressure", 0))
    mean_dist = abs(_safe_float(last.get("mean_dist", 0)))
    fat_tail = abs(_safe_float(last.get("fat_tail", 0)))
    volatility = abs(_safe_float(last.get("volatility", 0)))

    if pressure > 5 and adx >= 18:
        bias = "BUY"
    elif pressure < -5 and adx >= 18:
        bias = "SELL"
    else:
        bias = "WAIT"

    trend_score = np.clip(adx / 35 * 100, 0, 100)
    pressure_score = np.clip(abs(pressure) / 25 * 100, 0, 100)
    mean_risk = np.clip(mean_dist * 18, 0, 100)
    fat_risk = np.clip(fat_tail, 0, 100)
    spoof_risk = np.clip(max(0, fat_risk - pressure_score * 0.25), 0, 100)

    safe_pct = (
        trend_score * 0.30
        + pressure_score * 0.30
        + (100 - mean_risk) * 0.20
        + (100 - fat_risk) * 0.10
        + (100 - spoof_risk) * 0.10
    )

    safe_pct = float(np.clip(safe_pct, 0, 100))

    return {
        "bias": bias,
        "scale10": round(safe_pct / 10, 2),
        "safe_pct": round(safe_pct, 2),
        "adx": round(adx, 2),
        "pressure": round(pressure, 2),
        "ml_conf_pct": round(np.clip((trend_score + pressure_score) / 2, 0, 100), 2),
        "history_match_pct": round(np.clip(safe_pct * 0.85, 0, 100), 2),
        "mean_revert_risk_pct": round(mean_risk, 2),
        "fat_tail_risk_pct": round(fat_risk, 2),
        "spoofing_risk_pct": round(spoof_risk, 2),
        "ergodicity_pct": round(np.clip(100 - volatility * 10000, 0, 100), 2),
        "monte_carlo_pct": round(np.clip(safe_pct * 0.90, 0, 100), 2),
    }


def _safe_quant_stack(df, dfi):
    if quant_stack is not None:
        try:
            q = quant_stack(
                df,
                _safe_session_get("trade_history", []),
                _safe_session_get("account_snapshot", {}),
            )

            if isinstance(q, dict):
                fallback = _fallback_quant_stack(dfi)
                fallback.update(q)

                # Make sure important keys always exist
                for key, value in _fallback_quant_stack(dfi).items():
                    fallback.setdefault(key, value)

                return fallback
        except Exception:
            pass

    return _fallback_quant_stack(dfi)


# ==========================================================
# THRESHOLD / STATUS HELPERS
# ==========================================================

def _status_for_metric(name, value, bias=None):
    try:
        v = float(value)
    except Exception:
        return "UNKNOWN", "Need more data"

    n = str(name).lower()

    if "safety" in n or "safe" in n:
        if v >= 75:
            return "VERY GOOD", "High safety; still wait for entry rules"
        if v >= 58:
            return "GOOD", "Acceptable, use normal risk"
        if v >= 42:
            return "BAD", "Weak edge; reduce size or wait"
        return "DANGEROUS", "Low safety; avoid forcing trade"

    if n == "adx":
        if v >= 55:
            return "DANGEROUS", "Very strong/exhausted trend risk"
        if v >= 28:
            return "VERY GOOD", "Strong trend regime"
        if v >= 18:
            return "GOOD", "Trend building"
        return "BAD", "Weak/sideways regime"

    if "pressure" in n:
        av = abs(v)
        if av >= 28:
            return "DANGEROUS", "Extreme pressure; reversal/wick risk"
        if av >= 14:
            return "VERY GOOD", "Clear directional pressure"
        if av >= 6:
            return "GOOD", "Moderate pressure"
        return "BAD", "No clear pressure"

    if "mean" in n or "revert" in n:
        if v <= 30:
            return "VERY GOOD", "Low mean-reversion danger"
        if v <= 50:
            return "GOOD", "Manageable pullback risk"
        if v <= 70:
            return "BAD", "Pullback risk rising"
        return "DANGEROUS", "High snap-back/reversal risk"

    if "fat" in n:
        if v <= 25:
            return "VERY GOOD", "Normal tail risk"
        if v <= 45:
            return "GOOD", "Some tail risk"
        if v <= 65:
            return "BAD", "Wick/news risk rising"
        return "DANGEROUS", "Extreme tail/wick risk"

    if "spoof" in n:
        if v <= 20:
            return "VERY GOOD", "Clean pressure"
        if v <= 40:
            return "GOOD", "Acceptable noise"
        if v <= 65:
            return "BAD", "Possible fake pressure"
        return "DANGEROUS", "High fake-move risk"

    if "ergodicity" in n:
        if v >= 70:
            return "VERY GOOD", "Stable regime quality"
        if v >= 50:
            return "GOOD", "Acceptable regime quality"
        if v >= 35:
            return "BAD", "Unstable regime"
        return "DANGEROUS", "Very unstable regime"

    if "monte" in n or "ml" in n or "history" in n:
        if v >= 75:
            return "VERY GOOD", "Strong model agreement"
        if v >= 58:
            return "GOOD", "Acceptable model agreement"
        if v >= 42:
            return "BAD", "Weak model agreement"
        return "DANGEROUS", "Low model agreement"

    if "atr" in n or "volatility" in n:
        if v <= 0:
            return "UNKNOWN", "No volatility value"
        return "GOOD", "Use with symbol-specific context"

    return "GOOD", "Normal"


def _metric_with_status(col, label, value, status=None, note=None):
    if status is None or note is None:
        status, note = _status_for_metric(label, value)

    col.metric(label, value)
    col.caption(f"{status}: {note}")


def _threshold_table(q):
    rows = []

    checks = [
        ("Safety %", q.get("safe_pct", 0)),
        ("ADX", q.get("adx", 0)),
        ("Pressure", q.get("pressure", 0)),
        ("Mean Revert Risk %", q.get("mean_revert_risk_pct", 0)),
        ("Fat Tail Risk %", q.get("fat_tail_risk_pct", 0)),
        ("Spoofing Risk %", q.get("spoofing_risk_pct", 0)),
        ("Ergodicity %", q.get("ergodicity_pct", 0)),
        ("Monte Carlo %", q.get("monte_carlo_pct", 0)),
        ("ML Confidence %", q.get("ml_conf_pct", 0)),
        ("History Match %", q.get("history_match_pct", 0)),
    ]

    for metric, value in checks:
        status, note = _status_for_metric(metric, value, q.get("bias"))

        rows.append({
            "Data": metric,
            "Value": value,
            "Threshold": status,
            "Meaning": note,
        })

    return pd.DataFrame(rows)


def _compact_latest_data(dfi):
    if dfi is None or dfi.empty:
        return pd.DataFrame()

    cols = [
        "time",
        "open",
        "high",
        "low",
        "close",
        "adx",
        "plus_di",
        "minus_di",
        "pressure",
        "atr",
        "volatility",
        "mean_dist",
        "fat_tail",
        "adx_slope",
        "momentum",
    ]

    use = [c for c in cols if c in dfi.columns]

    if not use:
        return pd.DataFrame()

    out = dfi[use].tail(80).copy()

    for c in out.columns:
        if c != "time":
            out[c] = pd.to_numeric(out[c], errors="coerce").round(5)

    return out


# ==========================================================
# SAFE CONNECT
# ==========================================================

def _safe_manual_connect(source, symbol, api_key, bars, timeframe):
    if manual_connect is None:
        st.error("manual_connect is unavailable. Check core.data_connectors import.")
        return

    try:
        with st.spinner(f"Connecting {source.upper()} {symbol} {timeframe}..."):
            manual_connect(
                source,
                symbol,
                api_key,
                bars=bars,
                timeframe=timeframe,
            )

        st.success(f"Connected {source.upper()} {symbol} {timeframe}.")
        st.rerun()

    except Exception as exc:
        st.error(f"{source.upper()} connection failed: {exc}")




# ==========================================================
# 2026 ENGINE UPGRADE: QUALITY / REGIME / EXIT HELPERS
# ==========================================================

def _pct(x, digits=2):
    try:
        return round(float(x) * 100, digits)
    except Exception:
        return 0.0


def _latest_quality_report(dfi):
    if dfi is None or dfi.empty:
        return {"quality_pct": 0, "status": "NO DATA", "note": "No dataframe available."}
    needed = ["time", "open", "high", "low", "close"]
    missing = [c for c in needed if c not in dfi.columns]
    nan_pct = float(dfi[needed].isna().mean().mean() * 100) if not missing else 100.0
    duplicate_times = int(dfi["time"].duplicated().sum()) if "time" in dfi.columns else 0
    rows = len(dfi)
    row_score = min(100, rows / 500 * 100)
    missing_penalty = len(missing) * 18
    nan_penalty = min(45, nan_pct * 2)
    dup_penalty = min(20, duplicate_times / max(rows, 1) * 100)
    quality = float(np.clip(row_score - missing_penalty - nan_penalty - dup_penalty, 0, 100))
    if quality >= 80:
        status = "GOOD"
        note = "Data is strong enough for engine decisions."
    elif quality >= 55:
        status = "USABLE"
        note = "Usable, but more candles improve confidence."
    else:
        status = "WEAK"
        note = "Decision confidence should be reduced."
    return {
        "quality_pct": round(quality, 1),
        "status": status,
        "note": note,
        "rows": rows,
        "missing": missing,
        "nan_pct": round(nan_pct, 2),
        "duplicate_times": duplicate_times,
    }


def _directional_efficiency_window(dfi, window=60):
    try:
        close = pd.to_numeric(dfi["close"], errors="coerce").ffill().bfill()
        if len(close) < max(5, window):
            return 0.0
        path = close.diff().abs().tail(window).sum()
        net = abs(close.iloc[-1] - close.iloc[-window])
        return float(np.clip(net / max(path, 1e-12), 0, 1))
    except Exception:
        return 0.0


def _engine_regime_matrix(dfi):
    if dfi is None or dfi.empty:
        return {"regime": "WAIT", "direction": "WAIT", "score": 0, "exit_buy_risk": 50, "exit_sell_risk": 50}
    last = dfi.iloc[-1]
    adx = _safe_float(last.get("adx", 0))
    pressure = _safe_float(last.get("pressure", 0))
    adx_slope = _safe_float(last.get("adx_slope", 0))
    eff30 = _directional_efficiency_window(dfi, 30)
    eff120 = _directional_efficiency_window(dfi, 120)
    fat = abs(_safe_float(last.get("fat_tail", 0)))
    wick = abs(_safe_float(last.get("wick_ratio", 0)))
    range_exp = abs(_safe_float(last.get("range_expansion", 1)))
    direction = "BUY" if pressure > 5 else "SELL" if pressure < -5 else "WAIT"
    trend_score = np.clip((adx / 35 * 35) + (abs(pressure) / 30 * 25) + (eff30 * 25) + (max(adx_slope, 0) * 8), 0, 100)
    exhaustion = np.clip((max(adx - 45, 0) * 2.0) + (fat * 4.0) + (wick * 25.0) + (max(range_exp - 1.6, 0) * 18.0) + (eff120 * 10), 0, 100)
    if trend_score >= 70 and exhaustion < 55:
        regime = "ONE-WAY CONTINUATION"
    elif trend_score >= 55 and adx_slope > 0:
        regime = "ONE-WAY STARTING"
    elif exhaustion >= 70:
        regime = "LIMIT / EXHAUSTION RISK"
    elif adx < 18 and abs(pressure) < 8:
        regime = "RANGE / WAIT"
    else:
        regime = "MIXED / CONFIRM"
    # Exit-risk means: danger of closing that side now and leaving the opposite basket exposed.
    exit_buy_risk = 50
    exit_sell_risk = 50
    if direction == "BUY":
        exit_buy_risk = np.clip(70 + trend_score * 0.25 - exhaustion * 0.15, 0, 100)
        exit_sell_risk = np.clip(35 + exhaustion * 0.25 - trend_score * 0.10, 0, 100)
    elif direction == "SELL":
        exit_sell_risk = np.clip(70 + trend_score * 0.25 - exhaustion * 0.15, 0, 100)
        exit_buy_risk = np.clip(35 + exhaustion * 0.25 - trend_score * 0.10, 0, 100)
    return {
        "regime": regime,
        "direction": direction,
        "trend_score": round(float(trend_score), 1),
        "exhaustion_score": round(float(exhaustion), 1),
        "eff30_pct": round(eff30 * 100, 1),
        "eff120_pct": round(eff120 * 100, 1),
        "exit_buy_risk": round(float(exit_buy_risk), 1),
        "exit_sell_risk": round(float(exit_sell_risk), 1),
    }


def _render_engine_command_center(dfi, q):
    st.markdown("### 🧭 Engine Command Center")
    quality = _latest_quality_report(dfi)
    regime = _engine_regime_matrix(dfi)
    c = st.columns(6)
    c[0].metric("Data Quality %", quality.get("quality_pct", 0))
    c[0].caption(f"{quality.get('status')}: {quality.get('note')}")
    c[1].metric("Regime", regime.get("regime", "WAIT"))
    c[1].caption("Start / continue / exhaustion classification")
    c[2].metric("Dominant Direction", regime.get("direction", "WAIT"))
    c[2].caption("Based on DI pressure + efficiency")
    c[3].metric("Trend Score", regime.get("trend_score", 0))
    c[3].caption("70+ = strong one-way continuation")
    c[4].metric("Exhaustion Score", regime.get("exhaustion_score", 0))
    c[4].caption("70+ = limit / reversal danger")
    c[5].metric("Engine Bias", q.get("bias", "WAIT"))
    c[5].caption(f"Safety {q.get('safe_pct', 0)}%")
    r = st.columns(4)
    r[0].metric("DVE 30 candles %", regime.get("eff30_pct", 0))
    r[0].caption("60+ = clean one-way movement")
    r[1].metric("DVE 120 candles %", regime.get("eff120_pct", 0))
    r[1].caption("High + high ADX can become exhaustion")
    r[2].metric("Exit BUY Danger %", regime.get("exit_buy_risk", 0))
    r[2].caption("High = risky to close BUY basket now")
    r[3].metric("Exit SELL Danger %", regime.get("exit_sell_risk", 0))
    r[3].caption("High = risky to close SELL basket now")
    if quality.get("quality_pct", 0) < 55:
        st.warning("Data quality is weak. Do not rely on a single Engine signal until more candles load.")
    if regime.get("exhaustion_score", 0) >= 70:
        st.error("Exhaustion risk is high. Avoid aggressive one-side exit unless account survivability is confirmed.")
    elif regime.get("trend_score", 0) >= 70:
        st.success("Trend continuation is strong. Avoid closing the winning-side hedge too early without confirming the opposite exposure risk.")


def _render_multiframe_snapshot(dfi):
    st.markdown("### 🧩 Multi-Window Confirmation")
    if dfi is None or dfi.empty:
        st.info("No data for multi-window confirmation.")
        return
    rows = []
    for w in [30, 60, 120, 300, 600]:
        if len(dfi) < max(10, w):
            continue
        sub = dfi.tail(w)
        last = sub.iloc[-1]
        move_pct = (float(sub["close"].iloc[-1]) / max(float(sub["close"].iloc[0]), 1e-12) - 1) * 100
        pressure = _safe_float(last.get("pressure", 0))
        adx = _safe_float(last.get("adx", 0))
        eff = _directional_efficiency_window(dfi, w)
        bias = "BUY" if move_pct > 0 and pressure > 0 else "SELL" if move_pct < 0 and pressure < 0 else "MIXED"
        rows.append({
            "Window candles": w,
            "Move %": round(move_pct, 4),
            "ADX": round(adx, 2),
            "Pressure": round(pressure, 2),
            "DVE %": round(eff * 100, 1),
            "Bias": bias,
            "Meaning": "strong" if eff >= 0.60 and adx >= 25 else "building" if eff >= 0.35 else "mixed/chop",
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Need more rows for multi-window confirmation.")

# ==========================================================
# SAFE SIMILARITY ENGINE WRAPPER
# ==========================================================

def _fallback_similarity_engine(df, horizon=120, lookback_days=100, window=120, step=10, max_rank=25):
    """Real built-in fallback scanner.
    It does not require tabs.backtest, so Engine stays useful even after Backtest is removed.
    """
    dfi = _safe_add_indicators(df)
    if dfi is None or dfi.empty or len(dfi) < window + horizon + 30:
        summary = {
            "Status": f"Need at least {window + horizon + 30} candles for built-in similarity scan.",
            "Dominant Similar Bias": "WAIT",
            "Bullish Similar %": 0.0,
            "Bearish Similar %": 0.0,
            "Sideways Similar %": 100.0,
            "Safe Similarity Score /10": 0.0,
            "Top Similarity %": 0.0,
            "Days Ranked": 0,
            "Windows Scanned": 0,
            "Search Rule": "Built-in Engine scanner; no Backtest import required.",
        }
        return pd.DataFrame(), summary

    work = dfi.copy().reset_index(drop=True)
    if "time" in work.columns:
        work["time"] = pd.to_datetime(work["time"], errors="coerce")
        latest_day = work["time"].dropna().dt.date.max() if work["time"].notna().any() else None
        if latest_day is not None:
            cutoff_day = latest_day - pd.Timedelta(days=2).date() if False else None
    feats = ["ret", "adx", "pressure", "atr", "volatility", "directional_efficiency", "range_expansion"]
    for f in feats:
        if f not in work.columns:
            work[f] = 0.0
        work[f] = pd.to_numeric(work[f], errors="coerce").replace([np.inf, -np.inf], 0).fillna(0)
    latest = work[feats].tail(window).copy()
    latest_vec = latest.to_numpy(dtype=float).reshape(-1)
    latest_std = latest_vec.std() or 1.0
    latest_vec = (latest_vec - latest_vec.mean()) / latest_std
    rows = []
    scans = 0
    max_i = len(work) - window - horizon
    latest_date = None
    if "time" in work.columns and work["time"].notna().any():
        latest_date = work["time"].dropna().dt.date.max()
    start_i = 0
    if "time" in work.columns and work["time"].notna().any() and lookback_days:
        min_time = work["time"].max() - pd.Timedelta(days=int(lookback_days) + 2)
        candidates = work.index[work["time"] >= min_time]
        if len(candidates):
            start_i = max(0, int(candidates[0]) - window - horizon)
    for i in range(start_i, max_i, max(1, int(step))):
        end = i + window
        fut_end = end + horizon
        if fut_end >= len(work):
            break
        if latest_date is not None and "time" in work.columns:
            day = work["time"].iloc[end-1].date() if pd.notna(work["time"].iloc[end-1]) else None
            if day is not None and (latest_date - day).days < 2:
                continue
        seg = work[feats].iloc[i:end].to_numpy(dtype=float).reshape(-1)
        if len(seg) != len(latest_vec):
            continue
        seg_std = seg.std() or 1.0
        seg = (seg - seg.mean()) / seg_std
        denom = (np.linalg.norm(latest_vec) * np.linalg.norm(seg)) or 1.0
        sim = float(np.dot(latest_vec, seg) / denom)
        sim_pct = round((sim + 1) / 2 * 100, 2)
        start_price = float(work["close"].iloc[end-1])
        future_price = float(work["close"].iloc[fut_end])
        future_move = (future_price / max(start_price, 1e-12) - 1) * 100
        outcome = "BUY" if future_move > 0.03 else "SELL" if future_move < -0.03 else "SIDEWAYS"
        eff = _directional_efficiency_window(work.iloc[:end], min(window, 120))
        score = np.clip(sim_pct * 0.70 + eff * 100 * 0.20 + min(abs(future_move) * 8, 10), 0, 100)
        rows.append({
            "Rank": 0,
            "End Time": work["time"].iloc[end-1] if "time" in work.columns else end,
            "Similarity %": sim_pct,
            "Efficiency Score": round(float(score), 2),
            "ADX": round(_safe_float(work["adx"].iloc[end-1]), 2),
            "Pressure": round(_safe_float(work["pressure"].iloc[end-1]), 2),
            "Future Move %": round(float(future_move), 4),
            "Outcome": outcome,
        })
        scans += 1
    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(), {
            "Status": "No eligible older windows found. Need more historical candles.",
            "Dominant Similar Bias": "WAIT",
            "Bullish Similar %": 0.0,
            "Bearish Similar %": 0.0,
            "Sideways Similar %": 100.0,
            "Safe Similarity Score /10": 0.0,
            "Top Similarity %": 0.0,
            "Days Ranked": 0,
            "Windows Scanned": scans,
            "Search Rule": "Built-in Engine scanner excludes today and yesterday when timestamps exist.",
        }
    out = out.sort_values(["Efficiency Score", "Similarity %"], ascending=False).head(max_rank).reset_index(drop=True)
    out["Rank"] = np.arange(1, len(out) + 1)
    bullish = float((out["Outcome"] == "BUY").mean() * 100)
    bearish = float((out["Outcome"] == "SELL").mean() * 100)
    sideways = max(0.0, 100.0 - bullish - bearish)
    dom = "BUY" if bullish > bearish and bullish >= 45 else "SELL" if bearish > bullish and bearish >= 45 else "WAIT"
    safe10 = float(np.clip(out["Efficiency Score"].head(10).mean() / 10, 0, 10))
    summary = {
        "Status": "OK - built-in Engine scanner used.",
        "Dominant Similar Bias": dom,
        "Bullish Similar %": round(bullish, 1),
        "Bearish Similar %": round(bearish, 1),
        "Sideways Similar %": round(sideways, 1),
        "Safe Similarity Score /10": round(safe10, 2),
        "Top Similarity %": round(float(out["Similarity %"].max()), 2),
        "Days Ranked": int(len(out)),
        "Windows Scanned": int(scans),
        "Search Rule": "Built-in Engine scanner; excludes today and yesterday when timestamps exist; ranks similarity + DVE + future move context.",
    }
    return out, summary


def _safe_similarity_engine(df, horizon=120, lookback_days=100, window=120, step=10, max_rank=25):
    engine = _backtest_similarity_engine

    if engine is None:
        return _fallback_similarity_engine(
            df,
            horizon=horizon,
            lookback_days=lookback_days,
            window=window,
            step=step,
            max_rank=max_rank,
        )

    try:
        sim_df, summary = engine(
            df,
            horizon=horizon,
            lookback_days=lookback_days,
            window=window,
            step=step,
            max_rank=max_rank,
        )

        if summary is None:
            summary = {}

        if sim_df is None:
            sim_df = pd.DataFrame()

        summary.setdefault("Status", "OK" if not sim_df.empty else "Need more data.")
        summary.setdefault("Dominant Similar Bias", "WAIT")
        summary.setdefault("Bullish Similar %", 0.0)
        summary.setdefault("Bearish Similar %", 0.0)
        summary.setdefault("Sideways Similar %", 0.0)
        summary.setdefault("Safe Similarity Score /10", 0.0)
        summary.setdefault("Top Similarity %", 0.0)
        summary.setdefault("Search Rule", "Uses older data only; excludes today and yesterday when timestamps exist.")

        return sim_df, summary

    except Exception as exc:
        summary = {
            "Status": f"Similarity engine crashed: {exc}",
            "Dominant Similar Bias": "WAIT",
            "Bullish Similar %": 0.0,
            "Bearish Similar %": 0.0,
            "Sideways Similar %": 100.0,
            "Safe Similarity Score /10": 0.0,
            "Top Similarity %": 0.0,
            "Days Ranked": 0,
            "Windows Scanned": 0,
            "Search Rule": "Similarity engine failed safely.",
        }

        return pd.DataFrame(), summary


# ==========================================================
# CHART
# ==========================================================

def _show_candlestick_chart(dfi):
    if dfi is None or dfi.empty:
        st.info("No chart data available.")
        return

    needed = ["time", "open", "high", "low", "close"]

    missing = [c for c in needed if c not in dfi.columns]

    if missing:
        st.warning(f"Chart missing columns: {missing}")
        return

    chart_df = dfi.tail(180).copy()

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=chart_df["time"],
                open=chart_df["open"],
                high=chart_df["high"],
                low=chart_df["low"],
                close=chart_df["close"],
                name="Price",
            )
        ]
    )

    fig.update_layout(
        height=390,
        xaxis_rangeslider_visible=False,
        margin=dict(l=5, r=5, t=10, b=5),
    )

    st.plotly_chart(fig, use_container_width=True)


# ==========================================================
# SNAPSHOT SAVE CONTROL
# ==========================================================

def _save_engine_snapshot_once(q, symbol):
    """
    Prevent saving duplicate rows on every Streamlit rerun.
    Saves at most once every 60 seconds unless user presses manual save.
    """
    now = pd.Timestamp.now()
    last_save = _safe_session_get("engine_last_auto_save_time")

    should_save = False

    if last_save is None:
        should_save = True
    else:
        try:
            elapsed = (now - pd.to_datetime(last_save)).total_seconds()
            should_save = elapsed >= 60
        except Exception:
            should_save = True

    if should_save:
        row = {
            "time": now,
            "symbol": symbol,
            **q,
        }

        ok, msg = _safe_append_csv("engine_mix_snapshots", row)

        if ok:
            st.session_state.engine_last_auto_save_time = now

        return ok, msg

    return True, "Skipped duplicate auto-save."


# ==========================================================
# MAIN STREAMLIT TAB
# ==========================================================

def show():
    st.markdown("# ⚡ Engine — One Efficient Decision Dashboard")
    st.caption("Fast decision mode: core metrics show first; heavy tables, chart, similarity scan, and debug output stay under open/close fields.")

    with st.expander("⚙️ Optional Engine symbol + old connector buttons", expanded=False):
        engine_symbol = st.text_input("Symbol", value=_safe_session_get("symbol", "XAUUSD"), key="engine_symbol")
        engine_symbol = str(engine_symbol or "XAUUSD").upper().strip()
        st.session_state.symbol = engine_symbol
        api_key = _safe_session_get("twelve_api_key", "")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("Connect MT5 M1", use_container_width=True, key="engine_mt5"):
                _safe_manual_connect("mt5", st.session_state.symbol, api_key, bars=5000, timeframe="M1")
        with c2:
            if st.button("Connect MT5 M2", use_container_width=True, key="engine_mt5_m2"):
                _safe_manual_connect("mt5", st.session_state.symbol, api_key, bars=80000, timeframe="M2")
        with c3:
            if st.button("Connect Twelve", use_container_width=True, key="engine_twelve"):
                _safe_manual_connect("twelve", st.session_state.symbol, api_key, bars=5000, timeframe="M1")
        with c4:
            if st.button("Connect Fallback", use_container_width=True, key="engine_fallback"):
                _safe_manual_connect("fallback", st.session_state.symbol, api_key, bars=5000, timeframe="M1")

    df = _safe_session_get("last_df")
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("No shared live data yet. Connect Twelve/MT5 from the sidebar, then this Engine tab will open automatically with the same data.")
        return

    dfi = _safe_add_indicators(df)
    if dfi.empty:
        st.error("Data loaded, but indicators could not be calculated yet.")
        with st.expander("Debug raw data"):
            try:
                st.write(df)
            except Exception:
                st.write("Could not display raw data.")
        return

    q = _safe_quant_stack(df, dfi)
    _render_engine_command_center(dfi, q)
    with st.expander("🧩 Open Multi-Window Confirmation table", expanded=False):
        _render_multiframe_snapshot(dfi)

    section = st.radio(
        "Open Engine decision section",
        ["🎯 Decision + Thresholds", "🧠 Similar Regime", "📈 Chart + Compact Data", "💾 Save / Debug"],
        horizontal=True,
        key="engine_decision_lazy_section",
    )

    if section == "🎯 Decision + Thresholds":
        row1 = st.columns(5)
        bias = q.get("bias", "WAIT")
        bias_status = "GOOD" if bias in ["BUY", "SELL"] else "BAD"
        bias_note = "Directional output; confirm with thresholds" if bias in ["BUY", "SELL"] else "No strong direction yet"
        _metric_with_status(row1[0], "Priority Bias", bias, bias_status, bias_note)
        safety_status, safety_note = _status_for_metric("Safety %", q.get("safe_pct", 0))
        _metric_with_status(row1[1], "Safety /10", q.get("scale10", 0), safety_status, safety_note)
        _metric_with_status(row1[2], "Safety %", q.get("safe_pct", 0))
        _metric_with_status(row1[3], "ADX", q.get("adx", 0))
        _metric_with_status(row1[4], "Pressure", q.get("pressure", 0))
        row2 = st.columns(5)
        _metric_with_status(row2[0], "ML Confidence %", q.get("ml_conf_pct", 0))
        _metric_with_status(row2[1], "History Match %", q.get("history_match_pct", 0))
        _metric_with_status(row2[2], "Mean Revert Risk %", q.get("mean_revert_risk_pct", 0))
        _metric_with_status(row2[3], "Fat Tail Risk %", q.get("fat_tail_risk_pct", 0))
        _metric_with_status(row2[4], "Spoofing Risk %", q.get("spoofing_risk_pct", 0))
        with st.expander("📋 Open Threshold Table", expanded=False):
            st.dataframe(_threshold_table(q), use_container_width=True, hide_index=True)
        auto_save = st.checkbox("Auto-save engine snapshot safely every 60 seconds", value=True, key="engine_auto_save_snapshot")
        if auto_save:
            _save_engine_snapshot_once(q, st.session_state.symbol)
        return

    if section == "🧠 Similar Regime":
        st.markdown("### Last-120 Similar Regime")
        st.caption("The scan runs only when you open this section, not every time the Engine tab opens.")
        sim_controls = st.columns(4)
        with sim_controls[0]:
            sim_lookback = st.slider("Lookback days", 30, 120, 100, 5, key="engine_sim_lookback")
        with sim_controls[1]:
            sim_window = st.number_input("Window candles", min_value=60, max_value=240, value=120, step=10, key="engine_sim_window")
        with sim_controls[2]:
            sim_horizon = st.number_input("Future context candles", min_value=30, max_value=240, value=120, step=10, key="engine_sim_horizon")
        with sim_controls[3]:
            sim_step = st.select_slider("Scan step", options=[2, 4, 6, 10, 15, 20], value=10, key="engine_sim_step")
        run_sim = st.button("Run Similar Regime Scan", use_container_width=True, key="engine_run_similarity")
        if run_sim or "engine_last_similarity_result" not in st.session_state:
            sim_df, summary = _safe_similarity_engine(dfi, horizon=int(sim_horizon), lookback_days=int(sim_lookback), window=int(sim_window), step=int(sim_step), max_rank=25)
            st.session_state.engine_last_similarity_result = {"sim_df": sim_df, "summary": summary}
        saved_sim = _safe_session_get("engine_last_similarity_result", {})
        sim_df = saved_sim.get("sim_df", pd.DataFrame())
        summary = saved_sim.get("summary", {})
        cols = st.columns(5)
        for col, key in zip(cols, ["Dominant Similar Bias", "Bullish Similar %", "Bearish Similar %", "Safe Similarity Score /10", "Top Similarity %"]):
            col.metric(key, summary.get(key, "N/A"))
        st.caption(summary.get("Search Rule", "Uses older data only; excludes today and yesterday when timestamps exist."))
        with st.expander("📊 Open Similar Regime ranked table", expanded=False):
            if sim_df is None or sim_df.empty:
                st.warning(summary.get("Status", "Need more data for similar-regime matching."))
            else:
                st.dataframe(sim_df, use_container_width=True, height=420)
        return

    if section == "📈 Chart + Compact Data":
        with st.expander("📈 Open Candlestick Chart", expanded=True):
            _show_candlestick_chart(dfi)
        with st.expander("📋 Open Compact latest data table", expanded=False):
            compact = _compact_latest_data(dfi)
            if compact.empty:
                st.info("No compact data available.")
            else:
                st.dataframe(compact, use_container_width=True, height=380)
        return

    st.markdown("### Save / Debug")
    if st.button("💾 Save Engine Snapshot Now", use_container_width=True, key="engine_save_now"):
        row = {"time": pd.Timestamp.now(), "symbol": st.session_state.symbol, **q}
        ok, msg = _safe_append_csv("engine_mix_snapshots", row)
        if ok:
            st.success("Engine snapshot saved.")
        else:
            st.error(msg)
    with st.expander("Current Quant Output JSON", expanded=False):
        st.json(q)
    with st.expander("Latest dataframe columns", expanded=False):
        st.write(list(dfi.columns))
    with st.expander("Latest 10 rows", expanded=False):
        st.dataframe(dfi.tail(10), use_container_width=True)
    with st.expander("Import status", expanded=False):
        st.write({
            "add_indicators_available": add_indicators is not None,
            "quant_stack_available": quant_stack is not None,
            "manual_connect_available": manual_connect is not None,
            "append_csv_available": append_csv is not None,
            "backtest_similarity_engine_available": _backtest_similarity_engine is not None,
        })

