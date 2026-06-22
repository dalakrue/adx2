# Test Report

## Environment

- Local interpreter: Python 3.13.5.
- Configured deployment interpreter: Python 3.12 (`runtime.txt`, `.python-version`).
- Research test mode: `ADX_TEST_PROFILE=fast`.
- Streamlit installed from the declared requirement before the final dependency and startup tests.

## Final local results

- Python compilation for `app.py`, `main.py`, `adx_dashpoard.py`, `core`, `services`, `tabs`, `ui`, `scripts` and `tests`: **PASS**.
- Complete per-file suite: **290 passed, 0 failed across 28 test files**.
- Post-integration patch rerun: **26 passed, 0 failed** for the new research layer, canonical runtime and Settings restore files.
- Local headless Streamlit startup: **PASS**, `/_stcore/health` returned HTTP 200 and `ok`.
- Additive database migration smoke: **PASS**, 14 tables verified and integrity `ok`.
- Database rollback smoke: **PASS**, no new tables remained and integrity `ok`.

The first per-file run had one environmental failure because Streamlit was not installed in the container. After installing the dependency already declared in `requirements.txt`, the entire affected file passed: **33 passed**. The final effective result is therefore 290/290. Detailed machine-readable evidence is in `reports/FINAL_TEST_SUMMARY_20260621.json`.

## Coverage in the focused tests

Determinism, same-input hashing, idempotent database writes, no future leakage/future append invariance, chronological settlement, duplicates, missing candles, incomplete newest candle, NaN/infinity, sparse history, empty challenger set, small ESS, poor overlap, weight concentration, fixed-share normalization/caps/floors, deterministic SPA, HAC behavior, rollback, publication blocking, previous-state preservation, SQLite transaction behavior, bounded monitoring, closed-tab static safety and protected-direction preservation.

## Status labels

- **Code-complete:** yes for requested modules and integration.
- **Locally tested:** yes; 290 tests plus compilation, migration/rollback and local Streamlit health smoke.
- **Python 3.12 executed here:** no; the available interpreter was Python 3.13.5.
- **Streamlit Cloud live-tested:** no.
- **Live-market-data tested:** no.
