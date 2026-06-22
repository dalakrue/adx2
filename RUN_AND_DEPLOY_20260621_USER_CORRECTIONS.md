# Run and Deploy

## Windows local run

```powershell
cd <extracted-package-folder>
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Validation commands

```powershell
python -m compileall -q .
pytest -q
streamlit run app.py --server.headless true
```

## Streamlit Community Cloud

- Repository entry file: `app.py`
- Python version: `3.12` (`runtime.txt`)
- Install file: `requirements.txt`
- Start command used by Streamlit: `streamlit run app.py`
- Put real API credentials only in Streamlit Secrets. Do not edit `.streamlit/secrets.example.toml` with live values.
