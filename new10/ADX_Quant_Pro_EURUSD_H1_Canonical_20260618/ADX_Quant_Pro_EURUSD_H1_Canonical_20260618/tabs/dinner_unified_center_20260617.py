"""Lazy Dinner renderer over the single published canonical generation.

Protected calculations remain in the Settings pipeline. Dinner renders only the
compact summary by default; historical tables/charts/diagnostics import the
legacy renderers only after an explicit user gate is enabled.
"""
from __future__ import annotations

from typing import Any, Dict
import time
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import streamlit as st

from core.compact_canonical_20260619 import get_compact_summary
from core.performance_store_20260619 import record_timing
from ui.composite_summary_cards_20260619 import render_eight_cards

UNIQUE = "dinner_unified_20260617_lazy_20260619"


def _gate(label: str, key: str, help_text: str = "") -> bool:
    return bool(st.toggle(label, value=False, key=key, help=help_text or None))


def _summary() -> Dict[str, Any]:
    return get_compact_summary(st.session_state)


def _render_all_metrics(lifecycle_renderer=None) -> Dict[str, Any]:
    """Compatibility name; now renders eight HTML cards and zero st.metric."""
    del lifecycle_renderer
    summary = _summary()
    render_eight_cards(summary, location="dinner")
    return {"summary": summary, "calculation_id": summary.get("calculation_id")}


def _legacy():
    name = "tabs._dinner_unified_center_20260617_legacy_runtime"
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).with_name("dinner_unified_center_20260617_legacy.src")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def _render_powerbi_regime_chart(ns: dict) -> None:
    _legacy()._render_powerbi_regime_chart(ns)


def _render_all_tables(context: Dict[str, Any]) -> None:
    _legacy()._render_all_tables(context)


def _render_audit_copy(context: Dict[str, Any]) -> None:
    _legacy()._render_audit_copy(context)


def render_dinner_unified_center(ns: dict, prev_data=None, lifecycle_renderer=None) -> None:
    started = time.perf_counter()
    summary = _summary()
    st.markdown("#### Synchronized EURUSD H1 Decision Center")
    render_eight_cards(summary, location="dinner")
    if summary:
        st.caption(f"Canonical calculation ID: {summary.get('calculation_id', '-')} — identical to Lunch.")

    # True gates: code inside does not import or execute while closed.
    if _gate("Open / Close — Regime lifecycle details", "dinner_gate_lifecycle_20260619"):
        if callable(lifecycle_renderer):
            lifecycle_renderer()
    if _gate("Open / Close — PowerBI red / yellow / blue projection", "dinner_gate_chart_20260619"):
        _render_powerbi_regime_chart(ns)
    if _gate("Open / Close — KNN, Greedy, history and validation tables", "dinner_gate_tables_20260619"):
        from core.canonical_runtime_20260617 import shared_from_runtime, get_canonical
        context = {"shared": shared_from_runtime(st.session_state), "canonical": get_canonical(st.session_state)}
        _render_all_tables(context)
    if _gate("Open / Close — synchronized audit and copy", "dinner_gate_audit_20260619"):
        _render_audit_copy({"summary": summary})
    record_timing(st.session_state, "dinner_open", time.perf_counter() - started, calculation_id=summary.get("calculation_id"))


def render_dinner_regime_summary(ns: dict, prev_data=None, lifecycle_renderer=None) -> None:
    render_dinner_unified_center(ns, prev_data, lifecycle_renderer)


def render_dinner_combined_logic(ns: dict, prev_data=None, lifecycle_renderer=None) -> None:
    render_dinner_unified_center(ns, prev_data, lifecycle_renderer)


__all__ = [
    "render_dinner_unified_center", "render_dinner_regime_summary",
    "render_dinner_combined_logic", "_render_all_metrics",
]
