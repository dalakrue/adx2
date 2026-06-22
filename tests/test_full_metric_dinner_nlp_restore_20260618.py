from __future__ import annotations

from pathlib import Path

import pandas as pd

from ui.table_ordering_20260618 import chronological_view

ROOT = Path(__file__).resolve().parents[1]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_full_metric_history_is_current_first_and_future_safe() -> None:
    frame = pd.DataFrame(
        {
            "Time": [
                "2026-05-27 12:00:00+00:00",
                "2026-06-18 07:00:00+00:00",
                "2026-06-18 08:00:00+00:00",
                "2026-06-18 12:00:00+00:00",  # future at decision time
            ],
            "Master /10": [4.0, 5.0, 6.0, 9.0],
        }
    )
    view = chronological_view(frame, row_limit=None, now=pd.Timestamp("2026-06-18 08:15:00+00:00"))
    assert view["Time"].tolist() == [
        "2026-06-18 08:00:00+00:00",
        "2026-06-18 07:00:00+00:00",
        "2026-05-27 12:00:00+00:00",
    ]


def test_live_full_metric_renderer_is_failure_isolated_and_complete() -> None:
    src = _source("ui/full_metric_shared_renderer_20260618.py")
    assert "def _render_dataframe_safely" in src
    assert "Complete Full Metric History — Latest Completed H1 First" in src
    assert '"direction", "direction_table"' in src
    assert '"hold", "hold_table"' in src
    assert '"exit", "exit_table"' in src
    assert '"tp", "tp_table"' in src
    assert "row_limit=None" in src
    assert "render_existing_regime_inner_section(result)" in src


def test_lunch_uses_one_shared_full_metric_renderer() -> None:
    src = _source("ui/lunch_restored.py")
    assert "render_full_metric_shared(ns, result=result)" in src
    assert "Complete Current-H1-First View" in src


def test_dinner_navigation_and_router_restore_ai_assistant() -> None:
    nav = _source("ui/antd_navigation_20260615.py")
    router = _source("tabs/antd_page_router_20260615.py")
    assert 'DINNER_CHILDREN = ["Regime + Combined Logic", "AI Assistant"]' in nav
    assert 'options = ["Regime + Combined Logic", "AI Assistant"]' in router
    assert "AI Assistant — Dinner" in router
    assert "_render_chatgpt_style_ai" in router


def test_research_nlp_has_no_duplicate_password_input_and_renders_top_workspace() -> None:
    research = _source("tabs/research.py")
    legacy_auth = _source("tabs/final_research_projection_auth_sync_20260612.py")
    assert "render_nlp_research_workspace(selected)" in research
    assert "build_all_research_pack_for_settings" in research
    assert 'if not bool(st.session_state.get("research_run_calculate", False))' not in research
    assert "Legacy NLP source snapshot" in research
    assert "FMP API backup" not in legacy_auth
    assert "st.text_input" not in legacy_auth


def test_public_rss_parser_can_supply_ten_real_rankable_rows(monkeypatch) -> None:
    import requests
    from ui.nlp_research_panel import _fetch_public_rss_news

    items = "".join(
        f"<item><title>EURUSD market article {i}</title>"
        f"<pubDate>Thu, 18 Jun 2026 {i:02d}:00:00 GMT</pubDate>"
        f"<link>https://example.test/{i}</link>"
        f"<description>ECB Fed USD EUR impact article {i}</description></item>"
        for i in range(12)
    )
    payload = f"<?xml version='1.0'?><rss><channel>{items}</channel></rss>".encode()

    class Response:
        content = payload

        @staticmethod
        def raise_for_status() -> None:
            return None

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: Response())
    rows = _fetch_public_rss_news(limit=10)
    assert len(rows) == 10
    assert all(row["headline"].startswith("EURUSD market article") for row in rows)
    assert all(row["source"] for row in rows)
    assert all(row["url"].startswith("https://example.test/") for row in rows)
