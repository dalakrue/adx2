2026-05-31 SYSTEM RELATIONSHIP + TIMING FULL UPGRADE
====================================================

This upgrade is non-destructive. It keeps the original tab code and adds a shared
coordination layer so frontend, backend, tabs, database, connectors, API health,
and UI/UX timing work together more correctly.

WHAT WAS ADDED
--------------
1) core/system_contract.py
   - One shared runtime contract for all tabs.
   - Tracks app cycle, tab timing, data version, connection health, API health,
     dataframe quality, frontend mode, backend status, and runtime events.
   - Gives every tab the same relationship/timing diagnostics without replacing
     original logic.

2) All-tab UI shell upgrade
   - core/app_shell.py now renders the universal UI/UX header on every tab.
   - Every tab gets data-quality warning cards.
   - Every tab gets a System Relationship + Timing panel.
   - Every tab render is timed safely; slow or broken tabs are recorded.

3) Connector/API synchronization
   - core/data_connectors.py now increments a shared data_version after each
     successful connect/refresh.
   - MT5 / Twelve Data / Doo Bridge / Cache / Safe Demo states are recorded into
     api_health and connection events.
   - Cache fallback no longer returns early without updating shared session state.

4) Database relationship upgrade
   - core/database.py now has append_rows_csv, save_market_cache,
     load_market_cache, vacuum_sqlite, and database_relationship_summary.
   - tabs/database_tab.py now shows backend/database relationship health, tab
     timing, runtime events, market cache save, and SQLite optimization.

5) Sidebar integration
   - core/navigation.py now shows a compact Sync card with source, rows,
     data version, and quality score.
   - Manual disconnect is now recorded as a system event.

6) UI/UX styling
   - core/styles.py includes a new responsive Relationship + Timing card.
   - Phone mode keeps the new diagnostics compact and readable.

HOW TO RUN
----------
1) Extract the zip.
2) Open PowerShell in the extracted quant_app_upgrade folder.
3) Run:

   pip install -r requirements.txt
   streamlit run adx_dashpoard.py

or:

   streamlit run main.py

IMPORTANT
---------
- SAFE_DEMO and CACHE sources are shown as WARN in the relationship panel. This
  prevents mistaking demo/cached candles for live broker/API data.
- The original tabs are not deleted. The new system layer only wraps and tracks
  them.
- The Database tab can now save data/latest_market_cache.csv from the currently
  shared dataframe.
