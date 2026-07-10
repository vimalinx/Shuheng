from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install.sh"


def run_installer(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    run_env.pop("PYTHONPATH", None)
    if env:
        run_env.update(env)
    return subprocess.run(
        ["sh", str(SCRIPT), *args],
        cwd=ROOT,
        env=run_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_install_script_is_executable_and_syntax_valid() -> None:
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR

    result = subprocess.run(["sh", "-n", str(SCRIPT)], text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr


def test_install_script_help_documents_platform_contract() -> None:
    result = run_installer("--help")
    assert result.returncode == 0, result.stderr
    assert "Linux" in result.stdout
    assert "Windows via WSL2" in result.stdout
    assert "macOS" in result.stdout
    assert "Windows native" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--source PATH" in result.stdout
    assert "--wheel-url URL" in result.stdout
    assert "shuheng runtime setup-omp" in result.stdout
    assert "shuheng runtime setup-pi" in result.stdout


def test_install_launchers_honor_custom_bun_install() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'BUN_ROOT="\\${BUN_INSTALL:-\\${HOME:-$HOME_DIR}/.bun}"' in source
    assert 'PATH="\\$BUN_ROOT/bin:\\${PATH:-}"' in source


def test_install_script_dry_run_source_install_does_not_mutate(tmp_path: Path) -> None:
    prefix = tmp_path / "install-root"
    bin_dir = tmp_path / "bin"

    result = run_installer(
        "--dry-run",
        "--source",
        str(ROOT),
        "--editable",
        "--prefix",
        str(prefix),
        "--bin-dir",
        str(bin_dir),
        "--skip-check",
        "--skip-agent-gateway-skill",
        env={"HOME": str(tmp_path)},
    )

    assert result.returncode == 0, result.stderr
    assert "Platform:" in result.stdout
    assert f"Install target: source {ROOT}" in result.stdout
    assert f"+ mkdir -p {prefix}" in result.stdout
    assert f"+ mkdir -p {bin_dir}" in result.stdout
    assert "pip install -e" in result.stdout
    assert f"+ {bin_dir}/shuheng runtime setup-omp" in result.stdout
    assert "runtime setup-omp --replace" not in result.stdout
    assert "Skipping shuheng-check." in result.stdout
    assert not prefix.exists()
    assert not bin_dir.exists()


def test_install_script_derives_alpha_wheel_url_in_dry_run(tmp_path: Path) -> None:
    result = run_installer(
        "--dry-run",
        "--version",
        "v9.8.7-alpha.6",
        "--prefix",
        str(tmp_path / "install-root"),
        "--bin-dir",
        str(tmp_path / "bin"),
        "--skip-check",
        "--skip-agent-gateway-skill",
        env={"HOME": str(tmp_path)},
    )

    assert result.returncode == 0, result.stderr
    assert "https://github.com/vimalinx/Shuheng/releases/download/v9.8.7-alpha.6/" in result.stdout
    assert "shuheng-9.8.7a6-py3-none-any.whl" in result.stdout


def test_install_script_default_release_uses_pep440_alpha_wheel_name(tmp_path: Path) -> None:
    result = run_installer(
        "--dry-run",
        "--prefix",
        str(tmp_path / "install-root"),
        "--bin-dir",
        str(tmp_path / "bin"),
        "--skip-check",
        "--skip-agent-gateway-skill",
        env={"HOME": str(tmp_path)},
    )

    assert result.returncode == 0, result.stderr
    assert "/v0.2.0-alpha.1/shuheng-0.2.0a1-py3-none-any.whl" in result.stdout


def test_install_script_rejects_native_windows_shell(tmp_path: Path) -> None:
    result = run_installer(
        "--dry-run",
        env={
            "HOME": str(tmp_path),
            "SHUHENG_INSTALL_UNAME": "MINGW64_NT-10.0",
        },
    )

    assert result.returncode != 0
    assert "native Windows is unsupported" in result.stderr
    assert "WSL2" in result.stderr
