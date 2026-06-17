"""Final synchronized page router (updated 2026-06-17).

Only the selected top-level page and selected inner page are imported/rendered.
All renderers consume the canonical runtime adapter already created by runner.py;
none of them may trigger a second shared calculation during the same rerun.
"""
from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
import streamlit as st


def _safe_rerun() -> None:
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _sync_shared(force: bool = False) -> dict:
    """Compatibility name: read the already-published adapter, never rebuild it."""
    del force
    try:
        from core.canonical_runtime_20260617 import shared_from_runtime
        return shared_from_runtime(st.session_state)
    except Exception:
        value = st.session_state.get("adx_shared_calc_result_20260615") or st.session_state.get("shared_calc_result")
        return value if isinstance(value, dict) else {}


def _safe_component(label: str, fn, *args, **kwargs):
    try:
        if callable(fn):
            return fn(*args, **kwargs)
        st.dataframe(pd.DataFrame([{"Component": label, "Status": "Renderer unavailable"}]), use_container_width=True, hide_index=True)
    except Exception as exc:
        st.warning(f"{label} skipped safely; remaining components are still available.")
        with st.expander(f"Open / Close — {label} error", expanded=False):
            st.code(str(exc))
    return None


def _home_ns() -> dict:
    try:
        import tabs.home as home
        return home.__dict__
    except Exception:
        return {}


def _prev_data(ns: dict):
    return ns.get("_render_lunch_data_visualization_inner_tab")


def _prev_morning(ns: dict):
    return ns.get("_render_doo_prime_inner_tab")


def _canonical_priority_table() -> pd.DataFrame:
    table = st.session_state.get("canonical_priority_table_20260617")
    if isinstance(table, pd.DataFrame) and not table.empty:
        return table
    try:
        from core.canonical_runtime_20260617 import get_canonical
        canonical = get_canonical(st.session_state)
        records = canonical.get("priority_table") if isinstance(canonical, dict) else None
        if isinstance(records, list) and records:
            return pd.DataFrame.from_records(records)
    except Exception:
        pass
    return pd.DataFrame()


def _display_priority_table(table: pd.DataFrame, *, height: int = 440) -> None:
    if table.empty:
        st.dataframe(pd.DataFrame([{"Status": "Run Calculation in Settings first"}]), use_container_width=True, hide_index=True)
        return
    sort_cols = [c for c in ("priority rank", "KNN Priority", "Greedy Priority") if c in table.columns]
    show = table.sort_values(sort_cols, ascending=True, kind="stable") if sort_cols else table
    phone = bool(st.session_state.get("phone_mode", False))
    display_rows = 168 if phone else 360
    st.dataframe(show.tail(display_rows), use_container_width=True, hide_index=True, height=height)


def _render_lunch(ns: dict, subpage: str) -> None:
    if not subpage:
        from tabs.final_lunch_upgrade_20260617 import render_lunch_quick_decision
        # Quick Decision already contains the authoritative 25-day synchronized
        # table. Do not render the same full metric/history table a second time.
        _safe_component("Lunch Quick Synced Decision", render_lunch_quick_decision)
        try:
            from ui.lunch_restored import render_restored_lunch_bottom
            render_restored_lunch_bottom(ns)
        except Exception as exc:
            st.warning(f"Restored original Lunch area skipped safely: {exc}")
        return

    st.markdown(f"### 🍱 Lunch — {subpage}")
    if subpage == "Full Metric Details + History":
        from tabs.final_three_center_upgrade_20260614 import _render_metric_detail_section
        _safe_component("Full Metric Details + History", _render_metric_detail_section, ns)
    elif subpage == "PowerBI Projection":
        from tabs.dinner_morning_data_patch_20260614 import _render_lunch_red_prediction_line, _render_powerbi_regime_projection
        _safe_component("PowerBI Regime Projection", _render_powerbi_regime_projection, ns)
        _safe_component("PowerBI Price Projection", _render_lunch_red_prediction_line)
        try:
            from ui.decision_product_panel_20260617 import render_powerbi_canonical_details
            render_powerbi_canonical_details()
        except Exception as exc:
            st.caption(f"Validated projection details skipped safely: {exc}")
        with st.expander("Open / Close — Full Original PowerBI Projection", expanded=False):
            if st.button("▶ Load Full Original Projection", key="load_full_powerbi_20260617", use_container_width=True):
                st.session_state["load_original_powerbi_from_antd_lunch_20260615"] = True
            if st.session_state.get("load_original_powerbi_from_antd_lunch_20260615"):
                _safe_component("Original PowerBI Projection", _prev_data(ns))
    elif subpage == "Priority + Decision + Reliability":
        from tabs.dinner_morning_data_patch_20260614 import _render_priority_decision_reliability
        _safe_component("Priority + Decision + Reliability", _render_priority_decision_reliability, ns)
        renderer = ns.get("render_reliability_control_center_20260614")
        if callable(renderer):
            _safe_component("Reliability Control Center", renderer)
    elif subpage == "Finder":
        finder = _canonical_priority_table()
        if not finder.empty:
            f1, f2 = st.columns(2)
            time_col = "Time" if "Time" in finder.columns else ("candle time" if "candle time" in finder.columns else None)
            hour_col = "Hour" if "Hour" in finder.columns else ("hour" if "hour" in finder.columns else None)
            dates = sorted(pd.to_datetime(finder[time_col], errors="coerce", utc=True).dropna().dt.date.unique().tolist()) if time_col else []
            selected_date = f1.selectbox("Finder day", dates, index=max(0, len(dates) - 1), key="finder_day_20260617") if dates else None
            hours = sorted(finder[hour_col].dropna().astype(str).unique().tolist()) if hour_col else []
            selected_hour = f2.selectbox("Finder hour", ["All"] + hours, key="finder_hour_20260617")
            mask = pd.Series(True, index=finder.index)
            if selected_date is not None and time_col:
                mask &= pd.to_datetime(finder[time_col], errors="coerce", utc=True).dt.date == selected_date
            if selected_hour != "All" and hour_col:
                mask &= finder[hour_col].astype(str) == selected_hour
            _display_priority_table(finder.loc[mask], height=440)
        else:
            _display_priority_table(finder)
    else:
        from tabs.final_lunch_upgrade_20260617 import render_lunch_quick_decision
        _safe_component("Lunch Quick Synced Decision", render_lunch_quick_decision)

    try:
        from tabs.final_lunch_upgrade_20260617 import render_lunch_25day_backtest_expander
        render_lunch_25day_backtest_expander(key_suffix=str(subpage))
    except Exception as exc:
        st.caption(f"25-day Lunch Regime + NLP history table skipped safely: {exc}")


def _render_dinner(ns: dict, subpage: str) -> None:
    prev = _prev_data(ns)
    if subpage == "AI Assistant":
        st.markdown("### 🌙 Dinner — AI Assistant")
        from tabs.dinner_morning_data_patch_20260614 import _render_chatgpt_style_ai
        _safe_component("Dinner AI Assistant", _render_chatgpt_style_ai)
        return

    # The former Regime Summary and Combine Logic inner pages are now one
    # authoritative section. Legacy subpage names route here for compatibility.
    from tabs.dinner_unified_center_20260617 import render_dinner_unified_center
    from ui.decision_product_panel_20260617 import render_regime_lifecycle_panel
    _safe_component(
        "Unified Regime + Combined Intelligence",
        render_dinner_unified_center,
        ns,
        prev,
        render_regime_lifecycle_panel,
    )


def _render_morning(ns: dict) -> None:
    st.markdown("### 🌅 Morning — Doo Prime")
    _safe_component("Morning / Doo Prime", _prev_morning(ns))


def _render_research(subpage: str) -> None:
    st.markdown("### 🎓 Research")
    if subpage == "AI Assistant":
        try:
            from tabs.ai_assistant_lite import render_ai_assistant_lite_tab
            _safe_component("AI Assistant", render_ai_assistant_lite_tab)
        except Exception as exc:
            st.warning(f"AI Assistant skipped safely: {exc}")
        return
    if subpage == "KNN / Greedy":
        _display_priority_table(_canonical_priority_table(), height=430)
        return
    if subpage == "Quant Structure":
        pack = st.session_state.get("final_synced_research_merge_pack_20260612") or st.session_state.get("final_merged_intelligence_pack_20260612") or {}
        quant = pack.get("quant_structure", {}) if isinstance(pack, dict) else {}
        if isinstance(quant, dict):
            st.dataframe(pd.DataFrame([{"Metric": k, "Value": str(v)} for k, v in quant.items()]), use_container_width=True, hide_index=True)
        elif isinstance(quant, pd.DataFrame):
            st.dataframe(quant, use_container_width=True, hide_index=True)
        else:
            st.dataframe(pd.DataFrame([{"Status": "Run synchronized intelligence first"}]), use_container_width=True, hide_index=True)
        return
    try:
        import tabs.research as research
        _safe_component("Research", research.show)
    except Exception as exc:
        st.warning(f"Research skipped safely: {exc}")


def _render_other() -> None:
    try:
        import tabs.other as other
        _safe_component("Other", other.show)
    except Exception as exc:
        st.warning(f"Other workspace skipped safely: {exc}")


def _render_settings() -> None:
    st.markdown("### ⚙️ Settings")
    st.caption("One Run Calculation button builds the existing Lunch, PowerBI, regime and shared caches, then opens Lunch automatically. No second Run or Load button is required.")
    c1, c2 = st.columns(2)
    if c1.button("▶ Run Calculation + Open Lunch", key="settings_run_calc_20260617", use_container_width=True):
        ns = _home_ns()
        with st.spinner("Calculating existing Lunch, PowerBI and regime data…"):
            from core.settings_run_orchestrator_20260617 import run_settings_calculation
            calculation_status = run_settings_calculation(ns)
        if bool((calculation_status.get("canonical") or {}).get("ok")):
            st.session_state["active_page"] = "Lunch"
            st.session_state["active_subpage"] = ""
        else:
            st.session_state["active_page"] = "Settings"
        _safe_rerun()
    if c2.button("🔄 Reset UI to Settings", key="settings_reset_ui_20260617", use_container_width=True):
        st.session_state["active_page"] = "Settings"
        st.session_state["active_subpage"] = ""
        _safe_rerun()

    status = st.session_state.get("settings_run_status_20260617")
    if isinstance(status, dict):
        cols = st.columns(5)
        cols[0].metric("Last Run", "READY" if status.get("ok") else "PARTIAL")
        cols[1].metric("Generation", str(status.get("calculation_generation", "-")))
        cols[2].metric("Lunch Metric", "READY" if (status.get("metric") or {}).get("ok") else "CHECK")
        cols[3].metric("PowerBI", "READY" if (status.get("powerbi") or {}).get("ok") else "CHECK")
        cols[4].metric("Built At", str(status.get("built_at", "-")))
        if status.get("errors"):
            with st.expander("Open / Close — Last calculation status", expanded=False):
                st.dataframe(pd.DataFrame({"Status": list(status.get("errors") or [])}), use_container_width=True, hide_index=True)

    with st.expander("Open / Close — Finnhub API Connector", expanded=True):
        try:
            from core.finnhub_connector import render_finnhub_connector
            render_finnhub_connector(location="settings")
        except Exception as exc:
            st.warning(f"Finnhub connector skipped safely: {exc}")

    try:
        from ui.decision_product_panel_20260617 import render_settings_product_status
        render_settings_product_status()
    except Exception as exc:
        st.caption(f"Decision diagnostics skipped safely: {exc}")

    try:
        from ui.sidebar_fallback_panel import render_sidebar_fallback_panel
        _safe_component("Settings controls", render_sidebar_fallback_panel, expanded=True)
    except Exception as exc:
        st.warning(f"Settings controls skipped safely: {exc}")


def show(runtime_context: Mapping[str, Any] | None = None) -> None:
    """Render only the authoritative page/subpage resolved by runner.py."""
    try:
        from core.tab_state_stability_20260615 import stabilize_tab_state
        stabilize_tab_state()
        page = str((runtime_context or {}).get("active_page") or st.session_state.get("active_page") or "Settings")
        subpage = str((runtime_context or {}).get("active_subpage") or st.session_state.get("active_subpage") or "")
        # Legacy navigation keys are mirrors only.
        from ui.antd_navigation_20260615 import sync_active_page_to_legacy_state
        page, subpage = sync_active_page_to_legacy_state()
    except Exception:
        page, subpage = "Settings", ""

    if page == "Settings":
        _render_settings()
    elif page == "Lunch":
        _render_lunch(_home_ns(), subpage)
    elif page == "Dinner":
        _render_dinner(_home_ns(), subpage)
    elif page == "Morning":
        _render_morning(_home_ns())
    elif page == "Research":
        _render_research(subpage)
    elif page == "Other":
        _render_other()
    else:
        _render_settings()
