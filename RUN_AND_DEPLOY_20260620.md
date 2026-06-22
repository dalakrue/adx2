# Install, Run, and Deploy

## Preferred main entry

`app.py`

`main.py` and `adx_dashpoard.py` remain compatibility entry points, but `app.py` is preferred because it explicitly inserts the project root before importing the dashboard.

## Windows PowerShell

```powershell
cd "C:\path\to\EURUSD_H1_Advanced_Reliability_Shift_20260620"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m compileall .
python -m pytest -q
streamlit run app.py
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Windows Command Prompt

```bat
cd /d "C:\path\to\EURUSD_H1_Advanced_Reliability_Shift_20260620"
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m compileall .
python -m pytest -q
streamlit run app.py
```

## Streamlit Community Cloud

1. Push the complete folder contents to the root of a GitHub repository.
2. In Streamlit Community Cloud choose **Create app**.
3. Select the repository and branch.
4. Set **Main file path** to `app.py`.
5. Keep `runtime.txt` and `.python-version`; both specify Python 3.12.
6. Copy only required private keys/settings into the app's Secrets interface, following `.streamlit/secrets.example.toml`. Do not commit real secrets.
7. Deploy and check the app logs for requirement installation and the normal Streamlit health startup.

## Local startup verification performed

The health endpoint `/_stcore/health` returned `ok` on port 8517 using `streamlit run app.py --server.headless true`.
