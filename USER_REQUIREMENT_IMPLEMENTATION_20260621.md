# User Requirement Implementation — Lunch Fields 1, 2, 5 and 6

Date: 2026-06-21  
Application: ADX Quant Pro — EURUSD H1  
Entry command: `streamlit run app.py`

## Implemented result

### Lunch Field 1 — only two visible history groups

The Field 1 open/close gate now renders only:

1. `Overall Full Metric History — Last 25 Days`
2. `All 10 Decision Histories — Last 25 Days`

The previous current-snapshot tables, medium-standard card, evidence browser and duplicate copy/export block are not rendered inside Field 1. Their functions remain in the source for rollback and other compatibility routes; no protected calculation or historical dataset was deleted.

### Lunch Field 2 — more valid direction-accuracy evaluation

The protected point forecast, red/yellow/blue paths and BUY/SELL decision logic are unchanged. A new validation-only wrapper:

- evaluates the actual outcome from the forecast origin (`Pred Open`) rather than from the target candle's own open;
- derives each actionability threshold only from ranges settled before that validation row;
- marks tiny forecast moves as `WAIT / NOT_ACTIONABLE` rather than forcing UP or DOWN;
- reports causal actionable accuracy, balanced direction accuracy, actionable coverage and minimum-support status;
- retains the old candle-body direction accuracy as `legacy_direction_accuracy_pct` for audit;
- never promotes WAIT and never reverses BUY to SELL or SELL to BUY.

This improves the correctness and usefulness of the accuracy measurement. It does not guarantee that the model's future hit rate or profitability will increase.

### Lunch Field 5 — false “Run Calculation” message fixed

Field 5 now checks the compact fact pack first and, when it is missing, rebuilds that small read-only projection from the last valid completed canonical generation. This recovery:

- does not call the Settings orchestrator;
- does not retrain or recalculate any model;
- does not query large histories;
- does not alter any protected score or decision;
- preserves generation replacement checks before publishing an answer.

Therefore, a valid completed Settings calculation is usable by the AI Assistant even when the optional compact cache key was lost during a Streamlit rerun.

### Lunch Field 6 — future strategy research history

The former generic `End-to-End Preparation and System Readiness` A–F checklist was replaced by `Future Strategy Research & Historical Evidence`.

The field now provides bounded, read-only access to research evidence not duplicated in Fields 1–5:

- ML production-readiness and feature-selection history;
- conditional predictive ability and SPA/model-comparison history;
- covariate-shift conformal and flexible-loss history;
- FFORMA/fixed-share expert-weight history;
- reject-option and online-FDR history;
- monotonicity, delta-equality, metamorphic, CALM and evidence-gate history;
- research-paper run/promotion history;
- a searchable equation, theorem/property, concept and hypothesis registry explaining assumptions, EURUSD H1 relevance, evidence tables, production influence and guarantee boundaries.

Only one selected database table is queried at a time. Queries use a read-only SQLite URI, projected columns and a hard 120-row display limit. Empty tables display `INSUFFICIENT EVIDENCE`; they are never interpreted as zero risk.

The packaged database currently contains zero settled rows in the 19 selected future-strategy tables, so the correct packaged status is `INSUFFICIENT EVIDENCE`. Future rows can appear only after the existing Settings calculation publishes them and their evidence gates pass.

## Protection confirmation

Unchanged SHA-256 hashes versus the uploaded ZIP:

- `core/settings_run_orchestrator_20260617.py`: `bdedf3fd39ec5f36f07187ae0efdcd957d21b9a68898178eb2958781fae19745`
- `core/decision_product_engine_20260617.py`: `e26c948f88a96f3af4881a2d0e1b06738b4f5b9e2a872b002d8d0aa8aabdfe76`
- `core/canonical_runtime_20260617.py`: `2d5b1007290b5cf92a493fcebb92353b24cf4af9a1025036cf88b1e869c0bf89`
- `tabs/home_parts/part_005.py` (original protected Power BI forecast implementation): `8e99f9a998f1258ff0fef51faf369efa49bebc5e9932094e856fa644e3583e92`

No new top-level page, tab, sidebar item or seventh Lunch field was added.

## Validation result

- Python files compiled: **521**, errors: **0**
- Pytest tests collected and passed: **347 / 347**
- Headless Streamlit startup: **PASS**, server reached `127.0.0.1:8765`
- SQLite integrity checks: **4 / 4 `ok`**
- DuckDB open/integrity check: **1 / 1 `OPEN_OK`**
- Preferred entry point: **`streamlit run app.py`**

See `TEST_REPORT_20260621_USER_CORRECTIONS.md`, `DATABASE_INTEGRITY_20260621_USER_CORRECTIONS.json`, and `PROTECTED_LOGIC_CONFIRMATION_20260621_USER_CORRECTIONS.md`.
