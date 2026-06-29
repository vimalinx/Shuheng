#!/usr/bin/env python3
"""Repository-level hygiene checks for public Shuheng alpha releases."""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    "README.md",
    "README.en.md",
    "MANIFEST.in",
    ".github/workflows/ci.yml",
)

PRIVATE_PATH_PREFIXES = (
    "config/",
    "references/",
)

PRIVATE_PATHS = {
    "docs/foreign-student-acquisition-research.md",
    "docs/homework-pricing-research.md",
}

PUBLIC_SCAN_PREFIXES = (
    ".github/",
    "docs/",
    "integrations/",
    "scripts/",
    "src/",
)

PUBLIC_SCAN_FILES = {
    ".gitignore",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "MANIFEST.in",
    "README.en.md",
    "README.md",
    "SECURITY.md",
    "pyproject.toml",
}

SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)

LOCAL_PATH_PATTERNS = (
    re.compile(r"/home/[A-Za-z0-9._-]+/"),
    re.compile(r"/Users/[A-Za-z0-9._-]+/"),
)


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def is_public_scan_path(path: str) -> bool:
    return path in PUBLIC_SCAN_FILES or path.startswith(PUBLIC_SCAN_PREFIXES)


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def check_required_files(errors: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not (ROOT / path).is_file():
            errors.append(f"missing required release file: {path}")


def check_private_files_are_not_tracked(errors: list[str]) -> None:
    tracked = set(git_lines("ls-files"))
    for path in sorted(tracked):
        if path in PRIVATE_PATHS or path.startswith(PRIVATE_PATH_PREFIXES):
            errors.append(f"private/local path is tracked: {path}")

    untracked = set(git_lines("ls-files", "-o", "--exclude-standard"))
    for path in sorted(untracked):
        if path in PRIVATE_PATHS or path.startswith(PRIVATE_PATH_PREFIXES):
            errors.append(f"private/local path is unignored and could be committed: {path}")


def check_secret_and_local_literals(errors: list[str]) -> None:
    tracked = [path for path in git_lines("ls-files") if is_public_scan_path(path)]
    for path in tracked:
        full_path = ROOT / path
        if not full_path.is_file() or full_path.suffix in {".pyc", ".pyo"}:
            continue
        text = read_text(path)
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"secret-like literal found in public file: {path}")
                break
        for pattern in LOCAL_PATH_PATTERNS:
            if pattern.search(text):
                errors.append(f"local absolute path found in public file: {path}")
                break


def check_pyproject_metadata(errors: list[str]) -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project") or {}
    for key in ("name", "version", "description", "readme", "requires-python", "license", "authors", "classifiers", "urls"):
        if not project.get(key):
            errors.append(f"pyproject missing project.{key}")
    if project.get("name") != "shuheng":
        errors.append("pyproject project.name must be shuheng")
    scripts = (project.get("scripts") or {}).keys()
    required_scripts = {
        "shuheng",
        "shuheng-agent-bridge",
        "shuheng-check",
        "shuheng-install-core-shim",
        "shuheng-integration",
    }
    missing = sorted(required_scripts - set(scripts))
    if missing:
        errors.append(f"pyproject missing console scripts: {', '.join(missing)}")
    public_legacy = sorted(script for script in scripts if script.startswith("ga-tui"))
    if public_legacy:
        errors.append(f"legacy ga-tui console scripts are public: {', '.join(public_legacy)}")


def check_public_positioning(errors: list[str]) -> None:
    readme = read_text("README.md")
    readme_en = read_text("README.en.md")
    for path, text in (("README.md", readme), ("README.en.md", readme_en)):
        if "experimental local alpha" not in text:
            errors.append(f"{path} must state experimental local alpha")
        if "A2A/MCP" not in text:
            errors.append(f"{path} must mention A2A/MCP compatibility boundaries")
        if "Secret Vault" not in text:
            errors.append(f"{path} must mention Secret Vault release boundary")
        if "scripts/runtime_smoke.py" not in text:
            errors.append(f"{path} must list runtime smoke in release checks")
        if "runtime smoke" not in text.lower():
            errors.append(f"{path} CI summary must mention runtime smoke")
        if "scripts/wheel_smoke.py" not in text:
            errors.append(f"{path} must list wheel smoke in release checks")
        if "wheel smoke" not in text.lower():
            errors.append(f"{path} CI summary must mention wheel smoke")

    package_json = read_text("integrations/omp-ga-tui-plugin/package.json")
    if '"name": "@shuheng/omp-bridge"' not in package_json:
        errors.append("OMP plugin package name should use Shuheng public branding")


def check_ci_workflow(errors: list[str]) -> None:
    workflow = read_text(".github/workflows/ci.yml")
    required_fragments = (
        "python -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/runtime_smoke.py scripts/wheel_smoke.py",
        "python scripts/check_release_hygiene.py",
        "python scripts/check_policy_gates.py",
        "python scripts/runtime_smoke.py",
        "python -m pytest -q -p no:cacheprovider",
        "python -m compileall -q src scripts",
        "python -m build --sdist --wheel --outdir /tmp/shuheng-dist",
        "python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist",
    )
    for fragment in required_fragments:
        if fragment not in workflow:
            errors.append(f"CI workflow missing release command: {fragment}")


def main() -> int:
    errors: list[str] = []
    check_required_files(errors)
    check_private_files_are_not_tracked(errors)
    check_secret_and_local_literals(errors)
    check_pyproject_metadata(errors)
    check_public_positioning(errors)
    check_ci_workflow(errors)

    if errors:
        print("release hygiene checks failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("release hygiene checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
