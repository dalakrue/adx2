from __future__ import annotations

import numpy as np
import pandas as pd

from core.powerbi_path_calibration_20260617 import calibrate_projection_bundle, calibrated_candles


def _market(rows: int = 240) -> pd.DataFrame:
    time = pd.date_range("2026-06-01", periods=rows, freq="h")
    drift = np.linspace(0.0, 0.0035, rows)
    wave = np.sin(np.arange(rows) / 7.0) * 0.00025
    close = 1.155 + drift + wave
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({
        "time": time,
        "open": open_,
        "high": np.maximum(open_, close) + 0.00018,
        "low": np.minimum(open_, close) - 0.00018,
        "close": close,
    })


def test_calibration_invariants_with_three_existing_paths() -> None:
    market = _market()
    anchor = float(market["close"].iloc[-1])
    future = pd.date_range(market["time"].iloc[-1] + pd.Timedelta(hours=1), periods=6, freq="h")
    red = pd.DataFrame({"time": future, "open": anchor, "Predicted Close": anchor + np.arange(1, 7) * 0.00008})
    yellow = pd.DataFrame({"time": future, "anchor_price": anchor, "path": anchor + np.arange(1, 7) * 0.00005})
    blue = pd.DataFrame({"time": future, "anchor_price": anchor - 0.0001, "path": anchor - 0.0001 + np.arange(1, 7) * 0.00004})
    actual = anchor + np.arange(1, 31) * 0.00001
    bt = pd.DataFrame({"Actual Close": actual, "Pred Close": actual - 0.00006})

    bundle = calibrate_projection_bundle(
        market, red=red, yellow=yellow, blue=blue, horizon=6,
        bt_history=bt, bt_summary={"direction_accuracy_pct": 62.0}, regime_reliability=74.0,
    )

    assert bundle["ok"] is True
    main = bundle["main"]
    assert len(main) == 6
    assert (main["upper_band"] >= main["main_path"]).all()
    assert (main["main_path"] >= main["lower_band"]).all()
    assert (main["band_width"].diff().dropna() >= 0).all()
    assert 25.0 <= bundle["summary"]["reliability_pct"] <= 92.0
    assert bundle["summary"]["error_samples"] == 30

    candles = calibrated_candles(bundle, anchor_price=anchor)
    assert len(candles) == 6
    assert (candles["high"] >= candles[["open", "close"]].max(axis=1)).all()
    assert (candles["low"] <= candles[["open", "close"]].min(axis=1)).all()


def test_calibration_falls_back_to_market_prior_without_paths() -> None:
    market = _market(120)
    bundle = calibrate_projection_bundle(market, horizon=4)
    assert bundle["ok"] is True
    assert len(bundle["main"]) == 4
    assert bundle["summary"]["error_is_proxy"] is True
    assert "market_prior" in bundle["summary"]["sources_used"]
