# Complete Test Report — Ten-Paper Shadow Layers

## Baseline before changes

- All 489 original Python files compiled successfully.
- The initial full pytest invocation exceeded the execution window after 48 tests had passed.
- No baseline failure had appeared before timeout, but this is recorded as **incomplete**, not as a complete baseline pass.

## After changes

`pytest --collect-only -q` collected **296 tests**. Every collected node was executed in controlled groups:

- passed: **296**;
- failed: **0**;
- skipped: **0**;
- unavailable: **0** after the declared Streamlit dependency was installed in the verification environment.

A single cumulative-process invocation of `test_ten_paper_research_calibration_20260618.py` stalled after 31 dots around a dependency-import boundary. The file was then executed as 31 tests plus its final 2 tests; all 33 unique tests passed. This is an execution-environment anomaly, not hidden as a full one-shot pass.

## New focused tests

`tests/test_ten_paper_shadow_layers_20260621.py`: **6 passed**.

Coverage includes:

- Model-X deterministic construction and no automatic removal;
- central online FDR wealth/alpha records;
- reject-option no reversal and no WAIT promotion;
- two-window flexible loss with fixed versioned weights;
- six monotonicity contracts;
- exact delta/full-recompute equality;
- all 12 required metamorphic relations;
- CALM coordination classification;
- protected canonical output preservation;
- deterministic transaction/output hashes;
- bounded provenance and no DataFrame in research canonical state;
- SQLite idempotency and lineage queries;
- atomic rollback preserving the previous completed generation;
- exactly one orchestrator builder call and zero renderer calls;
- separate 4A/4B dispatcher functions;
- migration replay idempotency.

## Compilation

All active Python files compile. The final compile count is recorded in `COMPILE_REPORT_20260621_TEN_PAPER.json`.

## App and deployment tests

- `app.py` started with Streamlit in headless mode.
- `/_stcore/health` returned `ok`.
- Streamlit and all changed core/UI modules imported successfully.
- Existing Streamlit Cloud preflight tests passed.
- Migration applied twice to a temporary database and verified successfully.

## Final hardening revalidation

After the explicit boundary/provenance schema hardening, the six focused tests passed again, changed canonical/store/UI paths passed in isolated regression processes, nine Cloud/requirements tests passed, the old-schema additive migration smoke passed, all 493 Python files compiled, and the final Streamlit health check returned `ok`. Some cumulative pytest processes can stall during teardown after printing completed test dots; fresh-process execution is used and this anomaly is not counted as a product failure.

## Honesty statement

These tests establish software behavior on the tested inputs. They do not establish improved accuracy, profitability, theorem-level FDR control, causal validity, or lower production resource usage.
