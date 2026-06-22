# Existing Research Inventory

**Inventory boundary:** code and reports present in the uploaded package before the 2026-06-21 implementation.  
**Important:** the word “implemented” means a code adaptation or diagnostic inspired by the research concept. It does not imply exact reproduction of every paper experiment, theorem assumption, or production guarantee.

## Existing ten-paper causal calibration layer (2026-06-18)

| # | Existing paper/concept | Existing algorithm mapping | Main implementation |
|---|---|---|---|
| 1 | Adaptive Conformal Inference Under Distribution Shift | bounded adaptive coverage controller by H+1…H+6 and condition | `core/research_calibration_20260618.py` |
| 2 | Conformal Prediction for Time Series | coherent six-horizon residual-vector bootstrap and empirical bands | same |
| 3 | Bayesian Online Changepoint Detection | lightweight Bayesian run-length/transition-risk evidence | same |
| 4 | Adaptive Windowing | nine causal evidence windows with drift-sensitive sizes | same |
| 5 | Dynamic Model Averaging / Dynamic Occam’s Window | bounded horizon-specific weights and suppression/reactivation | same |
| 6 | Conditional Method Confidence Set | supported candidate set before dynamic weights | same |
| 7 | Probability of Backtest Overfitting | chronological experiment registry and deterministic split evaluation | same |
| 8 | Deflated Sharpe Ratio | DSR from aligned returns/trial distribution/skew/kurtosis | same |
| 9 | Deep Evidential Regression theory | separate aleatoric and epistemic diagnostic scores; no live deep training | same |
| 10 | DLinear-style challenger baselines | causal trend/remainder challenger and residual fallback | same |

## Existing ten-paper risk and scoring layer (2026-06-19)

| # | Existing paper/concept | Existing algorithm mapping | Main implementation |
|---|---|---|---|
| 1 | Intraday periodicity normalization | causal 168 hour-of-week robust normalization | `core/research_risk_stack_20260619.py` |
| 2 | Proper scoring rules | CRPS, energy score, sharpness, calibration and baseline skill | same |
| 3 | Competing risks | TP-first/SL-first/neither/censored/ambiguous settlement | same |
| 4 | Anytime-valid confidence sequences | incremental time-uniform trust boundaries | same |
| 5 | Selective prediction/risk–coverage | fixed threshold risk/coverage curves with subgroup fallback | same |
| 6 | Extreme Value Theory tail protection | GPD when supported; empirical POT fallback | same |
| 7 | Invariant evidence reliability | cross-environment sign/rank stability diagnostics | same |
| 8 | Risk-constrained Kelly theory | informational multiplier capped at 0.25; never sends orders | same |
| 9 | Wasserstein-style robust expectancy | downside ambiguity penalty and qualification gate | same |
| 10 | Hawkes-style event-cluster intensity | bounded exponential-decay event/shock intensity | same |

## Existing ten-paper history-first performance layer (2026-06-20)

| # | Paper/concept | Existing algorithm mapping | Main implementation |
|---|---|---|---|
| 1 | TinyLFU: A Highly Efficient Cache Admission Policy | bounded admission/frequency concepts for reusable evidence | `core/history_research_pipeline_20260620.py` and cache modules |
| 2 | C-Store: A Column-oriented DBMS | projected history columns and columnar archive concepts | history store/archive modules |
| 3 | Maintenance of Materialized Views | incremental history materialization and watermarks | history evidence/store modules |
| 4 | The Dataflow Model | event-time, completed-H1 and watermark discipline | history pipeline |
| 5 | M4 time-series aggregation | display-oriented bounded time-series reduction | history/UI adapters |
| 6 | Matrix Profile I | motifs, discords and Similar-Day support | history research and similarity modules |
| 7 | PELT / optimal changepoints | linear-cost changepoint evidence | regime history modules |
| 8 | Conformalized Quantile Regression | interval calibration on settled residuals | history research pipeline |
| 9 | MinT forecast reconciliation | coherent path reconciliation | Power BI reconciliation/history modules |
| 10 | Comparing Predictive Accuracy | settled forecast-loss comparison/DM-style evidence | history research pipeline |

## Existing ten-paper advanced reliability/distribution-shift layer (2026-06-20)

| # | Paper/concept | Existing algorithm mapping | Main implementation |
|---|---|---|---|
| 1 | Conformal Risk Control | final bounded risk gate that may downgrade tradeability to WAIT | `core/advanced_reliability_shift_20260620.py` |
| 2 | Multicalibration | supported/shrunk group probability calibration | same |
| 3 | RevIN | reversible normalization diagnostic; no promotion without evidence | same |
| 4 | Maximum Mean Discrepancy | block-permutation feature/residual shift diagnostic | same |
| 5 | BBSE label-shift correction | support/conditioning checked prior correction | same |
| 6 | Double/Debiased Machine Learning | offline event-effect estimator with chronological cross-fitting | same |
| 7 | Invariant Risk Minimization | lightweight cross-environment ridge diagnostics | same |
| 8 | Group DRO | average/worst-group validation and robust selection score | same |
| 9 | Robust Random Cut Forest | bounded dependency-free random-cut-tree anomaly approximation | same |
| 10 | Path signatures | bounded level-2 lead-lag path signature support | same |

## Non-duplication conclusion for the requested 2026-06-21 layer

The uploaded package did not contain dedicated modules or exact persisted schemas for:

- Giacomini–White conditional predictive ability with HAC inference by the requested condition grid;
- Hansen SPA with moving-block bootstrap and all promotion gates;
- covariate-shift weighted conformal ESS/support safeguards in shadow comparison;
- FFORMA-style offline feature-to-existing-path weights;
- fixed-share expert tracking with per-settlement weight audit;
- ML Test Score machine-readable production-readiness rubric;
- a declarative pre-calculation and prepublication data-validation generation gate;
- exponential-histogram operational counters;
- DDSketch-style bounded relative-error quantile monitoring.

Those items were therefore added as a distinct 2026-06-21 validation/shadow layer. Existing ACI/CQR, DMA/MMSE, drift, calibration, regime, reliability, and history algorithms were reused as fallbacks or comparison baselines rather than replaced.
