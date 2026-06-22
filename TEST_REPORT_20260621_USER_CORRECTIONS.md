# Test Report — 2026-06-21 User Corrections

## Final totals

| Validation | Result |
|---|---:|
| Collected pytest tests | 347 |
| Passed | 347 |
| Failed | 0 |
| Full-suite wall time | 95.40 seconds |
| Python source files compiled | 521 |
| Compile failures | 0 |
| Headless Streamlit startup | PASS |
| SQLite databases checked | 4 |
| SQLite integrity failures | 0 |
| DuckDB databases checked | 1 |
| DuckDB open failures | 0 |

Full pytest output is stored in `FULL_TEST_RESULTS_20260621_USER_CORRECTIONS.txt`.

## New focused coverage

`tests/test_lunch_user_corrections_20260621.py` verifies:

- Field 1 invokes only the requested full-metric and ten-decision history renderer.
- Hidden Field 1 implementations remain present for rollback.
- A valid canonical result can reconstruct the AI fact pack without Run Calculation.
- The Power BI direction evaluator uses the forecast origin, not target-candle body direction.
- Tiny predicted movements are non-actionable WAIT evidence.
- Direction evaluation is deterministic and leaves point forecasts equal.
- Field 6 contains research histories and the equation/theorem/concept/hypothesis registry, not Sections A–F.
- Field 6 reads a bounded projected table through a read-only database connection.
- AI history is catalogued under Field 5 rather than Field 6.

## Startup procedure used

The following process was started headlessly for 12 seconds and then terminated normally:

```powershell
streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8765
```

Observed startup message: `Uvicorn server started on 127.0.0.1:8765`.

## Dependency note

The test environment initially lacked two packages already declared in `requirements.txt`: Streamlit and DuckDB. The declared versions were installed before final validation. This was an environment preparation issue, not an application dependency omission.
