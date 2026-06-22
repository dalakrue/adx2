# Known Limitations

1. No live Streamlit Cloud deployment was performed from this environment.
2. No live Finnhub/market connector or broker data was used for the new tests.
3. The available interpreter for local execution was Python 3.13.5; package configuration targets Python 3.12, but a Python 3.12 interpreter was not available here for direct execution.
4. FFORMA remains shadow-only unless a separately produced compact artifact passes purged walk-forward, SPA and resource gates.
5. SPA fast tests use 49 bootstrap iterations; production defaults to 1,000. Fast-profile p-values are suitable for deterministic plumbing tests, not final promotion.
6. Sparse condition/regime slices correctly return insufficient evidence.
7. Covariate-shift conformal falls back when overlap/ESS/support is weak; it does not guarantee coverage for arbitrary future shift.
8. The exponential-histogram and DDSketch-style code is a lightweight in-project adaptation, not a claim of byte-for-byte equivalence to every reference implementation.
9. Static closed-tab testing verifies no call path to new research code; browser CPU on every device was not profiled.
10. No accuracy, profitability, TP-hit-rate or reliability uplift is claimed.
11. The one-shot `pytest -q` command exceeded the bounded tool window, so every test file was executed separately; the final aggregate is 290 passed and 0 failed.
12. Existing legacy/compatibility modules remain, by protection rule, even where source duplication exists.
