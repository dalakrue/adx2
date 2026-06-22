# Performance Report — Similar-Day Final

All numbers below were measured on the same container and synthetic EURUSD H1 fixture unless marked unavailable. No percentage improvement is inferred from noise.

## Similar-Day calculation

- Fixture: 1,055 H1 rows, 44 represented business days, 25 attempted candidates, eight Stage-2 candidates.
- Separate-process function duration: **1.963 seconds**.
- Separate-process total wall time including Python/pandas imports: **4.56 seconds**.
- Separate-process maximum RSS: **299,052 KB**. This includes the Python interpreter, pandas, NumPy and imported project modules; it is not the incremental Similar-Day-only memory.
- Python allocation peak under `tracemalloc`: **1,163,935 bytes**. The instrumented run was slower because tracing was enabled.
- Four repeated cache hits: 0.0193, 0.0175, 0.0167 and 0.0185 seconds; mean **0.0180 seconds**.
- Cache test sequence hit rate: **80%** (one miss followed by four hits). This is a controlled test rate, not a prediction of real-session behavior.

## SQLite feature store

- Empty schema migration: **0.0075 seconds**.
- Atomic persistence of 25 compact feature rows plus one generation: **0.0153 seconds**.
- Mean latest-generation read over ten reads: **0.0044 seconds**.
- Maximum latest-generation read: **0.0048 seconds**.
- Temporary populated benchmark database: **90,112 bytes**.

## Original versus modified regression workload

The same 95 deployment-critical tests were run against the original extracted project and the modified project:

| Measure | Original | Modified |
|---|---:|---:|
| Pytest result | 95 passed in 13.02 s | 95 passed in 12.63 s |
| External wall clock | 19.27 s | 19.07 s |
| Maximum RSS | 582,008 KB | 581,068 KB |

The difference is small and within ordinary process/test noise. It is reported as **no material regression**, not as a claimed app-wide performance gain.

## Structural performance changes

- Similar-Day builder calls in the Settings run transaction: **1**.
- Similar-Day builder calls in Lunch/UI renderers: **0**.
- Bounded in-session generations: **2**.
- Cache TTL: **21,600 seconds**.
- New 16-card UI: one responsive HTML grid rather than 16 separate Streamlit metric components.
- Numerical OHLCV/feature arrays: `float32` where verified safe.
- Stored data: compact daily vectors/outcomes; no complete API response or full market DataFrame is placed in the Similar-Day session cache/database.
- Full pre-existing DataFrame-copy paths removed: **0**. Existing protected paths were not rewritten without a reproducible live benchmark.
- Pre-existing active canonical Similar-Day calculation paths removed: **0**. No active canonical equivalent existed; embedded legacy/demo code was preserved.

## Not reliably measurable in this environment

- full live canonical calculation duration before/after
- actual browser rerun count in a real Streamlit session
- real Streamlit startup duration
- iPhone 11 Pro temperature, battery draw or Safari memory
- production cache hit rate

These are not estimated. The new static lifecycle guarantees that opening Field 4, switching a tab, scrolling or reading a cached result does not call the Similar-Day builder.
