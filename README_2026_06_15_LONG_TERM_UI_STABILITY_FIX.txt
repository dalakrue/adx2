# 2026-06-15 Long-Term UI Stability Fix

Scope: UI/UX and control layer only.

Protected rule:
- No trading logic, calculations, formulas, ML logic, prediction logic, charts, tables, exports, copy text content, history, KNN/Greedy, PowerBI, regime logic, or existing AI answer logic was intentionally changed.

Main fixes:
1. Home Top Control Panel is now the real stable control center.
   - Main navigation is duplicated at the top of the app.
   - It uses st.session_state, not JavaScript DOM sidebar hacks.
   - Native Streamlit sidebar remains backup only and opens collapsed first.

2. Sidebar future-breaking protection.
   - Main app works even if native sidebar never opens.
   - Sidebar backup is controlled with session_state policy.
   - No fragile sidebar DOM open/close JavaScript is used.

3. Central copy engine.
   - Added ui/copy_tools.py.
   - core.pro_terminal_uiux.render_mobile_copy_button now routes to the central copy engine.
   - Copy Current Home, Copy Active Tab, Copy Short, Copy Full, and AI copy buttons share the same clipboard + fallback-download behavior.
   - Fake preserved-copy messages are removed from the main menu fallback path.

4. AI Assistant stable chat UI.
   - Final AI renderer now uses st.chat_input.
   - Press Enter to answer directly.
   - Selecting a choice-box question answers immediately.
   - Analysis button is optional advanced rerun only.
   - Local NLP diagnostics are combined into one clean expander.
   - Added AI inner tabs: Chat, Local NLP, Data Mining, Deep Analysis, History.
   - Uses existing local NLP/data-mining/similarity/answer functions only.
   - No external API and no heavy new model.

5. Modern UI library alignment.
   - Added safe optional adapter: ui/stable_ui_libs_20260615.py.
   - Uses streamlit-antd-components when available for segmented/tab navigation.
   - Uses streamlit-shadcn-ui, streamlit-modal, and streamlit-aggrid defensively with Streamlit fallback.
   - Missing optional UI packages will not crash the app.

6. Lunch update status.
   - Top update status is stored in one session_state card only:
     lunch_update_status_card_20260615
   - It does not create repeated status panels.

7. Performance.
   - Heavy calculation still runs only after Run Calculation.
   - Low-RAM button clears large display caches only.
   - UI components are defensive and low CPU/mobile friendly.

Files changed/added:
- requirements.txt
- core/pro_terminal_uiux.py
- ui/copy_tools.py
- ui/stable_ui_libs_20260615.py
- ui/home_master_control_bar_20260615.py
- ui/main_menu_drawer.py
- ui/top_status_bar.py
- tabs/ai_assistant_lite.py

Validation:
- python -m compileall -q . passed.
- ZIP integrity test passed after packaging.
