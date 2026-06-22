# Leakage and Causality Report

## Static leakage scan

`LEAKAGE_STATIC_SCAN_20260621_TEN_PAPER.json` reports:

- negative shift patterns: 0;
- centered rolling patterns: 0;
- future backfill patterns: 0;
- random train/test split patterns: 0;
- full-sample scaler patterns: 0;
- research builder call sites in orchestrator: 1;
- research builder references in UI/tabs/pages: 0;
- DataFrame assignments to session state in the new layer: 0.

## Time-series controls

Settled evidence is chronologically sorted. Model-X and flexible-loss validation use two adjacent chronological windows with explicit purge and embargo. The evidence gate requires embargo of at least six rows, matching the declared maximum horizon. Completed-H1 filtering excludes future/incomplete append rows.

## Metamorphic leakage defenses

Tests cover future incomplete-candle append invariance, row-order invariance after canonical sorting, duplicate timestamp rejection, deterministic identity, and phone/full history overlap equality.

## Causality boundary

SHAP/linear/rule contributions are labeled attribution, not causal evidence. The implementation does not infer intervention effects from prediction explanations. Existing DML/IRM/Group-DRO mechanisms are not modified and are not treated as proof that a displayed feature caused a market move.

## Remaining limitations

- Intrahour first-touch order is unavailable in the settled ledger, so TP-late and SL-first components are proxies.
- Estimated time-series knockoffs do not establish exact Model-X exchangeability.
- Online FDR guarantees depend on p-value validity and dependence assumptions not proven by code alone.
- Historical backtests cannot rule out structural market change.
