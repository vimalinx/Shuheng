"""Gateway registry payload helpers for Shuheng."""
from __future__ import annotations

from typing import Any


def gateway_base_url(host: str, port: int) -> str:
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else (host or "127.0.0.1")
    return f"http://{display_host}:{int(port)}"


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
        {"uri": "resource://agent-mail/gateway-daemon", "path": paths["gateway_daemon_status"], "description": "Gateway daemon status JSON"},
        {"uri": "resource://agent-mail/gateway-push-subscriptions", "path": paths["gateway_push_subscriptions"], "description": "Gateway push subscriptions JSONL"},
        {"uri": "resource://agent-mail/gateway-push-deliveries", "path": paths["gateway_push_deliveries"], "description": "Gateway push delivery audit JSONL"},
        {"uri": "resource://agent-mail/bridges", "path": paths["bridges"], "description": "External bridge registry JSON"},
        {"uri": "resource://agent-mail/policy", "path": paths["policy"], "description": "Policy gate config"},
    ]


def gateway_service_descriptor(
    *,
    host: str,
    port: int,
    bind_safety: dict[str, Any],
    daemon_state: dict[str, Any],
    gateway_push_subscriptions_path: str,
    gateway_push_deliveries_path: str,
    gateway_daemon_pid_path: str,
    gateway_daemon_status_path: str,
    gateway_daemon_log_path: str,
) -> dict[str, Any]:
    base_url = gateway_base_url(host, port)
    return {
        "schema_version": "agentgateway.service.v1",
        "status": "local_no_auth_compatibility_surface",
        "bind": {"host": host, "port": int(port)},
        "base_url": base_url,
        "security": bind_safety,
        "release_posture": "experimental_alpha",
        "request_response": {
            "health": f"{base_url}/health",
            "registry": f"{base_url}/gateway",
            "a2a": f"{base_url}/a2a",
            "mcp": f"{base_url}/mcp",
            "a2a_task_query": f"{base_url}/a2a/tasks/query",
            "mcp_resource_read": f"{base_url}/mcp/resource?uri=resource://agent-mail/tasks",
        },
        "sse": {
            "endpoint": f"{base_url}/a2a/events",
            "content_type": "text/event-stream",
            "event_sources": ["agent_mail", "trace"],
        },
        "push_notifications": {
            "subscribe_endpoint": f"{base_url}/a2a/push-subscriptions",
            "test_endpoint": f"{base_url}/a2a/push-test",
            "subscriptions_path": gateway_push_subscriptions_path,
            "deliveries_path": gateway_push_deliveries_path,
            "default_endpoint_policy": "loopback_only_unless_SHUHENG_GATEWAY_ALLOW_REMOTE_PUSH=1",
            "auth": "none",
        },
        "daemon": {
            "commands": ["start", "stop", "restart", "status"],
            "pid_path": gateway_daemon_pid_path,
            "status_path": gateway_daemon_status_path,
            "log_path": gateway_daemon_log_path,
            "state": daemon_state,
        },
    }
