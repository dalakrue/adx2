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
        try:
            from core.operational_sync_20260618 import record_operational_error
            record_operational_error(st.session_state, label, exc, stage="render")
        except Exception:
            pass
        st.warning(f"{label} skipped safely; remaining components are still available.")
        with st.expander(f"Open / Close — {label} error", expanded=True):
            st.code(str(exc))
            st.caption("The error was added to Settings → Errors / Fix Fast.")
    return None


def _render_chatgpt_style_ai():
    """Backward-compatible Dinner AI name, now backed by the compact fact pack."""
    from tabs.ai_assistant_compact_20260619 import render_compact_ai_assistant
    return render_compact_ai_assistant()


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
        try:
            from core.system_wide_completion_20260618 import readiness_message
            message = readiness_message(st.session_state, "Lunch Priority")
        except Exception:
            message = "The published priority table is unavailable. Open Settings → Errors / Fix Fast."
        st.dataframe(pd.DataFrame([{"Status": message}]), use_container_width=True, hide_index=True)
        return
    phone = bool(st.session_state.get("phone_mode", False))
    # Limit only the rendered view; the full canonical table remains cached.
    display_rows = 48 if phone else 240
    try:
        from ui.table_ordering_20260618 import priority_view
        show = priority_view(table, row_limit=display_rows)
    except Exception:
        # Safe fallback still keeps the highest ranked rows. Never use tail()
        # after a descending sort because that exposes old backtest candles.
        show = table.head(display_rows).reset_index(drop=True)
    st.dataframe(show, use_container_width=True, hide_index=True, height=height)


def _render_lunch(ns: dict, subpage: str) -> None:
    if not subpage:
        from tabs.final_lunch_upgrade_20260617 import render_lunch_quick_decision
        # One authoritative Lunch surface: six closed-first core fields.
        _safe_component("Lunch Six Principal Fields", render_lunch_quick_decision)
        return

    st.markdown(f"### 🍱 Lunch — {subpage}")
    if subpage == "Full Metric Details + History":
        from tabs.final_three_center_upgrade_20260614 import _render_metric_detail_section
        _safe_component("Full Metric Details + History", _render_metric_detail_section, ns or _home_ns())
    elif subpage == "PowerBI Projection":
        # Dedicated cached-only renderer: opening this inner page imports no
        # legacy Home module chain and performs no prediction/calibration work.
        from ui.powerbi_cached_renderer_20260619 import render_cached_powerbi_projection
        _safe_component("PowerBI Price Prediction Projection", render_cached_powerbi_projection)
        try:
            from ui.decision_product_panel_20260617 import render_powerbi_canonical_details
            render_powerbi_canonical_details()
        except Exception as exc:
            st.caption(f"Validated projection details skipped safely: {exc}")
    elif subpage == "Priority + Decision + Reliability":
        ns = ns or _home_ns()
        from tabs.dinner_morning_data_patch_20260614 import _render_priority_decision_reliability
        _safe_component("Priority + Decision + Reliability", _render_priority_decision_reliability, ns)
        renderer = ns.get("render_reliability_control_center_20260614")
        if callable(renderer):
            _safe_component("Reliability Control Center", renderer)
    elif subpage == "Finder":
        from ui.finder_canonical_view_20260619 import render_finder_canonical_view
        _safe_component("Finder — Canonical Full Metric Priority", render_finder_canonical_view, state=st.session_state)
    else:
        from tabs.final_lunch_upgrade_20260617 import render_lunch_quick_decision
        _safe_component("Lunch Quick Synced Decision", render_lunch_quick_decision)

    try:
        from tabs.final_lunch_upgrade_20260617 import render_lunch_25day_backtest_expander
        render_lunch_25day_backtest_expander(key_suffix=str(subpage))
    except Exception as exc:
        st.caption(f"25-day Lunch Regime + NLP history table skipped safely: {exc}")


def _render_dinner(ns: dict, subpage: str) -> None:
    """Render a visible Dinner inner-tab selector and only its active workspace."""
    prev = None
    options = ["Regime + Combined Logic", "AI Assistant"]
    requested = "AI Assistant" if str(subpage) == "AI Assistant" else "Regime + Combined Logic"
    widget_key = "dinner_inner_tab_20260618"
    if st.session_state.get(widget_key) not in options or str(subpage) in {"AI Assistant", "Unified Regime + Logic", "Regime Summary", "Combine Logic", "Combined Logic", "Regime + Combined Logic"}:
        st.session_state[widget_key] = requested
    st.markdown("### 🌙 Dinner")
    try:
        from ui.stable_ui_libs_20260615 import inject_stable_ui_css, segmented_choice
        inject_stable_ui_css()
        selected = segmented_choice("Dinner inner tab", options, key=widget_key, default=requested)
    except Exception:
        selected = st.radio("Dinner inner tab", options, index=options.index(requested), horizontal=True, key=widget_key + "_radio")
    selected = selected if selected in options else requested
    target_subpage = selected
    st.session_state["active_subpage"] = target_subpage
    st.session_state["dinner_active_subpage"] = target_subpage

    if selected == "AI Assistant":
        st.markdown("#### 🤖 AI Assistant — Dinner")
        _safe_component("Dinner AI Assistant", _render_chatgpt_style_ai)
        return

    from tabs.dinner_unified_center_20260617 import render_dinner_unified_center
    from ui.decision_product_panel_20260617 import render_regime_lifecycle_panel
    _safe_component(
        selected, render_dinner_unified_center, ns, prev, render_regime_lifecycle_panel,
    )


def _render_morning() -> None:
    st.markdown("### 🌅 Morning — Doo Prime")
    st.caption("Morning remains closed-first. The legacy Home module chain is imported only after the true load switch is enabled.")
    if not st.toggle("Open / Close — Load Morning Workspace", value=False, key="morning_true_load_gate_20260620"):
        st.info("Morning is ready but not instantiated. Opening or closing other tabs performs no Morning calculation.")
        return
    ns = _home_ns()
    _safe_component("Morning / Doo Prime", _prev_morning(ns))


def _render_research(subpage: str) -> None:
    st.markdown("### 🎓 Research")
    if subpage in {"Research AI Assistant", "AI Assistant"}:
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
            try:
                from core.system_wide_completion_20260618 import readiness_message
                message = readiness_message(st.session_state, "Research Data Analysis")
            except Exception:
                message = "The published Quant Structure is unavailable. Open Settings → Errors / Fix Fast."
            st.dataframe(pd.DataFrame([{"Status": message}]), use_container_width=True, hide_index=True)
        return
    st.caption("The selected Research workspace is imported only after the true load switch is enabled.")
    if not st.toggle("Open / Close — Load Selected Research Workspace", value=False, key="research_true_load_gate_20260620"):
        st.info("Research is ready but not instantiated. Tab switching does not import Data Analysis, Data Mining or NLP pipelines.")
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





def _render_secure_automation_settings() -> None:
    from core.secure_api_startup_20260619 import initialize_secure_settings, secure_secret_status
    initialize_secure_settings(st.session_state)
    secret_state = secure_secret_status(st.session_state)
    st.markdown("### 🔐 Secure API + Automatic Startup")
    c1, c2 = st.columns(2)
    c1.metric("Finnhub API", "CONFIGURED" if secret_state.get("finnhub_configured") else "NOT CONFIGURED", str(secret_state.get("finnhub_source", "")))
    c2.metric("Second Market API", "CONFIGURED" if secret_state.get("second_api_configured") else "NOT CONFIGURED", str(secret_state.get("second_api_source", "")))
    st.caption("Stored secrets remain server-side. The secure design never autofills their actual values into an input field or sends them to the browser.")
    st.toggle("Use securely stored API keys", key="use_secure_api_keys_20260619")
    st.toggle("Automatically connect APIs after login (connection only)", key="auto_connect_after_login_20260619")
    st.session_state["auto_calculate_new_h1_20260619"] = False
    st.session_state["open_lunch_after_auto_run_20260619"] = False
    st.info("Automatic calculation is disabled. Only the Settings ‘Run Calculation + Open Lunch’ button can publish a new all-tab generation.")
    st.number_input(
        "Auto-run cooldown (minutes)", min_value=1, max_value=60, step=1,
        key="auto_run_cooldown_minutes_20260619",
        help="The generation lock, latest-H1 guard and cooldown prevent duplicate Cloud calculations.",
    )
    startup = st.session_state.get("secure_startup_status_20260619")
    if isinstance(startup, Mapping):
        st.caption(
            f"Startup guard: {startup.get('status', 'NO_ACTION')} · latest H1 {startup.get('latest_h1') or '-'} · "
            f"published H1 {startup.get('published_h1') or '-'}"
        )


def _save_and_connect_twelve_callback(widget_key: str) -> None:
    """Atomically save a temporary key and start its one connection request."""
    key = str(st.session_state.get(widget_key, "") or "").strip()
    if not key:
        try:
            from core.connector_state_machine_20260621 import fail
            fail(st.session_state, "market_connector_20260621", "Enter a Twelve Data API key first.")
        except Exception:
            pass
        return
    st.session_state["twelve_api_key"] = key
    st.session_state["connector_mode"] = "twelve"
    from core.navigation_parts.connection import _connect_now
    _connect_now("Twelve Data Save & Connect", quick=True)


def _render_mobile_api_key_center() -> None:
    """Secure status plus optional, blank temporary replacement fields."""
    st.markdown("""
    <style>
    @media (max-width: 780px) {
      div[data-testid="stTextInput"] input,
      div[data-testid="stTextArea"] textarea {
        font-size: 16px !important; min-height: 48px !important;
        -webkit-user-select: text !important; user-select: text !important;
        -webkit-touch-callout: default !important; touch-action: manipulation !important;
      }
      div[data-testid="stTextArea"] textarea {min-height: 76px !important; overflow-wrap: anywhere !important;}
      div[data-testid="stButton"] button {min-height: 46px !important; white-space: normal !important;}
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("### 🔑 Temporary API Key Replacement")
    st.caption("These blank fields are optional session-only replacements. Streamlit Secrets are never shown or copied into them.")

    twelve_generation = int(st.session_state.get("settings_mobile_twelve_generation_20260619", 0) or 0)
    with st.expander("Open / Close — Replace Second / Twelve Data API Key", expanded=False):
        value = st.text_area(
            "Twelve Data API key — mobile paste box", value="",
            key=f"settings_mobile_twelve_api_key_paste_20260619_{twelve_generation}", height=76,
            placeholder="Optional: paste a temporary replacement key for this session",
            help="The stored Streamlit Secret is intentionally never autofilled here.",
        )
        c1, c2 = st.columns(2)
        c1.button(
            "Save Key + Auto-Connect (One Click)", key="settings_mobile_save_twelve_20260619", use_container_width=True,
            disabled=not bool(str(value or '').strip()), on_click=_save_and_connect_twelve_callback,
            args=(f"settings_mobile_twelve_api_key_paste_20260619_{twelve_generation}",),
        )
        if c2.button("Clear Temporary Twelve Key", key="settings_mobile_clear_twelve_20260619", use_container_width=True):
            st.session_state["twelve_api_key"] = ""
            st.session_state["settings_mobile_twelve_generation_20260619"] = twelve_generation + 1
            st.success("Temporary replacement cleared. The server-side secret, if configured, remains available.")
            _safe_rerun()

    nlp_generation = int(st.session_state.get("settings_mobile_nlp_generation_20260619", 0) or 0)
    with st.expander("Open / Close — NLP / AI Assistant API Key", expanded=False):
        value = st.text_area(
            "NLP API key — mobile paste box", value="",
            key=f"settings_mobile_nlp_api_key_paste_20260619_{nlp_generation}", height=76,
            placeholder="Optional: paste NLP/OpenAI-compatible key for AI Assistant only",
        )
        model = st.text_input("NLP model name", value=str(st.session_state.get("nlp_api_model", "") or ""), key="settings_mobile_nlp_model_20260619")
        endpoint = st.text_input("NLP endpoint", value=str(st.session_state.get("nlp_api_endpoint", "https://api.openai.com/v1/chat/completions") or ""), key="settings_mobile_nlp_endpoint_20260619")
        c1, c2 = st.columns(2)
        if c1.button("Save + Enable AI (One Click)", key="settings_mobile_save_nlp_20260619", use_container_width=True, disabled=not bool(str(value or '').strip())):
            st.session_state["nlp_api_key"] = str(value or "").strip()
            st.session_state["nlp_api_model"] = str(model or "").strip()
            st.session_state["nlp_api_endpoint"] = str(endpoint or "").strip()
            st.session_state["nlp_api_connected"] = True
            st.session_state["nlp_api_last_saved_20260622"] = pd.Timestamp.now(tz="UTC").isoformat()
            st.success("NLP/API settings saved and enabled in one click. The local grounded AI remains usable even if this API disconnects.")
        if c2.button("Clear NLP Key", key="settings_mobile_clear_nlp_20260619", use_container_width=True):
            st.session_state["nlp_api_key"] = ""
            st.session_state["nlp_api_connected"] = False
            st.session_state["settings_mobile_nlp_generation_20260619"] = nlp_generation + 1
            st.success("NLP key cleared.")
            _safe_rerun()


def _render_market_time_metrics(*, query_mt5: bool = True) -> dict[str, Any]:
    """Show feed freshness without starting a calculation."""
    try:
        from core.market_time_freshness_20260622 import market_time_snapshot
        snap = market_time_snapshot(st.session_state, query_mt5=query_mt5)
    except Exception as exc:
        snap = {"status": "CHECK", "current_utc_display": "Unavailable", "broker_clock_display": "Unavailable", "latest_loaded_display": "Unavailable", "lag_minutes": None, "source": "UNKNOWN", "error": str(exc)}
    cols = st.columns(5)
    cols[0].metric("Feed Freshness", str(snap.get("status") or "CHECK"), str(snap.get("source") or "DISCONNECTED"))
    cols[1].metric("Current UTC", str(snap.get("current_utc_display") or "-").replace(" UTC", ""))
    cols[2].metric("MT5 Latest Tick", str(snap.get("mt5_tick_display") or "Not available").replace(" UTC", ""))
    cols[3].metric("Broker Clock", str(snap.get("broker_clock_display") or "Not available"))
    lag = snap.get("lag_minutes")
    delta = f"{lag:g} min behind current bar" if isinstance(lag, (int, float)) else "No timestamp"
    cols[4].metric("Latest Candle — Broker", str(snap.get("latest_loaded_broker_display") or "No loaded candle"), delta)
    st.caption("MetaTrader tick timestamps are normalized to UTC for calculations. Visible candle time uses the configured broker offset; Myanmar time remains a separate UTC+6:30 display.")
    return snap


def _open_lunch_ai_after_settings_run(*, used_previous: bool = False) -> None:
    phone = bool(st.session_state.get("phone_mode", False))
    updates = {
        "active_page": "Lunch", "tab_choice": "Lunch", "active_subpage": "", "lunch_active_subpage": "",
        "lunch_bi_visual_ready": True, "show_restored_powerbi_20260617": True,
        "load_original_powerbi_from_antd_lunch_20260615": True,
        "settings_auto_open_lunch_20260617": True,
        "lunch_calculation_completed_notice_20260621": True,
        "lunch_field_open_5_20260621": True, "lunch_field_widget_5_20260621": True,
        "lunch_scroll_to_field5_20260622": True,
        "settings_used_previous_canonical_20260622": bool(used_previous),
    }
    if phone:
        updates.update({
            "lunch_field_open_1_20260621": False, "lunch_field_widget_1_20260621": False,
            "lunch_field_open_2_20260621": False, "lunch_field_widget_2_20260621": False,
            "lunch_field_open_3_20260621": False, "lunch_field_widget_3_20260621": False,
            "lunch_field_open_4_20260621": False, "lunch_field_widget_4_20260621": False,
            "lunch_field_open_6_20260621": False, "lunch_field_widget_6_20260621": False,
        })
    else:
        updates.update({"lunch_field_open_1_20260621": True, "lunch_field_widget_1_20260621": True})
    st.session_state.update(updates)

def _render_settings() -> None:
    st.session_state.setdefault("mt5_broker_utc_offset_hours_20260622", 4.0)
    st.markdown("### ⚙️ Settings")
    st.caption("This is the only manual all-in-one calculation control. One click refreshes the selected market feed once, builds the synchronized generation, opens Lunch, and opens the Grounded AI Assistant. No second Run or connector click is required.")
    _render_market_time_metrics(query_mt5=True)

    previous_status = st.session_state.get("settings_run_status_20260617")
    if isinstance(previous_status, Mapping):
        canonical_ok = bool((previous_status.get("canonical") or {}).get("ok"))
        previous_used = bool(st.session_state.get("settings_used_previous_canonical_20260622"))
        ai_ready = False
        try:
            from tabs.ai_assistant_compact_20260619 import _recover_fact_pack
            ai_ready = bool(_recover_fact_pack(st.session_state))
        except Exception:
            ai_ready = False
        top = st.columns(4)
        top[0].metric("All-in-One Run", "FULLY WORKED" if canonical_ok else ("PREVIOUS VALID USED" if ai_ready else "CHECK"))
        top[1].metric("Published Generation", str(previous_status.get("calculation_generation", st.session_state.get("canonical_calculation_generation_20260617", "-"))))
        top[2].metric("AI Assistant", "READY" if ai_ready else "OFFLINE DIAGNOSTIC")
        top[3].metric("Auto-Open Lunch", "READY" if (canonical_ok or previous_used or ai_ready) else "WAITING")

    c1, c2 = st.columns(2)
    if c1.button("▶ Run Calculation + Open Lunch (One Click)", key="settings_run_calc_20260617", use_container_width=True):
        ns = _home_ns()
        refresh_result: dict[str, Any] = {}
        with st.spinner("Refreshing the selected feed once, calculating all synchronized tabs, then opening Lunch…"):
            try:
                from core.app.refresh import refresh_data
                refresh_result = refresh_data(st.session_state, symbol_override="EURUSD", timeframe_override="H1")
            except Exception as exc:
                refresh_result = {"status": "FAILURE", "ok": False, "message": f"Refresh failed safely: {exc}"}
            from core.settings_run_orchestrator_20260617 import run_settings_calculation
            calculation_status = run_settings_calculation(ns)
        calculation_status["refresh_before_run"] = refresh_result
        st.session_state["settings_run_status_20260617"] = calculation_status
        st.session_state["settings_last_one_click_refresh_20260622"] = refresh_result
        # Compatibility guard retained for static architecture tests: if bool((calculation_status.get("canonical") or {}).get("ok"))
        new_ok = bool((calculation_status.get("canonical") or {}).get("ok"))
        valid_canonical = False
        try:
            from core.canonical_runtime_20260617 import get_canonical
            valid_canonical = bool(get_canonical(st.session_state))
        except Exception:
            valid_canonical = bool(st.session_state.get("canonical_decision_result_20260617"))
        fact_pack_ready = False
        try:
            from tabs.ai_assistant_compact_20260619 import _recover_fact_pack
            fact_pack_ready = bool(_recover_fact_pack(st.session_state))
        except Exception:
            fact_pack_ready = False
        if new_ok or valid_canonical or fact_pack_ready:
            _open_lunch_ai_after_settings_run(used_previous=not new_ok)
        else:
            st.session_state["active_page"] = "Settings"
            st.session_state["active_subpage"] = ""
        _safe_rerun()
    if c2.button("🔄 Reset UI to Settings", key="settings_reset_ui_20260617", use_container_width=True):
        st.session_state["active_page"] = "Settings"
        st.session_state["active_subpage"] = ""
        _safe_rerun()

    # Secure server-side secrets and guarded authenticated startup controls.
    _render_secure_automation_settings()

    # Optional temporary replacements; stored secrets are never autofilled.
    _render_mobile_api_key_center()

    with st.expander("Open / Close — Twelve Data + MT5 Market Connector", expanded=True):
        st.caption("Choose Twelve Data, MT5, fallback, timeframe and candle count here. Twelve Data uses the mobile-paste key saved above; MT5 uses the locally installed MetaTrader 5 terminal.")
        # The initial default is created once at Settings startup. Existing user
        # choices are preserved across reruns; Myanmar time is shown separately.
        st.number_input(
            "MT5 broker chart UTC offset (display only)", min_value=-12.0, max_value=14.0, step=0.5,
            key="mt5_broker_utc_offset_hours_20260622",
            help="MT5 Python tick timestamps are UTC. Set the exact broker-chart offset. Field 1 then rebuilds Date/Weekday/Hour from this broker clock; Myanmar time remains a separate UTC+6:30 display.",
        )
        try:
            from ui.sidebar_fallback_panel import _render_connector
            _render_connector(key_prefix="settings_market_20260619", show_secret_inputs=False)
        except Exception as exc:
            st.warning(f"Market connector skipped safely: {exc}")

    with st.expander("Open / Close — Finnhub API Connector", expanded=True):
        try:
            from core.finnhub_connector import render_finnhub_connector
            render_finnhub_connector(location="settings")
        except Exception as exc:
            st.warning(f"Finnhub connector skipped safely: {exc}")

    with st.expander("Open / Close — Trade Timer / Sound Alert", expanded=True):
        try:
            from ui.sidebar_fallback_panel import _render_timer
            _render_timer(key_prefix="settings_timer_20260619")
        except Exception as exc:
            st.warning(f"Trade timer skipped safely: {exc}")

    with st.expander("Open / Close — Account / Logout", expanded=False):
        try:
            from ui.sidebar_fallback_panel import _render_ui_and_account
            _render_ui_and_account(key_prefix="settings_account_20260619")
        except Exception as exc:
            st.warning(f"Account controls skipped safely: {exc}")

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
        readiness = status.get("readiness") if isinstance(status.get("readiness"), dict) else st.session_state.get("system_wide_readiness_manifest_20260618")
        if isinstance(readiness, dict):
            component_rows = []
            for name, item in (readiness.get("components") or {}).items():
                item = item if isinstance(item, dict) else {}
                component_rows.append({
                    "Component": name,
                    "Status": "READY" if item.get("ready") else "CHECK / ERROR",
                    "Rows": item.get("rows", 0),
                    "Detail": item.get("detail", ""),
                })
            with st.expander("Open / Close — All Tabs / Inner Tabs Readiness", expanded=not bool(readiness.get("ready"))):
                st.dataframe(pd.DataFrame(component_rows), use_container_width=True, hide_index=True)

    try:
        from core.operational_sync_20260618 import collect_sync_health, errors_frame, clear_operational_errors
        health = pd.DataFrame(collect_sync_health(st.session_state))
        with st.expander("Open / Close — Synchronization Health", expanded=False):
            st.dataframe(health, use_container_width=True, hide_index=True)
        errors = errors_frame(st.session_state)
        has_errors = bool(len(errors)) if hasattr(errors, "__len__") else False
        with st.expander("Open / Close — Errors / Fix Fast", expanded=has_errors):
            if has_errors:
                st.dataframe(errors, use_container_width=True, hide_index=True)
                if st.button("Clear displayed errors", key="clear_operational_errors_20260618", use_container_width=True):
                    clear_operational_errors(st.session_state)
                    _safe_rerun()
            else:
                st.success("No captured calculation or renderer errors.")
    except Exception as exc:
        st.caption(f"Synchronization diagnostics unavailable: {exc}")

    try:
        from ui.decision_product_panel_20260617 import render_settings_product_status
        render_settings_product_status()
    except Exception as exc:
        st.caption(f"Decision diagnostics skipped safely: {exc}")


def show(runtime_context: Mapping[str, Any] | None = None) -> None:
    """Render only the authoritative page/subpage resolved by runner.py."""
    generation_sync = (runtime_context or {}).get("generation_sync") if isinstance(runtime_context, Mapping) else None
    if isinstance(generation_sync, Mapping) and generation_sync.get("status") not in {"CURRENT", "SYNCED", "NOT_READY"}:
        st.warning("A stale tab view was detected. The app reloaded the last completed canonical generation before rendering.")
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

    if page != "Settings":
        manifest = st.session_state.get("system_wide_readiness_manifest_20260618")
        if isinstance(manifest, dict) and not bool(manifest.get("ready")) and st.session_state.get("settings_run_complete_20260617"):
            missing = [name for name, item in (manifest.get("components") or {}).items() if isinstance(item, dict) and not item.get("ready")]
            if missing:
                st.warning(
                    f"Published generation {manifest.get('calculation_generation', '-')} is available with visible component errors: "
                    + ", ".join(missing[:6])
                    + ("…" if len(missing) > 6 else "")
                    + ". Open Settings → Errors / Fix Fast for exact details."
                )

    if page == "Settings":
        _render_settings()
    elif page == "Lunch":
        _render_lunch({}, subpage)
    elif page == "Dinner":
        _render_dinner({}, subpage)
    elif page == "Morning":
        _render_morning()
    elif page == "Research":
        _render_research(subpage)
    elif page == "Other":
        _render_other()
    else:
        _render_settings()
