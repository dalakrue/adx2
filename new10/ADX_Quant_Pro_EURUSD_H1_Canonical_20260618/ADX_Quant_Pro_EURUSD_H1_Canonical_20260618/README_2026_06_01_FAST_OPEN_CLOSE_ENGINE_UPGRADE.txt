FAST OPEN/CLOSE + ENGINE PERFORMANCE UPGRADE - 2026-06-01

What changed:
1. Sidebar: only tab-choice buttons stay visible. Symbol, quick refresh, connector settings, system health, UI mode, timer, websocket, and system info are under open/close expanders.
2. Shared System Status + Global Market Pulse: one compact line first; full status and pulse inside an open/close field.
3. System Relationship + Timing: now under an open/close field on every tab.
4. Engine tab: changed from eager st.tabs to lazy radio workspace selector. Only the selected workspace renders, so Engine opens much faster.
5. Engine duplicate Doo Prime Analysis inner tab was removed. Doo Prime analysis remains in Home/Doo Prime/account panels.
6. Engine inner sections: heavy tables, similarity scan, chart, compact data, and debug output are under open/close fields. Similarity scan runs only when opened.
7. Doo Prime/account/positions tables: position, risk, scenario, exposure, history, and explanation tables are under open/close fields.
8. Train Data and Database tables: large tables are also under open/close fields.

Run:
    streamlit run adx_dashpoard.py
