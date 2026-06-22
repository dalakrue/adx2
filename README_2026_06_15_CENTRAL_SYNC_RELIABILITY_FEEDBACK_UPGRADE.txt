ADX Quant Pro / new7 — 2026-06-15 Central Sync + Reliability + Feedback Upgrade
================================================================================

Base ZIP
--------
This upgrade was applied on top of the latest uploaded ZIP:
59407b0c-4e5c-411a-ac21-4e7faa1fd206.zip

Main rule followed
------------------
No new top-level tab, page, sidebar, or menu section was added.
Existing tabs, tables, charts, metrics, copy buttons, exports, ML/NLP/AI functions,
Power BI projection, priority logic, regime logic, menu logic, and tab-choice logic
were preserved.

Changed files
-------------
1. core/adx_shared_sync_20260615.py
   - New additive shared calculation sync module.
   - Creates one shared result in Streamlit session_state:
       adx_shared_calc_result_20260615
       shared_calc_result
   - Reads existing outputs only; it does not replace original engines.
   - Central result contains:
       current market summary
       data quality score
       calibrated reliability score
       prediction-vs-actual feedback summary
       Regime Alpha / Delta validation
       hourly priority calibration table
       AI grounding contract
   - Adds phone-safe default row limits and lazy shared-result refresh.

2. core/tab_state_stability_20260615.py
   - New state-only tab repair helper.
   - Normalizes old/invalid active_page, tab_choice, active_subpage, and inner-tab keys.
   - Keeps the existing tab choice design unchanged.
   - Prevents lock problems where clicking one tab can remain stuck on another tab.

3. core/app/runner.py
   - Installs phone safety defaults at app boot.
   - Stabilizes tab state during startup and after navigation.
   - Refreshes the shared calculation result before page render and after page render.
   - If one shared sync step fails, the app continues safely.

4. tabs/antd_page_router_20260615.py
   - Added _safe_component wrapper around existing renderers.
   - One broken renderer now shows a contained warning instead of crashing the whole page.
   - Existing routes and page choices remain unchanged.
   - Research > KNN / Greedy can now also read:
       adx_hourly_priority_calibrated_20260615
     before falling back to older priority tables.

5. tabs/ai_assistant_lite.py
   - Wrapped AI context builder so AI reads the central shared result.
   - Wrapped AI answer generation with an AI Grounding Guard.
   - AI now cannot silently conflict with Regime, Priority, Power BI / Prediction,
     Reliability, or Data Quality.
   - Added show() compatibility alias for page wrappers.

6. tabs/home.py
   - Wrapped existing Home/Lunch show() with shared-sync before/after refresh.
   - Existing Home/Lunch UI and calculations remain unchanged.

What improved
-------------
1. Central Calculation Sync
   - All major tabs can now read one shared session result instead of each tab relying
     only on separate scattered keys.
   - The shared result is refreshed before and after rendering so new calculations
     become available to other tabs.

2. Reliability Score Calibration
   - Reliability is now capped by prediction-vs-actual feedback.
   - Data quality weakness and regime/prediction conflict reduce reliability.
   - Stored at:
       adx_reliability_calibrated_20260615

3. Prediction-vs-Actual Feedback Loop
   - Reads existing prediction feedback history when available.
   - If not enough history exists, it uses a conservative volatility proxy until
     completed prediction-vs-actual rows exist.
   - Stored at:
       adx_prediction_feedback_20260615

4. Regime Alpha / Delta Validation
   - Adds Regime Alpha Now, Previous Alpha, Alpha Ratio, Delta, and validation status.
   - Uses existing OHLC/regime history only.
   - Stored at:
       adx_regime_alpha_delta_20260615

5. Hourly Priority Ranking
   - Creates an anti-constant calibrated priority table using existing priority rows
     when available, or existing OHLC data if priority rows are not available yet.
   - Adds Shared Sync Score, Priority Rank 1-14, Priority Label, and calibration reason.
   - Stored at:
       adx_hourly_priority_calibrated_20260615

6. AI Assistant Grounding
   - AI answers now include a grounding guard when reliability/data quality is low or
     Regime and Power BI / Prediction conflict.
   - AI is explanation-only and cannot override the system decision.
   - Stored at:
       adx_ai_grounding_20260615

7. Phone Performance
   - Shared sync reads only limited tail rows by default.
   - Uses session-state caching/signature logic to avoid recalculating the shared result
     unnecessarily.
   - Keeps heavy renderers behind the existing run/load gates.

8. Tab State Stability
   - Invalid old names such as Doo Prime, Regime, Metric, PowerBI, etc. are normalized
     to the current existing tab names.
   - Duplicate AI Assistant inner/top labels are handled safely.

9. Error Handling
   - Existing renderer calls in the AntD router are now component-safe.
   - If Power BI, Reliability, Research, Dinner, Morning, or AI renderer fails, the
     rest of the active tab continues.

How to run
----------
1. Unzip the package.
2. Open terminal inside the extracted project folder.
3. Install requirements if needed:
       pip install -r requirements.txt
4. Run:
       streamlit run adx_dashpoard.py

Validation completed
--------------------
- Python compile check passed for all project .py files using compileall.
- New shared sync module was smoke-tested with sample OHLC + prediction feedback data.
- No top-level tab/page/sidebar/menu addition was made.

Notes
-----
This is an additive safety/sync patch. It intentionally does not remove or rewrite
your old calculation engines. The original tables/charts/copy/export functions remain
available, while the new shared result acts as a central alignment layer across tabs.
