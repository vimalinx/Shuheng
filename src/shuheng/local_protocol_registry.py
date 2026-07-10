"""Local protocol registry payload helpers for Shuheng."""
from __future__ import annotations

from typing import Any


def local_protocol_base_uri() -> str:
    return "local://shuheng"


def mcp_resource_registry(paths: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {"uri": "resource://agent-mail/messages", "path": paths["messages"], "description": "Internal Agent Mail JSONL"},
        {"uri": "resource://agent-mail/tasks", "path": paths["tasks"], "description": "Task ledger JSONL"},
        {"uri": "resource://agent-mail/progress", "path": paths["progress"], "description": "Progress ledger JSONL"},
        {"uri": "resource://agent-mail/artifacts", "path": paths["artifacts"], "description": "Artifact index JSONL"},
        {"uri": "resource://agent-mail/checkpoints", "path": paths["checkpoints"], "description": "Checkpoint index JSONL"},
        {"uri": "resource://agent-mail/recovery", "path": paths["recovery"], "description": "Recovery records JSONL"},
        {"uri": "resource://agent-mail/recovery-plans", "path": paths["recovery_plans"], "description": "Replayable recovery plan JSONL"},
        {"uri": "resource://agent-mail/runtime-evidence", "path": paths["runtime_evidence"], "description": "Runtime and E2E smoke evidence JSONL"},
        {"uri": "resource://agent-mail/runtime-providers", "path": paths["runtime_providers"], "description": "Agent runtime provider registry JSON"},
        {"uri": "resource://agent-mail/schedules", "path": paths["schedules"], "description": "Top-level scheduled task registry JSONL"},
        {"uri": "resource://agent-mail/schedule-runs", "path": paths["schedule_runs"], "description": "Scheduled task run audit JSONL"},
        {"uri": "resource://agent-mail/bridges", "path": paths["bridges"], "description": "External bridge registry JSON"},
        {"uri": "resource://agent-mail/policy", "path": paths["policy"], "description": "Policy gate config"},
    ]


def local_protocol_service_descriptor(
    *,
    persistent_gateway: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gateway = persistent_gateway or {}
    request_response = {
        "registry": "resource://agent-mail/local-protocol-registry",
        "agent_directory": "agent-directory://local",
        "message_inbox": "agent-mail://inbox",
        "resource_registry": "resource://agent-mail/*",
    }
    if gateway:
        request_response.update({
            "message_send": "shuheng-gateway://message-send",
            "task_status": "shuheng-gateway://task-status/{task_id}",
        })
    return {
        "schema_version": "agentgateway.service.v1",
        "status": "local_persistent_stdio_gateway" if gateway else "local_record_only",
        "release_posture": "experimental_alpha",
        "transport": "local-jsonl-stdio" if gateway else "local-record",
        "request_response": request_response,
        "stdio": {
            "framing": "jsonl",
            "input": "stdin",
            "output": "stdout",
            "commands": gateway.get("commands") or [],
            "state": gateway.get("state")
            or {"schema_version": "agentgateway.runtime.v1", "status": "local_record_only"},
        },
    }
