"""Compact sticky-compatible Liquid menu and restored narrow sidebar (2026-06-17)."""
from __future__ import annotations

import time
from typing import Iterable

import streamlit as st

PAGES = ["Settings", "Lunch", "Morning", "Research", "Other"]
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
    text = {"Home":"Lunch", "Data Visualization":"Lunch", "AI Assistant":"Research", "Dinner":"Lunch", "Regime":"Lunch"}.get(text, text)
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
    .stApp{font-size:15px!important}
    .main .block-container{padding-left:.28rem!important;padding-right:.28rem!important;padding-top:.34rem!important}
    .stButton button,.stDownloadButton button{min-height:41px!important;font-size:.80rem!important;padding:.30rem .38rem!important}
    input,textarea,[data-baseweb="select"]>div{font-size:.90rem!important;min-height:42px!important}
    [data-testid="stMetric"]{min-height:76px!important;height:auto!important;padding:.44rem!important;min-width:0!important;overflow:visible!important}
    [data-testid="stMetricValue"]{font-size:clamp(1rem,5vw,1.26rem)!important;line-height:1.06!important;white-space:normal!important;overflow-wrap:anywhere!important}
    [data-testid="stMetricLabel"]{font-size:.74rem!important;white-space:normal!important;overflow-wrap:anywhere!important}
    [data-testid="stMetricDelta"]{font-size:.68rem!important}
    [data-testid="stDataFrame"]{font-size:.78rem!important}
    details summary{font-size:.80rem!important;min-height:38px!important}
    """ if phone else ""
    st.markdown(f"""
<style id="new7-liquid-column-menu-20260617">
.new7-liquid-pop-note{{margin:.12rem 0 .36rem;padding:6px 8px;border-radius:12px;background:rgba(239,246,255,.88);border:1px solid rgba(59,130,246,.13);font-size:.70rem;color:#475569}}
.new7-liquid-side-title{{margin:.1rem 0 .35rem;padding:8px 9px;border-radius:14px;background:rgba(255,255,255,.82);border:1px solid rgba(59,130,246,.13);font-weight:900}}
div[data-testid="stPopover"] button,section[data-testid="stSidebar"] button{{border-radius:11px!important;min-height:31px!important;font-weight:800!important;padding:.12rem .28rem!important;font-size:.72rem!important}}
div[data-testid="stPopoverBody"]{{width:clamp(124px,10vw,148px)!important;min-width:124px!important;max-width:148px!important;padding:.24rem!important;max-height:78vh!important;overflow-y:auto!important}}
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"]{{gap:.22rem!important}}
div[data-testid="stPopoverBody"] hr{{margin:.28rem 0!important}}
section[data-testid="stSidebar"] .block-container{{padding:.48rem .42rem .7rem!important}}
@media(max-width:780px){{div[data-testid="stPopoverBody"]{{width:128px!important;min-width:128px!important;max-width:128px!important;padding:.20rem!important}}div[data-testid="stPopoverBody"] button{{min-height:29px!important;font-size:.64rem!important;white-space:normal!important;line-height:1.05!important}}}}
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




# Settings is the only owner of the protected run_settings_calculation transaction.

# Shared canonical service compatibility: render_canonical_copy_export and the direct menu wrapper use services.canonical_exports.
def _render_copy_actions(location_key: str) -> None:
    """Direct menu copy buttons for the latest Lunch canonical generation."""
    try:
        from ui.canonical_copy_export_20260619 import render_direct_canonical_copy_buttons
        render_direct_canonical_copy_buttons(state=st.session_state, location=location_key, compact=True, include_full=True)
    except Exception as exc:
        st.caption(f"Copy controls unavailable: {str(exc)[:80]}")


def _render_refresh_status() -> None:
    result = st.session_state.get("last_refresh_result_20260621")
    if not isinstance(result, dict):
        return
    status = str(result.get("status") or "")
    message = str(result.get("message") or "")
    text = f"{status}: {message}"[:220]
    if status == "SUCCESS":
        st.success(text)
    elif status == "WARNING":
        st.warning(text)
    elif status:
        st.error(text)


def _render_runtime_actions(location_key: str) -> None:
    top_cols = st.columns(3)
    if top_cols[0].button("🔄 Refresh", key=f"{location_key}_refresh_data_20260621", use_container_width=True):
        from core.app.refresh import refresh_data
        refresh_data(st.session_state)
    with top_cols[1]:
        try:
            from ui.canonical_copy_export_20260619 import render_direct_canonical_copy_buttons
            render_direct_canonical_copy_buttons(state=st.session_state, location=f"{location_key}_short_inline", compact=True, include_full=False)
        except Exception as exc:
            st.caption(f"Short copy unavailable: {str(exc)[:60]}")
    with top_cols[2]:
        try:
            from ui.canonical_copy_export_20260619 import render_direct_canonical_copy_buttons
            # Render only Full here by building the two-button helper inside the copy tab below would duplicate Short.
            from core.canonical_runtime_20260617 import get_canonical
            from core.compact_canonical_20260619 import get_compact_summary
            from services.canonical_exports import all_text, generation_identity, payload_stats
            from ui.copy_tools import central_copy_button
            canonical = get_canonical(st.session_state)
            if canonical:
                summary = get_compact_summary(st.session_state)
                plan = st.session_state.get("position_sizing_plan_20260619") or {}
                readiness = st.session_state.get("system_readiness_snapshot_20260621") or {}
                payload = all_text(canonical, summary, plan, readiness)
                stats = payload_stats(payload)
                st.caption(f"Full: {stats.lines} lines")
                central_copy_button("Copy Full", payload, f"{location_key}_direct_full_inline_{generation_identity(canonical)[:16]}", height=70, show_fallback=False)
            else:
                st.caption("Copy Full after Run")
        except Exception as exc:
            st.caption(f"Full copy unavailable: {str(exc)[:60]}")
    st.caption("Run Calculation and Reduce RAM are intentionally hidden here. Use the one-click Settings calculation to publish and open Lunch.")
    _render_refresh_status()


if hasattr(st, "fragment"):
    _render_runtime_actions_isolated = st.fragment(_render_runtime_actions)
else:
    _render_runtime_actions_isolated = _render_runtime_actions


def render_liquid_popup_menu_button(current_page: str | None = None, *, key: str = "top_liquid_column_menu_20260615") -> str:
    inject_liquid_menu_css()
    current=_normalize_page(current_page)
    if hasattr(st,"popover"):
        with st.popover("⋮", use_container_width=False):
            render_column_menu_buttons(key)
            st.divider(); _render_ui_mode(key)
            _render_runtime_actions_isolated(key)
            st.divider()
            _render_copy_actions(key)
    else:
        with st.expander("⋮",expanded=False):
            render_column_menu_buttons(key); _render_ui_mode(key); _render_runtime_actions_isolated(key); _render_copy_actions(key)
    return _normalize_page(st.session_state.get("active_page",current))


def clear_large_display_caches() -> None:
    """Clear reconstructable presentation objects and preserve authoritative data."""
    prefixes = (
        "lunch_bi_visual_cache", "lunch_visualization_export", "lunch_red_chart_alpha",
        "history_search_result_", "ai_answer_cache_", "ai_retrieval_", "temporary_dataframe_",
        "canonical_copy_short_payload_", "canonical_copy_all_payload_", "presentation_cache_20260621",
    )
    protected_tokens = ("canonical_result", "canonical_calculation", "settled_evidence", "connector", "user_settings")
    for item in list(st.session_state.keys()):
        text = str(item)
        if any(token in text for token in protected_tokens):
            continue
        if text.startswith(prefixes):
            st.session_state.pop(item, None)
    try:
        from core.adaptive_presentation_cache_20260621 import clear_reconstructable
        clear_reconstructable(st.session_state)
    except Exception:
        pass
    # Close large field presentation gates while preserving the non-widget
    # preference keys and all completed calculation/history data.
    for index in range(1, 7):
        if not bool(st.session_state.get(f"lunch_field_open_{index}_20260621", False)):
            st.session_state.pop(f"lunch_field_widget_{index}_20260621", None)
    st.session_state["ui_navigation_click_ts"] = time.time()
    st.session_state["fast_tab_switch_active"] = True


def render_sidebar_liquid_menu_only(current_page: str | None = None) -> str:
    """Backward-compatible no-sidebar callable.

    Old imports now open the main-page menu state instead of creating a native
    Streamlit sidebar. No sidebar widget or collapsed control is rendered.
    """
    inject_liquid_menu_css()
    current = _normalize_page(current_page)
    st.session_state["new7_main_menu_drawer_open"] = True
    st.session_state["menu_open"] = True
    return _normalize_page(st.session_state.get("active_page", current))

# Compatibility note: connector status formerly used render_finnhub_status_compact;
# it now renders only inside the main-page drawer, never in st.sidebar.
