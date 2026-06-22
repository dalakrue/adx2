# Before/After Performance Report — History-First Workload

## Measurement boundary

Local synthetic completed-H1 workload on Python 3.13.5; no authenticated broker/API, no browser DOM profiler and no live phone thermal measurement. “Before/after Lunch” uses identical injected renderer work to isolate dispatch. Computation, render dispatch, serialized payload and process RSS are reported separately.

## Closed Lunch / tab-switch dispatch

| Measurement | Before | After |
|---|---:|---:|
| Mean rerun dispatch | 20.768 ms | 0.013 ms |
| Heavy renderer calls/rerun | 8.0 | 0.0 |
| Python peak allocation | 1,516,631 B | 1,096 B |
| Process RSS delta | 0.914 MB | 0.000 MB |

The after result proves the true gate dispatch path does no heavy work while all fields are closed. It does not claim that a full live Streamlit rerun takes 0.013 ms.

## Selected field dispatch

| Field/workspace | Mean dispatch | Heavy calls/rerun | Python peak | RSS delta |
|---|---:|---:|---:|---:|
| Field 1 | 4.751 ms | 2.0 | 1,456,794 B | 0.734 MB |
| Field 2 | 2.581 ms | 1.0 | 1,450,438 B | 0.000 MB |
| Field 3 | 2.833 ms | 1.0 | 1,450,338 B | 0.000 MB |
| Field 4A | 2.633 ms | 1.0 | 1,450,438 B | 0.000 MB |
| Field 4B | 2.418 ms | 1.0 | 1,450,388 B | 0.000 MB |
| Field 6 | 2.596 ms | 1.0 | 1,450,438 B | 0.000 MB |

## Completed-H1 history transaction

- Evidence computation: **1212.234 ms** for **229 prepared rows**.
- Python peak allocation: **619,190 B**; process RSS delta **1.000 MB**.
- TinyLFU diagnostic sample: hit ratio **0.500**, 3 admissions, 0 evictions.
- Atomic SQLite write: **297.356 ms** in the synthetic benchmark.

## Browser rows and serialized payload

- 48-row projected query: 9.032 ms; 19,615 serialized CSV bytes.
- 120-row request returned 96 available rows: 9.495 ms; 38,800 bytes.
- Full export is not built until explicit action: 96 rows in 10.498 ms in the synthetic store.
- M4 display test: 10,000 raw rows -> 364 display rows; 573,877 -> 20,876 bytes (**96.362%** reduction); aggregation 30.725 ms.

## Requested workload status

| Requested item | Status |
|---|---|
| Settings complete calculation time | Not reproducible without the user’s authenticated live connector/exact input generation; history transaction measured separately above. |
| Cold/warm Lunch open | Closed-field dispatch measured; complete browser/server cold/warm timing requires a running user deployment. |
| Tab-switch time | Dispatch component measured; full network/browser rerun not claimed. |
| Fields 1–6 open | Controlled per-field dispatch measured above. |
| Morning open | Structural lazy-import tests passed; live browser timing not claimed. |
| Research Data Analysis/Data Mining/NLP open | Structural lazy-import tests passed; live model/API timing not claimed. |
| Python allocation/process RSS | Measured above with tracemalloc/process RSS. |
| Browser rows/payload | Server-side rows and serialized payload measured; DOM/Plotly websocket framing not measured. |
| Database query time | Measured above. |
| Cache hit ratio | TinyLFU synthetic diagnostic measured; production ratio accumulates in history. |
| Heavy renderer calls/rerun | Before/after controlled count measured above. |

Raw measurements: `PERFORMANCE_MEASUREMENTS_20260620_HISTORY_FIRST.json`.
