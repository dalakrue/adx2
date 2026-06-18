CODE QUALITY + EFFICIENCY UPGRADE - 2026-06-01

What was upgraded without removing original code:

1) Added core/code_quality.py
   - Shared OHLC dataframe normalizer.
   - Data quality scoring for all tabs.
   - Session list trimming so activity/system/training history does not grow forever.
   - Lightweight garbage collection throttle.
   - Import self-check panel for important modules.

2) Safer tab loading
   - core/app/routes.py now isolates tab import errors.
   - If one tab has a broken import, the whole app does not crash.
   - The failed tab shows the import error inside that tab only.

3) Better shared data efficiency
   - Successful connector data is normalized through the new quality helper.
   - Time rows are sorted/deduplicated.
   - OHLC/volume values are converted to compact numeric types.
   - This reduces memory pressure on Streamlit reruns and makes all tabs read cleaner data.

4) Lighter app reruns
   - App runner now performs safe light maintenance only every ~20 seconds.
   - This keeps navigation faster and avoids heavy cleanup on every click.

5) More reliable database location
   - core/storage/database.py now stores data beside the project root /data folder.
   - This avoids accidental data files being created in the wrong folder when Streamlit is launched from another directory.

6) Added Code/Data Quality panel
   - Open: page status + system relationship expander.
   - It shows data status, quality score, row count, issues, and an import self-check button.

How to run:
   streamlit run adx_dashpoard.py
or
   streamlit run main.py

Important:
   MetaTrader5 still requires local Windows + logged-in MT5 terminal.
   Safe Demo fallback remains OFF unless you explicitly enable it.
