from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.research_validation_store_20260621 import (
    BUNDLE_KEY,
    insert_research_validation_bundle,
    latest_delta_state,
    latest_online_fdr_state,
    query_provenance_lineage,
)
from core.snapshot_schema_20260619 import build_run_snapshot
from core.ten_paper_research_layers_20260621 import (
    CALM_OPERATIONS,
    FLEXIBLE_LOSS_DEFINITION,
    HISTORY_DELTA_INVENTORY,
    MONOTONICITY_CONTRACT,
    PAPER_TITLES,
    apply_online_fdr,
    build_reject_option_shadow,
    build_ten_paper_research_transaction,
    classify_calm_operations,
    evaluate_flexible_asymmetric_loss,
    gaussian_model_x_knockoffs,
    run_metamorphic_relations,
    run_model_x_feature_validation,
    update_exact_delta_state,
    validate_monotonicity_contract,
)
from services.canonical_snapshot_store import commit_snapshot, latest_completed


@pytest.fixture(scope="module")
def evidence() -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    n = 288
    rng = np.random.default_rng(20260621)
    index = pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC")
    close = 1.10 + np.cumsum(rng.normal(0.0, 0.00022, n))
    h1 = pd.DataFrame(
        {
            "open": close - rng.normal(0.0, 0.00004, n),
            "high": close + rng.uniform(0.0001, 0.0004, n),
            "low": close - rng.uniform(0.0001, 0.0004, n),
            "close": close,
            "volume": rng.integers(100, 2000, n),
        },
        index=index,
    )
    settled = pd.DataFrame(
        {
            "calculation_id": [f"CAL-{i:04d}" for i in range(n)],
            "forecast_origin_time": index - pd.Timedelta(hours=1),
            "target_time": index,
            "record_status": "SETTLED",
            "horizon": np.resize([1, 3, 6], n),
            "session": np.resize(["ASIA", "LONDON", "NEW_YORK"], n),
            "h1_regime": np.resize(["BULL", "BEAR", "RANGE"], n),
            "d1_regime": np.resize(["BULL", "BEAR"], n),
            "full_metric_direction": np.resize(["BUY", "SELL", "WAIT"], n),
            "final_decision": np.resize(["BUY", "SELL", "WAIT"], n),
            "raw_confidence": rng.uniform(0.40, 0.90, n),
            "calibrated_confidence": rng.uniform(0.42, 0.86, n),
            "required_probability_threshold": rng.uniform(0.50, 0.70, n),
            "expected_favorable_movement": rng.uniform(1.0, 12.0, n),
            "expected_adverse_movement": rng.uniform(1.0, 10.0, n),
            "predicted_close": close + rng.normal(0.0, 0.0003, n),
            "actual_close": close,
            "absolute_error_pips": rng.uniform(0.0, 12.0, n),
            "squared_error": rng.uniform(0.0, 144.0, n),
            "direction_correct": rng.integers(0, 2, n),
            "interval_hit": rng.integers(0, 2, n),
            "maximum_favorable_excursion": rng.uniform(0.0, 15.0, n),
            "maximum_adverse_excursion": rng.uniform(0.0, 12.0, n),
            "tp_touched": rng.integers(0, 2, n),
            "sl_touched": rng.integers(0, 2, n),
            "data_quality_status": np.resize(["PASS", "PASS", "WARNING"], n),
            "priority": rng.integers(1, 15, n),
            "knn_score": rng.uniform(0.0, 100.0, n),
            "greedy_rank": rng.integers(1, 15, n),
            "model_agreement": rng.uniform(0.30, 1.0, n),
            "exit_risk": rng.uniform(0.0, 10.0, n),
            "reliability_score": rng.uniform(0.0, 100.0, n),
            "similarity_score": rng.uniform(0.0, 1.0, n),
            "nlp_reliability": rng.uniform(0.0, 100.0, n),
        }
    )
    canonical = {
        "canonical_calculation_id": "CAN-TEN-PAPER-TEST",
        "run_id": "RUN-TEN-PAPER-TEST",
        "calculation_generation": 42,
        "symbol": "EURUSD",
        "timeframe": "H1",
        "latest_completed_candle_time": index[-1].isoformat(),
        "data_signature": "TEST-SIGNATURE",
        "last_close": float(close[-1]),
        "master_score": 6.2,
        "entry_score": 6.0,
        "buy_score": 6.5,
        "sell_score": 3.2,
        "hold_safety": 5.9,
        "tp_quality": 5.4,
        "exit_risk": 3.1,
        "trend_capacity_remaining": 5.2,
        "data_quality": {"score": 92},
        "reliability": {"score": 76, "conflict_score": 12},
        "priority": {"knn_score": 72, "greedy_rank": 2, "forecast_agreement": 70},
        "nlp": {"reliability": 55},
        "regime": {"major_regime": "BULL"},
        "final_decision": {
            "final_decision": "BUY",
            "tradeability_decision": "BUY",
            "calibrated_confidence": 0.74,
            "uncertainty_pct": 26,
        },
        "research_calibration": {"validation_status": "PASS"},
    }
    return canonical, h1, settled


def _assert_no_dataframes(value) -> None:
    assert not isinstance(value, pd.DataFrame)
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_dataframes(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _assert_no_dataframes(child)


def test_paper_contracts_and_model_x_determinism(evidence):
    canonical, _, settled = evidence
    assert len(PAPER_TITLES) == 10
    assert len(MONOTONICITY_CONTRACT) == 6
    assert len(HISTORY_DELTA_INVENTORY) >= 8
    assert len(CALM_OPERATIONS) >= 10
    assert FLEXIBLE_LOSS_DEFINITION["version"].startswith("trading-flexible-loss")

    x = np.arange(240, dtype=float).reshape(60, 4) / 100.0
    first, first_diag = gaussian_model_x_knockoffs(x, seed=17)
    second, second_diag = gaussian_model_x_knockoffs(x, seed=17)
    assert np.array_equal(first, second)
    assert first_diag == second_diag

    first_result = run_model_x_feature_validation(settled, source_generation_id="GEN-X", minimum_samples=96, embargo=6)
    second_result = run_model_x_feature_validation(settled, source_generation_id="GEN-X", minimum_samples=96, embargo=6)
    assert first_result["feature_statistics"] == second_result["feature_statistics"]
    assert first_result["automatic_feature_removal"] is False
    assert first_result["production_feature_set_changed"] is False
    assert first_result["fdr_control_claimed"] is False
    assert all(row["sample_support"] > 0 for row in first_result["feature_statistics"])


def test_online_fdr_reject_option_and_flexible_loss(evidence):
    canonical, _, settled = evidence
    tests = [
        {"test_key": "a", "test_family": "drift", "source": "mmd", "raw_p_value": 0.001},
        {"test_key": "b", "test_family": "calibration", "source": "cal", "raw_p_value": 0.8},
    ]
    fdr = apply_online_fdr(tests, source_generation_id="GEN-FDR", fdr_target=0.1)
    assert fdr["controller_scope"] == "CENTRAL_ALL_SEQUENTIAL_TESTS"
    assert len(fdr["records"]) == 2
    assert all("wealth_before" in row and "wealth_after" in row for row in fdr["records"])
    assert all(row["allocated_alpha"] <= 0.1 for row in fdr["records"])

    risky = dict(canonical)
    risky["final_decision"] = {"final_decision": "BUY", "tradeability_decision": "BUY", "calibrated_confidence": 0.05, "uncertainty_pct": 95}
    risky["exit_risk"] = 9.5
    rejected = build_reject_option_shadow(risky, settled, source_generation_id="GEN-R", rejection_cost=0.35)
    assert rejected["protected_decision"] == "BUY"
    assert rejected["shadow_reject_option_decision"] == "WAIT"
    wait = dict(risky)
    wait["final_decision"] = {"final_decision": "WAIT", "tradeability_decision": "WAIT", "calibrated_confidence": 0.99}
    wait_result = build_reject_option_shadow(wait, settled, source_generation_id="GEN-W")
    assert wait_result["shadow_reject_option_decision"] == "WAIT"

    losses = evaluate_flexible_asymmetric_loss(settled, source_generation_id="GEN-L", minimum_samples=96, embargo=6)
    assert len(losses["windows"]) == 2
    assert losses["weights_tuned_on_complete_history"] is False
    assert losses["existing_mae_rmse_brier_crps_interval_score_unchanged"] is True
    assert all(row["loss_definition_version"] == FLEXIBLE_LOSS_DEFINITION["version"] for row in losses["windows"])


def test_monotonic_delta_metamorphic_and_calm(evidence):
    canonical, h1, settled = evidence
    monotonic = validate_monotonicity_contract(settled, source_generation_id="GEN-M")
    assert len(monotonic["results"]) == 6
    assert monotonic["protected_scores_altered"] is False
    assert monotonic["constrained_model_promoted"] is False

    first = update_exact_delta_state(settled.iloc[:180], source_generation_id="GEN-D1")
    second = update_exact_delta_state(settled, source_generation_id="GEN-D2", previous_state=first["state"])
    assert second["exact_full_recompute_equal"] is True
    assert second["approximate_delta_logic_used"] is False
    assert second["state"]["statistics"]["count"] == len(settled)

    reject = build_reject_option_shadow(canonical, settled, source_generation_id="GEN-R2")
    meta = run_metamorphic_relations(canonical, h1, source_generation_id="GEN-META", reject_shadow=reject)
    expected = {
        "future_incomplete_candle_append_invariance",
        "row_order_invariance",
        "duplicate_timestamp_rejection",
        "price_translation_invariance_difference_returns",
        "positive_price_scaling_invariance_normalized_shape",
        "cold_cache_vs_warm_cache_equality",
        "serialization_round_trip_equality",
        "phone_projected_history_overlap_equality",
        "tab_open_close_canonical_identity_invariance",
        "research_no_direction_reversal_invariant",
        "same_inputs_deterministic_identity_and_output_hashes",
        "atomic_rollback_preserves_previous_valid_generation",
    }
    observed = {row["relation_name"] for row in meta["relations"]}
    assert expected <= observed
    assert not [row for row in meta["relations"] if row["status"] == "FAIL"]

    calm = classify_calm_operations(source_generation_id="GEN-CALM")
    assert calm["partially_staged_non_monotonic_generation_visible"] is False
    assert any(row["operation_name"] == "latest_current_selection" and row["coordination_required"] for row in calm["operations"])


def test_full_transaction_is_shadow_bounded_deterministic_and_protected(evidence):
    canonical, h1, settled = evidence
    first, first_bundle, first_summary = build_ten_paper_research_transaction(
        canonical, completed_h1=h1, settled_predictions=settled, minimum_samples=96, embargo=6
    )
    second, second_bundle, second_summary = build_ten_paper_research_transaction(
        canonical, completed_h1=h1, settled_predictions=settled, minimum_samples=96, embargo=6
    )
    research = first["ten_paper_research_20260621"]
    assert research["mode"] == "SHADOW"
    assert research["production_influence_enabled"] is False
    assert research["protected_calculation_changed"] is False
    assert first["final_decision"] == canonical["final_decision"]
    assert research["research_shadow_decision"] in {"BUY", "WAIT"}
    assert first_summary["paper_count"] == 10
    assert research["transaction_id"] == second["ten_paper_research_20260621"]["transaction_id"]
    assert research["output_hash"] == second["ten_paper_research_20260621"]["output_hash"]
    assert len(research["paper_8"]["nodes"]) <= 768
    assert len(research["paper_8"]["edges"]) <= 1536
    assert research["bounded_settled_rows"] <= 3000
    assert BUNDLE_KEY in first_bundle
    assert set(first_bundle[BUNDLE_KEY]) == set(second_bundle[BUNDLE_KEY])
    _assert_no_dataframes(research)


def test_sqlite_bundle_idempotency_lineage_and_atomic_rollback(evidence, tmp_path):
    canonical, h1, settled = evidence
    output, bundle, _ = build_ten_paper_research_transaction(canonical, completed_h1=h1, settled_predictions=settled)
    db_path = tmp_path / "research.sqlite3"
    connection = sqlite3.connect(db_path)
    first = insert_research_validation_bundle(connection, bundle[BUNDLE_KEY])
    connection.commit()
    second = insert_research_validation_bundle(connection, bundle[BUNDLE_KEY])
    connection.commit()
    assert sum(v["inserted"] for v in first.values()) > 0
    assert sum(v["inserted"] for v in second.values()) == 0
    assert latest_online_fdr_state(db_path=db_path)["state_id"].startswith("ONLINE_FDR-")
    assert latest_delta_state(db_path=db_path)["state_id"].startswith("EXACT-DELTA-")
    generation_node = output["ten_paper_research_20260621"]["paper_8"]["nodes"][0]["node_id"]
    lineage = query_provenance_lineage(generation_node, source_generation_id=canonical["canonical_calculation_id"], db_path=db_path)
    assert lineage["nodes"]
    assert lineage["bounded"] is True
    connection.close()

    snapshot_db = tmp_path / "snapshot.sqlite3"
    previous = dict(canonical)
    previous.update({"run_id": "ROLLBACK-PREVIOUS", "calculation_generation": 1})
    previous_snapshot = build_run_snapshot(previous)
    commit_snapshot(previous_snapshot, db_path=snapshot_db)
    staged = dict(canonical)
    staged.update({"run_id": "ROLLBACK-STAGED", "calculation_generation": 2})
    with pytest.raises(RuntimeError):
        commit_snapshot(build_run_snapshot(staged), db_path=snapshot_db, fail_after_stage=True, history_bundle=bundle)
    latest = latest_completed(db_path=snapshot_db)
    assert latest["run_id"] == "ROLLBACK-PREVIOUS"
    conn = sqlite3.connect(snapshot_db)
    assert conn.execute("SELECT COUNT(*) FROM runs WHERE run_id='ROLLBACK-STAGED'").fetchone()[0] == 0
    conn.close()


def test_architecture_static_guards_and_migration_idempotency(tmp_path):
    root = Path(__file__).resolve().parents[1]
    orchestrator = (root / "core" / "settings_run_orchestrator_20260617.py").read_text(encoding="utf-8")
    assert orchestrator.count("build_ten_paper_research_transaction(") == 1
    for folder in ("ui", "tabs", "pages"):
        for path in (root / folder).rglob("*.py") if (root / folder).exists() else []:
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "build_ten_paper_research_transaction" not in text
    lunch = (root / "ui" / "lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    assert "def _render_workspace_4a" in lunch
    assert "def _render_workspace_4b" in lunch
    assert "if str(selected).startswith(\"4B\")" in lunch
    assert "No explanation builder is imported or executed during rendering" in lunch

    migration = (root / "migrations" / "20260621_ten_paper_shadow_layers.sql").read_text(encoding="utf-8")
    db_path = tmp_path / "migration.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.executescript(migration)
    conn.executescript(migration)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "research_paper_run" in tables
    assert "provenance_edge" in tables
    model_x_columns = {row[1] for row in conn.execute("PRAGMA table_info(model_x_knockoff_feature_history)")}
    provenance_columns = {row[1] for row in conn.execute("PRAGMA table_info(provenance_node)")}
    assert {"train_start", "train_end", "test_start", "test_end", "test_effect", "test_sample_support"} <= model_x_columns
    assert {"natural_key", "payload_hash"} <= provenance_columns
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 20260621
    conn.close()
