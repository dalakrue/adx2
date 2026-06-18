ENGINE TAB FULL UPGRADE - 2026-06-01

What changed:
1. Fixed Engine upgrade layer runtime issue:
   - tabs/engine_split/combined_engine.py now imports numpy as np.
   - It safely imports the original Engine indicator/quant helpers.
   - If those helpers are unavailable, Engine now uses a local fallback indicator engine instead of blanking.

2. Added non-destructive Engine decision layer:
   - Status, rows, bias, safe %, ADX, pressure, 10-candle move %, fat-tail Z.
   - Compact interpretation notes for BUY / SELL / WAIT.
   - Guard warning when ADX or pressure is weak.

3. Improved copy/paste export:
   - Engine GPT export now includes summary, interpretation rules, risk warning, and latest 50 candles.
   - Export can be copied from text area or downloaded as TXT.

4. Preserved original code:
   - Original Engine / Prelive / Backtest inner tabs still render from the existing modules.
   - Upgrade layer is additive and safe-fails if something unexpected happens.

How to run:
   pip install -r requirements.txt
   streamlit run main.py --server.address 0.0.0.0 --server.port 8501

Important:
- Connect MT5 / Doo Bridge / TwelveData from the sidebar first.
- Engine reads shared st.session_state['last_df'].
- For hedged Doo Prime baskets, use Engine direction together with account margin risk before closing one full side.
