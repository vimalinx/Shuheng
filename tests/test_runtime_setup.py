from __future__ import annotations

import json
from pathlib import Path
import stat
import subprocess

from shuheng import integration
from shuheng import runtime_setup


def write_executable(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_omp_probe_fails_actionably_in_clean_home(tmp_path: Path) -> None:
    probe = runtime_setup.check_omp_runtime({"HOME": str(tmp_path), "PATH": ""})

    assert probe.ok is False
    assert probe.status == "missing_binary"
    assert probe.package == "@oh-my-pi/pi-coding-agent"
    assert probe.required_version == "16.1.7"
    assert probe.action == "Run: shuheng runtime setup-omp"


def test_omp_probe_requires_pinned_cli_and_supported_bun(tmp_path: Path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    guard = '[ -z "${OPENAI_API_KEY:-}${AWS_SECRET_ACCESS_KEY:-}${SSH_AUTH_SOCK:-}" ] || exit 97\n'
    write_executable(bin_dir / "omp", f"#!/bin/sh\n{guard}printf 'omp/16.1.7\\n'\n")
    write_executable(bin_dir / "bun", f"#!/bin/sh\n{guard}printf '1.3.14\\n'\n")
    monkeypatch.setattr(runtime_setup, "_omp_rpc_readiness_error", lambda *_args: "")

    probe = runtime_setup.check_omp_runtime(
        {
            "HOME": str(tmp_path),
            "PATH": str(bin_dir),
            "OPENAI_API_KEY": "ambient-openai-secret",
            "AWS_SECRET_ACCESS_KEY": "ambient-aws-secret",
            "SSH_AUTH_SOCK": "/tmp/agent.sock",
        }
    )

    assert probe.ok is True
    assert probe.detected_version == "16.1.7"
    assert "Bun 1.3.14" in probe.detail


def test_omp_setup_uses_pinned_user_global_bun_package(tmp_path: Path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    (tmp_path / ".bun" / "bin").mkdir(parents=True)
    bun = """#!/bin/sh
[ -z "${OPENAI_API_KEY:-}${AWS_SECRET_ACCESS_KEY:-}${SSH_AUTH_SOCK:-}" ] || exit 97
if [ "$1" = "--version" ]; then
  printf '1.3.14\\n'
  exit 0
fi
printf '%s\\n' "$*" > "$HOME/bun-args.txt"
printf '#!/bin/sh\\nprintf "omp/16.1.7\\\\n"\\n' > "$HOME/.bun/bin/omp"
/usr/bin/chmod 700 "$HOME/.bun/bin/omp"
"""
    write_executable(bin_dir / "bun", bun)
    monkeypatch.setattr(runtime_setup, "_omp_rpc_readiness_error", lambda *_args: "")
    env = {
        "HOME": str(tmp_path),
        "PATH": str(bin_dir),
        "OPENAI_API_KEY": "ambient-openai-secret",
        "AWS_SECRET_ACCESS_KEY": "ambient-aws-secret",
        "SSH_AUTH_SOCK": "/tmp/agent.sock",
    }

    probe = runtime_setup.setup_omp_runtime(env)

    assert probe.ok is True
    assert (tmp_path / "bun-args.txt").read_text(encoding="utf-8").strip() == (
        "add --global @oh-my-pi/pi-coding-agent@16.1.7"
    )
    assert (tmp_path / ".bun" / "bin" / "omp").is_file()


def test_omp_setup_repairs_path_for_custom_bun_install(tmp_path: Path, monkeypatch) -> None:
    bun_install = tmp_path / "custom-bun"
    bun = """#!/bin/sh
case "$1" in
  --version)
    printf '1.3.14\n'
    ;;
  add)
    printf '#!/usr/bin/env bun\n' > "$BUN_INSTALL/bin/omp"
    /usr/bin/chmod 700 "$BUN_INSTALL/bin/omp"
    ;;
  */omp)
    printf 'omp/16.1.7\n'
    ;;
  *)
    exit 2
    ;;
esac
"""
    write_executable(bun_install / "bin" / "bun", bun)
    monkeypatch.setattr(runtime_setup, "_omp_rpc_readiness_error", lambda *_args: "")

    probe = runtime_setup.setup_omp_runtime(
        {"HOME": str(tmp_path), "BUN_INSTALL": str(bun_install), "PATH": ""}
    )

    assert probe.ok is True
    assert probe.binary == str(bun_install / "bin" / "omp")


def test_omp_probe_requires_rpc_round_trip(tmp_path: Path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    write_executable(bin_dir / "omp", "#!/bin/sh\nprintf 'omp/16.1.7\\n'\n")
    write_executable(bin_dir / "bun", "#!/bin/sh\nprintf '1.3.14\\n'\n")
    monkeypatch.setattr(
        runtime_setup,
        "_omp_rpc_readiness_error",
        lambda *_args: "OMP RPC readiness probe did not complete a state round trip.",
    )

    probe = runtime_setup.check_omp_runtime({"HOME": str(tmp_path), "PATH": str(bin_dir)})

    assert probe.ok is False
    assert probe.status == "rpc_unavailable"
    assert "state round trip" in probe.detail


def test_omp_rpc_probe_uses_controlled_placeholder_not_ambient_key(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class FakeRpcAgent:
        def __init__(self, *, env, **_kwargs) -> None:
            captured.update(env)

        def probe_runtime_ready(self, *, timeout) -> bool:
            return timeout == 10.0

        def close(self) -> None:
            return None

    monkeypatch.setattr(runtime_setup, "OhMyPiRpcAgent", FakeRpcAgent)

    error = runtime_setup._omp_rpc_readiness_error(
        "/fake/omp",
        {"PATH": "/usr/bin", "OPENAI_API_KEY": "ambient-secret-must-not-survive"},
    )

    assert error == ""
    assert captured["OPENAI_API_KEY"] == "shuheng-runtime-health-placeholder"
    assert "ambient-secret-must-not-survive" not in captured.values()


def test_omp_replace_prefers_new_managed_binary_over_old_path_binary(tmp_path: Path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    managed_bin = tmp_path / ".bun" / "bin"
    managed_bin.mkdir(parents=True)
    write_executable(bin_dir / "omp", "#!/bin/sh\nprintf 'omp/15.0.0\\n'\n")
    bun = """#!/bin/sh
if [ "$1" = "--version" ]; then
  printf '1.3.14\n'
  exit 0
fi
printf '#!/bin/sh\\nprintf "omp/16.1.7\\\\n"\\n' > "$BUN_INSTALL/bin/omp"
/usr/bin/chmod 700 "$BUN_INSTALL/bin/omp"
"""
    write_executable(bin_dir / "bun", bun)
    monkeypatch.setattr(runtime_setup, "_omp_rpc_readiness_error", lambda *_args: "")

    probe = runtime_setup.setup_omp_runtime(
        {"HOME": str(tmp_path), "PATH": str(bin_dir)},
        replace=True,
    )

    assert probe.ok is True
    assert probe.binary == str(managed_bin / "omp")
    assert "omp/15.0.0" in (bin_dir / "omp").read_text(encoding="utf-8")


def test_omp_setup_rejects_old_bun_before_install(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    write_executable(bin_dir / "bun", "#!/bin/sh\nprintf '1.2.9\\n'\n")

    probe = runtime_setup.setup_omp_runtime({"HOME": str(tmp_path), "PATH": str(bin_dir)})

    assert probe.ok is False
    assert probe.status == "unsupported_installer"
    assert "Upgrade Bun" in probe.action


def test_omp_setup_preserves_existing_unsupported_version_without_replace(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    write_executable(bin_dir / "omp", "#!/bin/sh\nprintf 'omp/17.0.0\\n'\n")

    probe = runtime_setup.setup_omp_runtime({"HOME": str(tmp_path), "PATH": str(bin_dir)})

    assert probe.ok is False
    assert probe.status == "unsupported_version"
    assert "--replace" in probe.action
    assert (bin_dir / "omp").read_text(encoding="utf-8") == "#!/bin/sh\nprintf 'omp/17.0.0\\n'\n"


def write_pi_fixture(root: Path) -> Path:
    root.mkdir(parents=True)
    sidecar = root / "sidecar.mjs"
    sidecar.write_text("// test sidecar\n", encoding="utf-8")
    (root / "package.json").write_text(
        json.dumps({"dependencies": {runtime_setup.PI_NATIVE_SDK_PACKAGE: runtime_setup.PI_NATIVE_SDK_VERSION}}),
        encoding="utf-8",
    )
    (root / "package-lock.json").write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {"dependencies": {runtime_setup.PI_NATIVE_SDK_PACKAGE: runtime_setup.PI_NATIVE_SDK_VERSION}},
                    "node_modules/@earendil-works/pi-coding-agent": {
                        "version": runtime_setup.PI_NATIVE_SDK_VERSION,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return sidecar


def test_pi_setup_uses_locked_npm_ci_and_live_health(tmp_path: Path) -> None:
    sidecar = write_pi_fixture(tmp_path / "sidecar")
    bin_dir = tmp_path / "bin"
    npm_args = tmp_path / "npm-args.txt"
    npm = f"""#!/bin/sh
[ -z "${{OPENAI_API_KEY:-}}${{AWS_SECRET_ACCESS_KEY:-}}${{SSH_AUTH_SOCK:-}}" ] || exit 97
printf '%s\\n' "$*" > "{npm_args}"
/usr/bin/mkdir -p "$PWD/node_modules/@earendil-works/pi-coding-agent"
printf '{{"name":"@earendil-works/pi-coding-agent","version":"0.80.6"}}\\n' \
  > "$PWD/node_modules/@earendil-works/pi-coding-agent/package.json"
"""
    node = """#!/bin/sh
[ -z "${OPENAI_API_KEY:-}${AWS_SECRET_ACCESS_KEY:-}${SSH_AUTH_SOCK:-}" ] || exit 98
printf '{"type":"sidecar_ready"}\\n'
printf '{"type":"response","command":"health","success":true,"data":{"status":"ok"}}\\n'
"""
    write_executable(bin_dir / "npm", npm)
    write_executable(bin_dir / "node", node)
    env = {
        "HOME": str(tmp_path),
        "PATH": str(bin_dir),
        "SHUHENG_PI_NATIVE_SIDECAR": str(sidecar),
        "OPENAI_API_KEY": "ambient-openai-secret",
        "AWS_SECRET_ACCESS_KEY": "ambient-aws-secret",
        "SSH_AUTH_SOCK": "/tmp/agent.sock",
    }

    probe = runtime_setup.setup_pi_native_runtime(env)

    assert probe.ok is True
    assert npm_args.read_text(encoding="utf-8").strip() == (
        "ci --omit=dev --ignore-scripts --no-audit --no-fund"
    )
    assert probe.detected_version == "0.80.6"


def test_pi_live_health_filters_sensitive_environment(tmp_path: Path, monkeypatch) -> None:
    sidecar = write_pi_fixture(tmp_path / "sidecar")
    sdk_package = sidecar.parent / "node_modules" / "@earendil-works" / "pi-coding-agent"
    sdk_package.mkdir(parents=True)
    (sdk_package / "package.json").write_text(
        json.dumps({"name": runtime_setup.PI_NATIVE_SDK_PACKAGE, "version": runtime_setup.PI_NATIVE_SDK_VERSION}),
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    write_executable(bin_dir / "node", "#!/bin/sh\nexit 0\n")
    captured_envs: list[dict[str, str]] = []

    def fake_run(command, *, env, **_kwargs):
        captured_envs.append(dict(env))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                '{"type":"response","command":"health","success":true,'
                '"data":{"status":"ok"}}\n'
            ),
            stderr="",
        )

    monkeypatch.setattr(runtime_setup, "_run_command", fake_run)
    probe = runtime_setup.check_pi_native_runtime(
        {
            "HOME": str(tmp_path),
            "PATH": str(bin_dir),
            "LANG": "C.UTF-8",
            "HTTPS_PROXY": "http://proxy.test:8080",
            "OPENAI_API_KEY": "ambient-openai-secret",
            "AWS_SECRET_ACCESS_KEY": "ambient-aws-secret",
            "SSH_AUTH_SOCK": "/tmp/agent.sock",
            "SHUHENG_PI_NATIVE_SIDECAR": str(sidecar),
        }
    )

    assert probe.ok is True
    assert captured_envs == [
        {
            "PATH": str(bin_dir),
            "LANG": "C.UTF-8",
            "HTTPS_PROXY": "http://proxy.test:8080",
        }
    ]


def test_pi_probe_rejects_unpinned_lock_before_sdk_execution(tmp_path: Path) -> None:
    sidecar = write_pi_fixture(tmp_path / "sidecar")
    (sidecar.parent / "package-lock.json").write_text("{}\n", encoding="utf-8")

    probe = runtime_setup.check_pi_native_runtime(
        {"HOME": str(tmp_path), "PATH": "", "SHUHENG_PI_NATIVE_SIDECAR": str(sidecar)}
    )

    assert probe.ok is False
    assert probe.status == "invalid_lock"


def test_pi_setup_reports_invalid_lock_without_running_installer(tmp_path: Path, monkeypatch) -> None:
    sidecar = write_pi_fixture(tmp_path / "sidecar")
    (sidecar.parent / "package-lock.json").write_text("{}\n", encoding="utf-8")

    def fail_run(*_args, **_kwargs):
        raise AssertionError("installer must not run with an invalid lock")

    monkeypatch.setattr(runtime_setup, "_run_command", fail_run)
    probe = runtime_setup.setup_pi_native_runtime(
        {"HOME": str(tmp_path), "PATH": "", "SHUHENG_PI_NATIVE_SIDECAR": str(sidecar)}
    )

    assert probe.ok is False
    assert probe.status == "invalid_lock"
    assert probe.action == "Reinstall Shuheng, then run: shuheng runtime setup-pi"


def test_shuheng_check_fails_without_omp_and_package_only_is_explicit(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("BUN_INSTALL", raising=False)

    assert integration.doctor_main([]) == 1
    failed_output = capsys.readouterr().out
    assert "OMP runtime check: FAIL (missing_binary)" in failed_output
    assert "shuheng runtime setup-omp" in failed_output
    assert "Status: FAIL" in failed_output

    assert integration.doctor_main(["--package-only"]) == 0
    package_output = capsys.readouterr().out
    assert "OMP runtime check: SKIPPED" in package_output
    assert "does not prove" in package_output
    assert "Status: OK" in package_output
