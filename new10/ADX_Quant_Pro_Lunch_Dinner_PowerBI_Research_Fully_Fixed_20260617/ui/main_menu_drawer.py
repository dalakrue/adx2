"""Stable main-page menu replacing native-sidebar dependency (2026-06-15).

The app can be fully navigated and controlled from this expander even if the
native Streamlit sidebar is closed, hidden, or unavailable.
"""
from __future__ import annotations

import time
import streamlit as st


def _safe_rerun() -> None:
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _soft_menu_css() -> None:
    st.markdown(
        """
<style id="new7-main-page-menu-antd-20260615">
.new7-card{
  border:1px solid rgba(99,102,241,.13);
  border-radius:20px;
  padding:11px 12px;
  margin:.20rem 0 .55rem 0;
  background:linear-gradient(135deg,rgba(255,255,255,.83),rgba(239,246,255,.68));
  box-shadow:0 10px 26px rgba(15,23,42,.055);
}
.new7-menu-note{font-size:.76rem;color:#64748b;line-height:1.28;}
@media(max-width:430px){
  .new7-card{border-radius:16px;padding:9px 10px;margin:.15rem 0 .42rem 0;box-shadow:0 6px 14px rgba(15,23,42,.045);} 
  div[data-testid="stExpander"] details{border-radius:16px!important;}
  div[data-testid="stButton"] button{min-height:38px!important;font-size:.78rem!important;padding:.18rem .35rem!important;}
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _sync_status() -> None:
    try:
        from ui.antd_navigation_20260615 import render_active_nav_status
        render_active_nav_status()
    except Exception:
        page = st.session_state.get("active_page", "Settings")
        sub = st.session_state.get("active_subpage", "")
        st.caption(f"Active page: {page} | Subpage: {sub or 'Main'}")


def _render_quick_actions() -> None:
    st.markdown("#### ⚡ Quick Controls")
    try:
        from ui.home_master_control_bar_20260615 import build_current_home_payload, run_home_calculation_gate
        from ui.copy_tools import central_copy_button
    except Exception:
        build_current_home_payload = None
        run_home_calculation_gate = None
        central_copy_button = None
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("▶ Run All", key="main_menu_run_calculation_20260615", use_container_width=True):
        if callable(run_home_calculation_gate):
            run_home_calculation_gate()
        else:
            st.session_state["metric_run_calculate"] = True
            st.session_state["research_run_calculate"] = True
            st.session_state["other_run_calculate"] = True
            st.session_state["ui_navigation_click_ts"] = time.time()
        _safe_rerun()
    if callable(build_current_home_payload) and callable(central_copy_button):
        with c2:
            central_copy_button("📋 Copy Short", build_current_home_payload(short=True), "main_menu_copy_short_real_20260615", show_fallback=True)
        with c3:
            central_copy_button("📋 Copy Full", build_current_home_payload(short=False), "main_menu_copy_full_real_20260615", show_fallback=True)
    else:
        short_payload = build_current_home_payload(short=True) if callable(build_current_home_payload) else "Copy engine unavailable."
        full_payload = build_current_home_payload(short=False) if callable(build_current_home_payload) else "Copy engine unavailable."
        with c2:
            st.download_button("⬇️ Copy Short fallback", short_payload, file_name="copy_short_fallback.txt", mime="text/plain", key="main_menu_copy_short_download_20260615", use_container_width=True)
        with c3:
            st.download_button("⬇️ Copy Full fallback", full_payload, file_name="copy_full_fallback.txt", mime="text/plain", key="main_menu_copy_full_download_20260615", use_container_width=True)
    if c4.button("🔄 Reset UI State", key="main_menu_reset_ui_state_20260615", use_container_width=True):
        for key, value in {
            "active_page": "Settings",
            "active_subpage": "",
            "tab_choice": "Settings",
            "home_inner_tab": "Lunch",
            "lunch_active_subpage": "",
            "dinner_active_subpage": "",
            "research_active_subpage": "",
            "new7_main_menu_drawer_open": False,
            "menu_open": False,
        }.items():
            st.session_state[key] = value
        st.session_state["ui_navigation_click_ts"] = time.time()
        _safe_rerun()


def _render_native_backup_controls() -> None:
    st.markdown("#### 🧱 Native Sidebar Backup")
    st.caption("Native Streamlit sidebar opens collapsed on first load. These controls change only app state; they do not use fragile DOM-click JavaScript.")
    try:
        from ui.sidebar_hard_lock import enable_native_sidebar_backup, disable_native_sidebar, native_sidebar_disabled
        disabled = native_sidebar_disabled()
        st.caption("Native backup status: " + ("RESTORED / AVAILABLE"))
        b1, b2, b3 = st.columns(3)
        if b1.button("🧭 Show Backup", key="main_menu_unlock_native_backup_nojs_20260615", use_container_width=True):
            enable_native_sidebar_backup()
            st.session_state["new7_native_sidebar_status_20260614"] = "Backup sidebar menu is available. Use Streamlit's sidebar arrow to open it."
            _safe_rerun()
        if b2.button("✅ Keep Visible", key="main_menu_keep_native_backup_20260617", use_container_width=True):
            enable_native_sidebar_backup()
            _safe_rerun()
        if b3.button("☰ Main Menu", key="main_menu_open_main_drawer_20260615", use_container_width=True):
            st.session_state["new7_main_menu_drawer_open"] = True
            st.session_state["menu_open"] = True
            st.session_state["ui_navigation_click_ts"] = time.time()
            st.info("Main Page Menu remains the reliable menu even if the native sidebar is closed.")
    except Exception as exc:
        st.caption(f"Native backup controls skipped safely: {exc}")


def render_main_menu_drawer(current_tab: str | None = None) -> str:
    """Liquid-glass app drawer.

    Hidden by default. Opens from the top ☰ button and replaces the bulky
    always-open controls above the page tabs. It is normal Streamlit UI, so no
    sidebar DOM hack is used and it cannot get stuck like the native sidebar.
    """
    _soft_menu_css()
    try:
        from ui.liquid_glass_theme_20260615 import apply_liquid_glass_theme
        apply_liquid_glass_theme()
    except Exception:
        pass
    pages = {"Settings", "Lunch", "Dinner", "Morning", "Research", "Other"}
    if current_tab and current_tab in pages:
        st.session_state.setdefault("active_page", current_tab)
    st.session_state.setdefault("active_page", st.session_state.get("tab_choice", "Settings"))
    st.session_state.setdefault("active_subpage", "")
    if not bool(st.session_state.get("new7_main_menu_drawer_open", False) or st.session_state.get("menu_open", False)):
        return st.session_state.get("active_page", st.session_state.get("tab_choice", "Settings"))

    st.markdown('<div class="new7-liquid-drawer">', unsafe_allow_html=True)
    top_a, top_b = st.columns([5, 1])
    with top_a:
        st.markdown('<div class="new7-liquid-drawer-title"><div><b>⋮ Liquid Glass App Drawer</b><br><span style="color:#64748b;font-size:.78rem;font-weight:750;">Three-dot app menu: navigation, connector, timer, copy, and UI controls are independent from the native Streamlit sidebar.</span></div></div>', unsafe_allow_html=True)
    with top_b:
        if st.button("✕ Close", key="liquid_close_app_drawer_20260615", use_container_width=True):
            st.session_state["new7_main_menu_drawer_open"] = False
            st.session_state["menu_open"] = False
            st.session_state["ui_navigation_click_ts"] = time.time()
            _safe_rerun()

    drawer_tabs = ["Menu", "Connector", "Timer", "Copy", "UI / Sidebar"]
    active = "Menu"
    try:
        from ui.stable_ui_libs_20260615 import tab_choice
        active = tab_choice("Drawer section", drawer_tabs, "liquid_drawer_active_tab_20260615", default="Menu")
    except Exception:
        active = st.radio("Drawer section", drawer_tabs, horizontal=True, key="liquid_drawer_active_radio_20260615")

    if active == "Menu":
        st.markdown('<div class="new7-liquid-section">', unsafe_allow_html=True)
        try:
            from ui.antd_navigation_20260615 import safe_antd_navigation
            safe_antd_navigation("antd_liquid_drawer_navigation")
        except Exception as exc:
            st.warning("streamlit-antd-components not installed; using safe fallback navigation.")
            st.caption(f"Navigation fallback reason: {exc}")
            page_list = ["Settings", "Lunch", "Dinner", "Morning", "Research", "Other"]
            current = st.session_state.get("active_page", "Settings")
            idx = page_list.index(current) if current in page_list else 0
            page = st.selectbox("Navigation", page_list, index=idx, key="hard_fallback_nav_liquid_20260615")
            st.session_state["active_page"] = page
            st.session_state["active_subpage"] = ""
            st.session_state["tab_choice"] = page
        _sync_status()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="new7-liquid-section">', unsafe_allow_html=True)
        _render_quick_actions()
        st.markdown('</div>', unsafe_allow_html=True)
    elif active == "Connector":
        st.markdown('<div class="new7-liquid-section">', unsafe_allow_html=True)
        try:
            from ui.sidebar_fallback_panel import _render_connector
            _render_connector()
        except Exception:
            try:
                from ui.sidebar_fallback_panel import render_sidebar_fallback_panel
                render_sidebar_fallback_panel(expanded=True)
            except Exception as exc:
                st.warning(f"Connector panel failed safely: {exc}")
        st.markdown('</div>', unsafe_allow_html=True)
    elif active == "Timer":
        st.markdown('<div class="new7-liquid-section">', unsafe_allow_html=True)
        try:
            from ui.sidebar_fallback_panel import _render_timer
            _render_timer()
        except Exception as exc:
            st.warning(f"Timer panel failed safely: {exc}")
        st.markdown('</div>', unsafe_allow_html=True)
    elif active == "Copy":
        st.markdown('<div class="new7-liquid-section">', unsafe_allow_html=True)
        _render_quick_actions()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="new7-liquid-section">', unsafe_allow_html=True)
        st.markdown("#### 🧊 App Shell / Sidebar")
        st.session_state["compact_liquid_app_shell_20260615"] = st.toggle(
            "Compact real-app shell: hide duplicate top status/command sections",
            value=bool(st.session_state.get("compact_liquid_app_shell_20260615", True)),
            key="compact_liquid_app_shell_toggle_20260615",
            help="Keeps only ⋮ Menu + Run All + Copy Short + Copy Full above tabs. Extra status panels stay inside this drawer.",
        )
        _render_native_backup_controls()
        try:
            from ui.sidebar_hard_lock import render_sidebar_policy_status
            render_sidebar_policy_status()
        except Exception:
            pass
        with st.expander("🧪 Open / Close — UI Health + Duplicate Check", expanded=False):
            try:
                from ui.ui_health_check import render_ui_health_check
                render_ui_health_check(compact=False)
            except Exception as exc:
                st.caption(f"UI health check skipped safely: {exc}")
        with st.expander("🏗️ Open / Close — Future Upgrade / Downgrade Architecture", expanded=False):
            try:
                from core.upgrade_architecture_20260615 import render_architecture_upgrade_panel
                render_architecture_upgrade_panel()
            except Exception as exc:
                st.caption(f"Architecture panel skipped safely: {exc}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    return st.session_state.get("active_page", st.session_state.get("tab_choice", "Settings"))
