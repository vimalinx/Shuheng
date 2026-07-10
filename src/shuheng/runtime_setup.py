"""Install and verify Shuheng's external JavaScript runtimes.

OMP is Shuheng's permanent main runtime.  The Pi-native SDK sidecar is an
optional worker runtime installed beside the Python package data files.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Mapping

from .ohmypi_provider import OhMyPiRpcAgent
from .pi_native_provider import PI_NATIVE_SDK_PACKAGE, PI_NATIVE_SDK_VERSION, pi_native_subprocess_env


OMP_PACKAGE = "@oh-my-pi/pi-coding-agent"
OMP_VERSION = "16.1.7"
OMP_PACKAGE_SPEC = f"{OMP_PACKAGE}@{OMP_VERSION}"
OMP_MIN_BUN_VERSION = "1.3.14"

_VERSION_RE = re.compile(r"(?<!\d)(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)(?!\d)")
_RUNTIME_COMMAND_ENV_NAMES = frozenset(
    {
        "ALL_PROXY",
        "BUN_INSTALL",
        "COLORTERM",
        "COMSPEC",
        "FORCE_COLOR",
        "HOME",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "LANG",
        "LANGUAGE",
        "LOGNAME",
        "NODE_EXTRA_CA_CERTS",
        "NO_COLOR",
        "NO_PROXY",
        "PATH",
        "PATHEXT",
        "SHELL",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "SYSTEMROOT",
        "TEMP",
        "TERM",
        "TMP",
        "TMPDIR",
        "USER",
        "USERPROFILE",
        "WINDIR",
        "all_proxy",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    }
)


@dataclass(frozen=True)
class RuntimeProbe:
    """Machine- and human-readable runtime availability result."""

    runtime: str
    ok: bool
    status: str
    package: str
    required_version: str
    binary: str = ""
    detected_version: str = ""
    detail: str = ""
    action: str = ""

    def to_record(self) -> dict[str, object]:
        return asdict(self)


def _source_env(env: Mapping[str, str] | None) -> dict[str, str]:
    return {str(key): str(value) for key, value in (os.environ if env is None else env).items()}


def _runtime_command_env(env: Mapping[str, str]) -> dict[str, str]:
    """Filter host state before executing third-party runtime and installer code."""

    filtered = {
        str(key): str(value)
        for key, value in env.items()
        if key in _RUNTIME_COMMAND_ENV_NAMES or key.startswith("LC_")
    }
    home = str(filtered.get("HOME") or "").strip()
    bun_install = str(filtered.get("BUN_INSTALL") or (os.path.join(home, ".bun") if home else "")).strip()
    if bun_install:
        bun_bin = os.path.join(bun_install, "bin")
        bun = os.path.join(bun_bin, "bun")
        path_parts = [part for part in str(filtered.get("PATH") or "").split(os.pathsep) if part]
        if os.path.isfile(bun) and os.access(bun, os.X_OK) and bun_bin not in path_parts:
            filtered["PATH"] = os.pathsep.join([bun_bin, *path_parts])
    return filtered


def _home_dir(env: Mapping[str, str]) -> Path:
    configured = str(env.get("HOME") or "").strip()
    return Path(configured).expanduser() if configured else Path.home()


def _bun_install_dir(env: Mapping[str, str]) -> Path:
    configured = str(env.get("BUN_INSTALL") or "").strip()
    return Path(configured).expanduser() if configured else _home_dir(env) / ".bun"


def _executable(command: str, env: Mapping[str, str]) -> str:
    candidate = str(command or "").strip()
    if not candidate:
        return ""
    if os.path.sep in candidate:
        path = Path(candidate).expanduser()
        return str(path.resolve()) if path.is_file() and os.access(path, os.X_OK) else ""
    return shutil.which(candidate, path=env.get("PATH")) or ""


def _bun_binary(env: Mapping[str, str]) -> str:
    discovered = _executable("bun", env)
    if discovered:
        return discovered
    candidate = _bun_install_dir(env) / "bin" / "bun"
    return str(candidate) if candidate.is_file() and os.access(candidate, os.X_OK) else ""


def _omp_binary(env: Mapping[str, str]) -> str:
    explicit = str(env.get("SHUHENG_OHMYPI_BIN") or "").strip()
    if explicit:
        return _executable(explicit, env)
    candidates = (
        _bun_install_dir(env) / "bin" / "omp",
        _home_dir(env) / ".bun" / "bin" / "omp",
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return _executable("omp", env)


def _numeric_version(value: str) -> tuple[int, int, int] | None:
    match = _VERSION_RE.search(value)
    if not match:
        return None
    core = match.group(1).split("-", 1)[0].split("+", 1)[0]
    try:
        major, minor, patch = core.split(".")
        return int(major), int(minor), int(patch)
    except (TypeError, ValueError):
        return None


def _bun_version(binary: str, env: Mapping[str, str]) -> tuple[str, str]:
    try:
        result = _run_command([binary, "--version"], env=env, timeout=15.0)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", f"Bun version probe failed: {type(exc).__name__}: {exc}"
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    match = _VERSION_RE.search(output)
    version = match.group(1) if match else ""
    if result.returncode != 0 or not version:
        return version, f"`bun --version` failed: {output or 'no output'}"
    return version, ""


def _run_command(
    command: list[str],
    *,
    env: Mapping[str, str],
    cwd: Path | None = None,
    input_text: str | None = None,
    timeout: float = 120.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=dict(env),
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )


def _omp_rpc_readiness_error(binary: str, env: Mapping[str, str]) -> str:
    """Return a bounded error when OMP cannot complete a real RPC round trip."""

    try:
        with tempfile.TemporaryDirectory(prefix="shuheng-omp-check-") as tmp:
            agent_dir = Path(tmp) / "agent"
            agent_dir.mkdir(mode=0o700)
            process_env = dict(env)
            process_env["PI_CODING_AGENT_DIR"] = str(agent_dir)
            # OMP needs one provider to enter RPC mode. This fixed placeholder
            # enables local state inspection only; no model request is sent.
            process_env["OPENAI_API_KEY"] = "shuheng-runtime-health-placeholder"
            agent = OhMyPiRpcAgent(
                command=[binary, "--mode", "rpc", "--no-title", "--approval-mode", "write"],
                cwd=tmp,
                env=process_env,
                startup_timeout=10.0,
                stop_timeout=2.0,
            )
            try:
                if not agent.probe_runtime_ready(timeout=10.0):
                    return "OMP RPC readiness probe did not complete a state round trip."
            finally:
                agent.close()
    except Exception as exc:
        return f"OMP RPC readiness probe failed: {type(exc).__name__}."
    return ""


def check_omp_runtime(env: Mapping[str, str] | None = None) -> RuntimeProbe:
    """Require the pinned OMP CLI and verify that it starts."""

    source = _source_env(env)
    process_env = _runtime_command_env(source)
    binary = _omp_binary(source)
    action = "Run: shuheng runtime setup-omp"
    if not binary:
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="missing_binary",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            detail="The required `omp` executable was not found on PATH or at ~/.bun/bin/omp.",
            action=action,
        )
    try:
        result = _run_command([binary, "--version"], env=process_env, timeout=15.0)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="unresponsive",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            binary=binary,
            detail=f"OMP version probe failed: {type(exc).__name__}: {exc}",
            action=action,
        )
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    match = _VERSION_RE.search(output)
    detected_version = match.group(1) if match else ""
    if result.returncode != 0:
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="unresponsive",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            binary=binary,
            detected_version=detected_version,
            detail=f"`omp --version` exited with status {result.returncode}: {output or 'no output'}",
            action=action,
        )
    if detected_version != OMP_VERSION:
        detected = detected_version or "unknown"
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="unsupported_version",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            binary=binary,
            detected_version=detected_version,
            detail=f"Detected OMP {detected}; Shuheng currently pins {OMP_VERSION}.",
            action=action,
        )
    bun = _bun_binary(source)
    if not bun:
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="missing_bun",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            binary=binary,
            detected_version=detected_version,
            detail=f"OMP {OMP_VERSION} requires Bun >= {OMP_MIN_BUN_VERSION}, but Bun was not found.",
            action="Install Bun so `bun` is on PATH, then run: shuheng runtime setup-omp",
        )
    bun_version, bun_error = _bun_version(bun, process_env)
    parsed_bun = _numeric_version(bun_version)
    minimum_bun = _numeric_version(OMP_MIN_BUN_VERSION)
    if bun_error or parsed_bun is None or minimum_bun is None or parsed_bun < minimum_bun:
        detected_bun = bun_version or "unknown"
        detail = bun_error or f"Detected Bun {detected_bun}; OMP {OMP_VERSION} requires Bun >= {OMP_MIN_BUN_VERSION}."
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="unsupported_bun",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            binary=binary,
            detected_version=detected_version,
            detail=detail,
            action="Upgrade Bun, then run: shuheng runtime setup-omp",
        )
    rpc_error = _omp_rpc_readiness_error(binary, process_env)
    if rpc_error:
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="rpc_unavailable",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            binary=binary,
            detected_version=detected_version,
            detail=rpc_error,
            action=action,
        )
    return RuntimeProbe(
        runtime="omp",
        ok=True,
        status="available",
        package=OMP_PACKAGE,
        required_version=OMP_VERSION,
        binary=binary,
        detected_version=detected_version,
        detail=f"Pinned OMP runtime and RPC state round trip are available with Bun {bun_version}.",
    )


def setup_omp_runtime(env: Mapping[str, str] | None = None, *, replace: bool = False) -> RuntimeProbe:
    """Idempotently install the pinned OMP CLI with Bun's user-global store.

    An existing unsupported OMP is preserved unless the operator explicitly
    requests replacement.
    """

    source = _source_env(env)
    source.setdefault("BUN_INSTALL", str(_home_dir(source) / ".bun"))
    current = check_omp_runtime(source)
    if current.ok:
        return current
    if current.binary and not replace:
        action = current.action
        if current.status in {"unresponsive", "unsupported_version"}:
            action = "Keep the existing OMP, or explicitly replace it with: shuheng runtime setup-omp --replace"
        return RuntimeProbe(**{**current.to_record(), "action": action})
    bun = _bun_binary(source)
    if not bun:
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="missing_installer",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            detail="Bun is required to install and run the supported OMP package.",
            action="Install Bun so `bun` is on PATH, then run: shuheng runtime setup-omp",
        )
    process_env = _runtime_command_env(source)
    bun_version, bun_error = _bun_version(bun, process_env)
    parsed_bun = _numeric_version(bun_version)
    minimum_bun = _numeric_version(OMP_MIN_BUN_VERSION)
    if bun_error or parsed_bun is None or minimum_bun is None or parsed_bun < minimum_bun:
        detected_bun = bun_version or "unknown"
        detail = bun_error or f"Detected Bun {detected_bun}; OMP requires Bun >= {OMP_MIN_BUN_VERSION}."
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="unsupported_installer",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            binary=bun,
            detected_version=detected_bun,
            detail=detail,
            action="Upgrade Bun, then run: shuheng runtime setup-omp",
        )
    command = [bun, "add", "--global", OMP_PACKAGE_SPEC]
    try:
        result = _run_command(command, env=process_env, timeout=300.0)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="install_failed",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            detail=f"OMP installation failed: {type(exc).__name__}: {exc}",
            action=f"Run manually: bun add --global {OMP_PACKAGE_SPEC}",
        )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or "no installer output"
        return RuntimeProbe(
            runtime="omp",
            ok=False,
            status="install_failed",
            package=OMP_PACKAGE,
            required_version=OMP_VERSION,
            detail=f"Bun exited with status {result.returncode}: {detail}",
            action=f"Run manually: bun add --global {OMP_PACKAGE_SPEC}",
        )
    installed = check_omp_runtime(source)
    if installed.ok:
        return RuntimeProbe(**{**installed.to_record(), "detail": f"Installed {OMP_PACKAGE_SPEC}."})
    return RuntimeProbe(
        **{
            **installed.to_record(),
            "detail": f"Bun installed {OMP_PACKAGE_SPEC}, but verification failed. {installed.detail}",
        }
    )


def pi_native_sidecar_path(env: Mapping[str, str] | None = None) -> Path:
    source = _source_env(env)
    configured = str(source.get("SHUHENG_PI_NATIVE_SIDECAR") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    root = Path(__file__).resolve().parents[2]
    source_checkout = root / "integrations" / "pi-native-sidecar" / "sidecar.mjs"
    installed_data = Path(sys.prefix) / "share" / "shuheng" / "pi-native-sidecar" / "sidecar.mjs"
    for candidate in (source_checkout, installed_data):
        if candidate.is_file():
            return candidate
    return installed_data


def _pi_binary(env: Mapping[str, str]) -> str:
    explicit = str(env.get("SHUHENG_PI_NATIVE_BIN") or "").strip()
    if explicit:
        return _executable(explicit, env)
    return _bun_binary(env) or _executable("node", env)


def _pi_sdk_metadata(sidecar: Path) -> tuple[str, str]:
    package_path = sidecar.parent / "node_modules" / "@earendil-works" / "pi-coding-agent" / "package.json"
    try:
        payload = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    return str(payload.get("name") or ""), str(payload.get("version") or "")


def _pi_lock_is_pinned(sidecar: Path) -> bool:
    lock_path = sidecar.parent / "package-lock.json"
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    packages = payload.get("packages")
    if not isinstance(packages, dict):
        return False
    root = packages.get("")
    sdk = packages.get("node_modules/@earendil-works/pi-coding-agent")
    if not isinstance(root, dict) or not isinstance(sdk, dict):
        return False
    dependencies = root.get("dependencies")
    return (
        isinstance(dependencies, dict)
        and dependencies.get(PI_NATIVE_SDK_PACKAGE) == PI_NATIVE_SDK_VERSION
        and sdk.get("version") == PI_NATIVE_SDK_VERSION
    )


def check_pi_native_runtime(env: Mapping[str, str] | None = None) -> RuntimeProbe:
    """Verify the optional sidecar, pinned SDK package, and live SDK import."""

    source = _source_env(env)
    process_env = pi_native_subprocess_env(source)
    sidecar = pi_native_sidecar_path(source)
    action = "Run: shuheng runtime setup-pi"
    if not sidecar.is_file():
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="missing_sidecar",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            detail=f"Pi-native sidecar is missing: {sidecar}",
            action="Reinstall Shuheng, then run: shuheng runtime setup-pi",
        )
    if not _pi_lock_is_pinned(sidecar):
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="invalid_lock",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            detail=f"Pi-native package-lock.json is missing or does not pin {PI_NATIVE_SDK_PACKAGE}@{PI_NATIVE_SDK_VERSION}.",
            action="Reinstall Shuheng, then run: shuheng runtime setup-pi",
        )
    binary = _pi_binary(source)
    if not binary:
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="missing_binary",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            detail="Neither Bun nor Node was found for the optional Pi-native sidecar.",
            action=action,
        )
    package, version = _pi_sdk_metadata(sidecar)
    if package != PI_NATIVE_SDK_PACKAGE or version != PI_NATIVE_SDK_VERSION:
        detected = f"{package}@{version}" if package and version else "not installed"
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="missing_package" if not package else "unsupported_version",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            binary=binary,
            detected_version=version,
            detail=f"Detected Pi-native SDK {detected}; required {PI_NATIVE_SDK_PACKAGE}@{PI_NATIVE_SDK_VERSION}.",
            action=action,
        )
    health_request = json.dumps({"id": "shuheng-runtime-check", "type": "health"}) + "\n"
    try:
        result = _run_command(
            [binary, str(sidecar)],
            cwd=sidecar.parent,
            env=process_env,
            input_text=health_request,
            timeout=30.0,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="unresponsive",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            binary=binary,
            detected_version=version,
            detail=f"Pi-native health probe failed: {type(exc).__name__}: {exc}",
            action=action,
        )
    response: dict[str, object] = {}
    for line in result.stdout.splitlines():
        try:
            frame = json.loads(line)
        except ValueError:
            continue
        if isinstance(frame, dict) and frame.get("command") == "health":
            response = frame
            break
    if result.returncode != 0 or response.get("success") is not True:
        error = str(response.get("error") or result.stderr.strip() or "no health response")
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="unhealthy",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            binary=binary,
            detected_version=version,
            detail=f"Pi-native sidecar health check failed: {error}",
            action=action,
        )
    return RuntimeProbe(
        runtime="pi-native",
        ok=True,
        status="available",
        package=PI_NATIVE_SDK_PACKAGE,
        required_version=PI_NATIVE_SDK_VERSION,
        binary=binary,
        detected_version=version,
        detail="Optional Pi-native SDK sidecar is available.",
    )


def setup_pi_native_runtime(env: Mapping[str, str] | None = None) -> RuntimeProbe:
    """Idempotently install the pinned Pi SDK beside the packaged sidecar."""

    source = _source_env(env)
    process_env = pi_native_subprocess_env(source)
    current = check_pi_native_runtime(source)
    if current.ok:
        return current
    sidecar = pi_native_sidecar_path(source)
    package_json = sidecar.parent / "package.json"
    package_lock = sidecar.parent / "package-lock.json"
    if not sidecar.is_file() or not package_json.is_file() or not package_lock.is_file():
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="missing_sidecar",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            detail=f"Packaged Pi-native integration files are incomplete under {sidecar.parent}.",
            action="Reinstall Shuheng, then run: shuheng runtime setup-pi",
        )
    if not _pi_lock_is_pinned(sidecar):
        return current
    npm = _executable("npm", source)
    if not npm:
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="missing_installer",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            detail="npm is required for the lockfile-reproducible optional Pi-native SDK installation.",
            action="Install Node.js/npm, then run: shuheng runtime setup-pi",
        )
    command = [npm, "ci", "--omit=dev", "--ignore-scripts", "--no-audit", "--no-fund"]
    try:
        result = _run_command(command, cwd=sidecar.parent, env=process_env, timeout=300.0)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="install_failed",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            detail=f"Pi-native SDK installation failed: {type(exc).__name__}: {exc}",
            action="Run: shuheng runtime setup-pi",
        )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or "no installer output"
        return RuntimeProbe(
            runtime="pi-native",
            ok=False,
            status="install_failed",
            package=PI_NATIVE_SDK_PACKAGE,
            required_version=PI_NATIVE_SDK_VERSION,
            detail=f"Package installer exited with status {result.returncode}: {detail}",
            action="Run: shuheng runtime setup-pi",
        )
    installed = check_pi_native_runtime(source)
    if installed.ok:
        spec = f"{PI_NATIVE_SDK_PACKAGE}@{PI_NATIVE_SDK_VERSION}"
        return RuntimeProbe(**{**installed.to_record(), "detail": f"Installed and verified {spec}."})
    return RuntimeProbe(
        **{
            **installed.to_record(),
            "detail": f"Pi-native package installation completed, but verification failed. {installed.detail}",
        }
    )


__all__ = [
    "OMP_PACKAGE",
    "OMP_PACKAGE_SPEC",
    "OMP_MIN_BUN_VERSION",
    "OMP_VERSION",
    "PI_NATIVE_SDK_PACKAGE",
    "PI_NATIVE_SDK_VERSION",
    "RuntimeProbe",
    "check_omp_runtime",
    "check_pi_native_runtime",
    "pi_native_sidecar_path",
    "setup_omp_runtime",
    "setup_pi_native_runtime",
]
