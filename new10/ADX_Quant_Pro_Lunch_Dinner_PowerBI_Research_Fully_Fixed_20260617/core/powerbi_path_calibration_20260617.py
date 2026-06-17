"""Accuracy/reliability calibration for existing PowerBI projection paths.

This module does not train or add a prediction model.  It post-processes the
project's already-computed red/yellow/blue paths with deterministic robust
statistics, completed prediction-vs-actual error, regime reliability and
cross-path agreement.  Original source columns remain untouched by callers.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional
import math

import numpy as np
import pandas as pd


CALIBRATION_VERSION = "powerbi-path-calibration-20260617-v1"


def _finite(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else float(default)
    except Exception:
        return float(default)


def _clip(value: Any, low: float, high: float) -> float:
    return float(max(low, min(high, _finite(value, low))))


def _find_col(frame: pd.DataFrame, aliases: Iterable[str]) -> Optional[str]:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    normalized = {str(c).strip().lower().replace("_", " "): c for c in frame.columns}
    for alias in aliases:
        key = str(alias).strip().lower().replace("_", " ")
        if key in normalized:
            return normalized[key]
    for alias in aliases:
        key = str(alias).strip().lower().replace("_", " ")
        for norm, original in normalized.items():
            if key and key in norm:
                return original
    return None


def _prepare_market(data: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame) or data.empty:
        return pd.DataFrame()
    frame = data.copy()
    lower = {str(c).strip().lower(): c for c in frame.columns}
    rename = {}
    for target, aliases in {
        "time": ("time", "datetime", "timestamp", "date"),
        "open": ("open", "o"),
        "high": ("high", "h"),
        "low": ("low", "l"),
        "close": ("close", "c"),
    }.items():
        for alias in aliases:
            if alias in lower:
                rename[lower[alias]] = target
                break
    frame = frame.rename(columns=rename)
    if "time" not in frame.columns or "close" not in frame.columns:
        return pd.DataFrame()
    for column in ("open", "high", "low", "close"):
        if column not in frame.columns:
            frame[column] = frame["close"]
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["time"] = pd.to_datetime(frame["time"], errors="coerce")
    frame = frame.dropna(subset=["time", "close"]).sort_values("time")
    frame = frame.drop_duplicates("time", keep="last").reset_index(drop=True)
    if frame.empty:
        return frame
    frame["high"] = frame[["open", "high", "close"]].max(axis=1)
    frame["low"] = frame[["open", "low", "close"]].min(axis=1)
    return frame


def _bar_delta(market: pd.DataFrame) -> pd.Timedelta:
    try:
        deltas = pd.to_datetime(market["time"], errors="coerce").diff().dropna()
        median = deltas.median() if len(deltas) else pd.Timedelta(hours=1)
        if pd.notna(median) and median.total_seconds() > 0:
            return median
    except Exception:
        pass
    return pd.Timedelta(hours=1)


def _source_path(
    source: pd.DataFrame,
    *,
    name: str,
    horizon: int,
    future_times: pd.Series,
    anchor_price: float,
) -> pd.DataFrame:
    if not isinstance(source, pd.DataFrame) or source.empty:
        return pd.DataFrame(columns=["step", "time", name])
    time_col = _find_col(source, ("time", "future time", "datetime", "date", "projection time"))
    value_col = _find_col(
        source,
        (
            "path", "accuracy adjusted price", "predicted close", "projected close",
            "yellow predicted close", "calibrated close", "close", "projected path",
        ),
    )
    if value_col is None:
        return pd.DataFrame(columns=["step", "time", name])
    work = pd.DataFrame({name: pd.to_numeric(source[value_col], errors="coerce")})
    if time_col is not None:
        work["time"] = pd.to_datetime(source[time_col], errors="coerce")
    else:
        # Limit before assigning generated times so a long source without an
        # explicit time column cannot create a length mismatch.
        work = work.head(horizon).copy()
        work["time"] = future_times.iloc[: len(work)].to_numpy()
    step_col = _find_col(source, ("step", "prediction step", "horizon point", "projection step"))
    if step_col is not None:
        work["step"] = pd.to_numeric(source[step_col], errors="coerce")
    else:
        work["step"] = np.arange(1, len(work) + 1)
    work = work.dropna(subset=[name]).copy()
    work["step"] = pd.to_numeric(work["step"], errors="coerce").fillna(0).astype(int)
    work = work[work["step"] > 0].sort_values("step").drop_duplicates("step", keep="last")
    work = work.head(horizon).reset_index(drop=True)
    if work.empty:
        return pd.DataFrame(columns=["step", "time", name])
    # Anchor correction removes stale source offsets while preserving the source's
    # shape. This is especially important for the previous-candle blue path.
    first_value = _finite(work[name].iloc[0], anchor_price)
    if abs(first_value - anchor_price) > max(abs(anchor_price) * 0.00002, 1e-9):
        source_anchor_col = _find_col(source, ("anchor price", "anchor_price", "start price", "predicted open", "open"))
        if source_anchor_col is not None:
            source_anchor = _finite(source[source_anchor_col].iloc[0], anchor_price)
            work[name] = anchor_price + (work[name] - source_anchor)
    return work[["step", "time", name]]


def _backtest_error(
    bt_history: pd.DataFrame,
    bt_summary: Dict[str, Any],
    *,
    anchor_price: float,
    atr: float,
) -> Dict[str, Any]:
    history = bt_history if isinstance(bt_history, pd.DataFrame) else pd.DataFrame()
    summary = bt_summary if isinstance(bt_summary, dict) else {}
    residuals = pd.Series(dtype=float)
    direction_accuracy = None
    if not history.empty:
        actual_col = _find_col(history, ("actual close", "actual", "close actual", "real close"))
        pred_col = _find_col(history, ("predicted close", "pred close", "prediction", "projected close", "forecast close"))
        if actual_col and pred_col:
            actual = pd.to_numeric(history[actual_col], errors="coerce")
            predicted = pd.to_numeric(history[pred_col], errors="coerce")
            residuals = (actual - predicted).abs().dropna()
        dir_col = _find_col(history, ("direction correct", "correct direction", "direction hit"))
        if dir_col:
            values = history[dir_col]
            if values.dtype == bool:
                direction_accuracy = float(values.mean() * 100.0)
            else:
                mapped = values.astype(str).str.upper().map({"TRUE": 1.0, "YES": 1.0, "CORRECT": 1.0, "1": 1.0, "FALSE": 0.0, "NO": 0.0, "WRONG": 0.0, "0": 0.0})
                if mapped.notna().any():
                    direction_accuracy = float(mapped.mean() * 100.0)
    if direction_accuracy is None:
        for key in ("direction_accuracy_pct", "direction accuracy pct", "direction_accuracy", "accuracy_pct"):
            if key in summary:
                direction_accuracy = _finite(summary.get(key), 0.0)
                if 0.0 <= direction_accuracy <= 1.0:
                    direction_accuracy *= 100.0
                break
    sample_count = int(len(residuals))
    empirical_price_error = float(residuals.median()) if sample_count else 0.0
    error_pct = 0.0
    for key in ("avg_abs_close_error_pct", "average_error_pct", "mae_pct", "close_error_pct"):
        if key in summary:
            error_pct = abs(_finite(summary.get(key), 0.0))
            break
    if empirical_price_error <= 0 and error_pct > 0:
        empirical_price_error = anchor_price * error_pct / 100.0
    proxy = empirical_price_error <= 0
    if proxy:
        empirical_price_error = max(atr * 0.55, abs(anchor_price) * 0.00018)
    return {
        "median_abs_error_price": float(empirical_price_error),
        "median_abs_error_pct": float(empirical_price_error / max(abs(anchor_price), 1e-12) * 100.0),
        "direction_accuracy_pct": direction_accuracy,
        "samples": sample_count,
        "is_proxy": proxy,
    }


def calibrate_projection_bundle(
    market_data: pd.DataFrame,
    *,
    red: pd.DataFrame | None = None,
    yellow: pd.DataFrame | None = None,
    blue: pd.DataFrame | None = None,
    horizon: int = 6,
    bt_history: pd.DataFrame | None = None,
    bt_summary: Dict[str, Any] | None = None,
    regime_reliability: float | None = None,
) -> Dict[str, Any]:
    """Return calibrated main/red/yellow/blue paths and empirical bands.

    The main path is a reliability-weighted consensus of existing paths plus a
    small robust market prior.  Bands expand with empirical error, robust ATR,
    horizon and disagreement; they never narrow at a later horizon.
    """
    market = _prepare_market(market_data)
    if market.empty or len(market) < 8:
        return {"ok": False, "message": "Need clean timestamped OHLC data."}
    horizon = int(max(1, min(int(horizon or 6), 96)))
    anchor_price = float(market["close"].iloc[-1])
    anchor_time = pd.Timestamp(market["time"].iloc[-1])
    delta = _bar_delta(market)
    future_times = pd.Series([anchor_time + delta * step for step in range(1, horizon + 1)])

    close = market["close"].astype(float)
    returns = close.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    true_range = (market["high"] - market["low"]).abs().replace(0, np.nan).dropna()
    atr = float(true_range.tail(96).median()) if not true_range.empty else abs(anchor_price) * 0.00035
    if not math.isfinite(atr) or atr <= 0:
        atr = abs(anchor_price) * 0.00035
    robust_vol = float(returns.tail(240).std()) if len(returns) else 0.0
    if not math.isfinite(robust_vol) or robust_vol <= 0:
        robust_vol = max(atr / max(abs(anchor_price), 1e-12), 1e-7)

    red_path = _source_path(red if isinstance(red, pd.DataFrame) else pd.DataFrame(), name="red_raw", horizon=horizon, future_times=future_times, anchor_price=anchor_price)
    yellow_path = _source_path(yellow if isinstance(yellow, pd.DataFrame) else pd.DataFrame(), name="yellow_raw", horizon=horizon, future_times=future_times, anchor_price=anchor_price)
    blue_path = _source_path(blue if isinstance(blue, pd.DataFrame) else pd.DataFrame(), name="blue_raw", horizon=horizon, future_times=future_times, anchor_price=anchor_price)

    base = pd.DataFrame({"step": np.arange(1, horizon + 1), "time": future_times})
    for source_frame in (red_path, yellow_path, blue_path):
        if not source_frame.empty:
            base = base.merge(source_frame.drop(columns=["time"], errors="ignore"), on="step", how="left")

    # Robust deterministic prior from existing market data only.
    ret6 = float(returns.tail(6).median()) if len(returns) else 0.0
    ret24 = float(returns.tail(24).median()) if len(returns) else ret6
    ema_fast = close.ewm(span=min(12, max(3, len(close) // 5)), adjust=False).mean()
    ema_slow = close.ewm(span=min(48, max(8, len(close) // 2)), adjust=False).mean()
    trend_gap = float((ema_fast.iloc[-1] - ema_slow.iloc[-1]) / max(abs(anchor_price), 1e-12))
    prior_drift = np.clip(ret6 * 0.42 + ret24 * 0.28 + trend_gap / 180.0, -robust_vol * 1.35, robust_vol * 1.35)
    prior_values = []
    previous = anchor_price
    for step in range(1, horizon + 1):
        drift = float(prior_drift) * (0.94 ** (step - 1))
        candidate = previous * (1.0 + drift)
        max_step = max(atr * 1.35, abs(anchor_price) * robust_vol * 2.2)
        candidate = previous + float(np.clip(candidate - previous, -max_step, max_step))
        prior_values.append(candidate)
        previous = candidate
    base["market_prior"] = prior_values

    error = _backtest_error(
        bt_history if isinstance(bt_history, pd.DataFrame) else pd.DataFrame(),
        bt_summary if isinstance(bt_summary, dict) else {},
        anchor_price=anchor_price,
        atr=atr,
    )
    dir_acc = error.get("direction_accuracy_pct")
    error_score = 1.0 - min(error["median_abs_error_price"] / max(atr * 2.2, 1e-12), 1.0)
    direction_score = 0.5 if dir_acc is None else _clip((float(dir_acc) - 45.0) / 20.0, 0.0, 1.0)
    sample_score = min(float(error["samples"]) / 80.0, 1.0)
    regime_score = _clip((regime_reliability if regime_reliability is not None else 55.0) / 100.0, 0.0, 1.0)
    reliability = 100.0 * (0.38 * error_score + 0.28 * direction_score + 0.18 * sample_score + 0.16 * regime_score)
    if error["is_proxy"]:
        reliability = min(reliability, 58.0)
    reliability = _clip(reliability, 25.0, 92.0)

    weights = {"red_raw": 0.44, "yellow_raw": 0.27, "blue_raw": 0.17, "market_prior": 0.12}
    available = [column for column in weights if column in base.columns and base[column].notna().any()]
    if not available:
        available = ["market_prior"]
    weight_sum = sum(weights[column] for column in available)
    normalized_weights = {column: weights[column] / weight_sum for column in available}

    main_values = []
    spread_values = []
    previous = anchor_price
    for _, row in base.iterrows():
        candidates = []
        candidate_weights = []
        for column in available:
            value = _finite(row.get(column), float("nan"))
            if math.isfinite(value):
                candidates.append(value)
                candidate_weights.append(normalized_weights[column])
        if not candidates:
            candidates = [_finite(row.get("market_prior"), previous)]
            candidate_weights = [1.0]
        total = sum(candidate_weights) or 1.0
        consensus = sum(v * w for v, w in zip(candidates, candidate_weights)) / total
        spread = float(np.std(candidates)) if len(candidates) > 1 else 0.0
        # Low reliability shrinks farther-horizon movement toward the market prior
        # and current anchor rather than pretending to know an exact price.
        step = int(row["step"])
        reliability_factor = 0.42 + reliability / 100.0 * 0.48
        horizon_shrink = 1.0 / (1.0 + max(0, step - 1) * (1.0 - reliability / 100.0) * 0.055)
        target = anchor_price + (consensus - anchor_price) * reliability_factor * horizon_shrink
        prior = _finite(row.get("market_prior"), target)
        target = target * 0.88 + prior * 0.12
        max_step = max(atr * (1.25 + 0.05 * math.sqrt(step)), abs(anchor_price) * robust_vol * 2.1)
        target = previous + float(np.clip(target - previous, -max_step, max_step))
        main_values.append(target)
        spread_values.append(spread)
        previous = target
    base["main_path"] = main_values
    base["source_spread"] = spread_values

    line_factor = 0.50 + reliability / 100.0 * 0.30
    for raw_column, calibrated_column in (
        ("red_raw", "red_path"),
        ("yellow_raw", "yellow_path"),
        ("blue_raw", "blue_path"),
    ):
        if raw_column in base.columns:
            raw_values = pd.to_numeric(base[raw_column], errors="coerce")
            base[calibrated_column] = base["main_path"] + (raw_values - base["main_path"]) * line_factor
        else:
            base[calibrated_column] = np.nan

    empirical = max(float(error["median_abs_error_price"]), atr * 0.38, abs(anchor_price) * robust_vol * 0.65)
    widths = []
    previous_width = 0.0
    for _, row in base.iterrows():
        step = int(row["step"])
        disagreement = _finite(row.get("source_spread"), 0.0)
        uncertainty = 1.0 + (1.0 - reliability / 100.0) * 0.85
        width = empirical * (0.95 + 0.42 * math.sqrt(step)) * uncertainty + disagreement * 0.75
        width = max(width, atr * (0.52 + 0.18 * math.sqrt(step)))
        width = max(width, previous_width * 1.015)
        widths.append(width)
        previous_width = width
    base["band_width"] = widths
    base["upper_band"] = base["main_path"] + base["band_width"]
    base["lower_band"] = base["main_path"] - base["band_width"]

    source_columns = [c for c in ("red_raw", "yellow_raw", "blue_raw") if c in base.columns]
    agreement = 100.0
    if source_columns:
        normalized_spread = float(base["source_spread"].mean() / max(atr, 1e-12))
        agreement = _clip(100.0 - normalized_spread * 32.0, 0.0, 100.0)
    coverage_proxy = _clip(50.0 + reliability * 0.42 + min(error["samples"], 80) * 0.10, 50.0, 94.0)

    main = base[["step", "time", "main_path", "upper_band", "lower_band", "band_width", "source_spread"]].copy()
    red_out = base[["step", "time", "red_path"]].dropna(subset=["red_path"]).copy()
    yellow_out = base[["step", "time", "yellow_path"]].dropna(subset=["yellow_path"]).copy()
    blue_out = base[["step", "time", "blue_path"]].dropna(subset=["blue_path"]).copy()

    summary = {
        "version": CALIBRATION_VERSION,
        "reliability_pct": round(reliability, 2),
        "path_agreement_pct": round(agreement, 2),
        "estimated_band_coverage_pct": round(coverage_proxy, 2),
        "median_abs_error_pct": round(float(error["median_abs_error_pct"]), 6),
        "error_samples": int(error["samples"]),
        "error_is_proxy": bool(error["is_proxy"]),
        "direction_accuracy_pct": None if dir_acc is None else round(float(dir_acc), 2),
        "atr_price": round(float(atr), 8),
        "sources_used": [column.replace("_raw", "") for column in available if column != "market_prior"] + ["market_prior"],
        "anchor_time": str(anchor_time),
        "anchor_price": round(anchor_price, 6),
    }
    return {
        "ok": True,
        "main": main,
        "red": red_out,
        "yellow": yellow_out,
        "blue": blue_out,
        "raw": base,
        "summary": summary,
    }


def calibrated_candles(bundle: Dict[str, Any], *, anchor_price: float) -> pd.DataFrame:
    """Convert a calibrated main path into the project's predicted OHLC schema."""
    if not isinstance(bundle, dict) or not bundle.get("ok"):
        return pd.DataFrame()
    main = bundle.get("main")
    if not isinstance(main, pd.DataFrame) or main.empty:
        return pd.DataFrame()
    rows = []
    previous = float(anchor_price)
    for _, row in main.iterrows():
        close = _finite(row.get("main_path"), previous)
        upper = _finite(row.get("upper_band"), max(previous, close))
        lower = _finite(row.get("lower_band"), min(previous, close))
        rows.append({
            "time": pd.Timestamp(row.get("time")),
            "open": round(previous, 6),
            "high": round(max(previous, close, upper), 6),
            "low": round(min(previous, close, lower), 6),
            "close": round(close, 6),
            "prediction_step": int(row.get("step", len(rows) + 1)),
            "candle_type": "CALIBRATED_POWERBI_FUTURE",
            "Upper Band": round(upper, 6),
            "Lower Band": round(lower, 6),
            "Calibration Version": CALIBRATION_VERSION,
        })
        previous = close
    return pd.DataFrame(rows)
