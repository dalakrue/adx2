# ADX Quant Pro / new7 Performance Implementation Report

Date: 2026-06-19  
Project: EURUSD H1 Streamlit system  
Protected authority: Full Metric History

## Run instructions

Main file: `app.py`

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

The historical `adx_dashpoard.py` entry point remains available and launches the same app shell.

## What changed

### Modified files

1. `core/canonical_runtime_20260617.py`
2. `core/settings_run_orchestrator_20260617.py`
3. `tabs/ai_assistant_lite.py`
4. `tabs/antd_page_router_20260615.py`
5. `tabs/dinner_unified_center_20260617.py`
6. `tabs/final_lunch_upgrade_20260617.py`
7. `ui/decision_product_panel_20260617.py`

### New runtime/support files

1. `core/compact_canonical_20260619.py`
2. `core/performance_store_20260619.py`
3. `tabs/ai_assistant_compact_20260619.py`
4. `ui/composite_summary_cards_20260619.py`
5. `tabs/dinner_unified_center_20260617_legacy.src`
6. `tabs/final_lunch_upgrade_20260617_legacy.src`
7. `tests/test_performance_architecture_20260619.py`
8. `tools/benchmark_performance_20260619.py`
9. `PERFORMANCE_MEASUREMENTS_20260619.json`
10. `TEST_RESULTS_20260619.json`
11. `CHANGE_MANIFEST_20260619.json`
12. `IMPLEMENTATION_REPORT_20260619_PERFORMANCE.md`

Removed project files: **none**.

The two `.src` files preserve the original detailed renderers. They are loaded only after an explicit detail/chart/history gate is enabled, so the original useful views remain available without entering the default render path.

## Implemented architecture

### One canonical shared result

`Run Calculation` still executes the existing protected calculation sequence and atomically publishes the canonical result only after validation succeeds. The canonical publisher now additionally creates:

- one deterministic calculation ID containing canonical ID, generation, and completed-H1 identity;
- one compact immutable summary for all default pages;
- one compact AI fact pack;
- a bounded in-memory cache containing only the current and previous generation;
- a persisted canonical summary in the SQLite runtime store.

Lunch and Dinner read `compact_canonical_summary_20260619`. They do not create independent Full Metric, regime, projection, reliability, priority, or NLP calculations.

### Eight composite cards

The default Lunch and Dinner summaries now use eight lightweight HTML cards:

1. Decision
2. Protected Scores
3. Regime
4. Projection
5. Priority
6. Uncertainty
7. NLP and Event Risk
8. Data and Validation

All requested values remain visible. The active default Lunch/Dinner path changed from **55 individual `.metric()` calls to 0**. Detailed metric views are preserved behind explicit gates.

### True lazy rendering

A closed section is now checked with a conditional gate before importing or calling its renderer. The following do not execute while closed:

- Full Metric/history pages
- regime standard tables
- KNN/Greedy and validation tables
- Power BI projection chart
- audit/JSON/copy preparation
- original Lunch tools
- detailed horizon reconciliation

The default Dinner route no longer imports the large `tabs.home` patch chain. The original render modules are loaded through `SourceFileLoader` only when a gated view is requested.

### Database and session-state optimization

`core/performance_store_20260619.py` adds a standard-library SQLite store with WAL mode and transaction-safe writes. No new package is required.

It separates:

- compact current-summary read;
- limited/projection history query;
- full export query;
- AI evidence/conversation query;
- manifest/audit query.

Normal history rendering uses explicit columns and SQL `LIMIT`. Full exports use the full export query. Large top-level and known nested historical DataFrames are written to disk after successful publication and replaced in session state with a 48-row phone page or 100-row desktop page. Full rows remain on disk.

### AI Assistant optimization

Run Calculation creates a compact fact pack containing the current canonical ID, completed H1 timestamp, close, decision, protected scores, regimes, reliability, priority, projection/bands, uncertainty, NLP summary, top opportunities, limited evidence, and validation status.

Opening AI Assistant:

- reads only the compact fact pack;
- loads a limited chat page;
- performs no model/API call;
- performs no full-history conversion;
- performs no prediction calculation.

Only Send/Analyze invokes answer logic. The advanced existing assistant is imported lazily. Answers are cached by calculation ID + normalized question + mode, capped at 32 entries. A stale-generation guard prevents an answer from an older calculation ID replacing the current result. Phone mode displays the latest six messages; older messages stay in SQLite.

### Caching and invalidation

- Canonical compact cache: maximum 2 generations.
- AI answer cache: maximum 32 entries.
- Cache identity includes calculation ID/completed H1 generation and question parameters.
- UI-only selection changes read the existing compact result.
- Existing causal/research incremental append logic is preserved.
- New-H1 identity changes invalidate the compact generation.
- NLP-only compact updates leave protected scores and projections unchanged.

### Mobile mode

- One-column card grid below 760 px.
- No animation, blur, or nested metric-column tree in the new cards.
- 48 history rows per phone page.
- Full export remains complete.
- Default Dinner chart builds: 1 before, 0 after.
- No calculation accuracy is changed for phone mode.

## Measurements

Measurement source: `tools/benchmark_performance_20260619.py` and `PERFORMANCE_MEASUREMENTS_20260619.json`.

The benchmark used the same deterministic 12,000-row × 26-column H1-shaped workload before and after. It is a local server-side render/data-preparation benchmark, **not iPhone hardware telemetry and not a live Streamlit network benchmark**.

| Measurement | Before | After | Result |
|---|---:|---:|---:|
| Dinner preparation | 31.04 ms | 0.66 ms | 97.88% lower |
| Dinner traced temporary allocation | 5.14 MB | 0.012 MB | 99.77% lower |
| Lunch preparation | 69.13 ms | 0.73 ms | 98.95% lower |
| Lunch traced temporary allocation | 8.25 MB | 0.012 MB | 99.85% lower |
| AI context opening proxy | 95.42 ms | 0.00083 ms | 99.999% lower |
| Compact local AI question, network excluded | — | 0.066 ms | measured after |
| Default Lunch/Dinner metric calls | 55 | 0 | 100% lower |
| Active Lunch/Dinner explicit `.copy()` calls | 3 | 0 | removed |
| Active Lunch/Dinner explicit sorts | 1 | 0 | removed |
| Large top-level session DataFrames | 5 | 0 | removed from large category |
| Top-level DataFrame payload | 12,480,660 bytes | 50,580 bytes | 99.59% lower |
| Dinner summary DB rows/columns | full paths previously available | 0 / 0 | compact state only |
| Limited history page | full table path | 48 rows / 8 columns | SQL projection + limit |
| Full export | 12,000 rows | 12,000 rows | preserved |
| AI fact pack | full history conversion | 35,578 bytes | bounded |
| Chart builds on default Dinner navigation | 1 | 0 | eliminated |

Immediate process RSS changed from 326.7 MB to 329.6 MB during the synthetic SQLite benchmark. This is **not claimed as an RSS reduction** because Python/SQLite allocators do not necessarily return memory to the operating system immediately. The measurable retained DataFrame payload decreased by 99.59%.

### Measurements not available in this environment

The following cannot be honestly measured here because the supplied container has no Streamlit installation, no live browser, no iPhone telemetry, and no connected live market/API session:

- full live Run Calculation duration;
- live peak/after-calculation RSS for the complete project;
- real Lunch/Dinner browser opening time over a network;
- iPhone CPU, RAM, battery, or heat;
- external AI network delay;
- exact browser payload transferred by Streamlit.

Runtime timing instrumentation was connected to Run Calculation, Lunch opening, Dinner opening, history query, and compact summary publication so these values are captured in a real installed run under `performance_timings_20260619` and `settings_run_status_20260617.performance`.

## Tests

Commands executed included:

```bash
python -m compileall -q .
python -m pytest -q tests/test_performance_architecture_20260619.py
python -m pytest -q tests/test_canonical_runtime_20260617.py
python -m pytest -q tests/test_causal_quant_end_to_end_20260618.py
python -m pytest -q tests/test_decision_product_20260617.py
python -m pytest -q tests/test_end_to_end_sync_regressions_20260618.py
python -m pytest -q tests/test_finnhub_connector_20260617.py
python -m pytest -q tests/test_full_metric_canonical_sync_20260618.py
python -m pytest -q tests/test_full_metric_dinner_nlp_restore_20260618.py
python -m pytest -q tests/test_full_metric_regime_visibility_20260618.py
python -m pytest -q tests/test_multiscale_probabilistic_upgrade_20260618.py
python -m pytest -q tests/test_one_click_system_wide_20260618.py
python -m pytest -q tests/test_powerbi_path_calibration_20260617.py
python -m pytest -q tests/test_sync_mobile_nlp_ai_final_20260618.py
python -m pytest -q tests/test_ten_paper_research_calibration_20260618.py
```

Results:

- Python syntax compilation: **PASS** for every Python file.
- Collected tests: **163**.
- Passed: **162**.
- Environment failure: **1**.
- Final focused regression run: **58 passed**.
- New required performance architecture suite: **30 passed**.

Failed test:

`test_requirements_compatibility_imports_lightweight_stack` failed only because this execution container does not have the `streamlit` package installed (`ModuleNotFoundError`). `streamlit>=1.35` remains correctly declared in `requirements.txt`. The true Streamlit startup command therefore could not be executed in this container.

## Protected behavior confirmations

- Full Metric authority file SHA-256 remains `fe0797ab30f469f3ea748bc66a690b18a68aaf91306ac33c797bdcdcf6e60682`.
- Full Metric History calculations and scale are unchanged.
- Master, Entry, Hold, TP, Exit Risk, and Trend Capacity scales are unchanged.
- Directional/volatility regime, Alpha/Delta, KNN, Greedy, reliability, conflict, NLP, and priority formulas were not modified.
- Red, yellow, and blue projection logic was not modified; the original chart renderer is preserved and lazy-loaded.
- Existing tabs and inner tabs remain available.
- AI Assistant remains available and functional after Run Calculation.
- No new top-level tab, page, sidebar item, menu item, prediction engine, Run Calculation button, or API field was added.
- Default tab opening performs no protected heavy calculation.
- Full historical rows remain stored for full export.
- Phone row limits affect display only and do not delete history.

## Limitations / deliberately unmodified items

A new row-level Full Metric algorithm was not introduced because the Full Metric calculation module is protected and has a byte-level integrity test. Existing incremental causal/research settlement and append logic remains active. The optimization instead removes repeated display-time calculations, imports, scans, copies, sorts, chart builds, and full-history transfers after the canonical run.

No new dependency was added. SQLite is part of Python.

The returned ZIP checksum is supplied outside the archive because embedding an archive's own final checksum inside itself is self-referential and would change that checksum.
