"""Runtime provider abstractions for the Shuheng control plane.

The TUI owns orchestration, ledgers, approvals, artifacts, model routing, and
scheduled work. OhMyPi/OMP is the default runtime core; legacy GenericAgent can
plug in through an adapter when explicitly available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuntimeTaskRequest:
    """Provider-neutral task envelope used above runtime-specific transports."""

    task_id: str
    provider_id: str
    prompt: str
    source: str = ""
    parent_task_id: str = ""
    agent_id: str = ""
    role: str = ""
    objective: str = ""
    context_pack_ref: str = ""
    model: str = ""
    permissions: dict[str, Any] = field(default_factory=dict)
    approval_policy: dict[str, Any] = field(default_factory=dict)
    output_contract: dict[str, Any] = field(default_factory=dict)
    artifact_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        prompt = str(self.prompt or "")
        return {
            "schema_version": "runtime.task_request.v1",
            "task_id": self.task_id,
            "parent_task_id": self.parent_task_id,
            "provider_id": self.provider_id,
            "agent_id": self.agent_id,
            "role": self.role,
            "objective": self.objective,
            "source": self.source,
            "prompt_preview": prompt[:1000],
            "prompt_chars": len(prompt),
            "context_pack_ref": self.context_pack_ref,
            "model": self.model,
            "permissions": dict(self.permissions),
            "approval_policy": dict(self.approval_policy),
            "output_contract": dict(self.output_contract),
            "artifact_refs": list(self.artifact_refs),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeTaskEvent:
    """Normalized runtime event emitted by concrete providers."""

    task_id: str
    provider_id: str
    event_type: str
    status: str = ""
    agent_id: str = ""
    source: str = ""
    message: str = ""
    delta: str = ""
    error: str = ""
    artifact_refs: list[str] = field(default_factory=list)
    tool_call_refs: list[str] = field(default_factory=list)
    request: RuntimeTaskRequest | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        request_record = self.request.to_record() if self.request is not None else {}
        return {
            "schema_version": "runtime.task_event.v1",
            "task_id": self.task_id,
            "provider_id": self.provider_id,
            "event_type": self.event_type,
            "status": self.status,
            "agent_id": self.agent_id,
            "source": self.source,
            "message": self.message,
            "delta": self.delta,
            "error": self.error,
            "artifact_refs": list(self.artifact_refs),
            "tool_call_refs": list(self.tool_call_refs),
            "request": request_record,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class RuntimeProviderSpec:
    provider_id: str
    name: str
    runtime_type: str
    status: str
    transport: str
    entrypoints: list[str] = field(default_factory=list)
    capabilities: dict[str, Any] = field(default_factory=dict)
    model_routing: dict[str, Any] = field(default_factory=dict)
    scheduler: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    a2a: dict[str, Any] = field(default_factory=dict)
    mcp: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": "agentruntime.provider.v1",
            "provider_id": self.provider_id,
            "name": self.name,
            "runtime_type": self.runtime_type,
            "status": self.status,
            "transport": self.transport,
            "entrypoints": list(self.entrypoints),
            "capabilities": dict(self.capabilities),
            "model_routing": dict(self.model_routing),
            "scheduler": dict(self.scheduler),
            "policy": dict(self.policy),
            "a2a": dict(self.a2a),
            "mcp": dict(self.mcp),
            "notes": list(self.notes),
        }


class RuntimeAdapter:
    """Base adapter for a concrete agent runtime."""

    def __init__(self, spec: RuntimeProviderSpec) -> None:
        self.spec = spec

    @property
    def provider_id(self) -> str:
        return self.spec.provider_id

    def create_agent(self) -> Any:
        raise NotImplementedError

    def prepare_agent(self, agent: Any, *, state: Any = None) -> None:
        del agent, state

    def start_agent(self, agent: Any, *, thread_name: str = "") -> Any:
        del agent, thread_name
        return None

    def abort_agent(self, agent: Any) -> None:
        try:
            agent.abort()
        except Exception:
            pass

    def put_task(self, agent: Any, prompt: str, *, source: str = "") -> Any:
        return agent.put_task(prompt, source=source)

    def put_runtime_task(self, agent: Any, request: RuntimeTaskRequest) -> Any:
        if hasattr(agent, "put_runtime_task"):
            return agent.put_runtime_task(request)
        return self.put_task(agent, request.prompt, source=request.source)

    def current_model(self, agent: Any) -> str:
        try:
            return str(agent.get_llm_name(model=True))
        except Exception:
            return ""


class RuntimeRegistry:
    def __init__(self, *, default_provider_id: str = "") -> None:
        self.default_provider_id = default_provider_id
        self._adapters: dict[str, RuntimeAdapter] = {}

    def register(self, adapter: RuntimeAdapter) -> RuntimeAdapter:
        self._adapters[adapter.provider_id] = adapter
        if not self.default_provider_id:
            self.default_provider_id = adapter.provider_id
        return adapter

    def get(self, provider_id: str) -> RuntimeAdapter | None:
        return self._adapters.get(provider_id)

    def default(self) -> RuntimeAdapter:
        adapter = self.get(self.default_provider_id)
        if adapter is not None:
            return adapter
        if self._adapters:
            return next(iter(self._adapters.values()))
        raise RuntimeError("No agent runtime providers are registered.")

    def records(self) -> list[dict[str, Any]]:
        return [adapter.spec.to_record() for adapter in self._adapters.values()]

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": "agentruntime.registry.v1",
            "default_provider_id": self.default().provider_id if self._adapters else "",
            "providers": self.records(),
            "provider_ids": sorted(self._adapters),
            "selection_policy": {
                "owner": "ga-tui.orchestrator",
                "default": "Use structured provider/capability metadata. Do not infer runtime choice from prose.",
                "write_conflict_policy": "read tasks may fan out; writes stay single-writer or approval-gated",
            },
        }


def genericagent_provider_spec(
    *,
    root_dir: str,
    harness_dir: str,
    recent_models_path: str,
    schedules_path: str,
) -> RuntimeProviderSpec:
    return RuntimeProviderSpec(
        provider_id="genericagent",
        name="GenericAgent",
        runtime_type="local_python_agent",
        status="legacy_available",
        transport="in_process_thread",
        entrypoints=["agentmain.GenericAgent", "continue_cmd.restore", "frontends/continue_cmd.py"],
        capabilities={
            "streaming": True,
            "interrupt": True,
            "session_restore": True,
            "tool_calling": True,
            "tui_query_tools": True,
            "artifact_refs": True,
            "memory_candidates": True,
            "human_approval": True,
            "subagents": True,
        },
        model_routing={
            "owner": "ga-tui.control_plane",
            "supports_runtime_switch": True,
            "supports_default_model": True,
            "supports_per_agent_default": True,
            "recent_models_path": recent_models_path,
            "selection_contract": "model config name or explicit provider/model metadata",
        },
        scheduler={
            "owner": "ga-tui.control_plane",
            "status": "registry_ready",
            "schedules_path": schedules_path,
            "dispatch_contract": "agenttask.v2",
            "runtime_provider_id": "genericagent",
        },
        policy={
            "approval_gate_owner": "ga-tui.policy",
            "tool_permissions": "role_template",
            "memory_write": "candidate_only",
            "risky_actions": ["deploy", "external_send", "delete_file", "spend_money", "access_secret"],
        },
        a2a={
            "agent_card": "runtime://provider/genericagent",
            "task_transport": "internal-agent-mail",
            "artifact_transport": "artifact_ref",
        },
        mcp={
            "tool_gateway": "resource://agent-mail/gateway",
            "resource_gateway": "resource://agent-mail",
        },
        notes=[
            "GenericAgent is an optional legacy compatibility adapter, not the Shuheng core runtime.",
            "The TUI owns orchestration, model routing, scheduled jobs, ledgers, approvals, and artifacts.",
            f"runtime_root={root_dir}",
            f"harness_dir={harness_dir}",
        ],
    )
