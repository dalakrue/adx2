# Test Report — 2026-06-20

## Result

**269 passed, 0 failed.**

The repository collects 269 tests after adding the 24-test v2 acceptance file. The environment enforces a five-minute command limit, and the older first-generation research tests accumulate substantial cache/state when all are run in one pytest process. Therefore the complete suite was executed in bounded file batches and isolated node groups. Every collected test was exercised and passed. This execution strategy is reported rather than presenting the timed-out monolithic command as a result.

## New v2 acceptance coverage — 24/24 passed

1. static no-future-leakage scan;
2. appended-future-row invariance;
3. deterministic same-input output;
4. completed-candle cutoff;
5. chronological purge/embargo;
6. small-sample fallback;
7. missing-column/optional failure safety;
8. MMD no-shift and synthetic shift;
9. random-cut normal stream and injected anomaly;
10. BBSE known prior shift;
11. ill-conditioned confusion rejection;
12. multicalibration supported subgroup improvement;
13. CRC risk and monotonicity;
14. RevIN inverse/no-leakage window;
15. IRM environment stability;
16. Group DRO worst-group validation;
17. DML placebo/synthetic treatment;
18. signature dimension/composition contract;
19. canonical ID/generation/timestamp and SQLite staging;
20. tab navigation no recalculation;
21. Python/Streamlit Cloud startup contract;
22. mobile/closed-field structure preservation;
23. memory/runtime bounds;
24. complete adapter reuse and regression-suite presence.

## Existing regression coverage — 245/245 passed

Includes canonical runtime, Full Metric synchronization, decision product, causal quant, Power BI paths, multiscale probabilistic upgrade, one-click system-wide calculation, performance architecture, selective-WAIT policy, Settings restoration, Similar-Day, Streamlit Cloud, mobile/NLP/AI, first-generation ten-paper research calibration, trust history, UI restoration, requirements, and Windows connection-reset behavior.

## Other verification

- `python -m compileall -q app.py adx_dashpoard.py main.py core services tabs tests`: passed.
- `streamlit run app.py --server.headless true --server.port 8517`: started.
- `/_stcore/health`: returned `ok`.
- Streamlit import check: passed after installing the declared `streamlit>=1.35,<2` requirement; tested version was 1.58.0.

## Important testing discovery

The future-row invariance test exposed an in-place mutation of a nested forecast mapping in the first v2 draft. It was corrected with targeted copy-on-write mappings. The final tests confirm the original pre-research canonical input remains unchanged.
