2026-06-02 Home copy/refresh/phone upgrade

What changed:
1. Home copy export is now simple: one Copy All Home Data button, no large GPT export text area shown by default.
2. The copy button uses browser clipboard + mobile fallback for phone tap/touch.
3. Copy payload includes Home shared-data metrics, account summary, Doo Prime deep analysis, Data Modeling/deep-frame metrics, and latest candles.
4. Detailed open-position rows are excluded from the copy payload to avoid inefficient repeated position-entry data.
5. Sidebar Quick Refresh now also rebuilds Doo Prime Analysis and Data Modeling blocks from the same shared dataframe. You no longer need to press a second Home/Doo refresh button just to update those panels.
6. Older/long Home panels are placed behind closed expanders so the start page is cleaner and less annoying during normal use.
7. Existing original code paths are preserved; this is an additive/safe UI and workflow upgrade.

Run:
streamlit run main.py --server.address 0.0.0.0 --server.port 8501
