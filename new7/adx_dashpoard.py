"""Main entry point for M1 ADX Quant Pro.
Run with:
    streamlit run adx_dashpoard.py

This file intentionally does not call st.set_page_config(); core.app_shell.run_app()
handles that once. Calling it twice can crash Streamlit on some versions.
"""

import streamlit as st


def main():
    try:
        from core.app_shell import run_app
        run_app()

    except ImportError as e:
        st.error("Import error. Check your project files and requirements.")
        st.code(str(e))

    except Exception as e:
        st.error("App crashed, but the entry file is working.")
        st.exception(e)


if __name__ == "__main__":
    main()
