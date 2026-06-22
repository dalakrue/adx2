# Implementation Report — Research Validation 2026-06-21

## Outcome

A new additive, lightweight research-validation layer was integrated into the existing Settings Run Calculation transaction. It validates source data before calculation, evaluates settled research evidence once, validates the final canonical payload, and writes all accepted evidence atomically with the canonical snapshot.

## Files added

- `core/research_validation_common_20260621.py`
- `core/declarative_data_quality_20260621.py`
- `core/canonical_data_validation_20260621.py`
- `core/conditional_predictive_ability_20260621.py`
- `core/superior_predictive_ability_20260621.py`
- `core/covariate_shift_conformal_20260621.py`
- `core/fforma_shadow_weighting_20260621.py`
- `core/fixed_share_expert_tracker_20260621.py`
- `core/ml_production_readiness_score_20260621.py`
- `core/sliding_monitoring_statistics_20260621.py`
- `core/bounded_quantile_monitoring_20260621.py`
- `core/research_validation_store_20260621.py`
- `core/research_validation_layer_20260621.py`
- `scripts/benchmark_research_validation_20260621.py`
- `scripts/migrate_research_validation_20260621.py`
- `scripts/rollback_research_validation_20260621.py`
- `scripts/run_fast_test_batches_20260621.py`
- `tests/test_research_validation_20260621.py`
- requested reports under `reports/`.

## Files modified

- `core/settings_run_orchestrator_20260617.py` — adds lazy preflight validation, one research transaction call, prepublication validation and rejection diagnostics.
- `services/canonical_snapshot_store.py` — inserts the new table bundle inside the existing canonical transaction.

## Protection results

- No existing calculation, metric, table, chart, tab, export, copy function or database table was removed or renamed.
- Existing BUY/SELL/WAIT/HOLD/regime/priority/reliability/TP/SL meanings are not rewritten.
- The new layer declares `direction_reversal_allowed = false` and `protected_calculation_changed = false`.
- FFORMA, fixed-share, CPA, SPA and weighted conformal run in shadow/validation mode.
- The new layer can block invalid publication and can support a trust/WAIT downgrade through existing safety policy, but it cannot reverse direction.
- No new top-level page, menu, sidebar item, section or Run Calculation button was added.
- No external API, scheduler, thread, loop or heavy model was added.

## Fast-test profile

`ADX_TEST_PROFILE=fast` changes only bounded validation/testing work:

- SPA bootstrap iterations: 49 instead of the production default 1,000.
- canonical settled evidence cap: 1,000 instead of 6,000.
- method evidence cap: 2,000 instead of 12,000.

Production behavior remains the default when the environment variable is absent.

## Exact commands

### Main file

```text
app.py
```

### Install

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Local run

```bash
python -m streamlit run app.py
```

### Fast focused tests

Linux/macOS:

```bash
ADX_TEST_PROFILE=fast python -m pytest -q tests/test_research_validation_20260621.py
```

Windows PowerShell:

```powershell
$env:ADX_TEST_PROFILE="fast"
python -m pytest -q tests/test_research_validation_20260621.py
```

### Complete per-file fast test runner

```bash
python scripts/run_fast_test_batches_20260621.py
```

### Full default suite

```bash
python -m pytest -q
```

### Benchmark

```bash
ADX_TEST_PROFILE=fast python scripts/benchmark_research_validation_20260621.py
```

## Streamlit Cloud configuration

- Repository root contains `app.py`.
- Main file path: `app.py`.
- Python: `3.12`, specified by `runtime.txt` and `.python-version`.
- Dependencies: `requirements.txt`.
- Existing `.streamlit/config.toml` is retained.
- Do not put API keys in source or the ZIP. Add optional connector secrets through Streamlit Cloud Secrets using the names documented in `.streamlit/secrets.example.toml`.
- No new secret is required by the 2026-06-21 research layer.

## Database migration

The application lazily creates the additive tables. To migrate explicitly:

```bash
python scripts/migrate_research_validation_20260621.py
```

For a non-default database:

```bash
python scripts/migrate_research_validation_20260621.py --db /path/to/canonical_runtime.sqlite3
```

## Rollback

1. Stop the app and back up `data/canonical_runtime.sqlite3` plus `-wal`/`-shm` files if present.
2. Revert the two modified integration files and remove the new 2026-06-21 modules.
3. To remove only additive tables, run:

```bash
python scripts/rollback_research_validation_20260621.py --confirm
```

The rollback script creates a timestamped database backup before dropping the new tables.

## Intentionally not changed

- Existing protected decision formulas and score domains.
- Existing red/yellow/blue/combined forecast paths.
- Existing MMSE/DMA/ACI/CQR/calibration/reliability modules.
- Existing UI navigation and top-level structure.
- Existing APIs and connector behavior.
- Existing database tables or old history retention.
- No automatic FFORMA training or model promotion during Streamlit calculation.
- No claimed accuracy/profitability improvement without settled out-of-sample evidence.
