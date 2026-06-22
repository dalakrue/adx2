# Evidence and Limitations

## Evidence retained

- Original protected source paths and separate reconciled display path.
- Canonical calculation ID/generation and completed-H1 watermark on each evidence row.
- Per-table catalog grain/key, watermarks and deterministic record keys.
- Cache hit/miss/admission/eviction diagnostics.
- Performance rows with tab, renderer, row count, browser rows, payload, duration, Python allocation, RSS and cache status.
- Machine-readable source/widget/cache/network/session/copy/render inventories.
- Byte-exact canonical database rollback backup.

## Limitations

1. Full live Settings latency and accuracy cannot be measured without the user’s authenticated market data, exact current generation and production Streamlit deployment.
2. Browser websocket/DOM/phone temperature were not measured; server-side row counts and serialized payload were measured.
3. Streamlit reruns execute top-level lightweight shell code; true field gates prevent heavy renderer imports/calls, not every shell statement.
4. CQR’s original exchangeability guarantee does not directly hold for serial EURUSD H1. The implementation uses chronological calibration and labels this limitation.
5. MinT is display-only and does not replace protected source forecasts or weights.
6. PELT is changepoint evidence only and cannot create BUY/SELL direction.
7. Diebold–Mariano requires aligned origin, target, actual and named benchmark; otherwise it returns `INSUFFICIENT DATA`.
8. Matrix Profile is bounded to 6/12/24-hour windows and runs once per completed-H1 transaction, not continuously.
9. Optional Parquet/DuckDB archive is intentionally inactive because the measured packaged history does not justify migration.
10. Static scans identify probable calls/references but cannot determine every dynamic import/cache object size. Runtime diagnostics cover the new bounded caches and history queries.

## Secret scan

A final credential-pattern scan found zero `sk-`/API-key/bearer-shaped values in all four packaged SQLite databases and zero hard-coded secret-shaped literals in the new TinyLFU cache, history browser and AI persistence paths. Synthetic redaction strings may exist only inside tests.
