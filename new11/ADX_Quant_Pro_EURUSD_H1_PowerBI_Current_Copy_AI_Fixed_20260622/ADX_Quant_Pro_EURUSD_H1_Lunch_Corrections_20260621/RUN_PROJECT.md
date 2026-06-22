# Run ADX Quant Pro EURUSD H1

Use Python 3.12, matching `runtime.txt`.

```powershell
cd "<project-folder>"
py -3.12 -m pip install -r requirements.txt
py -3.12 -m streamlit run main.py
```

The application starts in Settings. Use **Run Calculation + Open Lunch**. A successful run publishes one canonical generation, opens the main Lunch view, and displays the trusted decision cards, cached Power BI projection, and Full Metric History from the same calculation ID.

For local Windows with the restored MT5 connector, install the normal requirements plus MetaTrader5 in one command:

```powershell
py -3.12 -m pip install -r requirements-windows-mt5.txt
py -3.12 -m streamlit run app.py
```

For Streamlit Cloud/Linux, keep using `requirements.txt`; MT5 needs a local Windows MetaTrader 5 terminal, while Twelve Data remains available on Cloud.
