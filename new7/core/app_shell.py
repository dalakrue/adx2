import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None

from core.common import init_state
from core.styles import apply_global_styles, auto_close_sidebar_script
from core.navigation import sidebar_nav
from core.data_connectors import maybe_refresh
from core.system_upgrade import render_global_status_bar
from core.uiux import render_universal_header, render_data_quality_card, render_mobile_hint_once
from core.system_contract import (
    init_system_contract,
    start_tab_timing,
    finish_tab_timing,
    render_relationship_matrix,
    maybe_persist_runtime_snapshot,
    update_data_quality_from_session,
)


def _safe_run_page(tab_name, show_func):
    start_perf = start_tab_timing(tab_name)
    try:
        render_universal_header(tab_name)
        render_data_quality_card()
        render_mobile_hint_once()
        with st.expander("🔗 Open System Relationship + Timing", expanded=False):
            render_relationship_matrix(location=f"tab_{tab_name}", compact=True)
        show_func()
        finish_tab_timing(tab_name, start_perf, ok=True)
    except Exception as exc:
        finish_tab_timing(tab_name, start_perf, ok=False, error=str(exc))
        st.error(f"{tab_name} page failed to load.")
        with st.expander("Show error detail"):
            st.exception(exc)


def _load_tab(tab):
    if tab == "Home":
        from tabs.home import show
        return show

    if tab == "Engine":
        from tabs.engine import show
        return show

    if tab == "Train Data":
        from tabs.train_data import show
        return show

    if tab == "Pre Original":
        from tabs.pre_original import show
        return show

    if tab == "Database":
        from tabs.database_tab import show
        return show

    from tabs.profile import show
    return show


def run_app():
    try:
        st.set_page_config(
            page_title="M1 ADX Quant Pro",
            page_icon="⚡",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        # Safe when another entry point already configured Streamlit.
        pass

    try:
        init_state()
        init_system_contract()
    except Exception as exc:
        st.error("App state initialization failed.")
        st.exception(exc)
        return

    try:
        phone_mode = bool(st.session_state.get("phone_mode", False))
        apply_global_styles(phone_mode)
        auto_close_sidebar_script()
    except Exception as exc:
        st.warning("Styles failed to load, but the app will continue.")
        with st.expander("Show style error"):
            st.exception(exc)

    try:
        st_autorefresh(interval=600000, key="ten_min_refresh")
    except Exception:
        pass

    try:
        if st.session_state.get("ws_enabled", False):
            try:
                from core.websocket_feed import consume_websocket_into_session
                consume_websocket_into_session()
            except Exception:
                pass

        maybe_refresh(
            st.session_state.get("symbol", "XAUUSD"),
            st.session_state.get("twelve_api_key", ""),
            int(st.session_state.get("refresh_seconds", 600)),
            bridge_url=st.session_state.get("doo_bridge_url", ""),
            bridge_token=st.session_state.get("doo_bridge_token", ""),
        )
    except Exception as exc:
        st.warning("Auto data refresh failed. You can still use the app manually.")
        with st.expander("Show refresh error"):
            st.exception(exc)

    try:
        update_data_quality_from_session(persist=False)
        maybe_persist_runtime_snapshot("app_cycle")
    except Exception:
        pass

    try:
        tab = sidebar_nav()
    except Exception as exc:
        st.error("Sidebar navigation failed.")
        st.exception(exc)
        return

    try:
        render_global_status_bar(tab)
    except Exception as exc:
        st.caption(f"Global status bar skipped safely: {exc}")

    show = _load_tab(tab)
    _safe_run_page(tab, show)