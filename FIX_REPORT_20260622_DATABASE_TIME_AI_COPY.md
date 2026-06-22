# ADX Quant Pro — Runtime Fix Report (2026-06-22)

## Scope

This correction keeps the protected calculation logic intact. It changes schema safety, display-time projection, Grounded AI routing/cache behavior, and menu copy controls.

## 1. `prediction_outcomes` crash

### Original failure

`PredictionLedger.settle_pending_outcomes()` queried `prediction_outcomes` directly. A Streamlit Cloud deployment can retain an older or partially initialized SQLite file, so code and database schema can become temporarily mismatched.

### Fix

- Added an idempotent schema verifier for all six required ledger tables.
- Added automatic in-place schema repair before critical operations.
- Added missing-table/missing-column/schema-change retry handling.
- Added bounded lock retries.
- Made outcome settlement non-fatal: if persistent storage is read-only or cannot be repaired, the canonical calculation continues with a clearly reported memory fallback.
- Verified the packaged `data/quant_app.sqlite3` contains `prediction_outcomes` and all other required ledger tables.

### Acceptance test

A temporary database was initialized, `prediction_outcomes` was deliberately dropped, and `settle_pending_outcomes()` was called. The table was recreated and the operation returned successfully.

## 2. Lunch Field 1 broker-time synchronization

### Root causes

- Some valid candle histories store time in a `DatetimeIndex`; the former Field 1 freshness path checked only visible columns.
- Field 1 displayed an old `Hour` value even after another timestamp column was converted.
- Broker and Myanmar clocks were not projected from one normalized UTC source.

### Fix

- Added shared time extraction from timestamp columns, `DatetimeIndex`, and parseable object indexes.
- Normalizes internal timestamps to UTC without changing protected OHLC/calculation data.
- Field 1 now creates a display-only broker-time view.
- Rebuilds `Date`, `Weekday`, and `Hour` from broker time rather than retaining stale values.
- Shows broker candle time and Myanmar time (`UTC+6:30`) side-by-side.
- Uses the same broker-offset state as the Settings market-time display.
- Preserves the configured offset across reruns.
- Adds a current-row overlay from already-loaded published data when Field 1’s historical cache is older than the newest completed H1 candle.

### Important configuration rule

MT5 Python tick epochs are normalized to UTC. The visible broker chart clock depends on the broker’s configured UTC offset. In Settings, set **MT5 broker chart UTC offset (display only)** to the exact offset shown by the broker chart. Myanmar time is always shown separately as `UTC+6:30`; it is not substituted for broker time.

### Acceptance test

A row at `02:00 UTC` with a configured broker offset of `UTC+10` was rendered as:

- Broker Hour: `12:00`
- Myanmar time: `08:30`

The test also confirms a `DatetimeIndex` is accepted as the authoritative candle time.

## 3. Grounded AI Assistant relevance and repeated answers

### Root causes

- Broad decision phrases could override specific questions such as TP/SL.
- The local answer helper began many responses with the same generic decision template.
- Existing cached answers could survive a code upgrade.

### Fix

- Added question-specific intent routes for:
  - broker/Myanmar time and freshness;
  - TP/SL evidence;
  - price forecasts and bands;
  - position sizing and risk;
  - priority/best-hour ranking;
  - regime/alpha/delta;
  - reliability/uncertainty/error;
  - similar-day evidence;
  - historical comparison;
  - system health;
  - current decision explanation.
- Reordered intent precedence so specific categories beat generic decision wording.
- Each route now selects only related canonical evidence and uses a category-specific response structure.
- Added `AI_ANSWER_VERSION = 20260622-question-focused-v2` to the cache key, invalidating older repetitive cached answers.
- Keeps the assistant local, read-only, and grounded. It does not invent missing values, call an external AI API, or trigger protected calculations.

### Acceptance test

Five different questions produced five different routes and headings:

- Market and broker time
- TP / SL evidence
- Price forecast evidence
- Reliability and uncertainty
- Priority and best-hour ranking

## 4. Duplicate/non-clickable copy buttons

### Root cause

The liquid popup rendered Short and Full copy controls in its runtime-action row and then rendered the same canonical copy controls again below. On narrow screens, nested component frames could overlap and intercept taps.

### Fix

- Runtime actions now own only **Refresh Data Only**.
- A single canonical owner renders **Copy Short** and **Copy Full** once.
- Copy components have full-width touch targets, explicit `pointer-events`, high stacking order, `touch-action: manipulation`, and a single click handler.
- Clipboard order is:
  1. secure browser Clipboard API;
  2. parent Clipboard API when allowed;
  3. `execCommand('copy')` fallback;
  4. visible selected text for Ctrl+C or mobile long-press Copy.
- Download/manual fallback remains available where configured.

## Modified files

- `core/prediction_ledger_20260617.py`
- `core/market_time_freshness_20260622.py`
- `core/ai_intent_router.py`
- `core/ai_answer_planner.py`
- `tabs/ai_assistant_compact_20260619.py`
- `tabs/antd_page_router_20260615.py`
- `ui/lunch_four_core_fields_20260619.py`
- `ui/liquid_menu_popup_20260615.py`
- `ui/copy_tools.py`
- `tests/test_user_requested_runtime_fixes_20260622.py`

## Validation performed

- Python bytecode compilation: passed.
- 73 focused and regression tests across database, time, Lunch, Settings, AI, copy UI, mobile/UI restoration, six-field layout, and Streamlit Cloud preflight: passed.
- Included SQLite schema health check: passed; all required tables present.
- Direct local Grounded AI route check: passed.

The repository contains 364 tests. A complete all-test run was attempted, but the container’s execution window was exceeded by a long-running causal end-to-end test. No failure was observed before the timeout, but this report does not claim that all 364 tests completed.
