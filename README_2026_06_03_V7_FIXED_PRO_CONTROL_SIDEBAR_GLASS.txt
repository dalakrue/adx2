V7 FIXED PRO CONTROL SIDEBAR GLASS PATCH

What changed:
1. App now starts with Streamlit sidebar collapsed, not opened first.
2. Added a real fixed PRO CONTROL button at top-left of the app window.
   - It stays visible when scrolling down.
   - It stays visible after changing tabs.
   - It opens and closes the sidebar from the same button.
3. Removed the old fake/cropped PRO CONTROL label from inside the sidebar.
4. Sidebar now uses transparent glass background with strong blur/backdrop effect.
5. Sidebar opens with popup/slide animation.
6. Sidebar controls, expanders, inputs, and buttons now have glass-card styling.
7. Trading logic, connector logic, reversal detector, account logic, and database files were not changed.

Run:
  streamlit run main.py

Important:
If your browser cached old CSS, press Ctrl+F5 once after starting the app.
