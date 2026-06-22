# Research Paper-to-Code Mapping — 2026-06-21

All ten additions are supporting validation/shadow mechanisms. None creates an independent BUY/SELL engine, and none can directly reverse BUY to SELL or SELL to BUY.

## 1. Tests of Conditional Predictive Ability — Giacomini and White

- **Code:** `core/conditional_predictive_ability_20260621.py`
- **Inputs:** chronologically settled canonical and existing method forecasts only.
- **Slices:** H+1…H+6, major/minor regime when supported, session, volatility, transition risk, event risk, trend strength and forecast disagreement.
- **Losses:** MAE, directional Brier, CRPS when quantiles exist, interval score, and existing documented system loss where present.
- **Inference:** Newey–West/HAC mean-loss-difference statistic with lag at least `horizon-1` for overlapping horizons.
- **Decision rule:** p-value alone is insufficient; sample, standardized effect and adjacent chronological stability must pass.
- **Persistence:** `conditional_predictive_ability_history`.

## 2. A Test for Superior Predictive Ability — Hansen

- **Code:** `core/superior_predictive_ability_20260621.py`
- **Benchmark:** existing production/canonical calculation.
- **Challengers:** existing method/configuration columns only.
- **Bootstrap:** deterministic moving-block bootstrap; production default 1,000 iterations, fast test profile 49.
- **Promotion gates:** sufficient settled OOS sample, SPA significance, meaningful positive effect, calibration not worse, no important-regime catastrophe, resource budget, second chronological window and rollback availability.
- **Current mode:** shadow; promotion is false unless every gate is explicitly evidenced.
- **Persistence:** `research_spa_results`.

## 3. Conformal Prediction Under Covariate Shift — Tibshirani, Barber, Candès and Ramdas

- **Code:** `core/covariate_shift_conformal_20260621.py`
- **Covariates:** available ATR percentile, ADX, DI spread, session, major regime, regime age, compression, event intensity, residual scale and MMD shift.
- **Weighting:** bounded historical relevance weights; weighted residual quantiles per H+1…H+6.
- **ESS:** `(sum(w)^2) / sum(w^2)`.
- **Safeguards:** poor overlap, concentrated weights, small ESS, missing covariates, unstable shift and sparse slices.
- **Fallback:** existing ACI/CQR/canonical interval; no immediate replacement.
- **Persistence:** `covariate_shift_conformal_history`.

## 4. FFORMA: Feature-based Forecast Model Averaging — Montero-Manso et al.

- **Code:** `core/fforma_shadow_weighting_20260621.py`
- **Adaptation:** chronological 25-day/regime/session/volatility/horizon blocks act as training cases for one EURUSD H1 series.
- **Model:** small ridge/softmax-style artifact with bounded existing-path weights.
- **Runtime:** loads and evaluates a compact artifact only; training is an explicit offline action.
- **Validation:** purged walk-forward, SPA and resource approval are mandatory before any promotion.
- **Persistence:** `fforma_shadow_history`; compact artifact metadata only.

## 5. Tracking the Best Expert — Herbster and Warmuth

- **Code:** `core/fixed_share_expert_tracker_20260621.py`
- **Experts:** existing forecast paths.
- **Update:** bounded settled loss, exponential loss update, fixed share, normalization, floors, ceilings and maximum hourly change.
- **Safety:** incomplete/duplicate/invalid settlements are ignored; deterministic settlement IDs prevent duplicate updates; no directional logic is altered.
- **Persistence:** `expert_weight_history`, `expert_tracker_state`, `expert_tracker_comparison`.

## 6. The ML Test Score — Breck et al.

- **Code:** `core/ml_production_readiness_score_20260621.py`
- **Groups:** data, model development, infrastructure, monitoring.
- **Checks:** schema, usefulness evidence, computation cost, secrets/privacy, reproducibility, baseline, slices, staleness, tests, rollback, debuggability, numerical stability, dependency changes, invariants, train/production skew, CPU/RAM and settled-quality regression.
- **Output:** four group scores, overall score, critical/warning counts and promotion flag.
- **UI:** compact summary is inserted into existing metadata/reliability fields only.
- **Persistence:** `ml_production_readiness_history`.

## 7. Data Validation for Machine Learning — Breck et al.

- **Code:** `core/canonical_data_validation_20260621.py`
- **Gates:** source frame before calculation and canonical payload before publication.
- **Critical-failure policy:** reject generation, preserve previous valid canonical result, record exact constraints, do not repair prices, and do not use partially valid rows.
- **Identity:** deterministic generation ID, source hash and idempotent records.
- **Persistence:** `data_quality_generation`, `data_quality_constraint_result`, `data_quality_metric_history`, `rejected_calculation_generation`.

## 8. Automating Large-Scale Data Quality Verification — Schelter et al.

- **Code:** `core/declarative_data_quality_20260621.py`
- **Method:** declarative `Constraint` objects and shared single-pass frame aggregates.
- **Checks:** required OHLC/metadata, numeric/datetime/finite, uniqueness, monotonic H1 frequency, missing/duplicate candles, timezone/freshness/completeness, OHLC inequalities, spread, probabilities/scores, forecast chronology, settlement chronology, row reconciliation, schema and transform consistency.
- **Safety:** exact observed/expected/violation details are persisted.

## 9. Maintaining Stream Statistics over Sliding Windows — Datar et al.

- **Code:** `core/sliding_monitoring_statistics_20260621.py`
- **Allowed approximate counters only:** coverage pass/fail, validation/connector/calculation failures, drift alerts, regime changes and WAIT downgrades.
- **Not approximated:** OHLC, settled prices, 25-day core history, TP, SL, accounting or final promotion statistics.
- **Method:** bounded exponential-histogram buckets after the exact/recent representation.
- **Persistence:** `sliding_monitoring_state`.

## 10. DDSketch — Masson, Rim and Lee

- **Code:** `core/bounded_quantile_monitoring_20260621.py`
- **Exact threshold:** exact observations while history is small; default switch threshold 1,024.
- **Relative error:** default 1% for positive magnitudes, documented in each state.
- **Eligible metrics:** calculation/database latency, memory, absolute forecast error, normalized residual, interval width, MFE, MAE, drift and anomaly scores.
- **Investigation support:** recent raw observations remain available.
- **Persistence:** `bounded_quantile_monitoring_state`.

## Orchestration mapping

- **Builder:** `core/research_validation_layer_20260621.build_research_validation_transaction`.
- **Call site:** `core/settings_run_orchestrator_20260617.py`, after settlement and existing research refresh and before canonical publication.
- **Atomic store:** `services/canonical_snapshot_store.py` delegates the additive bundle to `core/research_validation_store_20260621.py` inside the same `BEGIN IMMEDIATE` transaction.
- **Fast testing:** set `ADX_TEST_PROFILE=fast`; it reduces bounded test fixture sizes and SPA iterations without changing production defaults or protected decision semantics.
