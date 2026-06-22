# Local and Streamlit Community Cloud Deployment

## Correct main file

- **Main file name:** `app.py`
- **Streamlit Community Cloud Main file path:** `app.py`
- **Python runtime:** `python-3.12` from `runtime.txt`

No `packages.txt` was added because this release does not require an operating-system package.

## Windows PowerShell local run

Open PowerShell in the extracted project root, then run:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
streamlit run app.py
```

For later runs:

```powershell
cd "C:\path\to\your\extracted\project"
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Do not run the command from the `core` folder. Run it from the folder that contains `app.py` and `requirements.txt`.

## Streamlit Community Cloud

1. Upload the extracted project contents to the root of the GitHub repository.
2. In Streamlit Community Cloud, create or edit the app.
3. Select the repository and branch.
4. Set **Main file path** to exactly:

```text
app.py
```

5. Deploy. `runtime.txt` requests Python 3.12.
6. Open Settings, paste API keys through the existing mobile paste boxes, connect the required data source, and press **Run Calculation + Open Lunch**.
7. Lunch opens automatically after successful canonical publication. Field 4 reads the same generation and does not recalculate when opened.

## Cloud notes

- Linux path case was checked by compile and existing preflight tests.
- No local absolute Windows path was added to production Python code.
- MetaTrader 5 remains Windows-local and is intentionally not required by the Cloud requirements.
- API keys remain session/settings inputs; no key is embedded in the ZIP.
- The new Similar-Day store is created automatically in `data/` when needed.
