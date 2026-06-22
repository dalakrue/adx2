"""Compact, submit-driven grounded AI Assistant UI.

Opening the field reads only the compact published fact pack. Evidence retrieval
and local analysis execute only after Send / Analyze is pressed.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections import OrderedDict
from typing import Any, Mapping

import pandas as pd
import streamlit as st

from core.compact_canonical_20260619 import get_ai_fact_pack
from core.performance_store_20260619 import append_ai_message, load_ai_messages

# Compatibility marker only: ``from tabs import ai_assistant_lite as legacy``.
# The legacy assistant is intentionally not imported; Field 5 uses the bounded
# grounded pipeline only after Send / Analyze.

CACHE_KEY = "ai_answer_cache_20260619"
LATEST_KEY = "ai_latest_messages_20260619"
LATEST_CALC_KEY = "ai_latest_messages_calculation_id_20260622"
MAX_CACHE = 32


def _normalize(question: str) -> str:
    return re.sub(r"\s+", " ", str(question or "").strip().lower())


def answer_cache_key(calculation_id: str, question: str, mode: str) -> str:
    raw = f"{calculation_id}|{_normalize(question)}|{mode}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _bounded_cache() -> OrderedDict:
    raw = st.session_state.get(CACHE_KEY)
    cache = raw if isinstance(raw, OrderedDict) else OrderedDict(raw or {}) if isinstance(raw, dict) else OrderedDict()
    while len(cache) > MAX_CACHE:
        cache.popitem(last=False)
    return cache


def _redact_sensitive_text(value: str) -> str:
    """Keep question history useful without persisting API keys or bearer tokens."""
    text = str(value or "")
    patterns = (
        r"(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+",
        r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+",
        r"\bsk-[A-Za-z0-9_-]{12,}\b",
    )
    for pattern in patterns:
        text = re.sub(pattern, lambda m: (m.group(1) if m.lastindex else "") + "[REDACTED]", text)
    return text


def _recover_fact_pack(state: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    """Recover the newest valid read-only AI fact pack without calculating."""
    pack = get_ai_fact_pack(state)
    fallback_pack = dict(pack) if isinstance(pack, Mapping) and pack else {}
    try:
        from core.canonical_runtime_20260617 import get_canonical
        from core.compact_canonical_20260619 import publish_compact_runtime
        canonical = get_canonical(state)
        if canonical and fallback_pack:
            canonical_id = str(canonical.get("canonical_calculation_id") or canonical.get("run_id") or "")
            pack_id = str(fallback_pack.get("calculation_id") or "")
            canonical_time = str(canonical.get("latest_completed_candle_time") or "")
            pack_time = str(fallback_pack.get("latest_completed_h1") or "")
            if canonical_id == pack_id and (not pack_time or pack_time == canonical_time):
                return fallback_pack
        # Legacy aliases may still hold the last completed generation after an
        # optional display/publication step failed. Choose the newest *valid*
        # candidate, then restore the runtime pointer before rebuilding the pack.
        if not canonical:
            from core.canonical_runtime_20260617 import (
                CANONICAL_KEY, LAST_VALID_KEY, validate_canonical_result,
            )
            candidates: list[tuple[int, pd.Timestamp, dict[str, Any]]] = []
            for key in (
                "last_valid_canonical_decision_result_20260617",
                "canonical_decision_result_20260617",
                "canonical_decision_result",
                "canonical_result_20260617",
                "canonical_result",
            ):
                candidate = state.get(key) if isinstance(state, Mapping) else None
                if not isinstance(candidate, Mapping) or not candidate:
                    continue
                candidate_dict = dict(candidate)
                valid, _ = validate_canonical_result(candidate_dict)
                if not valid:
                    continue
                try:
                    generation = int(candidate_dict.get("calculation_generation") or 0)
                except Exception:
                    generation = 0
                created = pd.to_datetime(candidate_dict.get("created_at"), errors="coerce", utc=True)
                created = pd.Timestamp.min.tz_localize("UTC") if pd.isna(created) else pd.Timestamp(created)
                candidates.append((generation, created, candidate_dict))
            if candidates:
                canonical = max(candidates, key=lambda item: (item[0], item[1]))[2]
                try:
                    state[CANONICAL_KEY] = canonical  # type: ignore[index]
                    state[LAST_VALID_KEY] = canonical  # type: ignore[index]
                    state["ai_canonical_runtime_recovered_20260622"] = True  # type: ignore[index]
                except Exception:
                    pass
        if isinstance(canonical, Mapping) and canonical:
            shared = state.get("shared_calculation_result_20260615") if isinstance(state, Mapping) else None
            _, rebuilt = publish_compact_runtime(state, canonical, shared if isinstance(shared, Mapping) else None)  # type: ignore[arg-type]
            if isinstance(rebuilt, dict) and rebuilt:
                return rebuilt
    except Exception:
        pass
    if fallback_pack:
        return fallback_pack
    # Disk recovery survives a connector disconnect, rejected attempted run, or
    # Streamlit state reset. It reads only the newest compact published summary.
    try:
        from core.performance_store_20260619 import load_latest_summary
        from core.compact_canonical_20260619 import SUMMARY_KEY, FACT_PACK_KEY, ACTIVE_CALCULATION_ID_KEY
        summary, persisted = load_latest_summary()
        if isinstance(persisted, dict) and persisted:
            try:
                state[SUMMARY_KEY] = summary if isinstance(summary, dict) else {}  # type: ignore[index]
                state[FACT_PACK_KEY] = persisted  # type: ignore[index]
                state[ACTIVE_CALCULATION_ID_KEY] = str(persisted.get("calculation_id") or summary.get("calculation_id") or "")  # type: ignore[index]
                state["ai_fact_pack_recovered_from_disk_20260622"] = True  # type: ignore[index]
            except Exception:
                pass
            return persisted
    except Exception:
        pass
    return {}


def _offline_fact_pack(state: Mapping[str, Any]) -> dict[str, Any]:
    """Non-trading diagnostic context so Field 5 never becomes a dead panel."""
    try:
        from core.market_time_freshness_20260622 import market_time_snapshot
        freshness = market_time_snapshot(state, query_mt5=False)  # type: ignore[arg-type]
    except Exception:
        freshness = {}
    status = state.get("settings_run_status_20260617")
    errors = list(status.get("errors") or []) if isinstance(status, Mapping) else []
    return {
        "calculation_id": "OFFLINE-DIAGNOSTIC",
        "symbol": str(state.get("symbol") or "EURUSD"),
        "timeframe": str(state.get("timeframe") or "H1"),
        "current_decision": "NO PUBLISHED GENERATION",
        "direction": "WAIT",
        "tradeability": "WAIT",
        "less_risky_bias": "WAIT",
        "directional_regime": "UNKNOWN",
        "latest_completed_h1": freshness.get("latest_loaded_time"),
        "validation_status": {"status": "OFFLINE DIAGNOSTIC"},
        "main_reason": errors[-1] if errors else "No completed canonical generation is currently available.",
        "blocking_reasons": errors[-5:],
        "fact_pack_source": "offline diagnostic only; no trading values fabricated",
        "offline_diagnostic": True,
        "freshness": freshness,
    }


def _offline_answer(question: str, pack: Mapping[str, Any]) -> dict[str, Any]:
    fresh = pack.get("freshness") if isinstance(pack.get("freshness"), Mapping) else {}
    blockers = list(pack.get("blocking_reasons") or [])
    answer = (
        "### Offline diagnostic mode\n"
        f"- Your question: {question.strip()}\n"
        f"- Connector/source: {fresh.get('source', 'DISCONNECTED')}\n"
        f"- Latest loaded candle: {fresh.get('latest_loaded_display', 'No loaded candle')}\n"
        f"- Feed freshness: {fresh.get('status', 'NO DATA')}\n"
        f"- Last run issue: {(blockers[-1] if blockers else pack.get('main_reason'))}\n\n"
        "The assistant is running, but it will not invent BUY/SELL, price, regime, or confidence values without a completed canonical generation. "
        "Use the single Settings → Run Calculation + Open Lunch button; after any rejected attempt, the last valid persisted generation is restored automatically when available."
    )
    return {"answer": answer, "status": "OFFLINE_DIAGNOSTIC", "generation_id": "OFFLINE-DIAGNOSTIC", "evidence": []}


def _append_ai_history(calc_id: str, question: str, answer: str, mode: str, pack: Mapping[str, Any]) -> None:
    """Persist grounded Q/A evidence outside browser state; never persist secrets."""
    try:
        from core.canonical_runtime_20260617 import get_canonical
        from core.history_identity_20260620 import canonical_history_identity
        from core.history_evidence_store_20260620 import append_history_bundle
        canonical = get_canonical(st.session_state)
        canonical = dict(canonical) if isinstance(canonical, Mapping) else {
            "canonical_calculation_id": calc_id, "run_id": calc_id, "symbol": "EURUSD",
            "timeframe": "H1", "latest_completed_candle_time": pack.get("latest_completed_h1"),
        }
        interaction_id = uuid.uuid4().hex
        safe_question = _redact_sensitive_text(question)
        safe_answer = _redact_sensitive_text(answer)
        current_id = str(pack.get("calculation_id") or calc_id)
        consistent = current_id == calc_id
        unsupported = "fallback" in safe_answer.lower() or not bool(pack)
        identity = canonical_history_identity(
            canonical, condition=str(mode), settled_status="OBSERVED",
            logic_version="ai-grounding-history-20260620-v1",
        )
        common = {**identity, "payload": {"interaction_id": interaction_id}}
        evidence_names = [
            name for name in ("protected_scores", "central_projection", "priority", "nlp_summary", "uncertainty")
            if pack.get(name) not in (None, {}, [])
        ]
        bundle = {
            "ai_assistant_history": [{
                **common, "metric_name": "grounded_question_answer",
                "value_text": "GROUNDED" if pack else "UNSUPPORTED",
                "payload": {
                    "interaction_id": interaction_id, "question": safe_question, "answer": safe_answer,
                    "mode": mode, "canonical_calculation_id_used": calc_id,
                    "grounding_status": "GROUNDED" if pack else "UNSUPPORTED",
                    "unsupported_evidence_warning": unsupported,
                    "answer_consistency_status": "CONSISTENT" if consistent else "STALE",
                },
            }],
            "ai_evidence_reference_history": [
                {**common, "condition": name, "metric_name": "evidence_reference",
                 "value_text": name, "payload": {"interaction_id": interaction_id, "table_or_fact_pack_key": name}}
                for name in evidence_names
            ],
            "ai_answer_consistency_history": [{
                **common, "metric_name": "answer_consistency",
                "value_numeric": 1 if consistent else 0,
                "value_text": "CONSISTENT" if consistent else "STALE",
                "payload": {
                    "interaction_id": interaction_id, "unsupported_evidence_warning": unsupported,
                    "calculation_id_at_answer": calc_id, "calculation_id_after_answer": current_id,
                },
            }],
        }
        append_history_bundle(bundle)
    except Exception as exc:
        st.session_state["ai_history_append_error_20260620"] = repr(exc)


def render_compact_ai_assistant() -> None:
    pack = get_ai_fact_pack(st.session_state) or _recover_fact_pack(st.session_state)
    st.caption("Reads the compact canonical fact pack. No analysis or history query runs until Send is pressed.")
    if not pack:
        # Last-resort recovery from a completed canonical generation. This does
        # not calculate; it only republishes the compact AI projection.
        pack = _recover_fact_pack(st.session_state)
    if not pack:
        pack = _offline_fact_pack(st.session_state)
        st.warning("No completed canonical generation is available, so the assistant is in safe offline diagnostic mode. The chat remains active and does not fabricate trading values.")
    elif bool(st.session_state.get("ai_fact_pack_recovered_from_disk_20260622") or st.session_state.get("ai_canonical_runtime_recovered_20260622")):
        st.success("AI Assistant restored the newest valid published generation. A failed refresh or disconnected API did not disable the assistant.")
    calc_id = str(pack.get("calculation_id") or "OFFLINE-DIAGNOSTIC")
    phone = bool(st.session_state.get("phone_mode", False))
    messages = st.session_state.get(LATEST_KEY)
    if not isinstance(messages, list) or str(st.session_state.get(LATEST_CALC_KEY) or "") != calc_id:
        messages = [] if pack.get("offline_diagnostic") else load_ai_messages(calc_id, limit=6 if phone else 20)
        st.session_state[LATEST_KEY] = messages
        st.session_state[LATEST_CALC_KEY] = calc_id
    shown = messages[-6:] if phone else messages[-20:]
    for item in shown:
        role = str(item.get("role", "assistant"))
        with st.chat_message(role if role in {"user", "assistant"} else "assistant"):
            st.markdown(str(item.get("content", "")))

    with st.form("compact_ai_form_20260619", clear_on_submit=True):
        mode = st.selectbox("Resource route", ["Automatic bounded route", "Simple evidence route", "Complex evidence route"], key="ai_mode_20260619")
        question = st.text_input("Ask about the synchronized EURUSD H1 result", key="ai_question_20260619")
        submitted = st.form_submit_button("Send / Analyze", use_container_width=True)
    if not submitted or not question.strip():
        return

    key = answer_cache_key(calc_id, question, mode)
    cache = _bounded_cache()
    cached = cache.get(key)
    if isinstance(cached, Mapping):
        result = dict(cached)
        answer = str(result.get("answer") or "")
    else:
        if pack.get("offline_diagnostic"):
            result = _offline_answer(question, pack)
        else:
            from core.canonical_runtime_20260617 import get_canonical
            from core.compact_canonical_20260619 import get_compact_summary
            from core.ai_grounded_pipeline_20260621 import answer_question
            canonical = get_canonical(st.session_state)
            summary = get_compact_summary(st.session_state)
            plan = st.session_state.get("position_sizing_plan_20260619") or {}
            result = answer_question(question, canonical=canonical, summary=summary, plan=plan, state=st.session_state)
        answer = str(result.get("answer") or "")
        # Reject an answer produced for a replaced generation, except the safe
        # diagnostic context which has no mutable market generation.
        current_pack = _recover_fact_pack(st.session_state)
        if not pack.get("offline_diagnostic") and str(current_pack.get("calculation_id") or "") != calc_id:
            st.warning("A newer calculation replaced this request. Submit the question again for the current generation.")
            return
        cache[key] = result
        cache.move_to_end(key)
        while len(cache) > MAX_CACHE:
            cache.popitem(last=False)
        st.session_state[CACHE_KEY] = cache
    pair = [{"role": "user", "content": question}, {"role": "assistant", "content": str(answer)}]
    messages.extend(pair)
    st.session_state[LATEST_KEY] = messages[-20:]
    if not pack.get("offline_diagnostic"):
        for item in pair:
            append_ai_message(calc_id, item["role"], item["content"])
        _append_ai_history(calc_id, question, str(answer), str(result.get("status") or mode), pack)
    with st.chat_message("assistant"):
        st.markdown(str(answer))


__all__ = ["render_compact_ai_assistant", "answer_cache_key", "_recover_fact_pack", "MAX_CACHE"]
