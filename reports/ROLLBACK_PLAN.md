# Rollback Plan

## Code rollback

Revert:

- `core/settings_run_orchestrator_20260617.py`
- `services/canonical_snapshot_store.py`

Then remove the new `*_20260621.py` core modules, scripts, tests and reports. Existing protected calculations remain in the original files and were not replaced.

## Database rollback

1. Stop Streamlit and any process writing the database.
2. Copy `data/canonical_runtime.sqlite3`, its `-wal` and `-shm` files if present.
3. Run:

```bash
python scripts/rollback_research_validation_20260621.py --confirm
```

The script creates a timestamped `.bak` before dropping only these additive tables:

- `data_quality_generation`
- `data_quality_constraint_result`
- `data_quality_metric_history`
- `rejected_calculation_generation`
- `conditional_predictive_ability_history`
- `research_spa_results`
- `covariate_shift_conformal_history`
- `fforma_shadow_history`
- `expert_weight_history`
- `expert_tracker_state`
- `expert_tracker_comparison`
- `ml_production_readiness_history`
- `sliding_monitoring_state`
- `bounded_quantile_monitoring_state`

## Operational fallback

Before code rollback, the layer can be made low-cost for testing with `ADX_TEST_PROFILE=fast`. This does not disable source/publication safety. A full disable should be done by reverting the two integration edits rather than silently bypassing validation in production.

## Verification after rollback

```bash
python -m compileall -q app.py main.py adx_dashpoard.py core services tabs tests
python -m pytest -q
python -m streamlit run app.py
```

Then confirm `PRAGMA integrity_check` returns `ok` and that the previous canonical snapshot loads.
