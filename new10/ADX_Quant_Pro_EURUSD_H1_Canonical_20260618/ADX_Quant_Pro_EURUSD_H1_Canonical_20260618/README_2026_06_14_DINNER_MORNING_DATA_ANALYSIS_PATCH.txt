2026-06-14 Dinner / Morning / Data Analysis Patch

Base ZIP upgraded non-destructively.

Changed display placement only:
- Regime visible tab label is now Dinner.
- Doo Prime visible tab label is now Morning.
- Dinner contains inner tabs:
  1. Regime Summary
  2. Combine Logic
  3. AI Assistant
- Dinner Combine Logic contains:
  - PowerBI Regime Projection
  - Priority + Decision + Reliability KNN/Greedy
  - Final Synced Intelligence: ML Tables + KNN/Greedy + News/NLP + Quant Structure + Research
  - Original Data / Advanced Details at the last place, protected by a manual load button.
- Lunch keeps Full Metric Details + History and adds the smoother/error-adjusted red prediction line display with reliability warning.
- Research/Data Analysis adds a result table for Descriptive Analysis, Predictive Analysis, and Prescriptive Analysis.

Preserved rules:
- No existing logic, calculation, table, chart, copy button, export, JSON output, ML table, history table, function, tab source, or section source was deleted.
- No external API was added.
- No heavy neural network was added.
- No new prediction engine was added.
- Heavy original advanced display is guarded by manual Run/Load buttons.

Validation completed:
- Python compile check passed for all .py files.
- ZIP integrity check passed after rebuild.
