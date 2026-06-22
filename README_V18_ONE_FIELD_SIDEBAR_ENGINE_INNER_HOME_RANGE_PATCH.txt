V18 ONE-FIELD SIDEBAR + ENGINE INNER TAB + HOME RANGE PATCH

What changed:
1) Sidebar
- Tab choice buttons stay visible.
- Everything else is inside one large field: "Open / Close ALL Sidebar Controls".
- Sidebar open/close and tab buttons are bigger for phone use.
- Refresh buttons are guarded with safe try/except so a refresh error shows inside Streamlit instead of breaking the app.

2) Engine
- Train Data is no longer a top-level sidebar tab.
- Database is no longer a top-level sidebar tab.
- Both are now inner buttons inside Engine:
  - Engine
  - Train Data
  - Database

3) Home
- 10-Reversal Decision stays at the top before all other Home content.
- Beside the 10-Reversal title, Home now shows:
  - Last Hour <= 3/10 metric
  - 25D Total <= 3/10 metric
- The low reversal table is now one open/close field, not multiple nested fields.
- Added one Home field for:
  - Today regime
  - Monthly / last 30D regime
  - Supply zone
  - Resistance zone
  - Order zone
  - Impulse zone
  - TP Buy range
  - TP Sell range

Files changed:
- core/config/defaults.py
- core/navigation_parts/main.py
- tabs/home.py
- tabs/engine.py

Run:
streamlit run main.py
