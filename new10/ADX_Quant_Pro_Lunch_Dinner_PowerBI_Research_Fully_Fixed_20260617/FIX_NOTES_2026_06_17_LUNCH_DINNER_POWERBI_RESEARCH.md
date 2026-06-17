# Lunch / Dinner / PowerBI / Research UI Upgrade — 2026-06-17

## Completed changes

### Lunch
- Removed the duplicated authoritative 25-day full-metric/regime/NLP table from the Lunch main page.
- Removed the repeated full-detail renderer from the restored Lunch main area.
- Preserved the dedicated **Full Metric Details + History** Lunch subpage and all underlying calculations, caches, copy/export data, and history sources.

### PowerBI Price Prediction Projection
- Added deterministic calibration for the existing red, yellow, and blue projection paths; no new prediction model was introduced.
- Added a reliability-weighted main path based on existing paths, completed prediction-vs-actual residuals, direction accuracy, regime reliability, robust ATR/volatility, and cross-path agreement.
- Rebuilt upper/lower bands from empirical error, disagreement, horizon expansion, and volatility, with non-decreasing uncertainty width.
- Added safe current-anchor correction for stale previous-candle paths while preserving each source path shape.
- Published calibrated path, bands, reliability, agreement, coverage, and calibrated future OHLC to shared session state for synchronized Lunch and Dinner use.
- Preserved the original raw predictions for audit and fallback.

### Dinner
- Replaced the separate **Regime Summary** and **Combine Logic** choices with one **Unified Regime + Logic** choice.
- Dinner now has exactly two navigation choices: **Unified Regime + Logic** and **AI Assistant**.
- Merged synchronized regime, alpha/delta, lifecycle, decision, priority, reliability, NLP, PowerBI, ML, history, and audit displays into one large section with no nested Dinner tabs.
- Grouped all `st.metric` values first and all deduplicated tables afterward.
- Kept legacy route names compatible so old session state opens the new unified page instead of failing.

### Research
- Replaced the circle/radio-style inner selector with a full-width Ant Design segmented workspace selector.
- Added a modern workspace card and full-width button fallback when the optional Ant Design package is unavailable.
- Only the selected research workspace renders, preserving mobile efficiency.

## Validation completed
- Python compile checks: passed.
- Project unit/integration tests: **39 passed**.
- Architecture validator: passed.
- Final synchronization validator: passed.
- Finnhub/NLP/Lunch/Research validator: passed.
- Actual headless Streamlit startup smoke test: passed; server started successfully with no traceback/import/syntax/runtime-start error.

## Main run command

```bash
streamlit run app.py
```
