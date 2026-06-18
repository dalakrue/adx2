@echo off
cd /d %~dp0
python -m streamlit run adx_dashpoard.py --server.address 0.0.0.0 --server.port 8501
pause
