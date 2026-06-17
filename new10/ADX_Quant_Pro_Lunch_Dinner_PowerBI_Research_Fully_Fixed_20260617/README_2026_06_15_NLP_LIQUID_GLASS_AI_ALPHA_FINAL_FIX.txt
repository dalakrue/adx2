M1 ADX Quant Pro — 2026-06-15 NLP + Liquid Glass + AI + Alpha/Delta Final Fix

Base ZIP: user uploaded e28d48b4-4d6f-43c0-9053-2aeb8b24a532.zip

What was upgraded without removing existing logic:

1) NLP pipeline added/kept in both Research NLP and AI Assistant Local NLP
- Text normalization
- Tokenization
- Stopword removal
- Stemming
- Lemmatization
- POS tagging
- Dependency parsing
- Constituency parsing
- NER / entity extraction
- Word-sense disambiguation
- Coreference resolution
- Mention extraction
- Relation extraction
- Topic detection
- Text summarization
- Text generation seed

Main file:
- core/nlp_lightweight_20260615.py

2) AI Assistant improvements
- No Analyze button is required.
- Choice-box selection answers immediately.
- Chat input answers by pressing Enter.
- Result display stays above choice box/input field.
- Prepared local pattern library now has 1200+ patterns.
- Every question pattern now has an answer_rule, answer_mode, and pattern_id.
- BUY/SELL threshold is lighter; WAIT needs the stronger triple-standard filter.
- Local NLP diagnostics are inside one open/close field to prevent duplicate clutter.

Main file:
- tabs/ai_assistant_lite.py

3) Liquid Glass UI + 3-dot app drawer
- System theme updated to Liquid Glass card/button/sidebar style.
- Top control is compact and app-like.
- 3-dot menu button opens the Liquid Glass App Drawer.
- Native Streamlit sidebar is backup only; the app does not depend on fragile sidebar DOM close/open hacks.
- Connector, Timer, Copy, and UI/Sidebar controls are independent drawer sections.

Main files:
- ui/liquid_glass_theme_20260615.py
- ui/home_master_control_bar_20260615.py
- ui/main_menu_drawer.py
- ui/sidebar_hard_lock.py
- core/navigation_parts/main.py

4) Run All + copy placement
- Master Run All is placed before Copy Short and Copy Full.
- Run All sets existing run-gated sections to calculate in low-RAM cached mode.
- No new prediction engine was added.
- Copy buttons use central fallback so missing copy-button library will not crash the app.

Main file:
- ui/home_master_control_bar_20260615.py

5) PowerBI / Regime alpha-delta data point
- Adds difference, ratio, divergence mean, Alpha Now, Alpha Prev, Delta Point, and Data Point Score.
- Uses existing blue/red path data only.
- Display-only; original PowerBI/regime calculations are untouched.

Main file:
- core/alpha_delta_points_20260615.py

6) Future upgrade/downgrade architecture
- Registry-based page routing.
- Lazy tab imports isolate broken future tabs.
- Compatibility wrappers preserve old import paths.
- UI health check and duplicate key scan are available.
- Native sidebar can be hidden/unlocked as backup without breaking main navigation.

Main files:
- core/app/registry.py
- core/app/routes.py
- ui/navigation_registry.py
- core/diagnostics.py
- docs/architecture/FUTURE_UPGRADE_DOWNGRADE_FLEXIBILITY_20260615.md

Validation performed:
- python -m compileall -q . passed.
- Lightweight smoke import for main patched modules passed using a dummy Streamlit module.
- AI prepared pattern count checked: 1203 patterns, 0 missing answer_rule.

Run command:
streamlit run adx_dashpoard.py

Recommended Git upload:
git add .
git commit -m "Add NLP pipeline, Liquid Glass drawer, AI pattern rules, alpha delta points"
git push origin main
