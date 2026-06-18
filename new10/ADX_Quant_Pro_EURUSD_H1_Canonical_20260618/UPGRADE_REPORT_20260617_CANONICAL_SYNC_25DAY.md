# ADX Quant Pro / new7 Upgrade Report — 2026-06-17

## Scope completed

This build uses the uploaded project as its only code base. It preserves the existing Settings, Lunch, Dinner, Morning, Research and Other structure and does not add a top-level page, menu item, sidebar section, model or prediction engine.

The existing Regime + NLP history in Lunch and Research/NLP was changed from a 10-day display to a 25-day H1 history. The full 25-day canonical table remains available to calculations and exports; browser rendering uses a bounded display view to reduce phone and desktop load.

## Files changed

### Modified

- `_home_joined.py`
- `core/adx_shared_sync_20260615.py`
- `core/app/lifecycle.py`
- `core/app/runner.py`
- `core/decision_contract_20260617.py`
- `core/decision_product_engine_20260617.py`
- `core/finnhub_connector.py`
- `core/regime_sync_20260617.py`
- `core/settings_run_orchestrator_20260617.py`
- `core/tab_state_stability_20260615.py`
- `tabs/ai_assistant_lite.py`
- `tabs/antd_page_router_20260615.py`
- `tabs/dinner_morning_data_patch_20260614.py`
- `tabs/eurusd_h1_matrix.py`
- `tabs/final_lunch_upgrade_20260617.py`
- `tabs/research.py`
- `ui/home_master_control_bar_20260615.py`
- `ui/lunch_restored.py`
- `ui/nlp_research_panel.py`

### Added

- `core/canonical_runtime_20260617.py`
- `core/finnhub_validation_20260617.py`
- `core/runtime_cache_20260617.py`
- `tests/test_canonical_runtime_20260617.py`
- `ui/mobile_low_heat_20260617.py`
- `UPGRADE_REPORT_20260617_CANONICAL_SYNC_25DAY.md`

No original file was deleted.

## Synchronization architecture

- `canonical_decision_result_20260617` is the authoritative completed Settings result.
- A successful calculation creates one `run_id`, one `calculation_generation`, one `data_signature`, and one completed-candle identity.
- The canonical object carries `symbol`, `timeframe`, `source`, `latest_completed_candle_time`, `created_at`, `expires_at`, `schema_version`, `calculation_version` and `calculation_status`.
- One validated completed-candle DataFrame is staged privately and supplied to the existing metric, PowerBI, regime, priority and canonical builders.
- The canonical result and shared compatibility adapters are validated before publication. The authoritative canonical pointer is published last.
- A failed run does not increment the successful generation and does not replace the last valid canonical result.
- Component identity validation rejects run, symbol, timeframe, source and data-signature mismatches.
- `ensure_shared_calculation_result(force=False)` is called once during a normal rerun. The explicit Settings calculation is the only path that requests a forced rebuild.
- The runtime context records the rerun identifier, active page, active subpage, phone mode, canonical result, run ID, generation and data signature.

## Canonical state and legacy compatibility

Legacy session-state keys are retained as one-way compatibility mirrors. They point to canonical data or adapters and do not independently calculate or overwrite a newer decision.

Explicit adapter groups cover:

- market/OHLC
- metrics and decisions
- PowerBI/forecast
- regime and alpha/delta
- priority and KNN/Greedy
- reliability by horizon
- NLP
- data mining
- prediction history
- AI grounding

The canonical priority table is built once during Settings calculation and reused by Lunch, Dinner, Research, Finder and AI Assistant. Each row receives canonical run/generation identity and normalized fields for candle time, hour, regime, reliability, prediction direction, KNN score, Greedy score, combined score, rank, label, less-risky bias, conflict and data quality.

## Navigation and hidden-tab behavior

- `active_page` and `active_subpage` are authoritative.
- Legacy navigation keys remain one-way mirrors.
- Settings remains the first page for a new session.
- Only the selected top-level renderer and selected inner-tab renderer are imported and rendered.
- Hidden inner tabs do not construct their charts, tables or heavy optional feature paths.
- Renderers read the runtime context and canonical adapters instead of rebuilding shared calculations.

## 25-day Regime + NLP history

- Lunch history label and payload now use 25 days.
- Research/NLP history label and payload now use 25 days.
- The canonical Settings build uses `REGIME_NLP_HISTORY_DAYS = 25`.
- Research related-news priority requests use `window_days=25`.
- Backward-compatible callable names remain available where older imports expect them.

## Mobile heat reductions

Phone mode and reduced-motion behavior now disable nonessential:

- continuous animations
- transitions
- expensive filters and backdrop filters
- rotating/moving gradients and pseudo-element effects
- hover movement

Full-app autorefresh is disabled on phone unless live-data mode is explicitly enabled. It is also disabled for Settings, Research, Other and closed/non-live inner tabs. Existing layout, controls, metrics, tables and sections are preserved.

## Display and session-memory changes

- Full validated data remains available to calculations and exports.
- Phone display tables are bounded to a recent safe window; desktop display tables use a larger bounded window.
- Long history and expensive views remain behind their existing open/close controls.
- Compatibility DataFrame keys reuse controlled references where safe instead of separately produced copies.
- Synthetic timestamps are not created for production decision data; missing valid timestamps return a not-ready state.
- Internal completed-candle timestamps are normalized to UTC.

## Caching changes

Bounded `st.cache_data` helpers use TTL and `max_entries` for reusable serializable work, including:

- OHLC cleaning/preparation
- display DataFrames
- export serialization
- NLP normalization

Cache identity includes the relevant symbol/timeframe/source/data signature/calculation version or supplied calculation parameters. API secrets are not cache arguments or cache keys. Existing heavy optional libraries remain lazy-loaded only in selected features.

## Finnhub safety and testability

Pure key normalization, format validation and response classification were separated into `core/finnhub_validation_20260617.py`, which imports without Streamlit and is testable without network access. Keys remain session-only and are not written to files, logs, exports, SQLite or cached arguments. Error classification distinguishes invalid authentication from entitlement limits and rate limiting.

## Tests run and results

- `python -m compileall -q .` — passed
- `python -m pytest -q` — **37 passed**
- `python tools/validate_architecture.py` — passed
- `python tools/validate_final_sync_20260617.py` — passed
- `python tools/validate_finnhub_nlp_restore_20260617.py` — passed
- Import test for `app.py`, active routing and canonical runtime modules — passed
- Streamlit startup smoke test — passed; `/_stcore/health` returned HTTP 200 and `ok`

The automated suite includes canonical schema, cross-tab identity, calculation generation, failed-run preservation, identity mismatch, incomplete-candle exclusion, hidden-inner-tab nonexecution, mobile low-heat CSS, duplicate shared calculation prevention, canonical KNN/Greedy table, AI canonical grounding, 25-day Lunch/Research history, horizon-specific reliability/intervals, data quality, ledger, drift, and offline Finnhub validation.

## Environment-specific limitations

- Finnhub tests are intentionally offline; no real API key or live network request was stored or exercised.
- The startup smoke test verifies server startup and health, not every browser interaction with external market-data providers.
- Optional heavyweight ML/NLP packages are loaded only when their existing feature is selected; availability still depends on the deployment environment and installed project requirements.
- Bare Python validation scripts can emit normal Streamlit warnings about missing `ScriptRunContext`; these did not cause a validation failure.

## Entry point

Run the project with:

```bash
streamlit run app.py
```
