from __future__ import annotations

import base64
import hashlib
import json
import queue
import shutil
import threading
import time
from pathlib import Path

import pytest

from shuheng.pi_native_provider import (
    PI_NATIVE_BUILD_SCHEMA,
    PI_NATIVE_PROVIDER_ID,
    PI_NATIVE_SDK_PACKAGE,
    PI_NATIVE_SDK_VERSION,
    PiNativeRuntimeAdapter,
    PiNativeSidecarAgent,
    default_pi_native_sidecar_path,
    pi_native_provider_spec,
    pi_native_run_command,
)
from shuheng.runtime import RuntimeTaskEvent, RuntimeTaskRequest


def _build_file(path: str, role: str, content: bytes) -> dict[str, object]:
    return {
        "path": path,
        "role": role,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size": len(content),
        "content_base64": base64.b64encode(content).decode("ascii"),
    }


def _agent_build(*, with_skill: bool = True, with_tool: bool = True) -> dict[str, object]:
    project = {
        "schema_version": "shuheng.agent_project.v1",
        "id": "fixture-agent",
        "name": "Fixture Agent",
        "description": "",
        "entry_blueprint": "agent.json",
        "default_runtime": PI_NATIVE_PROVIDER_ID,
        "runtime_version": PI_NATIVE_SDK_VERSION,
        "tests": [],
    }
    skills = [{"id": "concise", "path": "skills/concise/SKILL.md"}] if with_skill else []
    tools = (
        [
            {
                "id": "lookup",
                "path": "tools/lookup.mjs",
                "requested_capabilities": ["repo.read"],
            }
        ]
        if with_tool
        else []
    )
    blueprint = {
        "schema_version": "shuheng.agent_blueprint.v1",
        "id": "main",
        "name": "Fixture Agent",
        "description": "",
        "prompt": {"path": "prompts/system.md"},
        "skills": skills,
        "tools": tools,
        "requested_capabilities": ["repo.read"] if with_tool else [],
        "delegation": {"max_subagents": 0},
        "budget": {},
        "output_contract": {"format": "text"},
    }
    project_bytes = json.dumps(project, sort_keys=True, separators=(",", ":")).encode()
    blueprint_bytes = json.dumps(blueprint, sort_keys=True, separators=(",", ":")).encode()
    files = [
        _build_file("agent-project.json", "project_manifest", project_bytes),
        _build_file("agent.json", "blueprint", blueprint_bytes),
        _build_file("prompts/system.md", "prompt", b"You are a frozen Pi-native worker."),
    ]
    if with_skill:
        files.append(
            _build_file(
                "skills/concise/SKILL.md",
                "skill:concise",
                b"---\nname: concise\ndescription: Answer briefly\n---\n\nKeep the result concise.\n",
            )
        )
    if with_tool:
        files.append(
            _build_file(
                "tools/lookup.mjs",
                "tool:lookup",
                (
                    "export default {name:'lookup',label:'Lookup',description:'Frozen lookup',"
                    "parameters:{type:'object',properties:{}},"
                    "async execute(){return {content:[{type:'text',text:'ok'}],details:{}}}};\n"
                ).encode(),
            )
        )
    digest = hashlib.sha256()
    digest.update(PI_NATIVE_BUILD_SCHEMA.encode() + b"\x00")
    for item in sorted(files, key=lambda record: str(record["path"])):
        content = base64.b64decode(str(item["content_base64"]))
        for part in (str(item["path"]).encode(), str(item["role"]).encode(), content):
            digest.update(len(part).to_bytes(8, "big"))
            digest.update(part)
    return {
        "schema_version": PI_NATIVE_BUILD_SCHEMA,
        "digest": digest.hexdigest(),
        "project": project,
        "blueprint": blueprint,
        "runtime": {"provider": PI_NATIVE_PROVIDER_ID, "version": PI_NATIVE_SDK_VERSION},
        "files": files,
        "validation": {"valid": True, "diagnostics": []},
    }


def _run_manifest(
    build: dict[str, object],
    *,
    task_id: str = "task-1",
    effective_tools: list[str] | None = None,
) -> dict[str, object]:
    blueprint = dict(build["blueprint"])
    requested_capabilities = list(blueprint.get("requested_capabilities") or [])
    requested_tools = [str(item["id"]) for item in blueprint.get("tools") or []]
    granted_tools = list(effective_tools or [])
    return {
        "schema_version": "shuheng.agent_run_manifest.v1",
        "assignment_id": task_id,
        "build_digest": build["digest"],
        "project_id": "fixture-agent",
        "blueprint_id": "main",
        "provider": {"id": PI_NATIVE_PROVIDER_ID, "revision": PI_NATIVE_SDK_VERSION},
        "workspace": "/workspace",
        "capabilities": {
            "requested": requested_capabilities,
            "granted": requested_capabilities,
            "effective": requested_capabilities,
        },
        "tools": {
            "requested": requested_tools,
            "granted": granted_tools,
            "effective": granted_tools,
        },
        "budget": {},
        "output_contract": {"format": "text"},
        "causation_refs": [],
    }


def _request(
    build: dict[str, object],
    *,
    task_id: str = "task-1",
    mock: dict[str, object] | None = None,
    effective_tools: list[str] | None = None,
) -> RuntimeTaskRequest:
    return RuntimeTaskRequest(
        task_id=task_id,
        provider_id=PI_NATIVE_PROVIDER_ID,
        prompt="summarize fixture",
        source="test",
        agent_id="fixture-agent",
        model="anthropic/claude-sonnet-4-5",
        metadata={
            "agent_project_id": "fixture-agent",
            "build_digest": str(build["digest"]),
            "provider_revision": PI_NATIVE_SDK_VERSION,
        },
        runtime_payload={
            "agent_build": build,
            "agent_run_manifest": _run_manifest(build, task_id=task_id, effective_tools=effective_tools),
            "pi_native_mock": dict(mock or {}),
        },
    )


def _wait_done(result_queue: queue.Queue, timeout: float = 5.0) -> tuple[list[dict[str, object]], dict[str, object]]:
    items: list[dict[str, object]] = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        item = result_queue.get(timeout=max(0.05, deadline - time.monotonic()))
        items.append(item)
        if "done" in item:
            return items, item
    raise AssertionError("Pi-native task did not finish")


def test_sidecar_package_pins_upstream_sdk_and_excludes_omp_package() -> None:
    sidecar_dir = Path(default_pi_native_sidecar_path()).parent
    package = json.loads((sidecar_dir / "package.json").read_text(encoding="utf-8"))

    assert package["dependencies"] == {PI_NATIVE_SDK_PACKAGE: PI_NATIVE_SDK_VERSION}
    assert "@oh-my-pi" not in (sidecar_dir / "package.json").read_text(encoding="utf-8")
    assert "@oh-my-pi" not in (sidecar_dir / "sidecar.mjs").read_text(encoding="utf-8")


def test_run_command_uses_transient_frozen_build_and_materializes_no_mutable_source(tmp_path: Path) -> None:
    build = _agent_build()
    request = _request(build, effective_tools=["lookup"])

    command = pi_native_run_command(
        request,
        agent_dir=str(tmp_path / "agent"),
        workspace_root=str(tmp_path / "workspace"),
        request_id="run-1",
        mock_mode=True,
    )

    assert command["build"]["system_prompt"] == "You are a frozen Pi-native worker."
    assert command["effective_tools"] == ["lookup"]
    tool = command["build"]["custom_tools"][0]
    assert tool["name"] == "lookup"
    assert tool["content_base64"]
    assert "source_path" not in tool
    assert "source_root" not in json.dumps(command)
    assert "runtime_payload" not in request.to_record()
    assert "content_base64" not in json.dumps(request.to_record())


def test_run_command_rejects_metadata_build_and_tampered_frozen_bytes(tmp_path: Path) -> None:
    build = _agent_build()
    metadata_only = RuntimeTaskRequest(
        task_id="metadata-only",
        provider_id=PI_NATIVE_PROVIDER_ID,
        prompt="no source",
        metadata={"agent_build": build},
    )
    with pytest.raises(ValueError, match="runtime_payload.agent_build"):
        pi_native_run_command(
            metadata_only,
            agent_dir=str(tmp_path / "agent"),
            workspace_root=str(tmp_path),
            request_id="run-metadata",
        )


def test_run_command_requires_manifest_binding_and_recomputes_authority(tmp_path: Path) -> None:
    build = _agent_build()
    missing_manifest = _request(build, effective_tools=["lookup"])
    del missing_manifest.runtime_payload["agent_run_manifest"]
    with pytest.raises(ValueError, match="agent_run_manifest is required"):
        pi_native_run_command(
            missing_manifest,
            agent_dir=str(tmp_path / "agent"),
            workspace_root=str(tmp_path),
            request_id="run-missing-manifest",
        )

    wrong_assignment = _request(build, effective_tools=["lookup"])
    wrong_assignment.runtime_payload["agent_run_manifest"]["assignment_id"] = "another-task"
    with pytest.raises(ValueError, match="assignment_id"):
        pi_native_run_command(
            wrong_assignment,
            agent_dir=str(tmp_path / "agent"),
            workspace_root=str(tmp_path),
            request_id="run-wrong-assignment",
        )

    escalated = _request(build, effective_tools=[])
    escalated.runtime_payload["agent_run_manifest"]["tools"]["effective"] = ["lookup"]
    with pytest.raises(ValueError, match="effective Tools"):
        pi_native_run_command(
            escalated,
            agent_dir=str(tmp_path / "agent"),
            workspace_root=str(tmp_path),
            request_id="run-escalated",
        )

    tampered = json.loads(json.dumps(build))
    tampered["files"][-1]["content_base64"] = base64.b64encode(b"changed source").decode("ascii")
    with pytest.raises(ValueError, match="size mismatch|digest mismatch"):
        pi_native_run_command(
            _request(tampered),
            agent_dir=str(tmp_path / "agent"),
            workspace_root=str(tmp_path),
            request_id="run-tampered",
        )


def test_transient_model_credentials_reach_sidecar_command_but_not_durable_record(tmp_path: Path) -> None:
    build = _agent_build(with_tool=False)
    request = RuntimeTaskRequest(
        task_id="model-task",
        provider_id=PI_NATIVE_PROVIDER_ID,
        prompt="use transient model",
        model=PI_NATIVE_PROVIDER_ID,
        runtime_payload={
            "agent_build": build,
            "agent_run_manifest": _run_manifest(build, task_id="model-task"),
            "model": {
                "provider": "shuheng-custom",
                "id": "custom-model",
                "name": "Custom Model",
                "api": "openai-completions",
                "api_key": "transient-model-secret",
                "base_url": "https://model.invalid/v1",
                "context_window": 64000,
                "max_tokens": 4096,
            },
        },
    )

    command = pi_native_run_command(
        request,
        agent_dir=str(tmp_path / "agent"),
        workspace_root=str(tmp_path / "workspace"),
        request_id="run-model",
    )

    assert command["model"]["provider"] == "shuheng-custom"
    assert command["model"]["id"] == "custom-model"
    assert command["model"]["api_key"] == "transient-model-secret"
    durable = json.dumps(request.to_record(), sort_keys=True)
    assert "transient-model-secret" not in durable
    assert "model.invalid" not in durable


def test_mock_sidecar_describe_health_and_runtime_event_mapping(tmp_path: Path, monkeypatch) -> None:
    node = shutil.which("node")
    assert node
    events: list[RuntimeTaskEvent] = []
    agent = PiNativeSidecarAgent(
        command=[node, default_pi_native_sidecar_path()],
        cwd=str(tmp_path),
        agent_dir=str(tmp_path / "runtime"),
        mock_mode=True,
        runtime_event_sink=events.append,
    )
    build = _agent_build(with_tool=False)
    request = _request(
        build,
        mock={"response": "deterministic result", "chunks": ["deterministic ", "result"]},
    )
    runtime_dirs: list[Path] = []

    def isolated_runtime_dir(*, prefix: str) -> str:
        path = tmp_path / f"{prefix}{len(runtime_dirs) + 1}"
        path.mkdir(mode=0o700)
        runtime_dirs.append(path)
        return str(path)

    from shuheng import pi_native_provider as provider_module

    monkeypatch.setattr(provider_module.tempfile, "mkdtemp", isolated_runtime_dir)
    try:
        describe = agent.describe()
        assert agent._process is None
        health = agent.health()
        assert agent._process is None
        items, done = _wait_done(agent.put_runtime_task(request))
    finally:
        agent.close()

    assert describe["status"] == "ok"
    assert describe["data"]["sdk_package"] == PI_NATIVE_SDK_PACKAGE
    assert describe["data"]["sdk_version"] == PI_NATIVE_SDK_VERSION
    assert describe["data"]["isolation"]["implicit_extensions"] is False
    assert describe["data"]["isolation"]["implicit_context_files"] is False
    assert describe["data"]["isolation"]["implicit_prompt_templates"] is False
    assert describe["data"]["isolation"]["implicit_skills"] is False
    assert describe["data"]["isolation"]["fresh_process_per_run"] is True
    assert describe["data"]["isolation"]["os_syscall_sandbox"] is False
    assert health["status"] == "ok"
    assert health["data"]["mode"] == "mock"
    assert [item.get("next") for item in items if "next" in item] == ["deterministic ", "result"]
    assert done["done"] == "deterministic result"
    assert [event.event_type for event in events] == [
        "runtime_task_requested",
        "runtime_task_started",
        "runtime_task_delta",
        "runtime_task_delta",
        "runtime_task_completed",
    ]
    assert all(event.provider_id == PI_NATIVE_PROVIDER_ID for event in events)
    assert all("content_base64" not in json.dumps(event.to_record()) for event in events)
    assert agent._process is None
    assert runtime_dirs and all(not path.exists() for path in runtime_dirs)


def test_abort_during_sidecar_startup_cannot_overtake_run_frame(tmp_path: Path, monkeypatch) -> None:
    agent = PiNativeSidecarAgent(
        cwd=str(tmp_path),
        agent_dir=str(tmp_path / "runtime"),
        mock_mode=True,
    )
    entered = threading.Event()
    release = threading.Event()
    sent: list[dict[str, object]] = []

    def delayed_start() -> None:
        entered.set()
        assert release.wait(3)

    monkeypatch.setattr(agent, "_ensure_process", delayed_start)
    monkeypatch.setattr(agent, "_send", lambda frame: sent.append(dict(frame)))
    result_queue = agent.put_runtime_task(_request(_agent_build(with_tool=False)))
    assert entered.wait(3)
    agent.abort()
    release.set()
    _items, done = _wait_done(result_queue)
    agent.close()

    assert done["status"] == "aborted"
    assert not any(frame.get("type") == "run" for frame in sent)


def test_mock_sidecar_abort_is_terminal_and_non_crashing(tmp_path: Path) -> None:
    node = shutil.which("node")
    assert node
    events: list[RuntimeTaskEvent] = []
    agent = PiNativeSidecarAgent(
        command=[node, default_pi_native_sidecar_path()],
        cwd=str(tmp_path),
        agent_dir=str(tmp_path / "runtime"),
        mock_mode=True,
        runtime_event_sink=events.append,
    )
    request = _request(
        _agent_build(with_tool=False),
        task_id="abort-task",
        mock={"response": "late", "chunks": ["late"], "delay_ms": 500},
    )
    try:
        result_queue = agent.put_runtime_task(request)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not any(event.event_type == "runtime_task_started" for event in events):
            time.sleep(0.01)
        agent.abort()
        _items, done = _wait_done(result_queue)
    finally:
        agent.close()

    assert "abort" in str(done["done"]).lower()
    assert events[-1].event_type == "runtime_task_aborted"
    assert events[-1].status == "aborted"


def test_missing_binary_and_missing_sdk_are_user_visible_failures(tmp_path: Path) -> None:
    events: list[RuntimeTaskEvent] = []
    missing_binary = PiNativeSidecarAgent(
        command=[str(tmp_path / "missing-runtime"), default_pi_native_sidecar_path()],
        cwd=str(tmp_path),
        agent_dir=str(tmp_path / "missing-binary-agent"),
        mock_mode=True,
        runtime_event_sink=events.append,
    )
    try:
        _items, done = _wait_done(missing_binary.put_runtime_task(_request(_agent_build(with_tool=False))))
    finally:
        missing_binary.close()
    assert "启动失败" in str(done["done"])
    assert "executable not found" in str(done["done"])
    assert events[-1].event_type == "runtime_task_failed"

    node = shutil.which("node")
    assert node
    isolated_sidecar = tmp_path / "without-node-modules" / "sidecar.mjs"
    isolated_sidecar.parent.mkdir()
    shutil.copyfile(default_pi_native_sidecar_path(), isolated_sidecar)
    live_events: list[RuntimeTaskEvent] = []
    missing_sdk = PiNativeSidecarAgent(
        command=[node, str(isolated_sidecar)],
        cwd=str(tmp_path),
        agent_dir=str(tmp_path / "missing-sdk-agent"),
        runtime_event_sink=live_events.append,
    )
    try:
        _items, live_done = _wait_done(missing_sdk.put_runtime_task(_request(_agent_build(with_tool=False))))
    finally:
        missing_sdk.close()
    assert "运行失败" in str(live_done["done"])
    assert PI_NATIVE_SDK_PACKAGE in str(live_done["done"])
    assert live_events[-1].event_type == "runtime_task_failed"


def test_provider_spec_and_adapter_are_optional_task_worker_foundation(tmp_path: Path) -> None:
    node = shutil.which("node")
    assert node
    spec = pi_native_provider_spec(
        command=[node, default_pi_native_sidecar_path()],
        mock_mode=True,
    )
    adapter = PiNativeRuntimeAdapter(
        spec,
        command=[node, default_pi_native_sidecar_path()],
        cwd=str(tmp_path),
        agent_dir=str(tmp_path / "runtime"),
        mock_mode=True,
    )
    agent = adapter.create_agent()
    try:
        assert spec.provider_id == PI_NATIVE_PROVIDER_ID
        assert spec.status == "available"
        assert spec.capabilities["immutable_agent_build"] is True
        assert spec.policy["implicit_resource_discovery"] is False
        assert spec.policy["tool_os_sandbox"] == "not_available_trusted_local_code_only"
        assert isinstance(agent, PiNativeSidecarAgent)
        assert "task-worker" in spec.notes[0]
    finally:
        agent.close()


def test_provider_module_has_no_app_or_curses_dependency() -> None:
    source = Path(__file__).parents[1].joinpath("src", "shuheng", "pi_native_provider.py").read_text(encoding="utf-8")
    assert "shuheng.app" not in source
    assert "import curses" not in source


def test_sidecar_process_environment_drops_unrelated_host_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    from shuheng import pi_native_provider as provider_module

    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("LANG", "C.UTF-8")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-tool")
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-reach-tool-either")

    isolated = provider_module._isolated_sidecar_process_env()

    assert isolated["PATH"] == "/usr/bin"
    assert isolated["LANG"] == "C.UTF-8"
    assert "OPENAI_API_KEY" not in isolated
    assert "GITHUB_TOKEN" not in isolated
