"""Lexical, deterministic intent detection for the read-only AI assistant."""
from __future__ import annotations
import re
from typing import Any

# More-specific intents come first so a question about TP, broker time, or a
# forecast does not collapse into the same generic decision response.
INTENTS = {
    "market_time": ("broker time", "myanmar time", "latest candle", "current time", "what time", "clock", "fresh", "stale"),
    "tp_sl_guidance": ("take profit", "stop loss", "tp", "sl", "target", "exit price"),
    "exit_guidance": ("should i exit", "exit now", "close now", "close trade", "hold or exit", "take profit now"),
    "entry_guidance": ("should i buy", "should i sell", "buy now", "sell now", "enter now", "entry now", "open trade", "entry"),
    "price_forecast": ("predicted price", "future price", "price path", "power bi", "powerbi", "forecast", "projection", "band"),
    "risk_position_sizing": ("position size", "lot size", "margin", "risk", "position", "lot", "sizing"),
    "priority_ranking": ("best hour", "priority", "rank", "knn", "greedy", "opportunity"),
    "regime_explanation": ("major regime", "regime", "alpha", "delta", "transition", "trend"),
    "reliability_explanation": ("reliability", "confidence", "uncertainty", "calibration", "trust", "accuracy"),
    "similar_day": ("similar day", "historical match", "analogue", "pattern"),
    "historical_comparison": ("last 25", "history", "historical", "compare", "previous"),
    "system_health": ("system health", "connector", "data quality", "generation", "ready", "status", "error"),
    "decision_explanation": ("current decision", "less risky", "decision", "buy", "sell", "wait", "entry", "why"),
}

SOURCE_MAP = {
    "market_time": ("identity", "validation", "connector"),
    "tp_sl_guidance": ("projection", "risk", "decision", "warnings"),
    "exit_guidance": ("decision", "risk", "projection", "reliability", "scores", "warnings"),
    "entry_guidance": ("decision", "scores", "regime", "reliability", "priority", "warnings"),
    "price_forecast": ("projection", "forecast", "reliability", "validation"),
    "decision_explanation": ("decision", "scores", "regime", "reliability", "warnings"),
    "regime_explanation": ("regime", "reliability", "history"),
    "reliability_explanation": ("reliability", "uncertainty", "validation", "evidence"),
    "similar_day": ("similar_day", "history", "reliability"),
    "historical_comparison": ("history", "decision", "regime", "evidence"),
    "priority_ranking": ("priority", "decision", "regime", "reliability"),
    "risk_position_sizing": ("risk", "decision", "scores", "warnings"),
    "system_health": ("identity", "validation", "connector", "evidence", "warnings"),
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+_-]+", str(text or "").lower()))


def detect_intent(question: str) -> dict[str, Any]:
    q = str(question or "").strip().lower()
    tokens = _tokens(q)
    scored: list[tuple[int, int, str]] = []
    for order, (intent, phrases) in enumerate(INTENTS.items()):
        score = 0
        specificity = 0
        for phrase in phrases:
            phrase_l = phrase.lower()
            if " " in phrase_l:
                if phrase_l in q:
                    score += 5
                    specificity += len(phrase_l)
            elif phrase_l in tokens:
                score += 2
                specificity += len(phrase_l)
        # Earlier specific intents win exact ties.
        scored.append((score, specificity - order, intent))
    score, _, intent = max(scored, default=(0, 0, "decision_explanation"))
    if score <= 0:
        intent = "decision_explanation"
    return {
        "intent": intent,
        "score": score,
        "required_sources": SOURCE_MAP[intent],
        "normalized_question": " ".join(q.split()),
    }


__all__ = ["detect_intent", "INTENTS", "SOURCE_MAP"]
