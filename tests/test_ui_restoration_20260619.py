from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_run_calculation_opens_cached_powerbi_transaction():
    router = (ROOT / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
    assert '"active_page": "Lunch"' in router
    assert '"active_subpage": ""' in router
    lunch = (ROOT / "tabs" / "final_lunch_upgrade_20260617.py").read_text(encoding="utf-8")
    assert "render_cached_powerbi_projection" in lunch
    assert '"lunch_active_subpage": ""' in router
    assert '"lunch_bi_visual_ready": True' in router


def test_powerbi_active_route_is_cached_only():
    router = (ROOT / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
    branch = router.split('elif subpage == "PowerBI Projection":', 1)[1].split('elif subpage == "Priority + Decision + Reliability":', 1)[0]
    assert "render_cached_powerbi_projection" in branch
    assert "_render_lunch_red_prediction_line" not in branch
    assert "_render_powerbi_regime_projection" not in branch
    assert "_home_ns()" not in branch


def test_cached_powerbi_renderer_does_not_recalculate():
    source = (ROOT / "ui" / "powerbi_cached_renderer_20260619.py").read_text(encoding="utf-8")
    for forbidden in (
        "calibrate_projection_bundle(",
        "ensure_shared_calculation_result(",
        "run_settings_calculation(",
        "_dv_predict_future_candles",
    ):
        assert forbidden not in source
    assert 'state.get("powerbi_calibrated_bundle_20260617")' in source
    assert "@_FRAGMENT" in source
    assert "st.plotly_chart" in source


def test_full_metric_uses_25day_view_and_one_factor_only():
    source = (ROOT / "ui" / "full_metric_shared_renderer_20260618.py").read_text(encoding="utf-8")
    display_block = source.split('st.markdown("#### Complete Full Metric History', 1)[1].split("# Regime section", 1)[0]
    assert "history_25day" in display_block
    assert "history_view," not in display_block
    assert "st.tabs(" not in source
    assert "Choose reverse-decision factor" in source
    assert "@_fragment" in source


def test_regime_renders_medium_and_higher_without_hourly_duplicates():
    source = (ROOT / "ui" / "full_metric_regime_inner_renderer_20260618.py").read_text(encoding="utf-8")
    assert '("medium", "Medium Standard Regime — About 5 Days")' in source
    assert '("higher", "Higher Standard Regime — About 25 Days")' in source
    render_body = source.split("def render_existing_regime_inner_section", 1)[1]
    assert "Current Major Regime" in render_body
    assert "Medium Standard Regime" in render_body
    assert "Higher Standard Regime" in render_body
    assert "Raw current-hour" not in render_body
    assert "collect_existing_regime_tables" in render_body


def test_future_rows_are_warning_only_after_exclusion():
    source = (ROOT / "core" / "decision_product_engine_20260617.py").read_text(encoding="utf-8")
    assert "Future timestamps detected and safely excluded" in source
    future_block = source.split("Future timestamps detected and safely excluded", 1)[0][-500:]
    assert "blocking.append" not in future_block


def test_windows_selector_policy_is_targeted_not_silent_exception_swallowing():
    source = (ROOT / "core" / "windows_asyncio_compat_20260619.py").read_text(encoding="utf-8")
    assert "WindowsSelectorEventLoopPolicy" in source
    assert "set_exception_handler" not in source
    assert "except ConnectionResetError" not in source
