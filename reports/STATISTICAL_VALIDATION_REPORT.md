# Statistical Validation Report

## Conditional predictive ability

- Settled-only observations.
- H+1 through H+6 and requested condition slices when support exists.
- HAC/Newey–West standard error with overlap-aware lag.
- Explicit `INSUFFICIENT_CONDITIONAL_EVIDENCE` for sparse slices.
- No weight or promotion decision from p-value alone.

## Superior predictive ability

- Existing production calculation is the benchmark.
- Challengers are aligned existing paths/configurations.
- Serial dependence is handled with deterministic moving blocks.
- Fixed seeds are derived from source generation, horizon and candidate identity.
- Promotion requires all statistical, calibration, regime, resource, second-window and rollback gates.

## Covariate-shift conformal

- Weighted residual quantiles are calculated separately by horizon.
- ESS and maximum-weight share are surfaced.
- Missing covariates, poor overlap, small ESS and concentration trigger the existing canonical interval fallback.
- The result is shadow-only and stores comparisons rather than replacing the existing interval.

## FFORMA and fixed-share

- FFORMA training is offline and explicit; runtime only loads/evaluates a small artifact.
- Fixed-share updates only after complete settlement and records old/new weights and loss.
- Weight normalization, floors, ceilings and maximum hourly changes are tested.

## Monitoring approximation policy

- Operational counters may use bounded exponential-histogram concepts.
- Quantile summaries remain exact below 1,024 observations and retain recent raw observations.
- DDSketch-style summaries use a documented default 1% relative error only for eligible monitoring metrics.
- Price, settlement, TP/SL, 25-day core history, accounting and final promotion statistics are never approximated by these modules.

## Interpretation limits

These tests validate implementation invariants and deterministic statistical plumbing. They do not prove that a challenger is economically superior, that coverage will hold under all future market shifts, or that live trading profitability improves.
