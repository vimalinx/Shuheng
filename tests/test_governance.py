"""Tests for low-level governance ledger helpers."""
from __future__ import annotations

import json
import os
from pathlib import Path

from ga_tui import app as app_module
from ga_tui import governance
from ga_tui.ledger_store import read_jsonl
from ga_tui.ui_types import PolicyDecision, SubAgentRuntime


def test_policy_decision_and_approval_metadata_shapes() -> None:
    decision = PolicyDecision(
        decision_id="policy_test",
        action="deploy",
        subject="orchestrator.main",
        role="ops",
        status="approval_required",
        allowed=False,
        approval_required=True,
        approval_required_for="deploy",
        risk="high",
        reason="requires approval",
        source="/deploy",
        target="production",
        approval_id="appr_test",
        payload={"task_id": "task_policy"},
    )

    row = governance.policy_decision_to_dict(decision, timestamp="2026-07-01T00:00:00+0800")

    assert row["schema_version"] == "agentpolicy.decision.v1"
    assert row["approval_id"] == "appr_test"
    assert row["payload"]["task_id"] == "task_policy"
    assert app_module.APPROVAL_REQUIRED_FOR is governance.APPROVAL_REQUIRED_FOR
    assert app_module.approval_metadata(decision=decision) == governance.approval_metadata(decision=decision)


def test_subagent_result_task_row_helpers(tmp_path: Path, monkeypatch) -> None:
    artifact_ref = "artifact://artifacts/subagent-results/result.md"
    task_rows = [
        {"task_id": "task_x", "timestamp": "20", "artifact_refs": [artifact_ref]},
        {"task_id": "task_x", "timestamp": "10", "artifact_refs": []},
        {"task_id": "task_y", "timestamp": "bad", "artifact_refs": []},
    ]

    assert governance.subagent_result_artifact_ref(["artifact://other.md", artifact_ref]) == artifact_ref
    assert governance.subagent_result_artifact_ref("not-list") == ""
    assert governance.subagent_result_body_from_text("# Agent result\n\nTask: task_x\n\nbody\nline") == "body\nline"
    assert governance.subagent_result_body_from_text("plain body") == "plain body"
    assert governance.subagent_name_from_task_row({"title": "子 agent 执行: Coder"}) == "Coder"
    assert governance.subagent_name_from_task_row(
        {"assigned_agent": "agent-coder"},
        agent_name_lookup=lambda agent_id: "Coder Meta" if agent_id == "agent-coder" else "",
    ) == "Coder Meta"
    assert governance.subagent_result_task_first_timestamps(
        task_rows,
        timestamp_parser=lambda value: float(value) if value.isdigit() else 0.0,
    ) == {"task_x": 10.0}
    assert governance.completed_subagent_result_row({
        "status": "completed",
        "kind": "subagent_task",
        "artifact_refs": [artifact_ref],
    })
    assert not governance.completed_subagent_result_row({"status": "completed", "artifact_refs": []})

    harness = tmp_path / "agent_harness"
    artifact_path = harness / "artifacts" / "subagent-results" / "result.md"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text("# Agent result\n\nTask: task_x\n\nwrapped body\n", encoding="utf-8")
    subagents_dir = tmp_path / "subagents"
    meta_path = subagents_dir / "agent-coder" / "meta.json"
    meta_path.parent.mkdir(parents=True)
    meta_path.write_text(json.dumps({"name": "Coder From Disk"}), encoding="utf-8")

    monkeypatch.setattr(app_module, "AGENT_HARNESS_DIR", str(harness))
    monkeypatch.setattr(app_module, "SUBAGENTS_DIR", str(subagents_dir))
    monkeypatch.setattr(app_module, "TEMP_SUBAGENTS_DIR", str(tmp_path / "temp-subagents"))

    assert app_module.subagent_result_artifact_ref(["artifact://other.md", artifact_ref]) == artifact_ref
    assert app_module.subagent_result_body_from_artifact(artifact_ref) == "wrapped body"
    assert app_module.subagent_name_from_task_row({"assigned_agent": "agent-coder"}) == "Coder From Disk"
    assert app_module.subagent_result_task_first_timestamps(
        [{"task_id": "task_x", "timestamp": "2026-07-01T00:00:05"}],
    )["task_x"] > 0
    assert app_module.completed_subagent_result_row({
        "status": "completed",
        "assigned_agent": "agent-coder",
        "artifact_refs": [artifact_ref],
    })


def test_progress_approval_artifact_and_trace_round_trip(tmp_path: Path) -> None:
    harness = tmp_path / "agent_harness"
    artifacts_dir = harness / "artifacts"
    progress_path = harness / "progress.jsonl"
    approvals_path = harness / "approvals.jsonl"
    artifact_index_path = harness / "artifacts.jsonl"
    traces_path = harness / "traces.jsonl"

    progress = governance.append_progress_ledger(
        str(progress_path),
        {
            "task_id": "task_governance",
            "status": "working",
            "assigned_agent": "agent_test",
            "summary": "started",
            "artifact_refs": ["artifact://existing.md"],
        },
    )
    assert progress["schema_version"] == "agentprogress.v1"
    assert read_jsonl(str(progress_path))[0]["task_id"] == "task_governance"

    mailed: list[dict[str, object]] = []
    approval_id = governance.queue_approval(
        str(approvals_path),
        approval_type="policy_approval_request",
        summary="approve deploy",
        payload={"task_id": "task_governance"},
        source="orchestrator.main",
        target="ops",
        approval_required_for="deploy",
        mail_callback=mailed.append,
    )
    assert approval_id.startswith("appr_")
    assert mailed and mailed[0]["approval_id"] == approval_id
    assert governance.approval_latest_records(str(approvals_path))[approval_id]["status"] == "pending"

    artifact_ref = governance.write_harness_artifact(
        str(artifacts_dir),
        str(harness),
        str(artifact_index_path),
        "subagent-results",
        "Task Governance",
        "result body",
        source_task_id="task_governance",
    )
    artifact_rows = read_jsonl(str(artifact_index_path))
    assert artifact_ref.startswith("artifact://artifacts/subagent-results/")
    assert artifact_rows[-1]["uri"] == artifact_ref
    assert artifact_rows[-1]["hash"].startswith("sha256:")

    trace = governance.append_trace(
        str(traces_path),
        "task_governance",
        "approval_waiting",
        agent_id="agent_test",
        status="approval_required",
        payload={"approval_id": approval_id, "artifact_ref": artifact_ref},
    )
    assert trace["audit_refs"]["approvals"] == [approval_id]
    assert trace["metrics"]["artifact_refs_delta"] == 1

    refs = governance.collect_task_audit_refs(
        {
            "traces": str(traces_path),
            "artifacts": str(artifact_index_path),
            "messages": str(harness / "messages.jsonl"),
            "approvals": str(approvals_path),
            "memory_candidates": str(harness / "memory_candidates.jsonl"),
            "orchestrator_plans": str(harness / "orchestrator_plans.jsonl"),
        },
        "task_governance",
    )
    assert artifact_ref in refs["artifacts"]
    assert approval_id in refs["approvals"]
    assert trace["trace_id"] in refs["traces"]


def test_single_writer_lock_round_trip(tmp_path: Path) -> None:
    locks_path = str(tmp_path / "locks.json")

    ok, error = governance.acquire_single_writer_lock(
        locks_path,
        task_id="task_a",
        agent_id="coder-a",
        agent_name="Coder A",
        role="coder",
        objective="write the fix",
        is_write_role=True,
        latest_tasks={},
    )
    assert ok and not error

    ok, error = governance.acquire_single_writer_lock(
        locks_path,
        task_id="task_b",
        agent_id="coder-b",
        agent_name="Coder B",
        role="coder",
        is_write_role=True,
        latest_tasks={"task_a": {"status": "working"}},
    )
    assert not ok
    assert "coder-a" in error

    assert governance.release_single_writer_lock(locks_path, "task_a")
    assert governance.current_writer_lock(locks_path) is None


def test_app_wrappers_use_retargeted_paths(tmp_path: Path, monkeypatch) -> None:
    harness = tmp_path / "agent_harness"
    monkeypatch.setattr(app_module, "AGENT_HARNESS_DIR", str(harness))
    monkeypatch.setattr(app_module, "AGENT_ARTIFACTS_DIR", str(harness / "artifacts"))
    monkeypatch.setattr(app_module, "AGENT_ARTIFACT_INDEX_PATH", str(harness / "artifacts.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_PROGRESS_LEDGER_PATH", str(harness / "progress.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_LOCKS_PATH", str(harness / "locks.json"))

    artifact_ref = app_module.write_harness_artifact("wrapper", "result", "body", source_task_id="task_wrapper")
    assert artifact_ref.startswith("artifact://artifacts/wrapper/")
    assert read_jsonl(str(harness / "artifacts.jsonl"))[-1]["source_task_id"] == "task_wrapper"

    app_module.append_progress_ledger({"task_id": "task_wrapper", "status": "completed"})
    assert read_jsonl(str(harness / "progress.jsonl"))[-1]["status"] == "completed"

    sub = SubAgentRuntime(agent_id="coder-wrapper", name="Coder Wrapper", home=str(tmp_path), role="coder")
    monkeypatch.setattr(app_module, "AGENT_TASK_LEDGER_PATH", str(harness / "tasks.jsonl"))
    assert app_module.acquire_single_writer_lock(sub, "task_wrapper", "objective")[0]
    assert os.path.exists(harness / "locks.json")
