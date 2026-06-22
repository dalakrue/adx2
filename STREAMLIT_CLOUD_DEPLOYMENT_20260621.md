# Streamlit Community Cloud Deployment

## Repository settings

- Main file: `app.py`
- Branch: your deployment branch, normally `main`
- Python target: 3.12
- Dependencies: `requirements.txt`

## Git commands

```powershell
git init
git add .
git commit -m "Add ten-paper shadow research validation layers"
git branch -M main
git remote add origin https://github.com/<YOUR-USER>/<YOUR-REPOSITORY>.git
git push -u origin main
```

For an existing repository:

```powershell
git add .
git commit -m "Add ten-paper shadow research validation layers"
git push origin main
```

## Cloud configuration

1. Select `app.py` as the main file.
2. Keep API keys only in Streamlit Secrets; do not commit them.
3. Confirm Python 3.12 in the Cloud advanced settings/runtime configuration.
4. Deploy, then open Settings and run the existing calculation action once.

## Pre-deployment checks performed

- declared Streamlit dependency import: PASS;
- changed core/UI modules import: PASS;
- `app.py` Streamlit health endpoint: `ok`;
- Cloud preflight tests: PASS;
- all collected tests: PASS in controlled groups.

The local verification container used Python 3.13.5, while the application explicitly targets Python 3.12. This is noted rather than treated as proof of every Cloud binary dependency; Cloud should install from `requirements.txt` on Python 3.12.
