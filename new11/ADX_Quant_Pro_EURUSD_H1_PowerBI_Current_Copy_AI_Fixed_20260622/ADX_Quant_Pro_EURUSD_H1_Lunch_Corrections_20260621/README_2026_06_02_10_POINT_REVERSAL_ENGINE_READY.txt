10-POINT REVERSAL EARLY WARNING ENGINE READY ZIP
================================================

Added additive upgrade without deleting original logic:

1) Home top Reversal Early Warning Engine
   - Compares previous hour vs latest loaded hour from shared dataframe.
   - Shows warning when at least 5/10 thresholds are active.
   - Shows red/blue danger banner when 7/10 thresholds are active.

2) Doo Prime Analysis > Finder integration
   - Finder selected day/hour now recalculates the same 10 reversal drivers.
   - Metrics change when the Finder calendar date/hour changes.
   - Includes 10 st.metric cards in one section.
   - Includes threshold table and JSON delta details.

3) 10 reversal drivers added
   - Direction Rotation
   - Kurtosis Explosion
   - Sell -> Buy Flip
   - Rising Efficiency Jump
   - Fat Tail Z Expansion
   - Buy Ratio Increase
   - Sell Ratio Decrease
   - Trust Confirmation
   - DVE Rotation
   - Reversal Strength Score

4) Alert rules
   - 0-4 active = normal
   - 5+ active = possible reversal warning
   - 7+ active = important reversal danger banner

5) Copy/export
   - Finder copy export now includes the 10-point reversal engine.
   - Home copy payload includes the last reversal engine state.
   - Existing mobile-safe copy button remains restored.

Files changed:
- tabs/home_split/doo_prime_deep.py
- tabs/home_split/legacy/implementation.py

Run:
streamlit run main.py
