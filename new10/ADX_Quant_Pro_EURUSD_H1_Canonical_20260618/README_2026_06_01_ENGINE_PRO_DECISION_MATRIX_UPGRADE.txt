ENGINE PRO DECISION MATRIX UPGRADE - 2026-06-01

What changed:
1. Added tabs/engine_split/pro_engine_upgrade.py as a non-destructive Engine upgrade layer.
2. Kept tabs/engine.py compatibility wrapper unchanged.
3. Kept original Engine / Prelive / Websocket / Backtest Original inner workspaces unchanged.
4. Added stronger OHLC normalization for MT5, TwelveData, bridge, websocket, and manual dataframe formats.
5. Added Engine Pro Decision Matrix:
   - Bias: BUY / SELL / WAIT
   - Trust % and scale/10
   - ADX, +DI, -DI, pressure
   - ATR %, M10/M30 momentum
   - fat-tail z-score
   - DVE directional volatility efficiency
   - rising/falling efficiency
   - data quality score
6. Added hedged basket full-side exit guards:
   - Exit BUY guard
   - Exit SELL guard
   These are intentionally strict because exiting one side of a hedged basket leaves one-way naked exposure.
7. Added Save Engine Snapshot button.
8. Added Build Pro GPT Export + Download TXT button.
9. Added latest feature table and close chart in an expander.
10. All new Streamlit widget keys are unique and prefixed with engine_pro_ to avoid duplicate key errors.

How to run:
1. Extract this ZIP.
2. Open terminal inside the new7 folder.
3. Run:
   streamlit run main.py

Safety note:
This upgrade improves analysis quality but does not guarantee market direction. For dangerous margin situations, use the exit guard with your Doo Prime account-risk panel before closing a full BUY or SELL side.
