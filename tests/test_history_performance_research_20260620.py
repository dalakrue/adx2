from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from core.history_evidence_store_20260620 import (
    SPECS, append_history_bundle, catalog_frame, export_history, query_history,
    validate_no_future_rows,
)
from core.history_research_pipeline_20260620 import build_history_research_transaction
from core.research_evidence_algorithms_20260620 import (
    conformalized_quantile_interval, diebold_mariano_test, m4_downsample,
    matrix_profile_current_matches, mint_reconcile_display_paths, pelt_mean_changes,
)

ROOT = Path(__file__).resolve().parents[1]



def _fake_streamlit():
    class Column:
        def metric(self, *args, **kwargs):
            return None
    return SimpleNamespace(
        markdown=lambda *a, **k: None, caption=lambda *a, **k: None,
        info=lambda *a, **k: None, warning=lambda *a, **k: None,
        columns=lambda n: [Column() for _ in range(n)],
        toggle=lambda *a, **k: False, session_state={},
        cache_data=lambda *a, **k: (lambda fn: fn),
        cache_resource=lambda *a, **k: (lambda fn: fn),
    )


def _load_lunch_module():
    fake = _fake_streamlit()
    with patch.dict(sys.modules, {"streamlit": fake}):
        sys.modules.pop("ui.lunch_four_core_fields_20260619", None)
        module = importlib.import_module("ui.lunch_four_core_fields_20260619")
    return module, fake

def fixture_payload() -> tuple[dict, pd.DataFrame, pd.DataFrame, dict]:
    idx = pd.date_range("2026-05-01", periods=720, freq="h", tz="UTC")
    rng = np.random.default_rng(7)
    close = 1.15 + np.cumsum(np.sin(np.arange(len(idx)) / 15) * 1e-5 + rng.normal(0, 2e-5, len(idx)))
    frame = pd.DataFrame({
        "time": idx, "open": close - 1e-5, "high": close + 6e-5,
        "low": close - 6e-5, "close": close,
    })
    latest = idx[-1].isoformat()
    canonical = {
        "schema_version": "2.0.0", "canonical_calculation_id": "CALC-20260620-1",
        "run_id": "RUN-20260620-1", "calculation_generation": 31,
        "symbol": "EURUSD", "timeframe": "H1", "source": "TEST",
        "latest_completed_candle_time": latest, "data_signature": "signature-1",
        "final_decision": {"final_decision": "WAIT", "directional_market_view": "BUY", "less_risky_decision": "WAIT"},
        "regime": {"major_regime": "BULL_NORMAL", "alpha": 1.2, "delta": 0.2, "reliability": 74},
        "forecasts": {"horizons": {
            f"{h}h": {"horizon_hours": h, "point_forecast": float(close[-1] + h * 1e-5),
                       "lower_bound": float(close[-1] - 7e-5), "upper_bound": float(close[-1] + 7e-5),
                       "direction": "BUY"}
            for h in range(1, 7)
        }},
        "reliability": {"score": 74}, "data_quality": {"score": 99, "rejected_rows": 0},
        "master_score": 5.4, "entry_score": 5.1, "buy_score": 5.8, "sell_score": 4.2,
        "hold_safety": 5.2, "tp_quality": 4.9, "exit_risk": 5.6,
        "trend_capacity_remaining": 4.4, "market_quality": 71, "forecast_agreement": 68,
        "medium_standard_regime_bias": {"decision": "WAIT", "score": 5.0},
    }
    priority = pd.DataFrame([
        {"Time": idx[-1], "Priority Score": 81, "Priority": "A", "KNN Priority": 2, "Greedy Priority": 3},
        {"Time": idx[-2], "Priority Score": 76, "Priority": "A", "KNN Priority": 3, "Greedy Priority": 4},
    ])
    paths = {
        "red": pd.DataFrame({"red_path": close[-1] + np.arange(1, 7) * 1e-5}),
        "yellow": pd.DataFrame({"yellow_path": close[-1] + np.arange(1, 7) * 2e-5}),
        "blue": pd.DataFrame({"blue_path": close[-1] + np.arange(1, 7) * 0.5e-5}),
    }
    return canonical, frame, priority, paths


def test_closed_lunch_gates_call_no_heavy_renderer():
    lunch, fake_st = _load_lunch_module()
    heavy = ["_render_current_data", "_render_medium_standard_bias", "_render_full_metric_history", "_render_powerbi", "_render_regime_history", "_render_regime_combined_logic", "_render_ai_assistant_lazy"]
    mocks = {name: Mock() for name in heavy}
    with patch.object(lunch, "st", fake_st):
        with patch.multiple(lunch, **mocks):
            lunch.render_lunch_six_core_fields(state=fake_st.session_state)
    assert all(mock.call_count == 0 for mock in mocks.values())

def test_field4_selection_does_not_mutate_canonical_source():
    lunch, _ = _load_lunch_module()
    canonical = {"final_decision": {"final_decision": "WAIT"}, "run_id": "g1"}
    state = {"canonical_result_20260617": canonical}
    before = {"final_decision": {"final_decision": "WAIT"}, "run_id": "g1"}
    lunch._canonical(state)
    assert canonical == before

def test_history_pipeline_preserves_decision_and_original_paths_and_orders_bands():
    canonical, frame, priority, paths = fixture_payload()
    original = json.loads(json.dumps(canonical))
    output, bundle, summary = build_history_research_transaction(
        canonical, completed_h1=frame, priority_table=priority, calibrated_bundle=paths,
    )
    assert output["final_decision"] == original["final_decision"]
    assert summary["protected_outputs_changed"] is False
    assert len(bundle["powerbi_source_path_history"]) == 18
    assert len(bundle["powerbi_reconciled_path_history"]) == 6
    for row in bundle["powerbi_prediction_ledger"]:
        values = [row["lower_value"], row["median_value"], row["upper_value"]]
        assert values == sorted(values)
        assert row["settled_status"] == "PENDING"


def test_same_completed_h1_is_idempotent_and_views_are_bounded(tmp_path: Path):
    canonical, frame, priority, paths = fixture_payload()
    _, bundle, _ = build_history_research_transaction(
        canonical, completed_h1=frame, priority_table=priority, calibrated_bundle=paths,
    )
    db = tmp_path / "history.sqlite3"
    first = append_history_bundle(bundle, db_path=db)
    second = append_history_bundle(bundle, db_path=db)
    assert sum(v["inserted"] for v in first.values()) > 0
    assert sum(v["inserted"] for v in second.values()) == 0
    assert sum(v["idempotent_ignored"] for v in second.values()) > 0
    bounded = query_history("similar_day_outcome_history", limit=48, db_path=db)
    complete = export_history("similar_day_outcome_history", db_path=db)
    assert len(bounded) <= 48
    assert len(complete) >= len(bounded)
    assert validate_no_future_rows(db_path=db) == []
    times = pd.to_datetime(bounded["latest_completed_h1"], utc=True)
    assert times.is_monotonic_decreasing


def test_catalog_documents_every_history_grain_and_business_key():
    catalog = catalog_frame()
    assert len(catalog) == len(SPECS) >= 35
    assert catalog["grain"].str.len().gt(0).all()
    assert catalog["business_key"].str.len().gt(0).all()
    names = set(catalog["name"])
    for required in (
        "full_metric_overall_history", "powerbi_prediction_ledger", "regime_changepoint_history",
        "similar_day_ranked_match_history", "canonical_priority_history", "ai_assistant_history",
        "cache_diagnostics_history", "performance_history",
    ):
        assert required in names


def test_algorithms_are_validation_or_display_only():
    x = np.sin(np.arange(300) / 9) + np.r_[np.zeros(150), np.ones(150)]
    pelt = pelt_mean_changes(x, min_segment=8)
    assert pelt["direction_created"] is False
    mp = matrix_profile_current_matches(x, windows=(6, 12, 24))
    assert set(mp["windows"]) == {"6", "12", "24"}
    m4 = m4_downsample(pd.DataFrame({"time": np.arange(1000), "value": x[np.arange(1000) % len(x)]}), x_col="time", y_col="value", max_points=100)
    assert len(m4) <= 100
    mint = mint_reconcile_display_paths({"a": [1, 2, 3], "b": [1.1, 2.1, 3.1]}, anchor_price=0.9)
    assert mint["protected_paths_changed"] is False
    assert set(mint["original_paths"]) == {"a", "b"}
    dm = diebold_mariano_test([1, 2], [2, 3], horizon=6)
    assert dm["status"] == "INSUFFICIENT DATA"
    cqr = conformalized_quantile_interval(pd.DataFrame(), point=1.0, lower=.9, upper=1.1, horizon=1)
    assert cqr["status"] == "INSUFFICIENT DATA"


def test_api_key_redaction_and_no_secret_in_history_schema():
    fake = _fake_streamlit()
    with patch.dict(sys.modules, {"streamlit": fake}):
        sys.modules.pop("tabs.ai_assistant_compact_20260619", None)
        module = importlib.import_module("tabs.ai_assistant_compact_20260619")
    _redact_sensitive_text = module._redact_sensitive_text
    redacted = _redact_sensitive_text("api_key=sk-super-secret-123456789 Authorization: Bearer abcdefghijklmnop")
    assert "super-secret" not in redacted
    assert "abcdefghijklmnop" not in redacted
    store_source = (ROOT / "core" / "history_evidence_store_20260620.py").read_text(encoding="utf-8").lower()
    assert "api_key text" not in store_source
    assert "secret text" not in store_source


def test_router_lazy_gates_precede_heavy_morning_research_and_lunch_imports():
    source = (ROOT / "tabs" / "antd_page_router_20260615.py").read_text(encoding="utf-8")
    morning = source.split("def _render_morning", 1)[1].split("def _render_research", 1)[0]
    assert morning.index("morning_true_load_gate_20260620") < morning.index("_home_ns()")
    research = source.split("def _render_research", 1)[1].split("def _render_other", 1)[0]
    assert research.index("research_true_load_gate_20260620") < research.index("import tabs.research")
    lunch = (ROOT / "ui" / "lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    body = lunch.split("def render_lunch_six_core_fields", 1)[1].split("def render_lunch_four_core_fields", 1)[0]
    assert body.index("if _gate(CURRENT_FIELD, 4, state):") < body.index("_render_regime_combined_logic(state)")
    assert body.index("if _gate(AI_FIELD, 5, state):") < body.index("_render_ai_assistant_lazy(state)")

def test_python_312_and_entry_file_contract():
    assert (ROOT / "runtime.txt").read_text().strip() == "python-3.12"
    assert (ROOT / ".python-version").read_text().strip().startswith("3.12")
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "adx_dashpoard" in app
