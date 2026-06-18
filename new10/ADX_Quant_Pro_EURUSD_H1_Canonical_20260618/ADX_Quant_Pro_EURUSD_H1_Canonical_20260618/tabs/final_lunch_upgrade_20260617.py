"""Fast Lunch summary and true lazy access to preserved detail/history views."""
from __future__ import annotations

import time
from typing import Any
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from core.compact_canonical_20260619 import ACTIVE_CALCULATION_ID_KEY, get_compact_summary
from core.performance_store_20260619 import query_frame, export_frame, record_timing
from ui.composite_summary_cards_20260619 import render_eight_cards


def _legacy():
    name = "tabs._final_lunch_upgrade_20260617_legacy_runtime"
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).with_name("final_lunch_upgrade_20260617_legacy.src")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def _lunch_route_active() -> bool:
    return str(st.session_state.get("active_page") or st.session_state.get("tab_choice") or "") == "Lunch"


def _history_key() -> str:
    refs = st.session_state.get("disk_backed_frame_refs_20260619")
    if isinstance(refs, dict):
        for key in ("full_metric_history_df_20260618", "canonical_priority_table_20260617", "lunch_quick_decision_merged_table_20260617"):
            if key in refs:
                return key
    return "canonical_priority_table_20260617"


def _canonical_history_table(*, limit: int | None = 100, columns: list[str] | None = None) -> pd.DataFrame:
    calc_id = str(st.session_state.get(ACTIVE_CALCULATION_ID_KEY) or "")
    if calc_id:
        try:
            return query_frame(calc_id, _history_key(), columns=columns, limit=limit, order_by="Time", descending=True)
        except Exception as exc:
            st.session_state["lunch_history_optional_error_20260619"] = str(exc)
    # Compatibility fallback, reached only when the disk-backed generation is unavailable.
    for key in ("full_metric_history_df_20260618", "canonical_priority_table_20260617"):
        value = st.session_state.get(key)
        if isinstance(value, pd.DataFrame) and not value.empty:
            return value.head(limit) if limit is not None else value
    return pd.DataFrame()


def _safe_display_view(table: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(table, pd.DataFrame) or table.empty:
        return table
    phone = bool(st.session_state.get("phone_mode", False))
    return table.head(48 if phone else 100)


def render_lunch_25day_backtest_expander(*, key_suffix: str = "root") -> None:
    if not _lunch_route_active():
        return
    if not st.toggle("Open / Close — 25-Day Regime + NLP + KNN/Greedy History Table", value=False, key=f"lunch_history_gate_{key_suffix}_20260619"):
        return
    started = time.perf_counter()
    table = _canonical_history_table(limit=48 if st.session_state.get("phone_mode") else 100)
    if table.empty:
        st.info("The published history page is unavailable. Full stored history is preserved for export.")
    else:
        st.dataframe(_safe_display_view(table), use_container_width=True, hide_index=True, height=440)
        calc_id = str(st.session_state.get(ACTIVE_CALCULATION_ID_KEY) or "")
        if calc_id and st.button("Prepare full history export", key=f"lunch_export_gate_{key_suffix}_20260619"):
            full = export_frame(calc_id, _history_key())
            st.download_button("Download full history CSV", full.to_csv(index=False).encode(), "full_metric_history.csv", "text/csv", key=f"lunch_export_download_{key_suffix}_20260619")
    record_timing(st.session_state, "history_table_database_read", time.perf_counter() - started, rows=int(len(table)))


def render_lunch_10day_backtest_expander(*, key_suffix: str = "root") -> None:
    render_lunch_25day_backtest_expander(key_suffix=key_suffix)


def render_lunch_quick_decision() -> None:
    if not _lunch_route_active():
        return
    started = time.perf_counter()
    summary = get_compact_summary(st.session_state)
    st.markdown("### 🍱 Lunch — Quick Synced Decision")
    render_eight_cards(summary, location="lunch")
    if summary:
        st.caption(f"Canonical calculation ID: {summary.get('calculation_id', '-')} — the same object used by Dinner, Finder, Research and AI.")
    # Details are preserved but not imported/executed until explicitly opened.
    if st.toggle("Open / Close — detailed decision reasons and horizon reconciliation", value=False, key="lunch_decision_detail_gate_20260619"):
        from ui.decision_product_panel_20260617 import render_lunch_canonical_panel_details
        render_lunch_canonical_panel_details()
    if st.toggle("Open / Close — Lower 1D + Medium 5D + Higher 25D regime tables", value=False, key="lunch_regime_tables_gate_20260619"):
        _legacy()._render_three_regime_standard_tables()
    render_lunch_25day_backtest_expander(key_suffix="quick")
    record_timing(st.session_state, "lunch_open", time.perf_counter() - started, calculation_id=summary.get("calculation_id"))


__all__ = ["render_lunch_quick_decision", "render_lunch_25day_backtest_expander", "render_lunch_10day_backtest_expander"]
