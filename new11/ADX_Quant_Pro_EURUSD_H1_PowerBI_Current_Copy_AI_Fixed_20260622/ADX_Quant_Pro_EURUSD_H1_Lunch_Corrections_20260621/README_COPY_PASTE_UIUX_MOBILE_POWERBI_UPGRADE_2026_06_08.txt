COPY / PASTE UPGRADE FORM — UIUX + MOBILE + LUNCH DATA + POWER BI VISUALS

What was upgraded:
1. Copy buttons
   - Beautiful glass blue/teal UI.
   - Phone-safe pointer/touch/click handlers.
   - Secure clipboard first, textarea fallback second.
   - Better status messages: Ready, Copied, or fallback warning.

2. Mobile app reliability
   - Copy buttons now work inside Streamlit iframe on phones.
   - Buttons use touch-action manipulation and passive:false touch handlers.
   - Sidebar close behavior remains called from Lunch/Data Visualization tab clicks.

3. Lunch data reliability/efficiency
   - Lunch copy export remains cached and invalidates on refresh/calculation changes.
   - Data Visualization uses cleaned, sorted, de-duplicated OHLC data.
   - Added richer BI export fields without changing original metric/engine code.

4. Advanced Power BI-style Data Visualization
   - Added trend-gap percentage.
   - Added volume anomaly z-score when volume exists.
   - Added volatility risk bucket.
   - Added session-hour return heatmap.
   - Added trend-vs-volatility risk scatter map.
   - Added risk bucket distribution chart.
   - Added volume anomaly / trend gap chart.
   - Existing original charts remain: price/trend/projection, rolling volatility, bias mix, latest BI table.

Files changed:
- core/pro_terminal_uiux.py
- core/legacy_impl/global_upgrade_impl.py
- tabs/home.py
- tabs/account_split/legacy/implementation.py

How to use:
1. Copy these files into your project, replacing the same paths.
2. Run:
   python -m compileall -q .
3. Start the app:
   streamlit run main.py
4. On phone:
   - open Lunch
   - press Run Calculating
   - press Copy Necessary or Copy Full Export
   - open Data Visualization
   - press Build / Refresh Visual Dashboard

Safety:
- This is additive/non-destructive UIUX + visualization upgrade.
- It does not change trading orders, connector login, or original decision engine math.
