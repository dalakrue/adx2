2026-06-01 FULL UI/UX + ANIMATION + RELATIONSHIP UPGRADE

What was added without removing original logic:

1) New additive helper: core/ui_relationship.py
   - Tracks active main tab + inner tab path.
   - Keeps sidebar navigation, inner choice buttons, and shared connection state synchronized.
   - Adds shared connection version/signature so every tab can see when sidebar data changes.
   - Adds a small top command bar on every tab.
   - Adds a relation footer confirming: Sidebar connector -> shared session dataframe -> tab -> inner section.

2) App shell integration
   - Initializes the UI relationship state on boot.
   - Renders transition popup + command bar before every tab.
   - Renders relationship footer after every tab.
   - Updates shared connection signature every app cycle.

3) Sidebar/navigation integration
   - Main tab clicks now update the shared UI relationship state before rerun.
   - Successful sidebar refresh/connect now updates the shared connection signature and shows a toast.
   - Existing auto-close sidebar behavior is preserved.

4) Inner-tab helper integration
   - Existing choice_buttons now also marks active inner workspace/section.
   - This improves relationship between Engine inner tabs, Pre inner sections, sidebar, and shared helper functions.

5) CSS/UI/animation upgrade
   - Added sticky glass command bar.
   - Added animated popup/toast when opening tabs/inner sections.
   - Added button ripple/click/hover effects.
   - Added metric/table soft glass styling.
   - Added phone responsive adjustment for command bar and popup.

Run:
    streamlit run adx_dashpoard.py --server.address 0.0.0.0 --server.port 8501

If port 8501 is busy:
    streamlit run adx_dashpoard.py --server.address 0.0.0.0 --server.port 8502
