# Rollback / Backup Note

The original uploaded ZIP remains unchanged outside the modified project folder. This final release does not perform a destructive migration on existing SQLite or CSV data.

## Full rollback

1. Stop Streamlit.
2. Keep a copy of any new runtime data you want to retain.
3. Replace the modified project directory with the original uploaded ZIP contents.
4. Reinstall the original `requirements.txt` only if your environment changed.
5. Run the original entry file.

## Similar-Day-only rollback

Revert these integration files to their original versions:

- `core/settings_run_orchestrator_20260617.py`
- `core/canonical_runtime_20260617.py`
- `core/compact_canonical_20260619.py`
- `ui/lunch_four_core_fields_20260619.py`

Then remove:

- `core/similar_day_config_20260619.py`
- `core/similar_day_intelligence_20260619.py`
- `ui/similar_day_renderer_20260619.py`
- `data/adx_similarity_store.sqlite3`

Deleting the new Similar-Day database does not affect authentication, canonical runtime, Full Metric, Power BI, regime or existing history databases.
