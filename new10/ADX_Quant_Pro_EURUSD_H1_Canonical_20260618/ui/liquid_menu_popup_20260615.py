"""Compact sticky-compatible Liquid menu and restored narrow sidebar (2026-06-17)."""
from __future__ import annotations

import time
from typing import Iterable

import streamlit as st

PAGES = ["Settings", "Lunch", "Dinner", "Morning", "Research", "Other"]
ICONS = {"Settings":"⚙️","Lunch":"🍱","Dinner":"🌙","Morning":"🌅","Research":"🎓","Other":"📂"}


def _safe_rerun() -> None:
    # Detach the canonical Research widget value from widget cleanup when an
    # early menu rerun happens before the Research radio is rendered.
    if "research_inner_tab" in st.session_state:
        st.session_state["research_inner_tab"] = st.session_state.get("research_inner_tab", "Data Analysis")
    try: st.rerun()
    except Exception:
        try: st.experimental_rerun()
        except Exception: pass


def _normalize_page(page: str | None) -> str:
    text = str(page or st.session_state.get("active_page") or "Settings")
    text = {"Home":"Lunch", "Data Visualization":"Lunch", "AI Assistant":"Research"}.get(text, text)
    return text if text in PAGES else "Settings"


def set_active_page(page: str, subpage: str = "", *, rerun: bool = True) -> None:
    page = _normalize_page(page)
    st.session_state["active_page"] = page
    st.session_state["tab_choice"] = page
    st.session_state["active_subpage"] = str(subpage or "")
    st.session_state["ui_navigation_click_ts"] = time.time()
    st.session_state["fast_tab_switch_active"] = True
    if page in {"Lunch","Dinner","Morning","Research"}: st.session_state["home_inner_tab"] = page
    if page == "Lunch": st.session_state["lunch_active_subpage"] = str(subpage or "")
    elif page == "Dinner": st.session_state["dinner_active_subpage"] = str(subpage or "")
    elif page == "Research": st.session_state["research_active_subpage"] = str(subpage or "")
    if rerun: _safe_rerun()


def inject_liquid_menu_css() -> None:
    phone = bool(st.session_state.get("phone_mode", False))
    phone_css = """
    .stApp{font-size:18px!important}
    .main .block-container{padding-left:.32rem!important;padding-right:.32rem!important;padding-top:.50rem!important}
    .stButton button,.stDownloadButton button{min-height:54px!important;font-size:1rem!important;padding:.48rem .58rem!important}
    input,textarea,[data-baseweb="select"]>div{font-size:17px!important;min-height:50px!important}
    [data-testid="stMetric"]{min-height:112px!important;padding:.72rem!important}
    [data-testid="stMetricValue"]{font-size:1.58rem!important;line-height:1.12!important}
    [data-testid="stMetricLabel"]{font-size:.92rem!important}
    [data-testid="stMetricDelta"]{font-size:.82rem!important}
    [data-testid="stDataFrame"]{font-size:.92rem!important}
    details summary{font-size:1rem!important;min-height:48px!important}
    """ if phone else ""
    st.markdown(f"""
<style id="new7-liquid-column-menu-20260617">
.new7-liquid-pop-note{{margin:.12rem 0 .36rem;padding:6px 8px;border-radius:12px;background:rgba(239,246,255,.88);border:1px solid rgba(59,130,246,.13);font-size:.70rem;color:#475569}}
.new7-liquid-side-title{{margin:.1rem 0 .35rem;padding:8px 9px;border-radius:14px;background:rgba(255,255,255,.82);border:1px solid rgba(59,130,246,.13);font-weight:900}}
div[data-testid="stPopover"] button,section[data-testid="stSidebar"] button{{border-radius:13px!important;min-height:36px!important;font-weight:800!important;padding:.18rem .38rem!important;font-size:.77rem!important}}
section[data-testid="stSidebar"] .block-container{{padding:.48rem .42rem .7rem!important}}
{phone_css}
</style>
""", unsafe_allow_html=True)


def _render_ui_mode(location_key: str) -> None:
    st.markdown("##### Display size")
    c1,c2=st.columns(2)
    phone=bool(st.session_state.get("phone_mode",False))
    if c1.button("📱 Phone" + (" ✓" if phone else ""), key=f"{location_key}_phone", use_container_width=True):
        st.session_state["phone_mode"] = True
        st.session_state["uiux_density"] = "phone-large"
        _safe_rerun()
    if c2.button("🖥 Laptop" + (" ✓" if not phone else ""), key=f"{location_key}_laptop", use_container_width=True):
        st.session_state["phone_mode"] = False
        st.session_state["uiux_density"] = "wide"
        _safe_rerun()


def render_column_menu_buttons(location_key: str, pages: Iterable[str] = PAGES) -> str:
    inject_liquid_menu_css()
    current = _normalize_page(st.session_state.get("active_page"))
    for i,page in enumerate(pages):
        page=_normalize_page(page)
        if st.button(f"{ICONS.get(page,'•')} {page}{' ✓' if current==page else ''}", key=f"{location_key}_{i}_{page}", use_container_width=True):
            set_active_page(page)
    return _normalize_page(st.session_state.get("active_page",current))



def _render_copy_actions(location_key: str) -> None:
    """Keep copy controls inside the menu; never outside the floating button."""
    try:
        from ui.home_master_control_bar_20260615 import build_current_home_payload
        from ui.copy_tools import central_copy_button
        c1, c2 = st.columns(2)
        with c1:
            central_copy_button("📋 Short", build_current_home_payload(short=True), f"{location_key}_copy_short", show_fallback=True)
        with c2:
            central_copy_button("📋 Full", build_current_home_payload(short=False), f"{location_key}_copy_full", show_fallback=True)
    except Exception as exc:
        st.caption(f"Copy controls unavailable: {str(exc)[:80]}")

def render_liquid_popup_menu_button(current_page: str | None = None, *, key: str = "top_liquid_column_menu_20260615") -> str:
    inject_liquid_menu_css()
    current=_normalize_page(current_page)
    if hasattr(st,"popover"):
        with st.popover("⋮", use_container_width=False):
            render_column_menu_buttons(key)
            st.divider(); _render_ui_mode(key)
            try:
                from ui.sidebar_hard_lock import soft_sidebar_hidden, hide_native_sidebar, show_native_sidebar
                if st.button("☰ Open Sidebar" if soft_sidebar_hidden() else "✕ Close Sidebar", key=f"{key}_sidebar_toggle", use_container_width=True):
                    show_native_sidebar() if soft_sidebar_hidden() else hide_native_sidebar()
                    _safe_rerun()
            except Exception:
                pass
            c1,c2=st.columns(2)
            if c1.button("▶ Run",key=f"{key}_run",use_container_width=True):
                try:
                    from ui.home_master_control_bar_20260615 import run_home_calculation_gate
                    run_home_calculation_gate()
                except Exception:
                    st.session_state["metric_run_calculate"]=True
                _safe_rerun()
            if c2.button("🧹 RAM",key=f"{key}_ram",use_container_width=True):
                clear_large_display_caches(); _safe_rerun()
            _render_copy_actions(key)
    else:
        with st.expander("⋮",expanded=False):
            render_column_menu_buttons(key); _render_ui_mode(key); _render_copy_actions(key)
    return _normalize_page(st.session_state.get("active_page",current))


def clear_large_display_caches() -> None:
    for key in ["home_reversal_25d_scan","lunch_bi_visual_cache","lunch_visualization_export","dv_pp_projection_history","dv_pp_bt_hist","lunch_red_chart_alpha_20260615","research_export_20260612"]:
        st.session_state.pop(key,None)
    st.session_state["ui_navigation_click_ts"]=time.time(); st.session_state["fast_tab_switch_active"]=True


def render_sidebar_liquid_menu_only(current_page: str | None = None) -> str:
    inject_liquid_menu_css(); current=_normalize_page(current_page)
    with st.sidebar:
        st.markdown('<div class="new7-liquid-side-title">⋮ Menu</div>',unsafe_allow_html=True)
        try:
            from ui.sidebar_hard_lock import hide_native_sidebar
            if st.button("✕ Close Sidebar", key="sidebar_close_compact_20260617", use_container_width=True):
                hide_native_sidebar(); _safe_rerun()
        except Exception:
            pass
        render_column_menu_buttons("sidebar_liquid_20260617")
        with st.expander("Finnhub API Connector", expanded=False):
            try:
                from core.finnhub_connector import render_finnhub_status_compact
                render_finnhub_status_compact(location="sidebar")
            except Exception as exc:
                st.warning(f"Finnhub connector unavailable: {str(exc)[:120]}")
        with st.expander("Display / actions",expanded=False):
            _render_ui_mode("sidebar_liquid_20260617")
            if st.button("▶ Run All",key="sidebar_run_all_20260617",use_container_width=True):
                try:
                    from ui.home_master_control_bar_20260615 import run_home_calculation_gate
                    run_home_calculation_gate()
                except Exception: st.session_state["metric_run_calculate"]=True
                _safe_rerun()
            _render_copy_actions("sidebar_liquid_20260617")
    return _normalize_page(st.session_state.get("active_page",current))
