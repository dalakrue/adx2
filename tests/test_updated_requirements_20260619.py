from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_secure_secrets_are_server_side_and_never_autofilled():
    secure = text("core/secure_api_startup_20260619.py")
    router = text("tabs/antd_page_router_20260615.py")
    finnhub = text("core/finnhub_connector.py")
    assert 'st.secrets' in secure
    assert '"api_keys", "finnhub"' in secure
    assert '"api_keys", "second_api"' in secure
    assert 'value=""' in router
    assert "never autofills" in router.lower()
    assert "Use temporary replacement Finnhub key" in finnhub
    assert ".streamlit/secrets.toml" in text(".gitignore")
    assert (ROOT / ".streamlit" / "secrets.example.toml").exists()


def test_guarded_startup_has_all_required_guards():
    source = text("core/secure_api_startup_20260619.py")
    for required in (
        "AUTH_REQUIRED", "RERUN_GUARD", "MANUAL_CALCULATION_REQUIRED",
        "latest_h1", "published_h1", "new7_auth_guest", "auto_connected",
    ):
        assert required in source
    runner = text("core/app/runner.py")
    assert "run_guarded_startup" in runner


def test_decision_11_has_requested_weights_and_does_not_change_original_ten():
    from core.medium_standard_regime_bias_20260619 import WEIGHTS, build_medium_standard_regime_bias

    assert WEIGHTS == {
        "regime_alignment": 0.30,
        "regime_reliability": 0.20,
        "adx_di": 0.15,
        "volatility_suitability": 0.10,
        "forecast_agreement": 0.10,
        "market_quality": 0.10,
        "conflict_penalty": 0.05,
    }
    result = build_medium_standard_regime_bias({
        "regime": {"h1_regime": "BULL_NORMAL", "h4_regime": "BULL", "d1_regime": "BULL", "reliability": 72},
        "final_decision": {"directional_market_view": "BUY"},
        "adx": 28, "plus_di": 30, "minus_di": 14,
        "forecast_agreement": 75, "market_quality": 70,
    })
    assert result["decision_number"] == 11
    assert result["decision"] in {"BUY", "SELL", "WAIT"}
    assert 0 <= result["score"] <= 10
    assert result["protected_ten_decisions_changed"] is False


def test_similar_day_publishes_five_fixed_history_tables():
    source = text("core/similar_day_intelligence_20260619.py")
    for key in (
        "current_hour_core_metrics_history", "decision_outcome_history",
        "regime_compatibility_history", "pattern_recognition_history",
        "powerbi_forecast_calibration_history",
    ):
        assert key in source
    assert "outcomes_calculated_after_ranking" in source
    assert "future_rows_used_in_similarity" in source


def test_dinner_is_hidden_but_compatibility_redirect_remains():
    defaults = text("core/config/defaults.py")
    visible_nav = text("ui/antd_navigation_20260615.py")
    stability = text("core/tab_state_stability_20260615.py")
    assert '"Dinner"' not in defaults.split("DEFAULT_TABS", 1)[1].split("SESSION_DEFAULTS", 1)[0]
    assert 'sac.MenuItem("Dinner"' not in visible_nav
    assert 'raw_page == "Dinner"' in stability
    assert 'lunch_focus_field_20260619' in stability


def test_powerbi_has_intervals_scenarios_and_validation_panel():
    source = text("ui/powerbi_cached_renderer_20260619.py")
    for required in (
        "50% empirical upper", "80% empirical upper / Bull scenario",
        "95% empirical upper", "Historical similar-day scenario",
        "Forecast Validation Panel", "Skill vs Rolling Mean",
        "Skill vs Previous Close", "Forecast Age",
    ):
        assert required in source
