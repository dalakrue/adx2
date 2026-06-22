ADX QUANT PRO / NEW7 — EURUSD H1 CANONICAL BUILD

Preferred run command:
  pip install -r requirements.txt
  streamlit run app.py

Main entry file:
  app.py

Compatible historical entry files:
  main.py
  adx_dashpoard.py

Important protection:
- Full Metric Detail + History remains the canonical source of truth.
- tabs/eurusd_h1_matrix.py is protected and unchanged.
- The existing Regime inner section and its tables are visible inside Full Metric Detail + History without a second Run button or hidden inner tab.
- Current/latest completed H1 history remains first; older history remains accessible.
