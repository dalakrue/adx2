# ADX Quant Pro / new7 — Ten-Paper Causal Research Integration

**Release date:** 2026-06-18  
**Primary market:** EURUSD  
**Primary timeframe:** H1  
**Protected authority:** Full Metric Detail + History / Full Metric History  
**Preferred entry point:** `app.py`

## 1. Release outcome

The uploaded project was used as the only project base. The complete project was inspected before editing. The ten requested research ideas were integrated as one hidden, Streamlit-independent causal calibration layer that runs once inside the existing Settings → Run Calculation transaction, after protected Full Metric and existing Power BI path calculations and before atomic canonical publication.

The implementation does **not** add a top-level tab, page, sidebar item, menu item, visible section, duplicate prediction engine, duplicate Run Calculation button, duplicate API field, or separate Lunch/Dinner calculation.

Full Metric History remains the calculation authority. Protected Full Metric scores, existing directional meaning, existing score ranges, and the red/yellow/blue central paths are not replaced or recalculated by the research layer.

## 2. Runtime commands

### Main file

```text
app.py
```

### Installation

```bash
python -m pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py
```

The existing `main.py` and `adx_dashpoard.py` compatibility entry points remain present, but `app.py` is the preferred command.

## 3. Canonical architecture

The existing one-click Settings transaction now follows this effective sequence:

1. Existing data preflight and completed-H1 validation.
2. Existing feature and Full Metric History calculations.
3. Existing directional and multiscale volatility regime calculations.
4. Existing Power BI red/yellow/blue path construction.
5. Ten-paper research calibration:
   - causal challenger baselines;
   - coherent residual-vector conformal forecasts;
   - adaptive conformal coverage;
   - Bayesian run-length/changepoint inference;
   - adaptive estimation windows;
   - conditional model confidence sets;
   - bounded dynamic model averaging and Occam suppression;
   - PBO and DSR validation gates;
   - aleatoric/epistemic uncertainty separation;
   - bounded Reliability and decision-confidence refinement.
6. Existing NLP/event-risk confirmation.
7. Existing Full Metric authority confirmation pass.
8. One atomic canonical publication.
9. One read-only adapter generation reused by Lunch, Dinner, Finder, Research, NLP, AI Assistant, Reliability, Priority, Regime, and Power BI views.

Opening or changing a tab reads the published adapter and does not run the research calculations.

## 4. Research-paper implementations

### Paper 1 — Adaptive Conformal Inference Under Distribution Shift

Implemented a bounded adaptive coverage controller with separate state keys for each H+1 through H+6 horizon and the active volatility-regime/session/transition-risk condition.

Completed interval outcomes update exponentially smoothed observed coverage. Undercoverage gradually widens later bands; persistent overcoverage gradually narrows them. The correction is bounded to `0.65–2.50`, and each observation contributes through a clipped update so one extreme candle cannot cause an unlimited change. Repeating the same completed-H1 input reuses/recomputes the same evidence idempotently.

Persisted fields include target coverage, observed coverage, coverage error, adaptive correction, sample size, condition, and coverage quality.

### Paper 2 — Conformal Prediction for Time Series

Implemented a completed-outcome residual bank and coherent six-horizon residual-vector bootstrap. H+1 through H+6 errors from the same forecast origin remain together; six unrelated hourly residuals are never sampled independently.

The condition fallback hierarchy is:

1. volatility regime + session + direction;
2. volatility regime + direction;
3. volatility regime;
4. similar realized volatility;
5. all valid completed vectors.

The deterministic simulation seed is derived from the research calculation ID, data hash, and last completed H1 time.

Outputs include P10/P25/P50/P75/P90, lower/upper bands, TP touch probability, SL touch probability, probability above/below the current close, expected MFE, and expected MAE. Quantile and band invariants are asserted.

When fewer than 12 coherent completed system vectors exist, the layer uses a clearly labeled causal DLinear walk-forward residual fallback and reduces validation confidence rather than fabricating system history.

### Paper 3 — Bayesian Online Changepoint Detection

Implemented a lightweight Bayesian run-length engine over past-only standardized H1 return, absolute-return, range, and realized-volatility change features.

It produces most-likely run length, expected run length, probability of change now, probability of a change during the last three and six completed candles, continuation probability, transition risk, a probabilistic transition window, and LOW/MODERATE/HIGH confidence.

It does not emit a guaranteed regime-end time and does not independently force WAIT. Transition evidence is combined with uncertainty, reliability, path support, and protected Full Metric evidence.

### Paper 4 — Adaptive Windowing

Implemented nine independent adaptive-window states:

- prediction residuals;
- direction accuracy;
- reliability calibration;
- model performance;
- session performance;
- volatility estimation;
- feature importance;
- KNN candidate history;
- NLP-impact relationship.

Full stored history is never deleted. Window states only control which recent observations are eligible for current estimation. Drift magnitude and Bayesian transition risk shrink windows; stable evidence grows them. Updates are incremental and keyed to the last completed H1 timestamp.

The prediction-residual and model-performance windows directly bound live residual/model evidence. KNN window diagnostics and other states are exposed in the existing canonical details/JSON for their relevant consumers. States whose required specialized historical observations do not yet exist retain an honest sample-size warning.

### Paper 5 — Dynamic Model Averaging / Dynamic Occam’s Window

Implemented bounded, horizon-specific weighting among existing contributors that have completed error evidence. Current live contributors normally include the existing combined system path and existing red/yellow/blue path residual histories. Other existing model contributors become eligible only when model-specific completed residual histories are available; no model quality is invented.

Weights use recent conditional MAE evidence and a forgetting factor. Models sufficiently far outside the best conditional probability are temporarily suppressed, retain their history, record the suppression reason, and can reactivate automatically when their evidence improves.

A bounded-simplex projection guarantees that active weights sum to approximately one while respecting minimum and maximum bounds. A one-model valid ensemble is disallowed; the controller broadens to the nearest valid fallback evidence rather than assigning 100% weight.

The weights refine confidence/reliability and existing combined-path validation. They do not replace the protected red/yellow/blue central paths.

### Paper 6 — Conditional Method Confidence Set

Implemented an accepted-model set for each H+1 through H+6 active condition. Models with sufficient completed samples are compared against the best current conditional loss using a conservative sample-size-dependent equivalence margin.

The confidence set determines eligibility; dynamic model averaging assigns weights among eligible methods. Insufficient data produces a broader fallback and lower confidence rather than a claim of superiority.

The requested full condition grid is represented in the canonical contract, while live calculation evaluates the current active condition only. Exhaustive cross-product statistics are intentionally not recomputed on every Streamlit render. They become data-backed through completed conditioned outcomes/experiment registration.

### Paper 7 — Probability of Backtest Overfitting

Implemented a SQLite-backed development/validation experiment registry with configuration hashes, parameters, feature sets, thresholds, model weights, regime settings, train/validation/purge/embargo metadata, return/error/calibration metrics, selection state, and rejection reason.

The PBO function consumes the chronological period × configuration performance matrix and performs deterministic symmetric in-sample/out-of-sample selection/ranking splits. It measures how often the in-sample winner ranks below the out-of-sample median.

PBO is not used as a BUY/SELL signal. It is a validation/reliability gate. When fewer than four chronological periods or four configurations exist, value is `None` with an exact UNAVAILABLE reason.

### Paper 8 — Deflated Sharpe Ratio

Implemented DSR from actual aligned strategy returns, number of trials, trial Sharpe distribution, sample size, skewness, and kurtosis. It stores raw Sharpe, deflated statistic/probability, trial count, sample size, non-normality measures, label, and unavailable reason.

It is never calculated from direction accuracy. With fewer than 30 aligned returns, fewer than two trials, or no Sharpe-trial distribution, DSR remains `None / UNAVAILABLE` with the missing requirement stated exactly.

### Paper 9 — Deep Evidential Regression theory

No heavy neural network is trained during Streamlit rendering. The requested theory is implemented as two separate causal uncertainty scores:

- **Aleatoric:** realized volatility, ranges, empirical conformal width, and NLP event importance.
- **Epistemic:** path disagreement, completed residual support, model-weight instability, conditional model support, and transition risk.

The result includes aleatoric, epistemic, and combined 0–100 scores, primary source (`MARKET`, `MODEL`, `BOTH`, or `LOW`), explanation, and sample-size status. The output explicitly states that it is not an exact Bayesian guarantee.

### Paper 10 — DLinear-style challenger baselines

Implemented four lightweight causal challengers:

- last-close naive;
- recent-drift;
- same-session/similar-hour linear;
- DLinear-style past-only trend/remainder decomposition.

All baselines forecast H+1 through H+6. Walk-forward residuals are produced using only observations available at each origin. Skill is calculated as `1 − system MAE / baseline MAE` for every horizon and baseline when enough completed samples exist.

A brief baseline win does not replace an existing path. Negative skill lowers validation confidence until adequate evidence accumulates.

## 5. Canonical contract additions

The hidden research object now carries:

- research calculation ID;
- calculation timestamp;
- last completed H1 timestamp;
- data source identity;
- data hash;
- input hash;
- output hash;
- cache version;
- schema version;
- row count;
- stale flag/status;
- error message;
- layer status;
- per-layer execution metadata and duration;
- challenger baselines and skill;
- conformal quantiles/bands/probabilities/MFE/MAE;
- adaptive coverage states;
- Bayesian changepoint/run-length summary;
- adaptive-window metadata;
- conditional accepted-model sets;
- dynamic model weights;
- uncertainty decomposition;
- PBO/DSR states;
- bounded research Reliability;
- hidden meta-labels;
- validation status and invariant results.

The existing Priority adapter also exposes KNN neighbour-quality diagnostics and calibrated Greedy inputs inside the existing Priority structure. Existing KNN/Greedy score formulas are not renamed or replaced.

## 6. Causality and determinism

Implemented safeguards include:

- immutable latest-completed-H1 cutoff;
- sorted/deduplicated timestamped OHLC;
- no negative shifts in active Python calculations;
- no centered rolling windows;
- no future backward fill;
- no random time-series split;
- no full-sample scaler in the research layer;
- expanding past-only standardization;
- purged chronological validation;
- embargo at least the six-hour maximum horizon;
- completed-target settlement only;
- deterministic hash-based random seed;
- idempotent adaptive coverage, windows, and model-weight updates for unchanged evidence;
- output hash excludes timing-only execution metadata.

The same canonical inputs, same completed H1 cutoff, same existing central paths, and same completed outcome histories produce the same research calculation ID, seed, input hash, and output hash.

## 7. Persistence and fail-safe behavior

SQLite tables are created idempotently for:

- research calibration runs;
- pending conformal predictions;
- settled conformal outcomes;
- experiment registry;
- chronological experiment-period performance.

Pending targets are settled only when the matching completed H1 close exists. Valid history is never overwritten with partial output.

The research layer is optional and fail-safe. An exception returns the untouched protected canonical payload/bundle, records the actual error, and does not corrupt Full Metric output. Required canonical publication remains atomic and preserves the previously published generation if canonical validation fails.

## 8. Files changed

1. `_home_joined.py`
2. `core/canonical_runtime_20260617.py`
3. `core/causal_quant_support_20260618.py`
4. `core/models/quant_models.py`
5. `core/nlp_event_response.py`
6. `core/regime_sync_20260617.py`
7. `core/research_causality_20260618.py`
8. `core/settings_run_orchestrator_20260617.py`
9. `tabs/dv_news_nlp_intelligence_20260612.py`
10. `tabs/engine_split/combined_engine.py`
11. `tabs/engine_split/pro_engine_upgrade.py`
12. `tabs/final_priority_history_dv_fix_20260611.py`
13. `tabs/reliability_control_center_20260614.py`

The non-research files above received causal leakage cleanup or canonical integration changes. No file was removed.

## 9. New files

1. `core/research_calibration_20260618.py`
2. `tests/test_ten_paper_research_calibration_20260618.py`
3. `IMPLEMENTATION_REPORT_20260618_TEN_PAPER_RESEARCH.md`

## 10. Test commands and final results

### Python compilation

```bash
python -m compileall -q .
```

Result: **PASS** — every Python file compiled.

### Focused research tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_ten_paper_research_calibration_20260618.py --disable-warnings --maxfail=1
```

Result: **PASS — 33 passed**.

### Complete project tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q --disable-warnings --maxfail=10
```

Result: **PASS — 133 passed in 31.23s**.

### Import smoke test

```bash
python -c "import app; import adx_dashpoard; from core.app_shell import run_app; import core.research_calibration_20260618; print('IMPORT_SMOKE_OK')"
```

Result: **PASS — `IMPORT_SMOKE_OK`**.

### Streamlit startup smoke test

```bash
timeout 25s streamlit run app.py --server.headless true --server.port 8765 --browser.gatherUsageStats false
```

Result: **PASS** — Streamlit started, served the local/network URLs, and was then intentionally stopped by the timeout.

### Package-environment check

`python -m pip check` reported one host-container conflict: installed `moviepy 2.2.1` requires Pillow `<12`, while the host has Pillow `12.2.0`. MoviePy is not in this project’s requirements and no dependency was added by this release. Project compilation, imports, all 133 tests, and Streamlit startup passed despite that unrelated host-package conflict.

## 11. Focused test coverage

The new suite covers:

- completed-candle cutoff and future-row exclusion;
- static negative-shift/centered-window/future-backfill guards;
- no random split/full-sample scaling;
- purging and embargo;
- deterministic same-input output;
- new-H1 and NLP-only invalidation;
- residual-vector coherence and fallback hierarchy;
- quantile ordering and band monotonicity;
- conformal widening/narrowing/bounds/idempotence;
- changepoint probability/run-length ranges;
- adaptive-window growth/shrink/idempotence;
- conditional-set fallback;
- DMA sums/bounds/suppression/reactivation;
- PBO and DSR valid/unavailable states;
- baseline skill;
- uncertainty separation;
- Reliability downgrade/bounds;
- protected score/path preservation;
- short-history fallback;
- optional-layer failure isolation;
- SQLite persistence and completed-target settlement;
- experiment matrix/PBO persistence;
- Lunch/Dinner shared-generation synchronization;
- tab-adapter no-recalculation behavior;
- all probability/score invariants;
- versioned contract metadata;
- existing Priority adapter exposure;
- lightweight requirements imports.

## 12. Data-dependent limitations and intentionally omitted heavy behavior

No requested research concept is represented by a placeholder-only function. All ten have executable calculations, canonical integration, bounded behavior, and tests.

The following outputs are intentionally data-dependent:

- **PBO:** remains UNAVAILABLE until at least 4 tested configurations across at least 4 chronological periods are registered.
- **DSR:** remains UNAVAILABLE until at least 30 aligned actual strategy returns and a valid multi-trial Sharpe distribution exist.
- **Model-specific DMA:** LSTM, Transformer, XGBoost, Prophet, or other contributors are weighted only after their model-specific completed residual histories are available. The system never fabricates model losses.
- **Highly specific conformal groups:** broaden through the documented hierarchy when fewer than the minimum completed vectors exist.
- **Exhaustive condition grid:** not recomputed during tab rendering; the current active condition is evaluated during Run Calculation, with offline/periodic evidence accumulated through persistence.
- **Heavy evidential neural network:** intentionally not added because the specification prohibited unnecessary heavy live training. The useful uncertainty-separation theory is implemented with causal existing measurements instead.

## 13. Dependencies

No project dependency was added or changed. The implementation uses packages already declared by the project, primarily Python standard library, NumPy, pandas, and SQLite.

## 14. Protection confirmations

- Full Metric History formulas and tables are preserved.
- Master, Entry, Hold, TP, Exit Risk, Trend Capacity Remaining, Alpha, Delta, KNN, Greedy, regime, NLP, and existing projection meanings/scales are preserved.
- Existing score scales remain unchanged: protected scores stay on their original ranges; research uncertainty/reliability use 0–100.
- Red, yellow, and blue central paths are preserved; only empirical bands/quantiles/confidence metadata are enriched.
- No new top-level tab, page, sidebar item, menu item, or visible section was added.
- Lunch and Dinner consume one identical published canonical adapter/generation.
- All new live calculations are completed-candle-only and causal.
- Same completed inputs produce deterministic research identity and output.
- The delivered ZIP contains the complete runnable project, not an isolated patch.

## 15. Archive checksum note

The final ZIP SHA-256 is supplied with the external delivery message. Embedding the final archive’s own checksum inside itself would change the archive and therefore invalidate that checksum.
