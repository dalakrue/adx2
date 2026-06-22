# Local Windows PowerShell Run Instructions

Open PowerShell in the extracted project folder or set the folder first:

```powershell
$ProjectPath = "<path-to-extracted-project>"
Set-Location $ProjectPath
```

Create and activate a Python 3.12 virtual environment:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Initialize the analytical history database:

```powershell
python .\scripts\migrate_regime_trust_20260621.py
```

Run tests:

```powershell
python -m pytest -q
```

Start the application:

```powershell
streamlit run app.py
```

The browser normally opens automatically. The main file must remain `app.py`.

To stop the server, press `Ctrl+C`. Do not put API keys in source files, terminal history, screenshots, or Git commits; use the existing secure application/Streamlit secret workflow.
