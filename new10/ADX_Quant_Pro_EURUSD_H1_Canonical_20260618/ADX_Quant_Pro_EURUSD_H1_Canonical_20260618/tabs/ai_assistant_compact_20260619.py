"""Compact, submit-driven AI Assistant UI.

Opening this tab reads only the fact pack created by Run Calculation.  The
legacy analysis engine is imported only after the user submits a question.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from typing import Any, Mapping

import streamlit as st

from core.compact_canonical_20260619 import compact_ai_context, get_ai_fact_pack
from core.performance_store_20260619 import append_ai_message, load_ai_messages

CACHE_KEY = "ai_answer_cache_20260619"
LATEST_KEY = "ai_latest_messages_20260619"
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


def _local_fact_answer(question: str, pack: Mapping[str, Any]) -> str:
    q = _normalize(question)
    scores = pack.get("protected_scores") if isinstance(pack.get("protected_scores"), Mapping) else {}
    proj = pack.get("central_projection") if isinstance(pack.get("central_projection"), Mapping) else {}
    unc = pack.get("uncertainty") if isinstance(pack.get("uncertainty"), Mapping) else {}
    nlp = pack.get("nlp_summary") if isinstance(pack.get("nlp_summary"), Mapping) else {}
    priority = pack.get("priority") if isinstance(pack.get("priority"), Mapping) else {}
    if any(x in q for x in ("projection", "price", "h+", "target", "forecast")):
        return (f"Current close: {pack.get('current_close')}. H+1: {proj.get('h1')}, H+3: {proj.get('h3')}, "
                f"H+6: {proj.get('h6')}, band {proj.get('lower_band')}–{proj.get('upper_band')}. "
                f"Projection confidence is {proj.get('projection_confidence')}%.")
    if any(x in q for x in ("regime", "transition", "alpha", "delta")):
        return (f"Directional regime: {pack.get('directional_regime')}; volatility regime: {pack.get('volatility_regime')}. "
                f"Transition risk is {pack.get('transition_risk')}% with window {pack.get('transition_window')}. "
                f"Reliability: {pack.get('reliability')}%.")
    if any(x in q for x in ("news", "nlp", "event")):
        return (f"NLP direction: {nlp.get('direction')}; reliability: {nlp.get('reliability')}%; "
                f"conflict: {nlp.get('conflict')}; top event: {nlp.get('highest_ranked_news')}; "
                f"event risk: {nlp.get('event_risk_condition')}.")
    if any(x in q for x in ("priority", "best hour", "opportunity", "knn", "greedy")):
        return (f"KNN priority: {priority.get('knn_priority')}; Greedy priority: {priority.get('greedy_priority')}; "
                f"best entry hour: {priority.get('best_entry_hour')}; second-best: {priority.get('second_best_entry_hour')}; "
                f"quality: {priority.get('opportunity_quality')}.")
    return (f"Canonical decision: {pack.get('current_decision')} with direction {pack.get('direction')} and less-risky bias "
            f"{pack.get('less_risky_bias')}. Master {scores.get('master')}/10, Entry {scores.get('entry')}/10, "
            f"Hold {scores.get('hold')}/10, TP {scores.get('tp')}/10, Exit Risk {scores.get('exit_risk')}/10. "
            f"Combined uncertainty is {unc.get('combined')}%. Main reason: {pack.get('main_reason')}.")


def _legacy_answer(question: str, pack: Mapping[str, Any], mode: str) -> str:
    """Import the existing engine only after Submit; fall back without losing UI."""
    if mode == "Compact facts":
        return _local_fact_answer(question, pack)
    try:
        from tabs import ai_assistant_lite as legacy
        context = compact_ai_context(pack)
        for name in ("generate_ai_answer", "_generate_answer", "answer_question"):
            fn = getattr(legacy, name, None)
            if callable(fn):
                try:
                    answer = fn(question, context)
                except TypeError:
                    answer = fn(question=question, context=context)
                if answer:
                    return str(answer)
    except Exception as exc:
        return _local_fact_answer(question, pack) + f"\n\nAdvanced engine fallback: {exc}"
    return _local_fact_answer(question, pack)


def render_compact_ai_assistant() -> None:
    pack = get_ai_fact_pack(st.session_state)
    st.caption("Reads the compact canonical fact pack. No analysis or history query runs until Send is pressed.")
    if not pack:
        st.info("Run Calculation in Settings before using the AI Assistant.")
        return
    calc_id = str(pack.get("calculation_id") or "")
    phone = bool(st.session_state.get("phone_mode", False))
    messages = st.session_state.get(LATEST_KEY)
    if not isinstance(messages, list):
        messages = load_ai_messages(calc_id, limit=6 if phone else 20)
        st.session_state[LATEST_KEY] = messages
    shown = messages[-6:] if phone else messages[-20:]
    for item in shown:
        role = str(item.get("role", "assistant"))
        with st.chat_message(role if role in {"user", "assistant"} else "assistant"):
            st.markdown(str(item.get("content", "")))

    with st.form("compact_ai_form_20260619", clear_on_submit=True):
        mode = st.selectbox("Answer mode", ["Compact facts", "Existing advanced analysis"], key="ai_mode_20260619")
        question = st.text_input("Ask about the synchronized EURUSD H1 result", key="ai_question_20260619")
        submitted = st.form_submit_button("Send / Analyze", use_container_width=True)
    if not submitted or not question.strip():
        return

    key = answer_cache_key(calc_id, question, mode)
    cache = _bounded_cache()
    answer = cache.get(key)
    if answer is None:
        answer = _legacy_answer(question, pack, mode)
        # Reject an answer produced for a stale generation.
        current_pack = get_ai_fact_pack(st.session_state)
        if str(current_pack.get("calculation_id") or "") != calc_id:
            st.warning("A newer calculation replaced this request. Submit the question again for the current generation.")
            return
        cache[key] = answer
        cache.move_to_end(key)
        while len(cache) > MAX_CACHE:
            cache.popitem(last=False)
        st.session_state[CACHE_KEY] = cache
    pair = [{"role": "user", "content": question}, {"role": "assistant", "content": str(answer)}]
    messages.extend(pair)
    st.session_state[LATEST_KEY] = messages[-20:]
    for item in pair:
        append_ai_message(calc_id, item["role"], item["content"])
    with st.chat_message("assistant"):
        st.markdown(str(answer))


__all__ = ["render_compact_ai_assistant", "answer_cache_key", "MAX_CACHE"]
