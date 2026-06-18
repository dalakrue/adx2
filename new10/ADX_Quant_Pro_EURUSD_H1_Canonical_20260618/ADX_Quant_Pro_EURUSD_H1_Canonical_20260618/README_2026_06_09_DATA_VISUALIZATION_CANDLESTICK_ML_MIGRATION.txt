DATA VISUALIZATION CANDLESTICK + ML MIGRATION — 2026-06-09

Updated area:
- Data Visualization inner tab in the Home/Lunch workflow.

What changed:
1. The first/main Data Visualization section is now:
   Advanced Power BI Price Candlestick + ML Projection.
2. The main candlestick section shows actual OHLC candles first, with blue predicted future candles, a light-blue current-hour predicted path, and rolling ML projection history.
3. Other panels are now folded into open/close fields below the main candlestick section:
   - Original PowerBI + ML Projection
   - Prediction vs Actual
   - Smooth Regime
   - Copy Export
4. Heavy calculation no longer runs automatically just because data signature changes.
   It runs only after pressing:
   Run Candlestick + ML Projection
5. Rows used from Lunch/Data Visualization were expanded up to 20,000 rows so the migrated candlestick + ML projection can use more of the loaded Lunch/shared data while still staying bounded for phone/RAM safety.

Files patched:
- tabs/home_parts/part_002.py
- tabs/home_parts/part_004.py
- tabs/home_parts/part_005.py
- tabs/home_split/home.py mirror text updated for consistency

Validation:
- Python syntax compile passed for main.py, adx_dashpoard.py, and tabs/home.py.
- Combined Home split SOURCE compile passed.
