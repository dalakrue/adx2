2026-06-15 Home Sidebar + Quick Controls + Red Line full fix

Fixed in this ZIP:
1. Native sidebar no longer starts open. Streamlit page config still uses initial_sidebar_state='collapsed'.
2. Native sidebar backup is not locked off by normal tab clicks anymore, so it can be opened again after close/open cycles.
3. Main Page Menu is duplicated into the native sidebar backup with unique widget keys.
4. Sidebar duplicate controls include navigation, Run, Copy Home Full/Short, RAM cleanup, API/Data, Timer, and Phone/Laptop UI controls.
5. Quick Controls Copy Short / Copy Full now create real copy buttons instead of showing only the old text message.
6. Added top Home Master Controls before tab/menu choice:
   - Run Home Calculation
   - Copy Current Home Full
   - Copy Current Home Short
   - Low RAM cleanup
7. Lunch Red Prediction Line upgraded to full display:
   - red exact/original projection line
   - red smoother error-adjusted line
   - red upper/lower bands
   - yellow latest-current path
   - yellow upper/lower bands
   - blue dotted previous-candle predicted path
   - green alpha difference line between yellow and blue path
   - regime metrics: current regime, regime start, regime end, reliability, avg error, alpha point
8. No new external API, no heavy model, no new prediction engine. The new display uses existing cached PowerBI/projection values or safe OHLC fallback.
9. Existing calculations, tabs, tables, exports, original copy builders, and original PowerBI sections are preserved.

Run:
streamlit run adx_dashpoard.py
