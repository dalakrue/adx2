# Performance Report — 2026-06-20

## Measurement scope

Representative bounded synthetic workload:

- 720 completed UTC H1 rows (the live maximum)
- 3,000 chronological settled prediction rows (below the 6,000 hard bound)
- five warmed runs
- persistence disabled to isolate computation
- Linux container, Python 3.13.5; deployment target remains Python 3.12

The baseline is the same input normalization plus a top-level canonical copy. It is not a historical whole-app benchmark. The advanced measurement is the full hidden v2 transaction.

## Measured results

| Measurement | Baseline median | Advanced median |
|---|---:|---:|
| Execution time | 0.1262 s | 4.0320 s |
| Incremental median | — | 3.9058 s |
| Peak Python allocation (tracemalloc) | 3,442,436 B | 3,442,731 B |
| Median process RSS delta | 0 B | 221,184 B |
| Maximum process RSS observed | 381,067,264 B | 382,742,528 B |

Advanced range across five runs: 3.8730–4.1228 seconds. Full raw measurements are in `reports/PERFORMANCE_MEASUREMENTS_20260620.json`.

## Performance controls

- heavy work runs only on existing Run Calculation;
- no renderer or tab-navigation training;
- 720 OHLC and 6,000 settled-row hard bounds;
- 128 samples per MMD side;
- deterministic bounded permutation count;
- compact JSON and bounded-vector persistence;
- no large DataFrame added to session state;
- copy-on-write selected forecast mapping, not a full canonical deep copy;
- DML is explicit maintenance/offline only;
- IRM and Group DRO use settled bounded evidence during Run Calculation, never navigation.

## Claims deliberately not made

- No phone-temperature improvement was measured.
- No production forecast/decision accuracy improvement is claimed.
- No live broker/API end-to-end latency was measured.
- Process RSS is affected by allocator reuse; delta values are therefore reported alongside peak process RSS and tracemalloc.
