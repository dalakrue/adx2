# ADX Quant Pro Upgrade — 2026-06-19

## Canonical synchronization

- Preserved Full Metric History as the protected direction authority.
- Added one calculation ID and canonical identity/status aliases for every published generation.
- Recorded calculation start/completion, data timestamp, data quality, staleness, source, and error status.
- Changed the Settings success route to open the main Lunch surface, where all required values and the cached Power BI chart are already present.

## Settled self-backtesting and trust

- Added an additive SQLite settled-forecast ledger with one immutable row per calculation and horizon.
- Added PENDING, SETTLED, INVALID, and EXCLUDED record states.
- Pending forecasts are settled only after the target completed H1 candle exists.
- Original prediction fields are never updated during settlement; only outcome columns are written.
- Added calibration, interval quality, MFE/MAE, TP/SL touch, grouped regime/session/horizon trust, DSR, PBO, DM, and SPA-equivalent status outputs with honest unavailable reasons.
- Added centralized configurable VALIDATED, DEVELOPING, INSUFFICIENT, and REJECTED thresholds.

## WAIT logic

- Split hard safety blockers from soft evidence.
- Moderate disagreement, neutral M1, moderate NLP risk, moderate transition risk, slightly low priority, and limited history now reduce confidence/priority without independently forcing WAIT.
- Missing/failed/stale critical data, negative expected value, critical drift/event/transition risk, invalid intervals, and direct forecast opposition remain protective blockers.
- No downstream module can reverse the Full Metric direction.

## Lunch and prediction path

- Replaced the active Lunch patch chain with one canonical progressive-disclosure renderer.
- Added six trusted operational cards with timestamp, calculation ID, settled sample count, trust state, and data quality.
- Placed the cached Power BI projection directly below the decision area.
- Added current-price, H+1/H+2/H+3/H+6, TP/SL when available, and expected MFE/MAE chart references.
- Added Current History, Settled Forecasts, Regime Performance, and Validation Scorecard inside the existing Full Metric History area.
- Kept supporting scores, KNN, Greedy, priority, detailed reasons, regime tables, JSON, and exports behind existing-style controls.

## Performance and safety

- Heavy calculations remain owned by Run Calculation; Lunch navigation reads published caches only.
- History rendering is paged/limited while full CSV export remains available.
- Added indexed incremental settlement and precomputed trust summaries.
- Standardized new ledger timestamps to timezone-aware UTC.
- Added user-safe module/category/action messages for new history and chart display failures.
