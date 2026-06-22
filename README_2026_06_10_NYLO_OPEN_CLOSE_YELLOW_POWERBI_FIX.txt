2026-06-10 NY/London Open-Close + Yellow PowerBI Prediction Fix

Changed:
1. NY/London overlap no longer renders from the shared Data Visualization copy bar.
2. NY/London overlap is now a separate Open / Close field in Lunch:
   "Open / Close — NY + London Overlap Hour Metrics"
3. It has its own Run NY/London Overlap Calculation button.
4. It does NOT calculate when the tab opens.
5. History is one row per overlap hour, not one row per day.
6. It shows today to last 25 days descending.
7. Added Entry Pressure /10, BUY Pressure /10, SELL Pressure /10, Score /10.
8. Full copy export includes the manually calculated hourly overlap history only after run.
9. Data Visualization PowerBI section now adds:
   "Open / Close — Last 2 Days Hourly Prediction vs Actual"
   with yellow predicted close markers over actual candlesticks.
10. The yellow section includes hit rate, average close error in pips, latest predicted direction, and an hourly table.

Safety:
- Manual-run only for heavy sections.
- DataFrame operations are bounded to reduce phone RAM/CPU usage.
- Added safe fallbacks so missing OHLC data shows a warning instead of crashing.
