"""Responsive sidebar policy for the single new7 navigation system.

The native sidebar is a compact backup/drawer.  It can be fully hidden with a
session-state button and reopened from the sticky three-dot menu; no API keys or
calculation state are touched by navigation changes.
"""
from __future__ import annotations

import time
import streamlit as st

NATIVE_SIDEBAR_DISABLED_KEY = "new7_native_sidebar_disabled_20260614"
NATIVE_SIDEBAR_STATUS_KEY = "new7_native_sidebar_status_20260614"
MAIN_DRAWER_KEY = "new7_main_menu_drawer_open"
LEGACY_DRAWER_KEY = "menu_open"
SOFT_HIDDEN_KEY = "new7_native_sidebar_soft_hidden_20260617"


def init_sidebar_policy() -> None:
    st.session_state.setdefault(NATIVE_SIDEBAR_DISABLED_KEY, False)
    st.session_state.setdefault(SOFT_HIDDEN_KEY, False)
    st.session_state.setdefault(NATIVE_SIDEBAR_STATUS_KEY, "Compact sidebar is available and may be closed or reopened from the menu.")
    st.session_state.setdefault(MAIN_DRAWER_KEY, False)
    st.session_state.setdefault(LEGACY_DRAWER_KEY, False)
    for key in ("sidebar_force_hidden_20260614", "sidebar_close_requested_20260614", "sidebar_close_requested_native_only"):
        st.session_state[key] = False


def native_sidebar_disabled() -> bool:
    init_sidebar_policy()
    return bool(st.session_state.get(NATIVE_SIDEBAR_DISABLED_KEY, False))


def soft_sidebar_hidden() -> bool:
    init_sidebar_policy()
    return bool(st.session_state.get(SOFT_HIDDEN_KEY, False))


def hide_native_sidebar() -> None:
    init_sidebar_policy()
    st.session_state[SOFT_HIDDEN_KEY] = True
    st.session_state[NATIVE_SIDEBAR_STATUS_KEY] = "Sidebar closed. Reopen it from the sticky three-dot menu."
    st.session_state["ui_navigation_click_ts"] = time.time()


def show_native_sidebar() -> None:
    init_sidebar_policy()
    st.session_state[SOFT_HIDDEN_KEY] = False
    st.session_state[NATIVE_SIDEBAR_STATUS_KEY] = "Compact sidebar open."
    st.session_state["ui_navigation_click_ts"] = time.time()


def disable_native_sidebar(reason: str = "Sidebar remains restored and available.") -> None:
    """Backward-compatible close operation; it never deletes navigation."""
    hide_native_sidebar()


def enable_native_sidebar_backup() -> None:
    show_native_sidebar()


def open_main_drawer() -> None:
    st.session_state[MAIN_DRAWER_KEY] = True
    st.session_state[LEGACY_DRAWER_KEY] = True
    st.session_state["ui_navigation_click_ts"] = time.time()


def close_main_drawer() -> None:
    st.session_state[MAIN_DRAWER_KEY] = False
    st.session_state[LEGACY_DRAWER_KEY] = False
    st.session_state["ui_navigation_click_ts"] = time.time()


def inject_sidebar_policy_css() -> None:
    """Apply a 180–220 px desktop width and a zero-width closed phone drawer."""
    init_sidebar_policy()
    hidden_css = """
section[data-testid="stSidebar"]{display:none!important;width:0!important;min-width:0!important;max-width:0!important;}
[data-testid="stSidebarCollapsedControl"]{display:none!important;}
[data-testid="stAppViewContainer"]>.main{margin-left:0!important;max-width:100%!important;}
""" if soft_sidebar_hidden() else ""
    st.markdown(
        f"""
<style id="new7-native-sidebar-responsive-20260617">
section[data-testid="stSidebar"]{{
  width:clamp(11.25rem,13vw,13.75rem)!important;
  min-width:clamp(11.25rem,13vw,13.75rem)!important;
  max-width:13.75rem!important;
  border-right:1px solid rgba(15,23,42,.06)!important;
  box-shadow:10px 0 28px rgba(15,23,42,.055)!important;
  background:linear-gradient(180deg,rgba(248,250,252,.98),rgba(239,246,255,.95))!important;
  overflow-x:hidden!important;
}}
section[data-testid="stSidebar"] .block-container{{padding:.48rem .42rem .75rem!important;max-width:100%!important;overflow-x:hidden!important;}}
section[data-testid="stSidebar"] button{{border-radius:13px!important;min-height:36px!important;white-space:normal!important;overflow-wrap:anywhere!important;line-height:1.15!important;}}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span{{overflow-wrap:anywhere!important;word-break:normal!important;}}
section[data-testid="stSidebar"] input{{min-width:0!important;width:100%!important;}}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details{{
  border-radius:15px!important;border:1px solid rgba(99,102,241,.12)!important;
  background:rgba(255,255,255,.66)!important;overflow:hidden!important;
}}
@media(max-width:780px){{
  section[data-testid="stSidebar"]{{width:min(78vw,13.5rem)!important;min-width:min(78vw,13.5rem)!important;max-width:78vw!important;position:fixed!important;z-index:99990!important;}}
  section[data-testid="stSidebar"] button{{min-height:42px!important;font-size:.82rem!important;padding:.22rem .34rem!important;}}
  body,html,.stApp{{max-width:100vw!important;overflow-x:hidden!important;}}
  .main .block-container{{max-width:100vw!important;overflow-x:hidden!important;}}
}}
{hidden_css}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_policy_status() -> None:
    init_sidebar_policy()
    inject_sidebar_policy_css()
    st.markdown(
        f"""
<div class="new7-card"><b>🧱 Sidebar Status</b><br>
<span style="color:#64748b;font-size:.78rem;line-height:1.30;">Native sidebar: <b>{'CLOSED' if soft_sidebar_hidden() else 'OPEN / COMPACT'}</b><br>
Primary navigation state remains synchronized.</span></div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Open compact sidebar", key="sidebar_policy_open_20260617", use_container_width=True):
        show_native_sidebar(); st.rerun()
    st.caption(st.session_state.get(NATIVE_SIDEBAR_STATUS_KEY, "Sidebar ready."))
