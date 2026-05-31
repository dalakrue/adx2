import pandas as pd
import streamlit as st

from .connectors import safe_connect
from .shared_state import sync_backtest_keys_from_last_df, shared_data_status


def _show_shared_market_status():
    df = st.session_state.get("last_df")
    if isinstance(df, pd.DataFrame) and not df.empty:
        cols = st.columns(5)
        cols[0].metric("Shared Data", "ACTIVE")
        cols[1].metric("Rows", f"{len(df):,}")
        cols[2].metric("Source", st.session_state.get("source", "UNKNOWN"))
        cols[3].metric("Symbol", st.session_state.get("symbol", "XAUUSD"))
        cols[4].metric("TF", st.session_state.get("timeframe", "M1"))
        st.success("Twelve/MT5 data is available globally. All Engine inner tabs are reading the same st.session_state['last_df'].")
    else:
        st.warning("No shared market data yet. Connect Twelve/MT5 from the sidebar, then press Refresh if needed.")


def _safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _top_shared_connector():
    df = st.session_state.get("last_df")
    rows = len(df) if isinstance(df, pd.DataFrame) else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Symbol", st.session_state.get("symbol", "XAUUSD"))
    c2.metric("Timeframe", st.session_state.get("timeframe", "M1"))
    c3.metric("Shared Rows", f"{rows:,}")
    c4.metric("Current Source", st.session_state.get("source", "DISCONNECTED"))

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Use sidebar connection in Engine", use_container_width=True, key="engine_sync_sidebar_df"):
            sync_backtest_keys_from_last_df()
            st.success("Shared data synced into Engine / Prelive / Backtest.")
            _safe_rerun()
    with b2:
        if st.button("Clear Shared Data", use_container_width=True, key="combined_clear_shared"):
            for k in [
                "last_df", "connected", "source", "engine_shared_rows",
                "combined_original_backtest_raw_df",
                "combined_original_backtest_source",
                "combined_original_backtest_symbol",
                "combined_original_backtest_last_load",
            ]:
                st.session_state.pop(k, None)
            st.session_state.connected = False
            st.session_state.source = "DISCONNECTED"
            st.success("Shared data cleared.")
            _safe_rerun()

    ok, rows = shared_data_status()
    if ok:
        sync_backtest_keys_from_last_df()
        st.success(f"Shared data active: {rows:,} rows. Engine / Prelive / Backtest use the same loaded data.")
    else:
        st.info("No shared data yet. Use the global sidebar connector first.")

def _call_original_show(module_name):
    try:
        if module_name == "engine":
            from . import original_engine_inner as mod
        elif module_name == "prelive":
            from . import original_prelive_inner as mod
        else:
            from . import original_backtest_inner as mod

        if hasattr(mod, "show"):
            mod.show()
        else:
            st.error(f"{module_name} module has no show() function.")

    except Exception as exc:
        st.error(f"{module_name} inner tab crashed safely: {exc}")
        with st.expander("Debug error"):
            st.exception(exc)


def show():
    st.markdown("# ⚡ Engine workspace")
    st.caption("Fast mode: only the selected inner workspace renders. The duplicated Doo Prime Analysis inner tab was removed from Engine.")

    with st.expander("🔗 Open shared Engine connection/status controls", expanded=False):
        _top_shared_connector()

    ok, rows = shared_data_status()
    quick = st.columns(4)
    quick[0].metric("Shared Data", "ACTIVE" if ok else "NO DATA")
    quick[1].metric("Rows", f"{rows:,}")
    quick[2].metric("Source", st.session_state.get("source", "DISCONNECTED"))
    quick[3].metric("TF", st.session_state.get("timeframe", "M1"))

    workspace = st.radio(
        "Open Engine inner workspace",
        ["⚡ Decision Engine", "📡 Prelive", "🌐 Websocket Live", "🧪 Backtest Original"],
        horizontal=True,
        key="engine_lazy_workspace",
    )

    if workspace == "⚡ Decision Engine":
        _show_shared_market_status()
        _call_original_show("engine")
        return

    if workspace == "📡 Prelive":
        _show_shared_market_status()
        _call_original_show("prelive")
        return

    if workspace == "🌐 Websocket Live":
        st.markdown("### 🌐 Websocket Live Feed")
        st.info("Optional fast tick layer. If it fails, your original sidebar connectors still work.")
        try:
            from core.websocket_feed import render_websocket_panel, websocket_status
            render_websocket_panel(location="engine")
            ws = websocket_status()
            c = st.columns(4)
            c[0].metric("WS Enabled", str(ws.get("enabled")))
            c[1].metric("Runtime Live", str(ws.get("runtime_connected")))
            c[2].metric("Queued Ticks", ws.get("queued_ticks", 0))
            c[3].metric("Provider", ws.get("provider", "generic"))
        except Exception as exc:
            st.error(f"Websocket panel failed safely: {exc}")
            with st.expander("Debug error"):
                st.exception(exc)
        return

    sync_backtest_keys_from_last_df()
    _show_shared_market_status()
    _call_original_show("backtest")

