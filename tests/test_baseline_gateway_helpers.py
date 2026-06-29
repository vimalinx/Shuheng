"""Tests for extracted baseline and gateway registry helpers."""
from __future__ import annotations

from ga_tui import baseline
from ga_tui import gateway_registry


def test_baseline_item_keeps_evidence_semantics() -> None:
    item = baseline.baseline_item(
        "a2a_mcp_gateway",
        "A2A/MCP Gateway",
        "compatibility surface",
        [
            (True, "schema exists"),
            {"ok": True, "description": "loopback smoke", "level": "e2e"},
        ],
    )

    assert item["status"] == "complete"
    assert item["strongest_evidence_level"] == "e2e"
    assert "End-to-end evidence exists" in item["claim_limit"]


def test_format_baseline_report_uses_caller_report_path() -> None:
    text = baseline.format_baseline_report(
        {
            "summary": {"complete": 1, "partial": 0, "missing": 0, "completion_ratio": 1.0},
            "items": [{"id": "x", "title": "X", "status": "complete", "strongest_evidence_level": "structural"}],
            "remaining_gaps": [],
        },
        report_path="/tmp/baseline.json",
    )

    assert "Architecture Baseline Comparison" in text
    assert "Report path: /tmp/baseline.json" in text


def test_gateway_resource_registry_and_descriptor_shapes() -> None:
    paths = {
        "messages": "/h/messages.jsonl",
        "tasks": "/h/tasks.jsonl",
        "progress": "/h/progress.jsonl",
        "artifacts": "/h/artifacts.jsonl",
        "checkpoints": "/h/checkpoints.jsonl",
        "recovery": "/h/recovery.jsonl",
        "recovery_plans": "/h/recovery_plans.jsonl",
        "runtime_evidence": "/h/runtime_evidence.jsonl",
        "runtime_providers": "/h/runtime_providers.json",
        "schedules": "/h/schedules.jsonl",
        "schedule_runs": "/h/schedule_runs.jsonl",
        "gateway_daemon_status": "/h/gateway_daemon.json",
        "gateway_push_subscriptions": "/h/gateway_push_subscriptions.jsonl",
        "gateway_push_deliveries": "/h/gateway_push_deliveries.jsonl",
        "bridges": "/h/bridge_registry.json",
        "policy": "/h/policy.json",
    }

    resources = gateway_registry.mcp_resource_registry(paths)
    descriptor = gateway_registry.gateway_service_descriptor(
        host="0.0.0.0",
        port=8765,
        bind_safety={"auth": "none", "local_only": False, "allowed": True},
        daemon_state={"status": "stopped"},
        gateway_push_subscriptions_path=paths["gateway_push_subscriptions"],
        gateway_push_deliveries_path=paths["gateway_push_deliveries"],
        gateway_daemon_pid_path="/h/gateway_daemon.pid",
        gateway_daemon_status_path=paths["gateway_daemon_status"],
        gateway_daemon_log_path="/h/gateway_daemon.log",
    )

    assert any(item["uri"] == "resource://agent-mail/runtime-evidence" for item in resources)
    assert descriptor["base_url"] == "http://127.0.0.1:8765"
    assert descriptor["status"] == "local_no_auth_compatibility_surface"
    assert descriptor["push_notifications"]["auth"] == "none"
