# Lunch Four-Core-Field Restoration — 2026-06-19

## Visible Lunch layout

The Lunch root now has exactly four top-level open/close fields, in this order, and every field starts closed:

1. **Full Metric 25-Day History + 10 Decision Histories**
   - Shows the overall Full Metric historical table for the latest completed 25-day generation.
   - Restores every published factor/decision history table inside the same field.
   - Historical rows are newest completed H1 first and are not reduced to the current hour.
2. **Power BI Price Prediction Projection**
   - Uses the already-published calibrated Power BI cache only.
   - Does not start a second calculation.
3. **25-Day Regime History + Lower / Medium / Higher Standards**
   - Shows the overall 25-day regime history.
   - Shows lower, medium, and higher standard history tables, each viewed across the latest 25-day historical generation.
4. **All Current Data Display**
   - Isolates current canonical identity, decision, operational metrics, priority/ranking, position-sizing publication, and current Full Metric snapshot tables.

Older Lunch child-page navigation and duplicate top-level fields are removed from the visible route.

## Sidebar removal

The Streamlit native sidebar, its collapsed reopen button, and its fallback rendering path are removed from the active app. The existing main-page three-dot Liquid Drawer remains the navigation/control surface.

## Protected behavior

No trading formula, scoring threshold, forecast engine, Full Metric calculation, regime calculation, priority logic, or Power BI calculation was changed. The restoration is a display, routing, and packaging change around already-published calculation results.

## Validation

- Python compile check passed for `core`, `tabs`, `ui`, and `tests`.
- Project regression suite: **197 passed**.
- Headless Streamlit startup smoke check reached the running server without a traceback or import failure.
