# Research-to-Feature Mapping

The upgrade is an additive evidence, calibration, storage, and audit layer. It does **not** replace the existing LSTM, Transformer, XGBoost, Prophet, Power BI, regime, reliability, KNN priority, greedy-ranking, conflict, counter-trend, NLP, or Similar-Day calculations.

| Research work | Implemented concept | Application feature | Safety boundary |
|---|---|---|---|
| Adams & MacKay, **Bayesian Online Changepoint Detection** | Bounded posterior over run length with a Normal-Gamma predictive model | BOCPD probability, most-likely run length, and run-length uncertainty | Evidence only; never writes the protected regime or direction |
| Bifet & Gavaldà, **Learning from Time-Changing Data with Adaptive Windowing** | Adaptive split-window mean test with a bounded internal window | ADWIN-style status and effective adaptive-window size | Visible 25-day history is untouched; adaptation is internal only |
| Gama et al., **A Survey on Concept Drift Adaptation** | Multi-signal drift taxonomy | `NONE`, `SUDDEN`, `GRADUAL`, `INCREMENTAL`, `RECURRING`, `VOLATILITY_ONLY`, `FEATURE_DRIFT`, `PREDICTION_ERROR_DRIFT` | No single detector can overwrite the existing regime engine |
| Gibbs & Candès, **Adaptive Conformal Inference Under Distribution Shift** | Rolling empirical coverage and residual quantiles | Adaptive lower/upper bands, rolling coverage, target coverage, coverage error | Reuses settled predictions and existing forecast point/bands |
| Angelopoulos, Candès & Tibshirani, **Conformal PID Control for Time Series Prediction** | Proportional, integral, and derivative feedback on interval coverage | P/I/D components and next interval-width adjustment | Bounded adjustment; does not create a new point-forecast model |
| Guo et al., **On Calibration of Modern Neural Networks** | Reliability-bin calibration diagnostics | Raw versus calibrated confidence and expected calibration error | Calibrates confidence presentation, not model direction |
| Lakshminarayanan et al., **Simple and Scalable Predictive Uncertainty Estimation Using Deep Ensembles** | Cross-model dispersion as epistemic-style evidence | Forecast disagreement across existing LSTM/Transformer/XGBoost/Prophet outputs | No new ensemble model or retraining is added |
| Sculley et al., **Hidden Technical Debt in Machine Learning Systems** | Explicit lineage, schema versioning, fingerprinting, fallback, and one canonical publication | System Trust Audit, error history, canonical run/generation checks | Last valid result remains visible after optional-component failure |
| Raasveldt & Mühleisen, **DuckDB: An Embeddable Analytical Database** | Embedded columnar analytical sidecar and projected reads | Normalized trust/history tables, top-five transition queries, Parquet checkpoints | Canonical trading snapshot remains in its protected existing transaction |
| Ahmad et al., **DBToaster: Higher-Order Delta Processing for Dynamic, Frequently Fresh Views** | Delta-oriented inserts, deduplication, maturation updates, and views | Incremental history writes; post-transition outcomes mature without duplicate event rows | No full database rebuild after widget interaction |

## Source modules

- `core/regime_transition_trust_20260621.py`: BOCPD, adaptive-window evidence, drift classification, calibration, conformal PID, transition matching, and audit payload.
- `core/regime_trust_store_20260621.py`: DuckDB schema, incremental inserts, outcome maturation, projected reads, view, Parquet checkpoints, and error history.
- `ui/regime_transition_trust_center_20260621.py`: cached-only Dinner renderer.
- `core/lunch_search_20260621.py` and `ui/lunch_search_20260621.py`: Enter-to-search over published canonical/history data only.
