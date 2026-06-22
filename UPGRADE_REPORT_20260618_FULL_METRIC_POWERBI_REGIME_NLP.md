# ADX Quant Pro / new7 Completion Report — 2026-06-18

## Delivery
Complete project upgraded in place from the supplied ZIP. No original file was deleted. Main command:

```bash
streamlit run app.py
```

## Files modified
- `core/adx_shared_sync_20260615.py`
- `core/canonical_runtime_20260617.py`
- `core/finnhub_connector.py`
- `core/nlp_related_priority_20260615.py`
- `core/powerbi_path_calibration_20260617.py`
- `core/settings_run_orchestrator_20260617.py`
- `tabs/antd_page_router_20260615.py`
- `tabs/dinner_morning_data_patch_20260614.py`
- `tabs/dinner_unified_center_20260617.py`
- `tabs/final_lunch_upgrade_20260617.py`
- `tabs/final_three_center_upgrade_20260614.py`
- `ui/antd_navigation_20260615.py`
- `ui/lunch_restored.py`
- `ui/nlp_research_panel.py`

## Files added
- `core/regime_window_analytics_20260618.py`
- `ui/table_ordering_20260618.py`
- `tests/test_20260618_projection_and_regime_upgrade.py`
- `UPGRADE_REPORT_20260618_FULL_METRIC_POWERBI_REGIME_NLP.md`

## Full metric and history restoration
- Restored all cached Full Metric Detail tables in the active Lunch renderer and the dedicated Lunch detail/history renderer.
- Removed the behavior that stopped visible details at one selected entry/reversal table.
- Full metric, factor, regime and Dinner history tables now use timestamp-aware newest-first display so the current completed day/hour appears first.
- Kept existing source calculation objects unchanged; this is a rendering/order repair.

## False Reversal Risk
- Added exactly one new `st.metric` named **False Reversal Risk** in the existing Lunch decision evidence row.
- Score is 0–10 with LOW, WATCH, CAUTION and HIGH thresholds.
- Uses only existing reversal strength, active-count, probability, move ratio, direction derivative, regime and shared reliability evidence.
- Calculated once in the central shared object and preserved by the canonical adapter; the renderer does not recalculate it.

## Power BI path calibration
- Preserved raw red, yellow and blue source paths internally.
- Added separate completed residual histories by path and H+1 through H+6, with generic completed-history fallback only when legacy history lacks path/horizon labels.
- Added robust recency-weighted median bias correction, winsorization, same-regime/global shrinkage and per-horizon correction caps.
- Added path-specific reliability from recent absolute error, stability, direction accuracy, sample completeness and disagreement.
- Enforced bounded normal weights of 15%–55% per available path and normalized weights to 100%; one-path fallback uses that one path as required.
- Main path now uses horizon-specific reliability weights and disagreement shrinkage.
- Red, yellow, blue, main and both bands are visibly anchored to the latest completed real close.
- Added ATR/expansion-aware one-step movement caps.
- All-path-missing fallback is flat from the latest completed close with conservative volatility bands.
- Added signed residual 10th/90th-quantile band inputs, horizon expansion, ATR floor, disagreement, regime reliability and transition/conflict widening.
- Enforced finite positive prices, noncrossing bands and `Lower <= Main <= Upper`.
- Stored raw/calibrated paths, weights, residual samples, global/regime/final corrections, quantiles, sample counts, fallback state and timestamps in the calibration audit object.

## Causal leakage protection
- Historical corrections require finite actual and predicted completed outcomes.
- Target/completed timestamps later than the latest completed market candle are excluded.
- No negative shifts, centered rolling windows, backward future fills, actual-future path reuse or full-sample normalization were introduced.
- Market features use trailing OHLC only.

## Three regime tables
- Added one shared causal Alpha/Delta history calculated once over up to 600 completed H1 rows.
- Added synchronized Lower 1D (24), Medium 5D (120) and Higher 25D (600) one-row analytics tables in the existing Dinner table area.
- All three use the same symbol/run source, final completed timestamp and canonical/shared result.
- Included required Alpha, Delta, mean, median, normalized slopes, velocity, acceleration, standard deviations, positive ratios, persistence, stability, transition risk, reliability, cross-window alignment and conservative BUY/SELL/WAIT bias.
- Delta is exactly current causal Alpha minus previous causal Alpha for the same history definition.
- Cross-window disagreement increases transition risk and lowers reliability; insufficient or unstable evidence forces WAIT.

## Dinner and NLP restoration
- Restored an unambiguous Dinner **AI Assistant** route.
- Gave Research AI Assistant a distinct internal label so the duplicated menu text can no longer route Dinner clicks to Research.
- Removed the duplicate Finnhub API-key input from Research > NLP; Research shows connection status and uses the Settings/sidebar-managed connector.
- Finnhub refresh now merges existing forex/general results with the retained cache, deduplicates, keeps newest articles for up to 25 days and no longer replaces a larger cache with one item.
- Existing related-news ranking remains ascending with KNN, Greedy, direction, impact, protection and explanation columns; the UI shows a target of at least 10 genuine cached articles without fabricating news.

## Synchronization and performance
- Power BI calibration and all three regime tables are produced during the existing Settings Run Calculation workflow.
- Outputs are stored in the existing shared/canonical result and session caches for read-only tab navigation.
- The 600-row Alpha history is calculated once; 120-row and 24-row tables are derived from it.
- No new model, external API, top-level tab, page, sidebar item or independent heavy calculation was added.

## Tests actually run
- `python -m compileall -q .` — passed.
- `PYTHONPATH=. pytest -q` — **43 passed**.
- Focused causal projection/regime tests — **4 passed**.
- Streamlit headless server on port 8765 — health endpoint returned `ok` and startup log contained no traceback.
- Streamlit `AppTest.from_file('app.py').run()` — **0 application exceptions**.

## Verified invariants
- Missing one, two or all paths do not crash.
- All-missing path is flat at the latest completed close.
- Same inputs produce identical displayed paths and bands.
- Available-path weights sum to 100% and remain within normal bounds.
- Future-dated completed-history rows are excluded.
- Extreme residuals are clipped robustly.
- Main/bands contain no NaN, infinity or negative prices.
- Bands do not cross and generally expand with horizon.
- All three regime tables have the same end timestamp.
- Ratios, stability, transition risk and reliability remain within 0–100.
