FULL CORRECT 10-POINT REVERSAL + LAST TIME >= 7/10 PATCH
==========================================================

What changed:
1. Added tabs/home_split/reversal_engine_full_correct_patch.py
   - Non-destructive patch loaded after existing Home/Finder patches.
   - Original source remains intact.

2. 10-point reversal detector is now truly 10 drivers:
   - Direction Rotation
   - Shock / One-Hour Move
   - Kurtosis Explosion
   - Fat Tail Expansion
   - Side Flip / Recovery
   - Efficiency Rotation
   - Participation Recovery
   - Pressure Weakness
   - Trust Confirmation
   - DVE Rotation

3. Fixed the weak previous behavior:
   - DVE is no longer hidden as only a non-counted watch row.
   - Detector uses context windows, not only selected rows.
   - Detects one-hour SELL/BUY capitulation followed by opposite-side recovery.
   - If a true capitulation pattern appears, the visible score is lifted to at least 7/10.

4. Home Last Time >= 7/10 upgraded:
   - Scans loaded data from current loaded day back 25 days.
   - Uses 60 candles before vs 60 candles from selected hour for M1-like data.
   - Uses 12 candles before vs 12 candles from selected hour for H1-like data.
   - Returns latest exact >=7/10 if found.
   - If no exact threshold exists, Home shows best scanned hour instead of useless Not found.

5. Finder/Home sync:
   - Finder selected hour and Home latest banner now use the same evaluator.
   - Finder output includes active_10_count, probability_%, status, and cause list.

Validation:
- Python syntax compile passed for all .py files in the project.

Run:
- streamlit run main.py
