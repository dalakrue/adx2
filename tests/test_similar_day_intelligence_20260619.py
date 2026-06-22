"""Acceptance and regression tests for Similar-Day Intelligence.

The calculation tests are intentionally independent of Streamlit so they also
run in lightweight CI. UI and deployment behavior is verified by source/AST
contracts when Streamlit is not installed in the test container.
"""
from __future__ import annotations

import ast
import math
import sqlite3
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core import similar_day_intelligence_20260619 as engine
from core.similar_day_config_20260619 import CONFIG, validate_weights

ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def synthetic_h1() -> pd.DataFrame:
    rows: list[tuple] = []
    for di, day in enumerate(pd.bdate_range("2026-04-20", "2026-06-19", tz="UTC")):
        base = 1.075 + di * 0.00017
        family = (di % 7) - 3
        for hour in range(24):
            timestamp = day + pd.Timedelta(hours=hour)
            trend = (family * 0.000006 + 0.000035) * hour
            wave = 0.00028 * math.sin((hour + di % 5) / 3.0)
            open_price = base + trend + wave
            close_price = open_price + 0.000055 * math.sin(hour + di * 0.7)
            high = max(open_price, close_price) + 0.00013 + (di % 3) * 0.00001
            low = min(open_price, close_price) - 0.00013 - (hour % 4) * 0.000005
            volume = 95 + di + hour * 2
            rows.append((timestamp, open_price, high, low, close_price, volume))
    frame = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    # One empty weekday acts as a holiday/attempted candidate.
    frame = frame.loc[frame["time"].dt.date != pd.Timestamp("2026-06-15").date()].copy()
    # One safely interpolatable missing historical H1 candle.
    frame = frame.loc[frame["time"] != pd.Timestamp("2026-06-16 05:00:00+00:00")].copy()
    return frame.reset_index(drop=True)


def canonical(generation: int = 17, latest: str = "2026-06-19T12:00:00+00:00") -> dict:
    return {
        "symbol": "EURUSD",
        "timeframe": "H1",
        "latest_completed_candle_time": latest,
        "calculation_generation": generation,
        "run_id": f"test-generation-{generation}",
        "canonical_generation_id": f"test-generation-{generation}",
        "final_decision": {
            "final_decision": "BUY",
            "less_risky_decision": "BUY",
            "directional_market_view": "BUY",
        },
        "regime": {"current_regime": "BULL_NORMAL", "major_regime": "BULL_NORMAL"},
        "powerbi": {"h3_pips": 4.5},
    }


@pytest.fixture(scope="module")
def calculation_bundle() -> dict:
    frame = synthetic_h1()
    state: dict = {}
    started = time.perf_counter()
    first = engine.build_similar_day_intelligence(frame, canonical(), state=state)
    first_wall = time.perf_counter() - started
    started = time.perf_counter()
    cached = engine.build_similar_day_intelligence(frame, canonical(), state=state)
    cache_wall = time.perf_counter() - started

    changed = frame.copy()
    future_mask = changed["time"] > pd.Timestamp("2026-06-19 12:00:00+00:00")
    changed.loc[future_mask, ["open", "high", "low", "close"]] += 0.50
    future_changed = engine.build_similar_day_intelligence(changed, canonical(), state={})
    return {
        "frame": frame,
        "first": first,
        "cached": cached,
        "future_changed": future_changed,
        "first_wall": first_wall,
        "cache_wall": cache_wall,
    }


# 1. Project import test
def test_01_project_import_test():
    validate_weights()
    assert callable(engine.build_similar_day_intelligence)


# 2. Main Streamlit entry-file test
def test_02_main_streamlit_entry_file_test():
    entry = ROOT / "app.py"
    assert entry.exists()
    ast.parse(entry.read_text(encoding="utf-8"))
    assert "adx_dashpoard" in entry.read_text(encoding="utf-8")


# 3. Streamlit Cloud dependency test
def test_03_streamlit_cloud_dependency_test():
    requirements = source("requirements.txt").lower()
    assert "streamlit" in requirements
    assert (ROOT / "runtime.txt").read_text(encoding="utf-8").strip() == "python-3.12"
    assert "tensorflow" not in requirements
    assert "faiss" not in requirements


# 4. Canonical shared-result test
def test_04_canonical_shared_result_test():
    orchestrator = source("core/settings_run_orchestrator_20260617.py")
    runtime = source("core/canonical_runtime_20260617.py")
    assert orchestrator.count("build_similar_day_intelligence(") == 1
    assert 'canonical["similar_day_intelligence"]' in orchestrator
    assert "publish_canonical_atomically" in orchestrator
    assert orchestrator.index('canonical["similar_day_intelligence"]') < orchestrator.rindex("publish_canonical_atomically(")
    assert '"similar_day_intelligence": similar_day' in runtime


# 5. Six-Lunch-field preservation test
def test_05_six_lunch_field_preservation_test():
    lunch = source("ui/lunch_four_core_fields_20260619.py")
    body = lunch.split("def render_lunch_six_core_fields", 1)[1].split("def render_lunch_four_core_fields", 1)[0]
    assert body.count("if _gate(") == 6
    assert 'CURRENT_FIELD = "4. Open / Close — Dinner Full Combined Intelligence"' in lunch
    assert 'AI_FIELD = "5. Open / Close — Grounded AI Assistant"' in lunch
    assert 'READINESS_FIELD = "6. Open / Close — Future Strategy Research History"' in lunch

def test_06_same_hour_alignment_test(calculation_bundle):
    result = calculation_bundle["first"]
    assert result["elapsed_hour_count"] == 13
    assert result["matched_hours_utc"] == list(range(13))
    assert all(row["Matched Hour Count"].endswith("/13") for row in result["history_25"])


# 7. No-future-data leakage test
def test_07_no_future_data_leakage_test(calculation_bundle):
    original = calculation_bundle["first"]
    changed = calculation_bundle["future_changed"]
    assert original["top_five"] == changed["top_five"]
    assert original["summary"] == changed["summary"]
    assert changed["no_lookahead"]["future_rows_used_in_similarity"] == 0
    assert changed["input_quality"]["future_rows_removed"] > 0


# 8. Weekend and holiday test
def test_08_weekend_and_holiday_test(calculation_bundle):
    rows = calculation_bundle["first"]["history_25"]
    dates = [pd.Timestamp(row["Historical Date"]) for row in rows]
    assert all(item.weekday() < 5 for item in dates)
    holiday = next(row for row in rows if row["Historical Date"] == "2026-06-15")
    assert holiday["Similarity Index"] == 0
    assert "holiday" in holiday["Exclusion or Warning Reason"].lower() or "empty trading day" in holiday["Exclusion or Warning Reason"].lower()


# 9. Missing-candle test
def test_09_missing_candle_test(calculation_bundle):
    row = next(item for item in calculation_bundle["first"]["history_25"] if item["Historical Date"] == "2026-06-16")
    assert row["Matched Hour Count"] == "12/13"
    assert "missing" in row["Exclusion or Warning Reason"].lower() or "interpol" in row["Exclusion or Warning Reason"].lower()


# 10. Duplicate timestamp test
def test_10_duplicate_timestamp_test():
    frame = synthetic_h1().head(30)
    duplicate = pd.concat([frame, frame.iloc[[3]]], ignore_index=True)
    normalized, quality = engine._normalise_ohlc(duplicate)
    assert quality["duplicates_removed"] == 1
    assert normalized["time"].is_unique


# 11. Timezone comparison test
def test_11_timezone_comparison_test():
    frame = synthetic_h1().head(48).copy()
    frame["time"] = frame["time"].dt.tz_convert("Asia/Yangon")
    normalized, _ = engine._normalise_ohlc(frame)
    assert str(normalized["time"].dt.tz) == "UTC"


# 12. Deterministic ranking test
def test_12_deterministic_ranking_test(calculation_bundle):
    result = calculation_bundle["first"]
    repeated = engine.build_similar_day_intelligence(calculation_bundle["frame"], canonical(), state={})
    assert [x["Historical Date"] for x in result["history_25"]] == [x["Historical Date"] for x in repeated["history_25"]]
    assert [x["Similarity Index"] for x in result["history_25"]] == [x["Similarity Index"] for x in repeated["history_25"]]


# 13. DTW constraint test
def test_13_dtw_constraint_test():
    a = np.linspace(-1, 1, 24, dtype=np.float32)
    b = np.roll(a, 2)
    distance = engine.constrained_dtw_distance(a, b, window=3)
    abandoned = engine.constrained_dtw_distance(a, b + 50, window=2, max_cost=0.01)
    assert math.isfinite(distance)
    assert abandoned == float("inf")


# 14. Data-quality penalty test
def test_14_data_quality_penalty_test():
    clean = engine._quality_score(matched=13, expected=13, duplicate=False, unsorted_input=False, volume_quality=100)
    damaged = engine._quality_score(matched=11, expected=13, duplicate=True, unsorted_input=True, volume_quality=0, current=True)
    assert clean == 100
    assert damaged < clean


# 15. Top-five ranking test
def test_15_top_five_ranking_test(calculation_bundle):
    result = calculation_bundle["first"]
    assert len(result["top_five"]) == 5
    assert [row["Rank"] for row in result["top_five"]] == [1, 2, 3, 4, 5]
    scores = [row["Similarity Index"] for row in result["history_25"]]
    assert scores == sorted(scores, reverse=True)


# 16. H+1/H+3/H+6 outcome test
def test_16_horizon_outcome_test(calculation_bundle):
    usable = [row for row in calculation_bundle["first"]["top_five"] if row["H+6 Pips"] is not None]
    assert usable
    for row in usable:
        assert row["H+1 Direction"] in {"BUY", "SELL", "WAIT"}
        assert row["H+3 Direction"] in {"BUY", "SELL", "WAIT"}
        assert row["H+6 Direction"] in {"BUY", "SELL", "WAIT"}


# 17. MFE and MAE test
def test_17_mfe_and_mae_test(calculation_bundle):
    row = next(item for item in calculation_bundle["first"]["top_five"] if item["Maximum Favourable Excursion"] is not None)
    assert row["Maximum Favourable Excursion"] >= 0
    assert row["Maximum Adverse Excursion"] >= 0


# 18. Reliability-gating test
def test_18_reliability_gating_test():
    high = engine.reliability_label(agreement_count=4, effective_sample_size=4.1, data_quality=96, regime_compatibility=85, best_similarity=80, anomaly=False, missing_current_hours=False)
    medium = engine.reliability_label(agreement_count=3, effective_sample_size=3, data_quality=82, regime_compatibility=55, best_similarity=61, anomaly=False, missing_current_hours=False)
    low = engine.reliability_label(agreement_count=2, effective_sample_size=2, data_quality=70, regime_compatibility=40, best_similarity=45, anomaly=True, missing_current_hours=True)
    assert (high, medium, low) == ("High Reliability", "Medium Reliability", "Low Reliability")


# 19. Conflict-warning test
def test_19_conflict_warning_test():
    conflict, text = engine.canonical_conflict_warning("SELL", "BUY")
    no_conflict, _ = engine.canonical_conflict_warning("WAIT", "BUY")
    assert conflict and "must not override" in text
    assert not no_conflict


# 20. Cache-key invalidation test
def test_20_cache_key_invalidation_test():
    base = engine.similarity_cache_key(canonical(), 13)
    generation_changed = engine.similarity_cache_key(canonical(generation=18), 13)
    hour_changed = engine.similarity_cache_key(canonical(), 12)
    timestamp_changed = engine.similarity_cache_key(canonical(latest="2026-06-19T13:00:00+00:00"), 14)
    assert len({base, generation_changed, hour_changed, timestamp_changed}) == 4


# 21. Stale-generation overwrite test
def test_21_stale_generation_overwrite_test(tmp_path, calculation_bundle):
    db = tmp_path / "similar.sqlite3"
    payload = dict(calculation_bundle["first"])
    features = payload.pop("_feature_store_rows")
    assert engine.persist_similarity_generation(payload, features, db_path=db)["status"] == "PUBLISHED"
    stale = dict(payload)
    stale["calculation_generation"] = payload["calculation_generation"] - 1
    assert engine.persist_similarity_generation(stale, [], db_path=db)["status"] == "STALE_REJECTED"


# 22. Database migration test
def test_22_database_migration_test(tmp_path):
    db = tmp_path / "migration.sqlite3"
    report = engine.migrate_similarity_store(db)
    assert report["ok"] and db.exists()
    with sqlite3.connect(db) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"similar_day_feature_store", "similar_day_generations"}.issubset(names)


# 23. Existing Full Metric history preservation test
def test_23_existing_full_metric_history_preservation_test():
    lunch = source("ui/lunch_four_core_fields_20260619.py")
    assert "_render_full_metric_history(state)" in lunch
    assert "Overall Full Metric History — Last 25 Days" in lunch
    assert "All 10 Decision Histories — Last 25 Days" in lunch


# 24. Power BI Projection preservation test
def test_24_power_bi_projection_preservation_test():
    lunch = source("ui/lunch_four_core_fields_20260619.py")
    assert "render_cached_powerbi_projection" in lunch
    assert "_render_powerbi(state)" in lunch


# 25. Existing Regime history preservation test
def test_25_existing_regime_history_preservation_test():
    lunch = source("ui/lunch_four_core_fields_20260619.py")
    assert "Overall Regime History — Last 25 Days" in lunch
    assert "Higher Standard Regime History — Last 25 Days" in lunch
    assert "_render_regime_history(state)" in lunch


# 26. Existing All Current Data preservation test
def test_26_existing_all_current_data_preservation_test():
    lunch = source("ui/lunch_four_core_fields_20260619.py")
    combined = lunch.split("def _render_regime_combined_logic", 1)[1].split("def _render_ai_assistant_lazy", 1)[0]
    assert '"Similar-Day and Pattern Intelligence"' in combined
    assert '"All Current Data"' in combined
    assert "render_similar_day_intelligence(state=state)" in combined
    assert "_render_current_data(state)" in combined

def test_27_copy_button_test():
    copy_sources = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in (ROOT / "ui").glob("*.py"))
    assert "copy" in copy_sources.lower()
    lunch_copy = source("ui/lunch_restored.py")
    assert "Copy Short" in lunch_copy and "Copy All" in lunch_copy


# 28. Mobile-width rendering test
def test_28_mobile_width_rendering_test():
    renderer = source("ui/similar_day_renderer_20260619.py")
    assert "@media(max-width:760px)" in renderer
    assert "grid-template-columns:1fr" in renderer
    assert "use_container_width=True" in renderer


# 29. API-key mobile paste test
def test_29_api_key_mobile_paste_test():
    settings = source("tabs/antd_page_router_20260615.py")
    finnhub = source("core/finnhub_connector.py")
    assert "mobile paste box" in settings.lower()
    assert "st.text_area(" in settings
    assert "Finnhub API key — mobile paste box" in finnhub


# 30. Guest-login flow test
def test_30_guest_login_flow_test():
    auth = source("core/light_auth_20260612.py")
    assert "guest" in auth.lower()
    assert "auth.sqlite3" in auth
    assert "password_hash" in auth


# 31. Run Calculation + Open Lunch end-to-end test
def test_31_run_calculation_open_lunch_end_to_end_test():
    router = source("tabs/antd_page_router_20260615.py")
    orchestrator = source("core/settings_run_orchestrator_20260617.py")
    assert "Run Calculation + Open Lunch" in router
    assert '"active_page": "Lunch"' in router
    assert "build_similar_day_intelligence" in orchestrator
    assert "persist_similarity_generation" in orchestrator


# 32. Tab-switch synchronization test
def test_32_tab_switch_synchronization_test():
    runtime = source("core/canonical_runtime_20260617.py")
    lunch = source("ui/similar_day_renderer_20260619.py")
    assert "get_canonical(state)" in lunch
    assert "build_shared_adapter" in runtime
    assert '"similar_day_intelligence": similar_day' in runtime


# 33. Browser rerun prevention test
def test_33_browser_rerun_prevention_test():
    renderer = source("ui/similar_day_renderer_20260619.py")
    lunch = source("ui/lunch_four_core_fields_20260619.py")
    assert "build_similar_day_intelligence" not in renderer
    assert "build_similar_day_intelligence" not in lunch
    assert "st.rerun" not in renderer
    assert "st.rerun" not in lunch


# 34. Peak RAM comparison/bounded-memory test
def test_34_peak_ram_bounded_fixture_test():
    frame = synthetic_h1()
    tracemalloc.start()
    result = engine.build_similar_day_intelligence(frame, canonical(generation=34), state={})
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert result["ok"]
    assert peak < 128 * 1024 * 1024
    assert all(str(dtype) == "float32" for dtype in engine._normalise_ohlc(frame)[0][["open", "high", "low", "close", "volume"]].dtypes)


# 35. CPU/calculation-duration comparison test
def test_35_cpu_calculation_duration_test(calculation_bundle):
    assert calculation_bundle["first_wall"] < 15.0
    assert calculation_bundle["cache_wall"] < calculation_bundle["first_wall"]
    assert calculation_bundle["cached"]["cache_status"] == "HIT"


# 36. Local startup smoke test
def test_36_local_startup_smoke_test():
    for relative in ("app.py", "adx_dashpoard.py", "core/app/runner.py"):
        ast.parse(source(relative))
    assert "from adx_dashpoard import main" in source("app.py")
