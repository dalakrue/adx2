# Streamlit Cloud deployment fix — 2026-06-19

## What caused the three-hour stall

The deployed app log used **Python 3.14.6**, but `requirements.txt` required
`numpy<2.3`. NumPy versions below 2.3 do not provide a compatible Python 3.14
Linux wheel. Streamlit Cloud's `uv` resolver therefore selected NumPy 2.2.x and
then attempted a source build after printing `Resolved ... packages`. Building
NumPy from source can remain at that stage for a very long time.

## Code fix included

`requirements.txt` now uses environment markers:

- Python 3.12/3.13: `numpy>=1.26,<2.3`
- Python 3.14+: `numpy>=2.3,<2.4`

This preserves the original dependency range on the recommended runtime while
allowing Streamlit Cloud's current Python 3.14 image to download a binary wheel
instead of compiling NumPy.

`runtime.txt` and `.python-version` both request Python 3.12 for local tooling.
Streamlit Community Cloud chooses Python from **Advanced settings** when an app
is first deployed; changing `runtime.txt` does not change an already-created
cloud environment.

## Deploy

1. Replace the GitHub repository contents with this folder's contents.
2. Commit and push to the `main` branch.
3. In Streamlit Cloud, reboot the app and clear cache.
4. Main file: `adx_dashpoard.py`.
5. Recommended clean deployment: delete/redeploy the app and choose Python 3.12
   under Advanced settings. The dependency fix also permits the existing
   Python 3.14 deployment to install without compiling NumPy.

## Local command

```powershell
python -m pip install -r requirements.txt
python -m streamlit run adx_dashpoard.py
```
