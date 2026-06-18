# ADX Quant Pro EURUSD H1 — Multi-Scale Probabilistic Upgrade

## Main entry point

- Main file: `app.py`
- Local command: `streamlit run app.py`
- Streamlit Cloud runtime: `python-3.12` from `runtime.txt`

## Changed files

1. `core/multiscale_probabilistic_upgrade_20260618.py` — new additive hidden risk/calibration layer.
2. `core/settings_run_orchestrator_20260617.py` — integrates the layer once inside the existing Settings transaction and republishes the same canonical result to every tab.
3. `core/canonical_runtime_20260617.py` — versioned shared-result fields, invariant validation, and one-way adapter propagation.
4. `core/decision_product_engine_20260617.py` — future timestamps are now explicitly blocking model evidence while completed rows remain usable.
5. `ui/full_metric_shared_renderer_20260618.py` — restores the complete current-first Full Metric history and complete CSV export without changing formulas.
6. `tests/test_multiscale_probabilistic_upgrade_20260618.py` — deterministic, causal, quantile, regime, cache, decomposition, and synchronization tests.

## Implemented concepts

- Hidden D1/H4/H1 CALM/TURBULENT/CRISIS volatility regimes with robust Student-t emissions and causal GARCH-like conditional variance.
- Static D1 transitions; H4/H1 time-varying transitions selected only when held-out transition log loss improves.
- Normalized Shannon entropy, dwell age, historical duration distribution, survival/transition probabilities, stability, change risk, and probabilistic transition windows.
- Soft 27-state D1 × H4 × H1 probability tensor and multi-scale agreement score.
- Coherent deterministic six-hour residual-vector scenario paths with P10/P25/P50/P75/P90, TP/SL touch probability, MFE and MAE. Existing central PowerBI path is preserved.
- Regime-conditioned volatility cone: CALM narrow, TURBULENT medium, CRISIS wide.
- TFT-style static/known/observed feature classes, dynamic weights, gating, suppression reasons and weighted contributions.
- N-BEATS-style additive decomposition with backward residual correction and reconciliation invariant.
- PatchTST-style causal 3h/6h/24h/120h summaries.
- Meta-labels for direction, tradeability, timing, risk, regime support, path support and event/liquidity condition.
- Calibrated reliability combining existing reliability with entropy, agreement, transition risk, coverage, sample size and path uncertainty.
- Versioned Layer-10 canonical data contract with calculation ID and layer execution metadata.
- Cache reuse, dirty-input hashing, deterministic seed, compact canonical records, and no heavy calculation on tab navigation.
- Existing regime tables are enriched in-place; no new visible section or top-level navigation item was created.

## Validation and tests

- Python compilation: PASS for every Python file.
- Requirements syntax: PASS.
- Main entry import: PASS.
- Streamlit headless startup and `/_stcore/health`: PASS (`ok`).
- Project tests: 100 passed across isolated test-module runs.
- New upgrade tests: 5 passed.
- Causality/future-row tests: PASS.
- Same-input deterministic-output tests: PASS.
- Quantile ordering and band monotonicity: PASS.
- D1/H4/H1 probability sums: PASS.
- 27-state probability sum: PASS.
- Volatility state ordering: PASS.
- Forecast decomposition reconciliation: PASS.
- Canonical adapter sync: PASS.
- Cache reuse and short-history fallback: PASS.
- Database/ledger persistence and API failure isolation: PASS through existing test suite.

A single-process `pytest -q` run in this container stalled due to an existing cross-test resource interaction, so every test module was executed in isolated groups. The complete collected set was 100 tests, and all 100 passed.

## Explicit limitations / honest unavailable metrics

- No full neural TFT, N-BEATS or PatchTST package was added. Their lightweight architectural concepts were implemented because live training would increase CPU/RAM/mobile heat and violate the requested staged runtime.
- No R/MSGARCH runtime or full skewed-t maximum-likelihood MS-GARCH training was added. The implementation uses robust Student-t state emissions, a causal GARCH-like variance recursion and validated transition selection.
- Exact PBO requires multiple competing strategy/model configurations; the project preserves one protected engine, so the canonical field remains unavailable with an explicit reason.
- Exact Deflated Sharpe Ratio requires aligned net strategy returns and the number of tried strategies; these are not inferred from forecast residuals.
- Exact Diebold-Mariano comparison requires an aligned named benchmark loss series, which the current history table does not store.
- Purged chronological fold stability, embargo metadata, MAE/RMSE, coverage, Brier, pinball and calibration metrics are implemented when completed samples exist; unavailable values remain `None` with reasons rather than fabricated substitutes.

## Protection confirmations

- Full Metric History calculations and formulas were not edited.
- Existing directional regime, Alpha/Delta, KNN, Greedy, PowerBI red/yellow/blue paths, NLP, history, copy and export behavior remain protected.
- No new top-level tab, page, sidebar item or visible section was added.
- Lunch, Dinner, Finder, Research and Data Visualization consume one canonical published generation.
- All new market calculations are causal and completed-candle-only.
- The package is a complete project, not an isolated patch.
