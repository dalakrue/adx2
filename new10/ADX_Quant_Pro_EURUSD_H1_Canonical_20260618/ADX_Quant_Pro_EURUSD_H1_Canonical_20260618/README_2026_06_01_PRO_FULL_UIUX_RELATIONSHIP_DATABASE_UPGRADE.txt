PRO FULL UI/UX + RELATIONSHIP + DATABASE UPGRADE

What was added:
1. Global animated glass live HUD above every tab.
2. Soft popup/toast effect for tab open, connector success/failure, disconnect, and UI mode change.
3. Connector guard card on data-dependent tabs when no shared dataframe exists.
4. File/tab/connection relationship hub in sidebar.
5. Additional CSS for ocean-glass background, compact phone layout, sticky HUD, animated popups.
6. Original wrappers and tab imports preserved. Existing app logic is not removed.

Run:
streamlit run main.py

Important:
Use sidebar connector once. All tabs share st.session_state.last_df and the database helpers. SAFE_DEMO remains explicit only.
