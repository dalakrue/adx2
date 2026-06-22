# One-Click Connector, Fresh-Time, Copy, and AI Assistant Fix

Date: 2026-06-22

## Delivered behavior

### 1. API connectors now use one click
- Twelve Data: **Save Key + Auto-Connect (One Click)** stores the session key and starts the connection in the same callback.
- Finnhub: the old two-step test/connect flow is replaced by **Save + Validate + Connect (One Click)**.
- NLP/AI key: **Save + Enable AI (One Click)** stores and enables the optional endpoint in one action.
- Settings connector actions use the lightweight/quick connection path. The expensive deep synchronization runs only when a connector signature changes.

### 2. One calculation owner
- The only manual all-in-one generation control is now:
  **Settings → Run Calculation + Open Lunch (One Click)**.
- Menu-level **Run Calculation** and **Reduce RAM** controls were removed.
- Automatic calculation on startup/new H1 was disabled. Startup may connect configured APIs, but it cannot publish a generation.
- The Settings transaction refreshes EURUSD/H1 once, runs the synchronized calculation once, publishes once, opens Lunch, and opens Field 5 AI Assistant.

### 3. Visible proof that the Settings run worked
Settings now shows `st.metric` status cards for:
- All-in-One Run
- Published Generation
- AI Assistant readiness
- Auto-Open Lunch readiness

When a new generation is rejected by validation but a previous valid canonical generation/fact pack exists, the status reports **PREVIOUS VALID USED** and Lunch/AI still opens safely.

### 4. Current MetaTrader/feed time and stale-data detection
A low-cost freshness service now displays:
- Current UTC
- Latest MT5 tick time in UTC, when the MT5 terminal is reachable
- Broker-chart clock using a configurable UTC offset
- Latest loaded candle timestamp
- Feed status: CURRENT / WATCH / LATE / NO DATA
- Lag in minutes/bars

The broker offset is display-only and does not modify candle timestamps or calculations. It defaults to UTC+4 for the reported terminal display difference and remains editable in Settings.

Before the Settings run, the connector is refreshed for the protected EURUSD/H1 identity. During preflight, a newly refreshed `last_df` now outranks materially stale display/history caches. A source more than 1.5 intervals behind the freshest valid source receives a hard stale penalty.

### 5. Two menu copy buttons restored
The menu contains exactly:
- Copy Short
- Copy Full

Each button now has one click handler only. Clipboard execution tries the iframe clipboard, then parent clipboard, then `execCommand`. If the browser blocks clipboard access, the text becomes visible and preselected with a clear Ctrl+C / long-press Copy fallback instead of appearing dead.

### 6. AI Assistant no longer becomes a dead field
Field 5 recovery order is:
1. Current compact canonical fact pack
2. Current valid canonical generation
3. Compatible legacy canonical aliases
4. Latest persisted compact summary/fact pack from SQLite
5. Safe offline diagnostic mode

The offline diagnostic mode reports source, latest candle, freshness, and the last run issue. It never invents BUY/SELL decisions or trading values. A connector disconnect or a rejected new generation therefore does not erase the last valid grounded assistant context.

## Main files changed
- `core/market_time_freshness_20260622.py` (new)
- `tabs/antd_page_router_20260615.py`
- `core/secure_api_startup_20260619.py`
- `core/app/refresh.py`
- `core/settings_run_orchestrator_20260617.py`
- `core/navigation_parts/connection.py`
- `core/finnhub_connector.py`
- `ui/sidebar_fallback_panel.py`
- `ui/main_menu_drawer.py`
- `ui/liquid_menu_popup_20260615.py`
- `ui/copy_tools.py`
- `core/performance_store_20260619.py`
- `tabs/ai_assistant_compact_20260619.py`
- `ui/lunch_four_core_fields_20260619.py`
- `tests/test_one_click_freshness_ai_copy_20260622.py` (new)
- Three legacy static tests updated to the new Settings-only requirement.

## Validation
- Python compile check: **PASS** (`python -m compileall -q .`)
- Broad test run: **307 passed in 28.55s**
- The broad run excluded two extremely slow research suites and one DuckDB-dependent suite unavailable in this execution environment.
- Static scans confirm only the Settings router invokes `run_settings_calculation(ns)` outside tests.
- Static scans confirm the menu has no executable Run Calculation or Reduce RAM action.

## Environment limitation
The live Streamlit server was not launched in this execution environment because the Streamlit runtime is not installed here. The package still declares Streamlit in `requirements.txt` and `requirements-core.txt`; compile and automated tests passed as stated above.
