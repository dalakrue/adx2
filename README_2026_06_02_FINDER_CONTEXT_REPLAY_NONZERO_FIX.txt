Finder Context Replay Non-Zero Fix - 2026-06-02

Problem fixed:
- Finder selected-hour metrics became all 0 / N/A because the old replay calculated Doo Prime analytics from only the selected hour.
- For H1, selected hour usually equals 1 candle, so DVE, Rising/Falling Efficiency, Fat Tail, Trust, 10s/1m/10m movement and score had no enough history.

What changed:
1. Finder still uses the exact selected day/hour for candle reaction and copy export.
2. Finder metric cards/table now use a lookback context ending at the selected hour, up to 720 prior candles per frame.
3. Added robust Finder replay analytics for:
   - price
   - 10s_%, 1m_%, 10m_% style movement using candle-count context
   - fat_tail_z
   - kurtosis
   - DVE %
   - rising_eff_%
   - falling_eff_%
   - trust_%
   - direction
   - regime
4. Metric table now shows selected_rows and context_rows so you can see both the exact selected period and how much history the analytics used.
5. Full-day 24-hour scan now uses the full day/context instead of recalculating from an isolated one-hour slice.
6. Original code and UI are preserved; only Finder replay logic was upgraded.

How to use:
- Open Home -> Doo Prime Analysis -> Finder.
- Choose day and hour.
- Check selected_rows vs context_rows.
- If context_rows is large, Finder metrics should no longer be all 0.
