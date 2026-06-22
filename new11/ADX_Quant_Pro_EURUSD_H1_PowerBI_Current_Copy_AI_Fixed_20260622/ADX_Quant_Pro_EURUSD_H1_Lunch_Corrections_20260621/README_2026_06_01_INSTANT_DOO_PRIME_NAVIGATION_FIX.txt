# 2026-06-01 Instant Doo Prime Navigation Fix

This patch fixes the slow Home inner-tab switch problem where Launcher / Doo Prime Analysis could block entry into the Doo Prime panel.

## What changed

1. Inner tab buttons now use Streamlit callbacks. The selected section is set before the rerun starts.
2. Global auto-refresh is skipped for a few seconds after any navigation click, so tab entry never waits behind MT5/TwelveData/Doo Bridge refresh.
3. The Home GPT Copy Export no longer builds while the expander is closed. Press **Build / refresh GPT export** only when you need copy text.
4. Doo Prime Analysis no longer performs a 60,000-candle connector fetch automatically on page entry.
5. Deep analysis still appears instantly when shared data exists, using the current dataframe. Manual **Refresh All 4 Now** still performs a fresh connector fetch.
6. SAFE_DEMO remains disabled unless you explicitly allow it from the sidebar.

## Run

```powershell
cd path\to\new7
streamlit run adx_dashpoard.py --server.address 0.0.0.0 --server.port 8501
```

If port 8501 is busy, use 8502 or close the old Streamlit terminal.
