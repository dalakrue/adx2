# Main account module.
# Keeps original implementation unchanged and exposes show().

try:
    from .implementation import show
except Exception as exc:
    import streamlit as st

    def show():
        st.error('Account module failed to load safely.')
        st.caption(f'Import error: {exc}')

__all__ = ['show']
