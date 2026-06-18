HOME + CSS + BACKGROUND + ANIMATED POPUP UPGRADE

What changed:
1. Added additive CSS patch in core/ui/styles.py.
2. Added animated ocean background using .stApp::before and .stApp::after.
3. Added Home hero glass card, compact status pills, animated snapshot cards, and soft popup note in tabs/home_split/pro_home_dashboard.py.
4. Kept original Home implementation untouched under tabs/home_split/implementation.py.
5. Kept compatibility wrappers: tabs/home.py and core/styles.py still import the modular implementation.
6. No existing tab logic was removed. If the new Home Pro layer fails, original Home still renders through the existing try/except guard.

Run:
streamlit run main.py --server.address 0.0.0.0 --server.port 8501

If port 8501 is busy, use:
streamlit run main.py --server.address 0.0.0.0 --server.port 8502
