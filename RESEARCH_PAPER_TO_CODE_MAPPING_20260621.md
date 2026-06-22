# Exact Research-Paper-to-Code Mapping

All ten mechanisms are implemented in `core/ten_paper_research_layers_20260621.py` and called once by `core/settings_run_orchestrator_20260617.py`. Persistence is centralized in `core/research_validation_store_20260621.py`.

| # | Exact paper title | Code entry points | Persisted tables | Production behavior |
|---|---|---|---|---|
| 1 | “Panning for Gold: ‘Model-X’ Knockoffs for High Dimensional Controlled Variable Selection.” | `gaussian_model_x_knockoffs`, `run_model_x_feature_validation`, `_knockoff_threshold` | `model_x_knockoff_feature_history` | Shadow feature audit only; no feature is removed. Stability requires two chronological windows and regime support. Exact FDR control is **not claimed** because the covariate distribution is estimated. |
| 2 | “Online Rules for Control of False Discovery Rate and False Discovery Exceedance.” | `collect_sequential_tests`, `apply_online_fdr` | `online_fdr_test_history`, `online_fdr_state` | One central sequential evidence budget. Records p-value, alpha, decision, family, wealth before/after, generation, and dependence notice. |
| 3 | “Classification with a Reject Option using a Hinge Loss.” | `build_reject_option_shadow` | `reject_option_history` | Produces a shadow BUY/SELL/WAIT decision. It may only preserve or downgrade to WAIT. Protected decision remains visible and unchanged. |
| 4 | “Estimation and Testing of Forecast Rationality under Flexible Loss.” | `_loss_rows`, `evaluate_flexible_asymmetric_loss` | `flexible_loss_history` | Fixed, versioned asymmetric loss evaluated in two chronological windows. Existing MAE/RMSE/Brier/CRPS/interval score outputs remain separate. |
| 5 | “A Unified Approach to Interpreting Model Predictions.” | `_rule_contributions`, `build_lightweight_explanations` | `model_explanation_cache` | Uses precomputed TreeSHAP only for compatible existing trees, exact precomputed linear contributions where available, and lightweight grouped protected-rule contributions otherwise. Explicitly non-causal. |
| 6 | “Monotonic Calibrated Interpolated Look-Up Tables.” | `MONOTONICITY_CONTRACT`, `_monotonic_violation_rate`, `validate_monotonicity_contract` | `monotonicity_validation_history` | Validator only. It reports violations for the six required monotonic contracts and does not alter scores. |
| 7 | “DBToaster: Higher-order Delta Processing for Dynamic, Frequently Fresh Views.” | `HISTORY_DELTA_INVENTORY`, `_exact_stats`, `_merge_stats`, `_stats_equal`, `update_exact_delta_state` | `delta_maintenance_history`, `exact_delta_state` | Exact insert-delta maintenance only for algebraically valid statistics. Any mismatch rejects the optimization and keeps exact full recomputation. |
| 8 | “Provenance Semirings.” | `_node`, `_edge`, `build_provenance_graph`, `lineage_for_result`; SQLite query `query_provenance_lineage` | `provenance_node`, `provenance_edge` | Bounded immutable identities and lineage edges tied to one source generation. No large symbolic expressions in session state. |
| 9 | “Metamorphic Testing: A New Approach for Generating Next Test Cases.” | `run_metamorphic_relations`; focused pytest module | `metamorphic_test_history` | Implements the 12 required invariants, including future append, row order, cache, serialization, phone overlap, no reversal, deterministic hash, and rollback. |
| 10 | “Keeping CALM: When Distributed Consistency Is Easy.” | `CALM_OPERATIONS`, `classify_calm_operations` | `calm_operation_classification` | Classifies append-only facts as monotonic and latest/current/top-k/controller/pointer decisions as coordinated. Non-monotonic visibility remains behind atomic publication. |

## Shared gates

`_evidence_gates` records the exact minimum sample requirement, chronological boundaries, purge/embargo, FDR target, effective sample size, regime/session support, adjacent-window stability, catastrophic-regime check, calibration status, resource status, monotonicity status, and metamorphic status. Rows are stored in `evidence_gate_history`; one status row per paper is stored in `research_paper_run`.

No layer is enabled for production influence. The code deliberately sets `production_influence_enabled = false` even when synthetic gates pass; a future production-enablement change would require a separately reviewed promotion transaction and two independent real chronological windows.
