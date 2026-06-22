# Ten Advanced Research Papers for ADX Quant Pro EURUSD H1

## Design constraints used for these recommendations

- Keep every existing protected score, table, model, forecast, history, and decision calculation.
- Add research methods as **shadow validation, calibration, weighting, monitoring, or gating layers** first.
- No external AI API and no heavy new model dependency.
- Heavy research computations run only after **Run Calculation + Open Lunch**.
- Store compact summaries and bounded histories; do not duplicate full DataFrames in session state or SQLite JSON.
- Never claim that a research method guarantees trading profit. Statistical guarantees concern coverage, error rates, regret, or test validity under stated assumptions.

---

## 1. “Conformalized Quantile Regression” — Romano, Patterson, and Candès (NeurIPS 2019)

**Core concept.** Combine lower/upper quantile forecasts with conformal residual calibration. Instead of showing an unverified forecast band, widen or narrow it using recent out-of-sample nonconformity scores.

**Working belief/assumption.** Under exchangeability, the calibration residuals and future residual are symmetric enough for rank-based coverage. EURUSD H1 is not strictly exchangeable, so use a rolling, regime-aware calibration window and clearly label the guarantee as empirical/rolling rather than unconditional.

**Theoretical principle.** Split conformal calibration provides finite-sample marginal coverage under exchangeability. CQR preserves local heteroscedastic structure from quantile estimates while conformal correction targets coverage.

**Benefit to this system.** Calibrate the existing Power BI lower/upper bands, report achieved 25-day coverage, and prevent narrow but unreliable bands from producing an A/A+ priority. This directly improves forecast uncertainty honesty and TP/SL interval reliability without replacing the existing forecast engines.

**Lightweight implementation.**

1. Use settled `prediction_outcomes` only.
2. For each horizon and regime, calculate `max(lower - actual, actual - upper, 0)`.
3. Take a rolling conformal quantile for target coverages such as 80%, 90%, and 95%.
4. Adjust existing lower/upper bands in a shadow result.
5. Publish raw band, calibrated band, sample size, achieved coverage, and calibration age.
6. Fall back to pooled-horizon calibration when a regime bucket is too small.

**Acceptance tests.** No future rows enter calibration; raw predictions remain unchanged; calibrated lower ≤ predicted ≤ calibrated upper; coverage history is reproducible; small-sample fallback is explicit.

Official source: https://proceedings.neurips.cc/paper/2019/hash/5103c3584b063c431bd1268e9b5e76fb-Abstract.html

---

## 2. “Adaptive Conformal Inference Under Distribution Shift” — Gibbs and Candès (NeurIPS 2021)

**Core concept.** Update the conformal miscoverage level online as the market distribution changes rather than using one static quantile forever.

**Working belief/assumption.** Forecast errors drift through regimes, sessions, volatility bursts, and news periods. A feedback controller that reacts to recent misses can maintain better long-run calibration than a fixed window alone.

**Theoretical principle.** Adaptive Conformal Inference modifies the target quantile using observed coverage errors and provides long-run calibration behavior under broad online distribution-shift settings. It does not promise every individual interval will cover.

**Benefit to this system.** Bands can widen after a sequence of misses and recover gradually after stability. This gives a mathematically motivated Forecast Aging/Calibration state and reduces overconfident entries immediately after regime change.

**Lightweight implementation.**

1. Maintain one scalar `alpha_t` per horizon, optionally per major regime.
2. After a settled outcome, update `alpha_{t+1} = clip(alpha_t + gamma * (target_error - observed_error))` using the paper’s sign convention consistently.
3. Use bounded `gamma` and minimum/maximum coverage limits.
4. Reset or partially pool on severe drift.
5. Record every update in compact calibration history.
6. Use it as a reliability multiplier, not as a replacement prediction engine.

**Acceptance tests.** Updates happen only after settlement; no look-ahead; alpha remains bounded; repeated misses widen bands; repeated coverage does not cause abrupt collapse; behavior is deterministic for fixed history.

Official source: https://proceedings.neurips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html

---

## 3. “Tracking the Best Expert” — Herbster and Warmuth (Machine Learning, 1998)

**Core concept.** Use a Fixed-Share style online ensemble that can follow the best changing sequence of experts, not merely the single best model over the entire history.

**Working belief/assumption.** LSTM, Transformer, XGBoost, Prophet, KNN, Greedy, regime, and full-metric signals can have regime-dependent usefulness. The winning expert can switch, but switches should be penalized to avoid noise chasing.

**Theoretical principle.** Tracking algorithms provide regret bounds relative to a comparator sequence with a limited number of expert switches. The switch/share parameter controls adaptation versus stability.

**Benefit to this system.** Replace static display weights with a **shadow dynamic weight recommendation** based on settled proper loss. The existing 0.35/0.30/0.25/0.10 forecast weights stay protected until the shadow layer passes validation.

**Lightweight implementation.**

1. Define each existing forecast source as an expert.
2. Score settled forecasts with bounded absolute error, log loss, or CRPS-compatible proxy.
3. Exponentially update weights and apply a small fixed-share mass to every expert.
4. Maintain separate H1 horizon/regime weight states only when sample size is sufficient.
5. Cap any single expert’s weight.
6. Compare static and dynamic ensembles in shadow history.

**Acceptance tests.** Weights sum to one; no expert gets zero forever; only settled outcomes update weights; switch count is tracked; shadow ensemble must beat static weights out-of-sample before promotion.

Official source: https://link.springer.com/article/10.1023/A%3A1007424614876

---

## 4. “The Combination of Forecasts” — Bates and Granger (Operational Research Quarterly, 1969)

**Core concept.** Combine forecasts using their error variance and covariance instead of selecting one forecast or averaging without regard to correlated mistakes.

**Working belief/assumption.** Forecast combination is valuable when individual errors are not perfectly correlated. Highly correlated models should not receive redundant weight merely because each looks accurate alone.

**Theoretical principle.** Under quadratic loss and estimated error covariance, appropriately weighted combinations can have lower error variance than component forecasts. Estimation error can make complex weights unstable, so shrinkage toward equal weights is prudent.

**Benefit to this system.** Add covariance-aware diversity to Forecast Agreement. Two bullish forecasts with nearly identical errors count as less independent evidence than two forecasts with complementary errors.

**Lightweight implementation.**

1. Build a rolling settled-error matrix by horizon.
2. Estimate covariance with diagonal shrinkage.
3. Solve non-negative weights summing to one, or use inverse-error covariance approximations.
4. Blend 50–80% toward existing/static weights when sample size is limited.
5. Publish ensemble diversity, effective expert count, and weight stability.

**Acceptance tests.** No singular-matrix crash; deterministic shrinkage fallback; weights are bounded; out-of-sample comparison against simple average and protected weights; correlated duplicate experts do not double confidence.

Official source: https://link.springer.com/article/10.1057/jors.1969.103

---

## 5. “Tests of Conditional Predictive Ability” — Giacomini and White (Econometrica, 2006)

**Core concept.** Test whether one forecast is better than another **conditional on current information**, rather than relying only on one unconditional average accuracy number.

**Working belief/assumption.** A model may be useful in BEAR_NORMAL or London overlap and poor in compression or low-liquidity hours. Evaluation should ask “when is it better?”

**Statistical principle.** Conditional predictive ability tests use loss differentials and instruments/state variables to assess equal predictive ability in realistic rolling-window environments.

**Benefit to this system.** Create a regime/session/horizon trust map for each model and each major decision component. This can explain why the assistant trusts one source now without changing protected predictions.

**Lightweight implementation.**

1. Compute settled loss differential between candidate and benchmark.
2. Use state indicators: regime, session, volatility quartile, conflict flag, freshness.
3. Apply HAC-robust variance or a conservative block bootstrap.
4. Require minimum sample count and correct for repeated tests.
5. Publish `BETTER / INCONCLUSIVE / WORSE`, effect size, sample size, and stability.

**Acceptance tests.** Time-order preserved; overlapping horizons handled with robust variance; insufficient data returns INCONCLUSIVE; no model is promoted based only on in-sample results.

Bibliographic source: Giacomini, R. and White, H. (2006), “Tests of Conditional Predictive Ability,” Econometrica 74, 1545–1578, DOI 10.1111/j.1468-0262.2006.00718.x.

---

## 6. “A Test for Superior Predictive Ability” — Hansen (Journal of Business & Economic Statistics, 2005)

**Core concept.** Test whether the best apparent alternative truly outperforms a benchmark after comparing many alternatives.

**Working belief/assumption.** When many indicators, thresholds, horizons, and model variants are tried, one can appear best by chance. Weak or poor alternatives should not excessively reduce test power.

**Statistical principle.** The SPA test uses studentized performance differentials and bootstrap inference to improve power while controlling the multiple-comparison problem relative to a benchmark.

**Benefit to this system.** Before promoting a new priority formula, model weight, calibration method, or history pattern, require evidence that it beats the existing protected method rather than merely topping a leaderboard.

**Lightweight implementation.**

1. Define one protected benchmark and a registered set of candidate shadow methods.
2. Use settled out-of-sample loss only.
3. Apply stationary/block bootstrap suitable for serial dependence.
4. Store candidate registry and number of trials.
5. Promote only when SPA p-value, effect size, stability, and operational checks all pass.

**Acceptance tests.** Candidate list is frozen before evaluation; same sample for all candidates; bootstrap seed recorded; no promotion from raw best score alone; p-values and economic effect reported together.

Official source: https://www.tandfonline.com/doi/abs/10.1198/073500105000000063

---

## 7. “A Reality Check for Data Snooping” — White (Econometrica, 2000)

**Core concept.** Adjust performance claims for the fact that many strategies/rules were searched on the same data.

**Working belief/assumption.** Research iteration creates selection bias even when each individual backtest appears properly calculated. The true null concerns the best searched rule, not a preselected rule.

**Statistical principle.** White’s bootstrap Reality Check tests whether the best rule in a searched family outperforms a benchmark while accounting for data snooping.

**Benefit to this system.** Add a Research Integrity table showing number of tried configurations, corrected significance, and whether a claimed improvement survives data-snooping correction.

**Lightweight implementation.**

1. Assign every tested strategy variant a stable experiment ID.
2. Store losses, date range, parameters, and benchmark before viewing final results.
3. Use block bootstrap over loss differentials.
4. Report naive best, Reality-Check-adjusted result, and trial count.
5. Never delete failed experiments from the registry.

**Acceptance tests.** Trial registry append-only; benchmark fixed; temporal blocks preserved; corrected results are never more optimistic than uncorrected selection claims; insufficient history returns NOT TESTABLE.

Official source: https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00152

---

## 8. “The Probability of Backtest Overfitting” — Bailey, Borwein, López de Prado, and Zhu (Journal of Computational Finance)

**Core concept.** Estimate how often the strategy selected as best in-sample performs poorly out-of-sample using Combinatorially Symmetric Cross-Validation (CSCV).

**Working belief/assumption.** A single train/test split is unstable for strategy selection, especially with limited and dependent financial samples. Repeated symmetric partitions reveal selection fragility.

**Statistical principle.** PBO estimates the probability that the in-sample winner has below-median out-of-sample performance. The associated degradation/logit diagnostics expose selection overfit.

**Benefit to this system.** Quantify whether a new priority rule, TP selection rule, or pattern-recognition table is likely overfit before it affects live decisions.

**Lightweight implementation.**

1. Divide settled chronological history into an even number of contiguous blocks.
2. Enumerate or sample symmetric train/test block combinations.
3. Select the best candidate in each train partition.
4. Rank that selected candidate in the paired test partition.
5. Calculate PBO, performance degradation, and confidence interval.
6. Use bounded candidate sets and cached block statistics to control CPU/RAM.

**Acceptance tests.** No random row shuffling; all candidates share identical partitions; parameter trials are included; PBO > threshold blocks promotion; result reports uncertainty when history is short.

Official source: https://www.risk.net/journal-of-computational-finance/2471206/the-probability-of-backtest-overfitting

---

## 9. “Learning from Time-Changing Data with Adaptive Windowing” — Bifet and Gavaldà (SDM 2007)

**Core concept.** ADWIN automatically changes the history-window length when statistically significant distribution change is detected.

**Working belief/assumption.** Fixed 25-day or fixed-N windows are sometimes too slow after regime change and too noisy during stability. Window length should reflect detected change rate.

**Theoretical principle.** ADWIN compares subwindows using concentration bounds, shrinking the window when the observed mean difference is unlikely under stationarity. Its compressed variants are designed for data streams with bounded memory.

**Benefit to this system.** Add drift-aware effective windows for reliability, forecast error, priority accuracy, and conflict rates while preserving the visible 25-day history table. This can reduce stale influence and CPU/RAM by retaining compact statistics.

**Lightweight implementation.**

1. Feed bounded values such as error %, direction correctness, interval miss, and conflict indicator.
2. Maintain one detector per critical metric/horizon, not per raw feature.
3. On drift, mark a new calibration epoch and reduce old-history weight.
4. Store only detector summary, change time, old/new means, and effective window length.
5. Keep hard minimum evidence before changing decisions.

**Acceptance tests.** No look-ahead; false-alarm sensitivity configurable; stable stream does not repeatedly reset; synthetic shift is detected; detector state remains small; drift only changes shadow reliability until validated.

Official source: https://epubs.siam.org/doi/10.1137/1.9781611972771.42

---

## 10. “The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction” — Breck, Cai, Nielsen, Salib, and Sculley (IEEE Big Data 2017)

**Core concept.** Production reliability requires tests for data, models, infrastructure, and monitoring—not only offline accuracy.

**Working belief/assumption.** Most failures in a trading decision system can occur around the model: stale data, schema mismatch, silent fallback, leakage, inconsistent clocks, duplicate UI actions, unbounded caches, or missing monitoring.

**Engineering principle.** The paper presents 28 concrete tests/monitoring needs and a scoring rubric for production readiness. This is an operational framework rather than a profit or statistical theorem.

**Benefit to this system.** Create a System Readiness Score that reflects actual safety gates: schema health, data freshness, time alignment, feature validity, prediction invariants, settlement completeness, drift, cache bounds, mobile controls, and rollback readiness.

**Lightweight implementation.**

1. Map each applicable rubric item to PASS/WARN/FAIL/NOT-APPLICABLE.
2. Add tests for input schema, timestamp monotonicity, missing/inf values, train-serving parity, prediction range, deterministic fallback, stale generation, ledger migration, and copy/export identity.
3. Separate blocking failures from informational warnings.
4. Store only current score plus small audit history.
5. Show exact failed checks in Field 6 and Grounded AI system-health answers.

**Acceptance tests.** Every score links to a concrete check; no hidden manual override; failure prevents false “READY”; test histories are bounded; critical failures survive UI reruns and are cleared only by a valid new generation.

Official source: https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/

---

# Recommended implementation order

## Phase 1 — operational reliability and drift

1. ML Test Score-inspired readiness checks.
2. ADWIN shadow drift monitor.
3. CQR rolling coverage audit.

These deliver immediate reliability value with low CPU/RAM and no model replacement.

## Phase 2 — uncertainty and ensemble adaptation

4. Adaptive Conformal Inference.
5. Bates–Granger covariance-aware shadow combination.
6. Fixed-Share expert tracking.

Promote only after settled out-of-sample evidence.

## Phase 3 — research-governance gates

7. Conditional Predictive Ability reports.
8. SPA promotion test.
9. White Reality Check.
10. PBO/CSCV.

These prevent research additions from appearing accurate merely because many alternatives were tried.

# Reusable implementation command

```text
Upgrade the uploaded ADX Quant Pro EURUSD H1 project using the ten-paper research blueprint in ADVANCED_RESEARCH_BLUEPRINT_20260622.md.

NON-NEGOTIABLE PROTECTION RULES
1. Do not delete, reduce, rename, move, replace, or silently change any existing protected calculation, score, ML model, forecast, priority, regime, table, chart, tab, history, export, copy payload, or decision output.
2. Add every new research method as a read-only shadow/calibration/validation/monitoring layer first. Do not promote a shadow result into the live decision unless explicit out-of-sample acceptance criteria pass.
3. No external AI API, no heavy LLM, and no new top-level page/tab/menu. Keep additions inside existing Lunch Fields, especially Field 6 for research readiness and Field 5 for grounded explanations.
4. Heavy calculations may run only after Run Calculation + Open Lunch. Opening/closing a field must never trigger calculation.
5. Use one canonical completed generation across all tabs. Never mix timestamps or results from different generations.
6. Internal timestamps remain UTC. Display broker time using the configured broker UTC offset and display Myanmar separately as UTC+6:30.
7. Use only settled prediction outcomes for calibration and evaluation. Prevent all look-ahead leakage and preserve chronological order.
8. Keep RAM/CPU bounded: compact state, rolling windows, cached summaries, no duplicate full DataFrames, bounded SQLite histories, and lazy rendering.

IMPLEMENTATION ORDER
A. Add an ML production-readiness rubric with concrete schema, freshness, timestamp, feature, prediction, ledger, cache, fallback, and mobile/export checks.
B. Add ADWIN shadow drift monitors for direction correctness, forecast error, interval misses, reliability, and conflict rate.
C. Add Conformalized Quantile Regression calibration for existing forecast bands, with rolling achieved-coverage history and explicit small-sample fallback.
D. Add Adaptive Conformal Inference for online coverage adaptation after settled outcomes only.
E. Add Bates–Granger covariance-aware shadow forecast weights with shrinkage toward protected weights.
F. Add Fixed-Share/Tracking-the-Best-Expert shadow weights with bounded switching and weight caps.
G. Add conditional predictive ability reports by regime, session, volatility, horizon, conflict, and freshness.
H. Add SPA, White Reality Check, and PBO/CSCV research-promotion gates using a registered append-only experiment set.

REQUIRED OUTPUTS
- Exact modified-file list and architecture explanation.
- Database migrations that are idempotent and self-healing on old Streamlit Cloud databases.
- Unit tests for every method, leakage prevention, schema migration, stale data, missing data, deterministic fallback, mobile copy buttons, and broker/Myanmar time display.
- Synthetic tests proving drift response and conformal coverage behavior.
- Out-of-sample shadow comparison against the current protected benchmark.
- A final ZIP containing the complete project, not only changed files.
- A test report that honestly states passed tests, failures, skipped tests, and anything not fully verified.

Do not only write recommendations. Inspect the whole project, implement the safe shadow layers, run tests, fix discovered integration errors, and return the complete corrected ZIP.
```
