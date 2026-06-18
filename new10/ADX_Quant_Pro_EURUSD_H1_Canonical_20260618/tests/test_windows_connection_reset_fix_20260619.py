from __future__ import annotations

import asyncio
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sitecustomize_is_valid_and_loads_before_streamlit_command():
    source = (ROOT / "sitecustomize.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "install_windows_selector_policy" in source
    assert "import streamlit" not in source.lower()


def test_windows_policy_helper_is_non_windows_noop_here():
    from core.windows_asyncio_compat_20260619 import install_windows_selector_policy

    before = type(asyncio.get_event_loop_policy()).__name__
    result = install_windows_selector_policy()
    after = type(asyncio.get_event_loop_policy()).__name__
    if sys.platform != "win32":
        assert result["installed"] is False
        assert result["reason"] == "non-Windows platform"
        assert before == after


def test_fix_is_targeted_not_exception_suppression():
    source = (ROOT / "core/windows_asyncio_compat_20260619.py").read_text(encoding="utf-8")
    assert "WindowsSelectorEventLoopPolicy" in source
    assert "set_exception_handler" not in source
    assert "ConnectionResetError" in source
    assert "WinError 10054" in source


def test_windows_batch_uses_preferred_entry_file():
    batch = (ROOT / "RUN_APP_WINDOWS.bat").read_text(encoding="utf-8")
    assert "python -m streamlit run app.py" in batch
