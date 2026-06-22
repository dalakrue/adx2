# Startup and Deployment Test Report

## Contract

- Main file: `app.py`
- Runtime: `python-3.12`
- Streamlit requirement: `streamlit>=1.35,<2`
- No Windows-only MetaTrader package in Linux requirements.
- No heavy local LLM or paid AI dependency added.

## Results

- `python -m compileall -q .`: **PASS**
- `python tools/streamlit_cloud_preflight.py`: **PASS**
  - imported `core.ui.styles`
  - imported `core.styles`
  - imported `tabs.antd_page_router_20260615`
  - imported `app`
- Streamlit headless server on port 8517: **STARTED**
- `/_stcore/health`: **ok**
- Focused six-field/migration suite: **85 passed**
- Final full repository suite: **338 passed in 99.52 seconds**
- DuckDB transition/history tests: **PASS** with the dependency already declared in `requirements.txt`

## Validation commands

```bash
python -m compileall -q .
python tools/streamlit_cloud_preflight.py
pytest -q
streamlit run app.py
```

## Streamlit Cloud

Use `app.py` as the main file and Python 3.12. Configure connector secrets through the existing project mechanism. Refresh Data does not run the protected calculation; after a successful refresh, press Run Calculation only when a new canonical generation is required.
