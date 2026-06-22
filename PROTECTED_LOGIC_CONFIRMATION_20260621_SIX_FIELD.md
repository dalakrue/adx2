# Protected Logic Confirmation

The upgrade does not modify the protected decision/calculation authority. **8/8 audited protected files are byte-for-byte identical** to the uploaded package.

| File | SHA-256 unchanged |
|---|---|
| `core/settings_run_orchestrator_20260617.py` | YES |
| `core/decision_product_engine_20260617.py` | YES |
| `core/canonical_runtime_20260617.py` | YES |
| `core/decision_policy_20260617.py` | YES |
| `core/medium_standard_regime_bias_20260619.py` | YES |
| `core/prediction_ledger_20260617.py` | YES |
| `services/position_sizing.py` | YES |
| `core/adx_shared_sync_20260615.py` | YES |

## Preserved invariants

- Ten protected decision tables and Decision 11 remain visible.
- One-generation canonical publication remains authoritative.
- Completed-H1 cutoff remains authoritative.
- No alternative BUY/SELL/WAIT engine was added.
- Refresh and field toggles do not call Run Calculation.
- AI/readiness are read-only and cannot mutate protected decision fields.
- Existing Power BI, regime, KNN, Greedy, reliability, conflict, risk, and history calculations are reused rather than reweighted.

Machine-readable hashes are in `PROTECTED_HASHES_20260621_SIX_FIELD.json`.
