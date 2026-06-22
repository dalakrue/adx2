# Exact Windows and Streamlit Cloud Commands

## Windows PowerShell — install and run

```powershell
cd "C:\path\to\ADX_Quant_Pro_EURUSD_H1_history_performance_20260620"
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python .\tools\migrate_history_evidence_20260620.py --backup
python -m compileall -q .
pytest -q
streamlit run app.py
```

Open `http://localhost:8501`. The correct main entry is **`app.py`**.

## Windows CMD — install and run

```bat
cd /d "C:\path	o\ADX_Quant_Pro_EURUSD_H1_history_performance_20260620"
py -3.12 -m venv .venv
call .venv\Scriptsctivate.bat
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python tools\migrate_history_evidence_20260620.py --backup
python -m compileall -q .
pytest -q
streamlit run app.py
```

## GitHub upload from PowerShell

```powershell
cd "C:\path\to\ADX_Quant_Pro_EURUSD_H1_history_performance_20260620"
git init
git add .
git commit -m "History-first lazy rendering and evidence hardening"
git branch -M main
git remote remove origin 2>$null
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main --force
```

## Streamlit Community Cloud

1. Push the folder to GitHub with the commands above.
2. In Streamlit Community Cloud choose **Create app**.
3. Repository: `YOUR_USERNAME/YOUR_REPOSITORY`; branch: `main`; main file path: **`app.py`**.
4. Use Python **3.12**. The included `runtime.txt` is the package contract.
5. Add secrets only in the Cloud Secrets panel; never commit `.streamlit/secrets.toml`.
6. Deploy. The schema is created automatically on first successful canonical publication, or can be pre-created locally with the migration command.

## Validation commands

```powershell
python tools\streamlit_cloud_preflight.py
pytest -q tests	est_history_performance_research_20260620.py
streamlit run app.py --server.headless true --server.port 8501
```
