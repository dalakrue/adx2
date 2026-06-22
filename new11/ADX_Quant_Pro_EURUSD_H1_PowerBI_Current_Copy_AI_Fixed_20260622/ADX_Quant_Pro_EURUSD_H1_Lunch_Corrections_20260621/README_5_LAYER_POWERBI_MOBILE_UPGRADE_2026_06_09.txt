5-Layer Power BI + ML Data Visualization Upgrade
Date: 2026-06-09

Changed file:
- tabs/home.py

Backup preserved:
- tabs/home.py.bak_before_5layer_powerbi_upgrade

Main changes:
- Data Visualization now calculates only after the Run Calculating button is clicked.
- Old original price chart flow is removed from the Data Visualization inner tab.
- Added one Power BI-style Plotly dashboard containing five separate layer results:
  1. Layer 1 Regime Engine
  2. Layer 2 Institutional Flow Engine
  3. Layer 3 Prediction Ensemble
  4. Layer 4 Deep AI Layer
  5. Layer 5 Forecast Engine
- Added top metric cards: Master Score, Bull Probability, Regime, Last Regime Change, Days In Regime, Estimated Days Remaining, Predicted Next Regime Change.
- Added newest-first regime history table so the latest/today row appears first.
- Added mobile/low-CPU performance improvements: 1,000-3,000 row limit, float32 columns, category regime/status text, cached cleaned OHLC, cached 5-layer outputs, session_state result reuse, downsampled Plotly chart.
