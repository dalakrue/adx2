MOBILE FILE ARCHITECTURE MIGRATION - 2026-06-09

Goal
- Split every Python file over 500 lines into smaller module chunks.
- Preserve all existing import paths and function names.
- Keep the app runnable through the existing entry point: streamlit run main.py
- Reduce editor/import scanning overhead on lower-memory devices such as iPhone 11 Pro / mobile Streamlit sessions.

What changed
- 16 oversized Python files were converted into small compatibility loaders.
- Each original source was divided into sibling *_parts/part_XXX.py chunk modules.
- Existing imports still work because each loader executes the chunks inside the original module namespace.
- No active .py file is now over 500 lines.

Split files
- core/pro_terminal_uiux.py
- tabs/home.py
- tabs/legacy_impl/upgraded_doo_prime_home_impl.py
- tabs/train/legacy_impl/train_data_legacy_impl.py
- tabs/profile_dashboard_split/legacy_impl/constants_impl.py
- tabs/profile_dashboard_split/profile_dashboard_split/legacy_impl/constants_impl.py
- tabs/pre_clean_split/legacy_impl/exit_survivability_impl.py
- tabs/pre_clean_split/legacy_impl/history_engine_impl.py
- tabs/home_split/legacy_impl/reversal_engine_full_correct_patch_impl.py
- tabs/engine_split/legacy_impl/original_backtest_inner_impl.py
- tabs/engine_split/legacy_impl/original_engine_inner_impl.py
- tabs/engine_split/legacy_impl/original_prelive_inner_impl.py
- tabs/account_split/legacy/implementation.py
- core/legacy_impl/global_upgrade_impl.py
- core/legacy_impl/system_contract_impl.py
- core/ui/legacy_impl/styles_impl.py

Validation completed
- python -m compileall -q .
- python tools/validate_architecture.py

Result
- Architecture validation passed.
- Run app with: streamlit run main.py
