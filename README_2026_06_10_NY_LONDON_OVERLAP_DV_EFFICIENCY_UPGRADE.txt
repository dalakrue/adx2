2026-06-10 Upgrade

Added safely through tabs/home_patch_20260609.py:

1. Lunch tab
- New section appears before Copy Center:
  "NY–London Overlap Metric Duplicate"
- Uses only EURUSD overlap-hour candles.
- Shows today to last 25 days descending.
- Table includes scores out of 10:
  Range Power, Trend Efficiency, BUY Align, SELL Align, Risk, Overlap Master.
- Top st.metric cards show Today Overlap, Today Bias, Today Risk, 25D Avg, 25D Best Bias.

2. Copy Full Export
- Full copy now includes:
  ny_london_overlap_summary
  ny_london_overlap_history_today_to_last_25d_desc
  data_visualization_efficiency_summary

3. Data Visualization tab
- Added top st.metric efficiency cards:
  Notice Efficiency /10
  Projection Quality /10
  Data Quality /10
  Model Risk /10
  Action Read
- Metrics calculate from the Data Visualization tab result, ML summary, prediction confidence, backtest accuracy, regime summary, and rows used.

4. Safety/error fixes
- All new renderers are guarded with try/except.
- If OHLC/time data is missing, the app displays a warning instead of crashing.
- No connector/order/trading logic was changed.

Run:
streamlit run adx_dashpoard.py
