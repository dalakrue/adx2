# Rollback Instructions — Six-Field Upgrade

## Full-package rollback

Keep the uploaded base ZIP as the authoritative rollback artifact. Stop the app, back up the current data directory, replace the application directory with the original package, restore connector secrets outside the repository, reinstall `requirements.txt`, and start `app.py`.

## Source-only rollback

The package includes `MODIFIED_FILES_MANIFEST_20260621_SIX_FIELD.json`. Restore each modified file from the original ZIP and remove only the added files listed in the manifest. Do not delete `data/`, connector configuration, secrets, or settled evidence.

## Database safety

This upgrade adds no required database schema migration. Before any rollback, copy all SQLite/DuckDB files to a timestamped backup. The test-generated database mutations were removed from the delivered package by restoring original database files.

## Verification after rollback

1. Run `python -m compileall -q .`.
2. Run the original test suite.
3. Start `streamlit run app.py`.
4. Confirm the latest completed canonical generation is readable.
5. Do not press Run Calculation until connector/source status is verified.
