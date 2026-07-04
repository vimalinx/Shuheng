"""Tests for low-level governance ledger helpers."""
from __future__ import annotations

import json
import os
from pathlib import Path

from shuheng import app as app_module
from shuheng import governance
from shuheng.ledger_store import append_jsonl, read_jsonl
from shuheng.ui_types import PolicyDecision, SubAgentRuntime


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


def test_checkpoint_recovery_read_model_helpers(tmp_path: Path, monkeypatch) -> None:
    checkpoint_index_path = str(tmp_path / "checkpoints.jsonl")
    recovery_path = str(tmp_path / "recovery.jsonl")
    recovery_plans_path = str(tmp_path / "recovery_plans.jsonl")
    snapshot_old = tmp_path / "snapshot-old.json"
    snapshot_new = tmp_path / "snapshot-new.json"
    snapshot_bad = tmp_path / "snapshot-bad.json"
    snapshot_list = tmp_path / "snapshot-list.json"
    snapshot_old.write_text(json.dumps({"task": {"task_id": "task_a"}, "status": "working"}), encoding="utf-8")
    snapshot_new.write_text(json.dumps({"task": {"task_id": "task_a"}, "status": "failed"}), encoding="utf-8")
    snapshot_bad.write_text("{bad json", encoding="utf-8")
    snapshot_list.write_text("[]", encoding="utf-8")

    append_jsonl(checkpoint_index_path, {
        "checkpoint_id": "ckpt_old",
        "task_id": "task_a",
        "timestamp": "2026-07-01T00:00:01",
        "path": str(snapshot_old),
    })
    append_jsonl(checkpoint_index_path, {
        "checkpoint_id": "ckpt_latest",
        "task_id": "task_a",
        "timestamp": "2026-07-01T00:00:05",
        "path": str(snapshot_new),
    })
    append_jsonl(checkpoint_index_path, {
        "checkpoint_id": "ckpt_other",
        "task_id": "task_b",
        "timestamp": "2026-07-01T00:00:09",
        "path": str(snapshot_new),
    })
    append_jsonl(recovery_path, {"recovery_id": "recovery_a", "task_id": "task_a", "action": "retry"})
    append_jsonl(recovery_path, {"recovery_id": "recovery_b", "task_id": "task_b", "action": "failed"})
    append_jsonl(recovery_plans_path, {"recovery_plan_id": "recoveryplan_a", "task_id": "task_a"})
    append_jsonl(recovery_plans_path, {"recovery_plan_id": "recoveryplan_b", "task_id": "task_b"})

    history = governance.checkpoint_history(checkpoint_index_path, "task_a")
    assert [row["checkpoint_id"] for row in history] == ["ckpt_old", "ckpt_latest"]
    assert governance.checkpoint_index_by_id(checkpoint_index_path, "ckpt_latest")["task_id"] == "task_a"
    assert governance.checkpoint_index_by_id(checkpoint_index_path, "missing") == {}
    assert governance.latest_checkpoint_for_task(checkpoint_index_path, "task_a")["checkpoint_id"] == "ckpt_latest"
    assert governance.latest_checkpoint_for_task(checkpoint_index_path, "missing") == {}
    assert governance.recovery_history(recovery_path, "task_a")[0]["recovery_id"] == "recovery_a"
    assert governance.recovery_plan_history(recovery_plans_path, "task_a")[0]["recovery_plan_id"] == "recoveryplan_a"
    assert governance.read_checkpoint_snapshot({"path": str(snapshot_new)})["status"] == "failed"
    assert governance.read_checkpoint_snapshot({"path": str(snapshot_bad)}) == {}
    assert governance.read_checkpoint_snapshot({"path": str(snapshot_list)}) == {}
    assert governance.read_checkpoint_snapshot({}) == {}

    retry_steps = governance.recovery_replay_steps("retry")
    assert retry_steps[0]["step"] == "validate_checkpoint_hash"
    assert any(step["step"] == "restart_assigned_agent" for step in retry_steps)
    assert governance.recovery_replay_steps("unknown")[-1]["step"] == "manual_review"

    monkeypatch.setattr(app_module, "AGENT_CHECKPOINT_INDEX_PATH", checkpoint_index_path)
    monkeypatch.setattr(app_module, "AGENT_RECOVERY_PATH", recovery_path)
    monkeypatch.setattr(app_module, "AGENT_RECOVERY_PLANS_PATH", recovery_plans_path)
    assert app_module.checkpoint_history("task_a") == history
    assert app_module.latest_checkpoint_for_task("task_a")["checkpoint_id"] == "ckpt_latest"
    assert app_module.checkpoint_index_by_id("ckpt_old")["path"] == str(snapshot_old)
    assert app_module.recovery_history("task_a")[0]["recovery_id"] == "recovery_a"
    assert app_module.recovery_plan_history("task_a")[0]["recovery_plan_id"] == "recoveryplan_a"
    assert app_module.read_checkpoint_snapshot({"path": str(snapshot_old)})["status"] == "working"
    assert app_module.recovery_replay_steps("release_lock")[-1]["step"] == "release_owned_writer_lock"


def test_task_display_helpers_and_app_wrappers() -> None:
    assert governance.task_status_marker("completed") == "✓"
    assert governance.task_status_marker("failed") == "✕"
    assert governance.task_status_marker("working") == "●"
    assert governance.task_status_marker("whatever", approval="pending") == "?"
    assert governance.task_status_marker("whatever") == "○"

    subagent_row = {"kind": "subagent_task", "assigned_agent": "worker"}
    agent_owner_row = {"assigned_agent": "agent-reader"}
    normal_row = {"kind": "task", "assigned_agent": "human"}
    assert governance.row_looks_like_subagent_task(subagent_row, "worker")
    assert governance.row_looks_like_subagent_task(agent_owner_row, "agent-reader")
    assert not governance.row_looks_like_subagent_task(normal_row, "human")

    assert governance.task_display_title({"title": "Explicit"}) == "Explicit"
    assert governance.task_display_title({"display_title": "Display"}) == "Display"
    assert governance.task_display_title({"task_title": "Task Title"}) == "Task Title"
    assert governance.task_display_title(
        {"kind": "subagent_task", "assigned_agent": "agent-reader"},
        owner_name="Reader",
    ) == "子 agent 任务: Reader"
    assert governance.task_display_title({"objective": "Objective text"}) == "Objective text"
    assert governance.task_display_title({"summary": "Summary text"}) == "Summary text"
    assert governance.task_display_title({"error": "Error text"}) == "Error text"
    assert governance.task_display_title({"task_id": "task_fallback"}) == "task_fallback"
    assert governance.task_display_title({}) == "任务"

    state = app_module.State(agent=object())
    state.subagents["agent-reader"] = SubAgentRuntime(
        agent_id="agent-reader",
        name="Reader Runtime",
        home="",
        role="researcher",
    )
    assert app_module.task_status_marker("completed") == governance.task_status_marker("completed")
    assert app_module.row_looks_like_subagent_task(agent_owner_row, "agent-reader")
    assert app_module.task_display_title(
        {"kind": "subagent_task", "assigned_agent": "agent-reader"},
        state,
    ) == "子 agent 任务: Reader Runtime"


def test_selected_plan_id_from_rows_and_app_wrapper() -> None:
    rows = [
        ("note_latest", {"kind": "task", "status": "working", "ts": 999.0}),
        ("plan_done_newest", {"kind": "plan", "status": "completed", "ts": 30.0}),
        ("plan_active_old", {"kind": "plan", "status": "working", "ts": 10.0}),
        ("plan_active_new", {"kind": "plan", "status": "pending", "ts": 20.0}),
    ]

    assert governance.selected_plan_id_from_rows(rows, "plan_done_newest") == "plan_done_newest"
    assert governance.selected_plan_id_from_rows(rows) == "plan_active_new"
    assert governance.selected_plan_id_from_rows(rows, require_active=True) == "plan_active_new"
    assert governance.selected_plan_id_from_rows([
        ("task_only", {"kind": "task", "status": "working", "ts": 100.0}),
    ]) == ""

    terminal_rows = [
        ("not_plan", {"kind": "task", "status": "working", "ts": 100.0}),
        ("plan_done_old", {"kind": "plan", "status": "completed", "ts": 5.0}),
        ("plan_failed_new", {"kind": "plan", "status": "failed", "ts": 15.0}),
    ]
    assert governance.selected_plan_id_from_rows(terminal_rows, require_active=True) == ""
    assert governance.selected_plan_id_from_rows(terminal_rows) == "plan_failed_new"

    assert app_module.selected_plan_id_from_rows(rows, "plan_active_old") == (
        governance.selected_plan_id_from_rows(rows, "plan_active_old")
    )
    assert app_module.selected_plan_id_from_rows(terminal_rows, require_active=True) == ""


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
