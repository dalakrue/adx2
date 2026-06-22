"""On-demand controls for the single canonical copy/export service."""
from __future__ import annotations

from typing import Any, Mapping, MutableMapping

import streamlit as st

from core.canonical_runtime_20260617 import get_canonical
from core.compact_canonical_20260619 import get_compact_summary
from services.canonical_exports import (
    all_text,
    build_short_payload,
    generation_identity,
    machine_json,
    payload_stats,
)


def _m(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _cache_key(kind: str, location: str) -> str:
    # Shared text identity by generation; locations only affect widget keys.
    return f"canonical_copy_{kind}_payload_20260621"


def render_canonical_copy_export(
    *,
    state: MutableMapping[str, Any] | None = None,
    plan: Mapping[str, Any] | None = None,
    readiness: Mapping[str, Any] | None = None,
    location: str = "lunch",
    compact: bool = False,
) -> None:
    state = state if state is not None else st.session_state
    canonical = get_canonical(state)
    summary = get_compact_summary(state)
    plan = dict(plan or state.get("position_sizing_plan_20260619") or {})
    readiness = dict(readiness or state.get("system_readiness_snapshot_20260621") or {})
    if not canonical:
        st.info("Copy/export becomes available after a successful Run Calculation.")
        return
    identity = generation_identity(canonical)
    if not compact:
        st.markdown("#### Copy and export — current canonical generation")

    cols = st.columns(3)
    prepare_short = cols[0].button("📋 Prepare Short", key=f"{location}_canonical_short_prepare_20260621", use_container_width=True)
    prepare_all = cols[1].button("📋 Prepare All", key=f"{location}_canonical_all_prepare_20260621", use_container_width=True)
    prepare_json = cols[2].button("⬇️ Prepare JSON", key=f"{location}_canonical_json_prepare_20260621", use_container_width=True)

    try:
        if prepare_short:
            text, stats = build_short_payload(canonical, summary, plan)
            state[_cache_key("short", location)] = {"identity": identity, "text": text, "stats": stats.__dict__}
        if prepare_all:
            # Generated only on explicit press and cached by canonical identity.
            text = all_text(canonical, summary, plan, readiness)
            state[_cache_key("all", location)] = {"identity": identity, "text": text, "stats": payload_stats(text).__dict__}
        if prepare_json:
            text = machine_json(canonical, summary, plan)
            state["canonical_export_json_payload_20260621"] = {"identity": identity, "text": text}
    except Exception as exc:
        st.error(f"Copy/export preparation failed safely: {type(exc).__name__}: {exc}")

    for kind, label in (("short", "Copy prepared Short"), ("all", "Copy prepared All")):
        item = state.get(_cache_key(kind, location))
        if not isinstance(item, Mapping) or item.get("identity") != identity:
            continue
        text = str(item.get("text") or "")
        stats = _m(item.get("stats")) or payload_stats(text).__dict__
        st.caption(f"{label}: {stats.get('characters', len(text)):,} characters · {stats.get('lines', len(text.splitlines()))} lines · ~{stats.get('estimated_tokens', 0):,} estimated tokens")
        from ui.copy_tools import central_copy_button
        central_copy_button(label, text, f"{location}_canonical_copy_{kind}_{identity[:16]}", show_fallback=True)

    export_item = state.get("canonical_export_json_payload_20260621")
    if isinstance(export_item, Mapping) and export_item.get("identity") == identity:
        st.download_button(
            "Download complete canonical generation JSON",
            str(export_item.get("text") or "").encode("utf-8"),
            file_name=f"eurusd_h1_generation_{canonical.get('calculation_generation')}.json",
            mime="application/json",
            use_container_width=True,
            key=f"{location}_canonical_export_download_20260621",
        )


def render_direct_canonical_copy_buttons(
    *,
    state: MutableMapping[str, Any] | None = None,
    location: str = "menu",
    compact: bool = True,
    include_full: bool = True,
) -> None:
    """Render real one-click Copy Short / Copy Full buttons for the menu rail.

    Unlike the larger export panel, this prepares only the current published
    canonical text and immediately hands it to the central clipboard component.
    No calculation, model, history scan, or external API is started here.
    """
    state = state if state is not None else st.session_state
    canonical = get_canonical(state)
    if not canonical:
        st.button("📋 Copy Short", key=f"{location}_copy_short_unavailable_20260622", disabled=True, use_container_width=True)
        if include_full:
            st.button("📋 Copy Full", key=f"{location}_copy_full_unavailable_20260622", disabled=True, use_container_width=True)
        st.caption("Copy becomes active after the one Settings calculation publishes a completed generation.")
        return
    summary = get_compact_summary(state)
    plan = dict(state.get("position_sizing_plan_20260619") or {})
    readiness = dict(state.get("system_readiness_snapshot_20260621") or {})
    identity = generation_identity(canonical) or "current"
    try:
        short_payload, short_stats = build_short_payload(canonical, summary, plan)
        from ui.copy_tools import central_copy_button
        if include_full:
            full_payload = all_text(canonical, summary, plan, readiness)
            full_stats = payload_stats(full_payload)
            if compact:
                st.caption(f"Short: {short_stats.lines} lines · ~{short_stats.estimated_tokens:,} tokens")
                central_copy_button("Copy Short", short_payload, f"{location}_direct_short_{identity[:16]}", height=70, show_fallback=False)
                st.caption(f"Full: {full_stats.lines} lines · ~{full_stats.estimated_tokens:,} tokens")
                central_copy_button("Copy Full", full_payload, f"{location}_direct_full_{identity[:16]}", height=70, show_fallback=False)
            else:
                cols = st.columns(2)
                with cols[0]:
                    st.caption(f"Short: {short_stats.lines} lines · ~{short_stats.estimated_tokens:,} tokens")
                    central_copy_button("Copy Short", short_payload, f"{location}_direct_short_{identity[:16]}", height=70, show_fallback=False)
                with cols[1]:
                    st.caption(f"Full: {full_stats.lines} lines · ~{full_stats.estimated_tokens:,} tokens")
                    central_copy_button("Copy Full", full_payload, f"{location}_direct_full_{identity[:16]}", height=70, show_fallback=False)
        else:
            st.caption(f"Short: {short_stats.lines} lines · ~{short_stats.estimated_tokens:,} tokens")
            central_copy_button("Copy Short", short_payload, f"{location}_direct_short_{identity[:16]}", height=70, show_fallback=False)
    except Exception as exc:
        st.caption(f"Copy unavailable safely: {type(exc).__name__}: {str(exc)[:90]}")


__all__ = ["render_canonical_copy_export", "render_direct_canonical_copy_buttons"]
