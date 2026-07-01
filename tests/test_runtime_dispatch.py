"""Tests for provider-neutral runtime dispatch helpers."""
from __future__ import annotations

import queue

from ga_tui import app as app_module
from ga_tui import runtime_dispatch
from ga_tui.runtime import RuntimeTaskRequest


class RuntimeTaskAgent:
    _ga_tui_runtime_provider_id = "ohmypi"
    native_session_file = " sessions/native.jsonl "
    native_context_usage = {"tokens": "50", "contextWindow": "200", "percent": 0}

    def __init__(self) -> None:
        self.requests: list[RuntimeTaskRequest] = []

    def get_llm_name(self, *, model: bool = False) -> str:
        return "test-model" if model else "Test Model"

    def put_runtime_task(self, request: RuntimeTaskRequest) -> queue.Queue:
        self.requests.append(request)
        result: queue.Queue = queue.Queue()
        result.put({"done": "runtime"})
        return result


class LegacyTaskAgent:
    _ga_tui_runtime_provider_id = ""

    def __init__(self) -> None:
        self.prompts: list[tuple[str, str]] = []

    def get_llm_name(self, *, model: bool = False) -> str:
        del model
        raise RuntimeError("model unavailable")

    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        self.prompts.append((prompt, source))
        result: queue.Queue = queue.Queue()
        result.put({"done": "legacy"})
        return result


class ModuleDetectedOmpAgent:
    __module__ = "ga_tui.ohmypi_provider"


def test_runtime_provider_identity_helpers() -> None:
    agent = RuntimeTaskAgent()
    legacy = LegacyTaskAgent()

    assert runtime_dispatch.agent_runtime_provider_id(agent) == "ohmypi"
    assert runtime_dispatch.agent_runtime_provider_id(legacy) == "unknown"
    assert runtime_dispatch.is_ohmypi_runtime_agent(agent) is True
    assert runtime_dispatch.is_ohmypi_runtime_agent(ModuleDetectedOmpAgent()) is True
    assert runtime_dispatch.is_ohmypi_runtime_agent(legacy) is False


def test_ohmypi_native_metadata_helpers() -> None:
    agent = RuntimeTaskAgent()

    assert runtime_dispatch.ohmypi_native_session_file(agent) == "sessions/native.jsonl"
    assert runtime_dispatch.ohmypi_native_context_usage(agent) == {
        "tokens": 50,
        "contextWindow": 200,
        "percent": 25.0,
    }
    assert runtime_dispatch.ohmypi_native_session_file(LegacyTaskAgent()) == ""
    assert runtime_dispatch.ohmypi_native_context_usage(LegacyTaskAgent()) == {}


def test_runtime_task_request_for_agent_fields_and_fallbacks() -> None:
    agent = RuntimeTaskAgent()
    request = runtime_dispatch.runtime_task_request_for_agent(
        agent=agent,
        task_id="task_runtime",
        parent_task_id="task_parent",
        prompt="Do work",
        source="test",
        agent_id="agent-runtime",
        role="researcher",
        objective="Runtime request",
        context_pack_ref="artifact://context_packs/agent-runtime/task_runtime.json",
        permissions={"write_policy": "none"},
        approval_policy={"approval_required_for": []},
        output_contract={"format": "summary"},
        metadata={"key": "value"},
    )

    assert request.provider_id == "ohmypi"
    assert request.model == "test-model"
    assert request.artifact_refs == ["artifact://context_packs/agent-runtime/task_runtime.json"]
    assert request.permissions["write_policy"] == "none"
    assert request.approval_policy == {"approval_required_for": []}
    assert request.output_contract == {"format": "summary"}
    assert request.metadata == {"key": "value"}

    fallback = runtime_dispatch.runtime_task_request_for_agent(
        agent=LegacyTaskAgent(),
        task_id="task_fallback",
        prompt="Prompt",
        source="legacy",
        agent_id="agent-legacy",
        role="specialist",
        objective="Fallback",
    )
    assert fallback.provider_id == "unknown"
    assert fallback.model == ""
    assert fallback.artifact_refs == []


def test_put_agent_runtime_task_uses_runtime_or_legacy_path() -> None:
    runtime_agent = RuntimeTaskAgent()
    runtime_request = runtime_dispatch.runtime_task_request_for_agent(
        agent=runtime_agent,
        task_id="task_runtime",
        prompt="runtime prompt",
        source="runtime",
        agent_id="agent-runtime",
        role="researcher",
        objective="Runtime",
    )
    runtime_dispatch.put_agent_runtime_task(runtime_agent, runtime_request)
    assert runtime_agent.requests == [runtime_request]

    legacy_agent = LegacyTaskAgent()
    legacy_request = runtime_dispatch.runtime_task_request_for_agent(
        agent=legacy_agent,
        task_id="task_legacy",
        prompt="legacy prompt",
        source="legacy-source",
        agent_id="agent-legacy",
        role="researcher",
        objective="Legacy",
    )
    runtime_dispatch.put_agent_runtime_task(legacy_agent, legacy_request)
    assert legacy_agent.prompts == [("legacy prompt", "legacy-source")]


def test_app_wrappers_match_runtime_dispatch_module() -> None:
    agent = RuntimeTaskAgent()
    request = app_module.runtime_task_request_for_agent(
        agent=agent,
        task_id="task_wrapper",
        prompt="wrapper prompt",
        source="wrapper",
        agent_id="agent-wrapper",
        role="researcher",
        objective="Wrapper",
        context_pack_ref="artifact://context_packs/agent-wrapper/task_wrapper.json",
    )
    module_request = runtime_dispatch.runtime_task_request_for_agent(
        agent=agent,
        task_id="task_wrapper",
        prompt="wrapper prompt",
        source="wrapper",
        agent_id="agent-wrapper",
        role="researcher",
        objective="Wrapper",
        context_pack_ref="artifact://context_packs/agent-wrapper/task_wrapper.json",
    )

    assert request == module_request
    assert app_module.agent_runtime_provider_id(agent) == runtime_dispatch.agent_runtime_provider_id(agent)
    assert app_module.is_ohmypi_runtime_agent(agent) == runtime_dispatch.is_ohmypi_runtime_agent(agent)
    assert app_module.ohmypi_native_session_file(agent) == runtime_dispatch.ohmypi_native_session_file(agent)
    assert app_module.ohmypi_native_context_usage(agent) == runtime_dispatch.ohmypi_native_context_usage(agent)
