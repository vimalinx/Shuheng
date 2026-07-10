#!/usr/bin/env python3
"""Repository-level hygiene checks for public Shuheng alpha releases."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by the Python 3.10 CI job
    import tomli as tomllib

try:
    from .release_scan_rules import text_release_leak_errors
except ImportError:
    from release_scan_rules import text_release_leak_errors


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "0.2.0a1"
MINIMUM_SETUPTOOLS_VERSION = (77, 0)
MINIMUM_SETUPTOOLS_CI_VERSION = "77.0.3"
PI_SIDECAR_SDK_PACKAGE = "@earendil-works/pi-coding-agent"

REQUIRED_FILES = (
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    "THIRD_PARTY_NOTICES.md",
    "README.md",
    "README.en.md",
    "docs/install.md",
    "docs/development/index.md",
    "docs/public-alpha-readiness.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    "MANIFEST.in",
    ".github/workflows/ci.yml",
    ".github/dependabot.yml",
    "scripts/check_policy_gates.py",
    "scripts/check_release_hygiene.py",
    "scripts/dogfood_stdio_gateway.py",
    "scripts/install.sh",
    "scripts/release_scan_rules.py",
    "scripts/runtime_smoke.py",
    "scripts/wheel_smoke.py",
    "integrations/pi-native-sidecar/package-lock.json",
)

PRIVATE_PATH_PREFIXES = (
    ".agents/",
    ".claude/",
    ".codex/",
    ".trellis/",
    "_knowledge_base/",
    "config/",
    "goal-",
    "memory/",
    "references/",
    "temp/",
    "tmp/",
)

PRIVATE_PATHS = {
    "docs/foreign-student-acquisition-research.md",
    "docs/homework-pricing-research.md",
    "mykey.py",
}

PRIVATE_ROOT_FILE_PREFIXES = (
    "mykey.py.bak-",
    "mykey.py.tmp-",
)

REQUIRED_IGNORED_LOCAL_PATHS = {
    ".agents/release-hygiene-probe": ".agents/",
    ".claude/release-hygiene-probe": ".claude/",
    ".trellis/release-hygiene-probe": ".trellis/",
    "mykey.py": "mykey.py",
    "mykey.py.bak-release-hygiene-probe": "mykey.py.bak-*",
    "mykey.py.tmp-release-hygiene-probe": "mykey.py.tmp-*",
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
    "include THIRD_PARTY_NOTICES.md",
    "recursive-include docs *.md",
    "recursive-include integrations/omp-shuheng-plugin *.md *.json *.ts",
    "recursive-include integrations/pi-native-sidecar *.md *.json *.mjs",
    "recursive-include src/shuheng/builtin_plugins *.json",
    "recursive-include src/shuheng/builtin_skills *.md *.yaml",
    "recursive-include tests *.py",
    "include scripts/check_policy_gates.py",
    "include scripts/check_release_hygiene.py",
    "include scripts/install.sh",
    "include scripts/dogfood_stdio_gateway.py",
    "include scripts/release_scan_rules.py",
    "include scripts/runtime_smoke.py",
    "include scripts/wheel_smoke.py",
)

REQUIRED_MANIFEST_EXCLUSIONS = (
    "exclude mykey.py",
    "exclude mykey.py.bak-*",
    "exclude mykey.py.tmp-*",
    "prune .agents",
    "prune .claude",
    "prune integrations/pi-native-sidecar/node_modules",
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

CI_ONLY_RELEASE_COMMAND_FRAGMENTS = (
    f'python -m pip install "setuptools=={MINIMUM_SETUPTOOLS_CI_VERSION}" wheel',
    "python -m shuheng runtime setup-omp --json",
    "python -m build --no-isolation --sdist --wheel --outdir /tmp/shuheng-min-backend-dist",
    "npm ci --ignore-scripts --prefix integrations/pi-native-sidecar",
    "node --check integrations/pi-native-sidecar/sidecar.mjs",
)

REQUIRED_ACTION_PINS = (
    "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10",  # v6
    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",  # v6
    "actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e",  # v6
    "oven-sh/setup-bun@0c5077e51419868618aeaa5fe8019c62421857d6",  # v2
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


def is_private_path(path: str) -> bool:
    return (
        path in PRIVATE_PATHS
        or path.startswith(PRIVATE_PATH_PREFIXES)
        or any(path.startswith(prefix) for prefix in PRIVATE_ROOT_FILE_PREFIXES)
    )


def is_public_scan_path(path: str) -> bool:
    """Treat every tracked, non-local path as part of the public source release."""
    return not is_private_path(path)


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def git_path_is_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", path],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode == 0


def check_required_files(errors: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not (ROOT / path).is_file():
            errors.append(f"missing required release file: {path}")


def check_private_files_are_not_tracked(errors: list[str]) -> None:
    tracked = set(git_lines("ls-files"))
    for path in sorted(tracked):
        if is_private_path(path):
            errors.append(f"private/local path is tracked: {path}")

    untracked = set(git_lines("ls-files", "-o", "--exclude-standard"))
    for path in sorted(untracked):
        if is_private_path(path):
            errors.append(f"private/local path is unignored and could be committed: {path}")


def check_local_paths_are_ignored(errors: list[str]) -> None:
    for path, required_pattern in REQUIRED_IGNORED_LOCAL_PATHS.items():
        if not git_path_is_ignored(path):
            errors.append(f".gitignore must ignore local release path: {required_pattern}")


def check_secret_and_local_literals(errors: list[str]) -> None:
    tracked = [path for path in git_lines("ls-files") if is_public_scan_path(path)]
    for path in tracked:
        full_path = ROOT / path
        if not full_path.is_file() or full_path.suffix in {".pyc", ".pyo"}:
            continue
        raw = full_path.read_bytes()
        if b"\0" in raw:
            continue
        text = raw.decode("utf-8", errors="replace")
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
    project_version = str(project.get("version") or "")
    if project_version != RELEASE_VERSION:
        errors.append(f"pyproject project.version must be {RELEASE_VERSION}")
    runtime_version = package_runtime_version()
    if runtime_version != project_version:
        errors.append(
            "package runtime __version__ must match pyproject project.version "
            f"({runtime_version or 'missing'} != {project_version or 'missing'})"
        )
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


def package_runtime_version() -> str:
    tree = ast.parse(read_text("src/shuheng/__init__.py"), filename="src/shuheng/__init__.py")
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value
    return ""


def setuptools_requirement_floor(requirements: list[str]) -> tuple[int, int] | None:
    for requirement in requirements:
        match = re.fullmatch(r"\s*setuptools\s*>=\s*(\d+)(?:\.(\d+))?\s*", str(requirement))
        if match:
            return (int(match.group(1)), int(match.group(2) or 0))
    return None


def check_build_backend_floor(errors: list[str]) -> None:
    data = tomllib.loads(read_text("pyproject.toml"))
    build_system = data.get("build-system") or {}
    if build_system.get("build-backend") != "setuptools.build_meta":
        errors.append("pyproject build-system.build-backend must be setuptools.build_meta")
    floor = setuptools_requirement_floor(list(build_system.get("requires") or []))
    if floor is None:
        errors.append("pyproject build-system.requires must declare a setuptools lower bound")
    elif floor < MINIMUM_SETUPTOOLS_VERSION:
        required = ".".join(str(part) for part in MINIMUM_SETUPTOOLS_VERSION)
        actual = ".".join(str(part) for part in floor)
        errors.append(f"setuptools build lower bound must be >= {required}, found {actual}")


def check_pi_sidecar_lock(errors: list[str]) -> None:
    package = json.loads(read_text("integrations/pi-native-sidecar/package.json"))
    lock = json.loads(read_text("integrations/pi-native-sidecar/package-lock.json"))
    expected_sdk_version = str((package.get("dependencies") or {}).get(PI_SIDECAR_SDK_PACKAGE) or "")
    if not re.fullmatch(r"\d+\.\d+\.\d+", expected_sdk_version):
        errors.append(f"Pi sidecar SDK dependency must use an exact version: {expected_sdk_version or 'missing'}")
        return
    if lock.get("lockfileVersion") != 3:
        errors.append("Pi sidecar package-lock.json must use lockfileVersion 3")
    lock_packages = lock.get("packages") or {}
    root_dependencies = (lock_packages.get("") or {}).get("dependencies") or {}
    if root_dependencies.get(PI_SIDECAR_SDK_PACKAGE) != expected_sdk_version:
        errors.append("Pi sidecar package-lock root dependency must match package.json")
    sdk_record = lock_packages.get(f"node_modules/{PI_SIDECAR_SDK_PACKAGE}") or {}
    if sdk_record.get("version") != expected_sdk_version or not sdk_record.get("integrity"):
        errors.append("Pi sidecar package-lock must pin the SDK version and integrity")
    pyproject = tomllib.loads(read_text("pyproject.toml"))
    data_files = (((pyproject.get("tool") or {}).get("setuptools") or {}).get("data-files") or {})
    sidecar_data = data_files.get("share/shuheng/pi-native-sidecar") or []
    if "integrations/pi-native-sidecar/package-lock.json" not in sidecar_data:
        errors.append("pyproject must install the Pi sidecar package-lock.json")


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
        if "local JSONL stdio" not in text and "本地 JSONL stdio" not in text:
            errors.append(f"{path} must identify the supported local JSONL stdio integration")
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
        "scripts/install.sh",
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
    for fragment in (*PUBLIC_RELEASE_COMMAND_FRAGMENTS, *CI_ONLY_RELEASE_COMMAND_FRAGMENTS):
        if fragment not in workflow:
            errors.append(f"CI workflow missing release command: {fragment}")
    for action in REQUIRED_ACTION_PINS:
        if action not in workflow:
            errors.append(f"CI workflow must pin official action to reviewed commit: {action}")


def check_contributing_release_checks(errors: list[str]) -> None:
    contributing = read_text("CONTRIBUTING.md")
    for fragment in PUBLIC_RELEASE_COMMAND_FRAGMENTS:
        if fragment not in contributing:
            errors.append(f"CONTRIBUTING.md missing contributor release command: {fragment}")


def main() -> int:
    errors: list[str] = []
    check_required_files(errors)
    check_private_files_are_not_tracked(errors)
    check_local_paths_are_ignored(errors)
    check_secret_and_local_literals(errors)
    check_public_wording(errors)
    check_pyproject_metadata(errors)
    check_build_backend_floor(errors)
    check_pi_sidecar_lock(errors)
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
