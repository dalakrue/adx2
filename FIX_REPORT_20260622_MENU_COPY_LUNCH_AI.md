# Fix Report — Menu Copy, Settings→Lunch, Lunch Field 5 AI

Date: 2026-06-22

## Fixed

1. Added direct **Copy Short** and **Copy Full** buttons inside the menu controls beside Refresh.
   - Copy Short uses the canonical short payload builder and remains bounded by the existing ChatGPT-free-plan style limits.
   - Copy Full copies the full Lunch canonical six-field payload.
   - Buttons use the existing central clipboard component, not a new engine.

2. Changed menu Run Calculation behavior.
   - Menu Run now says **Run Calculation + Open Lunch**.
   - After a successful run, or when a previous valid canonical run exists, the app opens Lunch automatically.
   - Power BI/Lunch cached visibility flags are set so the Lunch tab opens ready.

3. Changed Settings Run Calculation behavior.
   - The Settings button still performs the full existing calculation transaction.
   - After completion it opens Lunch automatically if a new or previous valid canonical generation exists.

4. Fixed Lunch Field 5 AI Assistant readiness.
   - The compact AI fact pack is now published during operational synchronization after the canonical generation is published.
   - Field 5 also performs a safe compact recovery from canonical state before showing the old “Run Calculation in Settings” message.
   - This does not recalculate protected trading logic; it only republishes the small read-only AI fact pack.

## Modified files

- `ui/canonical_copy_export_20260619.py`
- `ui/liquid_menu_popup_20260615.py`
- `ui/main_menu_drawer.py`
- `core/operational_sync_20260618.py`
- `tabs/antd_page_router_20260615.py`
- `tabs/ai_assistant_compact_20260619.py`

## Validation

- Ran Python compile check across the full project: `python3 -m compileall -q .`
- Streamlit runtime execution was not run in this sandbox because the sandbox does not have Streamlit installed.
