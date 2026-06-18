2026-06-09 Reliable Data Visualization + Copy Button Patch

What changed:
1. Data Visualization tab
   - Added runtime-safe override after the split-file loader.
   - Keeps original PowerBI + ML Projection available in an Open / Close expander.
   - Adds a second PowerBI-style candlestick chart with future BLUE candles.
   - Uses manual Run button only, so heavy ML/candlestick projection does not auto-run.
   - Uses clean OHLC normalization, duplicate-time removal, sorted time, and minimum 120-candle data-quality gate.

2. Copy buttons
   - Lunch tab keeps 2 copy buttons: Copy Necessary and Copy Full Export.
   - Data Visualization tab has 1 compact copy button.
   - Full Lunch and Data Visualization copy exports now include current/new projection data but exclude heavy history rows to reduce copy lines.
   - Excluded: 25D history/reversal scan rows, full prediction-vs-actual history rows, rolling projection history rows, account/order/deal history rows.

3. Button UI/UX
   - Added lighter but readable active/focus button styles.
   - Fixes the problem where clicked buttons become too white and text becomes hard to see.

Files added:
- tabs/home_patch_20260609.py
- core/pro_terminal_uiux_patch_20260609.py

Files updated:
- tabs/home.py
- core/pro_terminal_uiux.py

Validation:
- Python compileall passed for tabs/, core/, main.py, and adx_dashpoard.py.
