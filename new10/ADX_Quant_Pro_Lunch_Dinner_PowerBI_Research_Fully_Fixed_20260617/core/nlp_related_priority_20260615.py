"""Low-RAM 10-day related-news priority table for NLP and AI Assistant.

The table reads only existing cached/local/Finnhub results.  It never performs a
network request on render and never trains a model.  News is normalized,
deduplicated, filtered to the most recent ten days, then ranked with the
project's deterministic KNN-style and Greedy evidence scores.
"""
from __future__ import annotations

import json
import math
import re
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

MARKET_WORDS = {
    "eurusd", "eur", "euro", "eurozone", "ecb", "usd", "dollar", "fed", "fomc", "yield", "treasury",
    "cpi", "ppi", "nfp", "jobs", "unemployment", "inflation", "pmi", "gdp", "rate", "rates", "cut", "hike",
    "risk", "war", "conflict", "oil", "liquidity", "volatility", "breakout", "reversal", "safe", "haven",
}
PROTECT_WORDS = {
    "risk", "warning", "conflict", "volatile", "volatility", "drawdown", "reversal", "shock", "uncertain",
    "weak", "danger", "compression", "spread", "safe", "haven", "geopolitical", "war", "miss", "hot",
}
BUY_WORDS = {"euro", "eurozone", "ecb", "hawkish", "pmi", "inflation", "hot", "growth", "beat", "stronger"}
SELL_WORDS = {"dollar", "usd", "fed", "treasury", "yield", "nfp", "safe", "haven", "geopolitical", "risk", "stronger"}
MAX_CACHED_ROWS = 2000  # hard phone-safety cap; the normal 10-day window is shown in full


def _tokens(text: Any) -> set[str]:
    s = re.sub(r"[^a-z0-9_/ -]+", " ", str(text or "").lower())
    return {w.strip(" /-") for w in s.split() if len(w.strip(" /-")) >= 3}


def _float(v: Any, default: float = 0.0) -> float:
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def _row_text(row: Dict[str, Any]) -> str:
    keys = [
        "Title", "title", "headline", "Headline", "summary", "description",
        "extractive_summary", "display_text", "Static Impact", "News Direction", "Source", "source",
    ]
    return " ".join(str(row.get(k, "")) for k in keys)


def _timestamp(row: Dict[str, Any]) -> pd.Timestamp:
    value = None
    for key in (
        "timestamp", "Published", "published", "publishedDate", "publication_time",
        "datetime", "time", "Time", "date", "Date", "retrieval_time",
    ):
        candidate = row.get(key)
        if candidate is not None and str(candidate).strip() not in {"", "None", "NaT", "nan"}:
            value = candidate
            break
    try:
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            unit = "ms" if abs(float(value)) > 10_000_000_000 else "s"
            ts = pd.to_datetime(value, unit=unit, errors="coerce", utc=True)
        else:
            ts = pd.to_datetime(value, errors="coerce", utc=True)
        return pd.Timestamp(ts) if not pd.isna(ts) else pd.NaT
    except Exception:
        return pd.NaT


def _extract_news_rows(obj: Any, depth: int = 0) -> List[Dict[str, Any]]:
    if depth > 5 or obj is None:
        return []
    rows: List[Dict[str, Any]] = []
    if isinstance(obj, pd.DataFrame):
        rows.extend(obj.head(MAX_CACHED_ROWS).to_dict("records"))
    elif isinstance(obj, list):
        rows.extend([x for x in obj[:MAX_CACHED_ROWS] if isinstance(x, dict)])
    elif isinstance(obj, dict):
        title = obj.get("title") or obj.get("headline") or obj.get("Title") or obj.get("Headline")
        if title:
            rows.append(obj)
        for key in (
            "news_table", "table", "news", "rows", "articles", "event_response",
            "news_nlp", "nlp", "result", "data", "items",
        ):
            if key in obj:
                rows.extend(_extract_news_rows(obj.get(key), depth + 1))
    return rows[:MAX_CACHED_ROWS]


def collect_existing_news_rows(extra: Any = None, *, window_days: int = 10) -> List[Dict[str, Any]]:
    """Collect all cached news and keep every unique article in the last N days."""
    rows: List[Dict[str, Any]] = []
    rows.extend(_extract_news_rows(extra))
    for key in (
        "nlp_market_intelligence_result",
        "finnhub_news_cache",
        "nlp_related_news_priority_table_20260615",
        "dv_news_nlp_pack_20260612",
        "news_nlp_knn_greedy_pack_20260612",
        "research_pack_20260612",
        "final_synced_research_merge_pack_20260612",
        "final_merged_intelligence_pack_20260612",
        "related_news_rows", "news_rows", "nlp_ranked_news_df", "news_nlp_ranked_df",
        "news_nlp_table", "nlp_news_df", "latest_news_df",
    ):
        rows.extend(_extract_news_rows(st.session_state.get(key)))

    now = pd.Timestamp.now(tz="UTC")
    cutoff = now - pd.Timedelta(days=max(1, int(window_days or 10)))
    seen: set[str] = set()
    dated: List[Dict[str, Any]] = []
    undated: List[Dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("Title") or raw.get("title") or raw.get("headline") or raw.get("Headline") or "").strip()
        if not title:
            continue
        source = str(raw.get("Source") or raw.get("source") or raw.get("provider") or "").strip().lower()
        ts = _timestamp(raw)
        fingerprint = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()[:180] + "|" + source
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        row = dict(raw)
        row["_normalized_title"] = title
        row["_published_utc"] = ts.isoformat() if not pd.isna(ts) else None
        if pd.isna(ts):
            undated.append(row)
        elif cutoff <= ts <= now + pd.Timedelta(hours=2):
            dated.append(row)

    # A truthful fallback keeps legacy undated cached stories visible only when
    # no timestamped ten-day rows exist; the UI labels them as timestamp unknown.
    selected = dated if dated else undated
    selected.sort(key=lambda r: str(r.get("_published_utc") or ""), reverse=True)
    return selected[:MAX_CACHED_ROWS]


def _score(row: Dict[str, Any], query: str = "") -> Dict[str, Any]:
    text = _row_text(row)
    tks, qks = _tokens(text), _tokens(query)
    title = str(row.get("_normalized_title") or row.get("Title") or row.get("title") or row.get("headline") or row.get("Headline") or text[:120] or "-")[:180]
    source = str(row.get("Source") or row.get("source") or row.get("provider") or "-")[:60]
    ts = _timestamp(row)
    now = pd.Timestamp.now(tz="UTC")
    age_hours: Optional[float] = None
    if not pd.isna(ts):
        age_hours = max(0.0, (now - ts).total_seconds() / 3600.0)

    relevance = (100.0 * len(tks & qks) / max(1, len(qks))) if qks else (55.0 + min(30.0, len(tks & MARKET_WORDS) * 6.0))
    market_impact = min(100.0, len(tks & MARKET_WORDS) * 10.0 + abs(_float(row.get("EUR Impact")) - _float(row.get("USD Impact"))) * 18.0)
    protect = min(100.0, len(tks & PROTECT_WORDS) * 13.0 + (18.0 if str(row.get("News Sync", row.get("news_relationship_to_powerbi", ""))).upper() == "CONFLICT" else 0.0))
    freshness = 46.0 if age_hours is None else max(18.0, 100.0 - min(82.0, age_hours / 240.0 * 82.0))
    reliability = min(100.0, _float(row.get("nlp_reliability_score"), 55.0 + min(25.0, len(tks & MARKET_WORDS) * 3.0)))

    buy_pressure = len(tks & BUY_WORDS) + max(0.0, _float(row.get("EUR Impact")))
    sell_pressure = len(tks & SELL_WORDS) + max(0.0, _float(row.get("USD Impact")))
    direction = str(row.get("News Direction") or row.get("news_direction") or row.get("nlp_direction") or "").upper()
    if direction not in {"BUY", "SELL", "WAIT"}:
        direction = "BUY" if buy_pressure > sell_pressure + .7 else "SELL" if sell_pressure > buy_pressure + .7 else "WAIT"

    ideal = [100.0, 100.0, 100.0, 85.0, 85.0]
    vec = [relevance, market_impact, protect, freshness, reliability]
    dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, ideal)))
    knn = max(0.0, 100.0 - dist / math.sqrt(5 * 100.0**2) * 100.0)
    greedy = relevance * .25 + market_impact * .30 + protect * .24 + freshness * .08 + reliability * .13
    final = knn * .52 + greedy * .48

    impact_label = "High impact" if market_impact >= 70 else "Medium impact" if market_impact >= 45 else "Low impact"
    protect_label = "Wait / reduce risk" if protect >= 70 else "Confirm before entry" if protect >= 45 else "Normal protection"
    improve = "Improves sync" if direction != "WAIT" and market_impact >= 45 else "Improves protection" if protect >= 45 else "Awareness only"
    related = ", ".join(sorted(list((tks & qks) or (tks & MARKET_WORDS)))[:9]) or "-"
    published = ts.strftime("%Y-%m-%d %H:%M UTC") if not pd.isna(ts) else "Timestamp unknown"
    age = "Unknown" if age_hours is None else (f"{age_hours/24:.1f}d" if age_hours >= 24 else f"{age_hours:.1f}h")
    return {
        "Priority": 0,
        "Published": published,
        "Age": age,
        "Title": title,
        "Source": source,
        "Direction": direction,
        "KNN Score": round(knn, 2),
        "Greedy Score": round(greedy, 2),
        "Final Score": round(final, 2),
        "Impact": impact_label,
        "Protect": protect_label,
        "How it improves/protects": improve,
        "Related Tokens": related,
    }


@st.cache_data(ttl=300, show_spinner=False, max_entries=12)
def _cached_table(rows_json: str, query: str, top_n: int) -> pd.DataFrame:
    try:
        rows = json.loads(rows_json)
    except Exception:
        rows = []
    scored = [_score(r, query) for r in rows if isinstance(r, dict)]
    columns = ["Priority", "Published", "Age", "Title", "Source", "Direction", "KNN Score", "Greedy Score", "Final Score", "Impact", "Protect", "How it improves/protects", "Related Tokens"]
    if not scored:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(scored)
    df = df.sort_values(["Final Score", "KNN Score", "Greedy Score", "Published"], ascending=[False, False, False, False])
    limit = int(top_n or 0)
    if limit > 0:
        df = df.head(limit)
    df = df.reset_index(drop=True)
    df["Priority"] = df.index + 1
    return df[columns]


def render_related_news_priority_table(
    extra_rows: Any = None, *, query: str = "", top_n: int = 0,
    window_days: int = 10, title: str = "📰 Related News Priority — KNN + Greedy",
) -> pd.DataFrame:
    rows = collect_existing_news_rows(extra_rows, window_days=window_days)
    rows_json = json.dumps(rows, ensure_ascii=False, default=str)
    df = _cached_table(rows_json, str(query or ""), int(top_n or 0))
    st.markdown(f"#### {title}")
    st.caption(
        f"Full cached news window: every deduplicated article from the last {int(window_days)} days (phone-safety cap {MAX_CACHED_ROWS:,}). Priority is ascending (1 = strongest). "
        "KNN, Greedy, impact and protection are display-ranking evidence only. Rendering never calls the API or retrains a model."
    )
    if df.empty:
        st.info("No cached news from the last 10 days is available. Refresh Finnhub + Analyze once, or analyze cached/local news; the table will then retain the full ten-day window.")
        return df
    unknown = int((df["Published"] == "Timestamp unknown").sum()) if "Published" in df.columns else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("10-Day News Rows", len(df))
    c2.metric("Strongest Priority", int(df["Priority"].min()))
    c3.metric("Timestamp Coverage", f"{len(df)-unknown}/{len(df)}")
    height = min(620, max(300, 34 * min(len(df), 16) + 78))
    st.dataframe(df, use_container_width=True, hide_index=True, height=height)
    st.session_state["nlp_related_news_priority_table_20260615"] = df
    st.session_state["nlp_related_news_priority_window_days_20260617"] = int(window_days)
    return df
