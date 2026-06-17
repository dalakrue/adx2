LONG-TERM SIDEBAR HARD LOCK FIX — 2026-06-14

Problem fixed:
- Streamlit native sidebar sometimes opened on first load.
- Try Close Sidebar button sometimes did nothing.
- Older patches fought each other: force-hide CSS, un-force CSS, and JavaScript DOM click logic.

New long-term design:
1. Native Streamlit sidebar is OFF / locked closed by default.
2. The real app menu is the main-page "☰ Open / Close — Main Page Menu" drawer.
3. The main-page menu uses st.session_state, not fragile JavaScript.
4. API connection, timer, UI mode, account status, and navigation remain available inside the main-page controls.
5. Native sidebar can be unlocked only as an emergency backup from Sidebar Stability Guard, but it is not required for normal use.

Files changed:
- ui/sidebar_hard_lock.py
- core/app/runner.py
- core/navigation_parts/main.py
- ui/main_menu_drawer.py
- ui/native_sidebar_js.py
- core/ui/styles.py

How to run:
streamlit run app.py

Expected result:
- On first open / guest login, native sidebar does not appear.
- Main Page Menu starts closed.
- Press ☰ Menu to open controls.
- Press ✖ Close Menu or any navigation page button to close it.
- Sidebar stuck-open/stuck-closed problem is avoided because the app no longer depends on Streamlit native sidebar DOM state.
