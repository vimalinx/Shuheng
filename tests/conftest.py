"""Shared test fixtures for the Shuheng test suite.

Tests import from the installed `shuheng` package (pythonpath=src in
pyproject.toml). Most target functions are pure; they only need isolated
filesystem paths so they never touch the user's real ~/.shuheng state.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src/ is importable even when pytest runs without install.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture()
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect all Shuheng home/state dirs to a temp dir.

    shuheng.app reads several env vars at import time. Because the module is
    imported once per session, tests that need a *fresh* home should use the
    reset_app_state fixture. For pure-function tests this fixture is a no-op
    convenience that documents intent.
    """
    home = tmp_path / "fake_home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SHUHENG_HARNESS_DIR", str(home / "harness"))
    monkeypatch.setenv("SHUHENG_SECRET_VAULT_DIR", str(home / "secret"))
    return home


@pytest.fixture()
def fresh_app(isolated_home: Path, monkeypatch: pytest.MonkeyPatch):
    """Import shuheng.app with isolated paths via importlib.reload.

    This re-executes module-level path constants against the isolated_home env
    so SECRET_VAULT_DIR / AGENT_HARNESS_DIR point at temp dirs. Use sparingly;
    prefer the plain `app` fixture for pure-function tests that don't depend on
    path globals.
    """
    import importlib

    import shuheng.app as app_module

    reloaded = importlib.reload(app_module)
    yield reloaded
    # Restore the original module so other tests see production paths.
    importlib.reload(app_module)
