# 2026-06-18 Fix — Settings Run Sync + 25-Day History Display

Applied directly to the uploaded project.

## Fixed
- Future broker/API candles are now rejected row-by-row without failing the whole canonical generation when clean completed H1 candles remain.
- Removed `future timestamps` from the hard FAIL_ALL severe condition.
- System-wide publication no longer sends tabs back to the generic `Use Settings → Run Calculation + Open Lunch once...` gate because optional display packs are partial.
- Lunch Full Metric section now prioritizes the 25-day Full Metric history table instead of current-hour priority snapshots.
- Full Metric Detail + History hides current-only decision/detail tables in that history workspace and shows the 25-day history table first.
- Regime inside Full Metric now shows 25-day history tables only, not the current-only regime summary table.
- Suppressed noisy third-party `SettingWithCopyWarning` and sklearn `y_pred contains classes not in y_true` console warnings.

## Files changed
- `core/decision_product_engine_20260617.py`
- `core/system_wide_completion_20260618.py`
- `tabs/final_lunch_upgrade_20260617.py`
- `ui/full_metric_shared_renderer_20260618.py`
- `ui/full_metric_regime_inner_renderer_20260618.py`
- `adx_dashpoard.py`
