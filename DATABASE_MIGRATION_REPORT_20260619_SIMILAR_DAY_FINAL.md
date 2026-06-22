# Database Migration Report — Similar-Day Intelligence

**Date:** 2026-06-19  
**Schema version:** `1.0.0`  
**New database:** `data/adx_similarity_store.sqlite3`

## Migration result

The migration completed successfully and created an empty, deployment-ready schema. No existing project database table or row was deleted, renamed, rewritten or migrated.

Current packaged counts:

- `similar_day_feature_store`: 0 rows
- `similar_day_generations`: 0 rows

The first successful Run Calculation writes the current generation.

## Tables

### `similar_day_feature_store`

Compact daily/prefix records keyed by:

- symbol
- timeframe
- trading date
- feature version
- completed H1 count

It stores the compact feature vector, normalized return path, regime labels, settled outcome fields, quality flags and creation timestamp. It does not store complete API responses or full market DataFrames.

### `similar_day_generations`

Atomic canonical publication metadata keyed by symbol, timeframe and calculation generation. It stores calculation ID, latest completed H1 timestamp, engine/feature versions, deterministic cache key, compact payload and creation timestamp.

## Indexes

- `idx_similar_feature_lookup`
- `idx_similar_generation_latest`

## Safety controls

- SQLite WAL journal mode
- `BEGIN IMMEDIATE` atomic writes
- stale-generation rejection
- same-generation older-timestamp rejection
- retention limited to the latest two Similar-Day generations per symbol/timeframe
- idempotent `CREATE TABLE IF NOT EXISTS` migration
- independent database file, so existing authentication/canonical/runtime stores are untouched

## Rollback

Stopping the application and deleting only `data/adx_similarity_store.sqlite3` removes Similar-Day cached history without affecting existing project databases. The file and schema are recreated automatically on the next successful calculation.
