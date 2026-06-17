"""Top Home control bar: real copy + run gate controls (2026-06-15).

Display/control layer only. It uses existing session_state caches and existing
builders; it does not add a new prediction engine or external API.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict

import pandas as pd
import streamlit as st


def _safe_text(obj: Any, rows: int = 80) -> Any:
    if isinstance(obj, pd.DataFrame):
        return obj.tail(rows).to_dict("records")
    if isinstance(obj, pd.Series):
        return obj.tail(rows).to_dict()
    if isinstance(obj, (pd.Timestamp,)):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _safe_text(v, rows=rows) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_safe_text(v, rows=rows) for v in list(obj)[-rows:]]
    try:
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
    except Exception:
        pass
    return obj


def _copy_button(label: str, text: str, key: str) -> None:
    try:
        from ui.copy_tools import central_copy_button
        central_copy_button(label, str(text or ""), key, show_fallback=True)
    except Exception:
        st.text_area(label, str(text or ""), height=180, key=key + "_fallback")


def _home_ns() -> Dict[str, Any]:
    try:
        import tabs.home as home
        return home.__dict__
    except Exception:
        return {}


def build_current_home_payload(short: bool = False) -> str:
    """Build a current copy payload without triggering heavy calculations.

    Compact copy is curated instead of truncating the beginning of the full
    export, so it keeps the most useful regime, decision, reliability, error,
    priority, NLP and latest-price values within a practical chat input size.
    """
    if short:
        snapshot: Dict[str, Any] = {}
        shared: Dict[str, Any] = {}
        merged = pd.DataFrame()
        try:
            from core.regime_sync_20260617 import canonical_regime_snapshot, merged_hourly_regime_nlp_priority
            raw = canonical_regime_snapshot(days=25)
            snapshot = {
                "major_regime": raw.get("regime"),
                "regime_direction": raw.get("regime_direction"),
                "synced_decision": raw.get("decision"),
                "regime_start": str(raw.get("regime_start")),
                "regime_end": raw.get("regime_end_display"),
                "regime_true_false": raw.get("regime_validation"),
                "reliability_pct": raw.get("reliability"),
                "data_quality_pct": raw.get("data_quality"),
                "exit_risk_pct": raw.get("exit_risk_pct"),
                "avg_prediction_error_pct": raw.get("avg_error_pct"),
                "error_samples": raw.get("error_samples"),
                "error_method": raw.get("error_method"),
                "regime_source": raw.get("source"),
                "decision_policy": raw.get("decision_policy"),
            }
            merged = merged_hourly_regime_nlp_priority(days=25)
        except Exception as exc:
            snapshot = {"status": f"canonical snapshot unavailable: {exc}"}
        try:
            from core.canonical_runtime_20260617 import shared_from_runtime
            result = shared_from_runtime(st.session_state)
            if isinstance(result, dict):
                shared = {
                    "built_at": result.get("built_at"),
                    "current": _safe_text(result.get("current", {}), rows=20),
                    "reliability": _safe_text(result.get("reliability_calibration", {}), rows=20),
                    "prediction_feedback": _safe_text(result.get("prediction_feedback", {}), rows=20),
                    "data_quality": _safe_text(result.get("data_quality", {}), rows=20),
                }
        except Exception:
            pass
        ohlc = st.session_state.get("last_df")
        if not isinstance(ohlc, pd.DataFrame) or ohlc.empty:
            ohlc = st.session_state.get("dv_pp_df")
        payload = {
            "header": {
                "export": "M1 ADX Quant Pro — Compact Important Data for ChatGPT",
                "size_policy": "curated essential fields; maximum 6500 characters",
                "built_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": st.session_state.get("symbol", "EURUSD"),
                "timeframe": st.session_state.get("timeframe", "H1"),
            },
            "canonical_snapshot": snapshot,
            "shared_calculation": shared,
            "best_priority_rows": _safe_text(merged.head(12), rows=12) if isinstance(merged, pd.DataFrame) else [],
            "latest_ohlc": _safe_text(ohlc, rows=12) if isinstance(ohlc, pd.DataFrame) else [],
        }
        # Keep the compact copy comfortably below a typical free-plan message
        # input while preserving the most decision-relevant fields.
        return json.dumps(payload, indent=2, ensure_ascii=False, default=str)[:6500]

    ns = _home_ns()
    base = ""
    try:
        cached = st.session_state.get("lunch_copy_payload_cache")
        if isinstance(cached, str) and cached.strip():
            base = cached
        elif bool(st.session_state.get("metric_run_calculate", False)):
            getter = ns.get("_get_cached_lunch_copy_payload")
            if callable(getter):
                base = getter(False) or ""
            else:
                builder = ns.get("_build_lunch_all_copy_text")
                if callable(builder):
                    base = builder() or ""
    except Exception as exc:
        base = f"Existing full copy builder skipped safely: {exc}"

    important_keys = [
        "symbol", "timeframe", "source", "last_connection_rows", "last_connection_message",
        "metric_run_calculate", "lunch_metric_result_built_at", "current_regime",
        "canonical_regime_snapshot_20260617", "synced_current_decision_20260617",
        "dv_pp_base_result", "dv_pp_regime_summary", "dv_pp_bt_summary", "dv_pp_predicted",
        "dv_pp_lightblue_path", "lunch_red_projection_fallback_20260615",
        "reliability_control_center_20260614", "regime_context_20260614",
        "three_center_priority_summary_20260614", "three_center_priority_sorted_20260614",
        "final_synced_research_merge_pack_20260612", "final_merged_intelligence_pack_20260612",
        "research_export_20260612", "lunch_prediction_export", "ny_london_overlap_hourly_summary_v6",
    ]
    snap = {k: _safe_text(st.session_state.get(k), rows=120) for k in important_keys if k in st.session_state}
    df = st.session_state.get("last_df")
    if not isinstance(df, pd.DataFrame) or df.empty:
        df = st.session_state.get("dv_pp_df")
    if isinstance(df, pd.DataFrame) and not df.empty:
        snap["current_ohlc_tail"] = _safe_text(df, rows=80)
    try:
        from core.regime_sync_20260617 import merged_hourly_regime_nlp_priority
        merged_full = merged_hourly_regime_nlp_priority(days=25)
        if isinstance(merged_full, pd.DataFrame) and not merged_full.empty:
            history_text = _safe_text(merged_full, rows=600)
            snap["regime_nlp_knn_greedy_25day"] = history_text
            snap["regime_nlp_knn_greedy_10day"] = history_text  # legacy export key mirror
    except Exception:
        pass
    header = {
        "export": "M1 ADX Quant Pro — Full Current Data",
        "built_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "short": False,
        "note": "Uses existing cached state; no new prediction engine.",
    }
    payload = json.dumps({"header": header, "current_state": snap}, indent=2, ensure_ascii=False, default=str)
    full = (str(base).rstrip() + "\n\n" if base else "") + payload
    return full[:30000]


def run_home_calculation_gate() -> None:
    """Enable all existing run-gated sections in low-RAM mode.

    This is a master gate only. It does not create a new prediction engine; each
    existing section still builds from its own cached logic when displayed.
    """
    now = time.time()
    for key in [
        "metric_run_calculate", "lunch_force_reversal_scan", "research_run_calculate",
        "other_run_calculate", "home_run_all_low_ram_requested_20260615",
        "lunch_run_all_requested_20260615", "dinner_run_all_requested_20260615",
        "morning_run_all_requested_20260615", "ai_run_all_requested_20260615",
        "dv_run_all_requested_20260615", "final_synced_run_requested_20260615",
    ]:
        st.session_state[key] = True
    # Tell existing Data Visualization wrappers that the user has intentionally
    # requested a run/load; heavy visual work still occurs in its original code.
    st.session_state["lunch_bi_visual_ready"] = True
    st.session_state["ui_navigation_click_ts"] = now
    st.session_state["run_all_last_click_20260615"] = now
    # Invalidate only signatures/copy caches so existing engines rebuild once.
    for key in [
        "lunch_metric_result_signature", "lunch_copy_payload_signature",
        "reliability_control_center_20260614", "regime_context_20260614",
        "powerbi_alpha_delta_points_20260615", "regime_alpha_delta_points_20260615",
    ]:
        try:
            st.session_state.pop(key, None)
        except Exception:
            pass


def _safe_rerun() -> None:
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _set_page(page: str) -> None:
    st.session_state["active_page"] = page
    st.session_state["tab_choice"] = page
    st.session_state["active_subpage"] = ""
    st.session_state["ui_navigation_click_ts"] = time.time()


def render_home_master_control_bar(current_tab: str | None = None) -> None:
    """One very small fixed menu button that never disappears while scrolling."""
    pages = ["Settings", "Lunch", "Dinner", "Morning", "Research", "Other"]
    active = str(current_tab or st.session_state.get("active_page") or "Settings")
    active = {"Home":"Lunch", "Data Visualization":"Lunch", "AI Assistant":"Research"}.get(active, active)
    if active not in pages:
        active = "Settings"
    st.session_state["active_page"] = active
    st.session_state["tab_choice"] = active
    st.markdown(
        """<style id="fixed-mini-menu-20260617">
        .st-key-sticky_menu_bar_20260617{position:fixed!important;right:.48rem!important;top:50%!important;transform:translateY(-50%)!important;z-index:100000!important;width:28px!important;height:28px!important;margin:0!important;padding:0!important;background:rgba(248,250,252,.90)!important;backdrop-filter:blur(16px)!important;border-radius:9px!important;border:1px solid rgba(59,130,246,.18)!important;box-shadow:0 7px 20px rgba(15,23,42,.14)!important;overflow:visible!important}
        .st-key-sticky_menu_bar_20260617>div{width:28px!important;height:28px!important;padding:0!important;margin:0!important;overflow:visible!important}
        .st-key-sticky_menu_bar_20260617 button{width:28px!important;height:28px!important;min-height:28px!important;padding:0!important;margin:0!important;font-size:.82rem!important;line-height:1!important;border-radius:9px!important}
        @media(max-width:780px){.st-key-sticky_menu_bar_20260617{right:.28rem!important;top:50%!important;transform:translateY(-50%)!important;width:32px!important;height:32px!important}.st-key-sticky_menu_bar_20260617 button{width:32px!important;height:32px!important;min-height:32px!important;font-size:.92rem!important}}
        </style>""", unsafe_allow_html=True)
    try:
        container = st.container(key="sticky_menu_bar_20260617")
    except TypeError:
        container = st.container()
    with container:
        try:
            from ui.liquid_menu_popup_20260615 import render_liquid_popup_menu_button
            render_liquid_popup_menu_button(active, key="sticky_liquid_menu_20260617")
        except Exception:
            if st.button("⋮", key="sticky_menu_fallback_20260617"):
                st.session_state["new7_main_menu_drawer_open"] = True
                st.session_state["menu_open"] = True
                _safe_rerun()

