# Pre-Implementation Architecture Audit

**Audit date:** 2026-06-21  
**Scope:** uploaded ADX Quant Pro package before the 2026-06-21 research-validation additions  
**Protected authority:** Full Metric Detail + History and the atomic canonical shared result

## Package inventory

- 755 packaged files were inspected after extraction.
- 471 Python files existed before this implementation.
- 28 test files existed before this implementation.
- Four SQLite databases existed and all returned `PRAGMA integrity_check = ok` during the pre-change inspection.
- Static source counts before this implementation: 568 `.copy(...)` calls, 305 `sort_values(...)` calls, 53 `groupby(...)` calls, 5 explicit merge calls, 187 `.join(...)` calls, 25 direct `sqlite3.connect(...)` sites, and 6 `BEGIN IMMEDIATE` sites. These counts identify review locations; they do not prove that every call executes in the active path.

## Entry points and routing

1. Preferred entry: `app.py`.
2. Compatibility entry: `main.py`.
3. `app.py` delegates to `adx_dashpoard.main()`.
4. `adx_dashpoard.main()` delegates to `core.app_shell.run_app()` and the existing router.
5. The Settings **Run Calculation** action invokes `core/settings_run_orchestrator_20260617.run_settings_calculation()`.
6. Page and tab renderers consume the already-published shared adapter. The new 2026-06-21 research layer is not imported or executed by a renderer.

## Calculation and publication path

The active transaction is:

`Settings Run Calculation` → source acquisition and existing validation → completed-H1 preparation → existing settlement → protected Full Metric calculation → existing regime/priority/reliability/Power BI/NLP/research layers → 2026-06-21 research validation → prepublication validation → `core.canonical_runtime_20260617.publish_canonical_atomically(...)` → `services.canonical_snapshot_store.commit_snapshot(...)`.

`commit_snapshot(...)` opens SQLite with WAL, `synchronous=NORMAL`, a 30-second busy timeout, and one `BEGIN IMMEDIATE` transaction. It inserts the run, canonical snapshot, standard history bundle, and now the additive 2026-06-21 research rows. Any exception rolls the transaction back.

## Canonical result publication

- The canonical object is validated and checksummed before becoming the active shared adapter.
- `runs` and `run_snapshots` use `(run_id, generation)` as their composite key.
- The previous completed canonical adapter remains available unless a new generation commits successfully.
- The 2026-06-21 source gate blocks invalid generations before calculation; the prepublication gate blocks invalid canonical payloads before the atomic commit.

## Existing database inventory

### `data/adx_runtime_store.sqlite3`

- `canonical_summary` — key `calculation_id`; compact canonical/fact-pack JSON.
- `frame_manifest` — key `(calculation_id, logical_key)`; frame table manifests.
- `ai_conversation` — integer key; conversation rows tied to calculation IDs.

### `data/adx_similarity_store.sqlite3`

- `similar_day_feature_store` — composite key `(symbol, timeframe, trading_date, feature_version, completed_hours)`.
- `similar_day_generations` — composite key `(symbol, timeframe, calculation_generation)`.

### `data/canonical_runtime.sqlite3`

Forty pre-existing application tables were found. Core keys include `runs(run_id,generation)`, `run_snapshots(run_id,generation)`, and deterministic `record_key` keys in the history catalog. Existing history families include:

- Full Metric overall, protected decision, Decision-11 support, canonical priority, KNN and Greedy ranks.
- Regime overall/standard/alpha-delta/duration/changepoint/transition reliability/conflict.
- Reliability conflict, component/metric availability, input data quality, decision-change audit.
- Power BI source paths, reconciled paths, prediction ledger, forecast settlement.
- Similar-day query/ranked match/outcome, motifs and discords.
- AI assistant, AI evidence reference and answer consistency.
- Performance history/trace, cache diagnostics, history watermarks and catalog.

### `data/quant_app.sqlite3`

- `app_events`.
- `advanced_reliability_shift_snapshots_v2`.
- `advanced_reliability_shift_vectors_v2`.

## Existing forecast and weighting paths

- Existing Power BI central paths and displays: red calibrated path, yellow historical/current path, and blue/light-blue future path.
- Existing combined production forecast and method-specific settled prediction rows.
- Existing MMSE/Wiener/correlation weighting in `core/powerbi_mmse_weighting_20260618.py`.
- Existing bounded dynamic model averaging and dynamic Occam suppression in `core/research_calibration_20260618.py`.
- Existing model-confidence-set, conditional residual, conformal, calibration, drift, regime and reliability evidence remains authoritative and unchanged.

## Performance baseline available before this change

The package already contained a bounded synthetic benchmark dated 2026-06-20 using 720 completed H1 rows and 3,000 settled rows:

- normalization/top-level canonical-copy baseline median: 0.1262 seconds;
- existing advanced reliability transaction median: 4.0320 seconds under `tracemalloc`;
- existing advanced transaction median peak Python allocation: about 3.44 MB;
- report explicitly states it is not a whole-app benchmark and makes no accuracy or phone-temperature claim.

## Closed-tab and closed-expander cost

Existing 2026-06-20 hardening introduced lazy gates for heavy Lunch/Research/Morning content. Static call-path inspection confirms the new 2026-06-21 modules are imported only inside `run_settings_calculation()` and are not referenced by tab-switch, expander, or renderer modules. Therefore the new layer adds no research computation to closed-tab or closed-expander paths. This is a static and test-backed claim, not a browser profiler measurement on every device.

## Duplicate work and data-copy findings

The package contains extensive compatibility and legacy code. The static counts above identify many possible copy/sort/join sites, but only the active orchestration path was modified. The 2026-06-21 layer reduces new duplication by:

- using shallow DataFrame views and column projection;
- combining canonical and method ledgers once;
- pivoting settled losses once per horizon/loss family;
- bounding canonical settled rows to 6,000 and method rows to 12,000 in production;
- using 1,000/2,000 rows and 49 SPA bootstraps under `ADX_TEST_PROFILE=fast`;
- writing all new evidence in the existing atomic SQLite transaction.

No existing copy, sort, join, groupby, table, or history field was deleted merely to improve a static count.

## Atomicity, rollback and lock behavior

- Normal publication uses one `BEGIN IMMEDIATE` transaction and rolls back on error.
- Rejected pre-calculation generations are stored separately because no canonical snapshot is published for them.
- Additive schemas use `CREATE TABLE IF NOT EXISTS` and deterministic primary keys with `INSERT OR IGNORE`/upsert behavior as appropriate.
- SQLite busy timeout remains 30 seconds.
- The migration is additive and idempotent; rollback can drop only the new tables after creating a database backup.
