#!/usr/bin/env python3
"""Repository-level hygiene checks for public Shuheng alpha releases."""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

try:
    from .release_scan_rules import text_release_leak_errors
except ImportError:
    from release_scan_rules import text_release_leak_errors


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    "README.md",
    "README.en.md",
    "docs/install.md",
    "docs/public-alpha-readiness.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    "MANIFEST.in",
    ".github/workflows/ci.yml",
    "scripts/check_policy_gates.py",
    "scripts/check_release_hygiene.py",
    "scripts/dogfood_stdio_gateway.py",
    "scripts/release_scan_rules.py",
    "scripts/runtime_smoke.py",
    "scripts/wheel_smoke.py",
)

PRIVATE_PATH_PREFIXES = (
    ".codex/",
    ".trellis/.backup-",
    ".trellis/.cache/",
    ".trellis/.runtime/",
    ".trellis/worktrees/",
    "_knowledge_base/",
    "config/",
    "goal-",
    "memory/",
    "references/",
    "temp/",
    "tmp/",
)

PRIVATE_PATHS = {
    ".trellis/.current-task",
    ".trellis/.developer",
    ".trellis/.template-hashes.json",
    "docs/foreign-student-acquisition-research.md",
    "docs/homework-pricing-research.md",
}

PUBLIC_SCAN_PREFIXES = (
    ".github/",
    "docs/",
    "integrations/",
    "scripts/",
    "src/",
    "tests/",
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

PUBLIC_WORDING_FILES = (
    ".github/ISSUE_TEMPLATE/bug_report.md",
    "CONTRIBUTING.md",
    "README.en.md",
    "README.md",
    "docs/app-py-decomposition-plan.md",
    "docs/install.md",
    "docs/public-alpha-readiness.md",
    "docs/runtime-provider-control-plane.md",
)

REQUIRED_MANIFEST_LINES = (
    "include README.md",
    "include README.en.md",
    "include LICENSE",
    "include SECURITY.md",
    "include CONTRIBUTING.md",
    "include CODE_OF_CONDUCT.md",
    "include CHANGELOG.md",
    "recursive-include docs *.md",
    "recursive-include integrations/omp-shuheng-plugin *.md *.json *.ts",
    "recursive-include src/shuheng/builtin_plugins *.json",
    "recursive-include src/shuheng/builtin_skills *.md *.yaml",
    "recursive-include tests *.py",
    "include scripts/check_policy_gates.py",
    "include scripts/check_release_hygiene.py",
    "include scripts/dogfood_stdio_gateway.py",
    "include scripts/release_scan_rules.py",
    "include scripts/runtime_smoke.py",
    "include scripts/wheel_smoke.py",
)

REQUIRED_MANIFEST_EXCLUSIONS = (
    "exclude docs/foreign-student-acquisition-research.md",
    "exclude docs/homework-pricing-research.md",
    "prune .codex",
    "prune .trellis",
    "prune _knowledge_base",
    "prune config",
    "prune memory",
    "prune references",
    "prune temp",
    "prune tmp",
    "prune goal-*",
)

RELEASE_WHEEL_SMOKE_FRAGMENT = "scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist"
PYTHON_VERSION_PATTERN = re.compile(r"(?<!\d)(\d+\.\d+)(?!\d)")
PUBLIC_RELEASE_COMMAND_FRAGMENTS = (
    "python -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/dogfood_stdio_gateway.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py",
    "python scripts/check_release_hygiene.py",
    "python scripts/check_policy_gates.py",
    "python scripts/dogfood_stdio_gateway.py",
    "python scripts/runtime_smoke.py",
    "python -m pytest -q -p no:cacheprovider",
    "python -m compileall -q src scripts",
    "python -m build --sdist --wheel --outdir /tmp/shuheng-dist",
    "python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist",
    "git diff --check",
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
        errors.extend(text_release_leak_errors(text, path, location="public file"))


def check_public_wording(errors: list[str]) -> None:
    retired_runtime = "Generic" + "Agent"
    for path in PUBLIC_WORDING_FILES:
        text = read_text(path)
        if retired_runtime in text or retired_runtime.lower() in text.lower():
            errors.append(f"{path} must not mention retired runtime branding in public release wording")


def check_pyproject_metadata(errors: list[str]) -> None:
    data = tomllib.loads(read_text("pyproject.toml"))
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
        "shuheng-agent-gateway",
        "shuheng-check",
        "shuheng-install-core-shim",
        "shuheng-integration",
    }
    missing = sorted(required_scripts - set(scripts))
    if missing:
        errors.append(f"pyproject missing console scripts: {', '.join(missing)}")
    retired_script_prefix = "ga" + "-tui"
    public_legacy = sorted(script for script in scripts if script.startswith(retired_script_prefix))
    if public_legacy:
        errors.append(f"retired pre-Shuheng console scripts are public: {', '.join(public_legacy)}")


def python_version_key(version: str) -> tuple[int, int]:
    major, minor = version.split(".", 1)
    return (int(major), int(minor))


def minimum_requires_python_version(requires_python: str) -> str:
    match = re.search(r">=\s*(\d+\.\d+)", str(requires_python or ""))
    return match.group(1) if match else ""


def classifier_python_versions(classifiers: list[str]) -> list[str]:
    versions: set[str] = set()
    for classifier in classifiers:
        tail = str(classifier).rsplit("::", 1)[-1].strip()
        if PYTHON_VERSION_PATTERN.fullmatch(tail):
            versions.add(tail)
    return sorted(versions, key=python_version_key)


def ci_python_versions(workflow_text: str) -> list[str]:
    return sorted(set(PYTHON_VERSION_PATTERN.findall(workflow_text)), key=python_version_key)


def check_python_support_ci_coverage(errors: list[str]) -> None:
    project = (tomllib.loads(read_text("pyproject.toml")).get("project") or {})
    ci_versions = set(ci_python_versions(read_text(".github/workflows/ci.yml")))
    min_version = minimum_requires_python_version(str(project.get("requires-python") or ""))
    if min_version and min_version not in ci_versions:
        errors.append(f"CI matrix must include minimum supported Python {min_version}")
    declared_versions = classifier_python_versions(list(project.get("classifiers") or []))
    if declared_versions:
        highest = declared_versions[-1]
        if highest not in ci_versions:
            errors.append(f"CI matrix must include highest declared Python classifier {highest}")


def check_manifest_contract(errors: list[str]) -> None:
    manifest = read_text("MANIFEST.in")
    for line in REQUIRED_MANIFEST_LINES:
        if line not in manifest:
            errors.append(f"MANIFEST.in missing public release inclusion: {line}")
    for line in REQUIRED_MANIFEST_EXCLUSIONS:
        if line not in manifest:
            errors.append(f"MANIFEST.in missing private/local exclusion: {line}")


def check_public_positioning(errors: list[str]) -> None:
    readme = read_text("README.md")
    readme_en = read_text("README.en.md")
    for path, text in (("README.md", readme), ("README.en.md", readme_en)):
        if "experimental local alpha" not in text:
            errors.append(f"{path} must state experimental local alpha")
        if (
            "no built-in Web/HTTP" not in text
            and "no longer ships a built-in Web Console" not in text
            and "不再内置 Web Console" not in text
        ):
            errors.append(f"{path} must state no built-in Web/HTTP surface")
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

    install_doc = read_text("docs/install.md")
    install_required = (
        "Linux",
        "Windows via WSL2",
        "macOS",
        "Windows native",
        "shuheng install-agent-gateway-skill",
        "shuheng-check",
        "~/.shuheng/",
        "~/.agents/skills/",
    )
    for fragment in install_required:
        if fragment not in install_doc:
            errors.append(f"docs/install.md missing install/platform fragment: {fragment}")

    package_json = read_text("integrations/omp-shuheng-plugin/package.json")
    if '"name": "@shuheng/omp-bridge"' not in package_json:
        errors.append("OMP plugin package name should use Shuheng public branding")


def wheel_smoke_release_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if RELEASE_WHEEL_SMOKE_FRAGMENT in line
    ]


def check_wheel_smoke_release_mode(errors: list[str]) -> None:
    surfaces = {
        "README.md": read_text("README.md"),
        "README.en.md": read_text("README.en.md"),
        "CONTRIBUTING.md": read_text("CONTRIBUTING.md"),
        ".github/workflows/ci.yml": read_text(".github/workflows/ci.yml"),
    }
    for path, text in surfaces.items():
        lines = wheel_smoke_release_lines(text)
        if not lines:
            errors.append(f"{path} must run dependency-resolving wheel smoke: {RELEASE_WHEEL_SMOKE_FRAGMENT}")
            continue
        for line in lines:
            if "--no-deps" in line:
                errors.append(f"{path} release wheel smoke must not use --no-deps: {line}")
            if "--wheel-only" in line:
                errors.append(f"{path} release wheel smoke must include sdist, not --wheel-only: {line}")


def check_ci_workflow(errors: list[str]) -> None:
    workflow = read_text(".github/workflows/ci.yml")
    for fragment in PUBLIC_RELEASE_COMMAND_FRAGMENTS:
        if fragment not in workflow:
            errors.append(f"CI workflow missing release command: {fragment}")


def check_contributing_release_checks(errors: list[str]) -> None:
    contributing = read_text("CONTRIBUTING.md")
    for fragment in PUBLIC_RELEASE_COMMAND_FRAGMENTS:
        if fragment not in contributing:
            errors.append(f"CONTRIBUTING.md missing contributor release command: {fragment}")


def main() -> int:
    errors: list[str] = []
    check_required_files(errors)
    check_private_files_are_not_tracked(errors)
    check_secret_and_local_literals(errors)
    check_public_wording(errors)
    check_pyproject_metadata(errors)
    check_python_support_ci_coverage(errors)
    check_manifest_contract(errors)
    check_public_positioning(errors)
    check_wheel_smoke_release_mode(errors)
    check_ci_workflow(errors)
    check_contributing_release_checks(errors)

    if errors:
        print("release hygiene checks failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("release hygiene checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
