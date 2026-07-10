from __future__ import annotations

from pathlib import Path

import pytest

from shuheng import agent_bridge


@pytest.mark.parametrize(
    "value",
    [
        "artifact://artifacts/gateway-public/task-result.json",
        "artifact://context_packs/agent-safe/task-safe.json",
        "artifact://checkpoints/task-safe.json",
    ],
)
def test_public_artifact_ref_accepts_only_canonical_opaque_refs(value: str) -> None:
    assert agent_bridge.is_public_artifact_ref(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "",
        "artifact://",
        "artifact:///tmp/private.txt",
        "artifact://../private.txt",
        "artifact://public/../../private.txt",
        "artifact://tmp/shuheng-home/memory/private.txt",
        "artifact://artifacts/too/many/segments.json",
        "artifact://public\\private.txt",
        "file:///tmp/private.txt",
    ],
)
def test_public_artifact_ref_rejects_paths_and_traversal(value: str) -> None:
    assert agent_bridge.is_public_artifact_ref(value) is False


def test_public_artifact_ref_rejects_workspace_disguised_as_uri_authority() -> None:
    disguised = f"artifact://{Path.cwd().as_posix().lstrip('/')}/private.txt"

    assert agent_bridge.is_public_artifact_ref(disguised) is False


@pytest.mark.parametrize("command", ["metadata", "call", "query", "context-get", "memory-candidate-submit"])
def test_public_gateway_parser_has_no_internal_bridge_commands(command: str) -> None:
    with pytest.raises(SystemExit) as exc_info:
        agent_bridge.gateway_main([command])

    assert exc_info.value.code == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "agent_directory", "args": ["public", False]},
        {"action": "agent_directory", "args": None},
        {"action": ["agent_directory"], "args": {}},
        {"action": "agent_directory", "args": {}, "internal": True},
    ],
)
def test_public_gateway_rejects_non_schema_request_shapes(payload: dict[str, object]) -> None:
    service = object.__new__(agent_bridge.AgentBridgeService)

    result = service.handle_gateway(payload)

    assert result["status"] == "error"
    assert result["schema_version"] == "shuheng.agent_gateway.v1"
