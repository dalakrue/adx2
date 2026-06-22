V27 PHONE SAFE LUNCH / VISUAL / COPY UPGRADE — 2026-06-08

Copy/paste upgrade files changed:
1) tabs/home.py
2) core/pro_terminal_uiux.py

What this fixes:
- Phone freeze when opening Full Metric Details + History.
- Bad undefined `lines` reference in the reversal/history loader after visualization export exists.
- Data Visualization tab now uses ONE advanced Power BI-style dashboard instead of multiple heavy chart blocks.
- Rows are capped and converted to lighter numeric types to reduce RAM.
- Open/Close picture upload field added inside Data Visualization. It stays closed by default because it is important sometimes but useless most times.
- Full Metric Details now opens compact cached details first. It does not call the legacy heavy render_compact_panel on every open/close.
- Added Reduce RAM button in Full Metric Details.
- Home/sidebar Streamlit buttons now get the same premium phone-safe UI style as the copy buttons.
- Copy helper now includes a double-tap guard so mobile taps do not trigger duplicate copy work.

How to use:
- Run Calculating first.
- Open Full Metric Details + History.
- Tap Load Compact Details. Use Max rows shown on phone to control RAM.
- In Data Visualization, upload an optional picture only when needed, then Build / Refresh Visual Dashboard.

Original logic note:
- No trading/order logic is changed.
- The old heavy metric engine result is still used, but the phone UI now displays compact cached details instead of rebuilding heavy history every time.
