# Full Project Inspection — 2026-06-21

This inventory hashes every packaged file, reads every text/configuration file, parses every Python module, and inventories each readable SQLite/DuckDB schema without executing trading calculations.

## Coverage

- Files inspected: **839**
- Bytes inspected: **9,409,764**
- Python files parsed: **505**
- Python syntax errors: **0**
- Database files inventoried: **5**
- Absolute local Windows-path findings: **0**

## Entrypoint and runtime

- `app.py`: present
- `runtime.txt`: `python-3.12`

## Extension inventory

| Extension | Files |
|---|---:|
| `.py` | 505 |
| `.txt` | 170 |
| `.md` | 104 |
| `.json` | 30 |
| `.csv` | 13 |
| `.sqlite3` | 4 |
| `<none>` | 2 |
| `.toml` | 2 |
| `.sql` | 2 |
| `.log` | 2 |
| `.src` | 2 |
| `.bat` | 1 |
| `.bak` | 1 |
| `.duckdb` | 1 |

## Database inventory

| File | Engine | Objects |
|---|---|---:|
| `data/adx_runtime_store.sqlite3` | sqlite | 8 |
| `data/adx_similarity_store.sqlite3` | sqlite | 6 |
| `data/canonical_runtime.sqlite3` | sqlite | 230 |
| `data/quant_app.sqlite3` | sqlite | 9 |
| `data/regime_trust_history.duckdb` | duckdb | 7 |

## Machine-readable detail

See `FULL_PROJECT_INSPECTION_20260621.json` for per-file SHA-256, size, line count, Python imports/functions/classes/Streamlit calls, and complete database object metadata.

## Interpretation boundary

Static inspection proves package coverage and source integrity. Runtime behavior is covered separately by automated tests, import/compile checks, and the Streamlit startup health test.
