from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_settings_restores_market_timer_and_logout_sections():
    source = (ROOT / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
    assert "Open / Close — Twelve Data + MT5 Market Connector" in source
    assert '_render_connector(key_prefix="settings_market_20260619", show_secret_inputs=False)' in source
    assert "Open / Close — Trade Timer / Sound Alert" in source
    assert '_render_timer(key_prefix="settings_timer_20260619")' in source
    assert "Open / Close — Account / Logout" in source
    assert '_render_ui_and_account(key_prefix="settings_account_20260619")' in source


def test_mobile_api_paste_fields_are_present():
    router = (ROOT / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
    finnhub = (ROOT / "core" / "finnhub_connector.py").read_text(encoding="utf-8")
    assert "Twelve Data API key — mobile paste box" in router
    assert "-webkit-touch-callout: default" in router
    assert "Finnhub API key — mobile paste box" in finnhub
    assert 'if str(location).lower() == "settings"' in finnhub


def test_drawer_and_settings_controls_use_separate_widget_keys():
    source = (ROOT / "ui" / "sidebar_fallback_panel.py").read_text(encoding="utf-8")
    assert 'def _render_connector(*, key_prefix: str = "main_drawer", show_secret_inputs: bool = True)' in source
    assert 'def _render_timer(*, key_prefix: str = "main_drawer")' in source
    assert 'def _render_ui_and_account(*, key_prefix: str = "main_drawer")' in source
    assert 'key=f"{key_prefix}_connect_api_v1"' in source
    assert 'key=f"{key_prefix}_timer_start_v1"' in source
    assert 'key=f"{key_prefix}_logout_v1"' in source
