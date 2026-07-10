"""Tests for extracted baseline and local protocol registry helpers."""
from __future__ import annotations

from shuheng import baseline
from shuheng import local_protocol_registry


def test_baseline_item_keeps_evidence_semantics() -> None:
    item = baseline.baseline_item(
        "local_protocol_records",
        "Local Protocol Records",
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


def test_local_protocol_resource_registry_and_descriptor_shapes() -> None:
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
        "context_inspector": "/h/context_inspector.json",
        "permission_matrix": "/h/permission_matrix.json",
        "schedules": "/h/schedules.jsonl",
        "schedule_runs": "/h/schedule_runs.jsonl",
        "bridges": "/h/bridge_registry.json",
        "policy": "/h/policy.json",
    }

    resources = local_protocol_registry.mcp_resource_registry(paths)
    descriptor = local_protocol_registry.local_protocol_service_descriptor()

    assert any(item["uri"] == "resource://agent-mail/runtime-evidence" for item in resources)
    assert not any(item["uri"] == "resource://agent-mail/context-inspector" for item in resources)
    assert not any(item["uri"] == "resource://agent-mail/permission-matrix" for item in resources)
    assert descriptor["status"] == "local_record_only"
    assert descriptor["transport"] == "local-record"
    assert descriptor["request_response"]["message_inbox"] == "agent-mail://inbox"
    assert descriptor["request_response"]["agent_directory"] == "agent-directory://local"
    assert "message_send" not in descriptor["request_response"]
    assert "task_status" not in descriptor["request_response"]
    assert "context_inspector" not in descriptor["request_response"]
    assert "permission_matrix" not in descriptor["request_response"]
    assert descriptor["stdio"] == {
        "framing": "jsonl",
        "input": "stdin",
        "output": "stdout",
        "commands": [],
        "state": {"schema_version": "agentgateway.runtime.v1", "status": "local_record_only"},
    }


def test_local_protocol_descriptor_reports_registered_stdio_gateway_only_when_registered() -> None:
    descriptor = local_protocol_registry.local_protocol_service_descriptor(
        persistent_gateway={
            "transport": "local-jsonl-stdio",
            "commands": {"serve": ["shuheng-agent-gateway", "serve", "--stdio"]},
            "state": {"schema_version": "agentgateway.runtime.v1", "status": "registered", "alive": False},
        },
    )

    assert descriptor["status"] == "local_persistent_stdio_gateway"
    assert descriptor["transport"] == "local-jsonl-stdio"
    assert descriptor["request_response"]["message_send"] == "shuheng-gateway://message-send"
    assert descriptor["request_response"]["task_status"] == "shuheng-gateway://task-status/{task_id}"
    assert descriptor["stdio"]["commands"]["serve"] == ["shuheng-agent-gateway", "serve", "--stdio"]
    assert descriptor["stdio"]["state"]["status"] == "registered"
