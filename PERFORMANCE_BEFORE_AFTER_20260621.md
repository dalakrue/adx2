# Performance Before/After Report

## Measurement scope

The included harness `tools/benchmark_six_field_upgrade_20260621.py` is reproducible and records Wall-clock time, CPU time, Peak RSS, Session-state approximate size, Cache entries, DataFrame count, and Largest retained objects. The audit container did not initially include Streamlit or a browser, so browser paint, live connector latency, and the protected Run Calculation transaction were not fabricated. Those rows are explicitly marked `NOT_MEASURED_LIVE` in `PERFORMANCE_MEASUREMENTS_20260621_SIX_FIELD.json`.

## Key measured results

| Action | Before median wall | After median wall | Before peak allocation | After peak allocation | Interpretation |
|---|---:|---:|---:|---:|---|
| Copy All | 1122.0828 ms | 0.6131 ms | 6853.04 KiB | 7.54 KiB | Old path serialized raw canonical/DataFrames; new path emits six bounded summaries. |
| Field 3 history query | 10.7335 ms | 15.5608 ms | 560.59 KiB | 229.85 KiB | After path projects only regime columns; ordinary H1 views use vectorized pandas and larger histories use DuckDB pushdown. |
| Copy Short | 0.2227 ms | 0.8657 ms | 3.29 KiB | 12.52 KiB | New path validates budgets/stats while remaining sub-millisecond in the fixture. |
| Refresh Data | N/A | 11.3542 ms | N/A | 137.19 KiB | Connector function injected; no network and no calculation. |
| AI simple | N/A | 2.7677 ms | N/A | 44.52 KiB | Local bounded evidence pipeline. |
| AI complex | N/A | 2.8227 ms | N/A | 43.31 KiB | Same bounded stages with larger source requirements. |
| Reduce RAM | N/A | 1.7522 ms | N/A | 0.11 KiB | Reconstructable cache clear only. |

Copy All fixture size changed from **3,557,061** characters to **1,453** characters. Copy Short measured **25 lines**, **850 characters**, and approximately **213 tokens**.

## Field gates

The six open/close callbacks measured approximately 0.015–0.020 ms each in the headless harness. These numbers cover the actual persistent state callback, not the selected field renderer. Closed gates perform no field renderer import. Field-specific service costs are represented by the history, copy, AI, refresh, and cache rows.

## Retained state snapshot

- Session-state approximate size: 754,052 bytes
- Cache entries: 0
- DataFrame count: 0
- Largest retained objects: `canonical_result_20260617` at 746,321 bytes

## Honest boundary

No claim is made that CPU usage will fall from 309% to 50%. Actual production CPU/heat depends on connector latency, data volume, open field, browser, Streamlit reruns, and host resources. Run the same harness plus a live browser profiler in the deployment environment before making a production percentage claim.
