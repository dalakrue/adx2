# Project Hardening V5 — Final Verification Report

**Project:** ADX Quant Pro EURUSD H1  
**Build date:** 2026-06-22  
**Scope:** Time synchronization, history refresh/commit verification, AI Assistant V2 grounding/relevance, duplicate-answer prevention, and Copy Short/Copy Full reliability.

## 1. Protected logic contract

No prediction-engine formula, trading-strategy formula, protected score calculation, ML model, history table, or existing metric was deleted or replaced. Changes are additive or presentation/orchestration-level. The only history-pipeline fallback change removes a wall-clock timestamp fallback; it does not change a market calculation.

## 2. Global broker-candle time synchronization

Implemented `core/shared_broker_time_20260622.py` with:

- `shared_broker_time_provider()`
- canonical completed-H1 timestamp precedence
- broker fixed-offset display projection
- Myanmar candle-time projection
- `frame_to_shared_broker_clock()` for display-only table conversion
- `history_sync_status()` with broker candle, latest history record, and minute difference

The provider never invents a market timestamp from `datetime.now()`, `datetime.utcnow()`, `pd.Timestamp.now()`, local PC time, or `time.time()`. Canonical UTC remains the stored identity; broker time is a display projection only.

Field 1's former synthetic current-row overlay is no longer called. Actual persisted history is compared against the canonical completed broker candle.

## 3. History synchronization and automatic refresh

Implemented `core/history_sync_engine_20260622.py` and integrated it into the single Settings calculation transaction.

After a successful calculation:

1. Missing current-generation core rows are staged from already-published canonical values.
2. The complete history bundle is committed atomically with the canonical generation.
3. Every populated history table in that transaction is checked through `history_watermarks`.
4. Stale copy/presentation caches are invalidated.
5. Session state records generation ID, calculation ID, table-level sync status, latest history time, and difference minutes.

The verification covers all populated tables in the published bundle, including Full Metric, prediction/PowerBI, reliability/conflict, regime, and the other Lunch histories produced by that generation. AI Assistant history is verified immediately after each grounded Q/A append against the same canonical completed H1 candle.

Lunch displays now show:

- **GREEN — Synced** or **RED — Out of Sync**
- Latest Broker Candle
- Latest History Record
- Difference Minutes

## 4. AI Assistant V2

The dynamic grounded pipeline is now the primary answer route. The old focused formatter remains only as a safe fallback when retrieval fails.

Before answering, the registry can include:

- current metrics and protected scores
- regime and reliability
- priority and best-entry evidence
- forecast and PowerBI projection
- NLP summary
- bounded history summary
- forecast agreement
- risk score and position-sizing evidence
- trend capacity
- conflict/warning status
- shared broker-candle time

Question classification includes dedicated entry and exit intents in addition to prediction, TP/SL, regime, history, risk, forecast, reliability, priority, market-time, and system-health intents. Evidence retrieval is restricted to the classified intent's relevant source categories.

The answer footer reports confidence/evidence support, sources, completed timestamp/generation, regime, reliability, priority, freshness/conflict status, and a reasoning summary.

## 5. Duplicate-answer prevention

Implemented `core/ai_duplicate_guard_20260622.py`:

- stores the last 20 questions and answers
- normalizes and compares answer similarity
- threshold: greater than 90%
- removes duplicate lines
- restructures an overly similar answer using question-specific relevant evidence
- preserves the grounded metadata footer

## 6. Copy Short and Copy Full

Only one visible copy-control owner is active at a time: the compact popover when the main drawer is closed, or the main drawer when it is open.

### Copy Short

The V5 payload contains:

- Current Time
- Decision
- Direction
- Regime
- Reliability
- Priority
- Master Score
- Entry Score
- Hold Score
- Exit Risk
- TP Quality
- Trend Capacity
- PowerBI Projection
- Best Entry Summary
- Quick TP
- Quick SL
- Forecast Confidence
- AI Summary

It remains bounded to 40 lines, 6,000 characters, and approximately 1,500 tokens. Compatibility labels reference the same values and preserve existing consumers/tests.

### Copy Full

Copy Full contains all six Lunch field summaries, published scalar metrics, projection/reliability/regime summaries, evidence/limitations, table-level history synchronization summary, and the latest AI summary. It avoids unbounded raw model objects and duplicate calculations.

The clipboard component uses the secure Clipboard API, parent-frame fallback, legacy selection fallback, mobile-safe manual selection, and the explicit success message **Copied Successfully**. Payloads are regenerated from the current canonical generation after Run Calculation.

## 7. Performance hardening

Applied:

- one canonical calculation source
- no calculation from copy controls or AI display
- intent-bounded AI evidence retrieval
- maximum 20 conversation items
- bounded evidence registry and answer size
- lazy Lunch field rendering retained
- stale history/copy cache invalidation after atomic publication
- processed-result reuse rather than duplicate calculations
- long-table display remains bounded/compact

The requested 30% RAM/CPU reduction is an engineering target, not a claimed measured result. A production Streamlit Cloud telemetry run is required to prove an exact percentage under the user's real dataset and browser workload.

## 8. Verification results

### Automated tests

- **117 relevant regression and V5 tests passed**
- **0 failures** in the final relevant regression run
- Included time-provider precedence, broker display conversion, history sync true/false behavior, atomic watermark verification, missing-schema safety, exact Copy Short fields and limits, AI intent relevance, 20-item memory, >90% duplicate regeneration, Clipboard API, menu ownership, Lunch fields, Settings, performance architecture, six-field structure, UI restoration, history research, and Streamlit Cloud preflight.

### Syntax validation

- All modified modules passed `py_compile`.
- `core`, `ui`, `tabs`, and `services` passed recursive `compileall`.

### Wider suite note

The repository contains **372 collected tests**. A single-process all-suite run did not complete within the execution limit because some existing end-to-end tests are long-running/hanging in this environment. The affected core/runtime file itself completed its assertions successfully when run independently. The final packaged database files were restored from the uploaded project after tests so no test-generated records are shipped.

## 9. Files added

- `core/shared_broker_time_20260622.py`
- `core/history_sync_engine_20260622.py`
- `core/ai_duplicate_guard_20260622.py`
- `tests/test_project_hardening_v5_20260622.py`
- `FINAL_VERIFICATION_REPORT_PROJECT_HARDENING_V5_20260622.md`
- `PROJECT_HARDENING_V5_CHANGE_MANIFEST_20260622.json`

## 10. Runtime verification checklist

After deploying to Streamlit Cloud and running **Settings → Run Calculation + Open Lunch**, verify:

1. Latest Broker Candle equals the intended MetaTrader broker candle.
2. Field 1 Latest History Record matches it with Difference Minutes = 0.
3. Table-level history synchronization reports SYNCED.
4. Ask distinct entry, exit, regime, risk, history, and forecast questions; answers should use different relevant evidence.
5. Ask the same question repeatedly; a >90% duplicate should be restructured.
6. Copy Short and Copy Full should each appear once and show **Copied Successfully** after a permitted clipboard write.
7. Confirm phone and desktop browser clipboard permissions. The manual-select fallback remains available when a browser blocks clipboard access.
