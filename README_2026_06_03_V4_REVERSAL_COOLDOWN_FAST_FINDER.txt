2026-06-03 V4 REVERSAL COOLDOWN + QUALITY UPGRADE
===================================================

What changed
------------
1) Reversal Cooldown
   - After one 7+/10 signal fires, the next 4 hours are blocked in the 25D/Finder scan.
   - Example: 08:00 9/10, 09:00 blocked, 10:00 blocked, 11:00 blocked, 12:00 can count again.

2) Require Trend Before Reversal
   - If the old move has no trend structure, final danger score is capped at 6/10.
   - Uses available snapshot evidence: ADX if present, DVE, rising/falling efficiency, and BUY/SELL dominance.

3) Minimum Move Quality Filter
   - Tiny move signals are demoted.
   - Requires meaningful move/fat-tail displacement proxy; otherwise score is reduced by 2.

4) Reversal Persistence
   - Requires after-window direction persistence proxy from BUY/SELL participation or trust.
   - Weak one-candle flips are capped at 6/10.

5) Exhaustion Quality Score
   - Adds exhaustion_score 0-100.
   - 8+/10 now requires exhaustion_score >= 70.

6) Consecutive Signal Compression
   - Repeated 7+/10 rows become one REVERSAL ZONE with Peak Score.
   - History table now includes: cooldown_blocked, compressed_zone, zone_peak_score, count_as_reversal.

Performance improvement
-----------------------
- Finder and Doo Prime modeling now reuse cached collected candles and feature tables during tab switching.
- It avoids repeated heavy dataframe rebuilds when opening Finder/Data Modeling inner tabs.

Files changed
-------------
- tabs/home_split/doo_prime_deep.py
- tabs/home_split/reversal_cooldown_quality_upgrade.py

How to run
----------
streamlit run main.py
