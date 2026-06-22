# Performance Comparison

## Architectural comparison

| Area | Before this upgrade | After this upgrade |
|---|---|---|
| Regime-change evidence | Existing regime output only | Bounded BOCPD/ADWIN-style evidence around the unchanged regime |
| History persistence | Several display-oriented histories and repeated table shaping | Five normalized DuckDB histories, one transition-outcome view, incremental inserts, and outcome maturation |
| Lunch history views | Repeated physical/display subsets were possible | Compact Decision, Forecast, Regime, Reliability, and Complete column presets over one canonical 25-day dataset |
| Search | No unified Enter-to-search path | Bounded search over cached canonical output and normalized history; no calculator import/call |
| Display interaction | Legacy paths risked repeated imports/work | Large renderers are behind true gates; trust view is cached by run/generation |
| Navigation after calculation | Result could require manual movement | Router opens Lunch Field 1 and reuses the already-published generation |

## Measured synthetic benchmark

Source: `PERFORMANCE_MEASUREMENTS_20260621_REGIME_TRUST.json`. Measurements were run in the available validation environment on 768 synthetic H1 rows and 180 settled prediction rows. They are engineering comparisons, not trading-performance claims.

| Operation | Mean | P95 | Execution rule |
|---|---:|---:|---|
| Regime trust evidence build | ~79 ms | ~83 ms | Once, only during successful Run Calculation |
| Lunch search submission | ~199 ms | ~231 ms | Only when the user submits the search form |
| First incremental DuckDB write | ~249 ms | one run | After canonical publication |
| Duplicate/idempotent DuckDB write | ~172 ms | ~190 ms | Inserts zero duplicate rows |
| Projected top-five transition query | ~60 ms | ~73 ms | Cached display query; no trading calculation |

The previous ten-paper calculation benchmark measured approximately 1,725 ms mean for the combined existing research path. The new evidence layer adds about 79 ms in the synthetic benchmark—roughly 4.6% of that earlier measured path—and only on Run Calculation. Widget navigation, opening fields, changing inner tabs, and viewing cached evidence do not pay this calculation cost.

## Data-volume controls

- BOCPD is bounded to the latest 240 normalized returns.
- Adaptive-window evidence is bounded to 512 returns.
- Search flattening and history results have explicit caps.
- DuckDB queries are limited and project only required columns for display.
- Recent search history is bounded to eight items.
- The complete visible 25-day table remains available and is not shortened by the adaptive detector window.
