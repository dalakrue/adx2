from pathlib import Path
import importlib

ROOT = Path(__file__).resolve().parents[1]


def test_styles_are_self_contained_without_runtime_parts_import():
    source = (ROOT / "core/ui/legacy_impl/styles_impl.py").read_text(encoding="utf-8")
    assert "_PARTS_PACKAGE" not in source
    assert "_import_module" not in source
    module = importlib.import_module("core.ui.styles")
    assert callable(module.apply_global_styles)


def test_cloud_entry_and_requirements_contract():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "Path(__file__).resolve().parent" in app
    assert "from adx_dashpoard import main" in app
    assert "streamlit" in requirements
    assert "pandas" in requirements
    assert "MetaTrader5" not in requirements
    assert 'numpy>=1.26,<2.3; python_version < "3.14"' in requirements
    assert 'numpy>=2.3,<2.4; python_version >= "3.14"' in requirements
    assert (ROOT / "runtime.txt").read_text(encoding="utf-8").strip() == "python-3.12"
    assert (ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.12"


def test_mobile_settings_and_navigation_contract_still_present():
    router = (ROOT / "tabs/antd_page_router_20260615.py").read_text(encoding="utf-8")
    for required in (
        "Twelve Data API key — mobile paste box",
        "Finnhub API key — mobile paste box",
        "▶ Run Calculation + Open Lunch",
        "Open / Close — Twelve Data + MT5 Market Connector",
        "Open / Close — Trade Timer / Sound Alert",
        "Open / Close — Account / Logout",
    ):
        assert required in router or required in (ROOT / "core/finnhub_connector.py").read_text(encoding="utf-8")
