"""Pi-native task worker provider backed by an isolated JSONL sidecar.

The adapter consumes executable Agent Build bytes only from
``RuntimeTaskRequest.runtime_payload``.  The durable request record deliberately
omits that payload, so Prompt, Skill, and custom Tool source never enters the
task ledger or trace metadata by accident.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable

try:
    from .runtime import RuntimeAdapter, RuntimeProviderSpec, RuntimeTaskEvent, RuntimeTaskRequest
except ImportError:  # pragma: no cover - direct source-tree execution compatibility
    from runtime import RuntimeAdapter, RuntimeProviderSpec, RuntimeTaskEvent, RuntimeTaskRequest  # type: ignore


PI_NATIVE_PROVIDER_ID = "pi-native"
PI_NATIVE_PROTOCOL_VERSION = "shuheng.pi_native.sidecar.v1"
PI_NATIVE_EVENT_SCHEMA = "shuheng.pi_native_event.v1"
PI_NATIVE_BUILD_SCHEMA = "shuheng.agent_build.v1"
PI_NATIVE_RUN_MANIFEST_SCHEMA = "shuheng.agent_run_manifest.v1"
PI_NATIVE_SDK_PACKAGE = "@earendil-works/pi-coding-agent"
PI_NATIVE_SDK_VERSION = "0.80.6"

ProcessFactory = Callable[..., Any]
ThreadFactory = Callable[..., Any]
RuntimeEventSink = Callable[[RuntimeTaskEvent], None]

_SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")
_HEX_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SIDECAR_ENV_ALLOWLIST = frozenset(
    {
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "LANG",
        "LC_ALL",
        "NO_PROXY",
        "PATH",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "TMPDIR",
        "TZ",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    }
)


class _TaskCounter:
    def __init__(self) -> None:
        self._unfinished_tasks = 0
        self._lock = threading.Lock()

    @property
    def unfinished_tasks(self) -> int:
        with self._lock:
            return self._unfinished_tasks

    def start(self) -> None:
        with self._lock:
            self._unfinished_tasks += 1

    def done(self) -> None:
        with self._lock:
            self._unfinished_tasks = max(0, self._unfinished_tasks - 1)


@dataclass
class _ActiveTask:
    request_id: str
    request: RuntimeTaskRequest
    display_queue: queue.Queue
    source: str
    buffer: str = ""
    finished: bool = False
    abort_requested: bool = False
    runtime_dir: str = ""


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    to_record = getattr(value, "to_record", None)
    if callable(to_record):
        record = to_record()
        if isinstance(record, dict):
            return record
    return {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _safe_segment(value: str, fallback: str) -> str:
    text = _SAFE_SEGMENT_RE.sub("-", str(value or "").strip()).strip("-")
    return text or fallback


def pi_native_subprocess_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return the shared minimal environment for Pi-native SDK processes."""

    source = os.environ if base_env is None else base_env
    return {
        str(key): str(value)
        for key, value in source.items()
        if key in _SIDECAR_ENV_ALLOWLIST or key.startswith("LC_")
    }


def _isolated_sidecar_process_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Compatibility alias for the public subprocess-environment contract."""

    return pi_native_subprocess_env(base_env)


def _normalized_relative_path(value: Any) -> str:
    text = str(value or "")
    if not text or text != text.strip() or text.startswith(("/", "~")) or "\\" in text or "\x00" in text:
        return ""
    pure = PurePosixPath(text)
    if not pure.parts or any(part in {"", ".", ".."} for part in pure.parts) or pure.as_posix() != text:
        return ""
    return text


def _decode_build_file(record: dict[str, Any]) -> tuple[str, str, bytes, str]:
    relative_path = _normalized_relative_path(record.get("path"))
    role = str(record.get("role") or "").strip()
    expected_digest = str(record.get("sha256") or "").strip().lower()
    encoded = str(record.get("content_base64") or "").strip()
    if not relative_path or not role:
        raise ValueError("Agent Build file entries require normalized path and role")
    if not _HEX_DIGEST_RE.fullmatch(expected_digest):
        raise ValueError(f"Agent Build file {relative_path!r} has an invalid SHA-256 digest")
    try:
        content = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as exc:
        raise ValueError(f"Agent Build file {relative_path!r} has invalid content_base64") from exc
    if base64.b64encode(content).decode("ascii") != encoded:
        raise ValueError(f"Agent Build file {relative_path!r} has non-canonical content_base64")
    try:
        expected_size = int(record.get("size"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Agent Build file {relative_path!r} has an invalid size") from exc
    if expected_size != len(content):
        raise ValueError(f"Agent Build file {relative_path!r} size mismatch")
    if hashlib.sha256(content).hexdigest() != expected_digest:
        raise ValueError(f"Agent Build file {relative_path!r} digest mismatch")
    return relative_path, role, content, expected_digest


def _verified_build_files(build: dict[str, Any]) -> dict[str, tuple[str, bytes, str]]:
    raw_files = build.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise ValueError("Agent Build files must be a non-empty array")
    files: dict[str, tuple[str, bytes, str]] = {}
    digest = hashlib.sha256()
    digest.update(PI_NATIVE_BUILD_SCHEMA.encode("utf-8") + b"\x00")
    decoded: list[tuple[str, str, bytes, str]] = []
    for item in raw_files:
        if not isinstance(item, dict):
            raise ValueError("Agent Build file entries must be objects")
        entry = _decode_build_file(item)
        if entry[0] in files:
            raise ValueError(f"Agent Build repeats file path {entry[0]!r}")
        files[entry[0]] = (entry[1], entry[2], entry[3])
        decoded.append(entry)
    for relative_path, role, content, _file_digest in sorted(decoded, key=lambda item: item[0]):
        for part in (relative_path.encode("utf-8"), role.encode("utf-8"), content):
            digest.update(len(part).to_bytes(8, "big"))
            digest.update(part)
    expected_build_digest = str(build.get("digest") or build.get("build_digest") or "").strip().lower()
    if not _HEX_DIGEST_RE.fullmatch(expected_build_digest):
        raise ValueError("Agent Build digest must be a lowercase SHA-256 value")
    if digest.hexdigest() != expected_build_digest:
        raise ValueError("Agent Build digest does not match its frozen files")
    return files


def _utf8_source(relative_path: str, content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Agent Build source {relative_path!r} must be UTF-8") from exc


def _frozen_blueprint(files: dict[str, tuple[str, bytes, str]]) -> dict[str, Any]:
    candidates = [(path, entry) for path, entry in files.items() if entry[0] == "blueprint"]
    if len(candidates) != 1:
        raise ValueError("Agent Build must contain exactly one frozen Blueprint file")
    relative_path, entry = candidates[0]
    try:
        value = json.loads(_utf8_source(relative_path, entry[1]))
    except json.JSONDecodeError as exc:
        raise ValueError("Agent Build frozen Blueprint is not valid JSON") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "shuheng.agent_blueprint.v1":
        raise ValueError("Agent Build frozen Blueprint has an unsupported schema")
    return value


def _frozen_project(files: dict[str, tuple[str, bytes, str]]) -> dict[str, Any]:
    candidates = [(path, entry) for path, entry in files.items() if entry[0] == "project_manifest"]
    if len(candidates) != 1:
        raise ValueError("Agent Build must contain exactly one frozen Project manifest file")
    relative_path, entry = candidates[0]
    try:
        value = json.loads(_utf8_source(relative_path, entry[1]))
    except json.JSONDecodeError as exc:
        raise ValueError("Agent Build frozen Project manifest is not valid JSON") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "shuheng.agent_project.v1":
        raise ValueError("Agent Build frozen Project manifest has an unsupported schema")
    return value


def _validated_manifest_authority(
    request: RuntimeTaskRequest,
    build: dict[str, Any],
    project: dict[str, Any],
    blueprint: dict[str, Any],
    run_manifest: dict[str, Any],
) -> tuple[list[str], str]:
    """Recompute the manifest's authority intersection at the Provider boundary."""

    if run_manifest.get("schema_version") != PI_NATIVE_RUN_MANIFEST_SCHEMA:
        raise ValueError(f"runtime_payload.agent_run_manifest must use {PI_NATIVE_RUN_MANIFEST_SCHEMA}")
    if str(run_manifest.get("assignment_id") or "") != str(request.task_id or ""):
        raise ValueError("Agent Run Manifest assignment_id does not match RuntimeTaskRequest.task_id")
    if str(run_manifest.get("build_digest") or "") != str(build.get("digest") or ""):
        raise ValueError("Agent Run Manifest build_digest does not match Agent Build")
    if str(run_manifest.get("project_id") or "") != str(project.get("id") or ""):
        raise ValueError("Agent Run Manifest project_id does not match the frozen Project")
    if str(run_manifest.get("blueprint_id") or "") != str(blueprint.get("id") or ""):
        raise ValueError("Agent Run Manifest blueprint_id does not match the frozen Blueprint")

    provider = _dict(run_manifest.get("provider"))
    if str(provider.get("id") or "") != PI_NATIVE_PROVIDER_ID:
        raise ValueError("Agent Run Manifest does not select the pi-native Provider")
    if str(provider.get("revision") or "") != PI_NATIVE_SDK_VERSION:
        raise ValueError(f"Agent Run Manifest must select pinned Pi SDK revision {PI_NATIVE_SDK_VERSION}")

    frozen_runtime = str(blueprint.get("runtime") or project.get("default_runtime") or "").strip()
    if frozen_runtime != PI_NATIVE_PROVIDER_ID:
        raise ValueError("Agent Build frozen source does not select the pi-native Provider")
    frozen_revision = str(blueprint.get("runtime_version") or project.get("runtime_version") or "").strip()
    if frozen_revision and frozen_revision != PI_NATIVE_SDK_VERSION:
        raise ValueError(f"Agent Build requests unsupported Pi SDK revision {frozen_revision!r}")
    build_runtime = _dict(build.get("runtime"))
    if str(build_runtime.get("provider") or "") != frozen_runtime:
        raise ValueError("Agent Build runtime provider does not match its frozen source")
    if str(build_runtime.get("version") or "") != frozen_revision:
        raise ValueError("Agent Build runtime revision does not match its frozen source")

    capabilities = _dict(run_manifest.get("capabilities"))
    declared_capabilities = sorted(_string_list(blueprint.get("requested_capabilities")))
    requested_capabilities = sorted(_string_list(capabilities.get("requested")))
    granted_capabilities = sorted(_string_list(capabilities.get("granted")))
    effective_capabilities = sorted(_string_list(capabilities.get("effective")))
    if requested_capabilities != declared_capabilities:
        raise ValueError("Agent Run Manifest requested capabilities do not match the frozen Blueprint")
    expected_capabilities = sorted(set(requested_capabilities) & set(granted_capabilities))
    if effective_capabilities != expected_capabilities:
        raise ValueError("Agent Run Manifest effective capabilities are not requested ∩ granted")

    declared_tools: dict[str, set[str]] = {}
    for item in blueprint.get("tools") if isinstance(blueprint.get("tools"), list) else []:
        tool = _dict(item)
        tool_id = str(tool.get("id") or "").strip()
        if not tool_id or tool_id in declared_tools:
            raise ValueError("Agent Build frozen Blueprint contains an invalid or duplicate Tool ID")
        declared_tools[tool_id] = set(_string_list(tool.get("requested_capabilities")))
    tools = _dict(run_manifest.get("tools"))
    requested_tools = sorted(_string_list(tools.get("requested")))
    granted_tools = sorted(_string_list(tools.get("granted")))
    effective_tools = sorted(_string_list(tools.get("effective")))
    if requested_tools != sorted(declared_tools):
        raise ValueError("Agent Run Manifest requested Tools do not match the frozen Blueprint")
    unknown_grants = sorted(set(granted_tools) - set(declared_tools))
    if unknown_grants:
        raise ValueError(f"Agent Run Manifest grants undeclared Tools: {', '.join(unknown_grants)}")
    effective_capability_set = set(effective_capabilities)
    expected_tools = sorted(
        tool_id
        for tool_id in granted_tools
        if declared_tools[tool_id].issubset(effective_capability_set)
    )
    if effective_tools != expected_tools:
        raise ValueError("Agent Run Manifest effective Tools do not match granted Tools and capabilities")

    workspace = str(run_manifest.get("workspace") or "").strip()
    if not workspace or workspace.startswith("~") or not os.path.isabs(workspace):
        raise ValueError("Agent Run Manifest workspace must be an explicit absolute path")
    return effective_tools, os.path.normpath(workspace)


def _frontmatter_value(text: str, field: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 4)
    if end < 0:
        return ""
    prefix = f"{field}:"
    for line in text[4:end].splitlines():
        if line.strip().lower().startswith(prefix):
            return line.split(":", 1)[1].strip().strip("'\"")
    return ""


def _model_record(request: RuntimeTaskRequest, build: dict[str, Any]) -> dict[str, Any]:
    payload_model = _dict(getattr(request, "runtime_payload", {}).get("model"))
    build_model = _dict(build.get("model"))
    provider = str(payload_model.get("provider") or build_model.get("provider") or "").strip()
    model_id = str(payload_model.get("id") or payload_model.get("model_id") or build_model.get("id") or "").strip()
    selector = str(request.model or "").strip()
    if selector == PI_NATIVE_PROVIDER_ID:
        selector = ""
    if selector and "/" in selector:
        provider, model_id = selector.split("/", 1)
    elif selector and not model_id:
        model_id = selector
    thinking_level = str(
        payload_model.get("thinking_level") or build_model.get("thinking_level") or "off"
    ).strip()
    record: dict[str, Any] = {
        "provider": provider,
        "id": model_id,
        "thinking_level": thinking_level or "off",
    }
    for source_key, target_key in (
        ("name", "name"),
        ("api", "api"),
        ("api_key", "api_key"),
        ("base_url", "base_url"),
        ("headers", "headers"),
        ("auth_header", "auth_header"),
        ("reasoning", "reasoning"),
        ("context_window", "context_window"),
        ("max_tokens", "max_tokens"),
    ):
        if source_key in payload_model:
            record[target_key] = copy.deepcopy(payload_model[source_key])
    return record


def _effective_tool_ids(request: RuntimeTaskRequest, run_manifest: dict[str, Any]) -> list[str]:
    manifest_tools = _dict(run_manifest.get("tools"))
    if "effective" in manifest_tools:
        return _string_list(manifest_tools.get("effective"))
    permissions = _dict(request.permissions)
    return _string_list(permissions.get("effective_tool_ids") or permissions.get("tools_allowed"))


def pi_native_run_command(
    request: RuntimeTaskRequest,
    *,
    agent_dir: str,
    workspace_root: str,
    request_id: str,
    mock_mode: bool = False,
    runtime_dir: str = "",
) -> dict[str, Any]:
    """Create a sidecar command without copying executable source into durable metadata."""

    runtime_payload = _dict(getattr(request, "runtime_payload", {}))
    build = _dict(runtime_payload.get("agent_build"))
    if build.get("schema_version") != PI_NATIVE_BUILD_SCHEMA:
        raise ValueError(f"runtime_payload.agent_build must use {PI_NATIVE_BUILD_SCHEMA}")
    validation = _dict(build.get("validation"))
    if validation.get("valid") is False:
        raise ValueError("runtime_payload.agent_build is not valid")
    files = _verified_build_files(build)
    project = _frozen_project(files)
    blueprint = _frozen_blueprint(files)
    prompt_spec = _dict(blueprint.get("prompt"))
    prompt_path = _normalized_relative_path(prompt_spec.get("path"))
    prompt_entry = files.get(prompt_path)
    if not prompt_path or prompt_entry is None or prompt_entry[0] != "prompt":
        raise ValueError("Agent Build Blueprint prompt does not reference its frozen prompt file")
    system_prompt = _utf8_source(prompt_path, prompt_entry[1])

    skills: list[dict[str, Any]] = []
    for item in blueprint.get("skills") if isinstance(blueprint.get("skills"), list) else []:
        resource = _dict(item)
        skill_id = str(resource.get("id") or "").strip()
        skill_path = _normalized_relative_path(resource.get("path"))
        entry = files.get(skill_path)
        if not skill_id or entry is None or entry[0] != f"skill:{skill_id}":
            raise ValueError(f"Agent Build Skill {skill_id or '<unknown>'!r} has no matching frozen file")
        content = _utf8_source(skill_path, entry[1])
        skills.append(
            {
                "name": _frontmatter_value(content, "name") or skill_id,
                "description": _frontmatter_value(content, "description") or f"Frozen Skill {skill_id}",
                "content": content,
                "path": skill_path,
            }
        )

    custom_tools: list[dict[str, Any]] = []
    declared_tool_ids: list[str] = []
    for item in blueprint.get("tools") if isinstance(blueprint.get("tools"), list) else []:
        tool = _dict(item)
        tool_id = str(tool.get("id") or "").strip()
        tool_path = _normalized_relative_path(tool.get("path"))
        entry = files.get(tool_path)
        if not tool_id or entry is None or entry[0] != f"tool:{tool_id}":
            raise ValueError(f"Agent Build Tool {tool_id or '<unknown>'!r} has no matching frozen file")
        declared_tool_ids.append(tool_id)
        custom_tools.append(
            {
                "name": tool_id,
                "path": tool_path,
                "sha256": entry[2],
                "size": len(entry[1]),
                "content_base64": base64.b64encode(entry[1]).decode("ascii"),
                "export_name": str(tool.get("export_name") or "default"),
            }
        )

    run_manifest = _dict(runtime_payload.get("agent_run_manifest"))
    if not run_manifest:
        raise ValueError("runtime_payload.agent_run_manifest is required for governed Pi-native execution")
    effective_tools, effective_workspace = _validated_manifest_authority(
        request,
        build,
        project,
        blueprint,
        run_manifest,
    )
    undeclared = sorted(set(effective_tools) - set(declared_tool_ids))
    if undeclared:
        raise ValueError(f"effective Tool IDs are absent from Agent Build: {', '.join(undeclared)}")

    build_digest = str(build.get("digest") or "")
    run_dir = os.path.abspath(runtime_dir) if runtime_dir else os.path.join(
        os.path.abspath(agent_dir),
        "runs",
        _safe_segment(request.task_id, "task"),
        _safe_segment(request_id, build_digest[:12]),
    )
    command: dict[str, Any] = {
        "id": request_id,
        "type": "run",
        "task_id": request.task_id,
        "prompt": request.prompt,
        "workspace_root": effective_workspace,
        "agent_dir": run_dir,
        "effective_tools": effective_tools,
        "model": _model_record(request, build),
        "build": {
            "schema_version": PI_NATIVE_BUILD_SCHEMA,
            "digest": build_digest,
            "system_prompt": system_prompt,
            "skills": skills,
            "prompt_templates": [],
            "builtin_tools": [],
            "custom_tools": custom_tools,
        },
    }
    if mock_mode:
        command["mock"] = copy.deepcopy(_dict(runtime_payload.get("pi_native_mock")))
    return command


def default_pi_native_sidecar_path() -> str:
    configured = str(os.environ.get("SHUHENG_PI_NATIVE_SIDECAR") or "").strip()
    if configured:
        return os.path.abspath(os.path.expanduser(configured))
    root = Path(__file__).resolve().parents[2]
    source_checkout = root / "integrations" / "pi-native-sidecar" / "sidecar.mjs"
    installed_data = Path(sys.prefix) / "share" / "shuheng" / "pi-native-sidecar" / "sidecar.mjs"
    for candidate in (source_checkout, installed_data):
        if candidate.is_file():
            return str(candidate)
    return str(source_checkout)


def resolve_pi_native_binary(binary: str | None = None) -> str:
    explicit = str(binary or os.environ.get("SHUHENG_PI_NATIVE_BIN") or "").strip()
    if explicit:
        return explicit
    return shutil.which("bun") or shutil.which("node") or "bun"


def pi_native_sidecar_command(
    *,
    binary: str | None = None,
    sidecar_path: str | None = None,
) -> list[str]:
    return [resolve_pi_native_binary(binary), os.path.abspath(sidecar_path or default_pi_native_sidecar_path())]


def _executable_exists(executable: str) -> bool:
    if os.path.sep in executable:
        return os.path.isfile(executable) and os.access(executable, os.X_OK)
    return shutil.which(executable) is not None


def _sdk_package_path(sidecar_path: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(sidecar_path)),
        "node_modules",
        "@earendil-works",
        "pi-coding-agent",
        "package.json",
    )


def pi_native_provider_spec(
    *,
    sidecar_path: str | None = None,
    binary: str | None = None,
    command: list[str] | None = None,
    mock_mode: bool = False,
) -> RuntimeProviderSpec:
    resolved_command = list(command or pi_native_sidecar_command(binary=binary, sidecar_path=sidecar_path))
    executable = resolved_command[0] if resolved_command else ""
    resolved_sidecar = resolved_command[1] if len(resolved_command) > 1 else ""
    if not executable or not _executable_exists(executable):
        status = "missing_binary"
    elif not resolved_sidecar or not os.path.isfile(resolved_sidecar):
        status = "missing_sidecar"
    elif not mock_mode and not os.path.isfile(_sdk_package_path(resolved_sidecar)):
        status = "missing_package"
    else:
        status = "available"
    return RuntimeProviderSpec(
        provider_id=PI_NATIVE_PROVIDER_ID,
        name="Pi Native Task Worker",
        runtime_type="local_pi_sdk_sidecar",
        status=status,
        transport="jsonl_stdio_sidecar",
        entrypoints=[resolved_sidecar] if resolved_sidecar else [],
        capabilities={
            "runtime_task_requests": True,
            "runtime_task_events": True,
            "streaming": True,
            "interrupt": True,
            "session_restore": False,
            "tool_calling": True,
            "custom_tools": True,
            "immutable_agent_build": True,
            "one_task_at_a_time": True,
            "deterministic_mock": True,
        },
        model_routing={
            "owner": "shuheng.control_plane",
            "supports_runtime_switch": False,
            "selection_contract": "explicit RuntimeTaskRequest.model provider/model selector",
        },
        scheduler={
            "owner": "shuheng.control_plane",
            "status": "provider_adapter_ready",
            "dispatch_contract": "runtime.task_request.v1",
            "runtime_provider_id": PI_NATIVE_PROVIDER_ID,
        },
        policy={
            "approval_gate_owner": "shuheng.policy",
            "tool_permissions": "frozen_build_and_effective_tool_intersection",
            "tool_os_sandbox": "not_available_trusted_local_code_only",
            "memory_write": "not_exposed",
            "implicit_resource_discovery": False,
        },
        a2a={
            "agent_card": "runtime://provider/pi-native",
            "task_transport": "jsonl_stdio_sidecar",
            "artifact_transport": "artifact_ref",
        },
        mcp={"tool_registry": "not_exposed", "resource_registry": "not_exposed"},
        notes=[
            "Optional task-worker Provider; it does not replace the permanent OMP main runtime.",
            f"Pinned SDK dependency: {PI_NATIVE_SDK_PACKAGE}@{PI_NATIVE_SDK_VERSION}.",
            "Executable Agent Build bytes are accepted only through RuntimeTaskRequest.runtime_payload.",
            "Prompt, Skill, Tool, Extension, context, Theme, and global home discovery are disabled.",
            "The sidecar process receives a minimal environment allowlist; model credentials stay transient.",
            "Every assignment uses a fresh sidecar process and temporary resource directory.",
            "Granted project-local Tools are trusted local code; OS-level syscall sandboxing is not yet available.",
        ],
    )


class PiNativeSidecarAgent:
    """Queue-compatible one-task wrapper around the Pi-native sidecar."""

    def __init__(
        self,
        *,
        command: list[str] | None = None,
        cwd: str | None = None,
        agent_dir: str | None = None,
        env: dict[str, str] | None = None,
        process_factory: ProcessFactory | None = None,
        thread_factory: ThreadFactory = threading.Thread,
        runtime_event_sink: RuntimeEventSink | None = None,
        mock_mode: bool = False,
        startup_timeout: float = 5.0,
        stop_timeout: float = 2.0,
    ) -> None:
        self.command = list(command or pi_native_sidecar_command())
        self.cwd = os.path.abspath(cwd or os.getcwd())
        self._owns_agent_dir = not agent_dir
        self.agent_dir = os.path.abspath(agent_dir or tempfile.mkdtemp(prefix="shuheng-pi-native-"))
        self.env = dict(env) if env is not None else None
        self.process_factory = process_factory or subprocess.Popen
        self.thread_factory = thread_factory
        self.runtime_event_sink = runtime_event_sink
        self.mock_mode = bool(mock_mode)
        self.startup_timeout = max(0.1, float(startup_timeout))
        self.stop_timeout = max(0.1, float(stop_timeout))
        self.task_queue = _TaskCounter()
        self.is_running = False
        self.history: list[str] = []
        self.log_path = ""
        self._process: Any = None
        self._process_lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._active_lock = threading.Lock()
        self._active: _ActiveTask | None = None
        self._ready = threading.Event()
        self._closed = False
        self._request_no = 0
        self._waiters: dict[str, queue.Queue] = {}
        self._waiters_lock = threading.Lock()
        self._stderr_tail: list[str] = []
        self._startup_error = ""

    def run(self) -> None:
        return None

    def load_llm_sessions(self) -> None:
        return None

    def get_llm_name(self, b: Any = None, model: bool = False) -> str:
        del b
        if model:
            with self._active_lock:
                return str(self._active.request.model or "pi-native") if self._active is not None else "pi-native"
        return "Pi Native"

    def put_task(self, prompt: str, source: str = "", images: Any = None) -> queue.Queue:
        del images
        request = RuntimeTaskRequest(
            task_id=self._next_request_id("task"),
            provider_id=PI_NATIVE_PROVIDER_ID,
            prompt=prompt,
            source=source,
        )
        return self.put_runtime_task(request)

    def put_runtime_task(self, request: RuntimeTaskRequest) -> queue.Queue:
        display_queue: queue.Queue = queue.Queue()
        with self._active_lock:
            if self._active is not None and not self._active.finished:
                display_queue.put(
                    {
                        "done": "[Pi Native] 当前 sidecar 仍在运行一个任务，不能并发启动新任务。",
                        "source": request.source,
                        "status": "failed",
                        "error": "Pi-native sidecar already has an active task",
                    }
                )
                return display_queue
            request_id = self._next_request_id("run")
            self._active = _ActiveTask(
                request_id=request_id,
                request=request,
                display_queue=display_queue,
                source=request.source,
            )
            self.is_running = True
            self.task_queue.start()
        self._emit_runtime_event(
            "runtime_task_requested",
            status="starting",
            request=request,
            payload={"request_id": request_id},
        )

        def submit() -> None:
            try:
                runtime_dir = tempfile.mkdtemp(prefix="shuheng-pi-run-")
                try:
                    os.chmod(runtime_dir, 0o700)
                except Exception:
                    shutil.rmtree(runtime_dir, ignore_errors=True)
                    raise
                with self._active_lock:
                    active = self._active
                    if active is None or active.request_id != request_id or active.abort_requested:
                        shutil.rmtree(runtime_dir, ignore_errors=True)
                        runtime_dir = ""
                    else:
                        active.runtime_dir = runtime_dir
                if not runtime_dir:
                    self._finish_active(
                        request.task_id,
                        event_type="runtime_task_aborted",
                        status="aborted",
                        message="[Pi Native] 已请求中止。",
                    )
                    return
                command = pi_native_run_command(
                    request,
                    agent_dir=self.agent_dir,
                    workspace_root=self.cwd,
                    request_id=request_id,
                    mock_mode=self.mock_mode,
                    runtime_dir=runtime_dir,
                )
                # A task never reuses a process that served health/describe or
                # an earlier Build. This keeps module globals and SDK state
                # inside one frozen run boundary.
                self._stop_current_process()
                self._ensure_process()
                with self._active_lock:
                    active = self._active
                    aborted = active is None or active.request_id != request_id or active.abort_requested
                    if not aborted:
                        # Keep the active lock through the write so abort()
                        # cannot overtake the run frame during startup.
                        self._send(command)
                if aborted:
                    self._finish_active(
                        request.task_id,
                        event_type="runtime_task_aborted",
                        status="aborted",
                        message="[Pi Native] 已请求中止。",
                    )
                    return
            except Exception as exc:
                message = f"[Pi Native] 启动失败: {type(exc).__name__}: {exc}"
                self._finish_active(
                    request.task_id,
                    event_type="runtime_task_failed",
                    status="failed",
                    message=message,
                    error=message,
                )

        self.thread_factory(target=submit, daemon=True, name="pi-native-submit").start()
        return display_queue

    def describe(self, timeout: float = 3.0) -> dict[str, Any]:
        return self._control_request("describe", timeout=timeout)

    def health(self, timeout: float = 3.0) -> dict[str, Any]:
        return self._control_request("health", timeout=timeout)

    def abort(self) -> None:
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            active.abort_requested = True
            task_id = active.request.task_id
        try:
            if self._process_ready():
                self._send({"id": self._next_request_id("abort"), "type": "abort", "task_id": task_id})
        except Exception:
            self._finish_active(
                task_id,
                event_type="runtime_task_aborted",
                status="aborted",
                message="[Pi Native] 已请求中止。",
            )

    def close(self) -> None:
        self._closed = True
        self.abort()
        self._stop_current_process()
        with self._active_lock:
            active = self._active
            task_id = active.request.task_id if active is not None else ""
        if task_id:
            self._finish_active(
                task_id,
                event_type="runtime_task_aborted",
                status="aborted",
                message="[Pi Native] sidecar 已关闭。",
            )
        if self._owns_agent_dir:
            shutil.rmtree(self.agent_dir, ignore_errors=True)

    def _control_request(self, command: str, *, timeout: float) -> dict[str, Any]:
        request_id = self._next_request_id(command)
        waiter: queue.Queue = queue.Queue(maxsize=1)
        try:
            self._ensure_process()
            with self._waiters_lock:
                self._waiters[request_id] = waiter
            self._send({"id": request_id, "type": command})
            frame = waiter.get(timeout=max(0.1, float(timeout)))
            data = _dict(frame.get("data"))
            return {
                "schema_version": PI_NATIVE_EVENT_SCHEMA,
                "status": "ok" if frame.get("success") else "error",
                "command": command,
                "data": data,
                "error": str(frame.get("error") or ""),
            }
        except Exception as exc:
            return {
                "schema_version": PI_NATIVE_EVENT_SCHEMA,
                "status": "error",
                "command": command,
                "data": {},
                "error": f"{type(exc).__name__}: {exc}",
            }
        finally:
            with self._waiters_lock:
                self._waiters.pop(request_id, None)
            with self._active_lock:
                has_active_task = self._active is not None and not self._active.finished
            if not has_active_task:
                self._stop_current_process()

    def _next_request_id(self, prefix: str) -> str:
        with self._send_lock:
            self._request_no += 1
            return f"shuheng-pi-{prefix}-{self._request_no}"

    def _process_ready(self) -> bool:
        process = self._process
        return bool(process is not None and process.poll() is None and self._ready.is_set())

    def _stop_current_process(self) -> None:
        with self._process_lock:
            process = self._process
            self._process = None
            self._ready.clear()
        if process is not None:
            self._terminate_process(process)

    def _ensure_process(self) -> None:
        if self._closed:
            raise RuntimeError("Pi-native sidecar is closed")
        with self._process_lock:
            if self._process_ready():
                return
            executable = self.command[0] if self.command else ""
            if not executable or not _executable_exists(executable):
                raise FileNotFoundError(f"Pi-native runtime executable not found: {executable or '<empty>'}")
            if len(self.command) < 2 or not os.path.isfile(self.command[1]):
                raise FileNotFoundError("Pi-native sidecar entrypoint not found")
            os.makedirs(self.agent_dir, mode=0o700, exist_ok=True)
            isolated_home = os.path.join(self.agent_dir, "home")
            os.makedirs(isolated_home, mode=0o700, exist_ok=True)
            process_env = pi_native_subprocess_env(self.env)
            process_env["HOME"] = isolated_home
            process_env["USERPROFILE"] = isolated_home
            if self.mock_mode:
                process_env["SHUHENG_PI_NATIVE_MOCK"] = "1"
            else:
                process_env.pop("SHUHENG_PI_NATIVE_MOCK", None)
            self._ready.clear()
            self._startup_error = ""
            self._stderr_tail.clear()
            try:
                process = self.process_factory(
                    self.command,
                    cwd=self.cwd,
                    env=process_env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
            except Exception:
                self._ready.set()
                raise
            self._process = process
            self.thread_factory(
                target=self._read_stdout,
                args=(process,),
                daemon=True,
                name="pi-native-stdout",
            ).start()
            self.thread_factory(
                target=self._read_stderr,
                args=(process,),
                daemon=True,
                name="pi-native-stderr",
            ).start()
        if not self._ready.wait(self.startup_timeout):
            self._terminate_process(process)
            raise RuntimeError("Pi-native sidecar ready timeout")
        if self._startup_error:
            raise RuntimeError(self._startup_error)
        if process.poll() is not None:
            raise RuntimeError("Pi-native sidecar exited during startup")

    def _read_stdout(self, process: Any) -> None:
        stdout = getattr(process, "stdout", None)
        try:
            if stdout is None:
                self._startup_error = "Pi-native sidecar stdout is unavailable"
                return
            for raw_line in stdout:
                if process is not self._process:
                    break
                line = str(raw_line or "").strip()
                if not line:
                    continue
                try:
                    frame = json.loads(line)
                except json.JSONDecodeError:
                    self._remember_stderr(f"non-JSON sidecar output: {line[:500]}")
                    continue
                if not isinstance(frame, dict):
                    continue
                self._handle_frame(frame)
        except Exception as exc:
            if process is self._process:
                self._remember_stderr(f"sidecar stdout reader failed: {type(exc).__name__}: {exc}")
        finally:
            if process is self._process and not self._ready.is_set():
                tail = "; ".join(self._stderr_tail[-3:])
                self._startup_error = tail or "Pi-native sidecar exited before ready"
                self._ready.set()
            if process is self._process and not self._closed:
                with self._active_lock:
                    active = self._active
                    task_id = active.request.task_id if active is not None else ""
                if task_id:
                    tail = "; ".join(self._stderr_tail[-3:])
                    message = f"[Pi Native] sidecar 意外退出{': ' + tail if tail else '。'}"
                    self._finish_active(
                        task_id,
                        event_type="runtime_task_failed",
                        status="failed",
                        message=message,
                        error=message,
                    )

    def _read_stderr(self, process: Any) -> None:
        stderr = getattr(process, "stderr", None)
        if stderr is None:
            return
        try:
            for raw_line in stderr:
                if process is not self._process:
                    break
                line = str(raw_line or "").strip()
                if line:
                    self._remember_stderr(line)
        except Exception:
            return

    def _handle_frame(self, frame: dict[str, Any]) -> None:
        frame_type = str(frame.get("type") or "")
        if frame_type == "sidecar_ready":
            self._ready.set()
            return
        if frame_type == "response":
            request_id = str(frame.get("id") or "")
            with self._waiters_lock:
                waiter = self._waiters.get(request_id)
            if waiter is not None:
                waiter.put(frame)
            return
        self._handle_task_frame(frame_type, frame)

    def _handle_task_frame(self, frame_type: str, frame: dict[str, Any]) -> None:
        task_id = str(frame.get("task_id") or "")
        with self._active_lock:
            active = self._active
            if active is None or active.finished or active.request.task_id != task_id:
                return
            request = active.request
            if frame_type == "text_delta":
                delta = str(frame.get("delta") or "")
                active.buffer += delta
                # Match the queue contract consumed by the existing Shuheng TUI.
                active.display_queue.put({"next": delta, "source": active.source})
            else:
                delta = ""
        payload = _dict(frame.get("payload"))
        if frame_type == "task_started":
            self._emit_runtime_event(
                "runtime_task_started",
                status="working",
                request=request,
                payload=payload,
            )
        elif frame_type == "text_delta":
            self._emit_runtime_event(
                "runtime_task_delta",
                status="streaming",
                request=request,
                delta=delta,
                payload=payload,
            )
        elif frame_type in {"tool_started", "tool_updated", "tool_finished"}:
            suffix = {"tool_started": "started", "tool_updated": "updated", "tool_finished": "completed"}[frame_type]
            status = str(frame.get("status") or ("running" if frame_type != "tool_finished" else "completed"))
            error = str(frame.get("error") or "")
            if frame_type == "tool_finished" and (status == "failed" or error):
                suffix = "failed"
            tool_call_id = str(frame.get("tool_call_id") or "")
            self._emit_runtime_event(
                f"runtime_tool_{suffix}",
                status=status,
                request=request,
                error=error,
                tool_call_refs=[tool_call_id] if tool_call_id else [],
                payload={"tool_name": str(frame.get("tool_name") or ""), **payload},
            )
        elif frame_type == "task_completed":
            message = str(frame.get("message") or "")
            self._finish_active(
                task_id,
                event_type="runtime_task_completed",
                status="completed",
                message=message,
                payload=payload,
            )
        elif frame_type == "task_failed":
            error = str(frame.get("error") or "Pi-native task failed")
            self._finish_active(
                task_id,
                event_type="runtime_task_failed",
                status="failed",
                message=f"[Pi Native] 运行失败: {error}",
                error=error,
                payload=payload,
            )
        elif frame_type == "task_aborted":
            message = str(frame.get("message") or "[Pi Native] 已请求中止。")
            self._finish_active(
                task_id,
                event_type="runtime_task_aborted",
                status="aborted",
                message=message,
                payload=payload,
            )

    def _finish_active(
        self,
        task_id: str,
        *,
        event_type: str,
        status: str,
        message: str,
        error: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self._active_lock:
            active = self._active
            if active is None or active.finished or active.request.task_id != task_id:
                return
            active.finished = True
            request = active.request
            final_message = message or active.buffer
            runtime_dir = active.runtime_dir
            display_queue = active.display_queue
            source = active.source
            self.history.append(final_message)
            self._active = None
            self.is_running = False
            self.task_queue.done()
        if runtime_dir:
            shutil.rmtree(runtime_dir, ignore_errors=True)
        self._emit_runtime_event(
            event_type,
            status=status,
            request=request,
            message=final_message[:1200],
            error=error,
            payload=payload,
        )
        self._stop_current_process()
        display_queue.put(
            {
                "done": final_message,
                "source": source,
                "status": status,
                "error": error,
            }
        )

    def _emit_runtime_event(
        self,
        event_type: str,
        *,
        status: str,
        request: RuntimeTaskRequest,
        message: str = "",
        delta: str = "",
        error: str = "",
        artifact_refs: list[str] | None = None,
        tool_call_refs: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self.runtime_event_sink is None:
            return
        try:
            self.runtime_event_sink(
                RuntimeTaskEvent(
                    task_id=request.task_id,
                    provider_id=PI_NATIVE_PROVIDER_ID,
                    event_type=event_type,
                    status=status,
                    agent_id=request.agent_id,
                    source=request.source or PI_NATIVE_PROVIDER_ID,
                    message=message,
                    delta=delta,
                    error=error,
                    artifact_refs=list(artifact_refs or request.artifact_refs),
                    tool_call_refs=list(tool_call_refs or []),
                    request=request,
                    payload=dict(payload or {}),
                )
            )
        except Exception as exc:
            self._remember_stderr(f"runtime event sink failed: {type(exc).__name__}: {exc}")

    def _send(self, frame: dict[str, Any]) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            raise RuntimeError("Pi-native sidecar is not running")
        stdin = getattr(process, "stdin", None)
        if stdin is None:
            raise RuntimeError("Pi-native sidecar stdin is unavailable")
        line = json.dumps(frame, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._send_lock:
            stdin.write(line)
            stdin.flush()

    def _remember_stderr(self, line: str) -> None:
        self._stderr_tail.append(str(line or ""))
        if len(self._stderr_tail) > 20:
            del self._stderr_tail[:-20]

    def _terminate_process(self, process: Any) -> None:
        try:
            if process.poll() is not None:
                return
            process.terminate()
            process.wait(timeout=self.stop_timeout)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


class PiNativeRuntimeAdapter(RuntimeAdapter):
    def __init__(
        self,
        spec: RuntimeProviderSpec,
        *,
        command: list[str] | None = None,
        cwd: str | None = None,
        agent_dir: str | None = None,
        env: dict[str, str] | None = None,
        process_factory: ProcessFactory | None = None,
        thread_factory: ThreadFactory = threading.Thread,
        runtime_event_sink: RuntimeEventSink | None = None,
        mock_mode: bool = False,
    ) -> None:
        super().__init__(spec)
        self.command = list(command) if command is not None else None
        self.cwd = cwd
        self.agent_dir = agent_dir
        self.env = dict(env) if env is not None else None
        self.process_factory = process_factory
        self.thread_factory = thread_factory
        self.runtime_event_sink = runtime_event_sink
        self.mock_mode = bool(mock_mode)

    def create_agent(self) -> PiNativeSidecarAgent:
        return PiNativeSidecarAgent(
            command=self.command,
            cwd=self.cwd,
            agent_dir=self.agent_dir,
            env=self.env,
            process_factory=self.process_factory,
            thread_factory=self.thread_factory,
            runtime_event_sink=self.runtime_event_sink,
            mock_mode=self.mock_mode,
        )

    def start_agent(self, agent: Any, *, thread_name: str = "") -> Any:
        setattr(agent, "_shuheng_thread_name", thread_name or "shuheng-pi-native")
        return None


__all__ = [
    "PI_NATIVE_BUILD_SCHEMA",
    "PI_NATIVE_EVENT_SCHEMA",
    "PI_NATIVE_PROVIDER_ID",
    "PI_NATIVE_PROTOCOL_VERSION",
    "PI_NATIVE_SDK_PACKAGE",
    "PI_NATIVE_SDK_VERSION",
    "PiNativeRuntimeAdapter",
    "PiNativeSidecarAgent",
    "RuntimeEventSink",
    "default_pi_native_sidecar_path",
    "pi_native_provider_spec",
    "pi_native_run_command",
    "pi_native_sidecar_command",
    "pi_native_subprocess_env",
    "resolve_pi_native_binary",
]
