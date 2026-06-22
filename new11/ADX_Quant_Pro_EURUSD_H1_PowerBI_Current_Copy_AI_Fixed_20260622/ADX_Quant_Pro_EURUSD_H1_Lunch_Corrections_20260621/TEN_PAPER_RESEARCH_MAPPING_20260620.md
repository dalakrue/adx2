# Ten-Paper Research Mapping — Implemented Boundaries

## 1. TinyLFU: A Highly Efficient Cache Admission Policy

**Mapping:** Bounded frequency admission with LRU victim for reusable canonical/display artifacts. 48 entries/12 MB for UI cache; one-time exports excluded; diagnostics persisted.

**Boundary:** No secrets/raw questions in keys; process-local cache only.

## 2. C-Store: A Column-oriented DBMS

**Mapping:** Column projection on every evidence query; optional partitioned Parquet plus DuckDB only after measured row/DB-size thresholds.

**Boundary:** SQLite retained for transactions/small state; no cosmetic migration.

## 3. Maintenance of Materialized Views: Problems, Techniques, and Applications

**Mapping:** Per-completed-H1 affected-row bundle, deterministic keys, watermarks and idempotent insert.

**Boundary:** No 25-day full recomputation from tab switches.

## 4. The Dataflow Model: A Practical Approach to Balancing Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data Processing

**Mapping:** Latest completed H1 is the event-time watermark; record/target/processing/revision semantics are separated and published atomically.

**Boundary:** Late revisions are explicit; a tab rerun is not an event.

## 5. M4: A Visualization-Oriented Time Series Data Aggregation

**Mapping:** First/last/min/max-preserving visual buckets for Power BI history display.

**Boundary:** Exact raw history remains for statistics and downloads.

## 6. Matrix Profile I: All Pairs Similarity Joins for Time Series: A Unifying View that Includes Motifs, Discords and Shapelets

**Mapping:** Bounded normalized 6/12/24-hour windows, trivial-overlap exclusion, ranked matches, motifs, discords and observed outcomes.

**Boundary:** Runs only in completed-H1 Settings transaction; no direction engine.

## 7. Optimal Detection of Changepoints with a Linear Computational Cost

**Mapping:** Bounded PELT-style changepoints for returns, volatility and range plus evidence hooks for residual/coverage/reliability/priority.

**Boundary:** Bounded penalty; never independently creates a trade direction.

## 8. Conformalized Quantile Regression

**Mapping:** Chronological settled-outcome calibration by H+1…H+6, sparse-condition fallback and ordered intervals.

**Boundary:** EURUSD H1 serial dependence is explicitly outside the original exchangeable-data guarantee.

## 9. Optimal Forecast Reconciliation for Hierarchical and Grouped Time Series Through Trace Minimization

**Mapping:** Shrinkage covariance reconciles a separate display/combined path while retaining each original path and reconciliation delta.

**Boundary:** Protected source paths/weights remain unchanged.

## 10. Comparing Predictive Accuracy

**Mapping:** Diebold–Mariano validation on aligned forecast origin, target and actual; overlapping-horizon correction and named benchmarks.

**Boundary:** Returns INSUFFICIENT DATA when support/alignment is not valid; reliability evidence only.
