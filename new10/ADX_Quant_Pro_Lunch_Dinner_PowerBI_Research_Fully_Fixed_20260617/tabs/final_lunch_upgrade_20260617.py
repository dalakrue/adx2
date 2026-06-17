"""Compact, synchronized Lunch Quick Decision renderer (2026-06-17)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core.regime_sync_20260617 import canonical_regime_snapshot, regime_standard_detail_tables
from core.runtime_cache_20260617 import cached_display_dataframe


def _time_text(value, current: bool = False) -> str:
    try:
        if pd.isna(value):
            return "OPEN / CURRENT" if current else "Not recorded"
        return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value or ("OPEN / CURRENT" if current else "Not recorded"))


def _render_metrics(snapshot: dict) -> None:
    m1, m2, m3 = st.columns(3)
    m1.metric("Major Regime", snapshot.get("regime", "-"), snapshot.get("regime_direction", "WAIT"))
    m2.metric("Synced Decision", snapshot.get("decision", "WAIT"), snapshot.get("regime_direction", "WAIT"))
    m3.metric("Regime True / False", snapshot.get("regime_validation", "FALSE / WATCH"), f"Reliability {snapshot.get('reliability', 0):.1f}%")
    m4, m5, m6 = st.columns(3)
    m4.metric("Regime Start", _time_text(snapshot.get("regime_start")))
    m5.metric("Regime End", snapshot.get("regime_end_display", "OPEN / CURRENT"))
    samples = int(snapshot.get("error_samples", 0) or 0)
    error_value = snapshot.get("avg_error_pct")
    error_text = f"{float(error_value):.5f}%" if error_value is not None else "N/A"
    error_kind = "proxy" if snapshot.get("error_is_proxy") else "actual"
    error_delta = f"{samples} completed samples • {error_kind}" if error_value is not None else "Run prediction-vs-actual backtest"
    m6.metric("Avg Prediction Error", error_text, error_delta)




def _render_shared_quick_evidence() -> None:
    """Show synchronized evidence only; never calculate or override a trade."""
    try:
        from core.canonical_runtime_20260617 import shared_from_runtime
        shared = shared_from_runtime(st.session_state)
    except Exception:
        shared = {}
    decision = shared.get("decision", {}) if isinstance(shared, dict) else {}
    priority = shared.get("priority", {}) if isinstance(shared, dict) else {}
    reliability = shared.get("reliability", {}) if isinstance(shared, dict) else {}
    nlp = shared.get("nlp", {}) if isinstance(shared, dict) else {}
    nlp_summary = nlp.get("summary", {}) if isinstance(nlp, dict) else {}
    best = priority.get("best", {}) if isinstance(priority, dict) else {}
    p_label = best.get("Priority") or best.get("Priority Label") or best.get("priority") or best.get("KNN Priority") or "N/A"
    entry = decision.get("entry_score")
    entry_text = f"{float(entry):.2f}/10" if isinstance(entry, (int, float)) else "N/A"
    r1 = st.columns(4)
    r1[0].metric("Current Entry", entry_text, str(decision.get("central_decision", "WAIT")))
    r1[1].metric("Priority", str(p_label), "Shared priority table")
    r1[2].metric("System Reliability", f"{float(reliability.get('score', 0) or 0):.1f}%", str(reliability.get("label", reliability.get("status", "WATCH"))))
    r1[3].metric("NLP Direction", str(nlp_summary.get("nlp_direction", "WAIT")), f"Reliability {float(nlp_summary.get('reliability', 0) or 0):.1f}%")
    r2 = st.columns(3)
    r2[0].metric("NLP Conflict", str(nlp_summary.get("conflict_level", "NO NLP DATA")), f"Safer {nlp_summary.get('less_risky_decision', 'WAIT')}")
    r2[1].metric("Latest NLP Rank 1", str(nlp_summary.get("latest_rank_1_news", "No relevant news"))[:55])
    r2[2].metric("News Time", str(nlp_summary.get("news_time", "Not available"))[:32])


def _render_three_regime_standard_tables() -> None:
    """Three compact existing-field tables: lower 1D, medium 5D, higher 25D."""
    with st.expander("Open / Close — Lower 1D + Medium 5D + Higher 25D Regime Priority Tables", expanded=False):
        st.caption(
            "All three tables use the same completed H1 data and the same shared run. "
            "KNN and Greedy priorities are ascending (1 is strongest); scores are normalized to /10. "
            "Less Risky Bias may remain WAIT when evidence is weak or regime validation is unsafe."
        )
        try:
            tables = regime_standard_detail_tables(force=False)
        except Exception as exc:
            st.warning(f"Regime standard tables are not ready: {exc}")
            return
        specs = (
            ("lower", "Lower Standard Regime — 1 Day", "1 completed-day H1 range", 300),
            ("medium", "Medium Standard Regime — 5 Days", "5 completed-day H1 range", 380),
            ("higher", "Higher Standard Regime — 25 Days", "25 completed-day H1 range", 440),
        )
        for key, title, range_text, height in specs:
            table = tables.get(key, pd.DataFrame()) if isinstance(tables, dict) else pd.DataFrame()
            st.markdown(f"#### {title}")
            if not isinstance(table, pd.DataFrame) or table.empty:
                st.dataframe(pd.DataFrame([{"Status": "Run Calculation in Settings to build this synchronized table."}]), use_container_width=True, hide_index=True)
                continue
            bias = "WAIT"
            if "Less Risky Bias" in table.columns and not table["Less Risky Bias"].dropna().empty:
                modes = table["Less Risky Bias"].astype(str).mode()
                bias = str(modes.iloc[0]) if not modes.empty else "WAIT"
            best_knn = pd.to_numeric(table.get("KNN Priority"), errors="coerce").min()
            best_greedy = pd.to_numeric(table.get("Greedy Priority"), errors="coerce").min()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Rows", f"{len(table):,}", range_text)
            c2.metric("Best KNN Priority", f"{best_knn:.0f}" if pd.notna(best_knn) else "N/A", "Ascending")
            c3.metric("Best Greedy Priority", f"{best_greedy:.0f}" if pd.notna(best_greedy) else "N/A", "Ascending")
            c4.metric("Less Risky Bias", bias, "BUY / SELL / WAIT")
            st.dataframe(table, use_container_width=True, hide_index=True, height=height)



def _history_validation(row: pd.Series, current_validation: str) -> str:
    """Validate each displayed regime segment instead of copying one value to all rows."""
    try:
        regime = str(row.get("Regime", "") or "").strip()
        start = pd.to_datetime(row.get("Regime Start"), errors="coerce")
        end = pd.to_datetime(row.get("Regime End"), errors="coerce")
        status = str(row.get("Status", "") or "").upper()
        if status == "CURRENT":
            return current_validation
        valid = bool(regime and regime not in {"-", "NONE", "NAN"} and not pd.isna(start))
        if valid and not pd.isna(end):
            valid = bool(end >= start)
        return "TRUE" if valid else "FALSE / WATCH"
    except Exception:
        return "FALSE / WATCH"


def _render_table_metrics(table: pd.DataFrame, *, window: str, label: str) -> None:
    rows = len(table) if isinstance(table, pd.DataFrame) else 0
    latest = "-"
    if isinstance(table, pd.DataFrame) and not table.empty:
        for col in ("Time", "time", "Datetime", "Date"):
            if col in table.columns:
                parsed = pd.to_datetime(table[col], errors="coerce").dropna()
                if not parsed.empty:
                    latest = _time_text(parsed.max())
                    break
    c1, c2, c3 = st.columns(3)
    c1.metric(f"{label} Rows", f"{rows:,}")
    c2.metric("Data Window", window)
    c3.metric("Latest H1", latest)



def _canonical_history_table() -> pd.DataFrame:
    table = st.session_state.get("canonical_priority_table_20260617")
    if isinstance(table, pd.DataFrame) and not table.empty:
        return table
    return pd.DataFrame()


def _safe_display_view(table: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(table, pd.DataFrame) or table.empty:
        return table
    limit = 168 if bool(st.session_state.get("phone_mode", False)) else 360
    canonical = st.session_state.get("canonical_decision_result_20260617") or {}
    return cached_display_dataframe(
        table, row_limit=limit, time_column="Time",
        sort_columns=("KNN Priority", "Greedy Priority", "Time"),
        ascending=(True, True, True),
        data_signature=str(canonical.get("data_signature") or "NO_SIGNATURE"),
        calculation_version=str(canonical.get("calculation_version") or "decision-product-20260617-v1"),
    )

def _lunch_route_active() -> bool:
    # Strict route guard: this renderer is Lunch-only and must never appear on
    # Settings, the removed Home route, or another top-level page.
    return str(st.session_state.get("active_page") or st.session_state.get("tab_choice") or "") == "Lunch"


def render_lunch_25day_backtest_expander(*, key_suffix: str = "root") -> None:
    if not _lunch_route_active():
        return
    snapshot = canonical_regime_snapshot(days=25)
    table = _canonical_history_table()
    with st.expander("Open / Close — 25-Day Regime + NLP + KNN/Greedy History Table", expanded=False):
        _render_metrics(snapshot)
        full_table = table if isinstance(table, pd.DataFrame) and not table.empty else pd.DataFrame([{
            "Status": "Run Calculation in Settings to build the synchronized 25-day EURUSD H1 history."
        }])
        _render_table_metrics(full_table, window="25 days / EURUSD H1", label="Merged History")
        st.caption("The calculation/export table retains the full 25-day range. Phone and desktop rendering use a bounded recent view to reduce browser memory and heat.")
        st.dataframe(_safe_display_view(full_table), use_container_width=True, hide_index=True, height=440)


# Backward-compatible callable name used by older imports.
def render_lunch_10day_backtest_expander(*, key_suffix: str = "root") -> None:
    render_lunch_25day_backtest_expander(key_suffix=key_suffix)


def render_lunch_quick_decision() -> None:
    if not _lunch_route_active():
        return
    snapshot = canonical_regime_snapshot(days=25)
    st.markdown("### 🍱 Lunch — Quick Synced Decision")
    try:
        from ui.decision_product_panel_20260617 import render_lunch_canonical_panel
        render_lunch_canonical_panel()
    except Exception as exc:
        st.caption(f"Canonical decision panel skipped safely: {exc}")
    _render_metrics(snapshot)
    _render_shared_quick_evidence()
    _render_three_regime_standard_tables()

    table = _canonical_history_table()
    st.session_state["lunch_quick_decision_merged_table_20260617"] = table
    if isinstance(table, pd.DataFrame) and not table.empty:
        _render_table_metrics(table, window="25 days / EURUSD H1", label="Quick Decision")
        order = st.columns(2)
        order[0].metric("KNN Priority Order", "Ascending")
        order[1].metric("Greedy Priority Order", "Ascending")
        st.dataframe(_safe_display_view(table), use_container_width=True, hide_index=True, height=430)
    else:
        empty = pd.DataFrame([{"Status": "Run Calculation or connect EURUSD H1 data to build the merged table."}])
        _render_table_metrics(empty, window="25 days / EURUSD H1", label="Quick Decision")
        st.dataframe(empty, use_container_width=True, hide_index=True)

