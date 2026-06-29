#!/usr/bin/env python3
"""Install the built Shuheng wheel in a clean venv and run public entrypoints."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


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


def latest_wheel(dist_dir: Path) -> Path:
    wheels = sorted(dist_dir.glob("shuheng-*.whl"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not wheels:
        raise FileNotFoundError(f"no shuheng wheel found in {dist_dir}; run python -m build first")
    return wheels[0]


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


def run_wheel_smoke(wheel: Path) -> dict[str, object]:
    wheel = wheel.resolve()
    if not wheel.is_file():
        raise FileNotFoundError(f"wheel not found: {wheel}")
    with tempfile.TemporaryDirectory(prefix="shuheng_wheel_smoke_") as tmp_s:
        tmp = Path(tmp_s)
        venv_dir = tmp / "venv"
        fake_root = write_fake_genericagent_root(tmp)
        venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
        py = venv_python(venv_dir)
        env = clean_env()
        run([str(py), "-m", "pip", "install", "--no-deps", str(wheel)], cwd=tmp, env=env)
        module_result = run([str(py), "-m", "ga_tui.integration", "doctor", "--root", str(fake_root)], cwd=tmp, env=env)
        entrypoint = venv_script(venv_dir, "shuheng-check")
        entrypoint_result = run([str(entrypoint), "--root", str(fake_root)], cwd=tmp, env=env)
        return {
            "schema_version": "shuheng.wheel_smoke.v1",
            "ok": True,
            "wheel": wheel.name,
            "checks": [
                {"command": "python -m ga_tui.integration doctor", "returncode": module_result.returncode},
                {"command": "shuheng-check", "returncode": entrypoint_result.returncode},
            ],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install the built Shuheng wheel in a clean venv and run public entrypoints")
    parser.add_argument("--dist-dir", default="/tmp/shuheng-dist", help="directory containing shuheng-*.whl")
    parser.add_argument("--wheel", default="", help="explicit wheel path; overrides --dist-dir")
    args = parser.parse_args(argv)

    wheel = Path(args.wheel).expanduser() if args.wheel else latest_wheel(Path(args.dist_dir).expanduser())
    report = run_wheel_smoke(wheel)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
