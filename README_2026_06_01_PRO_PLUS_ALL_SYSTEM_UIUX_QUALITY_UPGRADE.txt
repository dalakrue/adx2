PRO PLUS ALL-SYSTEM UIUX + QUALITY UPGRADE

What was upgraded without deleting original functions:

1) Global UI/UX
- Added animated ocean-glass background layer.
- Added compact quality HUD below the shared connector HUD on every tab.
- Added more consistent glass cards, mobile grid behavior, soft animated popups, and quality badges.

2) Relationship between tabs/files/connectors
- Added core/pro_quality_upgrade.py as a safe contract layer.
- Every app cycle now repairs shared session fields: tab_choice, symbol, timeframe, last_df.
- Every tab reads the same normalized dataframe contract, so bad/dirty OHLC data is cleaned before analysis.
- Database tab is now included in DEFAULT_TABS and sidebar navigation.

3) Connector/data quality
- Shared dataframe is normalized into time/open/high/low/close/volume.
- Duplicate time rows, invalid OHLC rows, NaN/inf values, and overly large memory frames are safely cleaned.
- Data quality score is generated for all tabs.

4) Math / logic quality
- Added market regime diagnostics: BUY_TREND_CONTROL, SELL_TREND_CONTROL, HIGH_VOLATILITY_MIXED, RANGE_OR_WAIT.
- Added directional-efficiency and volatility sanity checks.
- Added logic_score to help detect whether the current data is reliable enough for decision modules.

5) ML algorithm quality
- Added ML readiness status: NOT_ENOUGH_DATA, BASIC_TRAINING_READY, ROBUST_TRAINING_READY.
- The Train Data tab can now benefit from global row/data quality diagnostics before model training.

6) Database quality
- Quality events are saved every ~120 seconds to data/pro_quality_events.csv through the existing database layer.
- Existing CSV + SQLite mirror behavior is preserved.

How to run:
streamlit run adx_dashpoard.py --server.port 8501

If port 8501 is already used:
streamlit run adx_dashpoard.py --server.port 8502
