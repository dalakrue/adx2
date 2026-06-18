# Full Metric History, Dinner AI, and NLP News Restore — 2026-06-18

## Completed changes

- Restored the complete Lunch Full Metric Details flow so rendering continues after the Entry Decision table.
- Restored ordered display of Session, 010 Reverse, Entry, Direction, Hold, Exit, TP, Metric, Full Metric, and any additional existing dataframe tables.
- Isolated each table renderer so one table error cannot hide the tables below it.
- Restored the complete Full Metric History and all available per-factor metric histories.
- Changed historical display ordering to current/latest completed H1 first. Older backtest rows remain available below the current rows.
- Kept KNN and Greedy ranking fields as secondary evidence instead of allowing an old high-ranked row to appear first.
- Restored a visible Dinner inner selector with Unified Regime + Logic and AI Assistant.
- Removed duplicate Research/NLP API-key entry placement. Research NLP now shows connection status and actions; the key remains managed in Settings/sidebar.
- Consolidated Research NLP to one top 10-day ranked-news table.
- Added deterministic news fields for Priority, KNN Score, Greedy Score, Impact Score, Likely EURUSD Impact, Protection Score, protection action, and decision impact.
- Added real-news deduplication and a button-gated public RSS fallback when the connected/cached news set is sparse. No placeholder/fabricated article rows are created.
- The NLP table targets at least 10 real articles when enough current sources are available and clearly reports when fewer real articles are available.

## Validation completed

- `PYTHONPATH=. pytest -q` — 43 passed.
- `PYTHONPATH=. python tools/validate_architecture.py` — passed.
- `PYTHONPATH=. python tools/validate_final_sync_20260617.py` — passed.
- `PYTHONPATH=. python tools/validate_finnhub_nlp_restore_20260617.py` — passed.
- Focused latest-first test — passed, including an older rank-1 row below the newest H1 row.
- Focused 10+ ranked-news test — passed with impact and protection columns.

## Run command

```bash
streamlit run app.py
```
