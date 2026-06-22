# Settings Full Restore — 2026-06-19

## Restored in Settings
- Twelve Data and MT5 market connector controls.
- Symbol, timeframe, candle-count, source, Connect/Refresh, Disconnect, connection status and loaded-row status.
- Trade Timer / Sound Alert with Start, Reset and live countdown.
- Account status and Logout control.
- Existing Finnhub connector and optional NLP/AI API settings.

## Mobile API paste fix
- Twelve Data uses a large mobile-safe `st.text_area` paste box with Save and Clear controls.
- Finnhub automatically uses a large paste-friendly field in Settings while preserving the masked desktop input elsewhere.
- Mobile CSS restores long-press selection, touch callout and 16 px input sizing for iPhone/Safari.
- Separate widget-key namespaces prevent the Settings controls from colliding with the app drawer controls.
- A blank hidden drawer field can no longer overwrite a Twelve Data key saved from Settings.

## Requirements
- Existing Streamlit Cloud requirements remain unchanged and resolve successfully.
- Added `requirements-windows-mt5.txt` for local Windows MT5 installation without breaking Linux/Streamlit Cloud deployment.
- Python runtime remains 3.12.

## Logic protection
- No trading, prediction, scoring, regime, PowerBI, database or calculation logic was changed.
- The restored UI calls the project's existing connector, timer and authentication state.

## Validation
- Python compile-all: passed.
- Focused Settings/Finnhub/UI tests: 17 passed.
- Added Settings restoration regression tests: passed.
- Direct requirement availability dry-run: passed.
