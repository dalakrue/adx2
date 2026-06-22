from __future__ import annotations

from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_app_starts_from_app_py_and_python_312_contract():
    ast.parse(text("app.py"))
    assert "from adx_dashpoard import main" in text("app.py")
    assert text("runtime.txt").strip() == "python-3.12"
    assert "streamlit run app.py" in text("app.py")


def test_no_absolute_local_windows_paths_in_package_text():
    pattern = re.compile(r"[A-Za-z]:[\\/]Users[\\/]")
    allowed_suffixes = {".py", ".md", ".txt", ".toml", ".json", ".yaml", ".yml", ".ini", ".cfg", ".csv"}
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if pattern.search(content):
            hits.append(path.relative_to(ROOT).as_posix())
    assert hits == []


def test_copy_export_and_complete_history_are_still_present():
    lunch = text("ui/lunch_four_core_fields_20260619.py")
    readiness = text("ui/system_readiness_20260621.py")
    similar = text("ui/similar_day_renderer_20260619.py")
    copy_export = text("ui/canonical_copy_export_20260619.py")
    assert "render_canonical_copy_export" in readiness
    assert "Prepare Short" in copy_export and "Prepare All" in copy_export and "Prepare JSON" in copy_export
    assert "Complete view" in similar
    assert "history_25" in similar
    assert "Complete Descending 25-Day History Table" in similar
    assert "render_system_readiness" in lunch

def test_last_valid_result_fallback_and_noncritical_error_records_exist():
    orchestrator = text("core/settings_run_orchestrator_20260617.py")
    store = text("core/regime_trust_store_20260621.py")
    assert "previous canonical generation was preserved" in orchestrator.lower()
    assert "FAILED SAFELY" in orchestrator
    for field in ("timestamp", "component", "run_id", "exception_type", "safe_summary", "fallback_used"):
        assert field in store


def test_required_delivery_documents_and_migration_script_exist():
    required = (
        "TEST_RESULTS_REPORT.md", "RESEARCH_TO_FEATURE_MAPPING.md", "ARCHITECTURE.md",
        "HISTORY_TABLE_DATA_DICTIONARY.md", "PERFORMANCE_COMPARISON.md", "CHANGELOG.md",
        "KNOWN_LIMITATIONS.md", "STREAMLIT_CLOUD_DEPLOYMENT.md", "WINDOWS_POWERSHELL_RUN.md",
        "scripts/migrate_regime_trust_20260621.py",
    )
    # Documents are created before final test execution.
    missing = [item for item in required if not (ROOT / item).exists()]
    assert missing == []
