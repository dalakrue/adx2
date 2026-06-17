"""Automatic cached Lunch restoration after the Settings Run Calculation button.

The user no longer has to press a second intermediate load or calculation button. This module reads and displays the caches produced by
``core.settings_run_orchestrator_20260617`` while preserving the project's
existing metric, regime, priority, PowerBI and export logic.
"""
from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import streamlit as st


def _lunch_active() -> bool:
    return str(st.session_state.get("active_page") or st.session_state.get("tab_choice") or "") == "Lunch"


def _safe_call(label: str, fn, *args, **kwargs) -> Any:
    if not callable(fn):
        return None
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        st.warning(f"{label} skipped safely; the rest of Lunch remains available.")
        with st.expander(f"Open / Close — {label} status", expanded=False):
            st.caption(f"{type(exc).__name__}: {exc}")
        return None


def _shared_status() -> Dict[str, Any]:
    try:
        from core.canonical_runtime_20260617 import shared_from_runtime
        return shared_from_runtime(st.session_state) or {}
    except Exception:
        return {}


def _cached_metric_result(ns: Dict[str, Any]) -> Dict[str, Any]:
    cached = st.session_state.get("lunch_metric_result_cache")
    if isinstance(cached, dict) and cached.get("ok"):
        return cached
    getter = ns.get("_get_cached_lunch_metric_result")
    result = _safe_call("Cached Lunch metric result", getter, False) if callable(getter) else {}
    return result if isinstance(result, dict) else {}


def _render_metric_summary(ns: Dict[str, Any], result: Dict[str, Any]) -> None:
    quality = ns.get("_render_lunch_metric_quality_table")
    if callable(quality):
        _safe_call("Original Lunch metric quality table", quality, result)

    scores = result.get("scores", {}) if isinstance(result.get("scores"), dict) else {}
    if scores:
        cols = st.columns(5)
        cols[0].metric("Master", f"{float(scores.get('Master /10', 0) or 0):.2f}/10", scores.get("Decision", "WAIT"))
        cols[1].metric("Entry", f"{float(scores.get('Entry /10', 0) or 0):.2f}/10")
        cols[2].metric("Direction", str(scores.get("Direction", "WAIT")))
        cols[3].metric("Hold", f"{float(scores.get('Hold /10', 0) or 0):.2f}/10")
        cols[4].metric("TP", f"{float(scores.get('TP /10', 0) or 0):.2f}/10")

    reverse = result.get("reverse10")
    st.markdown("#### 010 Reverse Decision Table")
    if isinstance(reverse, pd.DataFrame) and not reverse.empty:
        st.dataframe(reverse, use_container_width=True, hide_index=True, height=340)
    else:
        st.dataframe(pd.DataFrame([{"Status": "The current cached metric result has no reverse-decision rows."}]), use_container_width=True, hide_index=True)


def _render_full_details(ns: Dict[str, Any], result: Dict[str, Any]) -> None:
    with st.expander("Open / Close — Full Metric Details", expanded=False):
        detail = ns.get("_render_phone_safe_metric_details")
        if callable(detail):
            _safe_call("Full Metric Details", detail, result)
        else:
            tables = [(name, value) for name, value in result.items() if isinstance(value, pd.DataFrame) and not value.empty]
            for name, table in tables[:8]:
                st.markdown(f"##### {name.replace('_', ' ').title()}")
                st.dataframe(table.tail(250).iloc[::-1], use_container_width=True, hide_index=True, height=300)


def _render_full_history(ns: Dict[str, Any], result: Dict[str, Any]) -> None:
    with st.expander("Open / Close — Full Metric History", expanded=False):
        history = result.get("history")
        if isinstance(history, pd.DataFrame) and not history.empty:
            newest = ns.get("_lunch_newest_first_table_v20260609")
            show = newest(history, 250) if callable(newest) else history.tail(250).iloc[::-1]
            st.dataframe(show, use_container_width=True, hide_index=True, height=430)
        else:
            st.info("The current calculation result has no metric-history rows yet.")

        factor_history = result.get("history_by_factor", {})
        if isinstance(factor_history, dict) and factor_history:
            factor = st.selectbox("Reverse decision factor history", list(factor_history), key="restored_metric_history_factor_20260617")
            fdf = factor_history.get(factor)
            if isinstance(fdf, pd.DataFrame) and not fdf.empty:
                st.dataframe(fdf.tail(250).iloc[::-1], use_container_width=True, hide_index=True, height=360)

        regime_history = st.session_state.get("full_metric_regime_history_df")
        if not isinstance(regime_history, pd.DataFrame) or regime_history.empty:
            regime_history = st.session_state.get("major_regime_history_df")
        if isinstance(regime_history, pd.DataFrame) and not regime_history.empty:
            st.markdown("##### Major Regime History")
            st.dataframe(regime_history.tail(600).iloc[::-1], use_container_width=True, hide_index=True, height=360)


def _render_powerbi_auto() -> None:
    st.markdown("### 📊 Power BI Price Prediction Projection")
    try:
        from tabs.dinner_morning_data_patch_20260614 import _render_lunch_red_prediction_line
        _render_lunch_red_prediction_line()
    except Exception as exc:
        st.warning(f"PowerBI cached projection skipped safely: {exc}")


def _render_copy_export(ns: Dict[str, Any]) -> None:
    with st.expander("Open / Close — Original Lunch Copy and Export Controls", expanded=False):
        short_builder = ns.get("_build_short_necessary_copy_text")
        full_builder = ns.get("_build_lunch_all_copy_text")
        short_text = _safe_call("Original Lunch short-copy payload", short_builder) if callable(short_builder) else ""
        full_text = _safe_call("Original Lunch full-copy payload", full_builder) if callable(full_builder) else ""
        short_text = str(short_text or "No completed Lunch calculation is available yet.")
        full_text = str(full_text or short_text)
        try:
            from ui.copy_tools import central_copy_button
            c1, c2 = st.columns(2)
            with c1:
                central_copy_button("Copy Short", short_text, "restored_lunch_copy_short_20260617", show_fallback=True)
            with c2:
                central_copy_button("Copy All", full_text, "restored_lunch_copy_all_20260617", show_fallback=True)
        except Exception:
            st.text_area("Copy Short", short_text, height=150, key="restored_lunch_copy_short_fallback_20260617")
            st.text_area("Copy All", full_text, height=240, key="restored_lunch_copy_all_fallback_20260617")
        st.download_button(
            "Export Original Lunch Analysis",
            data=full_text.encode("utf-8", errors="replace"),
            file_name="original_lunch_analysis.txt",
            mime="text/plain",
            key="restored_lunch_export_20260617",
            use_container_width=True,
        )


def render_restored_lunch_bottom(ns: Dict[str, Any]) -> None:
    if not _lunch_active():
        return
    shared = _shared_status()
    result = _cached_metric_result(ns)

    st.divider()
    st.markdown("## Original Lunch Analysis — Auto Loaded")
    built_at = st.session_state.get("lunch_metric_result_built_at") or shared.get("built_at", "-")
    cols = st.columns(4)
    cols[0].metric("Calculation", "READY" if result.get("ok") else "CHECK DATA")
    cols[1].metric("Lunch Cache", "AUTO LOADED" if result.get("ok") else "NOT READY")
    cols[2].metric("PowerBI Cache", "READY" if st.session_state.get("lunch_bi_visual_ready") else "NOT READY")
    cols[3].metric("Built At", str(built_at))

    if not result.get("ok"):
        st.warning(result.get("message", "Run Calculation in Settings after connecting or loading EURUSD H1 data."))
    else:
        _render_metric_summary(ns, result)
        # Full Metric Details remain available once in the dedicated
        # Lunch → Full Metric Details + History view.  Keeping the same large
        # table here caused duplicate browser rendering and extra phone heat.
        _render_full_history(ns, result)

    _render_powerbi_auto()
    _render_copy_export(ns)
