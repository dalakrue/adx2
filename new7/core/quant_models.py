import numpy as np
import pandas as pd

try:
    from core.common import safe_float
except Exception:
    def safe_float(x, default=0.0):
        try:
            return float(x)
        except Exception:
            return default


try:
    from ta.trend import ADXIndicator
    from ta.volatility import AverageTrueRange
except Exception:
    ADXIndicator = None
    AverageTrueRange = None


try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
except Exception:
    RandomForestClassifier = None
    GradientBoostingClassifier = None


def _clean_ohlc(df):
    if df is None or len(df) == 0:
        return pd.DataFrame()

    df = df.copy()

    for c in ["open", "high", "low", "close"]:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")
        df[c] = pd.to_numeric(df[c], errors="coerce")

    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")

    if "volume" not in df.columns:
        df["volume"] = 0

    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["open", "high", "low", "close"])

    return df.reset_index(drop=True)


def _fallback_indicators(df):
    df = df.copy()

    prev_close = df["close"].shift(1)

    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.rolling(14, min_periods=1).mean()

    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    plus_di = 100 * plus_dm.rolling(14, min_periods=1).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.rolling(14, min_periods=1).mean() / atr.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(14, min_periods=1).mean()

    df["adx"] = adx.fillna(0)
    df["plus_di"] = plus_di.fillna(0)
    df["minus_di"] = minus_di.fillna(0)
    df["atr"] = atr.fillna(0)

    return df


def add_indicators(df):
    try:
        df = _clean_ohlc(df)
    except Exception:
        return pd.DataFrame()

    if len(df) < 5:
        return df

    try:
        if ADXIndicator is not None and AverageTrueRange is not None and len(df) >= 30:
            adx = ADXIndicator(df["high"], df["low"], df["close"], window=14)
            atr = AverageTrueRange(df["high"], df["low"], df["close"], window=14)

            df["adx"] = adx.adx()
            df["plus_di"] = adx.adx_pos()
            df["minus_di"] = adx.adx_neg()
            df["atr"] = atr.average_true_range()
        else:
            df = _fallback_indicators(df)
    except Exception:
        df = _fallback_indicators(df)

    df["ret"] = df["close"].pct_change().fillna(0)
    df["momentum"] = df["close"].diff().fillna(0)
    df["pressure"] = df["plus_di"] - df["minus_di"]
    df["adx_slope"] = df["adx"].diff().fillna(0)

    df["range"] = (df["high"] - df["low"]).replace(0, np.nan)
    df["body"] = (df["close"] - df["open"]).abs()
    df["wick_ratio"] = ((df["range"] - df["body"]) / df["range"]).fillna(0)

    df["volatility"] = df["ret"].rolling(30, min_periods=1).std().fillna(0)
    df["vol_decay"] = df["volatility"].diff().fillna(0)
    df["fat_tail"] = df["ret"].rolling(60, min_periods=5).kurt().fillna(0)

    df["ma20"] = df["close"].rolling(20, min_periods=1).mean()
    df["ma50"] = df["close"].rolling(50, min_periods=1).mean()
    df["mean_dist"] = (df["close"] - df["ma50"]).fillna(0)

    df["trend_power"] = df["adx"] * df["pressure"].abs()
    df["momentum_velocity"] = df["momentum"].rolling(5, min_periods=1).mean()
    df["range_expansion"] = (
        df["range"] / df["range"].rolling(20, min_periods=1).mean().replace(0, np.nan)
    ).fillna(0)

    df["directional_efficiency"] = (
        (df["close"] - df["close"].shift(30)).abs()
        / df["close"].diff().abs().rolling(30, min_periods=1).sum().replace(0, np.nan)
    ).fillna(0)

    df["trend_age"] = (
        (np.sign(df["pressure"]) == np.sign(df["pressure"].shift(1)))
        .astype(int)
        .rolling(30, min_periods=1)
        .sum()
    )

    df["exhaustion_risk"] = np.clip(
        (df["wick_ratio"] * 35)
        + (df["fat_tail"].clip(lower=0) * 5)
        + (df["trend_age"] / 30 * 25)
        - (df["directional_efficiency"] * 20),
        0,
        100,
    )

    df["start_impulse_score"] = np.clip(
        (df["adx_slope"].clip(lower=0) * 8)
        + (df["range_expansion"] * 20)
        + (df["directional_efficiency"] * 35)
        + (df["pressure"].abs() / 2),
        0,
        100,
    )

    df = df.replace([np.inf, -np.inf], np.nan).ffill().fillna(0)
    return df.reset_index(drop=True)


def regime_label(df):
    df = add_indicators(df)

    if df.empty:
        return "UNKNOWN", {}

    last = df.iloc[-1]

    adx = float(last.get("adx", 0))
    slope = float(last.get("adx_slope", 0))
    eff = float(last.get("directional_efficiency", 0))
    expansion = float(last.get("range_expansion", 0))
    exhaustion = float(last.get("exhaustion_risk", 0))
    start_score = float(last.get("start_impulse_score", 0))
    pressure = float(last.get("pressure", 0))

    if start_score >= 65 and slope > 0 and eff >= 0.35:
        regime = "IMPULSE_START"
    elif adx >= 25 and eff >= 0.25 and exhaustion < 60:
        regime = "TREND_CONTINUATION"
    elif exhaustion >= 70:
        regime = "EXHAUSTION_OR_REVERSAL_RISK"
    elif expansion < 0.85 and adx < 20:
        regime = "ACCUMULATION_OR_RANGE"
    elif adx < 18 and abs(pressure) < 8:
        regime = "DISTRIBUTION_OR_CHOP"
    else:
        regime = "WAIT_CONFIRMATION"

    return regime, {
        "adx": round(adx, 2),
        "adx_slope": round(slope, 4),
        "directional_efficiency": round(eff, 3),
        "range_expansion": round(expansion, 3),
        "exhaustion_risk": round(exhaustion, 1),
        "start_impulse_score": round(start_score, 1),
        "pressure": round(pressure, 2),
    }


def ml_bias(df):
    df = add_indicators(df)

    if df.empty:
        return "WAIT", 0.50, {"mode": "empty_data"}

    feats = [
        "adx", "plus_di", "minus_di", "atr", "pressure",
        "adx_slope", "momentum", "volatility", "mean_dist",
        "vol_decay", "fat_tail", "wick_ratio", "trend_power",
        "momentum_velocity", "range_expansion",
        "directional_efficiency", "exhaustion_risk", "start_impulse_score",
    ]

    if len(df) < 100 or RandomForestClassifier is None or GradientBoostingClassifier is None:
        p = float(df["pressure"].iloc[-1])
        bias = "BUY" if p > 0 else "SELL" if p < 0 else "WAIT"
        conf = float(np.clip(0.50 + abs(p) / 120, 0.50, 0.68))
        return bias, conf, {"mode": "fallback_pressure"}

    work = df.copy()
    work["target"] = (work["close"].shift(-12) > work["close"]).astype(int)
    work = work.dropna()

    if len(work) < 80 or work["target"].nunique() < 2:
        p = float(df["pressure"].iloc[-1])
        bias = "BUY" if p >= 0 else "SELL"
        return bias, 0.55, {"mode": "fallback_target"}

    X = work[feats].replace([np.inf, -np.inf], 0).fillna(0)
    y = work["target"].astype(int)

    try:
        split = int(len(X) * 0.80)

        X_train = X.iloc[:split]
        y_train = y.iloc[:split]

        rf = RandomForestClassifier(
            n_estimators=180,
            max_depth=8,
            min_samples_leaf=3,
            random_state=7,
            n_jobs=-1,
        )

        gb = GradientBoostingClassifier(
            random_state=11,
            n_estimators=100,
            max_depth=3,
        )

        rf.fit(X_train, y_train)
        gb.fit(X_train, y_train)

        x = df[feats].iloc[[-1]].replace([np.inf, -np.inf], 0).fillna(0)

        rf_buy = float(rf.predict_proba(x)[0][1])
        gb_buy = float(gb.predict_proba(x)[0][1])
        pr = (rf_buy * 0.55) + (gb_buy * 0.45)

        bias = "BUY" if pr >= 0.5 else "SELL"
        conf = float(max(pr, 1 - pr))

        return bias, conf, {
            "mode": "ml_ensemble",
            "rf_buy": round(rf_buy, 4),
            "gb_buy": round(gb_buy, 4),
            "ensemble_buy": round(pr, 4),
            "train_rows": len(X_train),
        }

    except Exception as e:
        p = float(df["pressure"].iloc[-1])
        return ("BUY" if p >= 0 else "SELL"), 0.55, {"mode": "ml_error", "error": str(e)}


def history_match(df, trade_history=None):
    df = add_indicators(df)

    if df.empty:
        return 0.50, 0

    latest = df.iloc[-1]
    hist = pd.DataFrame(trade_history or [])

    try:
        if not hist.empty and {"pressure", "adx", "result"}.issubset(hist.columns):
            hist = hist.copy()
            hist["pressure"] = pd.to_numeric(hist["pressure"], errors="coerce")
            hist["adx"] = pd.to_numeric(hist["adx"], errors="coerce")
            hist = hist.dropna(subset=["pressure", "adx"])

            hist["dist"] = (
                (hist["pressure"] - float(latest["pressure"])).abs()
                + (hist["adx"] - float(latest["adx"])).abs() / 2
            )

            m = hist.sort_values("dist").head(30)
            sample = len(m)

            wins = m["result"].astype(str).str.upper().isin(
                ["WIN", "PROFIT", "TP", "TAKE_PROFIT"]
            ).mean()

            if not np.isnan(wins):
                return float(np.clip(wins, 0.25, 0.85)), sample
    except Exception:
        pass

    score = float(
        np.clip(
            0.50 + np.tanh(
                abs(float(latest["pressure"])) / 30 + float(latest["adx"]) / 100
            ) / 4,
            0.35,
            0.75,
        )
    )

    return score, 0


def quant_stack(df, trade_history=None, account=None):
    df = add_indicators(df)

    if df.empty or len(df) < 5:
        return {
            "bias": "WAIT",
            "safe_pct": 1,
            "scale10": 0.1,
            "history_samples": 0,
            "error": "not_enough_data",
        }

    last = df.iloc[-1]

    bias, conf, meta = ml_bias(df)
    hm, hm_n = history_match(df, trade_history)
    regime, regime_meta = regime_label(df)

    vol = float(last.get("volatility", 0))
    mean_dist = float(last.get("mean_dist", 0))
    atr = max(float(last.get("atr", 0)), 1e-9)

    mean_revert_risk = min(1, abs(mean_dist) / (atr * 3 + 1e-9))
    decay = max(0, -float(last.get("vol_decay", 0)) * 10000)
    fat_tail = min(1, max(0, float(last.get("fat_tail", 0)) / 10))
    exhaustion = min(1, float(last.get("exhaustion_risk", 0)) / 100)
    impulse = min(1, float(last.get("start_impulse_score", 0)) / 100)

    bayes = (
        conf * 0.38
        + hm * 0.25
        + (1 - mean_revert_risk) * 0.12
        + (1 - fat_tail) * 0.10
        + impulse * 0.10
        + (1 - exhaustion) * 0.05
    )

    safe_pct = float(np.clip(bayes * 100, 1, 99))

    try:
        ret_mean = float(df["ret"].tail(200).mean())
        ret_std = float(df["ret"].tail(200).std() + 1e-8)
        mc = np.random.default_rng(42).normal(ret_mean, ret_std, (300, 720)).sum(axis=1)
        mc_positive = float((mc > 0).mean()) if bias == "BUY" else float((mc < 0).mean())
    except Exception:
        mc_positive = 0.50

    spoofing_risk = float(
        np.clip(abs(float(last["pressure"])) / (float(last["adx"]) + 1) / 3, 0, 1)
    )

    ergodicity = float(np.clip(1 - fat_tail * 0.55 - mean_revert_risk * 0.25 - exhaustion * 0.20, 0, 1))

    final_pct = float(
        np.clip(
            (safe_pct * 0.60 + mc_positive * 100 * 0.20 + ergodicity * 100 * 0.12 + impulse * 100 * 0.08)
            - spoofing_risk * 8,
            1,
            99,
        )
    )

    if regime in ["EXHAUSTION_OR_REVERSAL_RISK", "DISTRIBUTION_OR_CHOP"]:
        final_pct *= 0.82

    if final_pct < 45:
        final_bias = "WAIT"
    else:
        final_bias = bias

    return {
        "bias": final_bias,
        "safe_pct": round(final_pct, 1),
        "scale10": round(final_pct / 10, 1),

        "regime": regime,
        "regime_meta": regime_meta,

        "ml_conf_pct": round(conf * 100, 1),
        "history_match_pct": round(hm * 100, 1),
        "history_samples": hm_n,

        "volatility": round(vol, 8),
        "vol_decay": round(decay, 2),
        "mean_revert_risk_pct": round(mean_revert_risk * 100, 1),
        "fat_tail_risk_pct": round(fat_tail * 100, 1),
        "exhaustion_risk_pct": round(exhaustion * 100, 1),
        "impulse_start_pct": round(impulse * 100, 1),

        "bayes_pct": round(bayes * 100, 1),
        "kelly_fraction": round(max(0, min(0.25, (bayes * 2 - 1) / 2)), 3),
        "monte_carlo_pct": round(mc_positive * 100, 1),
        "ergodicity_pct": round(ergodicity * 100, 1),
        "spoofing_risk_pct": round(spoofing_risk * 100, 1),

        "meta": meta,
        "adx": round(float(last["adx"]), 2),
        "pressure": round(float(last["pressure"]), 2),
        "atr": round(float(atr), 4),
        "directional_efficiency": round(float(last.get("directional_efficiency", 0)), 3),
        "range_expansion": round(float(last.get("range_expansion", 0)), 3),
    }


def pre_manual_decision(plus_now, minus_now, plus_prev, minus_prev, selected_decision="WAIT"):
    plus_now = safe_float(plus_now)
    minus_now = safe_float(minus_now)
    plus_prev = safe_float(plus_prev)
    minus_prev = safe_float(minus_prev)

    selected_decision = str(selected_decision or "WAIT").upper()

    pressure = plus_now - minus_now
    prev = plus_prev - minus_prev
    accel = pressure - prev

    raw = 50 + np.tanh(pressure / 20) * 20 + np.tanh(accel / 10) * 15

    if selected_decision == "BUY":
        raw += 5 if pressure > 0 else -12
    elif selected_decision == "SELL":
        raw += 5 if pressure < 0 else -12
    elif selected_decision == "WAIT":
        raw = 100 - abs(raw - 50)

    pct = float(np.clip(raw, 0, 100))
    bias = "BUY" if pressure > 0 else "SELL" if pressure < 0 else "WAIT"

    return {
        "manual_bias": bias,
        "decision_quality_pct": round(pct, 1),
        "scale10": round(pct / 10, 1),
        "pressure": round(pressure, 2),
        "acceleration": round(accel, 2),
        "comment": "Dynamic manual emergency model; no API connection used.",
    }