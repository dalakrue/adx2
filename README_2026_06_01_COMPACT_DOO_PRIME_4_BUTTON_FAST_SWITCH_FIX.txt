COMPACT DOO PRIME 4-BUTTON FAST SWITCH FIX

Fixes applied:
1. Home inner section switching remains button-based and only selected section renders.
2. Doo Prime panel now has one clean row only: Account, Risk, History, Refresh.
3. Removed duplicate top refresh/read controls from Doo Prime.
4. Suppressed duplicate Read/Refresh/Clear buttons inside Account when opened from the compact Doo Prime panel.
5. Refresh button reads MT5 account snapshot and refreshes shared market data in one place.
6. History is still available but placed under one History section with Risk Snapshots / Doo Prime Account History choice.
7. Original analytics logic is not removed; this patch changes routing/UI controls only.

Run:
streamlit run adx_dashpoard.py --server.address 0.0.0.0 --server.port 8501
