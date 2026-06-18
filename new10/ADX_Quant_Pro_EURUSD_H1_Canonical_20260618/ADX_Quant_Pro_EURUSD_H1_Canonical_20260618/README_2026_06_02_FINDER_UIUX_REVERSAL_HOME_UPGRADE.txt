2026-06-02 Finder UIUX + 10 Reversal Home Upgrade
==================================================

What changed:
1. Added tabs/home_split/finder_uiux_upgrade.py
   - Finder Pro Replay glass UI.
   - Animated pop-up alert cards.
   - Mobile-friendly metric-card CSS.
   - Non-destructive wrappers around the existing Finder renderer.

2. Patched tabs/home_split/doo_prime_deep.py
   - Loads the upgrade after the existing split legacy source executes.
   - Keeps original code intact and only overrides focused functions at runtime.

3. Reversal 10 detector improvement
   - More sensitive to the exact failure pattern: strong SELL/capitulation hour -> fat-tail/kurtosis shock -> buyer participation recovery.
   - Detects danger even when after-window buy ratio is only around 38-45%, so the 16:00 -> 17:00 reversal case should no longer show as fully normal.
   - DVE Rotation now contributes as a confirmation instead of only watch text.
   - If a capitulation pattern is detected, visible score is lifted to at least 7/10.

4. Home tab compatibility
   - Existing Home Reversal banner still uses evaluate_latest_reversal_engine/render_reversal_home_banner from Doo Prime deep module.
   - Because the evaluator is patched globally, Home and Finder use the same upgraded 10-point logic.

How to run:
   pip install -r requirements.txt
   streamlit run main.py

