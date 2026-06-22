2026-06-03 HOME + FINDER 10-REVERSAL HISTORY UPGRADE
======================================================

WHAT CHANGED
------------
1) Home tab
   - Old st.metric-only "Best Time in 25D Scan" is replaced by an open/close field:
     "Open 25D 10-Reversal History Scan Table".
   - It scans today back 25 loaded days.
   - It shows every hour where the 10-reversal decision reached 7/10 or higher.
   - It also includes a full hourly scan table so "Not Found" is no longer a dead result;
     if no 7/10 exists, you can still see the best 5/10 or 6/10 hours.
   - Added threshold-style table similar to your screenshot:
     Safety %, ADX/Trend Proxy, Pressure, Mean Revert Risk %, Fat Tail Risk %,
     Spoofing Risk %, Ergodicity %, Monte Carlo %, ML Confidence %, History Match %.

2) Finder tab
   - Deleted hour chooser.
   - Deleted selected-hour/full-day mode selector.
   - Finder now only asks for day.
   - After you choose a day, Finder scans every loaded hour in that day.
   - It shows all 7/10+ 10-reversal decisions for that day, not only one hour.
   - It still keeps same-as-Doo metric table, candle preview, basket model, and copy button.

3) Calculation logic
   - Home and Finder use the same 10-point reversal engine.
   - The scan uses before-window + target-hour/window + after-context logic,
     so it is more reliable than judging only selected rows.
   - Strongest hour for the selected day is shown with full 10-driver details.

FILES ADDED / CHANGED
---------------------
ADDED:
- tabs/home_split/home_finder_reversal_history_upgrade.py

CHANGED:
- tabs/home_split/doo_prime_deep.py
  It now installs the new non-destructive patch after the previous reversal patch.

HOW TO RUN
----------
1) Extract this ZIP.
2) Open PowerShell in the extracted new7 folder.
3) Run:
   streamlit run main.py

NOTES
-----
- This patch does not delete the original code. It wraps/overrides the UI functions at runtime.
- If only a small amount of M1/H1 data is loaded, the scan can only evaluate those loaded hours.
- For best 25D scan, load enough M1 candles from MT5/Doo Prime or your data source.
