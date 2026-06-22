# ADX Quant Pro / new7 — Final Correction Report (2026-06-19)

## Base and entry point

- Only project base: `55b8051e-2696-4945-b8c2-a9aab5035a24.zip`
- Base ZIP SHA-256: `7ca9dd2bcac0a29589b7fc279e5848f8c8caec73eeb5e8f77a00de7348ea602e`
- Detected entry point: `app.py`
- Run command: `python -m streamlit run app.py`
- Supported runtime remains `python-3.12` in `runtime.txt`.

## Corrected errors

### Windows `WinError 10054`

Added a project-local startup compatibility policy in `sitecustomize.py` and
`core/windows_asyncio_compat_20260619.py`. On Windows only, Python selects
`WindowsSelectorEventLoopPolicy` before Streamlit/Tornado creates the server
loop. This prevents the benign Proactor connection-lost callback failure without
installing a global exception handler and without hiding calculation, network,
database, or renderer exceptions.

`RUN_APP_WINDOWS.bat` now starts the real entry file (`app.py`) from the project
folder.

### `Data quality FAIL_MODEL` caused only by future rows

`core/decision_product_engine_20260617.py` now excludes future/forming rows from
completed-H1 calculations and records a visible `PASS_WITH_WARNING` message.
Future rows no longer block all affected models after they have been safely
removed. Missing OHLC, invalid OHLC relationships, duplicate timestamps and
other real blocking defects remain blocking.

## Power BI restoration

- Added `ui/powerbi_cached_renderer_20260619.py`.
- The renderer reads only the completed cache:
  - calibrated main path;
  - red, yellow and blue paths;
  - upper/lower bands;
  - blue future candles;
  - historical yellow paths where the existing cache provides them;
  - prediction-vs-actual history;
  - confidence/reliability, direction accuracy, error, Alpha, Delta and six-hour price.
- It performs no model run, calibration run, OHLC rebuild or shared-system calculation.
- Local chart controls are isolated with `st.fragment`.
- Projection integrity failures display the stored real error and validation details rather than silently hiding the chart or substituting stale data.
- `tabs/antd_page_router_20260615.py` now performs one synchronized navigation transaction after a successful calculation and opens:
  - page: `Lunch`;
  - inner page: `PowerBI Projection`.
- The active Power BI route no longer imports the large legacy Home renderer chain.
- `ui/lunch_restored.py` also uses the same cached renderer, so opening optional restored Lunch tools cannot trigger a second Power BI calculation.

## Full Metric History corrections

- The visible canonical table now renders `history_25day`, not the unrestricted `history_view`.
- Stored complete history is not truncated.
- Complete CSV/JSON exports remain available and are generated lazily only after the user enables the export control.
- Ten reverse-factor `st.tabs` were replaced by one selector; only the selected cached factor DataFrame is serialized to the browser.
- All ten factor datasets and the selected-factor CSV export remain available.
- Optional restored Lunch fallback uses the same one-factor selector instead of ten rendered tabs.
- Protected Full Metric source file `tabs/eurusd_h1_matrix.py` remains byte-for-byte unchanged:
  `fe0797ab30f469f3ea748bc66a690b18a68aaf91306ac33c797bdcdcf6e60682`.

## Regime corrections

`ui/full_metric_regime_inner_renderer_20260618.py` now displays, in order:

1. Current Major Regime cards, reliability, Alpha, Delta, transition risk and expected remaining hours.
2. Medium Standard Regime table (existing approximately five-day payload).
3. Higher Standard Regime table (existing approximately 25-day payload).

The Lower Standard, current-hour, every-hour and duplicate raw hourly regime
history tables are no longer rendered in this section. Their underlying data is
not deleted. Medium/Higher tables are read from the published generation only;
opening the page cannot rebuild them. Visible rows/columns are bounded for
mobile, while complete table CSV export remains available on demand.

## CPU, RAM and mobile changes

- Cached-only Power BI display; no legacy recalibration on page open.
- One visible factor table instead of ten.
- Exactly two detailed regime standard tables instead of duplicated hourly tables.
- Twenty-five-day Full Metric browser slice while retaining complete disk/state data.
- Lazy export byte creation.
- Existing bounded canonical cache, disk-backed history store, compact Lunch/Dinner/AI summaries and low-heat CSS remain active.
- Mobile chart height and default historical overlays are reduced without changing predicted values or candle count.
- No new top-level page, tab, menu item, model, dataset, API or paid service was added.

## Tests executed

- Python compile check: PASS.
- Pytest: 175 collected, 175 passed, executed in three batches.
- Streamlit server startup: PASS.
  - health endpoint: HTTP 200 `ok`;
  - root page: HTTP 200;
  - startup-to-health in this container: 3.037 s.
- AppTest authentication screen and Guest Settings: 0 exceptions, 0 errors, 0 warnings.
- Cached Power BI synthetic-render smoke test: 0 exceptions/errors/warnings, one Plotly chart, 0.333 s.
- Full Metric/Regime synthetic-render smoke test: 0 exceptions/errors/warnings; four DataFrames total:
  - one 25-day Full Metric table;
  - one selected factor table;
  - one Medium Standard table;
  - one Higher Standard table.
- Final ZIP is extracted into a clean folder and startup-tested before delivery.

## Measured performance

The repeatable local benchmark uses the same synthetic 12,000-row H1 table for
before/after display preparation. It is server-side measurement, not iPhone
telemetry and not a complete live API calculation benchmark.

- Lunch display-preparation time: 99.03% lower.
- Lunch display-preparation tracemalloc peak: 99.85% lower.
- Dinner display-preparation time: 97.76% lower.
- Dinner display-preparation tracemalloc peak: 99.77% lower.
- Large DataFrames retained in the measured session: 5 to 0.
- Estimated DataFrame bytes retained in session: 12,480,660 to 50,580 (99.59% lower).
- Full retained history export still returned all 12,000 rows.

Process RSS did not fall in the short benchmark (394,940,416 to 396,259,328
bytes), because Python/SQLite retained allocated pages during that process. No
claim is made that end-to-end process RAM or iPhone heat fell by the same
percentages. Live Run Calculation time and live-phone CPU/temperature could not
be measured safely because the supplied ZIP contains no user API credentials or
current OHLC dataset.

## Limitations kept honest

- A clean Guest AppTest cannot complete the real Run Calculation without the
  user's connected/current OHLC source; it correctly reports missing OHLC rather
  than fabricating data.
- The complete protected numerical pipeline was covered by the existing causal,
  canonical, Power BI calibration, multiscale, Full Metric and regression tests.
- No protected formula or threshold was altered to obtain performance gains.
