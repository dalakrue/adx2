from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

from core.ai_canonical_grounding_20260618 import build_ai_grounding, format_grounded_answer
from core.canonical_runtime_20260617 import component_freshness_guard
from core.decision_product_engine_20260617 import validate_data_quality
from core.full_metric_canonical_adapter_20260618 import _top_two_daily_candidates
from core.news_event_store_20260618 import load_recent_articles, persist_articles
from ui.table_ordering_20260618 import chronological_view, priority_view

ROOT = Path(__file__).resolve().parents[1]
PROTECTED_FULL_METRIC_SHA256 = "fe0797ab30f469f3ea748bc66a690b18a68aaf91306ac33c797bdcdcf6e60682"


def _canonical() -> dict:
    candle = "2026-06-18T08:00:00+00:00"
    return {
        "schema_version": "2.0.0",
        "run_id": "RUN-CURRENT",
        "calculation_generation": 9,
        "created_at": "2026-06-18T09:02:00+00:00",
        "expires_at": "2026-06-18T10:02:00+00:00",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "source": "TEST",
        "latest_completed_candle_time": candle,
        "data_signature": "sig-current",
        "calculation_version": "decision-product-20260617-v1",
        "calculation_status": "COMPLETED",
        "market": {"latest_completed_candle_time": candle},
        "data_quality": {"status": "PASS", "score": 99},
        "regime": {"major_regime": "BULL_NORMAL", "alpha": 1.2, "delta": 0.2},
        "forecasts": {"selected_horizon": 3, "horizons": {"3h": {"point_forecast": 1.16, "lower_bound": 1.15, "upper_bound": 1.17}}},
        "nlp": {"conflict_level": "NONE"},
        "reliability": {"score": 72},
        "final_decision": {
            "final_decision": "BUY",
            "directional_market_view": "BUY",
            "tradeability_decision": "BUY",
            "less_risky_decision": "BUY",
            "uncertainty_pct": 22,
            "error_estimate_pct": 4,
            "blocking_reasons": [],
        },
        "full_metric_direction": "BUY",
        "tradeability_decision": "BUY",
        "full_metric_decision_label": "STRONG",
        "tp_quality": 7.0,
        "exit_risk": 3.0,
        "top_two_daily_candidates": [
            {"Opportunity": 1, "Qualification Status": "QUALIFIED ENTRY", "Priority Rank": 1}
        ],
        "metadata": {},
    }


def test_current_first_regression_never_uses_old_tail_rows():
    frame = pd.DataFrame({
        "row_id": ["old", "middle", "latest"],
        "Time": ["2026-05-27T10:00:00Z", "2026-06-17T10:00:00Z", "2026-06-18T08:00:00Z"],
    })
    result = chronological_view(frame, row_limit=2, now=pd.Timestamp("2026-06-18T09:00:00Z"))
    assert result["row_id"].tolist() == ["latest", "middle"]
    # The historical defect would have returned [middle, old] by calling tail(2)
    # after a descending sort.
    assert "old" not in result["row_id"].tolist()


def test_chronological_and_priority_views_share_rows_but_not_ordering():
    frame = pd.DataFrame([
        {"row_id": "latest", "Time": "2026-06-18T08:00:00Z", "Qualification Status": "WATCH CANDIDATE", "Priority Score": 72, "Expected Value": 0.1, "Reliability %": 70, "Conflict Status": "NONE", "Exit Risk /10": 3, "Current Day": True},
        {"row_id": "qualified-old", "Time": "2026-06-18T04:00:00Z", "Qualification Status": "QUALIFIED ENTRY", "Priority Score": 75, "Expected Value": 0.2, "Reliability %": 75, "Conflict Status": "NONE", "Exit Risk /10": 2, "Current Day": True},
        {"row_id": "wait", "Time": "2026-06-18T06:00:00Z", "Qualification Status": "NO ENTRY / WAIT", "Priority Score": 90, "Expected Value": -0.1, "Reliability %": 80, "Conflict Status": "NONE", "Exit Risk /10": 1, "Current Day": True},
    ])
    chronological = chronological_view(frame, now=pd.Timestamp("2026-06-18T09:00:00Z"))
    ranked = priority_view(frame)
    assert chronological.iloc[0]["row_id"] == "latest"
    assert ranked.iloc[0]["row_id"] == "qualified-old"
    assert set(chronological["row_id"]) == set(ranked["row_id"])


def test_future_and_incomplete_h1_rows_are_not_operational():
    now = pd.Timestamp("2026-06-18T11:00:00Z")
    times = pd.to_datetime([
        "2026-06-18T07:30:00Z", "2026-06-18T08:30:00Z", "2026-06-18T09:30:00Z",
        "2026-06-18T10:30:00Z",  # still forming at 11:00
        "2026-06-18T12:30:00Z",  # future and invalid
    ])
    frame = pd.DataFrame({"time": times, "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15})
    quality, clean = validate_data_quality(frame, symbol="EURUSD", timeframe="H1", source="TEST", now=now, minimum_rows=1)
    assert clean["time"].max() == pd.Timestamp("2026-06-18T09:30:00Z")
    assert not (clean["time"] > now).any()
    assert any("Future timestamps" in warning for warning in quality.warnings)
    assert quality.status == "PASS_WITH_WARNING"
    assert not quality.blocking_reasons


def test_two_opportunity_slots_do_not_force_a_trade():
    frame = pd.DataFrame([{
        "row_id": "one", "Time": "2026-06-18T08:00:00Z", "Current Day": True,
        "Qualification Status": "NO ENTRY / WAIT", "Less Risky Bias": "WAIT",
        "Direction": "WAIT", "Entry /10": 4.0, "Master /10": 4.5, "Exit Risk /10": 7.0,
    }])
    opportunities = _top_two_daily_candidates(frame)
    assert len(opportunities) == 2
    assert all(item["Qualification Status"] != "QUALIFIED ENTRY" for item in opportunities)
    assert opportunities[1]["Qualification Status"] == "NO ENTRY / WAIT"
    assert "no trade was forced" in opportunities[1]["Blocking Reason"].lower()


def test_stale_component_forces_safe_wait_without_reversing_direction():
    canonical = _canonical()
    stale = {
        "run_id": "RUN-OLD", "calculation_generation": 8, "data_signature": "old",
        "symbol": "EURUSD", "timeframe": "H1", "latest_completed_candle_time": "2026-06-18T07:00:00+00:00",
    }
    guard = component_freshness_guard(stale, canonical)
    assert guard["ok"] is False
    assert guard["safe_action"] == "WAIT"
    assert guard["directional_view"] == "BUY"


def _news(index: int, *, now: pd.Timestamp, title: str | None = None) -> dict:
    return {
        "headline": title or f"EURUSD macro update number {index}",
        "source": "Reuters-Test",
        "publication_time": (now - pd.Timedelta(hours=index * 4)).isoformat(),
        "url": f"https://example.invalid/{index}",
        "eurusd_pair_relevance": 80,
        "nlp_direction": "BUY" if index % 2 else "WAIT",
    }


def test_news_persistence_returns_ten_real_rows_and_rejects_future(tmp_path: Path):
    db = tmp_path / "news.sqlite3"
    now = pd.Timestamp("2026-06-18T09:00:00Z")
    rows = [_news(i, now=now) for i in range(12)]
    rows.append(_news(99, now=now, title=rows[0]["headline"]))  # exact/near duplicate title
    rows.append({"headline": "Future fabricated timestamp", "source": "Test", "publication_time": (now + pd.Timedelta(hours=2)).isoformat()})
    saved = persist_articles(rows, db_path=db, now=now)
    loaded = load_recent_articles(days=10, limit=100, db_path=db, now=now)
    assert saved >= 10
    assert len(loaded) >= 10
    assert all(pd.Timestamp(row["publication_time"]) <= now + pd.Timedelta(minutes=5) for row in loaded)
    assert len({row["duplicate_identity"] for row in loaded}) == len(loaded)


def test_news_persistence_honestly_keeps_fewer_than_ten(tmp_path: Path):
    db = tmp_path / "few.sqlite3"
    now = pd.Timestamp("2026-06-18T09:00:00Z")
    persist_articles([_news(i, now=now) for i in range(3)], db_path=db, now=now)
    loaded = load_recent_articles(days=10, limit=100, db_path=db, now=now)
    assert len(loaded) == 3


def test_news_store_never_persists_api_keys(tmp_path: Path):
    db = tmp_path / "secret.sqlite3"
    now = pd.Timestamp("2026-06-18T09:00:00Z")
    row = _news(1, now=now)
    row.update({"api_key": "SUPER-SECRET", "authorization": "Bearer SUPER-SECRET"})
    persist_articles([row], db_path=db, now=now)
    with sqlite3.connect(db) as conn:
        payload = conn.execute("SELECT payload_json FROM news_event_ledger_20260618").fetchone()[0]
    assert "SUPER-SECRET" not in payload
    assert "api_key" not in payload.lower()


def test_dinner_ai_grounding_uses_required_response_order():
    canonical = _canonical()
    component = {
        "run_id": canonical["run_id"], "calculation_generation": canonical["calculation_generation"],
        "data_signature": canonical["data_signature"], "symbol": "EURUSD", "timeframe": "H1",
        "latest_completed_candle_time": canonical["latest_completed_candle_time"],
    }
    grounding = build_ai_grounding(canonical, component)
    answer = format_grounded_answer(grounding, "Local supporting explanation")
    for index, label in enumerate((
        "Current canonical decision", "Less-risky decision", "Current regime", "Entry permission",
        "Opportunity rank", "TP/SL context", "Main supporting reasons", "Main conflicts",
        "Data freshness", "Uncertainty and reliability",
    ), start=1):
        assert f"{index}. {label}" in answer
    assert grounding["less_risky_decision"] == "BUY"


def test_active_routes_restore_dinner_tabs_and_single_full_metric_renderer():
    router = (ROOT / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
    full_metric_route = (ROOT / "tabs" / "final_three_center_upgrade_20260614.py").read_text(encoding="utf-8")
    nlp = (ROOT / "ui" / "nlp_research_panel.py").read_text(encoding="utf-8")
    sidebar = (ROOT / "ui" / "liquid_menu_popup_20260615.py").read_text(encoding="utf-8")
    protected = ROOT / "tabs" / "eurusd_h1_matrix.py"
    assert '["Regime + Combined Logic", "AI Assistant"]' in router
    assert "render_full_metric_shared(ns)" in full_metric_route
    assert '_render_run_gate(ns, "metric_detail")' not in full_metric_route
    assert 'text_input("Finnhub API key"' not in nlp
    assert "render_finnhub_status_compact" in sidebar
    assert "render_finnhub_connector(location=\"settings\")" in router
    assert hashlib.sha256(protected.read_bytes()).hexdigest() == PROTECTED_FULL_METRIC_SHA256


def test_cache_and_export_contracts_are_preserved():
    cache = (ROOT / "core" / "runtime_cache_20260617.py").read_text(encoding="utf-8")
    renderer = (ROOT / "ui" / "full_metric_shared_renderer_20260618.py").read_text(encoding="utf-8")
    home = (ROOT / "tabs" / "home.py").read_text(encoding="utf-8")
    assert all(field in cache for field in ("symbol: str", "timeframe: str", "data_signature: str", "calculation_version"))
    assert "Export Complete Full Metric History CSV" in renderer
    assert "Export Complete Full Metric Result JSON" in renderer
    assert "_render_short_necessary_metric_copy" in renderer
    assert "ensure_shared_calculation_result(force=True)" not in home
