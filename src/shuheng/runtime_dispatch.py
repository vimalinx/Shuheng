"""Provider-neutral runtime dispatch helpers for the Shuheng control plane."""
from __future__ import annotations

from typing import Any

try:
    from .runtime import RuntimeTaskRequest
except Exception:
    from runtime import RuntimeTaskRequest  # type: ignore


def agent_runtime_provider_id(agent: Any) -> str:
    provider_id = str(getattr(agent, "_shuheng_runtime_provider_id", "") or "").strip()
    return provider_id or "unknown"


def is_ohmypi_runtime_agent(agent: Any) -> bool:
    if agent_runtime_provider_id(agent) == "ohmypi":
        return True
    module = str(getattr(type(agent), "__module__", "") or "")
    return module.endswith("ohmypi_provider")


def ohmypi_native_session_file(agent: Any) -> str:
    if not is_ohmypi_runtime_agent(agent):
        return ""
    return str(getattr(agent, "native_session_file", "") or "").strip()


def ohmypi_native_context_usage(agent: Any) -> dict[str, Any]:
    if not is_ohmypi_runtime_agent(agent):
        return {}
    raw = getattr(agent, "native_context_usage", {}) or {}
    if not isinstance(raw, dict):
        return {}
    try:
        tokens = max(0, int(raw.get("tokens", 0) or 0))
    except (TypeError, ValueError):
        tokens = 0
    try:
        context_window = max(0, int(raw.get("contextWindow", raw.get("context_window", 0)) or 0))
    except (TypeError, ValueError):
        context_window = 0
    try:
        percent = float(raw.get("percent", 0) or 0.0)
    except (TypeError, ValueError):
        percent = 0.0
    if percent <= 0 and tokens > 0 and context_window > 0:
        percent = tokens / context_window * 100.0
    if tokens <= 0 and context_window <= 0:
        return {}
    return {"tokens": tokens, "contextWindow": context_window, "percent": max(0.0, percent)}


def runtime_task_request_for_agent(
    *,
    agent: Any,
    task_id: str,
    prompt: str,
    source: str,
    agent_id: str,
    role: str,
    objective: str,
    parent_task_id: str = "",
    context_pack_ref: str = "",
    permissions: dict[str, Any] | None = None,
    approval_policy: dict[str, Any] | None = None,
    output_contract: dict[str, Any] | None = None,
    artifact_refs: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RuntimeTaskRequest:
    model = ""
    try:
        model = str(agent.get_llm_name(model=True))
    except Exception:
        model = ""
    return RuntimeTaskRequest(
        task_id=task_id,
        parent_task_id=parent_task_id,
        provider_id=agent_runtime_provider_id(agent),
        agent_id=agent_id,
        role=role,
        objective=objective,
        prompt=prompt,
        source=source,
        context_pack_ref=context_pack_ref,
        model=model,
        permissions=permissions or {},
        approval_policy=approval_policy or {},
        output_contract=output_contract or {},
        artifact_refs=artifact_refs or ([context_pack_ref] if context_pack_ref else []),
        metadata=metadata or {},
    )


def put_agent_runtime_task(agent: Any, request: RuntimeTaskRequest) -> Any:
    if hasattr(agent, "put_runtime_task"):
        return agent.put_runtime_task(request)
    return agent.put_task(request.prompt, source=request.source)
