# Lunch Current-Hour, Copy Buttons, and AI Assistant Fix — 2026-06-22

## Completed fixes

1. **All Lunch fields now prefer the freshest completed market generation**
   - Full Metric, priority, regime, and Power BI cache selectors compare their latest candle timestamps instead of accepting the first legacy alias.
   - Stale 02:00 caches no longer outrank a newer 11:00 cache.

2. **Power BI chart hour is synchronized with the Lunch history hour**
   - Plotly receives timezone-naive source-clock values at display time only.
   - Browser timezone conversion can no longer change a source 11:00 candle into 02:00.
   - Validation calculations remain timezone-aware and unchanged.

3. **Field 3 is now atomically synchronized with the canonical generation**
   - Regime tables are staged during calculation.
   - They are published to Lunch only after canonical publication succeeds.
   - A rejected run can no longer make Field 3 show a newer hour than Fields 1, 2, 4, 5, and 6.

4. **False canonical rejection fixed**
   - Signed return/change/error/skill percentages are no longer incorrectly treated as bounded 0–100 fields.
   - Explicit confidence, reliability, accuracy, coverage, and probability domains remain protected.
   - An exact completed-H1 boundary is accepted after the source completion gate has already passed it.

5. **Grounded AI Assistant restored**
   - The assistant compares its fact pack with the current canonical generation.
   - It rebuilds a stale pack from the newest valid canonical result.
   - It can restore valid runtime pointers from legacy aliases before answering.
   - It still refuses to fabricate trading values when no valid completed generation exists.

6. **Menu Copy Short and Copy Full are real stacked buttons**
   - The narrow three-column menu layout was removed.
   - Copy Short and Copy Full now render as full-width clipboard buttons suitable for phone and desktop use.
   - Before calculation, visible disabled button placeholders are shown instead of vertically wrapped text.

## Validation performed

- Python compile validation: passed for modified modules.
- Focused regression suite: **61 passed**.
- Wider suite checkpoint: **216 passed** before two environment-only failures caused by `duckdb` not being installed in the test container. The project already declares `duckdb>=0.10,<2` in `requirements.txt`.
- Fresh-cache and source-clock smoke tests: passed.
- Original SQLite runtime databases were restored unchanged before packaging.

## Modified files

- `core/canonical_data_validation_20260621.py`
- `core/settings_run_orchestrator_20260617.py`
- `tabs/ai_assistant_compact_20260619.py`
- `ui/canonical_copy_export_20260619.py`
- `ui/lunch_four_core_fields_20260619.py`
- `ui/main_menu_drawer.py`
- `ui/powerbi_cached_renderer_20260619.py`
- `tests/test_one_click_freshness_ai_copy_20260622.py`
