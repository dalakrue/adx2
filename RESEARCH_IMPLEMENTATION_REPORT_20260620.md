# Research Implementation Report — v2 Reliability and Distribution Shift

## Integration rule

All ten modules are supporting evidence beneath Full Metric Detail + History. None is an independent direction engine. The permitted actions are: confirm, reduce confidence, cap priority/trust, add an exact warning, or let the final Conformal Risk Control gate downgrade an existing BUY/SELL tradeability decision to WAIT. Direction reversal is prohibited and validated before publication.

## 1. Conformal Risk Control

**Paper:** Angelopoulos, Bates, Fisch, Lei, and Schuster, *Conformal Risk Control* (arXiv:2208.02814).

**Concept/theory:** choose a monotone prediction/action threshold so a bounded loss is controlled at a target level, with a finite-sample upper correction under the paper's assumptions.

**System mapping:** chronological settled outcomes generate bounded losses for false entry, SL-without-TP, incorrect high-confidence direction, and unsafe non-WAIT action. States are selected through hierarchical direction/horizon/session/regime/event-risk fallback with minimum support. Returned fields include target risk, observed risk, upper bound, threshold, condition, support, validity, and a monotonicity audit curve.

**Conservatism:** EURUSD H1 is serially dependent, so the application labels this an operational chronological approximation rather than claiming the paper's iid/exchangeability guarantee. CRC is the final statistical gate.

## 2. Multicalibration

**Paper:** Hébert-Johnson, Kim, Reingold, and Rothblum, *Multicalibration: Calibration for the (Computationally-Identifiable) Masses* (arXiv:1711.08513).

**Concept/theory:** calibration should hold over many overlapping, computationally identifiable subpopulations rather than only globally.

**System mapping:** direction probabilities are checked over session, UTC hour, H1/H4/D1 regime, volatility, direction, horizon, event risk, conflict, counter-trend, transition-risk buckets, and supported intersections. Minimum support, hierarchical global fallback, shrinkage, and a ±0.15 maximum adjustment prevent tiny-group overfit. Raw/calibrated probability, gap, support, fallback, and group diagnostics are published.

## 3. RevIN

**Paper:** Kim et al., *Reversible Instance Normalization for Accurate Time-Series Forecasting against Distribution Shift* (ICLR 2022).

**Concept/theory:** normalize each input instance/window and exactly reverse the transformation on model output to reduce non-stationary distribution effects.

**System mapping:** a reversible wrapper computes mean/std only from the available trailing input window and round-trips compatible price-space forecast contributors. Original and RevIN points are retained. Influence remains disabled unless a compatible contributor exposes the required interface and purged chronological settled evidence demonstrates superior performance.

## 4. Maximum Mean Discrepancy

**Paper:** Gretton et al., *A Kernel Two-Sample Test*, JMLR 13 (2012).

**Concept/theory:** distributions differ when their kernel mean embeddings differ in a characteristic RKHS.

**System mapping:** bounded RBF-kernel MMD compares recent versus roughly 25-day reference features, current-session versus historical-session features, and recent versus reference residual vectors when present. A time-aware block permutation null is used. The result includes statistic, threshold, p-value, significance, severity, and standardized shifted-feature diagnostics.

## 5. BBSE label-shift correction

**Paper:** Lipton, Wang, and Smola, *Detecting and Correcting for Label Shift with Black Box Predictors* (ICML 2018; arXiv:1802.03916).

**Concept/theory:** under label shift, a reference confusion matrix maps current predicted-label frequencies to current class priors; inversion is valid only with sufficient support and conditioning.

**System mapping:** the module builds a chronological reference confusion matrix for BUY/SELL/WAIT, verifies class support, rank, and condition number, estimates current priors, and derives bounded correction weights. It rejects correction when strong MMD feature drift contradicts the label-shift-only assumption. TP-first/SL-first correction is not applied without a validated pre-outcome touch-class predictor.

## 6. Double/Debiased Machine Learning

**Paper:** Chernozhukov et al., *Double/Debiased Machine Learning for Treatment and Structural Parameters* (The Econometrics Journal, 2018; arXiv:1608.00060).

**Concept/theory:** orthogonalized residual moments and cross-fitting reduce regularization bias in treatment-effect estimation under identification assumptions.

**System mapping:** an offline-only function estimates event effects for H+1/H+3/H+6 return, MFE, MAE, and realized volatility using pre-treatment market features, chronological cross-fitting, and purge/embargo. It returns effect, standard error, confidence interval, support, and identification warnings. It is never run during tab navigation or normal rendering.

## 7. Invariant Risk Minimization diagnostics

**Paper:** Arjovsky, Bottou, Gulrajani, and Lopez-Paz, *Invariant Risk Minimization* (arXiv:1907.02893).

**Concept/theory:** useful predictive relationships should remain stable across environments rather than exploit environment-specific correlations.

**System mapping:** lightweight ridge diagnostics form environments from sessions, regimes, volatility, event risk, and chronological periods. Sign, coefficient, rank, and environment-loss stability generate feature labels of stable, environment-specific, or unsupported. This is explicitly a diagnostic, not heavy neural IRM training.

## 8. Group DRO validation

**Paper:** Sagawa, Koh, Hashimoto, and Liang, *Distributionally Robust Neural Networks for Group Shifts: On the Importance of Regularization for Worst-Case Generalization* (ICLR 2020; arXiv:1911.08731).

**Concept/theory:** model selection should consider worst-group loss, with regularization/early stopping needed to avoid poor worst-group generalization.

**System mapping:** existing probability and point-direction candidates are evaluated across session/regime/volatility/direction/horizon/conflict/event groups. The report returns average loss, worst-group loss/group/support, regularization penalty, and robust selection score. Existing model weights are never changed without separate settled walk-forward superiority.

## 9. Robust Random Cut Forest

**Paper:** Guha, Mishra, Roy, and Schrijvers, *Robust Random Cut Forest Based Anomaly Detection on Streams* (KDD 2016; arXiv:1606.06793).

**Concept/theory:** random cut trees expose points that cause disproportionate structural displacement; co-displacement supports streaming anomaly scoring.

**System mapping:** the live implementation maintains bounded market/system feature windows and deterministic random-cut-tree path scoring for market returns/range/pressure/volume/volatility/ADX/DI and system residual/disagreement/calibration/missingness/API/synchronization features. It returns separate scores, trust caps, and robust-deviation contributions once per new canonical H1 generation.

**Important limitation:** the bundled dependency-free implementation is a bounded random-cut-tree forest approximation. It does not claim exact dynamic RRCF co-displacement equivalence. This is disclosed in every payload and in the limitations report.

## 10. Path signatures

**Paper:** Chevyrev and Kormilitzin, *A Primer on the Signature Method in Machine Learning* (arXiv:1603.03788).

**Concept/theory:** truncated iterated integrals summarize ordered path geometry; Chen's identity enables composition of path segments.

**System mapping:** a lead-lag path is built from normalized return, range, pressure, volume change, volatility, and time. Level 2 is used, producing a bounded 156-dimensional vector; level 3 is rejected by the dimensional guard for this 12-dimensional lead-lag path. Signature evidence is supporting-only for Similar-Day, KNN, regime-transition, and anomaly confirmation.

## Decision integration order

1. MMD and random-cut anomaly evidence set warnings and trust caps.
2. BBSE adjusts priors only when support, conditioning, and feature-shift assumptions pass.
3. Multicalibration adjusts the selected direction probability only with supported/shrunk groups.
4. IRM and Group DRO constrain feature/model trust.
5. RevIN remains diagnostic unless settled superiority is proven.
6. DML enriches offline event evidence only.
7. Path signatures enrich similarity/transition/anomaly support only.
8. CRC is the final risk gate and may downgrade tradeability to WAIT with exact reasons.
