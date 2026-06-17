"""Research-area UI for the shared NLP and data-mining pipeline.

All heavy actions are explicitly button-gated.  The panel only adds evidence to
Research and never writes the central regime or trading decision.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence

import pandas as pd
import streamlit as st

from core.nlp_pipeline import NLPConfig, build_article_intelligence, map_market_direction
from core.nlp_models import (
    abstractive_summary, finbert_inference, fit_lda_topic_model, infer_lda_topics,
    predict_linear_svm, train_linear_svm, tune_svm_optuna, tune_lda_optuna,
    tune_decision_thresholds_optuna,
)
from core.nlp_event_response import (
    aggregate_event_responses, calculate_nlp_reliability, compare_with_shared_outputs,
    construct_event_response_dataset, error_analysis,
)

STATE_KEY = "nlp_market_intelligence_result"
CONFIG_KEY = "nlp_market_intelligence_config"


def _safe_shared() -> Dict[str, Any]:
    try:
        from core.canonical_runtime_20260617 import shared_from_runtime
        return shared_from_runtime(st.session_state) or {}
    except Exception:
        return {}


def _get_ohlc() -> pd.DataFrame:
    for key in ("dv_pp_df", "lunch_5layer_powerbi_df", "last_df", "ohlc_df"):
        obj = st.session_state.get(key)
        if isinstance(obj, pd.DataFrame) and not obj.empty:
            return obj.copy()
    return pd.DataFrame()


def _existing_articles() -> List[Dict[str, Any]]:
    rows = st.session_state.get("finnhub_news_cache", [])
    if isinstance(rows, list) and rows:
        return [x for x in rows if isinstance(x, dict)]
    candidates = []
    for key in ("news_nlp_knn_greedy_pack_20260612", "research_pack_20260612", "final_synced_research_merge_pack_20260612"):
        obj = st.session_state.get(key)
        if not isinstance(obj, dict):
            continue
        for path in (("news", "table"), ("nlp", "table"), ("news_nlp", "table")):
            cur: Any = obj
            for part in path:
                cur = cur.get(part) if isinstance(cur, dict) else None
            if isinstance(cur, pd.DataFrame) and not cur.empty:
                for _, row in cur.head(150).iterrows():
                    candidates.append({
                        "headline": row.get("Title", row.get("headline", row.get("title", ""))),
                        "summary": row.get("Summary", row.get("summary", row.get("Static Impact", ""))),
                        "source": row.get("Source", row.get("source", "Existing cache")),
                        "url": row.get("URL", row.get("url", "")),
                        "datetime": row.get("Time", row.get("timestamp", row.get("datetime"))),
                    })
    return candidates


def _config_from_state() -> NLPConfig:
    raw = st.session_state.get(CONFIG_KEY, {})
    if not isinstance(raw, dict):
        raw = {}
    allowed = NLPConfig.__dataclass_fields__.keys()
    values = {k: raw[k] for k in allowed if k in raw}
    try:
        return NLPConfig(**values)
    except Exception:
        return NLPConfig()


def _config_controls() -> NLPConfig:
    current = _config_from_state()
    with st.expander("Open / Close — NLP thresholds and decay", expanded=False):
        a, b, c = st.columns(3)
        duplicate = a.slider("Duplicate similarity", 0.80, 0.99, float(current.duplicate_threshold), 0.01, key="nlp_cfg_duplicate")
        related = b.slider("Related-update similarity", 0.55, 0.89, float(current.related_threshold), 0.01, key="nlp_cfg_related")
        pair = c.slider("Minimum EURUSD relevance", 0.0, 80.0, float(current.minimum_pair_relevance), 2.0, key="nlp_cfg_pair")
        d, e, f = st.columns(3)
        buy = d.slider("BUY score threshold", 5.0, 60.0, float(current.buy_threshold), 1.0, key="nlp_cfg_buy")
        sell_abs = e.slider("SELL score threshold magnitude", 5.0, 60.0, abs(float(current.sell_threshold)), 1.0, key="nlp_cfg_sell")
        decay = f.slider("General decay hours", 4.0, 72.0, float(current.general_decay_hours), 2.0, key="nlp_cfg_decay")
    cfg = NLPConfig(
        duplicate_threshold=duplicate if 'duplicate' in locals() else current.duplicate_threshold,
        related_threshold=related if 'related' in locals() else current.related_threshold,
        buy_threshold=buy if 'buy' in locals() else current.buy_threshold,
        sell_threshold=-(sell_abs if 'sell_abs' in locals() else abs(current.sell_threshold)),
        minimum_pair_relevance=pair if 'pair' in locals() else current.minimum_pair_relevance,
        max_features=current.max_features,
        ngram_min=current.ngram_min,
        ngram_max=current.ngram_max,
        general_decay_hours=decay if 'decay' in locals() else current.general_decay_hours,
        macro_decay_hours=current.macro_decay_hours,
        central_bank_decay_hours=current.central_bank_decay_hours,
        commentary_decay_hours=current.commentary_decay_hours,
    )
    st.session_state[CONFIG_KEY] = cfg.to_dict()
    return cfg


def _fetch_if_connected(force: bool) -> List[Dict[str, Any]]:
    try:
        from core.finnhub_connector import fetch_market_news
        rows = fetch_market_news("forex", force=force)
        if rows:
            return rows
    except Exception:
        pass
    return _existing_articles()


def _merge_optional_models(df: pd.DataFrame, *, use_finbert: bool, cfg: NLPConfig) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy().reset_index(drop=True)
    topic = infer_lda_topics(out["model_text"].astype(str).tolist())
    if len(topic) == len(out) and "topic_id" in topic.columns:
        for col in topic.columns:
            out[col] = topic[col].values
    svm = predict_linear_svm(out["model_text"].astype(str).tolist())
    if len(svm) == len(out) and "svm_label" in svm.columns:
        for col in svm.columns:
            out[col] = svm[col].values
    if use_finbert:
        eligible = out.index[(out["duplicate_status"] != "DUPLICATE") & (out["eurusd_pair_relevance"] >= 20)].tolist()[:16]
        if eligible:
            fin = finbert_inference(out.loc[eligible, "display_text"].astype(str).tolist())
            if len(fin) == len(eligible) and "sentiment_label" in fin.columns:
                for local_idx, row_idx in enumerate(eligible):
                    for col in fin.columns:
                        out.loc[row_idx, col] = fin.iloc[local_idx][col]
                    # Re-map the relative EUR-vs-USD direction using FinBERT's
                    # signed sentiment. Positive USD remains bearish EURUSD;
                    # positive EUR remains bullish EURUSD.
                    positive = float(out.loc[row_idx].get("sentiment_positive_probability", 0.0) or 0.0)
                    negative = float(out.loc[row_idx].get("sentiment_negative_probability", 0.0) or 0.0)
                    out.loc[row_idx, "sentiment_score"] = positive - negative
                    remapped = map_market_direction(out.loc[row_idx].to_dict(), cfg)
                    for col, value in remapped.items():
                        out.loc[row_idx, col] = value
    return out


def run_nlp_analysis(*, force_news: bool = False, use_finbert: bool = False) -> Dict[str, Any]:
    cfg = _config_from_state()
    articles = _fetch_if_connected(force_news)
    table = build_article_intelligence(articles, cfg)
    table = _merge_optional_models(table, use_finbert=use_finbert, cfg=cfg)
    shared = _safe_shared()
    # Attach only contemporaneous central context as descriptive fields. These
    # values are not text-model features and never change the central engine.
    if isinstance(table, pd.DataFrame) and not table.empty:
        current = shared.get("current", {}) if isinstance(shared, dict) else {}
        regime = shared.get("regime", {}) if isinstance(shared, dict) else {}
        decision = shared.get("decision", {}) if isinstance(shared, dict) else {}
        table["current_regime"] = str(regime.get("current") or current.get("regime") or "-")
        table["central_decision_at_event"] = str(decision.get("central_decision") or current.get("decision") or "WAIT")
        table["powerbi_direction_at_event"] = str((shared.get("powerbi", {}) if isinstance(shared, dict) else {}).get("direction") or current.get("prediction_direction") or "WAIT")
    ohlc = _get_ohlc()
    event_rows = construct_event_response_dataset(table, ohlc, atr_threshold=0.35)
    aggregate = aggregate_event_responses(event_rows, minimum_sample_size=12)
    enriched = []
    for _, row in table.iterrows():
        item = row.to_dict()
        agreement = compare_with_shared_outputs(item, shared)
        hist_sample = 0
        hist_acc = 0.0
        topic_sample = 0
        topic_acc = 0.0
        if isinstance(aggregate, pd.DataFrame) and not aggregate.empty:
            match = aggregate[
                (aggregate.get("event_type", pd.Series(index=aggregate.index, dtype=str)).astype(str) == str(item.get("event_type"))) &
                (aggregate.get("nlp_direction", pd.Series(index=aggregate.index, dtype=str)).astype(str) == str(item.get("nlp_direction"))) &
                (aggregate.get("horizon", pd.Series("3H", index=aggregate.index)).astype(str) == "3H")
            ]
            if not match.empty:
                hist_sample = int(match.iloc[0].get("sample_size", 0) or 0)
                hist_acc = float(match.iloc[0].get("historical_directional_accuracy", 0) or 0)
            topic_match = aggregate[
                (aggregate.get("group_dimension", pd.Series(index=aggregate.index, dtype=str)).astype(str) == "topic_name") &
                (aggregate.get("group_value", pd.Series(index=aggregate.index, dtype=str)).astype(str) == str(item.get("topic_name"))) &
                (aggregate.get("horizon", pd.Series("3H", index=aggregate.index)).astype(str) == "3H")
            ]
            if not topic_match.empty:
                topic_sample = int(topic_match.iloc[0].get("sample_size", 0) or 0)
                topic_acc = float(topic_match.iloc[0].get("historical_directional_accuracy", 0) or 0)
        reliability = calculate_nlp_reliability(item, agreement, historical_sample_size=hist_sample, historical_accuracy=hist_acc)
        item.update(agreement)
        item.update(reliability)
        item["historical_sample_size"] = hist_sample
        item["historical_accuracy"] = hist_acc
        item["topic_historical_sample_size"] = topic_sample
        item["topic_historical_accuracy"] = topic_acc if topic_sample >= 12 else None
        item["nlp_rank_score"] = abs(float(item.get("nlp_direction_score", 0) or 0)) * float(item.get("nlp_reliability_score", 0) or 0) / 100.0
        enriched.append(item)
    table = pd.DataFrame(enriched)
    if not table.empty:
        table = table.sort_values(["nlp_rank_score", "timestamp"], ascending=[False, False], na_position="last").reset_index(drop=True)
        table["rank"] = range(1, len(table) + 1)
    errors = error_analysis(event_rows)
    top = table.iloc[0].to_dict() if not table.empty else {}
    reaction_expectations: Dict[str, Any] = {}
    if top and isinstance(aggregate, pd.DataFrame) and not aggregate.empty:
        for horizon in (1, 2, 3, 6):
            match = aggregate[
                (aggregate.get("event_type", pd.Series(index=aggregate.index, dtype=str)).astype(str) == str(top.get("event_type"))) &
                (aggregate.get("nlp_direction", pd.Series(index=aggregate.index, dtype=str)).astype(str) == str(top.get("nlp_direction"))) &
                (aggregate.get("horizon", pd.Series(index=aggregate.index, dtype=str)).astype(str) == f"{horizon}H")
            ]
            if not match.empty and int(match.iloc[0].get("sample_size", 0) or 0) >= 12:
                reaction_expectations[f"reaction_expectation_{horizon}h"] = f"Median {float(match.iloc[0].get('median_movement_pips', 0) or 0):.2f} pips • n={int(match.iloc[0].get('sample_size',0) or 0)}"
            else:
                reaction_expectations[f"reaction_expectation_{horizon}h"] = "Insufficient historical sample"
    summary = {
        "status": "READY" if top else "NO ARTICLES",
        "article_count": int(len(table)),
        "non_duplicate_count": int((table.get("duplicate_status", pd.Series(dtype=str)) != "DUPLICATE").sum()) if not table.empty else 0,
        "latest_rank_1_news": top.get("title", "No relevant news"),
        "news_time": top.get("timestamp"),
        "source": top.get("source", "-"),
        "topic": top.get("topic_name", top.get("event_type", "OTHER")),
        "topic_confidence": top.get("topic_probability", 0),
        "eur_relevance": top.get("eur_relevance_score", 0),
        "usd_relevance": top.get("usd_relevance_score", 0),
        "pair_relevance": top.get("eurusd_pair_relevance", 0),
        "sentiment": top.get("sentiment_label", "NEUTRAL"),
        "nlp_direction": top.get("nlp_direction", "WAIT"),
        "direction_score": top.get("nlp_direction_score", 0),
        "reliability": top.get("nlp_reliability_score", 0),
        "reliability_label": top.get("nlp_reliability_label", "UNRELIABLE"),
        "conflict_level": top.get("nlp_conflict_level", "LOW"),
        "less_risky_decision": top.get("less_risky_nlp_decision", "WAIT"),
        "historical_sample_size": top.get("historical_sample_size", 0),
        "historical_accuracy": top.get("historical_accuracy", 0),
        "error_risk": top.get("nlp_error_risk", 100),
        "extractive_summary": top.get("extractive_summary", ""),
        "built_at": str(pd.Timestamp.now()),
        "central_decision_unchanged": True,
        "central_regime_unchanged": True,
        **reaction_expectations,
    }
    result = {
        "summary": summary,
        "articles": table,
        "event_response": event_rows,
        "aggregates": aggregate,
        "error_analysis": errors,
        "config": cfg.to_dict(),
        "shared_signature": shared.get("signature") if isinstance(shared, dict) else None,
    }
    st.session_state[STATE_KEY] = result
    # Persist deduplicated event-response memory without storing API keys.
    try:
        import hashlib
        from core.prediction_ledger_20260617 import get_prediction_ledger
        memory_rows = []
        source_rows = event_rows if isinstance(event_rows, pd.DataFrame) and not event_rows.empty else table
        if isinstance(source_rows, pd.DataFrame):
            current_regime = str((shared.get("regime") or {}).get("current") or (shared.get("current") or {}).get("regime") or "UNKNOWN") if isinstance(shared, dict) else "UNKNOWN"
            ad = (shared.get("regime_alpha_delta") or {}) if isinstance(shared, dict) else {}
            for _, row in source_rows.iterrows():
                raw_id = str(row.get("article_id") or row.get("id") or row.get("url") or "")
                if not raw_id:
                    raw_id = str(row.get("source") or "") + "|" + str(row.get("timestamp") or "") + "|" + str(row.get("title") or row.get("headline") or "")
                article_id = hashlib.sha256(raw_id.encode("utf-8", errors="ignore")).hexdigest()
                memory_rows.append({
                    "article_id": article_id,
                    "source": row.get("source"),
                    "publication_time": row.get("timestamp"),
                    "retrieval_time": pd.Timestamp.now(tz="UTC"),
                    "event_type": row.get("event_type"),
                    "entities": row.get("entities", row.get("named_entities", [])),
                    "currency_relevance": row.get("eurusd_pair_relevance", row.get("nlp_pair_relevance")),
                    "sentiment": row.get("sentiment_score"),
                    "importance": row.get("importance_score", row.get("event_importance")),
                    "source_reliability": row.get("source_reliability", row.get("nlp_source_reliability", 60)),
                    "duplicate_cluster_id": row.get("duplicate_cluster_id", row.get("duplicate_of")),
                    "regime_at_publication": row.get("current_regime", current_regime),
                    "session_at_publication": row.get("market_session"),
                    "alpha": ad.get("regime_alpha", ad.get("alpha")),
                    "delta": ad.get("regime_delta", ad.get("delta")),
                    "price_at_publication": row.get("event_close"),
                    "return_1h": row.get("future_return_1h"),
                    "return_2h": row.get("future_return_2h"),
                    "return_3h": row.get("future_return_3h"),
                    "return_6h": row.get("future_return_6h"),
                    "mfe": row.get("maximum_favourable_excursion"),
                    "mae": row.get("maximum_adverse_excursion"),
                    "finnhub_available": bool(st.session_state.get("finnhub_connected", False)),
                    "reaction_status": "SETTLED" if pd.notna(row.get("future_return_6h")) else "PENDING",
                })
        result["ledger_event_rows_saved"] = get_prediction_ledger().save_nlp_events(memory_rows)
    except Exception as exc:
        result["ledger_event_rows_saved"] = 0
        result["ledger_event_memory_warning"] = str(exc)
    # NLP evidence is staged in its own existing key. It becomes part of the
    # next successful Settings canonical generation; renderers never republish.
    return result


def _metric_grid(summary: Dict[str, Any]) -> None:
    r1 = st.columns(4)
    r1[0].metric("NLP Direction", summary.get("nlp_direction", "WAIT"), f"Score {float(summary.get('direction_score', 0) or 0):.1f}")
    r1[1].metric("Reliability", f"{float(summary.get('reliability', 0) or 0):.1f}%", summary.get("reliability_label", "UNRELIABLE"))
    r1[2].metric("Conflict", summary.get("conflict_level", "LOW"), f"Safer {summary.get('less_risky_decision', 'WAIT')}")
    r1[3].metric("Pair Relevance", f"{float(summary.get('pair_relevance', 0) or 0):.1f}%", f"EUR {float(summary.get('eur_relevance',0) or 0):.0f} / USD {float(summary.get('usd_relevance',0) or 0):.0f}")
    r2 = st.columns(4)
    r2[0].metric("Topic", summary.get("topic", "OTHER"), f"{float(summary.get('topic_confidence',0) or 0):.1f}%")
    r2[1].metric("Historical Sample", int(summary.get("historical_sample_size", 0) or 0), f"Accuracy {float(summary.get('historical_accuracy',0) or 0):.1f}%")
    r2[2].metric("Error Risk", f"{float(summary.get('error_risk', 100) or 100):.1f}%")
    r2[3].metric("Articles", int(summary.get("article_count", 0) or 0), f"Unique {int(summary.get('non_duplicate_count',0) or 0)}")


def _display_latest(result: Dict[str, Any]) -> None:
    summary = result.get("summary", {}) if isinstance(result, dict) else {}
    _metric_grid(summary)
    st.markdown("#### Latest rank-1 EURUSD news")
    st.dataframe(pd.DataFrame([{
        "News": summary.get("latest_rank_1_news", "No relevant news"),
        "Time": summary.get("news_time", "-"),
        "Source": summary.get("source", "-"),
        "Sentiment": summary.get("sentiment", "NEUTRAL"),
        "Direction": summary.get("nlp_direction", "WAIT"),
        "Reliability": summary.get("reliability", 0),
        "Conflict": summary.get("conflict_level", "LOW"),
    }]), use_container_width=True, hide_index=True)
    st.dataframe(pd.DataFrame([{
        "1H reaction expectation": summary.get("reaction_expectation_1h", "Insufficient historical sample"),
        "3H reaction expectation": summary.get("reaction_expectation_3h", "Insufficient historical sample"),
        "6H reaction expectation": summary.get("reaction_expectation_6h", "Insufficient historical sample"),
        "Error risk": summary.get("error_risk", 100),
    }]), use_container_width=True, hide_index=True)
    if summary.get("extractive_summary"):
        st.info(summary.get("extractive_summary"))


def _render_error_analysis(result: Dict[str, Any]) -> None:
    errors = result.get("error_analysis", {}) if isinstance(result, dict) else {}
    if not errors or not errors.get("ok"):
        st.info((errors or {}).get("message", "Run analysis with matched price history to build validation metrics."))
        return
    metrics = {k: v for k, v in errors.items() if k not in {"confusion_matrix", "performance_by_group", "performance_by_horizon", "ok"} and not isinstance(v, (pd.DataFrame, dict))}
    st.dataframe(pd.DataFrame([{"Metric": k, "Value": v} for k, v in metrics.items()]), use_container_width=True, hide_index=True)
    cm = errors.get("confusion_matrix")
    if isinstance(cm, pd.DataFrame):
        st.markdown("#### Confusion matrix")
        st.dataframe(cm, use_container_width=True)
    horizon = errors.get("performance_by_horizon")
    if isinstance(horizon, pd.DataFrame) and not horizon.empty:
        st.markdown("#### Performance by 1H / 3H / 6H horizon")
        st.dataframe(horizon, use_container_width=True, hide_index=True)
    groups = errors.get("performance_by_group", {})
    if isinstance(groups, dict) and groups:
        with st.expander("Open / Close — Error performance by topic, regime, session, volatility and confidence", expanded=False):
            for name, frame in groups.items():
                if isinstance(frame, pd.DataFrame) and not frame.empty:
                    st.markdown(f"##### {str(name).replace('_', ' ').title()}")
                    st.dataframe(frame, use_container_width=True, hide_index=True)


def _render_training(result: Dict[str, Any]) -> None:
    event_rows = result.get("event_response", pd.DataFrame()) if isinstance(result, dict) else pd.DataFrame()
    articles = result.get("articles", pd.DataFrame()) if isinstance(result, dict) else pd.DataFrame()
    st.caption("Training uses a chronological 80/20 split. Future returns are targets only and never enter text features.")
    a, b, c = st.columns(3)
    if a.button("Train / Refresh LDA", key="research_train_lda_shared", use_container_width=True):
        source = event_rows if isinstance(event_rows, pd.DataFrame) and not event_rows.empty else articles
        outcome = fit_lda_topic_model(source.get("model_text", pd.Series(dtype=str)).astype(str).tolist(), n_topics=10)
        st.session_state["nlp_last_lda_training"] = {k: v for k, v in outcome.items() if k not in {"model", "vectorizer"}}
        st.rerun()
    if b.button("Train TF-IDF + Linear SVM", key="research_train_svm_shared", use_container_width=True):
        outcome = train_linear_svm(event_rows, artifact_name="svm_direction")
        st.session_state["nlp_last_svm_training"] = {k: v for k, v in outcome.items() if k not in {"model", "vectorizer"}}
        st.rerun()
    if c.button("Tune TF-IDF + SVM", key="research_tune_svm_shared", use_container_width=True):
        with st.spinner("Running bounded time-based SVM tuning…"):
            outcome = tune_svm_optuna(event_rows, trials=15)
        st.session_state["nlp_last_optuna_tuning"] = outcome
        st.rerun()
    d, e = st.columns(2)
    if d.button("Tune LDA topics", key="research_tune_lda_shared", use_container_width=True):
        source = event_rows if isinstance(event_rows, pd.DataFrame) and not event_rows.empty else articles
        with st.spinner("Running bounded held-out LDA tuning…"):
            outcome = tune_lda_optuna(source.get("model_text", pd.Series(dtype=str)).astype(str).tolist(), trials=12)
        st.session_state["nlp_last_lda_tuning"] = outcome
        st.rerun()
    if e.button("Tune NLP decision thresholds", key="research_tune_decision_shared", use_container_width=True):
        with st.spinner("Running bounded time-based threshold tuning…"):
            outcome = tune_decision_thresholds_optuna(event_rows, trials=18)
        st.session_state["nlp_last_decision_tuning"] = outcome
        st.rerun()
    status_rows = [
        {"Component": "LDA", "Status": json.dumps(st.session_state.get("nlp_last_lda_training", {"message": "Not trained"}), default=str)[:400]},
        {"Component": "Linear SVM", "Status": json.dumps(st.session_state.get("nlp_last_svm_training", {"message": "Not trained"}), default=str)[:400]},
        {"Component": "SVM Optuna", "Status": json.dumps(st.session_state.get("nlp_last_optuna_tuning", {"message": "Not run"}), default=str)[:400]},
        {"Component": "LDA Optuna", "Status": json.dumps(st.session_state.get("nlp_last_lda_tuning", {"message": "Not run"}), default=str)[:400]},
        {"Component": "Decision-threshold Optuna", "Status": json.dumps(st.session_state.get("nlp_last_decision_tuning", {"message": "Not run"}), default=str)[:400]},
    ]
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)


def render_nlp_research_workspace(selected: str = "NLP") -> None:
    cfg = _config_controls()
    current = st.session_state.get(STATE_KEY, {})
    if selected == "NLP":
        # Restored directly inside the existing Research > NLP inner tab.
        # Finnhub remains optional; all local/cached NLP controls below work disconnected.
        with st.expander("Open / Close — Finnhub API Connector for NLP", expanded=True):
            try:
                from core.finnhub_connector import render_finnhub_connector
                render_finnhub_connector(location="research_nlp")
            except Exception as exc:
                st.warning(f"Finnhub connector is unavailable; local NLP remains active: {exc}")
        controls = st.columns([1.2, 1.2, 1, 1])
        use_finbert = controls[0].toggle("Use FinBERT", value=False, key="research_use_finbert_on_analyze")
        if controls[1].button("Analyze cached/local news", key="research_analyze_cached_news", use_container_width=True):
            with st.spinner("Normalizing, deduplicating and scoring EURUSD news…"):
                current = run_nlp_analysis(force_news=False, use_finbert=use_finbert)
        if controls[2].button("Refresh Finnhub + Analyze", key="research_refresh_finnhub_news", use_container_width=True):
            with st.spinner("Refreshing Finnhub and analyzing relevant non-duplicate news…"):
                current = run_nlp_analysis(force_news=True, use_finbert=use_finbert)
        if controls[3].button("Generate abstractive summary", key="research_abstractive_summary", use_container_width=True):
            table = current.get("articles", pd.DataFrame()) if isinstance(current, dict) else pd.DataFrame()
            if isinstance(table, pd.DataFrame) and not table.empty:
                st.session_state["nlp_abstractive_summary"] = abstractive_summary(str(table.iloc[0].get("display_text", "")))
            else:
                st.session_state["nlp_abstractive_summary"] = {"ok": False, "message": "Analyze at least one article first."}
            st.rerun()
        if not current:
            st.info("Finnhub is optional. Connect it in the sidebar, or analyze existing cached/local news. The app continues working when disconnected.")
        else:
            _display_latest(current)
            table = current.get("articles", pd.DataFrame())
            with st.expander("Open / Close — Detailed normalized NLP table", expanded=False):
                if isinstance(table, pd.DataFrame) and not table.empty:
                    columns = [c for c in [
                        "rank", "timestamp", "source", "title", "event_type", "topic_name", "topic_probability",
                        "eur_relevance_score", "usd_relevance_score", "eurusd_pair_relevance", "duplicate_status",
                        "similarity_to_previous", "novelty_score", "sentiment_label", "sentiment_confidence",
                        "svm_label", "svm_confidence", "nlp_direction", "nlp_direction_score", "nlp_reliability_score",
                        "nlp_conflict_level", "less_risky_nlp_decision", "extractive_summary",
                    ] if c in table.columns]
                    st.dataframe(table[columns], use_container_width=True, hide_index=True, height=460)
                else:
                    st.info("No normalized articles are available.")
            abs_result = st.session_state.get("nlp_abstractive_summary")
            if isinstance(abs_result, dict):
                with st.expander("Open / Close — Optional abstractive summary", expanded=False):
                    if abs_result.get("ok"):
                        summary = current.get("summary", {})
                        st.write(f"**Event:** {summary.get('topic','OTHER')}")
                        st.write(f"**What happened:** {abs_result.get('summary','')}")
                        st.write(f"**Affected currency:** EUR and/or USD according to relevance scores")
                        st.write(f"**Likely EURUSD pressure:** {summary.get('nlp_direction','WAIT')}")
                        st.write(f"**Reason:** Relative EUR-vs-USD sentiment and event relevance")
                        st.write(f"**Risk:** {summary.get('conflict_level','LOW')} conflict; model evidence cannot override the central decision")
                    else:
                        st.info(abs_result.get("message", "Abstractive model unavailable; extractive summary remains active."))
    elif selected == "Data Mining":
        if not current:
            st.info("Run NLP analysis first to create the historical event-response dataset.")
            return
        _render_training(current)
        with st.expander("Open / Close — Historical event-response rows", expanded=False):
            event_rows = current.get("event_response", pd.DataFrame())
            st.dataframe(event_rows if isinstance(event_rows, pd.DataFrame) else pd.DataFrame(), use_container_width=True, hide_index=True, height=420)
        with st.expander("Open / Close — Event-response aggregates", expanded=True):
            aggregate = current.get("aggregates", pd.DataFrame())
            st.dataframe(aggregate if isinstance(aggregate, pd.DataFrame) else pd.DataFrame(), use_container_width=True, hide_index=True)
    else:
        if not current:
            st.info("Run NLP analysis to calculate validation and error-analysis metrics.")
            return
        _render_error_analysis(current)
