LAST TIME >= 7/10 25-DAY SCAN FIX
==================================

Fixed file:
- tabs/home_split/doo_prime_deep.py

What changed:
1. Home metric no longer shows useless "Not found" when no exact >=7/10 hour is found.
2. Added _loaded_reversal_history_df(): uses loaded Home/sidebar/Doo Prime dataframe and limits scan from current loaded day back 25 days.
3. Added _reversal_pair_for_target():
   - M1/M5-like data: compares previous 1 hour vs selected hour.
   - H1/sparse data: compares previous candle block vs next/current candle block, so the metric still works with H1 data.
4. Upgraded _find_last_reversal_threshold_time():
   - Scans today back through last 25 days.
   - Finds the most recent hour where score >= 7/10.
   - Adds exact day + hour labels, e.g. Tue 2026-06-02 16:00.
   - If no >=7/10 exists in loaded data, shows the best scanned hour instead of "Not found".
5. Added Home expander:
   - day
   - hour
   - score
   - probability
   - weighted score
   - scan rows
   - scan mode
   - full driver threshold table

Important:
- To truly scan 25 days on M1, the app must load around 36,000+ M1 candles.
- If only 600 candles are loaded, the scan uses those loaded candles and shows the best available result.
- If H1 data is loaded, the fix uses H1 block comparison instead of failing because each hour only has one candle.
