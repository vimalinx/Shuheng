#!/usr/bin/env python3
"""Install built Shuheng distribution artifacts in clean venvs and run public entrypoints."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile


REQUIRED_CONTINUE_FUNCS = (
    "_format_response_segment",
    "_pairs",
    "_parse_native_history",
    "_preview_text",
    "_tool_results_from_prompt",
    "_user_text",
    "reset_conversation",
    "restore",
)

PUBLIC_CONSOLE_SCRIPTS = (
    "shuheng",
    "shuheng-agent-bridge",
    "shuheng-check",
    "shuheng-install-core-shim",
    "shuheng-integration",
)

HELP_SAFE_CONSOLE_SCRIPTS = (
    "shuheng-agent-bridge",
    "shuheng-install-core-shim",
    "shuheng-integration",
)

SDIST_REQUIRED_MEMBERS = (
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "MANIFEST.in",
    "README.en.md",
    "README.md",
    "SECURITY.md",
    "docs/agent-harness-architecture.md",
    "docs/runtime-provider-control-plane.md",
    "integrations/omp-ga-tui-plugin/README.md",
    "integrations/omp-ga-tui-plugin/package.json",
    "integrations/omp-ga-tui-plugin/tools/index.ts",
    "pyproject.toml",
    "scripts/check_policy_gates.py",
    "scripts/check_release_hygiene.py",
    "scripts/runtime_smoke.py",
    "scripts/wheel_smoke.py",
    "src/ga_tui/app.py",
    "tests/test_release_hygiene.py",
    "tests/test_wheel_smoke.py",
)

SDIST_FORBIDDEN_MEMBERS = (
    "docs/foreign-student-acquisition-research.md",
    "docs/homework-pricing-research.md",
)

SDIST_FORBIDDEN_PREFIXES = (
    ".codex/",
    ".trellis/",
    "config/",
    "goal-",
    "memory/",
    "references/",
    "temp/",
    "tmp/",
)

WHEEL_REQUIRED_PACKAGE_MEMBERS = (
    "ga_tui/__init__.py",
    "ga_tui/__main__.py",
    "ga_tui/app.py",
    "ga_tui/integration.py",
    "ga_tui/release_readiness.py",
)

WHEEL_REQUIRED_DIST_INFO_MEMBERS = (
    "METADATA",
    "WHEEL",
    "entry_points.txt",
    "top_level.txt",
    "RECORD",
    "licenses/LICENSE",
)

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


def latest_artifact(dist_dir: Path, pattern: str, label: str) -> Path:
    artifacts = sorted(dist_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not artifacts:
        raise FileNotFoundError(f"no Shuheng {label} found in {dist_dir}; run python -m build first")
    return artifacts[0]


def latest_wheel(dist_dir: Path) -> Path:
    return latest_artifact(dist_dir, "shuheng-*.whl", "wheel")


def latest_sdist(dist_dir: Path) -> Path:
    return latest_artifact(dist_dir, "shuheng-*.tar.gz", "sdist")


def venv_python(venv_dir: Path) -> Path:
    candidate = venv_dir / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if not candidate.is_file():
        raise FileNotFoundError(f"venv python not found: {candidate}")
    return candidate


def venv_script(venv_dir: Path, name: str) -> Path:
    bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    candidates = [bin_dir / name, bin_dir / f"{name}.exe"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"venv script not found: {name}")


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=cwd, env=env, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def write_fake_genericagent_root(root: Path) -> Path:
    ga_root = root / "GenericAgent"
    frontends = ga_root / "frontends"
    frontends.mkdir(parents=True, exist_ok=True)
    (ga_root / "agentmain.py").write_text("# wheel smoke stub\n", encoding="utf-8")
    (ga_root / "ga.py").write_text("# wheel smoke stub\n", encoding="utf-8")
    continue_cmd = "\n".join(
        ["# wheel smoke stub", *[f"def {name}(*args, **kwargs):\n    return None\n" for name in REQUIRED_CONTINUE_FUNCS]]
    )
    (frontends / "continue_cmd.py").write_text(continue_cmd, encoding="utf-8")
    return ga_root


def normalized_archive_parts(raw_name: str) -> tuple[str, ...]:
    posix = PurePosixPath(raw_name)
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError(f"unsafe archive member path: {raw_name}")
    return tuple(part for part in posix.parts if part not in {"", "."})


def text_release_leak_errors(text: str, path: str) -> list[str]:
    errors: list[str] = []
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        errors.append(f"secret-like literal found in artifact member: {path}")
    if any(pattern.search(text) for pattern in LOCAL_PATH_PATTERNS):
        errors.append(f"local absolute path found in artifact member: {path}")
    return errors


def check_archive_text_has_no_release_leaks(rows: list[tuple[str, bytes]], *, artifact_kind: str) -> dict[str, object]:
    errors: list[str] = []
    for path, data in rows:
        text = data.decode("utf-8", errors="replace")
        errors.extend(text_release_leak_errors(text, path))
    if errors:
        raise ValueError(f"{artifact_kind} artifact content leak scan failed: " + "; ".join(errors))
    return {
        "command": f"{artifact_kind} artifact content leak scan",
        "returncode": 0,
        "scanned_members": len(rows),
    }


def sdist_text_rows(sdist: Path) -> list[tuple[str, bytes]]:
    rows: list[tuple[str, bytes]] = []
    with tarfile.open(sdist, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            parts = normalized_archive_parts(member.name)
            if len(parts) < 2:
                continue
            display_path = "/".join(parts[1:])
            file_obj = archive.extractfile(member)
            if file_obj is not None:
                rows.append((display_path, file_obj.read()))
    return rows


def wheel_text_rows(wheel: Path) -> list[tuple[str, bytes]]:
    rows: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(wheel) as archive:
        for raw_name in archive.namelist():
            parts = normalized_archive_parts(raw_name)
            if not parts or raw_name.endswith("/"):
                continue
            rows.append(("/".join(parts), archive.read(raw_name)))
    return rows


def normalized_sdist_members(sdist: Path) -> set[str]:
    with tarfile.open(sdist, "r:gz") as archive:
        names = [member.name for member in archive.getmembers()]

    top_levels: set[str] = set()
    normalized: set[str] = set()
    for raw_name in names:
        parts = normalized_archive_parts(raw_name)
        if not parts:
            continue
        top_levels.add(parts[0])
        if len(parts) > 1:
            normalized.add("/".join(parts[1:]))

    if len(top_levels) != 1:
        raise ValueError(f"sdist archive must have one top-level directory, found: {sorted(top_levels)}")
    return normalized


def sdist_archive_contract_check(sdist: Path) -> dict[str, object]:
    members = normalized_sdist_members(sdist)
    missing = sorted(member for member in SDIST_REQUIRED_MEMBERS if member not in members)
    forbidden = sorted(
        member
        for member in members
        if member in SDIST_FORBIDDEN_MEMBERS or member.startswith(SDIST_FORBIDDEN_PREFIXES)
    )
    if missing or forbidden:
        details = []
        if missing:
            details.append("missing required members: " + ", ".join(missing))
        if forbidden:
            details.append("forbidden members present: " + ", ".join(forbidden))
        raise ValueError("sdist archive contract failed: " + "; ".join(details))
    return {
        "command": "sdist archive public/private member contract",
        "returncode": 0,
        "required_members": len(SDIST_REQUIRED_MEMBERS),
        "forbidden_members": 0,
    }


def normalized_wheel_members(wheel: Path) -> set[str]:
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()

    normalized: set[str] = set()
    for raw_name in names:
        parts = normalized_archive_parts(raw_name)
        if parts:
            normalized.add("/".join(parts))
    return normalized


def wheel_dist_info_dir(members: set[str]) -> str:
    dist_info_dirs = sorted({member.split("/", 1)[0] for member in members if member.split("/", 1)[0].endswith(".dist-info")})
    if len(dist_info_dirs) != 1:
        raise ValueError(f"wheel archive must have one dist-info directory, found: {dist_info_dirs}")
    return dist_info_dirs[0]


def wheel_archive_contract_check(wheel: Path) -> dict[str, object]:
    members = normalized_wheel_members(wheel)
    dist_info_dir = wheel_dist_info_dir(members)
    required_members = (
        *WHEEL_REQUIRED_PACKAGE_MEMBERS,
        *[f"{dist_info_dir}/{member}" for member in WHEEL_REQUIRED_DIST_INFO_MEMBERS],
    )
    missing = sorted(member for member in required_members if member not in members)
    forbidden = sorted(
        member
        for member in members
        if member in SDIST_FORBIDDEN_MEMBERS or member.startswith(SDIST_FORBIDDEN_PREFIXES)
    )
    with zipfile.ZipFile(wheel) as archive:
        metadata_text = archive.read(f"{dist_info_dir}/METADATA").decode("utf-8", errors="replace") if f"{dist_info_dir}/METADATA" in members else ""
        entry_points_text = (
            archive.read(f"{dist_info_dir}/entry_points.txt").decode("utf-8", errors="replace")
            if f"{dist_info_dir}/entry_points.txt" in members
            else ""
        )
    metadata_errors = []
    if "Name: shuheng" not in metadata_text:
        metadata_errors.append("METADATA missing Name: shuheng")
    if "Version:" not in metadata_text:
        metadata_errors.append("METADATA missing Version")
    missing_console_scripts = sorted(script for script in PUBLIC_CONSOLE_SCRIPTS if f"{script} =" not in entry_points_text)
    if missing_console_scripts:
        metadata_errors.append("entry_points.txt missing console scripts: " + ", ".join(missing_console_scripts))
    if missing or forbidden or metadata_errors:
        details = []
        if missing:
            details.append("missing required members: " + ", ".join(missing))
        if forbidden:
            details.append("forbidden members present: " + ", ".join(forbidden))
        details.extend(metadata_errors)
        raise ValueError("wheel archive contract failed: " + "; ".join(details))
    return {
        "command": "wheel archive metadata/private member contract",
        "returncode": 0,
        "required_members": len(required_members),
        "forbidden_members": 0,
        "console_scripts": len(PUBLIC_CONSOLE_SCRIPTS),
    }


def run_artifact_smoke(artifact: Path, *, artifact_kind: str, no_deps: bool = False) -> dict[str, object]:
    artifact = artifact.resolve()
    if not artifact.is_file():
        raise FileNotFoundError(f"{artifact_kind} not found: {artifact}")
    with tempfile.TemporaryDirectory(prefix=f"shuheng_{artifact_kind}_smoke_") as tmp_s:
        tmp = Path(tmp_s)
        venv_dir = tmp / "venv"
        fake_root = write_fake_genericagent_root(tmp)
        venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
        py = venv_python(venv_dir)
        env = clean_env()
        install_cmd = [str(py), "-m", "pip", "install"]
        if no_deps:
            install_cmd.append("--no-deps")
        install_cmd.append(str(artifact))
        run(install_cmd, cwd=tmp, env=env)
        scripts = {name: venv_script(venv_dir, name) for name in PUBLIC_CONSOLE_SCRIPTS}
        module_result = run([str(py), "-m", "ga_tui.integration", "doctor", "--root", str(fake_root)], cwd=tmp, env=env)
        main_help_result = run([str(scripts["shuheng"]), "--help"], cwd=tmp, env=env)
        for name in HELP_SAFE_CONSOLE_SCRIPTS:
            run([str(scripts[name]), "--help"], cwd=tmp, env=env)
        entrypoint = scripts["shuheng-check"]
        entrypoint_result = run([str(entrypoint), "--root", str(fake_root)], cwd=tmp, env=env)
        return {
            "schema_version": "shuheng.wheel_smoke.v1",
            "ok": True,
            "artifact": artifact.name,
            "artifact_kind": artifact_kind,
            "install_mode": "no_deps" if no_deps else "with_dependencies",
            "checks": [
                *[{"command": f"script exists: {name}", "returncode": 0} for name in PUBLIC_CONSOLE_SCRIPTS],
                {"command": "shuheng --help", "returncode": main_help_result.returncode},
                *[{"command": f"{name} --help", "returncode": 0} for name in HELP_SAFE_CONSOLE_SCRIPTS],
                {"command": "python -m ga_tui.integration doctor", "returncode": module_result.returncode},
                {"command": "shuheng-check", "returncode": entrypoint_result.returncode},
            ],
        }


def run_wheel_smoke(wheel: Path, *, no_deps: bool = False) -> dict[str, object]:
    archive_check = wheel_archive_contract_check(wheel)
    content_check = check_archive_text_has_no_release_leaks(wheel_text_rows(wheel), artifact_kind="wheel")
    report = run_artifact_smoke(wheel, artifact_kind="wheel", no_deps=no_deps)
    report["checks"] = [archive_check, content_check, *list(report["checks"])]
    return report


def run_sdist_smoke(sdist: Path, *, no_deps: bool = False) -> dict[str, object]:
    archive_check = sdist_archive_contract_check(sdist)
    content_check = check_archive_text_has_no_release_leaks(sdist_text_rows(sdist), artifact_kind="sdist")
    report = run_artifact_smoke(sdist, artifact_kind="sdist", no_deps=no_deps)
    report["checks"] = [archive_check, content_check, *list(report["checks"])]
    return report


def run_distribution_smoke(wheel: Path, sdist: Path | None, *, no_deps: bool = False) -> dict[str, object]:
    artifact_reports = [run_wheel_smoke(wheel, no_deps=no_deps)]
    if sdist is not None:
        artifact_reports.append(run_sdist_smoke(sdist, no_deps=no_deps))
    checks: list[dict[str, object]] = []
    for report in artifact_reports:
        artifact_kind = str(report["artifact_kind"])
        artifact = str(report["artifact"])
        for check in report["checks"]:
            row = dict(check)
            row["artifact_kind"] = artifact_kind
            row["artifact"] = artifact
            checks.append(row)
    return {
        "schema_version": "shuheng.wheel_smoke.v1",
        "ok": all(bool(report.get("ok")) for report in artifact_reports),
        "install_mode": "no_deps" if no_deps else "with_dependencies",
        "artifacts": artifact_reports,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install built Shuheng wheel/sdist artifacts in clean venvs and run public entrypoints")
    parser.add_argument("--dist-dir", default="/tmp/shuheng-dist", help="directory containing built shuheng wheel and sdist artifacts")
    parser.add_argument("--wheel", default="", help="explicit wheel path; overrides --dist-dir")
    parser.add_argument("--sdist", default="", help="explicit source distribution path; overrides --dist-dir")
    parser.add_argument("--wheel-only", action="store_true", help="smoke only the wheel artifact for local debugging")
    parser.add_argument("--no-deps", action="store_true", help="install artifacts without dependencies for offline debugging")
    args = parser.parse_args(argv)

    dist_dir = Path(args.dist_dir).expanduser()
    wheel = Path(args.wheel).expanduser() if args.wheel else latest_wheel(dist_dir)
    sdist = None if args.wheel_only else (Path(args.sdist).expanduser() if args.sdist else latest_sdist(dist_dir))
    report = run_distribution_smoke(wheel, sdist, no_deps=args.no_deps)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
