"""Single active renderer for the protected Full Metric result.

This module never imports or duplicates Full Metric formulas.  It renders the
already-computed result produced by ``tabs.eurusd_h1_matrix`` and keeps all
operational histories current-first.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

import pandas as pd
import streamlit as st

from ui.table_ordering_20260618 import chronological_view


_SKIP_TABLES = {"reverse10", "history", "history_by_factor"}
_PREFERRED_TABLES = (
    "session", "session_table", "entry", "entry_table", "direction",
    "direction_table", "hold", "hold_table", "exit", "exit_table", "tp",
    "tp_table", "metric_table", "full_metric_table", "detail", "details",
)


def _height(frame: pd.DataFrame, maximum: int = 560) -> int:
    return min(maximum, max(220, 44 + min(len(frame), 18) * 28))


def _jsonable(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return value.to_dict("records")
    if isinstance(value, pd.Series):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items() if str(k) != "metrics"}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _current_identity() -> dict[str, Any]:
    try:
        from core.canonical_runtime_20260617 import get_canonical
        canonical = get_canonical(st.session_state)
    except Exception:
        canonical = {}
    return {
        "Symbol": canonical.get("symbol", "EURUSD") if isinstance(canonical, dict) else "EURUSD",
        "Timeframe": canonical.get("timeframe", "H1") if isinstance(canonical, dict) else "H1",
        "Latest Completed H1": canonical.get("latest_completed_candle_time", "Not ready") if isinstance(canonical, dict) else "Not ready",
        "Run ID": canonical.get("run_id", "Not ready") if isinstance(canonical, dict) else "Not ready",
        "Generation": canonical.get("calculation_generation", "-") if isinstance(canonical, dict) else "-",
        "Data Signature": canonical.get("data_signature", "Not ready") if isinstance(canonical, dict) else "Not ready",
    }


def _decision_summary(result: Mapping[str, Any]) -> pd.DataFrame:
    scores = dict(result.get("scores") or {})
    rows = [
        {"Decision Field": "Current Decision", "Value": scores.get("Decision", "NO TRADE"), "Score /10": scores.get("Master /10")},
        {"Decision Field": "Direction Decision", "Value": scores.get("Direction", "WAIT"), "Score /10": scores.get("Direction Score")},
        {"Decision Field": "Entry Decision", "Value": (result.get("entry").iloc[0].get("Decision") if isinstance(result.get("entry"), pd.DataFrame) and not result.get("entry").empty else "Not recorded"), "Score /10": scores.get("Entry /10")},
        {"Decision Field": "Hold Decision", "Value": "Protected Hold score", "Score /10": scores.get("Hold /10")},
        {"Decision Field": "Exit Decision", "Value": (result.get("exit").iloc[0].get("Decision") if isinstance(result.get("exit"), pd.DataFrame) and not result.get("exit").empty else "Not recorded"), "Score /10": scores.get("Exit Risk /10")},
        {"Decision Field": "TP Decision", "Value": (result.get("tp").iloc[0].get("Decision") if isinstance(result.get("tp"), pd.DataFrame) and not result.get("tp").empty else "Not recorded"), "Score /10": scores.get("TP /10")},
        {"Decision Field": "Master Decision", "Value": scores.get("Decision", "NO TRADE"), "Score /10": scores.get("Master /10")},
        {"Decision Field": "Trend Capacity Remaining", "Value": "Protected metric", "Score /10": None},
    ]
    return pd.DataFrame(rows)


def render_full_metric_shared(ns: dict[str, Any], *, result: Any = None) -> None:
    """Render the complete cached Full Metric output without recalculation."""
    identity = _current_identity()
    st.caption(
        "Canonical source of truth: protected Full Metric Detail + History. "
        "Run Calculation is available only in Settings; this route reuses the published generation."
    )
    id_cols = st.columns(3)
    id_cols[0].metric("EURUSD H1", f"{identity['Symbol']} {identity['Timeframe']}", f"Generation {identity['Generation']}")
    id_cols[1].metric("Latest Completed H1", str(identity["Latest Completed H1"])[:25])
    id_cols[2].metric("Run", str(identity["Run ID"])[:18], str(identity["Data Signature"])[:18])

    if result is None:
        getter = ns.get("_get_cached_lunch_metric_result")
        if callable(getter):
            try:
                result = getter(force=False)
            except Exception as exc:
                st.warning(f"Cached Full Metric result could not load safely: {exc}")
                result = None
    if not isinstance(result, Mapping) or not result.get("ok"):
        st.info("Run Calculation in Settings to publish the complete Full Metric result.")
        return

    quality = ns.get("_render_lunch_metric_quality_table")
    if callable(quality):
        try:
            quality(result)
        except TypeError:
            quality()
        except Exception as exc:
            st.caption(f"Metric quality display skipped safely: {exc}")

    summary = _decision_summary(result)
    st.markdown("#### Current Decision, Direction, Entry, Hold, Exit, TP and Master")
    st.dataframe(summary, use_container_width=True, hide_index=True, height=_height(summary, 360))

    reverse = result.get("reverse10")
    st.markdown("#### Ten Reverse-Decision Factors")
    if isinstance(reverse, pd.DataFrame) and not reverse.empty:
        st.dataframe(reverse, use_container_width=True, hide_index=True, height=_height(reverse, 430))
    else:
        st.info("Ten reverse-decision factor table is empty for this generation.")

    tables: list[tuple[str, pd.DataFrame]] = []
    seen: set[int] = set()
    for key in _PREFERRED_TABLES:
        value = result.get(key)
        if isinstance(value, pd.DataFrame) and not value.empty and id(value) not in seen:
            seen.add(id(value)); tables.append((key, value))
    for key, value in result.items():
        if key in _SKIP_TABLES:
            continue
        if isinstance(value, pd.DataFrame) and not value.empty and id(value) not in seen:
            seen.add(id(value)); tables.append((str(key), value))
    for name, table in tables:
        st.markdown(f"#### {name.replace('_', ' ').title()}")
        show = chronological_view(table, row_limit=600)
        st.dataframe(show, use_container_width=True, hide_index=True, height=_height(show))

    history = result.get("history")
    st.markdown("#### Complete Full Metric History — Latest Completed H1 First")
    if isinstance(history, pd.DataFrame) and not history.empty:
        history_view = chronological_view(history, row_limit=600)
        st.dataframe(history_view, use_container_width=True, hide_index=True, height=500)
        st.download_button(
            "Export Complete Full Metric History CSV",
            data=history_view.to_csv(index=False).encode("utf-8"),
            file_name="eurusd_h1_full_metric_history_current_first.csv",
            mime="text/csv",
            key="full_metric_history_export_20260618",
            use_container_width=True,
        )
    else:
        st.info("Full Metric history is unavailable for this generation.")

    factor_history = result.get("history_by_factor") or {}
    valid_factors = [
        (str(name), frame) for name, frame in (factor_history.items() if isinstance(factor_history, Mapping) else [])
        if isinstance(frame, pd.DataFrame) and not frame.empty
    ]
    if valid_factors:
        st.markdown("#### Individual Histories for All Ten Reverse-Decision Factors")
        factor_tabs = st.tabs([f"{i + 1}. {name}" for i, (name, _) in enumerate(valid_factors)])
        for tab, (name, frame) in zip(factor_tabs, valid_factors):
            with tab:
                st.dataframe(chronological_view(frame, row_limit=600), use_container_width=True, hide_index=True, height=420)

    st.markdown("#### Existing Copy and Full Export Controls")
    try:
        from tabs.eurusd_h1_matrix import _render_short_necessary_metric_copy
        _render_short_necessary_metric_copy(result, key="metric_short_copy_shared_20260618")
    except Exception as exc:
        st.caption(f"Existing short-copy control unavailable: {exc}")
    export_payload = json.dumps(_jsonable(result), ensure_ascii=False, indent=2, default=str).encode("utf-8")
    st.download_button(
        "Export Complete Full Metric Result JSON",
        data=export_payload,
        file_name="eurusd_h1_full_metric_complete.json",
        mime="application/json",
        key="full_metric_complete_export_20260618",
        use_container_width=True,
    )


__all__ = ["render_full_metric_shared"]
