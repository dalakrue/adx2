# Test Results Report

## Final status

**PASS — 318/318 automated tests passed across all 32 test files.**

The authoritative regression was executed with each legacy test group isolated in fresh pytest processes. This avoids long-lived Streamlit/import state from one legacy test contaminating or blocking later files. A monolithic one-process run reached roughly three quarters without reporting a failure before the execution environment timed it out; the isolated full-file run then completed every collected test successfully.

## Coverage summary

| Validation | Result |
|---|---|
| Pytest collection | 318 tests in 32 files |
| Isolated complete regression | 318 passed, 0 failed |
| Focused delivery/upgrade suite | 72 passed |
| New transition/search/connector suite | 17 passed |
| Python compile validation | 505 files, 0 failures |
| Critical import validation | 11 modules imported successfully |
| DuckDB migration/initialization | Passed on an isolated database |
| Streamlit startup | Passed with `streamlit run app.py` |
| Streamlit health endpoint | Returned `ok` |
| Static full-package inspection | 0 Python syntax errors; 0 absolute local Windows paths |

## Required behavioral checks

1. Existing protected formula/regime/decision structures remain unchanged in evidence-layer tests.
2. Canonical adapters and page aliases use the same run ID/generation contract.
3. Run Calculation remains confined to the orchestrator path and executes once per successful action.
4. Successful calculation routes to Lunch and opens Field 1 without a second calculation.
5. Lunch search submits through a Streamlit form, including Enter-key submission behavior.
6. Search imports/calls no heavy calculator.
7. Live connector controls use callback-backed one-click Save & Connect behavior and persistent explicit state.
8. API-key paths are redacted and trust-history schemas contain no key/secret field.
9. BOCPD/ADWIN evidence cannot overwrite the original regime or decision engine.
10. The complete descending 25-day history remains visible.
11. Field 4 preserves existing data, nested workspaces, and copy/export controls.
12. DuckDB history is incremental, deduplicated, and post-transition outcomes mature without duplicate event rows.
13. Switching tabs does not call Run Calculation.
14. Opening/closing fields does not call Run Calculation.
15. Primary search and field controls do not force horizontal mobile layouts.
16. `app.py` is the runnable entrypoint.
17. Runtime is pinned to `python-3.12`; source/dependencies satisfy the Python 3.12 contract.
18. Static inspection found no absolute local Windows user paths.
19. Copy Short, Copy All, and export controls remain present.
20. Optional-component failures preserve the previous valid canonical result and record safe fallback/error metadata.

## Validation environment

- Available local interpreter: Python 3.13.5
- Deployment contract: Python 3.12 via `runtime.txt` and `.python-version`
- Limitation: a separate Python 3.12 executable was not available in the validation container. Compatibility was checked through syntax/import tests, dependency markers, runtime-contract tests, and Streamlit startup under the available interpreter.

## Machine-readable artifacts

- `FINAL_VALIDATION_20260621.json`
- `FULL_PROJECT_INSPECTION_20260621.json`
- `PERFORMANCE_MEASUREMENTS_20260621_REGIME_TRUST.json`
- `reports/FINAL_TEST_SUMMARY_20260621.json`
