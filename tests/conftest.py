"""Shared test fixtures for the Shuheng test suite.

Tests import from the installed `shuheng` package (pythonpath=src in
pyproject.toml). Most target functions are pure; they only need isolated
filesystem paths so they never touch the user's real ~/.shuheng state.
"""
from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure src/ is importable even when pytest runs without install.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Shuheng binds its storage roots when shuheng.app is imported. Test modules
# import app during collection, before fixtures can run, so isolate the whole
# pytest process here. Each concurrently running pytest process receives a
# different root and subprocesses inherit it through os.environ.
if "shuheng.app" in sys.modules:
    raise RuntimeError("tests/conftest.py must isolate SHUHENG_HOME before shuheng.app is imported")

_TEST_HOME_OWNER_PID = os.getpid()
_TEST_PROCESS_HOME = os.environ.get("HOME", "")
_TEST_ORIGINAL_SHUHENG_HOME = os.path.abspath(
    os.path.expanduser(os.environ.get("SHUHENG_HOME") or "~/.shuheng")
)
_TEST_SHUHENG_HOME = Path(tempfile.mkdtemp(prefix=f"shuheng-pytest-{_TEST_HOME_OWNER_PID}-"))
os.environ["SHUHENG_TEST_ORIGINAL_HOME"] = _TEST_ORIGINAL_SHUHENG_HOME
os.environ["SHUHENG_TEST_ISOLATED_HOME"] = str(_TEST_SHUHENG_HOME)
os.environ["SHUHENG_HOME"] = str(_TEST_SHUHENG_HOME)
os.environ["SHUHENG_HARNESS_DIR"] = str(_TEST_SHUHENG_HOME / "memory" / "agent_harness")
os.environ["SHUHENG_SECRET_VAULT_DIR"] = str(_TEST_SHUHENG_HOME / "memory" / "secret_vault")


def _cleanup_test_shuheng_home() -> None:
    # Forked children inherit atexit handlers. Only the process that created
    # this root may remove it; cleanup is deliberately idempotent.
    if os.getpid() == _TEST_HOME_OWNER_PID:
        shutil.rmtree(_TEST_SHUHENG_HOME, ignore_errors=True)


atexit.register(_cleanup_test_shuheng_home)


def pytest_unconfigure(config) -> None:
    del config
    _cleanup_test_shuheng_home()


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
    shuheng_home = home / ".shuheng"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SHUHENG_HOME", str(shuheng_home))
    monkeypatch.setenv("SHUHENG_HARNESS_DIR", str(shuheng_home / "memory" / "agent_harness"))
    monkeypatch.setenv("SHUHENG_SECRET_VAULT_DIR", str(shuheng_home / "memory" / "secret_vault"))
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
    try:
        yield reloaded
    finally:
        # Restore the process-level isolated roots, never production paths.
        if _TEST_PROCESS_HOME:
            monkeypatch.setenv("HOME", _TEST_PROCESS_HOME)
        else:
            monkeypatch.delenv("HOME", raising=False)
        monkeypatch.setenv("SHUHENG_HOME", str(_TEST_SHUHENG_HOME))
        monkeypatch.setenv("SHUHENG_HARNESS_DIR", str(_TEST_SHUHENG_HOME / "memory" / "agent_harness"))
        monkeypatch.setenv("SHUHENG_SECRET_VAULT_DIR", str(_TEST_SHUHENG_HOME / "memory" / "secret_vault"))
        importlib.reload(app_module)
