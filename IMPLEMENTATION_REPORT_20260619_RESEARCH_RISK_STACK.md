# ADX Quant Pro EURUSD H1 — Research Risk Stack Implementation Report

Release date: 2026-06-19  
Entry command: `python -m streamlit run app.py`

## Architecture confirmed

- True Streamlit entry: `app.py` → `adx_dashpoard.main` → `core.app_shell.run_app`.
- One-click orchestrator: `core/settings_run_orchestrator_20260617.py`.
- Canonical published result: `core/canonical_runtime_20260617.py`.
- Full Metric authority: `core/full_metric_canonical_adapter_20260618.py`, using the existing metric result history as the source of truth.
- Settled forecast source: `core/trust_history_20260619.py` and the existing SQLite ledger.
- No second BUY/SELL/WAIT direction engine was added. The research layer can confirm, reduce confidence, lower priority, or force WAIT only.

## Files changed

1. `core/research_risk_stack_20260619.py` — new unified lightweight research/risk stack.
2. `core/settings_run_orchestrator_20260617.py` — causal normalization before existing engines; one research transaction before canonical publication.
3. `core/canonical_runtime_20260617.py` — shared adapter propagation to Reliability, Power BI, AI grounding and all tabs.
4. `core/compact_canonical_20260619.py` — compact synchronized research summary.
5. `core/causal_quant_support_20260618.py` — normalized drift/change-point/volatility/compression/entropy support while preserving raw inputs.
6. `core/prediction_ledger_20260617.py` — compact normalized run persistence; full DataFrames are no longer duplicated in `calculation_runs.result_json`.
7. `ui/trusted_operational_metrics_20260619.py` — compact Lunch Quick Decision research metrics.
8. `ui/full_metric_history_center_20260619.py` — mobile-safe compact columns and expanded research detail.
9. `tabs/clean_decision_regime_ui_20260614.py` — research status inside the existing System Trust Center.
10. `ui/powerbi_cached_renderer_20260619.py` — uses bounded research confidence, bands, weights and risk warnings without hiding the projection.

## Research concepts implemented

### 1. Intraday periodicity normalization

`build_periodicity_normalization` creates causal 168 hour-of-week buckets. Every bucket estimate is shifted so the current observation is excluded. It uses robust medians for absolute return, range, ATR, volume/tick volume and residual scale, then falls back causally through session and fixed bootstrap/global scales. Raw values remain available.

Outputs include hour-of-week, expected volatility, normalized return/range/ATR/volume/residual, sample count and reliability. The normalized signals feed the existing causal drift, transition, anomaly, compression and entropy support.

### 2. Proper scoring

`build_proper_scoring` calculates CRPS for H1–H6 from existing quantiles, joint path Energy Score, sharpness, calibration and skill versus naive/drift baselines. Only settled forecasts are used. Weight influence is exponentially smoothed and clipped.

### 3. Competing-risk TP/SL probability

`build_competing_risk` and `_event_for_row` classify TP-first, SL-first, neither, censored and same-candle ambiguous outcomes from settled predictions plus completed candles. Censored rows are never counted as losses. BUY and SELL statistics are produced for 1/2/3/6 hours with contextual fallback from full condition to session/direction, direction and global history.

### 4. Anytime-valid sequential trust monitor

`build_confidence_sequences` keeps incremental sufficient statistics and a settlement watermark in SQLite. It monitors direction accuracy, TP-first rate, net pips, interval coverage and BUY/SELL/WAIT reliability with time-uniform empirical-Bernstein-style boundaries and the requested trust statuses.

### 5. Selective risk–coverage control

`build_selective_prediction` uses the fixed threshold grid 50–90. It builds global and subgroup risk/coverage curves for direction, session and major regime, then applies sparse-group fallback. It does not create direction; failed controls integrate with the existing WAIT protection.

### 6. EVT tail protection

`build_evt_tail` evaluates adverse excursion, residual, normalized-return and post-event tails. It uses SciPy GPD fitting only when SciPy is already present and the sample is sufficient; otherwise it uses an empirical peaks-over-threshold fallback. It can raise risk or block an entry but cannot reverse direction.

### 7. Invariant evidence reliability

`build_invariance` compares robust effect signs and rank correlations across session, regime, volatility and historical environments. It reports feature dispersion, recent stability, environment count and a bounded support weight. Features are never deleted automatically and no economic causality claim is made.

### 8. Risk-constrained Kelly multiplier

`build_risk_multiplier` produces an informational 0–1 multiplier, conservatively capped at 0.25. It is forced to zero for non-positive expectancy, insufficient history, degraded calibration/trust, EVT block or failed robust expectancy. It never recommends leverage or sends orders.

### 9. Wasserstein-style robust expectancy

`build_robust_expectancy` reuses existing scenarios/results and applies a downside ambiguity penalty that increases with low sample size, drift, calibration weakness, residual shift, EVT risk and event intensity. It only qualifies or blocks the canonical candidate.

### 10. Lightweight event-cluster intensity

`build_event_intensity` uses H1 exponential decay over high-impact events, abnormal normalized candles, large residuals, regime warnings and volatility shocks. It reports background/self-excited/total intensity, 1h/3h shock probabilities and LOW/MEDIUM/HIGH/CRITICAL risk levels.

## Existing concepts reused rather than duplicated

- The project already contained Wasserstein-style distribution drift monitoring and a simple Kelly-related field. These were not replaced or duplicated; the new robust expectancy and risk multiplier consume the existing canonical evidence and add the requested safety gates.
- Existing conformal/calibration, regime, KNN, Greedy, Power BI and Full Metric engines remain intact.
- No requested research module was skipped. Modules 6–10 intentionally use the requested lightweight safety approximations rather than heavy solvers or new models.

## Canonical integration and performance protections

- Periodicity is calculated once on the cleaned completed-H1 staging frame before existing feature/regime builders.
- The ten-module transaction runs once after existing forecasting and settled-history updates, before final canonical publication.
- Results are reused through the canonical result, compact snapshot and session state; tab changes do not refit or recalculate them.
- No new API calls, background loops, TensorFlow, PyTorch, tick processing, large Monte Carlo or optimization solver.
- NumPy/Pandas vectorization, bounded tails, fixed threshold grids, small scenario arrays, shallow DataFrame reuse and SQLite incremental accumulators are used.
- Closed UI areas render compact cached fields; no new top-level page/tab/sidebar item was added.
- `calculation_runs.result_json` now stores only compact scalar audit data. Forecast, regime and drift history remains in normalized existing tables.

## Tests performed

- Modified-file Python compilation: PASS.
- Import smoke test for all modified modules: PASS.
- Ten-module synthetic end-to-end transaction: PASS.
- No-future-leakage invariant by appending future candles and comparing all earlier normalized rows: PASS.
- Settled-only proper scoring: PASS.
- Competing-risk censoring and same-candle ambiguity policy: PASS.
- Fixed selective threshold grid and hierarchical fallback: PASS.
- Direction non-reversal invariant: PASS.
- Empty/sparse/NaN-safe fallback: PASS.
- Compact ledger test with a 250,000-row DataFrame in memory: PASS; persisted JSON was 830 bytes and excluded the frame.
- Streamlit headless health startup: PASS.
- Real guest route and real `Run Calculation + Open Lunch` button: PASS on a deterministic completed EURUSD H1 fixture; completed in 61.954 seconds with zero Streamlit exceptions, errors or warnings.
- Navigation no-recalculation test across Lunch, Settings and Dinner: PASS; canonical run ID unchanged; 0.094–0.105 seconds per route in the test harness.
- Power BI renderer with research-adjusted bundle: PASS; 12 metrics and the existing Plotly projection chart rendered with no error.
- UTC-aware and naive time conversion paths: PASS in compile, integration and invariance tests; no timezone comparison exception observed.

## Performance comparison

| Behaviour | Result |
|---|---|
| Cold server health startup | 11.571 s in this container; no research calculation runs at startup |
| Normal tab navigation | Approximately 0.10 s in AppTest; same canonical run ID/timestamp |
| New stack, 360 OHLC + 133 settled rows | Median 2.190 s; 0.678 MB peak traced Python allocations |
| New stack, 1,300 OHLC + 1,073 settled rows | Median 7.252 s; 3.415 MB peak traced Python allocations |
| Idle CPU | No added loop or timer; effectively no new idle work |
| Persistent size | Compact research snapshot; no duplicated history frame in run JSON |
| Mobile impact | Compact metric rows, mobile-selected history columns and lazy details; no added chart outside existing Power BI |

The complete legacy full-system click remains much more expensive than the research layer because it still runs all protected existing models, history builders and exports. The new layer is bounded and executes only during that click.

## Honest limitations

- Live broker/news API credentials were not available in the isolated test environment. The full button test therefore used deterministic, completed, UTC-aware EURUSD H1 OHLC injected through the same canonical session source.
- SciPy GPD fitting is optional. Deployments without SciPy use the empirical POT fallback, as required.
- Proper-scoring, competing-risk, confidence-sequence, EVT and selective controls safely remain in insufficient/developing status until enough settled history exists; the run continues without crashing.
