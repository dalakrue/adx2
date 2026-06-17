"""Preferred Streamlit entry point for the future-proof app shell.

Run with:
    streamlit run app.py

The historical entry point adx_dashpoard.py is kept for backward compatibility.
Both launch the same app shell.
"""

from adx_dashpoard import main


if __name__ == "__main__":
    main()
