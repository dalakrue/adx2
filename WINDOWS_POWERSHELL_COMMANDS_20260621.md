# Windows PowerShell Run Commands

## Extract and enter the project

```powershell
Expand-Archive -Path ".\ADX_Quant_Pro_EURUSD_H1_Ten_Paper_Shadow_20260621.zip" `
  -DestinationPath ".\ADX_Quant_Pro_EURUSD_H1_Ten_Paper_Shadow_20260621" -Force
Set-Location ".\ADX_Quant_Pro_EURUSD_H1_Ten_Paper_Shadow_20260621"
```

## Create Python 3.12 environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Back up and migrate the database

```powershell
py -3.12 tools\migrate_ten_paper_20260621.py --backup
py -3.12 tools\migrate_ten_paper_20260621.py --verify-only
```

## Run tests

```powershell
py -3.12 -m pytest -q
```

## Run the application

```powershell
streamlit run app.py
```

Use the existing Settings **Run Calculation + Open Lunch** action. Opening/closing Lunch fields or switching tabs reads the last published generation and does not run the new research transaction.

## Reproduce performance measurements

```powershell
py -3.12 tools\benchmark_ten_paper_20260621.py
```
