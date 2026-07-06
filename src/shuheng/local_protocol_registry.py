"""Local protocol registry payload helpers for Shuheng."""
from __future__ import annotations

from typing import Any


def local_protocol_base_uri(host: str, port: int) -> str:
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
    bind_safety: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "agentgateway.service.v1",
        "status": "local_record_only",
        "bind": {"host": "", "port": 0},
        "base_url": "",
        "security": bind_safety,
        "release_posture": "experimental_alpha",
        "request_response": {
            "registry": "resource://agent-mail/local-protocol-registry",
            "agent_directory": "agent-directory://local",
            "message_inbox": "agent-mail://inbox",
            "resource_registry": "resource://agent-mail/*",
        },
        "sse": {
            "enabled": False,
            "endpoint": "",
            "event_sources": [],
        },
        "push_notifications": {
            "enabled": False,
            "subscribe_endpoint": "",
            "test_endpoint": "",
            "default_endpoint_policy": "not_available_without_external_adapter",
            "auth": "none",
        },
        "daemon": {
            "commands": [],
            "state": {"schema_version": "agentgateway.daemon.v1", "status": "removed", "alive": False},
        },
    }
