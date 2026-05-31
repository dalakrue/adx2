import math
import numpy as np
import pandas as pd

try:
    from .data import normalize_ohlc
except Exception:
    def normalize_ohlc(df):
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

        work = df.copy()
        work.columns = [str(c).strip().lower() for c in work.columns]

        rename = {
            "datetime": "time",
            "date": "time",
            "timestamp": "time",
            "tick_volume": "volume",
            "real_volume": "volume",
        }

        work = work.rename(columns={k: v for k, v in rename.items() if k in work.columns})

        required = ["time", "open", "high", "low", "close"]
        missing = [c for c in required if c not in work.columns]

        if missing:
            raise ValueError(f"Missing columns: {missing}")

        if "volume" not in work.columns:
            work["volume"] = 0

        work["time"] = pd.to_datetime(work["time"], errors="coerce")

        for c in ["open", "high", "low", "close", "volume"]:
            work[c] = pd.to_numeric(work[c], errors="coerce")

        work = work.dropna(subset=["time", "open", "high", "low", "close"])
        work = work.sort_values("time").drop_duplicates("time").reset_index(drop=True)

        return work[["time", "open", "high", "low", "close", "volume"]]


def _clean_series(s, fill=0.0):
    return pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(fill)


def _safe_score(x, low=0, high=100):
    try:
        return max(low, min(high, float(x)))
    except Exception:
        return low


def add_features(df):
    work = normalize_ohlc(df)

    if work.empty:
        return work

    work = work.copy()

    high = _clean_series(work["high"])
    low = _clean_series(work["low"])
    close = _clean_series(work["close"])
    open_ = _clean_series(work["open"])
    volume = _clean_series(work["volume"])

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

    plus_dm = pd.Series(
        np.where((up > down) & (up > 0), up, 0.0),
        index=work.index,
    )

    minus_dm = pd.Series(
        np.where((down > up) & (down > 0), down, 0.0),
        index=work.index,
    )

    atr_safe = atr.replace(0, np.nan)

    plus_di = 100 * plus_dm.rolling(14, min_periods=1).mean() / atr_safe
    minus_di = 100 * minus_dm.rolling(14, min_periods=1).mean() / atr_safe

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(14, min_periods=1).mean()

    work["atr"] = atr
    work["plus_di"] = plus_di
    work["minus_di"] = minus_di
    work["adx"] = adx
    work["pressure"] = plus_di - minus_di
    work["adx_slope"] = work["adx"].diff().fillna(0)
    work["atr_slope"] = work["atr"].diff().fillna(0)

    work["ret"] = close.pct_change().replace([np.inf, -np.inf], 0).fillna(0)

    safe_close = close.replace(0, np.nan)
    work["log_ret"] = np.log(safe_close / safe_close.shift(1))
    work["log_ret"] = work["log_ret"].replace([np.inf, -np.inf], 0).fillna(0)

    candle_range = (high - low).replace(0, np.nan)
    body = (close - open_).abs()

    work["range"] = candle_range
    work["body"] = body
    work["wick_ratio"] = ((candle_range - body) / candle_range).replace([np.inf, -np.inf], 0).fillna(0)
    work["candle_efficiency"] = (body / candle_range).replace([np.inf, -np.inf], 0).fillna(0)

    work["trend_power"] = work["adx"] * work["pressure"].abs()

    atr_mean = work["atr"].rolling(50, min_periods=1).mean().replace(0, np.nan)
    work["volatility_regime"] = (work["atr"] / atr_mean).replace([np.inf, -np.inf], 0).fillna(0)

    work["volatility_decay"] = (
        work["atr"].rolling(10, min_periods=1).mean()
        - work["atr"].rolling(50, min_periods=1).mean()
    ).replace([np.inf, -np.inf], 0).fillna(0)

    mean_120 = close.rolling(120, min_periods=20).mean()
    std_120 = close.rolling(120, min_periods=20).std().replace(0, np.nan)

    work["regression_to_mean_z"] = ((close - mean_120) / std_120).replace([np.inf, -np.inf], 0).fillna(0)

    ret_mean = work["log_ret"].rolling(120, min_periods=20).mean()
    ret_std = work["log_ret"].rolling(120, min_periods=20).std().replace(0, np.nan)

    work["ergodicity_proxy"] = (ret_mean / ret_std).replace([np.inf, -np.inf], 0).fillna(0)

    vol_mean = volume.rolling(80, min_periods=10).mean().replace(0, np.nan)
    vol_std = volume.rolling(80, min_periods=10).std().replace(0, np.nan)

    work["volume_z"] = ((volume - vol_mean) / vol_std).replace([np.inf, -np.inf], 0).fillna(0)

    work["spoofing_proxy"] = (
        work["wick_ratio"].clip(0, 1) * 45
        + (1 - work["candle_efficiency"].clip(0, 1)) * 35
        + work["volume_z"].abs().clip(0, 5) * 4
    ).replace([np.inf, -np.inf], 0).fillna(0)

    work["time"] = pd.to_datetime(work["time"], errors="coerce")
    work = work.dropna(subset=["time"])

    work["date"] = work["time"].dt.date
    work["date_ts"] = pd.to_datetime(work["date"])
    work["tod_minute"] = work["time"].dt.hour * 60 + work["time"].dt.minute

    return work.replace([np.inf, -np.inf], 0).fillna(0)


def window_vector(win, cols):
    arr = win[cols].astype(float).values
    arr = np.nan_to_num(arr, nan=0, posinf=0, neginf=0)

    mean = arr.mean(axis=0)
    std = arr.std(axis=0)
    change = arr[-1] - arr[0]
    last10 = arr[-10:].mean(axis=0) if len(arr) >= 10 else arr[-1]
    q10 = np.percentile(arr, 10, axis=0)
    q90 = np.percentile(arr, 90, axis=0)

    return np.concatenate([mean, std, change, last10, q10, q90])


def cosine_score(a, b):
    try:
        denom = np.linalg.norm(a) * np.linalg.norm(b) + 1e-12
        raw = float(np.dot(a, b) / denom)
        score = max(0, min(100, (raw + 1) * 50))
        return raw, score
    except Exception:
        return 0.0, 50.0


def pca_score_numpy(all_vecs):
    if all_vecs.shape[0] < 3:
        return np.full(max(0, all_vecs.shape[0] - 1), 50.0)

    try:
        x = all_vecs - all_vecs.mean(axis=0)
        _, _, vt = np.linalg.svd(x, full_matrices=False)

        n_comp = min(6, vt.shape[0], all_vecs.shape[1], all_vecs.shape[0] - 1)

        coords = x @ vt[:n_comp].T
        current = coords[0]
        candidates = coords[1:]

        dist = np.linalg.norm(candidates - current, axis=1)
        med = max(float(np.median(dist)), 1e-9)

        return np.clip(100 * np.exp(-dist / med), 0, 100)

    except Exception:
        return np.full(max(0, all_vecs.shape[0] - 1), 50.0)


def kurtosis_value(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]

    if len(x) < 8:
        return 3.0

    m = x.mean()
    s = x.std()

    if s == 0:
        return 3.0

    return float(np.mean(((x - m) / s) ** 4))


def max_drawdown_pct(log_rets):
    x = np.asarray(log_rets, dtype=float)
    x = x[np.isfinite(x)]

    if len(x) == 0:
        return 0.0

    equity = np.exp(np.cumsum(x))
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / np.maximum(peak, 1e-12)

    return abs(float(dd.min()) * 100)


def monte_carlo_score(log_rets, horizon=120, paths=300, seed=1):
    x = np.asarray(log_rets, dtype=float)
    x = x[np.isfinite(x)]

    if len(x) < 10:
        return 50.0, "UNKNOWN", 0.0, 0.0

    rng = np.random.default_rng(seed)

    horizon = int(max(5, min(horizon, 1000)))
    paths = int(max(50, min(paths, 2000)))

    sims = rng.choice(x, size=(paths, horizon), replace=True).sum(axis=1)
    moves = (np.exp(sims) - 1) * 100

    prob_up = float(np.mean(moves > 0))
    prob_down = 1 - prob_up

    bias = "BULLISH" if prob_up >= prob_down else "BEARISH"

    confidence = max(prob_up, prob_down)
    dispersion = float(np.std(moves))
    expected = float(np.mean(moves))
    stability = 1 / (1 + dispersion / 5)

    score = confidence * 75 + stability * 25

    return round(score, 2), bias, round(expected, 4), round(dispersion, 4)


def find_similar_days(df, lookback_days=100, window=120, horizon=120, top_n=10, mc_paths=300):
    work = add_features(df)

    if work.empty:
        return pd.DataFrame(), {"Status": "No usable data."}

    lookback_days = int(max(5, lookback_days))
    window = int(max(20, window))
    horizon = int(max(5, horizon))
    top_n = int(max(1, top_n))
    mc_paths = int(max(50, mc_paths))

    need = int(window + horizon + 50)

    if len(work) < need:
        return pd.DataFrame(), {
            "Status": f"Need more candles. Have {len(work)}, need at least {need}."
        }

    cols = [
        "ret",
        "log_ret",
        "adx",
        "plus_di",
        "minus_di",
        "atr",
        "pressure",
        "adx_slope",
        "atr_slope",
        "wick_ratio",
        "candle_efficiency",
        "trend_power",
        "volatility_regime",
        "volatility_decay",
        "regression_to_mean_z",
        "ergodicity_proxy",
        "spoofing_proxy",
    ]

    today_date = work["date_ts"].iloc[-1]
    yesterday = today_date - pd.Timedelta(days=1)
    start_date = today_date - pd.Timedelta(days=lookback_days)

    today_rows = work[work["date_ts"] == today_date]

    if len(today_rows) >= window:
        current_win = today_rows.tail(window).copy()
    else:
        current_win = work.tail(window).copy()

    current_end = current_win["time"].iloc[-1]
    current_tod = int(current_win["tod_minute"].iloc[-1])
    current_vec_raw = window_vector(current_win, cols)

    current_pressure = float(current_win["pressure"].mean())
    current_bias = 1 if current_pressure >= 0 else -1

    search = work[
        (work["date_ts"] >= start_date)
        & (work["date_ts"] < yesterday)
    ].copy()

    if len(search) < window:
        return pd.DataFrame(), {
            "Status": "Not enough older data after excluding today and yesterday. Load more candles."
        }

    candidates = []

    for day, day_df in search.groupby("date"):
        day_df = day_df.sort_values("time")

        if len(day_df) < window:
            continue

        best_for_day = None
        positions = list(range(window - 1, len(day_df), 20))

        try:
            same_time_pos = int((day_df["tod_minute"] - current_tod).abs().idxmin())
            local_pos = list(day_df.index).index(same_time_pos)
            positions.append(local_pos)
        except Exception:
            pass

        positions.append(len(day_df) - 1)
        positions = sorted(set([p for p in positions if window - 1 <= p < len(day_df)]))

        for pos in positions:
            win = day_df.iloc[pos - window + 1: pos + 1].copy()

            if len(win) < window:
                continue

            end_idx = int(win.index[-1])
            future_idx = end_idx + horizon

            if future_idx >= len(work):
                continue

            try:
                vec = window_vector(win, cols)

                end_price = float(work.iloc[end_idx]["close"])
                future_price = float(work.iloc[future_idx]["close"])

                future_move = (future_price - end_price) / max(abs(end_price), 1e-12) * 100
                outcome = "BULLISH" if future_move > 0 else "BEARISH"

                cand_tod = int(work.iloc[end_idx]["tod_minute"])
                minutes = abs(cand_tod - current_tod)
                minutes = min(minutes, 1440 - minutes)

                fat_k = kurtosis_value(win["log_ret"].values)
                dd = max_drawdown_pct(win["log_ret"].values)

                fat_tail_score = _safe_score(100 - max(0, fat_k - 3) * 8 - dd * 0.8)

                cur_vd = float(current_win["volatility_decay"].mean())
                cand_vd = float(win["volatility_decay"].mean())
                volatility_decay_score = _safe_score(100 * math.exp(-abs(cur_vd - cand_vd) * 4))

                cur_z = float(current_win["regression_to_mean_z"].iloc[-1])
                cand_z = float(win["regression_to_mean_z"].iloc[-1])
                regression_score = _safe_score(100 * math.exp(-abs(cur_z - cand_z) / 2))

                cur_ergo = float(current_win["ergodicity_proxy"].mean())
                cand_ergo = float(win["ergodicity_proxy"].mean())
                ergodicity_score = _safe_score(100 * math.exp(-abs(cur_ergo - cand_ergo) * 4) - dd * 0.3)

                spoofing_risk = float(win["spoofing_proxy"].mean())
                spoofing_safety_score = _safe_score(100 - spoofing_risk)

                mc_score, mc_bias, mc_expected, mc_dispersion = monte_carlo_score(
                    win["log_ret"].values,
                    horizon=horizon,
                    paths=mc_paths,
                    seed=int(end_idx * 17 + len(win) * 11) % 999983,
                )

                candidate = {
                    "day": str(day),
                    "end_time": work.iloc[end_idx]["time"],
                    "minutes": int(minutes),
                    "vec": vec,
                    "future_move": float(future_move),
                    "outcome": outcome,
                    "fat_tail_score": float(fat_tail_score),
                    "fat_kurtosis": float(fat_k),
                    "max_drawdown_pct": float(dd),
                    "volatility_decay_score": float(volatility_decay_score),
                    "regression_score": float(regression_score),
                    "ergodicity_score": float(ergodicity_score),
                    "spoofing_safety_score": float(spoofing_safety_score),
                    "spoofing_risk": float(spoofing_risk),
                    "mc_score": float(mc_score),
                    "mc_bias": mc_bias,
                    "mc_expected": float(mc_expected),
                    "mc_dispersion": float(mc_dispersion),
                    "adx": float(win["adx"].mean()),
                    "atr": float(win["atr"].mean()),
                    "pressure": float(win["pressure"].mean()),
                }

                if best_for_day is None:
                    best_for_day = candidate
                else:
                    rough_current = abs(candidate["minutes"]) + candidate["spoofing_risk"] - candidate["fat_tail_score"]
                    rough_best = abs(best_for_day["minutes"]) + best_for_day["spoofing_risk"] - best_for_day["fat_tail_score"]

                    if rough_current < rough_best:
                        best_for_day = candidate

            except Exception:
                continue

        if best_for_day is not None:
            candidates.append(best_for_day)

    if not candidates:
        return pd.DataFrame(), {
            "Status": "No valid similar days found. Load more candles or reduce pattern window."
        }

    matrix = np.vstack([current_vec_raw] + [c["vec"] for c in candidates])

    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std[std == 0] = 1.0

    scaled = (matrix - mean) / std
    current_vec = scaled[0]
    cand_vecs = scaled[1:]

    pca_scores = pca_score_numpy(scaled)

    rows = []

    for i, c in enumerate(candidates):
        _, knn_score = cosine_score(current_vec, cand_vecs[i])
        pca_score = float(pca_scores[i])

        hist_bias = 1 if c["future_move"] >= 0 else -1

        feature_like = _safe_score((knn_score * 0.65 + pca_score * 0.35) / 100, 0.01, 0.99)
        outcome_strength = 1 / (1 + math.exp(-abs(c["future_move"]) / 0.30))

        outcome_like = outcome_strength if hist_bias == current_bias else 1 - outcome_strength

        numerator = feature_like * outcome_like
        denominator = numerator + (1 - feature_like) * (1 - outcome_like) + 1e-12
        bayes_score = _safe_score(numerator / denominator * 100)

        time_score = _safe_score(100 - (c["minutes"] / 360) * 100)

        final_score = (
            knn_score * 0.24
            + bayes_score * 0.14
            + pca_score * 0.13
            + c["fat_tail_score"] * 0.10
            + c["volatility_decay_score"] * 0.10
            + c["regression_score"] * 0.09
            + c["ergodicity_score"] * 0.08
            + c["spoofing_safety_score"] * 0.07
            + c["mc_score"] * 0.04
            + time_score * 0.01
        )

        rows.append(
            {
                "Most Similar Day": c["day"],
                "Most Similar Time": c["end_time"],
                "Minutes From Current Time": c["minutes"],
                "Final Rank Score": round(final_score, 2),
                "KNN Score": round(knn_score, 2),
                "Bayes Score": round(bayes_score, 2),
                "PCA Score": round(pca_score, 2),
                "Fat Tail Score": round(c["fat_tail_score"], 2),
                "Volatility Decay Score": round(c["volatility_decay_score"], 2),
                "Regression Mean Score": round(c["regression_score"], 2),
                "Ergodicity Score": round(c["ergodicity_score"], 2),
                "Spoofing Safety Score": round(c["spoofing_safety_score"], 2),
                "Monte Carlo Score": round(c["mc_score"], 2),
                "Monte Carlo Bias": c["mc_bias"],
                "MC Expected Move %": round(c["mc_expected"], 4),
                "Historical Future Move %": round(c["future_move"], 4),
                "Outcome": c["outcome"],
                "ADX": round(c["adx"], 2),
                "ATR": round(c["atr"], 5),
                "Pressure": round(c["pressure"], 2),
                "Fat Kurtosis": round(c["fat_kurtosis"], 2),
                "Max Drawdown %": round(c["max_drawdown_pct"], 3),
                "Spoofing Risk Proxy": round(c["spoofing_risk"], 2),
            }
        )

    result = pd.DataFrame(rows)

    result = result.sort_values("Final Rank Score", ascending=False)
    result = result.drop_duplicates("Most Similar Day", keep="first")
    result = result.head(top_n).reset_index(drop=True)
    result.insert(0, "Rank", range(1, len(result) + 1))

    bullish = float((result["Outcome"] == "BULLISH").mean() * 100) if len(result) else 50
    bearish = 100 - bullish

    summary = {
        "Status": "OK",
        "Current Window End": str(current_end),
        "Search": f"Last {lookback_days} days, excluding today and yesterday",
        "Returned Days": int(len(result)),
        "Dominant Bias": "BUY / BULLISH" if bullish > bearish else "SELL / BEARISH",
        "Bullish %": round(bullish, 1),
        "Bearish %": round(bearish, 1),
        "Top Score": float(result["Final Rank Score"].iloc[0]) if len(result) else 0,
    }

    return result, summary