V13 LOCKED TABLE COLLECTION FIX

What changed:
1. Home still shows 25D 10-Reversal history scan in open/close fields.
2. Home now also shows today's all-hours reversal-decision table in an open/close field.
3. Finder still shows the selected day and all reversal decisions for that day.
4. "Locked" now means anti-repaint memory, not hiding/removing history:
   - once an hour row is calculated after that hour closes, it is saved to data/reversal_locked_v13.csv
   - future candles/refreshes reuse the saved row for that date/hour
   - new closed hours are appended
5. The locked tables keep used_future_rows = 0 and use the causal V12 no-future reversal calculation.

Main files changed:
- tabs/home_split/doo_prime_deep.py
- tabs/home_split/v13_locked_history_tables_patch.py

Run:
streamlit run main.py
