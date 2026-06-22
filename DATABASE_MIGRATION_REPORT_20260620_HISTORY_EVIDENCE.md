# Database Migration Report — Common History Evidence

## Authority and migration mode

The authority remains `data/canonical_runtime.sqlite3`. The migration is additive and reversible. It creates `history_catalog`, `history_watermarks`, 35 history tables and indexes; it deletes or renames no existing object. A byte-exact pre-migration copy is included as `data/canonical_runtime.sqlite3.before_history_20260620.bak`.

## Common identity and performance columns

Every history row supports: `record_key, calculation_id, calculation_generation, run_id, symbol, timeframe, source, latest_completed_h1, record_time, target_time, horizon, data_signature, logic_version, condition, sample_count, settled_status, is_revision, created_at, metric_name, value_numeric, value_text, rank_value, lower_value, median_value, upper_value, actual_value, residual_value, coverage_flag, tab_name, renderer_name, row_count, browser_rows, payload_bytes, duration_ms, python_allocation_bytes, rss_mb, cache_status, payload_json`. The identity portion contains calculation ID/generation, run ID, symbol, timeframe, source, latest completed H1, record/target time, horizon, data signature, logic version, condition, sample count, settlement/revision state and creation time. Performance rows also expose tab, renderer, row count, browser rows, payload bytes, duration, Python allocation, RSS and cache status.

## Tables, grains and keys

- `full_metric_overall_history` — FIELD_1/FULL_METRIC; grain: one row per canonical completed H1 generation; key: calculation_id.
- `protected_decision_history` — FIELD_1/FULL_METRIC; grain: one row per protected decision per canonical generation; key: calculation_id + condition.
- `decision11_support_history` — FIELD_1/FULL_METRIC; grain: one row per canonical generation; key: calculation_id.
- `decision_change_audit_history` — FIELD_1/FULL_METRIC; grain: one row per consecutive canonical generation comparison; key: calculation_id.
- `input_data_quality_history` — FIELD_1/FULL_METRIC; grain: one row per canonical generation; key: calculation_id.
- `metric_availability_history` — FIELD_1/FULL_METRIC; grain: one row per metric per canonical generation; key: calculation_id + condition.
- `powerbi_prediction_ledger` — FIELD_2/POWER_BI; grain: one row per forecast origin and H+1..H+6; key: calculation_id + horizon.
- `powerbi_source_path_history` — FIELD_2/POWER_BI; grain: one row per protected source path and horizon; key: calculation_id + condition + horizon.
- `powerbi_reconciled_path_history` — FIELD_2/POWER_BI; grain: one row per displayed reconciled horizon; key: calculation_id + horizon.
- `powerbi_forecast_settlement_history` — FIELD_2/POWER_BI; grain: one row per settled target; key: calculation_id + target_time + horizon.
- `regime_overall_history` — FIELD_3/REGIME; grain: one row per canonical completed H1 generation; key: calculation_id.
- `regime_standard_history` — FIELD_3/REGIME; grain: one row per standard level per generation; key: calculation_id + condition.
- `regime_changepoint_history` — FIELD_3/REGIME; grain: one row per detected changepoint and signal; key: calculation_id + condition + record_time.
- `regime_duration_history` — FIELD_3/REGIME; grain: one row per regime segment or generation; key: calculation_id + condition.
- `regime_transition_reliability_history` — FIELD_3/REGIME; grain: one row per generation; key: calculation_id.
- `regime_alpha_delta_history` — FIELD_3/REGIME; grain: one row per generation; key: calculation_id.
- `regime_conflict_history` — FIELD_3/REGIME; grain: one row per conflict component per generation; key: calculation_id + condition.
- `similar_day_query_history` — FIELD_4A/SIMILAR_DAY; grain: one row per current-query generation and window; key: calculation_id + condition.
- `similar_day_ranked_match_history` — FIELD_4A/SIMILAR_DAY; grain: one row per ranked match; key: calculation_id + condition + rank_value.
- `similar_day_outcome_history` — FIELD_4A/SIMILAR_DAY; grain: one row per ranked match and outcome horizon; key: calculation_id + condition + horizon + rank_value.
- `motif_history` — FIELD_4A/SIMILAR_DAY; grain: one row per motif match; key: calculation_id + condition + rank_value.
- `discord_history` — FIELD_4A/SIMILAR_DAY; grain: one row per discord window; key: calculation_id + condition.
- `match_quality_calibration_history` — FIELD_4A/SIMILAR_DAY; grain: one row per generation and window; key: calculation_id + condition.
- `canonical_priority_history` — FIELD_4B/COMBINED_LOGIC; grain: one row per priority candidate per generation; key: calculation_id + rank_value + record_time.
- `knn_rank_history` — FIELD_4B/COMBINED_LOGIC; grain: one row per KNN-ranked candidate; key: calculation_id + rank_value + record_time.
- `greedy_rank_history` — FIELD_4B/COMBINED_LOGIC; grain: one row per Greedy-ranked candidate; key: calculation_id + rank_value + record_time.
- `reliability_conflict_history` — FIELD_4B/COMBINED_LOGIC; grain: one row per component per generation; key: calculation_id + condition.
- `component_availability_history` — FIELD_4B/COMBINED_LOGIC; grain: one row per component per generation; key: calculation_id + condition.
- `combined_evidence_explanation_history` — FIELD_4B/COMBINED_LOGIC; grain: one row per generation; key: calculation_id.
- `canonical_generation_change_history` — FIELD_4B/COMBINED_LOGIC; grain: one row per consecutive generation comparison; key: calculation_id.
- `ai_assistant_history` — FIELD_6/AI_ASSISTANT; grain: one row per user question/assistant answer pair; key: calculation_id + record_key.
- `ai_evidence_reference_history` — FIELD_6/AI_ASSISTANT; grain: one row per referenced evidence item; key: calculation_id + record_key.
- `ai_answer_consistency_history` — FIELD_6/AI_ASSISTANT; grain: one row per answered question; key: calculation_id + record_key.
- `cache_diagnostics_history` — SYSTEM/PERFORMANCE; grain: one row per cache diagnostic snapshot; key: calculation_id + condition.
- `performance_history` — SYSTEM/PERFORMANCE; grain: one row per timed renderer/stage; key: calculation_id + condition + created_at.

## Atomicity, watermark and idempotency

`commit_snapshot` opens `BEGIN IMMEDIATE`, inserts the canonical snapshot and affected history bundle, marks the run complete, then commits. Deterministic `record_key` values make an identical completed-H1 generation idempotent. `history_watermarks` records the latest completed event time, calculation ID, generation and data signature per table. Future `record_time`/`target_time` rows are rejected unless a forecast target is explicitly pending; settlements are only written when the target candle exists.

## Columnar decision

Measured packaged database size: **749,568 bytes**; largest new table row count: **0**. Thresholds are 250,000 rows or 128 MB. Result: **NOT JUSTIFIED**. SQLite remains simpler and transactional. `core/history_columnar_archive_20260620.py` provides an explicit, reversible partitioned-Parquet/DuckDB maintenance path when measured thresholds are later crossed. Full decisions are in `COLUMNAR_ARCHIVE_DECISION_20260620.json`.

## Migration and rollback

Run `python tools/migrate_history_evidence_20260620.py --backup`. Roll back code first; optional schema rollback uses `python tools/rollback_history_evidence_20260620.py --restore-backup`. See `ROLLBACK_INSTRUCTIONS_20260620.md`.
