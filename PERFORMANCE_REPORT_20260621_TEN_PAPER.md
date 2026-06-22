# Before/After Performance Report

## Measurement scope

Synthetic bounded evidence: 384 settled rows, EURUSD-like H1 OHLC, seven repeats, local container Python 3.13.5. Deployment target remains Python 3.12. These measurements quantify implementation overhead only; they do not verify future production latency, accuracy, profitability, or resource reduction.

| Measurement | Mean | p50 | p95 | Max traced allocation | Mean RSS delta | Serialized canonical payload |
|---|---:|---:|---:|---:|---:|---:|
| Existing research validation before | 611.96 ms | 610.01 ms | 636.66 ms | 764,957 B | 0.308 MB | 21,017 B |
| Ten-paper layer only | 1109.08 ms | 1109.29 ms | 1167.33 ms | 2,118,195 B | 0.829 MB | 418,687 B |
| Combined after | 1724.54 ms | 1730.02 ms | 1750.74 ms | 2,182,089 B | 0.227 MB | 438,792 B |

Measured combined-minus-before mean overhead: **1112.58 ms** on this synthetic benchmark.

## SQLite write measurement

| Bundle | Write time | SQL SELECT reads | Database size |
|---|---:|---:|---:|
| Existing validation bundle | 20.12 ms | 0 | 352,256 B |
| Ten-paper bundle | 108.10 ms | 0 | 1,179,648 B |
| Combined bundle | 92.21 ms | 0 | 1,196,032 B |

Statement counts include schema/index checks and transaction statements; detailed counts and per-table inserts are in `PERFORMANCE_MEASUREMENTS_20260621_TEN_PAPER.json`.

## Closed-field and tab-switch cost

The builder has exactly one call site in the Settings orchestrator and zero references in UI/tabs/pages. Therefore closed Lunch fields and ordinary tab reruns do not invoke the ten-paper transaction. They read the last canonical generation only. This is established by static scans and renderer tests; no claim is made that all unrelated existing UI work is zero-cost.

## Delta result

Exact delta updates are accepted only after equality with full recomputation. The benchmark records full and delta timings inside each research payload. Approximate delta logic is not used.

## Acceptance conclusion

The implementation meets the placement and boundedness requirements, but it **does not reduce total calculation CPU time or payload size** in this benchmark. The added statistical evidence has a measurable cost, so no CPU/RAM reduction claim is made. Its main performance protection is that this cost runs only on the existing explicit Settings calculation action, never on field open/close or tab switching.
