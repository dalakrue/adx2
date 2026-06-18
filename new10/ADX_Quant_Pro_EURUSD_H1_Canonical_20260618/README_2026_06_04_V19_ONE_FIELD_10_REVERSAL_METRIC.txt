V19 ONE-FIELD 10-REVERSAL METRIC UPGRADE

What changed:
1. Added one compact st.metric below/near the 10-Reversal title:
   - Now / Prev / Prev-Prev 10-Reversal score
   - Difference: now-prev and prev-prevprev
   - Ratio: now/prev and prev/prevprev
   - Derivative change: current difference minus previous difference
   - Mean deviation: now minus the 3-point mean

2. Home 10-Reversal display is cleaner:
   - Main title metrics stay visible.
   - Long locked tables are grouped into one Open / Close field.
   - Current threshold + engine detail is grouped into one Open / Close field.

3. Finder 10-Reversal display is cleaner:
   - Finder selected-period reversal detail is grouped into one Open / Close field.
   - Finder locked scan table is grouped into one Open / Close field.

4. Original calculation is preserved:
   - No old 10-Reversal scoring engine was replaced.
   - This patch only wraps display and adds derived metric summaries.

Files changed:
- tabs/home.py
- tabs/home_split/doo_prime_deep.py
- tabs/home_split/v19_one_field_reversal_metric_patch.py

Run:
streamlit run main.py
