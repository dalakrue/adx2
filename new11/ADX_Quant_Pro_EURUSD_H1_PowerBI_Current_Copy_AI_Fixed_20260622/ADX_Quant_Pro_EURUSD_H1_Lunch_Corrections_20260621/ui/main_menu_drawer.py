"""Stable main-page menu replacing native-sidebar dependency (2026-06-15).

The app is fully navigated and controlled from this main-page drawer.
The native Streamlit sidebar is permanently removed.
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
.new7-liquid-drawer{max-width:min(360px,92vw);margin-left:auto;border:1px solid rgba(99,102,241,.13);border-radius:18px;padding:.5rem;background:rgba(255,255,255,.92);}
@media(max-width:430px){
  .new7-card{border-radius:16px;padding:9px 10px;margin:.15rem 0 .42rem 0;box-shadow:none;}
  .new7-liquid-drawer{max-width:min(310px,88vw);padding:.35rem;border-radius:14px;} 
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


def _open_lunch_after_calculation() -> None:
    st.session_state.update({
        "active_page": "Lunch",
        "tab_choice": "Lunch",
        "active_subpage": "",
        "lunch_active_subpage": "",
        "lunch_bi_visual_ready": True,
        "show_restored_powerbi_20260617": True,
        "load_original_powerbi_from_antd_lunch_20260615": True,
        "settings_auto_open_lunch_20260617": True,
        "lunch_calculation_completed_notice_20260621": True,
    })


def _render_quick_actions() -> None:
    """Menu-only refresh plus exactly two real clipboard controls.

    Controls are deliberately stacked. The app drawer is narrow on phones, and
    three tiny columns caused Copy Short / Copy Full to wrap into unreadable text.
    """
    st.markdown("#### ⚡ Quick Controls")
    if st.button("🔄 Refresh Data Only", key="main_menu_refresh_data_20260621", use_container_width=True):
        try:
            from core.app.refresh import refresh_data
            result = refresh_data(st.session_state)
            if result.get("status") == "SUCCESS":
                st.success(str(result.get("message") or "Data refreshed. Run the one Settings calculation to publish the new generation."))
            elif result.get("status") == "WARNING":
                st.warning(str(result.get("message") or "Data refreshed with warnings."))
            else:
                st.error(str(result.get("message") or "Data refresh failed."))
        except Exception as exc:
            st.error(f"Refresh failed safely: {exc}")

    try:
        from ui.canonical_copy_export_20260619 import render_direct_canonical_copy_buttons
        render_direct_canonical_copy_buttons(
            state=st.session_state,
            location="main_drawer_short",
            compact=True,
            include_full=False,
        )
    except Exception as exc:
        st.button("📋 Copy Short", key="main_drawer_short_error_20260622", disabled=True, use_container_width=True)
        st.caption(f"Short copy unavailable: {str(exc)[:60]}")

    try:
        from core.canonical_runtime_20260617 import get_canonical
        from core.compact_canonical_20260619 import get_compact_summary
        from services.canonical_exports import all_text, generation_identity, payload_stats
        from ui.copy_tools import central_copy_button
        canonical = get_canonical(st.session_state)
        if canonical:
            payload = all_text(
                canonical,
                get_compact_summary(st.session_state),
                st.session_state.get("position_sizing_plan_20260619") or {},
                st.session_state.get("system_readiness_snapshot_20260621") or {},
            )
            stats = payload_stats(payload)
            st.caption(f"Full: {stats.lines} lines · ~{stats.estimated_tokens:,} tokens")
            central_copy_button("Copy Full", payload, f"main_drawer_direct_full_{generation_identity(canonical)[:16]}", height=86, show_fallback=False)
        else:
            st.button("📋 Copy Full", key="main_drawer_full_unavailable_20260622", disabled=True, use_container_width=True)
            st.caption("Copy Full activates after the Settings calculation publishes a completed generation.")
    except Exception as exc:
        st.button("📋 Copy Full", key="main_drawer_full_error_20260622", disabled=True, use_container_width=True)
        st.caption(f"Full copy unavailable: {str(exc)[:60]}")
    st.caption("Run Calculation and Reduce RAM stay in Settings. Copy buttons use the current published Lunch generation and are ready for paste into other apps.")


def render_main_menu_drawer(current_tab: str | None = None) -> str:
    """Liquid-glass app drawer.

    Hidden by default. Opens from the top ☰ button and replaces the bulky
    always-open controls above the page tabs. It is normal Streamlit UI, so no
    no native sidebar is used; the drawer is ordinary main-page Streamlit UI.
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
        st.markdown('<div class="new7-liquid-drawer-title"><div><b>⋮ Liquid Glass App Drawer</b><br><span style="color:#64748b;font-size:.78rem;font-weight:750;">Three-dot app menu: navigation, connector, timer, copy, and UI controls in one main-page drawer.</span></div></div>', unsafe_allow_html=True)
    with top_b:
        if st.button("✕ Close", key="liquid_close_app_drawer_20260615", use_container_width=True):
            st.session_state["new7_main_menu_drawer_open"] = False
            st.session_state["menu_open"] = False
            st.session_state["ui_navigation_click_ts"] = time.time()
            _safe_rerun()

    drawer_tabs = ["Menu", "Connector", "Timer", "Copy", "UI"]
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
            from ui.sidebar_fallback_panel import _render_connector_status_only
            _render_connector_status_only()
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
        st.markdown("#### 🧊 App Shell / UI")
        st.session_state["compact_liquid_app_shell_20260615"] = st.toggle(
            "Compact real-app shell: hide duplicate top status/command sections",
            value=bool(st.session_state.get("compact_liquid_app_shell_20260615", True)),
            key="compact_liquid_app_shell_toggle_20260615",
            help="Keeps only ⋮ Menu + Run All + Copy Short + Copy Full above tabs. Extra status panels stay inside this drawer.",
        )
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
