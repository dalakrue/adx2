# Implementation Report — ADX Quant Pro History-First Hardening

## Protected-logic result

No existing trading formula, protected ten-decision value, Decision 11 support rule, BUY/SELL/WAIT/NO TRADE direction, TP/SL, priority, sizing, KNN, Greedy, regime, reliability, conflict, NLP or source path was intentionally changed. Research outputs are historical evidence, calibration, display reconciliation or warnings only. MinT writes a separate display copy; original paths remain retained. PELT cannot create direction. Diebold–Mariano returns `INSUFFICIENT DATA` unless origins/targets/actuals align.

## Implemented changes

- True load gates precede every expensive default Lunch field; imports occur only inside an enabled branch.
- Fields 4 and 5 are combined only under one placement gate with exclusive 4A/4B workspaces.
- Morning and Research heavy module imports are gated.
- One common history identity contract and 35 additive evidence tables were added.
- The evidence bundle commits in the same SQLite transaction as the canonical snapshot.
- Idempotent record keys and per-table watermarks prevent duplicate rows for identical completed-H1 input.
- Bounded column projection, newest-completed-H1 ordering, server-side LIMIT and explicit full export were added.
- TinyLFU admission diagnostics and performance-history storage were added.
- M4 display-only aggregation was added to the cached Power BI historical path renderer.
- Matrix Profile windows 6/12/24, bounded PELT, chronological CQR, display-only MinT and aligned DM validation were implemented.
- Optional heavy libraries remain lazy; `n_jobs=1` is enforced in three existing parallel model locations for Streamlit Cloud.
- AI question/answer grounding history redacts credential-like strings and stores no API key fields.

## History tables

The catalog documents grain, business key and purpose for every table. Counts by area: Field 1 = 6, Field 2 = 4, Field 3 = 7, Field 4A = 6, Field 4B = 7, Field 6 = 3, System = 2. See `DATABASE_MIGRATION_REPORT_20260620_HISTORY_EVIDENCE.md` and `DATABASE_SCHEMA_INVENTORY_20260620.json`.

## Memory/CPU controls

Large evidence remains disk-backed. Browser limits are 48 rows on phone and 120 on desktop for the new evidence browser. TinyLFU is bounded to 48 entries/12 MB. Export bytes are created only after a button press. Display cache keys contain canonical/data identity, selected table/columns and row limit—not secrets. Full-frame deep copies were not introduced; new preparation code uses projection and shallow/copy-on-write behavior.

## Measured result

The controlled closed-Lunch dispatch benchmark changed from **20.768 ms/rerun and 8.0 heavy calls** to **0.013 ms/rerun and 0.0 heavy calls**. This isolates dispatch only and is not presented as live market latency. Full details and limitations are in `PERFORMANCE_REPORT_20260620_BEFORE_AFTER.md`.
