# Streamlit Cloud deployment

Use these settings when creating or rebooting the app:

- Repository: your GitHub repository
- Branch: `main`
- Main file path: `app.py`
- Python: controlled by `runtime.txt` (`python-3.12`)
- Dependencies: root `requirements.txt`

The Linux cloud build does not install the Windows-only MT5 Python package. Twelve Data, Finnhub, fallback and SAFE_DEMO remain available on Cloud. Local Windows MT5 users install with:

```powershell
py -3.12 -m pip install -r requirements-windows-mt5.txt
py -3.12 -m streamlit run app.py
```

Optional preflight from the project root:

```powershell
py -3.12 tools\streamlit_cloud_preflight.py
```
