# ADX Quant Pro / new7 — Final Finnhub, NLP and Lunch Restoration Report

## Verified Streamlit entry

```powershell
streamlit run app.py
```

`app.py` is the preferred wrapper. It calls `adx_dashpoard.main()`, which loads the active application shell through `core.app_shell.run_app()`.

## Files added in this correction

- `tools/validate_finnhub_nlp_restore_20260617.py`

## Files modified in this correction

- `core/finnhub_connector.py`
- `core/nlp_models.py`
- `core/nlp_pipeline.py`
- `tabs/research.py`
- `tools/validate_final_sync_20260617.py`
- `ui/lunch_restored.py`
- `ui/sidebar_fallback_panel.py`
- `UPGRADE_REPORT_2026_06_17_FINNHUB_NLP_RESTORE.md`

The ZIP already contained the shared-result, NLP/data-mining, sidebar, Lunch restoration and routing modules. This correction inspected and strengthened their active wiring rather than replacing trading calculations.

## Sidebar and Finnhub

- Kept the compact sidebar collapsed by default and fully closable/reopenable.
- Desktop width remains approximately 180–220 px; phone width is an overlay up to 78vw with zero reserved width when closed.
- Kept one canonical masked Finnhub key input in the compact sidebar.
- Removed the older NLP/LLM API connector UI from the general connector drawer.
- Connect, Test and Disconnect remain session-only, with timeout, bounded retry/backoff, rate-limit handling, JSON validation and key redaction.
- A failed replacement connection now clears any stale previously stored session key and cached Finnhub news.

## Lunch restoration

- Lunch Quick Decision remains at the top and is guarded to the Lunch route only.
- The actual original Lunch renderer remains available at the bottom under **Original Lunch Analysis**.
- The original Power BI Price Prediction Projection, Full Metric Detail and Full Metric History open successfully from lazy fields.
- Restored Copy Short, Copy All and text export controls from the original payload builders without rerunning trading calculations.

## Research selector

- Removed the second competing Research tab selector.
- Kept one canonical three-choice selector using only `research_inner_tab`.
- Data Analysis, Data Mining and NLP content now all read that same selected value.
- Library Status and Copy/Export were preserved as expanders rather than competing selectors.
- Research selection persists through reruns, Run Research and Finnhub button actions.

## NLP and data-mining strengthening

- Preserved the existing shared normalization, entity relevance, duplicate detection, LDA, TF-IDF/LinearSVC, optional FinBERT, summaries, event-response mining, reliability and error-analysis modules.
- Added support for `publishedDate` / `published_date` timestamp normalization.
- Corrected extractive-summary market-effect mapping so positive USD evidence is bearish for EURUSD and negative USD evidence can be bullish.
- Strengthened chronological SVM calibration: the final test block stays untouched, and calibration uses a later-in-time subset of past training data instead of random folds.
- Duplicate news remains WAIT evidence and does not multiply impact.

## Validation performed

- Compiled every Python file successfully.
- Verified all modified imports.
- Started `streamlit run app.py`; `/_stcore/health` returned `ok`.
- Streamlit AppTest: Settings initial page, no application exceptions or errors.
- Verified exactly one Finnhub secret input and one Research selector.
- Verified invalid/empty Finnhub connection fails safely, clears stale secrets and does not reset Research selection.
- Verified Lunch Quick Decision is Lunch-only.
- Opened Original Lunch, original Power BI, Full Metric Detail and Full Metric History individually with zero UI exceptions/errors.
- Verified positive USD news maps to EURUSD SELL pressure and positive EUR news maps to BUY pressure.
- Verified duplicate news suppression, conflict-to-WAIT behavior, small-sample reliability penalty and chronological SVM split/calibration.
- Ran both focused validation scripts successfully.
- Ran a dry-run resolution of `requirements.txt` successfully.

## Confirmations

- Existing trading, regime, priority, entry, BUY/SELL/WAIT, Power BI, reliability and conflict calculations were preserved.
- Original Lunch was restored at the bottom.
- Power BI was restored.
- Full Metric Detail and Full Metric History were restored.
- Only one canonical Research selector remains.
- The Finnhub API key is not hardcoded and is not persisted to project files.
- The project compiled and started successfully.

## Remaining limitations

- A real authenticated Finnhub success response could not be tested because no live API key was supplied. Invalid, empty, disconnected, redaction and fallback paths were tested.
- Optional FinBERT and abstractive models were not downloaded during packaging. They remain lazy-loaded after an explicit user action and safely fall back when unavailable.
- Original Power BI/history displays require the project’s existing completed calculation/cache data; no placeholder market prediction data was created.
