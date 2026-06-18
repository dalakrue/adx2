# Quick Fix — Finnhub, One-Click Lunch, Regime Standards, PowerBI Bounds

## Completed

- Added the canonical Finnhub API Connector to the existing Settings tab while keeping the compact sidebar connector.
- Changed the Settings action to **Run Calculation + Open Lunch**.
- The Settings run now calls the existing Lunch metric, PowerBI, regime and shared-sync logic, stores the normal caches, and opens Lunch automatically.
- Removed the intermediate **Load Original Lunch Renderer** gate.
- Original Lunch metrics, 010 Reverse Decision, details, history, PowerBI projection, copy and export displays now read the completed caches automatically.
- Moved the floating three-dot menu to the fixed middle-right position on laptop and phone.
- Added an open/close table at the top of Dinner → Regime Summary for:
  - Lower Standard: 1 day
  - Middle Standard: 5 days
  - Higher Standard: 25 days
  - Regime score /10
  - Ascending KNN and Greedy priority and score /10
- Extended the regime merge window to support up to 600 H1 rows for the 25-day display.
- Added vertical projection whiskers from lower bound to upper bound in Lunch PowerBI.
- Added an expanded vertical table containing H1 point, time, lower bound, projection, upper bound, Alpha point and Delta point.

## Protection

No new trading/prediction engine was introduced. The one-click orchestrator calls existing project functions and caches. The new regime standards and vertical Alpha/Delta/bound table are display-level aggregation and visualization.

## Validation

- Python compileall: PASS
- Final synchronization validation: PASS
- Finnhub/NLP/Lunch/Research validation: PASS
- Architecture validation: PASS
- Streamlit AppTest startup: PASS, zero exceptions
- Settings Run Calculation → Lunch route AppTest: PASS, zero exceptions
- Synthetic PowerBI Alpha/Delta + bounds render: PASS, zero exceptions
- Headless Streamlit HTTP startup: PASS (HTTP 200)
