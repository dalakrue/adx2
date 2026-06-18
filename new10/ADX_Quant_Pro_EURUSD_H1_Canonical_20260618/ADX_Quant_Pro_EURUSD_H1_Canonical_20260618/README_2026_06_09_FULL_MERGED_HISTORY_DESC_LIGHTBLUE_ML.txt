2026-06-09 FULL MERGED UPGRADE

Merged into tabs/home.py:
1. History/detail tables display newest/current records first when a time/date column exists.
2. Data Visualization Pro++ candle chart now shows last 10 continuous days of actual candles.
3. Added light-blue current-hour ML predicted path from latest actual candle into future predicted candles.
4. Added rolling ML projection history for the last 10 continuous days, recalculated through time.
5. Blue predicted future candle table is shown newest first for copy/export review.
6. Prediction-vs-actual and regime history tables are forced newest first.
7. Copy export now includes:
   - light_blue_current_hour_path
   - last_10_continuous_days_dynamic_projection_history
   - future_blue_predicted_candles
   - prediction_backtest_summary
   - smooth_regime_summary

Validation completed:
- python -m py_compile tabs/home.py
- python -m compileall -q project

Notes:
- Prediction paths are directional analysis only, not guaranteed price.
- The upgrade is additive and preserves existing tabs and original PowerBI/ML renderer.
