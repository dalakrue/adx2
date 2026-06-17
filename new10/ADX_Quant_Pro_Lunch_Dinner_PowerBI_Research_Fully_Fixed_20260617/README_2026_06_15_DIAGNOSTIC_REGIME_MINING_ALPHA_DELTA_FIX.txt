2026-06-15 Diagnostic + Regime Alpha/Delta + Data Mining Fix

Base: user uploaded ZIP.

Non-destructive upgrade rules followed:
- No new top-level tab.
- No new ML prediction engine.
- No external API requirement.
- Existing calculations/tables/charts/copy buttons are preserved.
- New features are inside existing tabs/open-close fields.
- CPU/RAM safe: deterministic pandas groupby/quantile/z-score only; no heavy training loop.

Added / fixed:
1) Data Analysis inner tab
   - Added Diagnostic Analysis table.
   - Added Sampling table.
   - Added Estimating table.
   - Added Hypothesis Testing table.
   - Added 3D Data Cube table.

2) Regime / Dinner
   - Added top Regime Alpha / Delta st.metric cards.
   - Regime Alpha uses previous-vs-now regime difference, ratio drift, and divergence mean.
   - Regime Delta uses previous-alpha vs now-alpha difference, ratio drift, and divergence mean.
   - Added Regime Alpha/Delta calculation table inside an open/close field.

3) PowerBI Regime Projection
   - Added Regime Alpha/Delta metrics before the chart.
   - Existing vertical alpha/delta markers remain display-only.

4) Data Mining tab
   - Added Pattern Evaluation.
   - Added Clustering analysis.
   - Added Association rules.
   - Added Anomaly analysis.
   - Added 3D Data Cube.

5) AI Assistant tab
   - Added the same advanced data-mining panel inside AI Assistant > Data Mining.
   - Existing Enter-to-answer chat, Local NLP, Deep Analysis, and History remain unchanged.

6) Router stability
   - Fixed a duplicate Home renderer call in the AntD page router to prevent duplicated Home/Lunch output and reduce CPU/RAM use.

Main files changed:
- core/advanced_analytics_20260615.py
- tabs/research.py
- tabs/dinner_morning_data_patch_20260614.py
- tabs/final_three_center_upgrade_20260614.py
- tabs/ai_assistant_lite.py
- tabs/antd_page_router_20260615.py

Run:
streamlit run adx_dashpoard.py
