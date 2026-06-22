# Rollback Instructions — History-First Upgrade

## Preferred full rollback

1. Stop Streamlit.
2. Keep a copy of the current folder.
3. Restore the original uploaded ZIP, or copy back the files listed as modified in `MODIFIED_FILES_MANIFEST_20260620.md`.
4. Restore the canonical database:

```powershell
Copy-Item -Force ".\data\canonical_runtime.sqlite3.before_history_20260620.bak" ".\data\canonical_runtime.sqlite3"
Remove-Item -Force -ErrorAction SilentlyContinue ".\data\canonical_runtime.sqlite3-wal", ".\data\canonical_runtime.sqlite3-shm"
```

5. Restart with `streamlit run app.py`.

## Schema-only rollback helper

```powershell
python .\tools\rollback_history_evidence_20260620.py --restore-backup
```

The migration is additive. Older code ignores the new tables, so dropping them is not required when restoring the original database backup.

## Code-only rollback

Revert the modified files in the manifest and remove the new `*_20260620.py` history/research/browser/tool files. Do not remove any pre-existing report/module from the original package.
