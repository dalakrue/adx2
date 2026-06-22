# History-Table Data Dictionary

All five required analytical histories include `timestamp`, `run_id`, and `calculation_generation`. The DuckDB sidecar is additive and does not replace the canonical trading store.

## `regime_transition_history`

| Column | Meaning |
|---|---|
| `timestamp` | UTC time the evidence row was persisted |
| `run_id` | Canonical calculation ID that recorded the event |
| `calculation_generation` | Canonical generation number |
| `transition_time` | Confirmed regime transition time |
| `previous_regime` | Regime before the transition |
| `new_regime` | Regime after the transition |
| `change_probability` | Combined transition-evidence probability, 0–100 |
| `drift_type` | Required drift taxonomy label |
| `run_length_before` | BOCPD most-likely run length before/currently around change |
| `confirmation_delay_bars` | Number of completed H1 bars between transition and confirmation snapshot |
| `volatility_before` | Prior rolling volatility estimate |
| `volatility_after` | Recent rolling volatility estimate |
| `forecast_disagreement` | Normalized cross-model disagreement, 0–100 |
| `calibrated_regime_trust` | Calibrated regime trust, 0–100 |
| `trigger_summary` | Safe plain-language evidence summary |

Uniqueness: one physical event per `(transition_time, previous_regime, new_regime)`.

## `post_transition_outcome_history`

| Column | Meaning |
|---|---|
| `timestamp` | UTC time of latest outcome maturation |
| `run_id` | Canonical run that last supplied newly settled evidence |
| `calculation_generation` | Generation that last matured the event |
| `transition_time` | Related transition time |
| `new_regime` | Regime entered |
| `entry_reference_price` | Close/reference price at transition |
| `actual_close_1h`, `actual_close_2h`, `actual_close_3h`, `actual_close_6h` | Settled closes after each horizon |
| `direction_correct_1h`, `direction_correct_3h`, `direction_correct_6h` | Whether the regime-implied direction matched the settled movement |
| `maximum_favorable_excursion` | Best movement during the bounded post-transition window |
| `maximum_adverse_excursion` | Worst movement during the bounded post-transition window |
| `regime_still_active_6h` | Whether the new regime remained active six hours later |

Uniqueness: one row per `(transition_time, new_regime)`. Missing outcomes mature incrementally without duplicating the event.

## `prediction_calibration_history`

| Column | Meaning |
|---|---|
| `timestamp`, `run_id`, `calculation_generation` | Canonical identity and persistence time |
| `raw_confidence` | Existing model/ensemble confidence before calibration |
| `calibrated_confidence` | Empirically adjusted confidence |
| `predicted_direction` | Published prediction direction |
| `actual_direction` | Settled direction where available |
| `absolute_close_error` | Absolute settled close error |
| `interval_lower`, `interval_upper` | Adaptive conformal/PID interval |
| `actual_inside_interval` | Settled coverage indicator |
| `rolling_coverage` | Rolling empirical coverage |
| `expected_calibration_error` | Reliability-bin ECE |
| `brier_score` | Binary probabilistic score where applicable |

Uniqueness: one row per canonical `run_id` and generation.

## `drift_detector_history`

| Column | Meaning |
|---|---|
| `timestamp`, `run_id`, `calculation_generation` | Canonical identity and persistence time |
| `bocpd_probability` | Bayesian online change-point probability |
| `adwin_detection_status` | `CHANGE` or `STABLE` evidence status |
| `adaptive_window_size` | Internal adaptive window size |
| `drift_type` | Classified drift label |
| `forecast_spread` | Relative spread across existing forecast models |
| `error_drift_score` | Settled prediction-error drift score |
| `volatility_drift_score` | Volatility-shift score |
| `action_taken` | Evidence-only action/fallback explanation |

Uniqueness: one row per canonical `run_id` and generation.

## `decision_audit_history`

| Column | Meaning |
|---|---|
| `timestamp`, `run_id`, `calculation_generation` | Canonical identity and persistence time |
| `master_decision` | Existing protected master decision |
| `less_risky_decision` | Existing/evidence-constrained safer display decision |
| `priority_rank` | Existing canonical priority rank |
| `regime` | Existing canonical regime |
| `regime_trust` | Calibrated trust score |
| `forecast_reliability` | Existing reliability score |
| `conflict_status` | Existing regime-versus-prediction conflict status |
| `data_freshness` | `CURRENT`, `AGING`, or `STALE` |
| `fallback_use` | Whether fallback data/result was used |
| `reason_summary` | Safe plain-language explanation |

Uniqueness: one row per canonical `run_id` and generation.

## `component_error_history`

Internal operational log with `timestamp`, `component`, `run_id`, `calculation_generation`, `exception_type`, `safe_summary`, and `fallback_used`. It stores no API key or secret field.

## Analytical view

`regime_transition_matches` joins transition events to matured outcomes by transition time and new regime. It is a view, not a duplicated physical table.
