from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_menu_has_no_calculation_or_ram_buttons_and_keeps_two_copy_actions():
    code = source("ui/main_menu_drawer.py")
    assert "main_menu_run_calculation_20260615" not in code
    assert "main_menu_reduce_ram_20260621" not in code
    assert "Extra Copy Panel" not in code
    assert 'central_copy_button("Copy Full"' in code
    assert "render_direct_canonical_copy_buttons" in code


def test_settings_is_single_all_in_one_refresh_calculate_open_lunch_path():
    code = source("tabs/antd_page_router_20260615.py")
    assert "Run Calculation + Open Lunch (One Click)" in code
    assert 'refresh_data(st.session_state, symbol_override="EURUSD", timeframe_override="H1")' in code
    assert "run_settings_calculation(ns)" in code
    assert '"lunch_field_open_5_20260621": True' in code
    assert '"lunch_field_widget_5_20260621": True' in code
    assert "_recover_fact_pack" in code


def test_copy_component_binds_one_click_and_has_visible_manual_fallback():
    code = source("ui/copy_tools.py")
    assert "addEventListener('click'" in code
    assert "addEventListener('pointerup'" not in code
    assert "addEventListener('touchend'" not in code
    assert "Clipboard blocked. Text is selected" in code


def test_ai_has_disk_recovery_and_offline_diagnostic_instead_of_dead_return():
    code = source("tabs/ai_assistant_compact_20260619.py")
    assert "load_latest_summary" in code
    assert "_offline_fact_pack" in code
    assert "_offline_answer" in code
    assert "return\n    calc_id" not in code


def test_freshness_helper_detects_current_and_late_frames():
    from core.market_time_freshness_20260622 import market_time_snapshot
    now = pd.Timestamp.now(tz="UTC").floor("h")
    current = pd.DataFrame({"time": [now - pd.Timedelta(hours=1), now], "close": [1.0, 1.1]})
    late = pd.DataFrame({"time": [now - pd.Timedelta(hours=8)], "close": [1.0]})
    current_result = market_time_snapshot({"timeframe": "H1", "source": "TEST"}, frame=current)
    late_result = market_time_snapshot({"timeframe": "H1", "source": "TEST"}, frame=late)
    assert current_result["status"] == "CURRENT"
    assert late_result["status"] == "LATE"


def test_preflight_explicitly_prefers_fresh_connector_over_stale_display_cache():
    code = source("core/settings_run_orchestrator_20260617.py")
    assert '"last_df": 55' in code
    assert "lag_intervals > 1.5" in code
    assert "fresh_fetch" in code
    assert "ohlc_source_selection_diagnostics_20260622" in code


def _minimal_canonical_for_validation(now: pd.Timestamp) -> dict:
    latest = now.floor("h")
    return {
        "symbol": "EURUSD",
        "timeframe": "H1",
        "source": "TWELVE",
        "data_signature": "unit-test",
        "calculation_generation": 7,
        "latest_completed_candle_time": latest.isoformat(),
        "market": {"latest_completed_candle_time": latest.isoformat(), "row_count": 500},
        "forecasts": {"horizons": {}},
        "validation_metrics": {
            "signed_return_pct": -0.25,
            "mean_signed_error_pct": -1.75,
            "skill_vs_naive_pct": -12.5,
            "confidence_pct": 72.0,
            "buy_probability": 0.58,
        },
    }


def test_prepublication_allows_signed_percentages_and_exact_completed_hour_boundary():
    from core.canonical_data_validation_20260621 import validate_canonical_payload

    now = pd.Timestamp.now(tz="UTC").floor("h") + pd.Timedelta(minutes=15)
    report = validate_canonical_payload(_minimal_canonical_for_validation(now), now=now)
    assert report.status == "PASS"
    assert report.metrics["score_failure_count"] == 0
    assert report.metrics["probability_failure_count"] == 0


def test_prepublication_still_rejects_out_of_range_bounded_confidence():
    from core.canonical_data_validation_20260621 import validate_canonical_payload

    now = pd.Timestamp.now(tz="UTC").floor("h") + pd.Timedelta(minutes=15)
    canonical = _minimal_canonical_for_validation(now)
    canonical["validation_metrics"]["confidence_pct"] = 140.0
    report = validate_canonical_payload(canonical, now=now)
    assert report.status == "REJECT"
    failed = next(item for item in report.constraints if item.constraint_name == "score_domains")
    assert "validation_metrics.confidence_pct" in failed.observed_value


def test_powerbi_uses_freshest_cache_and_source_clock_without_browser_shift():
    code = source("ui/powerbi_cached_renderer_20260619.py")
    assert "Choose the freshest usable cache" in code
    assert "def _plot_clock" in code
    assert 'x=_plot_clock(actual["time"])' in code
    assert 'x=_plot_clock(main_view["time"])' in code
    assert "All chart hours use the same source candle clock" in code


def test_menu_copy_controls_are_stacked_buttons_not_three_narrow_text_columns():
    menu = source("ui/main_menu_drawer.py")
    copy_export = source("ui/canonical_copy_export_20260619.py")
    quick = menu[menu.index("def _render_quick_actions"):menu.index("def render_main_menu_drawer")]
    assert "st.columns(3)" not in quick
    assert 'st.button("📋 Copy Short"' in copy_export
    assert 'st.button("📋 Copy Full"' in copy_export
    assert "disabled=True" in copy_export


def test_ai_recovery_restores_valid_runtime_pointer_before_answering():
    code = source("tabs/ai_assistant_compact_20260619.py")
    assert "validate_canonical_result" in code
    assert "state[CANONICAL_KEY] = canonical" in code
    assert "ai_canonical_runtime_recovered_20260622" in code


def test_regime_field3_tables_publish_only_after_canonical_success():
    code = source("core/settings_run_orchestrator_20260617.py")
    validation_pos = code.index("prepublication_validation = validate_canonical_payload(canonical)")
    sync_pos = code.index('status["operational_sync"] = synchronize_published_generation')
    published_pos = code.index('st.session_state["regime_standard_detail_tables_published_20260618"] = detail_tables', sync_pos)
    assert validation_pos < sync_pos < published_pos
    assert 'regime_standard_detail_tables_staging_20260622' in code[:validation_pos]
