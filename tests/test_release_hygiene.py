"""Tests for release hygiene guards."""
from __future__ import annotations

from pathlib import Path

from scripts import check_release_hygiene as hygiene


def test_wheel_smoke_release_mode_rejects_no_deps(monkeypatch) -> None:
    command = f"PYTHONDONTWRITEBYTECODE=1 python {hygiene.RELEASE_WHEEL_SMOKE_FRAGMENT}"
    texts = {
        "README.md": command,
        "README.en.md": f"{command} --no-deps",
        "CONTRIBUTING.md": command,
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
        "CONTRIBUTING.md": command,
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


def test_build_backend_floor_rejects_setuptools_before_pep639_support(monkeypatch) -> None:
    pyproject = """
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"
"""
    monkeypatch.setattr(hygiene, "read_text", lambda path: pyproject)

    errors: list[str] = []
    hygiene.check_build_backend_floor(errors)

    assert "setuptools build lower bound must be >= 77.0, found 69.0" in errors


def test_build_backend_floor_accepts_proven_minimum(monkeypatch) -> None:
    pyproject = """
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"
"""
    monkeypatch.setattr(hygiene, "read_text", lambda path: pyproject)

    errors: list[str] = []
    hygiene.check_build_backend_floor(errors)

    assert errors == []


def test_pi_sidecar_lock_rejects_dependency_drift(monkeypatch) -> None:
    texts = {
        "integrations/pi-native-sidecar/package.json": """
{"dependencies": {"@earendil-works/pi-coding-agent": "0.80.6"}}
""",
        "integrations/pi-native-sidecar/package-lock.json": """
{"lockfileVersion": 3, "packages": {
  "": {"dependencies": {"@earendil-works/pi-coding-agent": "0.80.5"}},
  "node_modules/@earendil-works/pi-coding-agent": {"version": "0.80.5", "integrity": "sha512-test"}
}}
""",
        "pyproject.toml": """
[tool.setuptools.data-files]
"share/shuheng/pi-native-sidecar" = ["integrations/pi-native-sidecar/package-lock.json"]
""",
    }
    monkeypatch.setattr(hygiene, "read_text", lambda path: texts[path])

    errors: list[str] = []
    hygiene.check_pi_sidecar_lock(errors)

    assert "Pi sidecar package-lock root dependency must match package.json" in errors
    assert "Pi sidecar package-lock must pin the SDK version and integrity" in errors


def test_runtime_version_must_match_package_metadata(monkeypatch) -> None:
    pyproject = """
[project]
name = "shuheng"
version = "0.2.0a1"
description = "test"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [{name = "test"}]
classifiers = ["Programming Language :: Python :: 3.10"]
urls = {Homepage = "https://example.invalid"}
[project.scripts]
shuheng = "shuheng.cli:main"
shuheng-agent-bridge = "shuheng.agent_bridge:main"
shuheng-agent-gateway = "shuheng.agent_bridge:gateway_main"
shuheng-check = "shuheng.integration:doctor_main"
shuheng-install-core-shim = "shuheng.integration:install_core_shim_main"
shuheng-integration = "shuheng.integration:main"
"""

    def fake_read(path: str) -> str:
        if path == "pyproject.toml":
            return pyproject
        if path == "src/shuheng/__init__.py":
            return '__version__ = "0.1.0"\n'
        raise AssertionError(path)

    monkeypatch.setattr(hygiene, "read_text", fake_read)

    errors: list[str] = []
    hygiene.check_pyproject_metadata(errors)

    assert any("package runtime __version__ must match" in error for error in errors)


def test_local_workflow_and_key_paths_must_be_ignored(monkeypatch) -> None:
    monkeypatch.setattr(hygiene, "git_path_is_ignored", lambda path: not path.startswith(".claude/"))

    errors: list[str] = []
    hygiene.check_local_paths_are_ignored(errors)

    assert errors == [".gitignore must ignore local release path: .claude/"]


def test_ci_workflow_requires_diff_cleanliness(monkeypatch) -> None:
    monkeypatch.setattr(hygiene, "read_text", lambda path: "" if path == ".github/workflows/ci.yml" else "")

    errors: list[str] = []
    hygiene.check_ci_workflow(errors)

    assert "CI workflow missing release command: git diff --check" in errors


def test_contributing_release_checks_reject_stale_command_list(monkeypatch) -> None:
    command_text = "\n".join(
        fragment
        for fragment in hygiene.PUBLIC_RELEASE_COMMAND_FRAGMENTS
        if "runtime_smoke.py" not in fragment
    )
    monkeypatch.setattr(hygiene, "read_text", lambda path: command_text if path == "CONTRIBUTING.md" else "")

    errors: list[str] = []
    hygiene.check_contributing_release_checks(errors)

    assert any("CONTRIBUTING.md missing contributor release command" in error and "runtime_smoke.py" in error for error in errors)


def test_private_runtime_paths_are_release_blockers(monkeypatch) -> None:
    def fake_git_lines(*args: str) -> list[str]:
        if args == ("ls-files",):
            return [
                "memory/secret_vault/session.secret",
                "temp/model_responses/model_responses_1.txt",
                "goal-6/tasks.md",
                ".trellis/spec/backend/index.md",
                ".agents/skills/local/SKILL.md",
                "mykey.py.bak-20260710",
            ]
        if args == ("ls-files", "-o", "--exclude-standard"):
            return ["tmp/local-smoke/output.json"]
        raise AssertionError(args)

    monkeypatch.setattr(hygiene, "git_lines", fake_git_lines)

    errors: list[str] = []
    hygiene.check_private_files_are_not_tracked(errors)

    assert "private/local path is tracked: memory/secret_vault/session.secret" in errors
    assert "private/local path is tracked: temp/model_responses/model_responses_1.txt" in errors
    assert "private/local path is tracked: goal-6/tasks.md" in errors
    assert "private/local path is tracked: .trellis/spec/backend/index.md" in errors
    assert "private/local path is tracked: .agents/skills/local/SKILL.md" in errors
    assert "private/local path is tracked: mykey.py.bak-20260710" in errors
    assert "private/local path is unignored and could be committed: tmp/local-smoke/output.json" in errors


def test_public_secret_scan_covers_packaged_tests(monkeypatch, tmp_path: Path) -> None:
    test_path = tmp_path / "tests" / "test_leaky_fixture.py"
    test_path.parent.mkdir(parents=True)
    secret_like = "sk-" + "testfixture12345678901234567890"
    test_path.write_text(f'TOKEN = "{secret_like}"\n', encoding="utf-8")

    monkeypatch.setattr(hygiene, "ROOT", tmp_path)
    monkeypatch.setattr(hygiene, "git_lines", lambda *args: ["tests/test_leaky_fixture.py"] if args == ("ls-files",) else [])

    errors: list[str] = []
    hygiene.check_secret_and_local_literals(errors)

    assert "secret-like literal found in public file: tests/test_leaky_fixture.py" in errors
