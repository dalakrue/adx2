"""Stable synchronized navigation (restored 2026-06-17).

Home, Data Visualization and top-level AI Assistant are intentionally absent
from the visible menu. Their existing renderers remain reachable inside Lunch
and Research. Settings is the first startup page and Other restores the legacy
Engine/Train Data/Pre Original/Backtest/Profile workspace.
"""
from __future__ import annotations

import time
from typing import Dict, List, Tuple

import streamlit as st

try:
    import streamlit_antd_components as sac  # type: ignore
    SAC_AVAILABLE = True
except Exception:
    sac = None  # type: ignore
    SAC_AVAILABLE = False

PAGES: List[str] = ["Settings", "Lunch", "Dinner", "Morning", "Research", "Other"]
LUNCH_CHILDREN = ["Full Metric Details + History", "PowerBI Projection", "Priority + Decision + Reliability", "Finder"]
DINNER_CHILDREN = ["Regime + Combined Logic", "AI Assistant"]
RESEARCH_CHILDREN = ["Research AI Assistant", "KNN / Greedy", "Quant Structure"]
SUBPAGE_PARENT: Dict[str, str] = {
    **{x: "Lunch" for x in LUNCH_CHILDREN},
    "Regime + Combined Logic": "Dinner", "Unified Regime + Logic": "Dinner", "Regime Summary": "Dinner", "Combine Logic": "Dinner", "Combined Logic": "Dinner",
    "Research AI Assistant": "Research", "KNN / Greedy": "Research", "Quant Structure": "Research",
}


def _normalize_page(page: str | None) -> str:
    text = str(page or "Settings").strip()
    aliases = {"Home": "Lunch", "Data Visualization": "Lunch", "AI Assistant": "Research", "Metric": "Lunch", "Doo Prime": "Morning", "Regime": "Dinner"}
    text = aliases.get(text, text)
    return text if text in PAGES else "Settings"


def _init_nav_state() -> None:
    page = _normalize_page(st.session_state.get("active_page") or st.session_state.get("tab_choice") or "Settings")
    st.session_state.setdefault("active_subpage", "")
    st.session_state["active_page"] = page
    st.session_state["tab_choice"] = page
    st.session_state.setdefault("home_inner_tab", "Lunch")


def _sync_legacy_state(page: str, subpage: str = "") -> Tuple[str, str]:
    _init_nav_state()
    page = _normalize_page(page)
    subpage = str(subpage or "").strip()
    if subpage in SUBPAGE_PARENT:
        page = SUBPAGE_PARENT[subpage]
    # Duplicate AI labels are resolved from the already selected parent.
    if subpage == "AI Assistant" and page == "Research":
        subpage = "Research AI Assistant"
    elif subpage == "AI Assistant" and page != "Dinner":
        page = "Research"; subpage = "Research AI Assistant"
    valid = _nested_options_for_page(page)
    if subpage not in valid:
        subpage = DINNER_CHILDREN[0] if page == "Dinner" else ""
    st.session_state["active_page"] = page
    st.session_state["tab_choice"] = page
    st.session_state["active_subpage"] = subpage
    st.session_state["ui_navigation_click_ts"] = time.time()
    st.session_state["fast_tab_switch_active"] = True
    if page in {"Lunch", "Dinner", "Morning", "Research"}:
        st.session_state["home_inner_tab"] = page
    if page == "Lunch":
        st.session_state["lunch_active_subpage"] = subpage
    elif page == "Dinner":
        st.session_state["dinner_active_subpage"] = subpage
    elif page == "Research":
        st.session_state["research_active_subpage"] = subpage
    return page, subpage


def sync_active_page_to_legacy_state() -> Tuple[str, str]:
    return _sync_legacy_state(st.session_state.get("active_page", "Settings"), st.session_state.get("active_subpage", ""))


def _nested_options_for_page(page: str) -> List[str]:
    if page == "Lunch": return [""] + LUNCH_CHILDREN
    if page == "Dinner": return DINNER_CHILDREN
    if page == "Research": return [""] + RESEARCH_CHILDREN
    return [""]


def _render_synced_nested_selector(location_key: str) -> Tuple[str, str]:
    page = _normalize_page(st.session_state.get("active_page", "Settings"))
    options = _nested_options_for_page(page)
    if len(options) <= 1:
        return _sync_legacy_state(page, "")
    current = str(st.session_state.get("active_subpage", "") or "")
    if current not in options: current = ""
    labels = (["Main"] + [x for x in options if x]) if "" in options else list(options)
    current_label = current or ("Main" if "Main" in labels else labels[0])
    selected = st.selectbox("Inner tab", labels, index=labels.index(current_label), key=f"{location_key}_nested_20260617")
    return _sync_legacy_state(page, "" if selected == "Main" else selected)


def _render_fallback(location_key: str) -> Tuple[str, str]:
    current = _normalize_page(st.session_state.get("active_page", "Settings"))
    selected = st.selectbox("Navigation", PAGES, index=PAGES.index(current), key=f"{location_key}_page_20260617")
    _sync_legacy_state(selected, st.session_state.get("active_subpage", "") if selected == current else "")
    return _render_synced_nested_selector(location_key + "_fallback")


def _menu_items():
    return [
        sac.MenuItem("Settings", icon="gear"),
        sac.MenuItem("Lunch", icon="activity", children=[sac.MenuItem(x) for x in LUNCH_CHILDREN]),
        sac.MenuItem("Dinner", icon="moon", children=[sac.MenuItem(x) for x in DINNER_CHILDREN]),
        sac.MenuItem("Morning", icon="sun"),
        sac.MenuItem("Research", icon="search", children=[sac.MenuItem(x) for x in RESEARCH_CHILDREN]),
        sac.MenuItem("Other", icon="folder"),
    ]


def safe_antd_navigation(location_key: str = "antd_main_navigation") -> Tuple[str, str]:
    _init_nav_state()
    if not SAC_AVAILABLE:
        return _render_fallback(location_key)
    try:
        selected = sac.menu(_menu_items(), open_all=True, key=location_key)
    except Exception:
        return _render_fallback(location_key)
    selected = str(selected or "").strip()
    if selected in PAGES:
        return _sync_legacy_state(selected, DINNER_CHILDREN[0] if selected == "Dinner" else "")
    if selected == "AI Assistant":
        return _sync_legacy_state("Dinner", selected)
    if selected in SUBPAGE_PARENT:
        return _sync_legacy_state(SUBPAGE_PARENT[selected], selected)
    return sync_active_page_to_legacy_state()


def render_active_nav_status() -> None:
    page, sub = sync_active_page_to_legacy_state()
    st.caption(f"Active page: {page} | Inner tab: {sub or 'Main'}")
