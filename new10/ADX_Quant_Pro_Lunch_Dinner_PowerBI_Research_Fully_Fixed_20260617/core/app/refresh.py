import time
import streamlit as st
from core.data_connectors import maybe_refresh


def run_deferred_refresh():
    """Refresh market data only when navigation is not actively switching tabs."""
    nav_age = time.time() - float(st.session_state.get("ui_navigation_click_ts", 0.0) or 0.0)
    if nav_age >= 3.0:
        maybe_refresh(
            st.session_state.get("symbol", "XAUUSD"),
            st.session_state.get("twelve_api_key", ""),
            int(st.session_state.get("refresh_seconds", 600)),
            bridge_url=st.session_state.get("doo_bridge_url", ""),
            bridge_token=st.session_state.get("doo_bridge_token", ""),
        )
    else:
        st.session_state["deferred_auto_refresh_reason"] = "Skipped one auto refresh because user navigation was active."
