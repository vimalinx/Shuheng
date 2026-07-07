#!/usr/bin/env python3
"""Install built Shuheng distribution artifacts in clean venvs and run public entrypoints."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile

try:
    from .release_scan_rules import text_release_leak_errors as shared_text_release_leak_errors
except ImportError:
    from release_scan_rules import text_release_leak_errors as shared_text_release_leak_errors


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
    "shuheng-agent-gateway",
    "shuheng-check",
    "shuheng-install-core-shim",
    "shuheng-integration",
)

HELP_SAFE_CONSOLE_SCRIPTS = (
    "shuheng-agent-bridge",
    "shuheng-agent-gateway",
    "shuheng-install-core-shim",
    "shuheng-integration",
)

SDIST_SOURCES_MEMBER = "src/shuheng.egg-info/SOURCES.txt"
SDIST_GENERATED_MEMBERS_NOT_IN_SOURCES = ("PKG-INFO", "setup.cfg")

SDIST_REQUIRED_MEMBERS = (
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "MANIFEST.in",
    "PKG-INFO",
    "README.en.md",
    "README.md",
    "SECURITY.md",
    "docs/agent-harness-architecture.md",
    "docs/runtime-provider-control-plane.md",
    "integrations/omp-shuheng-plugin/README.md",
    "integrations/omp-shuheng-plugin/package.json",
    "integrations/omp-shuheng-plugin/tools/index.ts",
    "pyproject.toml",
    "scripts/check_policy_gates.py",
    "scripts/check_release_hygiene.py",
    "scripts/release_scan_rules.py",
    "scripts/runtime_smoke.py",
    "scripts/wheel_smoke.py",
    "src/shuheng/builtin_plugins/shuheng-examples/plugin.json",
    "src/shuheng/builtin_plugins/shuheng-examples/workflows/daily-briefing.json",
    "src/shuheng/app.py",
    "src/shuheng.egg-info/PKG-INFO",
    SDIST_SOURCES_MEMBER,
    "src/shuheng.egg-info/entry_points.txt",
    "src/shuheng.egg-info/top_level.txt",
    "tests/test_release_hygiene.py",
    "tests/test_wheel_smoke.py",
)

SDIST_METADATA_MEMBERS = (
    "PKG-INFO",
    "src/shuheng.egg-info/PKG-INFO",
    "src/shuheng.egg-info/entry_points.txt",
    "src/shuheng.egg-info/top_level.txt",
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
    "shuheng/__init__.py",
    "shuheng/__main__.py",
    "shuheng/app.py",
    "shuheng/builtin_plugins/shuheng-examples/plugin.json",
    "shuheng/builtin_plugins/shuheng-examples/workflows/daily-briefing.json",
    "shuheng/integration.py",
    "shuheng/release_readiness.py",
)

WHEEL_FORBIDDEN_PACKAGE_MEMBERS = (
    "shuheng/gateway_registry.py",
    "shuheng/web_console.py",
    "shuheng/web_console_static.py",
)

WHEEL_REQUIRED_DIST_INFO_MEMBERS = (
    "METADATA",
    "WHEEL",
    "entry_points.txt",
    "top_level.txt",
    "RECORD",
    "licenses/LICENSE",
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
    return shared_text_release_leak_errors(text, path, location="artifact member")


def retired_naming_fragments() -> tuple[str, ...]:
    retired_tui = "ga" + "-tui"
    retired_package = "ga" + "_tui"
    retired_control = "ga" + "-control"
    retired_control_type = "ga" + "_control"
    retired_product = "generic" + "agent-tui"
    return (
        retired_tui,
        retired_tui.upper().replace("-", "_"),
        retired_package,
        retired_package.upper(),
        retired_control,
        retired_control_type,
        "<" + retired_tui,
        retired_product,
    )


def check_archive_text_has_no_retired_naming(rows: list[tuple[str, bytes]], *, artifact_kind: str) -> dict[str, object]:
    errors: list[str] = []
    fragments = retired_naming_fragments()
    for path, data in rows:
        text = data.decode("utf-8", errors="replace").lower()
        for fragment in fragments:
            if fragment.lower() in text:
                errors.append(f"retired pre-Shuheng naming found in artifact member: {path}: {fragment}")
    if errors:
        raise ValueError(f"{artifact_kind} retired naming surface scan failed: " + "; ".join(errors))
    return {
        "command": f"{artifact_kind} retired naming surface scan",
        "returncode": 0,
        "scanned_members": len(rows),
    }


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


def sdist_text_by_member(sdist: Path, wanted: tuple[str, ...]) -> dict[str, str]:
    wanted_set = set(wanted)
    texts: dict[str, str] = {}
    with tarfile.open(sdist, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            parts = normalized_archive_parts(member.name)
            if len(parts) < 2:
                continue
            display_path = "/".join(parts[1:])
            if display_path not in wanted_set:
                continue
            file_obj = archive.extractfile(member)
            if file_obj is not None:
                texts[display_path] = file_obj.read().decode("utf-8", errors="replace")
    return texts


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


def normalized_sdist_file_members(sdist: Path) -> set[str]:
    with tarfile.open(sdist, "r:gz") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]

    top_levels: set[str] = set()
    normalized: set[str] = set()
    for member in members:
        parts = normalized_archive_parts(member.name)
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


def sdist_metadata_contract_check(sdist: Path) -> dict[str, object]:
    members = normalized_sdist_members(sdist)
    missing = sorted(member for member in SDIST_METADATA_MEMBERS if member not in members)
    texts = sdist_text_by_member(sdist, SDIST_METADATA_MEMBERS)
    errors: list[str] = []
    for path in ("PKG-INFO", "src/shuheng.egg-info/PKG-INFO"):
        text = texts.get(path, "")
        if path in missing:
            continue
        if "Name: shuheng" not in text:
            errors.append(f"{path} missing Name: shuheng")
        if "Version:" not in text:
            errors.append(f"{path} missing Version")
    entry_points_text = texts.get("src/shuheng.egg-info/entry_points.txt", "")
    missing_console_scripts = sorted(script for script in PUBLIC_CONSOLE_SCRIPTS if f"{script} =" not in entry_points_text)
    if "src/shuheng.egg-info/entry_points.txt" not in missing and missing_console_scripts:
        errors.append("entry_points.txt missing console scripts: " + ", ".join(missing_console_scripts))
    top_level_text = texts.get("src/shuheng.egg-info/top_level.txt", "")
    if "src/shuheng.egg-info/top_level.txt" not in missing and "shuheng" not in {line.strip() for line in top_level_text.splitlines()}:
        errors.append("top_level.txt missing shuheng")
    if missing or errors:
        details = []
        if missing:
            details.append("missing required members: " + ", ".join(missing))
        details.extend(errors)
        raise ValueError("sdist metadata contract failed: " + "; ".join(details))
    return {
        "command": "sdist metadata/entry points contract",
        "returncode": 0,
        "required_members": len(SDIST_METADATA_MEMBERS),
        "console_scripts": len(PUBLIC_CONSOLE_SCRIPTS),
    }


def sdist_sources_integrity_check(sdist: Path) -> dict[str, object]:
    members = normalized_sdist_file_members(sdist)
    if SDIST_SOURCES_MEMBER not in members:
        raise ValueError(f"sdist SOURCES integrity failed: missing {SDIST_SOURCES_MEMBER}")

    sources_text = sdist_text_by_member(sdist, (SDIST_SOURCES_MEMBER,)).get(SDIST_SOURCES_MEMBER, "")
    rows = [line.strip() for line in sources_text.splitlines() if line.strip()]
    source_paths: list[str] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    invalid_rows: list[str] = []
    for row in rows:
        try:
            parts = normalized_archive_parts(row)
        except ValueError:
            invalid_rows.append(row)
            continue
        if not parts:
            invalid_rows.append(row)
            continue
        path = "/".join(parts)
        if path in seen:
            duplicates.append(path)
        seen.add(path)
        source_paths.append(path)

    source_set = set(source_paths)
    allowed_missing = set(SDIST_GENERATED_MEMBERS_NOT_IN_SOURCES)
    missing_rows = sorted(member for member in members if member not in source_set and member not in allowed_missing)
    extra_rows = sorted(path for path in source_set if path not in members)
    errors: list[str] = []
    if invalid_rows:
        errors.append("invalid SOURCES rows: " + ", ".join(sorted(invalid_rows)))
    if duplicates:
        errors.append("duplicate SOURCES rows: " + ", ".join(sorted(set(duplicates))))
    if missing_rows:
        errors.append("SOURCES missing rows for archive members: " + ", ".join(missing_rows))
    if extra_rows:
        errors.append("SOURCES rows for missing archive members: " + ", ".join(extra_rows))
    if errors:
        raise ValueError("sdist SOURCES integrity failed: " + "; ".join(errors))
    return {
        "command": "sdist SOURCES manifest integrity",
        "returncode": 0,
        "manifest_rows": len(rows),
        "archive_members": len(members),
        "generated_members_not_required": sorted(allowed_missing & members),
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


def wheel_record_hash(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def wheel_record_integrity_check(wheel: Path) -> dict[str, object]:
    members = normalized_wheel_members(wheel)
    dist_info_dir = wheel_dist_info_dir(members)
    record_path = f"{dist_info_dir}/RECORD"
    if record_path not in members:
        raise ValueError(f"wheel RECORD integrity failed: missing {record_path}")

    with zipfile.ZipFile(wheel) as archive:
        archive_names = [
            "/".join(normalized_archive_parts(raw_name))
            for raw_name in archive.namelist()
            if not raw_name.endswith("/")
        ]
        archive_member_set = set(archive_names)
        record_text = archive.read(record_path).decode("utf-8", errors="replace")
        record_rows = list(csv.reader(io.StringIO(record_text)))
        row_by_path: dict[str, list[str]] = {}
        duplicates: list[str] = []
        for row in record_rows:
            if not row:
                continue
            path = row[0]
            if path in row_by_path:
                duplicates.append(path)
            row_by_path[path] = row

        errors: list[str] = []
        if duplicates:
            errors.append("duplicate RECORD rows: " + ", ".join(sorted(duplicates)))
        missing_rows = sorted(member for member in archive_member_set if member not in row_by_path)
        if missing_rows:
            errors.append("RECORD missing rows: " + ", ".join(missing_rows))
        extra_rows = sorted(path for path in row_by_path if path not in archive_member_set)
        if extra_rows:
            errors.append("RECORD rows for missing members: " + ", ".join(extra_rows))

        verified = 0
        for member in sorted(archive_member_set):
            row = row_by_path.get(member)
            if not row:
                continue
            hash_field = row[1] if len(row) > 1 else ""
            size_field = row[2] if len(row) > 2 else ""
            if member == record_path:
                if hash_field or size_field:
                    errors.append(f"RECORD self row must not carry hash/size: {member}")
                continue
            data = archive.read(member)
            expected_hash = wheel_record_hash(data)
            if not hash_field:
                errors.append(f"RECORD missing hash: {member}")
            elif not hash_field.startswith("sha256="):
                errors.append(f"RECORD must use sha256 hash: {member}")
            elif hash_field != expected_hash:
                errors.append(f"RECORD hash mismatch: {member}")
            if not size_field:
                errors.append(f"RECORD missing size: {member}")
            else:
                try:
                    size = int(size_field)
                except ValueError:
                    errors.append(f"RECORD invalid size: {member}")
                else:
                    if size != len(data):
                        errors.append(f"RECORD size mismatch: {member}")
            if hash_field == expected_hash and size_field == str(len(data)):
                verified += 1

    if errors:
        raise ValueError("wheel RECORD integrity failed: " + "; ".join(errors))
    return {
        "command": "wheel RECORD hash/size integrity",
        "returncode": 0,
        "verified_members": verified,
        "record_rows": len(record_rows),
    }


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
        if (
            member in SDIST_FORBIDDEN_MEMBERS
            or member in WHEEL_FORBIDDEN_PACKAGE_MEMBERS
            or member.startswith(SDIST_FORBIDDEN_PREFIXES)
        )
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
        module_result = run([str(py), "-m", "shuheng.integration", "doctor", "--root", str(fake_root)], cwd=tmp, env=env)
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
                {"command": "python -m shuheng.integration doctor", "returncode": module_result.returncode},
                {"command": "shuheng-check", "returncode": entrypoint_result.returncode},
            ],
        }


def run_wheel_smoke(wheel: Path, *, no_deps: bool = False) -> dict[str, object]:
    archive_check = wheel_archive_contract_check(wheel)
    record_check = wheel_record_integrity_check(wheel)
    text_rows = wheel_text_rows(wheel)
    retired_naming_check = check_archive_text_has_no_retired_naming(text_rows, artifact_kind="wheel")
    content_check = check_archive_text_has_no_release_leaks(text_rows, artifact_kind="wheel")
    report = run_artifact_smoke(wheel, artifact_kind="wheel", no_deps=no_deps)
    report["checks"] = [archive_check, record_check, retired_naming_check, content_check, *list(report["checks"])]
    return report


def run_sdist_smoke(sdist: Path, *, no_deps: bool = False) -> dict[str, object]:
    archive_check = sdist_archive_contract_check(sdist)
    metadata_check = sdist_metadata_contract_check(sdist)
    sources_check = sdist_sources_integrity_check(sdist)
    text_rows = sdist_text_rows(sdist)
    retired_naming_check = check_archive_text_has_no_retired_naming(text_rows, artifact_kind="sdist")
    content_check = check_archive_text_has_no_release_leaks(text_rows, artifact_kind="sdist")
    report = run_artifact_smoke(sdist, artifact_kind="sdist", no_deps=no_deps)
    report["checks"] = [archive_check, metadata_check, sources_check, retired_naming_check, content_check, *list(report["checks"])]
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
