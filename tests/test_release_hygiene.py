"""Tests for release hygiene guards."""
from __future__ import annotations

from scripts import check_release_hygiene as hygiene


def test_wheel_smoke_release_mode_rejects_no_deps(monkeypatch) -> None:
    command = f"PYTHONDONTWRITEBYTECODE=1 python {hygiene.RELEASE_WHEEL_SMOKE_FRAGMENT}"
    texts = {
        "README.md": command,
        "README.en.md": f"{command} --no-deps",
        ".github/workflows/ci.yml": command,
    }

    monkeypatch.setattr(hygiene, "read_text", lambda path: texts[path])

    errors: list[str] = []
    hygiene.check_wheel_smoke_release_mode(errors)

    assert any("README.en.md release wheel smoke must not use --no-deps" in error for error in errors)


def test_wheel_smoke_release_mode_rejects_wheel_only(monkeypatch) -> None:
    command = f"PYTHONDONTWRITEBYTECODE=1 python {hygiene.RELEASE_WHEEL_SMOKE_FRAGMENT}"
    texts = {
        "README.md": command,
        "README.en.md": command,
        ".github/workflows/ci.yml": f"{command} --wheel-only",
    }

    monkeypatch.setattr(hygiene, "read_text", lambda path: texts[path])

    errors: list[str] = []
    hygiene.check_wheel_smoke_release_mode(errors)

    assert any("release wheel smoke must include sdist" in error for error in errors)


def test_python_support_ci_coverage_rejects_missing_minimum(monkeypatch) -> None:
    pyproject = """
[project]
requires-python = ">=3.10"
classifiers = [
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.13",
]
"""
    workflow = 'python-version: ["3.13"]'

    monkeypatch.setattr(
        hygiene,
        "read_text",
        lambda path: pyproject if path == "pyproject.toml" else workflow,
    )

    errors: list[str] = []
    hygiene.check_python_support_ci_coverage(errors)

    assert "CI matrix must include minimum supported Python 3.10" in errors


def test_python_support_ci_coverage_rejects_missing_highest_classifier(monkeypatch) -> None:
    pyproject = """
[project]
requires-python = ">=3.10"
classifiers = [
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.13",
]
"""
    workflow = 'python-version: ["3.10"]'

    monkeypatch.setattr(
        hygiene,
        "read_text",
        lambda path: pyproject if path == "pyproject.toml" else workflow,
    )

    errors: list[str] = []
    hygiene.check_python_support_ci_coverage(errors)

    assert "CI matrix must include highest declared Python classifier 3.13" in errors


def test_ci_workflow_requires_diff_cleanliness(monkeypatch) -> None:
    monkeypatch.setattr(hygiene, "read_text", lambda path: "" if path == ".github/workflows/ci.yml" else "")

    errors: list[str] = []
    hygiene.check_ci_workflow(errors)

    assert "CI workflow missing release command: git diff --check" in errors
