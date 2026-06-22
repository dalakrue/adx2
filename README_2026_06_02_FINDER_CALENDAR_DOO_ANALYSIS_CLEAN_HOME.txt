Finder Calendar Doo Analysis + Clean Home Upgrade - 2026-06-02

Main fixes
1. Finder is no longer a simple candle table only.
2. Finder now uses a calendar date picker plus selected-hour/full-day mode.
3. Finder recalculates the same Doo Prime Analysis metrics for the chosen period:
   - price / 10s / 1m / 10m movement
   - fat-tail z and kurtosis
   - DVE / directional efficiency
   - rising efficiency
   - falling efficiency
   - trust scale
   - trend direction
   - market regime
   - combined score
4. Finder keeps raw OHLC candles in deep-analysis results so date/hour replay does not lose open/high/low/close structure.
5. Finder includes:
   - same-as-Doo metric table
   - exact Doo metric cards for selected frame
   - 24-hour calendar scan for full-day mode
   - candle reaction summary
   - current basket P/L exit gate comparison
   - copy button for the selected calendar analysis
6. Home tab is cleaned so duplicate panels no longer stack on top of each other.
7. Old Home modules are preserved in the project but not repeatedly rendered in the clean launcher.

Files changed
- tabs/home_split/doo_prime_deep.py
- tabs/home_split/legacy/implementation.py

Run
1. Extract the ZIP.
2. Open PowerShell in the extracted new7 folder.
3. Run:
   pip install -r requirements.txt
   streamlit run main.py

How to use Finder
1. Open Home.
2. Open Doo Prime Analysis.
3. Press Refresh All 4 Now if you want fresh deep data, or use already-loaded shared data.
4. Choose Finder.
5. Pick the date with the calendar.
6. Choose Selected hour or Full day.
7. Read the same metrics that Doo Prime Analysis shows: Fat Tail, DVE, Rising/Falling Eff, Trust, Regime, speed, and candle summary.
