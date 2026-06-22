# Pre-Implementation Performance Baseline

## Available measured baseline

The uploaded package contained `reports/PERFORMANCE_MEASUREMENTS_20260620.json`, measured on Python 3.13.5 with a bounded synthetic fixture of 720 completed H1 rows and 3,000 settled rows.

| Component | Runs | Median elapsed | Peak Python allocation |
|---|---:|---:|---:|
| normalization + top-level canonical copy | 5 | 0.1262 s | 3,444,099 bytes maximum |
| existing advanced reliability live transaction | 5 | 4.0320 s | 3,445,002 bytes maximum |

The prior report measured an incremental median of 3.9058 seconds for that existing advanced layer. It explicitly did not measure the complete Streamlit application, browser rendering, phone temperature, live network latency, or production profitability.

## Static pre-change pressure indicators

- 471 Python files.
- 568 `.copy(...)` call sites.
- 305 `sort_values(...)` call sites.
- 53 `groupby(...)` call sites.
- 5 explicit merge call sites.
- 187 `.join(...)` call sites.
- 25 direct SQLite connection call sites.
- 6 `BEGIN IMMEDIATE` sites.

These are source-level counts, not runtime invocation counts. Compatibility and legacy files inflate them.

## New-layer benchmark protocol

The 2026-06-21 benchmark uses:

- 720 completed H1 candles;
- 3,000 canonical settled rows;
- 12,000 method-loss rows;
- `ADX_TEST_PROFILE=fast`;
- 49 deterministic moving-block SPA bootstrap iterations;
- `tracemalloc` plus process RSS sampling;
- persistence disabled for the isolated layer benchmark.

This protocol is intentionally fast and reproducible. It does not establish a whole-app before/after latency comparison because the earlier and current benchmarks cover different isolated components.
