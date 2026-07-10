"""Pure contracts and content-addressed compilation for local Agent Projects.

The module intentionally has no dependency on the TUI or runtime adapters.  An
Agent Project is user-authored source; an :class:`AgentBuild` is a frozen,
JSON-safe snapshot that a provider can consume without reopening mutable source
files.  Runtime grants are supplied separately when a run manifest is created.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar, Generic, Iterable, TypeVar


PROJECT_SCHEMA_VERSION = "shuheng.agent_project.v1"
BLUEPRINT_SCHEMA_VERSION = "shuheng.agent_blueprint.v1"
BUILD_SCHEMA_VERSION = "shuheng.agent_build.v1"
RUN_MANIFEST_SCHEMA_VERSION = "shuheng.agent_run_manifest.v1"
PROJECT_MANIFEST_NAME = "agent-project.json"

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
_HEX_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")

T = TypeVar("T")


@dataclass(frozen=True)
class AgentProjectDiagnostic:
    """A stable, UI-friendly diagnostic produced at a user-controlled boundary."""

    code: str
    message: str
    severity: str = "error"
    path: str = ""
    field: str = ""
    line: int = 0
    column: int = 0

    def to_record(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "path": self.path,
            "field": self.field,
            "line": self.line,
            "column": self.column,
        }


@dataclass(frozen=True)
class AgentProjectResult(Generic[T]):
    """Result envelope used by all public user-boundary helpers."""

    value: T | None = None
    diagnostics: tuple[AgentProjectDiagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return self.value is not None and not any(item.severity == "error" for item in self.diagnostics)

    @property
    def build(self) -> T | None:
        """Convenience alias used by compile call sites."""

        return self.value

    def to_record(self) -> dict[str, Any]:
        value = self.value
        if value is None:
            encoded: Any = None
        elif hasattr(value, "to_record"):
            encoded = value.to_record()  # type: ignore[union-attr]
        else:
            encoded = value
        return {
            "ok": self.ok,
            "value": encoded,
            "diagnostics": [item.to_record() for item in self.diagnostics],
        }


@dataclass(frozen=True)
class AgentResource:
    resource_id: str
    path: str

    def to_record(self) -> dict[str, Any]:
        return {"id": self.resource_id, "path": self.path}


@dataclass(frozen=True)
class AgentTool:
    tool_id: str
    path: str
    requested_capabilities: tuple[str, ...] = ()

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.tool_id,
            "path": self.path,
            "requested_capabilities": list(self.requested_capabilities),
        }


@dataclass(frozen=True)
class AgentProject:
    schema_version: ClassVar[str] = PROJECT_SCHEMA_VERSION

    project_id: str
    name: str
    description: str
    source_root: str
    manifest_path: str
    blueprint_path: str
    default_runtime: str
    runtime_version: str
    tests: tuple[AgentResource, ...] = ()

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.project_id,
            "name": self.name,
            "description": self.description,
            "source_root": self.source_root,
            "manifest_path": self.manifest_path,
            "entry_blueprint": self.blueprint_path,
            "default_runtime": self.default_runtime,
            "runtime_version": self.runtime_version,
            "tests": [item.to_record() for item in self.tests],
        }


@dataclass(frozen=True)
class AgentBlueprint:
    schema_version: ClassVar[str] = BLUEPRINT_SCHEMA_VERSION

    blueprint_id: str
    name: str
    description: str
    runtime: str
    runtime_version: str
    prompt_path: str
    skills: tuple[AgentResource, ...]
    tools: tuple[AgentTool, ...]
    requested_capabilities: tuple[str, ...]
    delegation_json: str
    budget_json: str
    output_contract_json: str

    @property
    def delegation(self) -> dict[str, Any]:
        return json.loads(self.delegation_json)

    @property
    def budget(self) -> dict[str, Any]:
        return json.loads(self.budget_json)

    @property
    def output_contract(self) -> dict[str, Any]:
        return json.loads(self.output_contract_json)

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.blueprint_id,
            "name": self.name,
            "description": self.description,
            "runtime": self.runtime,
            "runtime_version": self.runtime_version,
            "prompt": {"path": self.prompt_path},
            "skills": [item.to_record() for item in self.skills],
            "tools": [item.to_record() for item in self.tools],
            "requested_capabilities": list(self.requested_capabilities),
            "delegation": self.delegation,
            "budget": self.budget,
            "output_contract": self.output_contract,
        }


@dataclass(frozen=True)
class AgentBuildFile:
    """One immutable source blob captured by the compiler."""

    path: str
    role: str
    sha256: str
    size: int
    content_base64: str

    def content_bytes(self) -> bytes:
        return base64.b64decode(self.content_base64.encode("ascii"), validate=True)

    def to_record(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "role": self.role,
            "sha256": self.sha256,
            "size": self.size,
            "content_base64": self.content_base64,
        }


@dataclass(frozen=True)
class AgentBuild:
    """Content-addressed, provider-consumable snapshot of an Agent Project."""

    schema_version: ClassVar[str] = BUILD_SCHEMA_VERSION

    digest: str
    project: AgentProject
    blueprint: AgentBlueprint
    runtime: str
    runtime_version: str
    files: tuple[AgentBuildFile, ...]
    diagnostics: tuple[AgentProjectDiagnostic, ...] = ()

    def file(self, relative_path: str) -> AgentBuildFile | None:
        return next((item for item in self.files if item.path == relative_path), None)

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "digest": self.digest,
            "project": self.project.to_record(),
            "blueprint": self.blueprint.to_record(),
            "runtime": {"provider": self.runtime, "version": self.runtime_version},
            "files": [item.to_record() for item in self.files],
            "validation": {
                "valid": not any(item.severity == "error" for item in self.diagnostics),
                "diagnostics": [item.to_record() for item in self.diagnostics],
            },
        }


@dataclass(frozen=True)
class AgentRunManifest:
    """Frozen runtime authority derived from a Build plus control-plane grants."""

    schema_version: ClassVar[str] = RUN_MANIFEST_SCHEMA_VERSION

    assignment_id: str
    build_digest: str
    project_id: str
    blueprint_id: str
    provider_id: str
    provider_revision: str
    workspace: str
    requested_capabilities: tuple[str, ...]
    granted_capabilities: tuple[str, ...]
    effective_capabilities: tuple[str, ...]
    requested_tool_ids: tuple[str, ...]
    granted_tool_ids: tuple[str, ...]
    effective_tool_ids: tuple[str, ...]
    budget_json: str
    output_contract_json: str
    causation_refs: tuple[str, ...] = ()

    @property
    def budget(self) -> dict[str, Any]:
        return json.loads(self.budget_json)

    @property
    def output_contract(self) -> dict[str, Any]:
        return json.loads(self.output_contract_json)

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "assignment_id": self.assignment_id,
            "build_digest": self.build_digest,
            "project_id": self.project_id,
            "blueprint_id": self.blueprint_id,
            "provider": {"id": self.provider_id, "revision": self.provider_revision},
            "workspace": self.workspace,
            "capabilities": {
                "requested": list(self.requested_capabilities),
                "granted": list(self.granted_capabilities),
                "effective": list(self.effective_capabilities),
            },
            "tools": {
                "requested": list(self.requested_tool_ids),
                "granted": list(self.granted_tool_ids),
                "effective": list(self.effective_tool_ids),
            },
            "budget": self.budget,
            "output_contract": self.output_contract,
            "causation_refs": list(self.causation_refs),
        }


class _DuplicateJsonKey(ValueError):
    pass


class _NonFiniteJsonNumber(ValueError):
    pass


def safe_agent_id(value: Any) -> str:
    text = str(value or "").strip()
    return text if _SAFE_ID_RE.fullmatch(text) else ""


def _diagnostic(
    code: str,
    message: str,
    *,
    path: str = "",
    field: str = "",
    severity: str = "error",
    line: int = 0,
    column: int = 0,
) -> AgentProjectDiagnostic:
    return AgentProjectDiagnostic(
        code=code,
        message=message,
        severity=severity,
        path=path,
        field=field,
        line=line,
        column=column,
    )


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> Any:
    raise _NonFiniteJsonNumber(f"non-finite JSON number is not allowed: {value}")


def _load_json(
    path: Path,
    display_path: str,
    diagnostics: list[AgentProjectDiagnostic],
) -> tuple[dict[str, Any] | None, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        diagnostics.append(_diagnostic("file_read_failed", str(exc), path=display_path))
        return None, b""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        diagnostics.append(
            _diagnostic(
                "invalid_utf8",
                "JSON files must be UTF-8 encoded.",
                path=display_path,
                line=exc.start + 1,
            )
        )
        return None, raw
    try:
        value = json.loads(
            text,
            object_pairs_hook=_json_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        diagnostics.append(
            _diagnostic(
                "malformed_json",
                exc.msg,
                path=display_path,
                line=exc.lineno,
                column=exc.colno,
            )
        )
        return None, raw
    except (_DuplicateJsonKey, _NonFiniteJsonNumber) as exc:
        diagnostics.append(_diagnostic("invalid_json", str(exc), path=display_path))
        return None, raw
    if not isinstance(value, dict):
        diagnostics.append(_diagnostic("invalid_object", "The JSON document must be an object.", path=display_path))
        return None, raw
    return value, raw


def _unknown_fields(
    value: dict[str, Any],
    allowed: set[str],
    diagnostics: list[AgentProjectDiagnostic],
    *,
    path: str,
    field: str = "",
) -> None:
    for key in sorted(set(value) - allowed):
        pointer = f"{field}/{key}" if field else f"/{key}"
        diagnostics.append(
            _diagnostic("unknown_field", f"Unknown field {pointer!r} for this schema version.", path=path, field=pointer)
        )


def _required_string(
    value: Any,
    diagnostics: list[AgentProjectDiagnostic],
    *,
    path: str,
    field: str,
    max_length: int = 200,
) -> str:
    if not isinstance(value, str) or not value.strip():
        diagnostics.append(_diagnostic("required_string", "A non-empty string is required.", path=path, field=field))
        return ""
    if value != value.strip():
        diagnostics.append(
            _diagnostic("surrounding_whitespace", "Leading or trailing whitespace is not allowed.", path=path, field=field)
        )
        return ""
    if len(value) > max_length or _CONTROL_CHAR_RE.search(value):
        diagnostics.append(_diagnostic("invalid_string", "The string is too long or contains control characters.", path=path, field=field))
        return ""
    return value


def _optional_string(
    value: Any,
    diagnostics: list[AgentProjectDiagnostic],
    *,
    path: str,
    field: str,
    max_length: int = 2000,
) -> str:
    if value is None or value == "":
        return ""
    return _required_string(value, diagnostics, path=path, field=field, max_length=max_length)


def _id_value(value: Any, diagnostics: list[AgentProjectDiagnostic], *, path: str, field: str) -> str:
    text = _required_string(value, diagnostics, path=path, field=field, max_length=80)
    if text and not safe_agent_id(text):
        diagnostics.append(
            _diagnostic(
                "unsafe_id",
                "IDs must start with an ASCII letter or digit and contain only letters, digits, '.', '_' or '-'.",
                path=path,
                field=field,
            )
        )
        return ""
    return text


def _string_map_json(
    value: Any,
    diagnostics: list[AgentProjectDiagnostic],
    *,
    path: str,
    field: str,
) -> str:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        diagnostics.append(_diagnostic("invalid_object", "An object is required.", path=path, field=field))
        value = {}
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        diagnostics.append(_diagnostic("not_json_safe", str(exc), path=path, field=field))
        return "{}"


def _path_text(value: Any, diagnostics: list[AgentProjectDiagnostic], *, path: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        diagnostics.append(_diagnostic("required_path", "An explicit relative file path is required.", path=path, field=field))
        return ""
    if value != value.strip() or value.startswith("~"):
        diagnostics.append(
            _diagnostic("unsafe_path", "Paths cannot use '~' or surrounding whitespace.", path=path, field=field)
        )
        return ""
    if "\\" in value or "\x00" in value or value.startswith("/") or _WINDOWS_DRIVE_RE.match(value):
        diagnostics.append(
            _diagnostic("unsafe_path", "Only normalized POSIX paths relative to the project root are allowed.", path=path, field=field)
        )
        return ""
    if value.endswith("/") or "//" in value:
        diagnostics.append(_diagnostic("unsafe_path", "The file path must be normalized.", path=path, field=field))
        return ""
    pure = PurePosixPath(value)
    if not pure.parts or any(part in {"", ".", ".."} for part in pure.parts) or pure.as_posix() != value:
        diagnostics.append(
            _diagnostic("unsafe_path", "Path traversal and non-normalized paths are not allowed.", path=path, field=field)
        )
        return ""
    return value


def _is_within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((str(path), str(root))) == str(root)
    except ValueError:
        return False


def _resolve_file(
    root: Path,
    relative_path: str,
    diagnostics: list[AgentProjectDiagnostic],
    *,
    manifest_path: str,
    field: str,
) -> Path | None:
    if not relative_path:
        return None
    candidate = root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        diagnostics.append(
            _diagnostic("missing_file", f"Referenced file cannot be resolved: {exc}", path=manifest_path, field=field)
        )
        return None
    if not _is_within(resolved, root):
        diagnostics.append(
            _diagnostic(
                "path_escape",
                "The referenced file resolves outside the Agent Project root.",
                path=manifest_path,
                field=field,
            )
        )
        return None
    try:
        mode = resolved.stat().st_mode
    except OSError as exc:
        diagnostics.append(_diagnostic("file_stat_failed", str(exc), path=manifest_path, field=field))
        return None
    if not stat.S_ISREG(mode):
        diagnostics.append(_diagnostic("not_a_file", "The declared path must resolve to a regular file.", path=manifest_path, field=field))
        return None
    return resolved


def _string_list(
    value: Any,
    diagnostics: list[AgentProjectDiagnostic],
    *,
    path: str,
    field: str,
    safe_ids: bool = False,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        diagnostics.append(_diagnostic("invalid_array", "An array is required.", path=path, field=field))
        return ()
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        item_field = f"{field}/{index}"
        text = _required_string(item, diagnostics, path=path, field=item_field, max_length=80 if safe_ids else 500)
        if not text:
            continue
        if safe_ids and not safe_agent_id(text):
            diagnostics.append(_diagnostic("unsafe_id", "A safe capability or resource ID is required.", path=path, field=item_field))
            continue
        if text in seen:
            diagnostics.append(_diagnostic("duplicate_value", f"Duplicate value {text!r}.", path=path, field=item_field))
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)


def _resource_list(
    value: Any,
    diagnostics: list[AgentProjectDiagnostic],
    *,
    manifest_path: str,
    field: str,
) -> tuple[AgentResource, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        diagnostics.append(_diagnostic("invalid_array", "An array is required.", path=manifest_path, field=field))
        return ()
    result: list[AgentResource] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for index, item in enumerate(value):
        pointer = f"{field}/{index}"
        if not isinstance(item, dict):
            diagnostics.append(_diagnostic("invalid_object", "A resource object is required.", path=manifest_path, field=pointer))
            continue
        _unknown_fields(item, {"id", "path"}, diagnostics, path=manifest_path, field=pointer)
        resource_id = _id_value(item.get("id"), diagnostics, path=manifest_path, field=f"{pointer}/id")
        resource_path = _path_text(item.get("path"), diagnostics, path=manifest_path, field=f"{pointer}/path")
        if resource_id in ids:
            diagnostics.append(_diagnostic("duplicate_resource_id", f"Duplicate resource ID {resource_id!r}.", path=manifest_path, field=f"{pointer}/id"))
            resource_id = ""
        if resource_path in paths:
            diagnostics.append(_diagnostic("duplicate_resource_path", f"Duplicate resource path {resource_path!r}.", path=manifest_path, field=f"{pointer}/path"))
            resource_path = ""
        if resource_id:
            ids.add(resource_id)
        if resource_path:
            paths.add(resource_path)
        if resource_id and resource_path:
            result.append(AgentResource(resource_id=resource_id, path=resource_path))
    return tuple(result)


def _tool_list(
    value: Any,
    diagnostics: list[AgentProjectDiagnostic],
    *,
    manifest_path: str,
) -> tuple[AgentTool, ...]:
    field = "/tools"
    if value is None:
        return ()
    if not isinstance(value, list):
        diagnostics.append(_diagnostic("invalid_array", "An array is required.", path=manifest_path, field=field))
        return ()
    result: list[AgentTool] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for index, item in enumerate(value):
        pointer = f"{field}/{index}"
        if not isinstance(item, dict):
            diagnostics.append(_diagnostic("invalid_object", "A Tool object is required.", path=manifest_path, field=pointer))
            continue
        _unknown_fields(item, {"id", "path", "requested_capabilities"}, diagnostics, path=manifest_path, field=pointer)
        tool_id = _id_value(item.get("id"), diagnostics, path=manifest_path, field=f"{pointer}/id")
        tool_path = _path_text(item.get("path"), diagnostics, path=manifest_path, field=f"{pointer}/path")
        capabilities = _string_list(
            item.get("requested_capabilities"),
            diagnostics,
            path=manifest_path,
            field=f"{pointer}/requested_capabilities",
            safe_ids=True,
        )
        if tool_id in ids:
            diagnostics.append(_diagnostic("duplicate_tool_id", f"Duplicate Tool ID {tool_id!r}.", path=manifest_path, field=f"{pointer}/id"))
            tool_id = ""
        if tool_path in paths:
            diagnostics.append(_diagnostic("duplicate_tool_path", f"Duplicate Tool path {tool_path!r}.", path=manifest_path, field=f"{pointer}/path"))
            tool_path = ""
        if tool_id:
            ids.add(tool_id)
        if tool_path:
            paths.add(tool_path)
        if tool_id and tool_path:
            result.append(AgentTool(tool_id=tool_id, path=tool_path, requested_capabilities=capabilities))
    return tuple(result)


def _read_source_file(
    path: Path,
    relative_path: str,
    diagnostics: list[AgentProjectDiagnostic],
) -> bytes | None:
    try:
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
    except OSError as exc:
        diagnostics.append(_diagnostic("file_read_failed", str(exc), path=relative_path))
        return None
    before_key = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_key = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_key != after_key or len(raw) != after.st_size:
        diagnostics.append(
            _diagnostic(
                "source_changed_during_build",
                "The source file changed while the build snapshot was being captured; retry the build.",
                path=relative_path,
            )
        )
        return None
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        diagnostics.append(
            _diagnostic("invalid_utf8", "Agent Project source files must be UTF-8 encoded.", path=relative_path)
        )
        return None
    return raw


def _parse_project(
    root: Path,
    data: dict[str, Any],
    diagnostics: list[AgentProjectDiagnostic],
) -> AgentProject | None:
    manifest_path = PROJECT_MANIFEST_NAME
    _unknown_fields(
        data,
        {
            "schema_version",
            "id",
            "name",
            "description",
            "entry_blueprint",
            "default_runtime",
            "runtime_version",
            "tests",
        },
        diagnostics,
        path=manifest_path,
    )
    if data.get("schema_version") != PROJECT_SCHEMA_VERSION:
        diagnostics.append(
            _diagnostic(
                "unsupported_schema",
                f"schema_version must be {PROJECT_SCHEMA_VERSION!r}.",
                path=manifest_path,
                field="/schema_version",
            )
        )
    project_id = _id_value(data.get("id"), diagnostics, path=manifest_path, field="/id")
    name = _required_string(data.get("name"), diagnostics, path=manifest_path, field="/name")
    description = _optional_string(data.get("description"), diagnostics, path=manifest_path, field="/description")
    blueprint_path = _path_text(
        data.get("entry_blueprint"), diagnostics, path=manifest_path, field="/entry_blueprint"
    )
    default_runtime = _id_value(
        data.get("default_runtime"), diagnostics, path=manifest_path, field="/default_runtime"
    )
    runtime_version = _optional_string(
        data.get("runtime_version"), diagnostics, path=manifest_path, field="/runtime_version", max_length=200
    )
    tests = _resource_list(data.get("tests"), diagnostics, manifest_path=manifest_path, field="/tests")
    if blueprint_path == PROJECT_MANIFEST_NAME:
        diagnostics.append(
            _diagnostic(
                "blueprint_is_project_manifest",
                "The entry Blueprint must be a separate JSON file.",
                path=manifest_path,
                field="/entry_blueprint",
            )
        )
    if not all((project_id, name, blueprint_path, default_runtime)):
        return None
    return AgentProject(
        project_id=project_id,
        name=name,
        description=description,
        source_root=str(root),
        manifest_path=manifest_path,
        blueprint_path=blueprint_path,
        default_runtime=default_runtime,
        runtime_version=runtime_version,
        tests=tests,
    )


def _parse_blueprint(
    project: AgentProject,
    data: dict[str, Any],
    diagnostics: list[AgentProjectDiagnostic],
) -> AgentBlueprint | None:
    manifest_path = project.blueprint_path
    _unknown_fields(
        data,
        {
            "schema_version",
            "id",
            "name",
            "description",
            "runtime",
            "runtime_version",
            "prompt",
            "skills",
            "tools",
            "requested_capabilities",
            "delegation",
            "budget",
            "output_contract",
        },
        diagnostics,
        path=manifest_path,
    )
    if data.get("schema_version") != BLUEPRINT_SCHEMA_VERSION:
        diagnostics.append(
            _diagnostic(
                "unsupported_schema",
                f"schema_version must be {BLUEPRINT_SCHEMA_VERSION!r}.",
                path=manifest_path,
                field="/schema_version",
            )
        )
    blueprint_id = _id_value(data.get("id"), diagnostics, path=manifest_path, field="/id")
    name = _required_string(data.get("name"), diagnostics, path=manifest_path, field="/name")
    description = _optional_string(data.get("description"), diagnostics, path=manifest_path, field="/description")
    runtime = ""
    if data.get("runtime") not in (None, ""):
        runtime = _id_value(data.get("runtime"), diagnostics, path=manifest_path, field="/runtime")
    runtime_version = _optional_string(
        data.get("runtime_version"), diagnostics, path=manifest_path, field="/runtime_version", max_length=200
    )
    prompt = data.get("prompt")
    prompt_path = ""
    if not isinstance(prompt, dict):
        diagnostics.append(_diagnostic("invalid_object", "Prompt must be an object with an explicit path.", path=manifest_path, field="/prompt"))
    else:
        _unknown_fields(prompt, {"path"}, diagnostics, path=manifest_path, field="/prompt")
        prompt_path = _path_text(prompt.get("path"), diagnostics, path=manifest_path, field="/prompt/path")
    skills = _resource_list(data.get("skills"), diagnostics, manifest_path=manifest_path, field="/skills")
    tools = _tool_list(data.get("tools"), diagnostics, manifest_path=manifest_path)
    capabilities = _string_list(
        data.get("requested_capabilities"),
        diagnostics,
        path=manifest_path,
        field="/requested_capabilities",
        safe_ids=True,
    )
    capability_set = set(capabilities)
    for index, tool in enumerate(tools):
        missing = sorted(set(tool.requested_capabilities) - capability_set)
        if missing:
            diagnostics.append(
                _diagnostic(
                    "tool_capability_not_requested",
                    f"Tool {tool.tool_id!r} requests capabilities not declared by the Blueprint: {', '.join(missing)}.",
                    path=manifest_path,
                    field=f"/tools/{index}/requested_capabilities",
                )
            )
    delegation_json = _string_map_json(
        data.get("delegation"), diagnostics, path=manifest_path, field="/delegation"
    )
    budget_json = _string_map_json(data.get("budget"), diagnostics, path=manifest_path, field="/budget")
    output_contract_json = _string_map_json(
        data.get("output_contract"), diagnostics, path=manifest_path, field="/output_contract"
    )
    if not all((blueprint_id, name, prompt_path)):
        return None
    return AgentBlueprint(
        blueprint_id=blueprint_id,
        name=name,
        description=description,
        runtime=runtime,
        runtime_version=runtime_version,
        prompt_path=prompt_path,
        skills=skills,
        tools=tools,
        requested_capabilities=capabilities,
        delegation_json=delegation_json,
        budget_json=budget_json,
        output_contract_json=output_contract_json,
    )


def _compile_agent_project(project_root: os.PathLike[str] | str) -> AgentProjectResult[AgentBuild]:
    diagnostics: list[AgentProjectDiagnostic] = []
    raw_root = os.fspath(project_root)
    if not raw_root:
        return AgentProjectResult(
            diagnostics=(_diagnostic("missing_project_root", "An Agent Project root is required."),)
        )
    try:
        root = Path(raw_root).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        return AgentProjectResult(
            diagnostics=(_diagnostic("invalid_project_root", str(exc), path=str(raw_root)),)
        )
    if not root.is_dir():
        return AgentProjectResult(
            diagnostics=(_diagnostic("invalid_project_root", "The Agent Project root must be a directory.", path=str(root)),)
        )

    manifest = _resolve_file(
        root,
        PROJECT_MANIFEST_NAME,
        diagnostics,
        manifest_path=PROJECT_MANIFEST_NAME,
        field="",
    )
    if manifest is None:
        return AgentProjectResult(diagnostics=tuple(diagnostics))
    project_data, project_raw = _load_json(manifest, PROJECT_MANIFEST_NAME, diagnostics)
    if project_data is None:
        return AgentProjectResult(diagnostics=tuple(diagnostics))
    project = _parse_project(root, project_data, diagnostics)
    if project is None:
        return AgentProjectResult(diagnostics=tuple(diagnostics))

    blueprint_file = _resolve_file(
        root,
        project.blueprint_path,
        diagnostics,
        manifest_path=PROJECT_MANIFEST_NAME,
        field="/entry_blueprint",
    )
    if blueprint_file is None:
        return AgentProjectResult(diagnostics=tuple(diagnostics))
    blueprint_data, blueprint_raw = _load_json(blueprint_file, project.blueprint_path, diagnostics)
    if blueprint_data is None:
        return AgentProjectResult(diagnostics=tuple(diagnostics))
    blueprint = _parse_blueprint(project, blueprint_data, diagnostics)
    if blueprint is None:
        return AgentProjectResult(diagnostics=tuple(diagnostics))

    declared: list[tuple[str, str, Path, bytes | None]] = [
        (PROJECT_MANIFEST_NAME, "project_manifest", manifest, project_raw),
        (project.blueprint_path, "blueprint", blueprint_file, blueprint_raw),
    ]
    references: list[tuple[str, str, str, str]] = [
        (blueprint.prompt_path, "prompt", project.blueprint_path, "/prompt/path"),
    ]
    references.extend(
        (item.path, f"skill:{item.resource_id}", project.blueprint_path, f"/skills/{index}/path")
        for index, item in enumerate(blueprint.skills)
    )
    references.extend(
        (item.path, f"tool:{item.tool_id}", project.blueprint_path, f"/tools/{index}/path")
        for index, item in enumerate(blueprint.tools)
    )
    references.extend(
        (item.path, f"test:{item.resource_id}", PROJECT_MANIFEST_NAME, f"/tests/{index}/path")
        for index, item in enumerate(project.tests)
    )

    declared_paths = {PROJECT_MANIFEST_NAME, project.blueprint_path}
    resolved_paths = {manifest, blueprint_file}
    for relative_path, role, owner_path, field in references:
        if relative_path in declared_paths:
            diagnostics.append(
                _diagnostic(
                    "duplicate_source_path",
                    f"Source path {relative_path!r} is declared more than once.",
                    path=owner_path,
                    field=field,
                )
            )
            continue
        declared_paths.add(relative_path)
        resolved = _resolve_file(root, relative_path, diagnostics, manifest_path=owner_path, field=field)
        if resolved is None:
            continue
        if resolved in resolved_paths:
            diagnostics.append(
                _diagnostic(
                    "duplicate_resolved_source",
                    "Two declared source paths resolve to the same file.",
                    path=owner_path,
                    field=field,
                )
            )
            continue
        resolved_paths.add(resolved)
        declared.append((relative_path, role, resolved, None))

    if any(item.severity == "error" for item in diagnostics):
        return AgentProjectResult(diagnostics=tuple(diagnostics))

    build_files: list[AgentBuildFile] = []
    for relative_path, role, resolved, captured in sorted(declared, key=lambda item: item[0]):
        raw = captured if captured is not None else _read_source_file(resolved, relative_path, diagnostics)
        if raw is None:
            continue
        build_files.append(
            AgentBuildFile(
                path=relative_path,
                role=role,
                sha256=hashlib.sha256(raw).hexdigest(),
                size=len(raw),
                content_base64=base64.b64encode(raw).decode("ascii"),
            )
        )
    if any(item.severity == "error" for item in diagnostics):
        return AgentProjectResult(diagnostics=tuple(diagnostics))

    digest_hash = hashlib.sha256()
    digest_hash.update(BUILD_SCHEMA_VERSION.encode("utf-8") + b"\x00")
    for item in build_files:
        path_bytes = item.path.encode("utf-8")
        role_bytes = item.role.encode("utf-8")
        content = item.content_bytes()
        for part in (path_bytes, role_bytes, content):
            digest_hash.update(len(part).to_bytes(8, "big"))
            digest_hash.update(part)
    runtime = blueprint.runtime or project.default_runtime
    runtime_version = blueprint.runtime_version or project.runtime_version
    build = AgentBuild(
        digest=digest_hash.hexdigest(),
        project=project,
        blueprint=blueprint,
        runtime=runtime,
        runtime_version=runtime_version,
        files=tuple(build_files),
        diagnostics=tuple(diagnostics),
    )
    return AgentProjectResult(value=build, diagnostics=tuple(diagnostics))


def compile_agent_project(project_root: os.PathLike[str] | str) -> AgentProjectResult[AgentBuild]:
    """Validate and freeze an Agent Project without leaking user-input exceptions."""

    try:
        return _compile_agent_project(project_root)
    except Exception as exc:  # pragma: no cover - defensive user boundary
        return AgentProjectResult(
            diagnostics=(
                _diagnostic("compiler_failure", f"Agent Project compilation failed safely: {exc}"),
            )
        )


def _normalized_unique_ids(
    values: Iterable[Any],
    diagnostics: list[AgentProjectDiagnostic],
    *,
    field: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        diagnostics.append(_diagnostic("invalid_array", "A sequence of IDs is required.", field=field))
        return ()
    result: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        item_field = f"{field}/{index}"
        item = _id_value(value, diagnostics, path="", field=item_field)
        if not item:
            continue
        if item in seen:
            diagnostics.append(_diagnostic("duplicate_value", f"Duplicate value {item!r}.", field=item_field))
            continue
        seen.add(item)
        result.append(item)
    return tuple(sorted(result))


def _create_agent_run_manifest(
    build: AgentBuild,
    *,
    assignment_id: str,
    granted_capabilities: Iterable[str] = (),
    granted_tool_ids: Iterable[str] = (),
    workspace: os.PathLike[str] | str,
    provider_revision: str,
    causation_refs: Iterable[str] = (),
) -> AgentProjectResult[AgentRunManifest]:
    diagnostics: list[AgentProjectDiagnostic] = []
    assignment = _id_value(assignment_id, diagnostics, path="", field="/assignment_id")
    if not isinstance(build, AgentBuild) or not _HEX_DIGEST_RE.fullmatch(str(getattr(build, "digest", ""))):
        diagnostics.append(_diagnostic("invalid_build", "A valid compiled AgentBuild is required.", field="/build"))
        return AgentProjectResult(diagnostics=tuple(diagnostics))

    revision = _required_string(provider_revision, diagnostics, path="", field="/provider_revision", max_length=200)
    raw_workspace = os.fspath(workspace) if workspace is not None else ""
    normalized_workspace = ""
    if not raw_workspace or raw_workspace.startswith("~") or not os.path.isabs(raw_workspace):
        diagnostics.append(
            _diagnostic(
                "invalid_workspace",
                "Run manifests require an explicit absolute workspace path; '~' is not expanded.",
                field="/workspace",
            )
        )
    else:
        normalized_workspace = os.path.normpath(raw_workspace)

    granted = _normalized_unique_ids(granted_capabilities, diagnostics, field="/granted_capabilities")
    granted_tools = _normalized_unique_ids(granted_tool_ids, diagnostics, field="/granted_tool_ids")
    declared_tools = {item.tool_id: item for item in build.blueprint.tools}
    unknown_tools = sorted(set(granted_tools) - set(declared_tools))
    if unknown_tools:
        diagnostics.append(
            _diagnostic(
                "unknown_tool_grant",
                f"Tool grants are not declared by this Build: {', '.join(unknown_tools)}.",
                field="/granted_tool_ids",
            )
        )

    requested = tuple(sorted(build.blueprint.requested_capabilities))
    effective = tuple(sorted(set(requested) & set(granted)))
    effective_set = set(effective)
    effective_tools: list[str] = []
    for tool_id in granted_tools:
        tool = declared_tools.get(tool_id)
        if tool is None:
            continue
        missing = sorted(set(tool.requested_capabilities) - effective_set)
        if missing:
            diagnostics.append(
                _diagnostic(
                    "tool_capability_denied",
                    f"Tool {tool_id!r} cannot be enabled because effective capabilities are missing: {', '.join(missing)}.",
                    field="/granted_tool_ids",
                )
            )
            continue
        effective_tools.append(tool_id)

    refs: list[str] = []
    ref_seen: set[str] = set()
    if isinstance(causation_refs, (str, bytes)):
        diagnostics.append(_diagnostic("invalid_array", "causation_refs must be a sequence.", field="/causation_refs"))
    else:
        for index, value in enumerate(causation_refs):
            ref = _required_string(value, diagnostics, path="", field=f"/causation_refs/{index}", max_length=500)
            if not ref:
                continue
            if ref in ref_seen:
                diagnostics.append(_diagnostic("duplicate_value", f"Duplicate causation ref {ref!r}.", field=f"/causation_refs/{index}"))
                continue
            ref_seen.add(ref)
            refs.append(ref)

    if any(item.severity == "error" for item in diagnostics):
        return AgentProjectResult(diagnostics=tuple(diagnostics))
    manifest = AgentRunManifest(
        assignment_id=assignment,
        build_digest=build.digest,
        project_id=build.project.project_id,
        blueprint_id=build.blueprint.blueprint_id,
        provider_id=build.runtime,
        provider_revision=revision,
        workspace=normalized_workspace,
        requested_capabilities=requested,
        granted_capabilities=granted,
        effective_capabilities=effective,
        requested_tool_ids=tuple(sorted(declared_tools)),
        granted_tool_ids=granted_tools,
        effective_tool_ids=tuple(sorted(effective_tools)),
        budget_json=build.blueprint.budget_json,
        output_contract_json=build.blueprint.output_contract_json,
        causation_refs=tuple(refs),
    )
    return AgentProjectResult(value=manifest, diagnostics=tuple(diagnostics))


def create_agent_run_manifest(
    build: AgentBuild,
    *,
    assignment_id: str,
    granted_capabilities: Iterable[str] = (),
    granted_tool_ids: Iterable[str] = (),
    workspace: os.PathLike[str] | str,
    provider_revision: str,
    causation_refs: Iterable[str] = (),
) -> AgentProjectResult[AgentRunManifest]:
    """Derive effective runtime authority; source requests never become grants."""

    try:
        return _create_agent_run_manifest(
            build,
            assignment_id=assignment_id,
            granted_capabilities=granted_capabilities,
            granted_tool_ids=granted_tool_ids,
            workspace=workspace,
            provider_revision=provider_revision,
            causation_refs=causation_refs,
        )
    except Exception as exc:  # pragma: no cover - defensive user boundary
        return AgentProjectResult(
            diagnostics=(_diagnostic("run_manifest_failure", f"Run manifest creation failed safely: {exc}"),)
        )


def _write_new_file(path: Path, content: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _prepare_projects_root(projects_root: os.PathLike[str] | str) -> Path:
    root = Path(projects_root).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve(strict=True)


def _temporary_project_path(root: Path, project_id: str) -> Path:
    return root / f".{project_id}.tmp-{uuid.uuid4().hex}"


def _publish_project(temp: Path, target: Path) -> None:
    os.rename(temp, target)
    try:
        directory_fd = os.open(str(target.parent), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def create_agent_project(
    projects_root: os.PathLike[str] | str,
    *,
    project_id: str,
    name: str = "",
    description: str = "",
    runtime: str = "pi-native",
    runtime_version: str = "",
) -> AgentProjectResult[AgentProject]:
    """Atomically create a minimal local Agent Project."""

    diagnostics: list[AgentProjectDiagnostic] = []
    safe_id = _id_value(project_id, diagnostics, path="", field="/id")
    display_name = name or safe_id
    display_name = _required_string(display_name, diagnostics, path="", field="/name")
    safe_runtime = _id_value(runtime, diagnostics, path="", field="/default_runtime")
    checked_description = _optional_string(description, diagnostics, path="", field="/description")
    checked_version = _optional_string(runtime_version, diagnostics, path="", field="/runtime_version", max_length=200)
    if any(item.severity == "error" for item in diagnostics):
        return AgentProjectResult(diagnostics=tuple(diagnostics))
    temp: Path | None = None
    try:
        root = _prepare_projects_root(projects_root)
        target = root / safe_id
        if target.exists() or target.is_symlink():
            diagnostics.append(_diagnostic("project_exists", "The target Agent Project already exists.", path=str(target)))
            return AgentProjectResult(diagnostics=tuple(diagnostics))
        temp = _temporary_project_path(root, safe_id)
        temp.mkdir(mode=0o700)
        (temp / "prompts").mkdir()
        (temp / "skills").mkdir()
        (temp / "tools").mkdir()
        project_record: dict[str, Any] = {
            "schema_version": PROJECT_SCHEMA_VERSION,
            "id": safe_id,
            "name": display_name,
            "description": checked_description,
            "entry_blueprint": "agent.json",
            "default_runtime": safe_runtime,
            "tests": [],
        }
        if checked_version:
            project_record["runtime_version"] = checked_version
        blueprint_record = {
            "schema_version": BLUEPRINT_SCHEMA_VERSION,
            "id": "main",
            "name": display_name,
            "description": checked_description,
            "prompt": {"path": "prompts/system.md"},
            "skills": [],
            "tools": [],
            "requested_capabilities": [],
            "delegation": {"max_subagents": 0},
            "budget": {},
            "output_contract": {"format": "text"},
        }
        _write_new_file(temp / PROJECT_MANIFEST_NAME, _json_bytes(project_record))
        _write_new_file(temp / "agent.json", _json_bytes(blueprint_record))
        _write_new_file(
            temp / "prompts" / "system.md",
            f"# {display_name}\n\nComplete the assigned task and return an auditable result.\n".encode("utf-8"),
        )
        compiled = compile_agent_project(temp)
        if not compiled.ok:
            return AgentProjectResult(diagnostics=compiled.diagnostics)
        _publish_project(temp, target)
        temp = None
        final = compile_agent_project(target)
        if not final.ok or final.value is None:
            return AgentProjectResult(diagnostics=final.diagnostics)
        return AgentProjectResult(value=final.value.project, diagnostics=final.diagnostics)
    except Exception as exc:
        diagnostics.append(_diagnostic("project_create_failed", str(exc)))
        return AgentProjectResult(diagnostics=tuple(diagnostics))
    finally:
        if temp is not None:
            shutil.rmtree(temp, ignore_errors=True)


def fork_agent_project(
    source_root: os.PathLike[str] | str,
    projects_root: os.PathLike[str] | str,
    *,
    project_id: str,
    name: str = "",
) -> AgentProjectResult[AgentProject]:
    """Atomically fork a valid project while preserving ordinary project files."""

    source = compile_agent_project(source_root)
    if not source.ok or source.value is None:
        return AgentProjectResult(diagnostics=source.diagnostics)
    diagnostics: list[AgentProjectDiagnostic] = []
    safe_id = _id_value(project_id, diagnostics, path="", field="/id")
    display_name = name or source.value.project.name
    display_name = _required_string(display_name, diagnostics, path="", field="/name")
    if any(item.severity == "error" for item in diagnostics):
        return AgentProjectResult(diagnostics=tuple(diagnostics))
    temp: Path | None = None
    try:
        root = _prepare_projects_root(projects_root)
        target = root / safe_id
        if target.exists() or target.is_symlink():
            diagnostics.append(_diagnostic("project_exists", "The target Agent Project already exists.", path=str(target)))
            return AgentProjectResult(diagnostics=tuple(diagnostics))
        temp = _temporary_project_path(root, safe_id)
        shutil.copytree(
            source.value.project.source_root,
            temp,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        manifest_path = temp / PROJECT_MANIFEST_NAME
        data, _ = _load_json(manifest_path, PROJECT_MANIFEST_NAME, diagnostics)
        if data is None:
            return AgentProjectResult(diagnostics=tuple(diagnostics))
        data["id"] = safe_id
        data["name"] = display_name
        manifest_path.unlink()
        _write_new_file(manifest_path, _json_bytes(data))
        compiled = compile_agent_project(temp)
        if not compiled.ok:
            return AgentProjectResult(diagnostics=compiled.diagnostics)
        _publish_project(temp, target)
        temp = None
        final = compile_agent_project(target)
        if not final.ok or final.value is None:
            return AgentProjectResult(diagnostics=final.diagnostics)
        return AgentProjectResult(value=final.value.project, diagnostics=final.diagnostics)
    except Exception as exc:
        diagnostics.append(_diagnostic("project_fork_failed", str(exc)))
        return AgentProjectResult(diagnostics=tuple(diagnostics))
    finally:
        if temp is not None:
            shutil.rmtree(temp, ignore_errors=True)


__all__ = [
    "AgentBlueprint",
    "AgentBuild",
    "AgentBuildFile",
    "AgentProject",
    "AgentProjectDiagnostic",
    "AgentProjectResult",
    "AgentResource",
    "AgentRunManifest",
    "AgentTool",
    "BLUEPRINT_SCHEMA_VERSION",
    "BUILD_SCHEMA_VERSION",
    "PROJECT_MANIFEST_NAME",
    "PROJECT_SCHEMA_VERSION",
    "RUN_MANIFEST_SCHEMA_VERSION",
    "compile_agent_project",
    "create_agent_project",
    "create_agent_run_manifest",
    "fork_agent_project",
    "safe_agent_id",
]
