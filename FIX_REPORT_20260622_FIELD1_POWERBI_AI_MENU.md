# Fix Report — 2026-06-22 Field 1 / PowerBI / AI / Menu

Fixed user-reported issues from screenshots:

1. Lunch Field 1 stale hour display
   - Field 1 now uses the freshest completed H1 timestamp from canonical, market freshness, and already-loaded OHLC frames.
   - If the Full Metric history cache is older than the current loaded candle, Field 1 prepends display-only current rows from already-published market/priority data.
   - No protected calculation is started from Field 1.

2. Field 1 table column placement
   - Decision / Direction columns are moved beside Hour for phone readability.

3. Power BI Field 2 metric cards
   - Probability above/below current now falls back to the published path when explicit probability fields are missing.
   - TP/SL touch probability now falls back to selected TP/SL and the published path when direct fields are missing.
   - Risk cards show bounded neutral/current values instead of half-empty unavailable text where possible.

4. AI Assistant Field 5 relevance
   - Added local related-answer layer for bias, regime, TP/SL, risk, confidence, latest candle/time, and explanation questions.
   - The answer uses current canonical, compact summary, and fact-pack data only.
   - No external AI API or heavy model is used.

5. Menu duplicate copy controls
   - Removed the duplicate Copy drawer section.
   - Kept one visible menu copy area with Copy Short and Copy Full buttons.

Validation:
- Full Python compile check passed for project files.
