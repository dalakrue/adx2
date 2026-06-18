2026-06-02 PRO GLOBAL UI/UX + SIDEBAR UPGRADE

What changed:
1. Added a final clean ocean-glass CSS override in core/global_upgrade.py.
   - Better background effect.
   - Smaller cleaner transparent glass cards.
   - Softer popup animation.
   - Better iPhone/mobile grid behavior.
   - Cleaner sidebar shape and shadows.

2. Added global helper functions in core/global_upgrade.py:
   - render_page_shell()
   - render_tab_upgrade_console()
   - render_sidebar_pro_header()
   - render_shared_data_contract()
   - render_background_health_panel()

3. Upgraded sidebar in core/navigation.py:
   - New visible one-click sidebar command center.
   - MT5/Doo 600 quick connect.
   - Doo Bridge quick connect.
   - Twelve Data quick connect.
   - Refresh current connector.
   - Sync Data Modeling / Doo deep panels from the shared dataframe.
   - One safe global disconnect path.

4. Upgraded all main tabs with the new global page shell and helper panels:
   - Home
   - Engine
   - Train Data
   - Pre Original
   - Database
   - Profile

5. Original algorithms and tab functions were preserved.
   The upgrade uses wrappers and helper panels, so future fixes are easier and safer.

Run:
   cd new7
   pip install -r requirements.txt
   streamlit run main.py

Important:
- MT5/Doo Prime local connector needs local Windows + Doo Prime MT5 terminal open and logged in.
- Streamlit Cloud cannot run MetaTrader5 directly. Use Twelve Data or Doo Bridge on cloud.
- Safe Demo fallback is still OFF unless you explicitly enable it.
