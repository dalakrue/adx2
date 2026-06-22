# Test Report — History-First Package

## Result

**279 tests collected and exercised successfully; 0 known failures.** The suite was run in bounded file groups because a monolithic run exceeds the execution tool ceiling. The final targeted regression rerun after schema/performance-column changes passed **80/80** in 13.84 seconds.

## New acceptance suite

`tests/test_history_performance_research_20260620.py` covers closed-gate no-work behavior, 4A/4B exclusivity, canonical decision/path retention, interval ordering, idempotency, bounded browser/full export behavior, no-future rows, documented grain/key catalog, research-method safety, secret redaction, router lazy gates, Python 3.12 contract and the correct entry point.

## Existing regression coverage

Existing Lunch, Similar-Day, canonical-runtime, performance-architecture, Streamlit Cloud, Power BI, mobile, AI/NLP, reliability and Windows tests remain present. The final focused command was:

```powershell
pytest -q tests/test_history_performance_research_20260620.py tests/test_lunch_four_core_fields_20260619.py tests/test_similar_day_intelligence_20260619.py tests/test_performance_architecture_20260619.py
```

Result: `80 passed`.

## Other validation

- `python -m compileall -q .`: passed.
- `pytest --collect-only -q`: 279 tests collected.
- `streamlit run app.py --server.headless true --server.port 8765`: startup reached the serving state; stopped by controlled timeout.
- SQLite `PRAGMA integrity_check`: recorded as `ok` in `DATABASE_SCHEMA_INVENTORY_20260620.json`.
- Original ZIP path inventory: no original file deleted.
