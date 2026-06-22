# Data Validation Report

## Gate locations

1. **Pre-calculation source gate** in `core/settings_run_orchestrator_20260617.py` after the existing completed-H1/source preparation and before settlement/heavy calculation.
2. **Prepublication canonical gate** after the new research evidence is attached and before `publish_canonical_atomically(...)`.

## Source checks

- required time, open, high, low and close columns;
- numeric conversion and finite values;
- datetime parseability and timezone consistency;
- unique, monotonically increasing timestamps;
- H1 cadence and missing-candle detection;
- incomplete latest candle and source freshness;
- `Low <= Open <= High`, `Low <= Close <= High`, `High >= Low`;
- nonnegative spread when present;
- source-to-cleaned row reconciliation;
- expected feature schema and transform signature when supplied.

## Canonical checks

- probability values in `[0,1]`;
- documented score-like values in their detected domains;
- forecast origin earlier than target;
- settlement later than prediction creation;
- source/generation identity consistency.

## Failure behavior

A critical source failure returns before the new generation is calculated or published. A critical canonical failure returns before `publish_canonical_atomically(...)`. In both cases:

- previous valid canonical state is preserved;
- the rejected generation and exact constraints are written to `rejected_calculation_generation`;
- prices are not silently repaired;
- partially valid rows are not passed to research evaluation;
- a compact diagnostic is stored in the existing session diagnostic key.

## New tables

- `data_quality_generation`
- `data_quality_constraint_result`
- `data_quality_metric_history`
- `rejected_calculation_generation`

All identities are deterministic and insertion is idempotent by primary key.

## Validation tests executed

The focused suite covers duplicate timestamps, missing candles, incomplete newest candle, NaN/infinity, deterministic same-input hashes, probability/temporal checks, publication blocking and preservation of a previous valid snapshot. See `reports/TEST_REPORT.md` for actual run status.
