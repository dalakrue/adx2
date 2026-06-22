# ADX Quant Pro — Similar-Day Intelligence Final Implementation Report

**Release date:** 2026-06-19  
**Scope:** EURUSD H1, existing Streamlit application, Lunch Field 4  
**Preferred entry file:** `app.py`  
**Streamlit Community Cloud Main file path:** `app.py`

## Result

The uploaded project was audited recursively and upgraded in place. The application still has exactly four principal Lunch open/close fields. Field 4 is now:

> **4. Similar-Day Intelligence + All Current Data**

Similar-Day Intelligence is calculated once inside the existing Settings calculation transaction, attached to the same canonical generation, atomically published, persisted to a separate compact SQLite feature store, and rendered read-only in Lunch. Existing All Current Data remains below it.

No protected Full Metric, ten-decision history, Power BI, regime, KNN, Greedy, priority, reliability, conflict, counter-trend, forecast, NLP, connector, login, timer, logout, copy, export, chart, table, tab, or inner-tab implementation was removed.

## Audited dependency map

```text
app.py
  -> adx_dashpoard.main
    -> core.app_shell / core.app.runner
      -> tabs.antd_page_router_20260615._render_settings
        -> core.settings_run_orchestrator_20260617.run_settings_calculation
          -> validate/fetch connected data once
          -> existing canonical engines and Full Metric once
          -> build_similar_day_intelligence once
          -> canonical["similar_day_intelligence"]
          -> publish_canonical_atomically once
          -> persist_similarity_generation once
      -> Lunch route
        -> ui.lunch_four_core_fields_20260619
          1. Full Metric 25-Day History + 10 Decision Histories
          2. Power BI Price Prediction Projection
          3. Regime History + three standards
          4. Similar-Day Intelligence + All Current Data
             -> ui.similar_day_renderer_20260619 (display-only)
             -> existing _render_current_data
```

## Audit findings

- **True entry:** `app.py`; it imports `adx_dashpoard.main` and is safe when launched from a different working directory.
- **Lunch renderer:** `ui/lunch_four_core_fields_20260619.py`.
- **Canonical authority:** `core/canonical_runtime_20260617.py` and the existing Settings orchestrator.
- **Run flow:** the only Similar-Day builder call is in `core/settings_run_orchestrator_20260617.py`; Lunch renderers contain zero calculation calls.
- **Storage:** existing SQLite/CSV stores were preserved. A new isolated `data/adx_similarity_store.sqlite3` was added. The project already lists DuckDB/Parquet-capable dependencies; the new engine does not require a full analytical scan or new heavy library.
- **Existing 25-day logic:** preserved in the Full Metric and regime renderers. Similar-Day has its own equal-prefix 25-attempt table and does not replace those histories.
- **Existing similarity code:** NLP cosine similarity and embedded legacy/demo backtest Similar-Day code were found. They are not the active canonical calculation authority. They were preserved for compatibility rather than deleted.
- **Caching:** existing bounded/cache architecture was retained. The new engine uses a deterministic, TTL-limited, two-generation state cache.
- **Import risks:** no new third-party dependency was added. Linux case-sensitive compile/import contracts pass. No production Python file added a local Windows absolute path.
- **Mobile/browser risks:** the new 16-card summary is one responsive HTML grid rather than 16 separate `st.metric` components; tables are limited to five and 25 rows; no chart, polling loop, auto-refresh, or JavaScript timer was added.
- **Large-frame handling:** the new calculation projects required OHLCV columns, uses `float32` for numerical OHLCV and feature arrays, and stores compact JSON vectors instead of full market frames in session state or SQLite.

## Similar-Day engine

### Equal elapsed-hour alignment

Only completed UTC H1 candles through the canonical latest-completed timestamp are accepted. If the current day contains hours 00:00–12:00 UTC, each candidate is matched only against those same 13 hours. Historical H+1/H+3/H+6 candles are read only after ranking is finalized.

Weekends are not candidates. Empty/holiday days remain in the 25-row attempted table with an exclusion reason. A small historical gap may be interpolated for shape comparison and is visibly warned; excessive gaps, duplicate timestamps, or an unsorted per-day sequence reject the candidate.

### Two-stage pipeline

**Stage 1 — low-cost screening**

- normalized return path and cumulative return
- intraday range position
- ATR and realized volatility
- ADX, +DI, -DI and pressure
- volume/tick-volume quality
- canonical/history aliases when available: Master, Entry, Hold, Exit Risk, TP Quality, trend capacity, market quality, forecast agreement, reliability, conflict, counter-trend and H1/H4/D1 regimes
- compact catch22-style statistics: lag-1 autocorrelation, entropy, trend slope, mean absolute change, quantiles, zero-crossing rate, outlier ratio and candle-body efficiency
- robust median/IQR scaling fitted only on historical candidate prefixes

The strongest eight candidates proceed to Stage 2.

**Stage 2 — robust shape reranking**

- z-normalized Euclidean path distance
- Matrix-Profile-style subsequence join distance
- MPdist-inspired robust distance
- constrained Sakoe-Chiba DTW
- LB_Keogh lower-bound check and DTW early abandonment
- regime, volatility/ATR, ADX/DI/pressure, session and data-quality compatibility

### Centralized weighting

All weights are versioned in `core/similar_day_config_20260619.py`:

- 30% price-path shape
- 20% regime compatibility
- 15% volatility and ATR
- 15% ADX, DI and pressure
- 10% elapsed-hour/session compatibility
- 10% data/event quality

The output is always called **Similarity Index**, never probability.

### Reliability and decision protection

The result is supporting historical evidence only. High/Medium/Low reliability gates use top-five agreement, effective sample size, data quality, regime compatibility, match strength, anomaly status and missing-current-hour status. A visible warning appears when the weighted historical direction conflicts with the canonical less-risky decision. The Similar-Day engine does not overwrite or reverse the canonical decision.

### Baselines and validation

The payload includes previous-day continuation, same-weekday median, current-regime median, rolling mean, exponentially weighted forecast and existing Power BI H+3 baseline where available. Validation uses chronological rolling-origin logic; no random shuffle is used and no superiority claim is made without sufficient settled samples.

## Research concepts applied

1. **Matrix Profile I:** subsequence-shape join distance for motif-style comparison.
2. **Trillions of Time Series under DTW:** narrow warping band, candidate pruning, lower bounds and early abandonment.
3. **MPdist:** robust quantile aggregation of local shape distances.
4. **Time Series Snippets:** compact normalized prefix/path representation rather than storing every raw window.
5. **k-Shape:** z-normalized shape logic and an interpretable lightweight pattern-family classifier; no clustering retrain occurs during rendering.
6. **catch22:** inexpensive canonical characteristics implemented directly with NumPy/pandas.
7. **tsflex:** modular feature extraction and versioned feature schemas without adding the dependency.
8. **Forecasting concerns and ways forward:** baseline comparison, rolling-origin validation, honest uncertainty and no unverified accuracy claim.
9. **DuckDB:** analytical pushdown principles were followed; no unnecessary full-history pandas display scan was introduced. The current compact store uses SQLite because it is transactional and already stable for state.
10. **Hidden Technical Debt:** one authoritative engine, one config location, explicit versions, atomic generation publication, stale-write rejection, import-safe failure handling and bounded caches.

## Preservation checks

- Exactly four principal Lunch expanders remain.
- Existing Full Metric 25-day and ten-decision histories remain in Field 1.
- Existing cached Power BI projection remains in Field 2.
- Existing overall/lower/medium/higher regime histories remain in Field 3.
- Existing All Current Data remains after Similar-Day content in Field 4.
- Existing mobile API-key paste, guest/login, settings, timer and logout code remains.
- Existing copy/export infrastructure remains.

## Files changed

See `MODIFIED_FILES_20260619_SIMILAR_DAY_FINAL.txt` for the exact list.

## Tests

- All 36 new requested acceptance tests pass.
- Combined Similar-Day plus four-Lunch-field suite: **40 passed**.
- Deployment-critical existing regression suite: **95 passed**.
- Clean isolated project result: **237 passed; 2 environment-blocked** out of 239 collected.
- The two blocked tests import the real `streamlit` package, which is not installed in this execution container. They are not code assertion failures. `requirements.txt` includes Streamlit and the existing Cloud preflight suite passes.
- `python -m compileall` succeeds for entry files, core, UI, tabs, services and tests.

A live `streamlit run app.py` startup was not claimed because Streamlit is unavailable in this container.

## Performance evidence

See `PERFORMANCE_REPORT_20260619_SIMILAR_DAY_FINAL.md` and the accompanying JSON. The measured synthetic Similar-Day calculation produced all 25 rows and five top matches in 1.963 seconds in a separate process; repeated cached reads averaged 0.018 seconds. Full live canonical before/after timing and iPhone temperature were not measurable here and are explicitly not estimated.

## Deployment

See `STREAMLIT_CLOUD_DEPLOYMENT_20260619_SIMILAR_DAY_FINAL.md`.

## Rollback

The uploaded source ZIP was not overwritten. The new SQLite store is isolated. See `ROLLBACK_NOTE_20260619_SIMILAR_DAY_FINAL.md`.
