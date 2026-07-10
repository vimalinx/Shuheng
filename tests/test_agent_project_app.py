from __future__ import annotations

import base64
import json
from pathlib import Path
import queue
from typing import Any

import pytest

from shuheng import agent_projects
from shuheng import app as app_module


def _create_project_with_authority_requests(projects_root: Path, project_id: str) -> tuple[Path, str]:
    created = agent_projects.create_agent_project(
        projects_root,
        project_id=project_id,
        name="Local Tool Worker",
        runtime_version="0.80.6",
    )
    assert created.ok and created.value is not None
    project_root = projects_root / project_id
    source_marker = "FROZEN_AGENT_SOURCE_MUST_STAY_TRANSIENT"
    (project_root / "tools" / "local-inspect.ts").write_text(
        f"export const marker = {source_marker!r};\n",
        encoding="utf-8",
    )
    (project_root / "prompts" / "system.md").write_text(
        f"# Worker\n\n{source_marker}\n",
        encoding="utf-8",
    )
    blueprint_path = project_root / "agent.json"
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    blueprint["requested_capabilities"] = ["repo.read"]
    blueprint["tools"] = [
        {
            "id": "local-inspect",
            "path": "tools/local-inspect.ts",
            "requested_capabilities": ["repo.read"],
        }
    ]
    blueprint_path.write_text(
        json.dumps(blueprint, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return project_root, source_marker


def test_local_agent_project_resolution_and_listing_stay_inside_managed_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    projects_root = tmp_path / "agent-projects"
    monkeypatch.setattr(app_module, "SHUHENG_AGENT_PROJECTS_DIR", str(projects_root))
    for project_id in ("zeta", "alpha"):
        created = agent_projects.create_agent_project(projects_root, project_id=project_id)
        assert created.ok

    outside = tmp_path / "outside-project"
    outside_created = agent_projects.create_agent_project(tmp_path, project_id=outside.name)
    assert outside_created.ok
    (projects_root / "outside-link").symlink_to(outside, target_is_directory=True)
    (projects_root / ".hidden").mkdir()
    (projects_root / ".hidden" / agent_projects.PROJECT_MANIFEST_NAME).write_text("{}\n", encoding="utf-8")
    (projects_root / "no-manifest").mkdir()

    roots = app_module.local_agent_project_roots()

    assert [Path(root).name for root in roots] == ["alpha", "zeta"]
    assert app_module.agent_project_root_for_id("alpha") == str((projects_root / "alpha").resolve())
    assert app_module.agent_project_root_for_id("../outside-project") == ""
    assert app_module.agent_project_root_for_id(str(outside)) == ""
    assert app_module.agent_project_root_for_id("outside-link") == ""


def test_app_helpers_create_fork_and_build_local_agent_projects(
    tmp_path: Path,
    monkeypatch,
) -> None:
    projects_root = tmp_path / "agent-projects"
    monkeypatch.setattr(app_module, "SHUHENG_AGENT_PROJECTS_DIR", str(projects_root))

    created_message = app_module.create_local_agent_project("writer", "Writer")
    forked_message = app_module.fork_local_agent_project("writer", "writer-copy", "Writer Copy")
    build, build_message = app_module.build_local_agent_project("writer-copy")

    assert "已创建 Agent Project：writer" in created_message
    assert "已 Fork Agent Project：writer → writer-copy" == forked_message
    assert build is not None
    assert build.project.project_id == "writer-copy"
    assert build.project.name == "Writer Copy"
    assert build.runtime == "pi-native"
    assert f"Build 成功：writer-copy · {build.digest}" in build_message
    inventory = app_module.agent_project_inventory_text()
    assert "Agent Projects: 2" in inventory
    assert "- writer · Writer · pi-native" in inventory
    assert "- writer-copy · Writer Copy · pi-native" in inventory


def test_run_local_agent_project_requires_explicit_declared_authority_grant(
    tmp_path: Path,
    monkeypatch,
) -> None:
    projects_root = tmp_path / "agent-projects"
    monkeypatch.setattr(app_module, "SHUHENG_AGENT_PROJECTS_DIR", str(projects_root))
    _create_project_with_authority_requests(projects_root, "tool-worker")
    prepared: list[Any] = []
    dispatched: list[tuple[Any, Any, str, dict[str, Any]]] = []
    worker = object()

    def fake_agent_project_subagent(state: Any, build: Any) -> object:
        prepared.append((state, build))
        return worker

    def fake_start_subagent_task(state: Any, sub: Any, objective: str, **kwargs: Any) -> str:
        dispatched.append((state, sub, objective, kwargs))
        return "已派发 task-safe"

    monkeypatch.setattr(app_module, "agent_project_subagent", fake_agent_project_subagent)
    monkeypatch.setattr(app_module, "start_subagent_task", fake_start_subagent_task)
    state = app_module.State(agent=None)

    denied = app_module.run_local_agent_project(state, "tool-worker", "Inspect the repository")

    assert "尚未获得运行授权" in denied
    assert "--grant-declared" in denied
    assert prepared == []
    assert dispatched == []

    approved = app_module.run_local_agent_project(
        state,
        "tool-worker",
        "Inspect the repository",
        grant_declared=True,
    )

    assert "Build 成功：tool-worker" in approved
    assert "已派发 task-safe" in approved
    assert len(prepared) == 1
    assert len(dispatched) == 1
    dispatched_state, dispatched_worker, dispatched_objective, dispatched_kwargs = dispatched[0]
    assert dispatched_state is state
    assert dispatched_worker is worker
    assert dispatched_objective == "Inspect the repository"
    assert dispatched_kwargs == {
        "source": "user:agent_project:approved",
        "policy_approved": False,
        "task_title": "Agent Project: tool-worker",
        "expected_build_digest": prepared[0][1].digest,
        "agent_project_grant_declared": True,
    }


def test_prepare_runtime_envelope_persists_manifest_refs_but_keeps_build_source_transient(
    tmp_path: Path,
    monkeypatch,
) -> None:
    projects_root = tmp_path / "agent-projects"
    project_root, source_marker = _create_project_with_authority_requests(projects_root, "safe-worker")
    compiled = agent_projects.compile_agent_project(project_root)
    assert compiled.ok and compiled.build is not None
    build = compiled.build
    workspace = tmp_path / "workspace"
    artifact_ref = "artifact://agent_project_runs/task-safe.json"
    written: dict[str, Any] = {}

    def fake_write_harness_artifact(
        category: str,
        name: str,
        content: str,
        **kwargs: Any,
    ) -> str:
        written.update(category=category, name=name, content=content, kwargs=kwargs)
        return artifact_ref

    monkeypatch.setattr(app_module, "current_workspace_root", lambda: str(workspace))
    monkeypatch.setattr(app_module, "write_harness_artifact", fake_write_harness_artifact)
    monkeypatch.setattr(app_module, "pi_native_model_runtime_payload", lambda: {})

    runtime_payload, manifest_ref, durable_metadata = app_module.prepare_agent_project_runtime_envelope(
        build,
        assignment_id="task-safe",
        grant_declared=True,
        causation_refs=["approval:approval-safe", "policy:policy-safe"],
    )

    assert manifest_ref == artifact_ref
    assert durable_metadata == {
        "agent_project_id": "safe-worker",
        "agent_build_digest": build.digest,
        "agent_run_manifest_ref": artifact_ref,
    }
    assert set(runtime_payload) == {"agent_build", "agent_run_manifest"}
    assert runtime_payload["agent_build"] == build.to_record()
    manifest = runtime_payload["agent_run_manifest"]
    assert manifest["build_digest"] == build.digest
    assert manifest["causation_refs"] == ["approval:approval-safe", "policy:policy-safe"]
    assert manifest["capabilities"]["effective"] == ["repo.read"]
    assert manifest["tools"]["effective"] == ["local-inspect"]

    persisted_manifest = json.loads(written["content"])
    assert persisted_manifest == manifest
    assert written["category"] == "agent_project_runs"
    assert written["name"] == "task-safe.json"
    assert written["kwargs"] == {
        "source_task_id": "task-safe",
        "provenance": {
            "generated_by": "orchestrator.main",
            "project_id": "safe-worker",
            "build_digest": build.digest,
            "provider_id": "pi-native",
        },
        "content_type": "application/json",
    }

    prompt_file = next(
        item for item in runtime_payload["agent_build"]["files"] if item["path"] == "prompts/system.md"
    )
    assert source_marker in base64.b64decode(prompt_file["content_base64"]).decode("utf-8")
    persisted_text = json.dumps(
        {"artifact": persisted_manifest, "metadata": durable_metadata},
        ensure_ascii=False,
        sort_keys=True,
    )
    assert source_marker not in persisted_text
    assert "content_base64" not in persisted_text
    assert str(project_root.resolve()) not in persisted_text


def test_pi_native_agent_project_blocks_unledgered_direct_chat(tmp_path: Path, monkeypatch) -> None:
    state = app_module.State(agent=None)
    sub = app_module.SubAgentRuntime(
        agent_id="pi-worker",
        name="Pi Worker",
        home=str(tmp_path / "pi-worker"),
        runtime_provider_id="pi-native",
        agent_project_id="safe-worker",
    )
    monkeypatch.setattr(app_module, "save_subagent_meta", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "save_subagent_chat_session", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "mark_subagent_messages_changed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "append_subagent_event", lambda *_args, **_kwargs: None)

    message = app_module.start_subagent_chat(state, sub, "bypass the task ledger")

    assert "不开放无账本的直接聊天" in message
    assert "/agent-project run" in message
    assert sub.agent is None
    assert sub.status == "error"


def test_agent_project_run_confirmation_is_bound_to_one_build_digest(tmp_path: Path, monkeypatch) -> None:
    projects_root = tmp_path / "agent-projects"
    monkeypatch.setattr(app_module, "SHUHENG_AGENT_PROJECTS_DIR", str(projects_root))
    project_root, _marker = _create_project_with_authority_requests(projects_root, "digest-bound")
    confirmed = agent_projects.compile_agent_project(project_root)
    assert confirmed.ok and confirmed.build is not None
    (project_root / "prompts" / "system.md").write_text("# Changed after confirmation\n", encoding="utf-8")
    monkeypatch.setattr(
        app_module,
        "agent_project_subagent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not prepare a worker")),
    )

    message = app_module.run_local_agent_project(
        app_module.State(agent=None),
        "digest-bound",
        "Inspect",
        grant_declared=True,
        expected_build_digest=confirmed.build.digest,
    )

    assert "确认后发生了变化" in message
    assert confirmed.build.digest in message
    assert "请重新查看权限" in message


def test_queued_agent_project_task_keeps_its_own_build_digest(tmp_path: Path, monkeypatch) -> None:
    state = app_module.State(agent=None)
    sub = app_module.SubAgentRuntime(
        agent_id="pi-queue",
        name="Pi Queue",
        home=str(tmp_path / "pi-queue"),
        runtime_provider_id="pi-native",
        agent_project_id="queued-project",
        agent_build_digest="active-build",
        status="running",
    )
    state.subagents[sub.agent_id] = sub
    monkeypatch.setattr(app_module, "save_subagent_meta", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "append_subagent_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "mark_dirty", lambda *_args, **_kwargs: None)
    captured: dict[str, Any] = {}

    assert "已排队" in app_module.queue_subagent_task(
        state,
        sub,
        "queued objective",
        source="user:agent_project:approved",
        expected_build_digest="queued-build",
        agent_project_grant_declared=True,
        approved_policy={
            "approval_id": "approval-queued",
            "original_task_id": "task-queued",
        },
    )
    assert sub.agent_build_digest == "active-build"
    sub.status = "idle"
    monkeypatch.setattr(
        app_module,
        "start_subagent_task",
        lambda *_args, **kwargs: captured.update(kwargs) or "started",
    )

    assert app_module.maybe_start_next_subagent_task(state, sub) == "started"
    assert captured["expected_build_digest"] == "queued-build"
    assert captured["agent_project_grant_declared"] is True
    assert captured["source"] == "user:agent_project:approved"
    assert captured["approved_policy"] == {
        "approval_id": "approval-queued",
        "original_task_id": "task-queued",
    }


def test_busy_agent_project_dispatch_queues_without_losing_authority_token(tmp_path: Path, monkeypatch) -> None:
    state = app_module.State(agent=None)
    sub = app_module.SubAgentRuntime(
        agent_id="pi-busy",
        name="Pi Busy",
        home=str(tmp_path / "pi-busy"),
        role="coder",
        runtime_provider_id="pi-native",
        agent_project_id="busy-project",
        status="running",
    )
    captured: dict[str, Any] = {}
    queued_plans: list[dict[str, Any]] = []
    queued_ledgers: list[dict[str, Any]] = []
    queued_checkpoints: list[dict[str, Any]] = []
    queued_traces: list[dict[str, Any]] = []
    monkeypatch.setattr(app_module, "record_shared_user_profile_interaction", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        app_module,
        "queue_subagent_task",
        lambda *_args, **kwargs: captured.update(kwargs) or "queued",
    )
    monkeypatch.setattr(
        app_module,
        "append_orchestrator_plan",
        lambda _sub, _objective, task_id, **kwargs: queued_plans.append({"task_id": task_id, **kwargs}) or {},
    )
    monkeypatch.setattr(
        app_module,
        "append_task_ledger",
        lambda task_id, **kwargs: queued_ledgers.append({"task_id": task_id, **kwargs}) or {},
    )
    monkeypatch.setattr(app_module, "update_plan_step_from_child", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        app_module,
        "append_task_checkpoint",
        lambda task_id, **kwargs: queued_checkpoints.append({"task_id": task_id, **kwargs})
        or {"checkpoint_id": "checkpoint-queued"},
    )
    monkeypatch.setattr(
        app_module,
        "append_trace",
        lambda task_id, event, **kwargs: queued_traces.append({"task_id": task_id, "event": event, **kwargs}) or {},
    )

    result = app_module.start_subagent_task(
        state,
        sub,
        "Use the granted Tool",
        source="user:agent_project:approved",
        expected_build_digest="a" * 64,
        agent_project_grant_declared=True,
        policy_approved=True,
        approved_policy={
            "approval_id": "approval-busy",
            "original_task_id": "task-busy",
        },
    )

    assert result == "queued"
    assert captured["expected_build_digest"] == "a" * 64
    assert captured["agent_project_grant_declared"] is True
    assert captured["approved_policy"] == {
        "approval_id": "approval-busy",
        "original_task_id": "task-busy",
    }
    assert "action_override" not in captured
    assert queued_plans[-1]["task_id"] == "task-busy"
    assert queued_plans[-1]["status"] == "queued"
    assert queued_plans[-1]["approval"]["approval_status"] == "approved"
    assert queued_ledgers[-1]["task_id"] == "task-busy"
    assert queued_ledgers[-1]["title"] == "Agent Project: busy-project"
    assert queued_ledgers[-1]["approval"] == queued_plans[-1]["approval"]
    assert queued_checkpoints[-1]["reason"] == "approved_subagent_task_queued"
    assert queued_traces[-1]["event"] == "approved_subagent_task_queued"


def test_policy_approval_resumes_original_task_and_links_run_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    projects_root = tmp_path / "agent-projects"
    monkeypatch.setattr(app_module, "SHUHENG_AGENT_PROJECTS_DIR", str(projects_root))
    project_root, _marker = _create_project_with_authority_requests(projects_root, "approval-linked")
    compiled = agent_projects.compile_agent_project(project_root)
    assert compiled.ok and compiled.build is not None
    state = app_module.State(agent=None)
    sub = app_module.SubAgentRuntime(
        agent_id="pi-approved",
        name="Pi Approved",
        home=str(tmp_path / "pi-approved"),
        role="coder",
        runtime_provider_id="pi-native",
        agent_project_id="approval-linked",
        agent_project_root=str(project_root.resolve()),
    )
    captured: dict[str, Any] = {}
    plans: list[dict[str, Any]] = []
    ledgers: list[dict[str, Any]] = []
    checkpoints: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    def fake_prepare(
        _build: Any,
        *,
        assignment_id: str,
        grant_declared: bool,
        causation_refs: list[str],
    ) -> tuple[dict[str, Any], str, dict[str, Any]]:
        captured.update(
            assignment_id=assignment_id,
            grant_declared=grant_declared,
            causation_refs=causation_refs,
        )
        raise RuntimeError("stop after provenance capture")

    monkeypatch.setattr(app_module, "record_shared_user_profile_interaction", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "prepare_agent_project_runtime_envelope", fake_prepare)
    monkeypatch.setattr(
        app_module,
        "append_orchestrator_plan",
        lambda _sub, _objective, task_id, **kwargs: plans.append({"task_id": task_id, **kwargs}) or {},
    )
    monkeypatch.setattr(
        app_module,
        "append_task_ledger",
        lambda task_id, **kwargs: ledgers.append({"task_id": task_id, **kwargs}) or {},
    )
    monkeypatch.setattr(app_module, "update_plan_step_from_child", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        app_module,
        "append_task_checkpoint",
        lambda task_id, **kwargs: checkpoints.append({"task_id": task_id, **kwargs})
        or {"checkpoint_id": "checkpoint-preflight"},
    )
    monkeypatch.setattr(
        app_module,
        "append_trace",
        lambda task_id, event, **kwargs: traces.append({"task_id": task_id, "event": event, **kwargs}) or {},
    )

    message = app_module.start_subagent_task(
        state,
        sub,
        "Run the approved frozen Build",
        source="user:agent_project:approved",
        policy_approved=True,
        expected_build_digest=compiled.build.digest,
        agent_project_grant_declared=True,
        approved_policy={
            "approval_id": "approval-123",
            "policy_decision_id": "policy-456",
            "policy_action": "repo_write",
            "approval_required_for": "repository write",
            "original_task_id": "task-original",
        },
    )

    assert "stop after provenance capture" in message
    assert captured == {
        "assignment_id": "task-original",
        "grant_declared": True,
        "causation_refs": ["approval:approval-123", "policy:policy-456"],
    }
    assert plans[-1]["task_id"] == "task-original"
    assert plans[-1]["status"] == "failed"
    assert plans[-1]["approval"]["approval_status"] == "approved"
    assert plans[-1]["approval"]["approval_id"] == "approval-123"
    assert plans[-1]["action_override"] == "repo_write"
    assert ledgers[-1]["task_id"] == "task-original"
    assert ledgers[-1]["status"] == "failed"
    assert ledgers[-1]["approval"] == plans[-1]["approval"]
    assert checkpoints[-1]["task_id"] == "task-original"
    assert checkpoints[-1]["reason"] == "agent_project_run_manifest_failed"
    assert checkpoints[-1]["extra"]["approval_id"] == "approval-123"
    assert traces[-1]["task_id"] == "task-original"
    assert traces[-1]["event"] == "agent_project_run_manifest_failed"
    assert traces[-1]["payload"]["policy_decision_id"] == "policy-456"


def test_orchestrator_plan_keeps_resumed_approval_and_policy_action(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sub = app_module.SubAgentRuntime(
        agent_id="pi-plan",
        name="Pi Plan",
        home=str(tmp_path / "pi-plan"),
        role="coder",
        runtime_provider_id="pi-native",
        agent_project_id="plan-project",
    )
    rows: list[dict[str, Any]] = []
    monkeypatch.setattr(app_module, "append_jsonl", lambda _path, row: rows.append(row))
    approval = {
        "approval_required_for": ["repository write"],
        "approval_status": "approved",
        "approval_id": "approval-plan",
        "policy_decision_id": "policy-plan",
        "policy_action": "repo_write",
    }

    row = app_module.append_orchestrator_plan(
        sub,
        "Run the approved Build",
        "task-plan",
        status="working",
        source="approved_policy",
        approval=approval,
        action_override="repo_write",
    )

    assert rows[-1] == row
    assert row["approval"] == approval
    assert row["delegation_contract"]["approval"] == approval
    assert row["routing_decision"]["policy_action"] == "repo_write"


def test_approved_build_failure_redacts_mutable_project_path_from_durable_rows(
    tmp_path: Path,
    monkeypatch,
) -> None:
    projects_root = tmp_path / "agent-projects"
    monkeypatch.setattr(app_module, "SHUHENG_AGENT_PROJECTS_DIR", str(projects_root))
    project_root, _marker = _create_project_with_authority_requests(projects_root, "redacted-build")
    confirmed = agent_projects.compile_agent_project(project_root)
    assert confirmed.ok and confirmed.build is not None
    (project_root / "prompts" / "system.md").unlink()
    sub = app_module.SubAgentRuntime(
        agent_id="pi-redacted",
        name="Pi Redacted",
        home=str(tmp_path / "pi-redacted"),
        role="coder",
        runtime_provider_id="pi-native",
        agent_project_id="redacted-build",
        agent_project_root=str(project_root.resolve()),
    )
    durable_rows: list[dict[str, Any]] = []
    monkeypatch.setattr(app_module, "record_shared_user_profile_interaction", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        app_module,
        "append_orchestrator_plan",
        lambda _sub, _objective, task_id, **kwargs: durable_rows.append(
            {"surface": "plan", "task_id": task_id, **kwargs}
        )
        or {},
    )
    monkeypatch.setattr(
        app_module,
        "append_task_ledger",
        lambda task_id, **kwargs: durable_rows.append({"surface": "ledger", "task_id": task_id, **kwargs}) or {},
    )
    monkeypatch.setattr(app_module, "update_plan_step_from_child", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        app_module,
        "append_task_checkpoint",
        lambda task_id, **kwargs: durable_rows.append(
            {
                "surface": "checkpoint",
                "task_id": task_id,
                **{key: value for key, value in kwargs.items() if key != "state"},
            }
        )
        or {"checkpoint_id": "checkpoint-redacted"},
    )
    monkeypatch.setattr(
        app_module,
        "append_trace",
        lambda task_id, event, **kwargs: durable_rows.append(
            {"surface": "trace", "task_id": task_id, "event": event, **kwargs}
        )
        or {},
    )

    message = app_module.start_subagent_task(
        app_module.State(agent=None),
        sub,
        "Run the approved frozen Build",
        source="user:agent_project:approved",
        policy_approved=True,
        expected_build_digest=confirmed.build.digest,
        agent_project_grant_declared=True,
        approved_policy={
            "approval_id": "approval-redacted",
            "policy_decision_id": "policy-redacted",
            "policy_action": "repo_write",
            "original_task_id": "task-redacted",
        },
    )

    assert str(project_root.resolve()) in message
    durable_text = json.dumps(durable_rows, ensure_ascii=False, sort_keys=True)
    assert str(project_root.resolve()) not in durable_text
    assert "<agent-project-source>" in durable_text


def test_agent_project_task_lane_requires_confirmed_build_digest(tmp_path: Path, monkeypatch) -> None:
    state = app_module.State(agent=None)
    sub = app_module.SubAgentRuntime(
        agent_id="pi-unconfirmed",
        name="Pi Unconfirmed",
        home=str(tmp_path / "pi-unconfirmed"),
        runtime_provider_id="pi-native",
        agent_project_id="unconfirmed-project",
    )
    monkeypatch.setattr(
        app_module,
        "record_shared_user_profile_interaction",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must fail before dispatch")),
    )

    message = app_module.start_subagent_task(state, sub, "Run mutable current source", source="agent_control")

    assert "缺少已确认 Build digest" in message
    assert "/agent-project run" in message


def test_agent_project_recovery_retry_requires_new_build_confirmation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state = app_module.State(agent=None)
    sub = app_module.SubAgentRuntime(
        agent_id="pi-recovery",
        name="Pi Recovery",
        home=str(tmp_path / "pi-recovery"),
        runtime_provider_id="pi-native",
        agent_project_id="recovery-project",
    )
    state.subagents[sub.agent_id] = sub
    checkpoints: list[dict[str, Any]] = []
    recovery_rows: list[dict[str, Any]] = []
    recovery_plan_calls: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    task_updates: list[dict[str, Any]] = []
    released: list[str] = []
    monkeypatch.setattr(
        app_module,
        "latest_task_records",
        lambda: {
            "task-recovery": {
                "task_id": "task-recovery",
                "status": "working",
                "assigned_agent": sub.agent_id,
                "objective": "Run an old frozen Build",
            }
        },
    )
    monkeypatch.setattr(
        app_module,
        "append_task_checkpoint",
        lambda task_id, **kwargs: checkpoints.append({"task_id": task_id, **kwargs})
        or {"checkpoint_id": f"checkpoint-{len(checkpoints)}"},
    )
    monkeypatch.setattr(
        app_module,
        "append_recovery_plan",
        lambda *_args, **kwargs: recovery_plan_calls.append(kwargs)
        or {
            "recovery_plan_id": "recovery-plan",
            "artifact_refs": ["artifact://recovery-plan"],
        },
    )
    monkeypatch.setattr(
        app_module,
        "release_single_writer_lock",
        lambda task_id: released.append(task_id) or True,
    )
    monkeypatch.setattr(
        app_module,
        "append_task_update",
        lambda task_id, **kwargs: task_updates.append({"task_id": task_id, **kwargs}) or {},
    )
    monkeypatch.setattr(
        app_module,
        "start_subagent_task",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("old Build must not restart")),
    )
    monkeypatch.setattr(
        app_module,
        "append_recovery_record",
        lambda task_id, **kwargs: recovery_rows.append({"task_id": task_id, **kwargs}) or {},
    )
    monkeypatch.setattr(
        app_module,
        "append_trace",
        lambda task_id, event, **kwargs: traces.append({"task_id": task_id, "event": event, **kwargs}) or {},
    )

    result = app_module.recover_task_action(
        state,
        "task-recovery",
        "retry",
        policy_approved=True,
    )

    assert "不能从旧任务 retry" in result
    assert "/agent-project run" in result
    assert released == ["task-recovery"]
    assert task_updates[-1]["task_id"] == "task-recovery"
    assert task_updates[-1]["status"] == "failed"
    assert "不能从旧任务 retry" in task_updates[-1]["error"]
    assert recovery_plan_calls[-1]["replayable"] is False
    assert recovery_plan_calls[-1]["replacement_task_expected"] is False
    assert recovery_plan_calls[-1]["status"] == "approved_non_replayable"
    assert "/agent-project run" in recovery_plan_calls[-1]["non_replayable_reason"]
    assert checkpoints[-1]["reason"] == "agent_project_retry_requires_new_build_confirmation"
    assert recovery_rows[-1]["status"] == "rejected"
    assert traces[-1]["event"] == "agent_project_retry_rejected"


def test_agent_project_recovery_plan_is_explicitly_non_replayable(monkeypatch) -> None:
    artifacts: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    monkeypatch.setattr(
        app_module,
        "read_checkpoint_snapshot",
        lambda _checkpoint: {
            "task": {
                "task_id": "task-non-replayable",
                "status": "working",
                "assigned_agent": "pi-recovery",
                "objective": "Run an old frozen Build",
            }
        },
    )
    monkeypatch.setattr(
        app_module,
        "write_harness_artifact",
        lambda category, name, content, **kwargs: artifacts.append(
            {"category": category, "name": name, "content": content, "kwargs": kwargs}
        )
        or "artifact://recovery-plan/non-replayable",
    )
    monkeypatch.setattr(app_module, "append_jsonl", lambda _path, row: rows.append(row))

    plan = app_module.append_recovery_plan(
        "task-non-replayable",
        action="retry",
        source_checkpoint={
            "checkpoint_id": "checkpoint-source",
            "hash": "sha256:source",
            "status": "working",
        },
        assigned_agent="pi-recovery",
        objective="Run an old frozen Build",
        status="approved_replay",
        replayable=False,
        replacement_task_expected=False,
        non_replayable_reason="Confirm with /agent-project run.",
    )

    assert rows[-1] == plan
    assert plan["replayable"] is False
    assert plan["replay_steps"] == []
    assert plan["state_patch"]["task_status_after_action"] == "failed"
    assert plan["state_patch"]["replacement_task_expected"] is False
    assert plan["state_patch"]["required_user_action"] == "confirm_new_agent_project_build"
    assert plan["non_replayable_reason"] == "Confirm with /agent-project run."
    assert '"replayable": false' in artifacts[-1]["content"]
    assert '"replacement_task_expected": false' in artifacts[-1]["content"]


def test_recovery_recognizes_project_from_durable_manifest_without_live_subagent(monkeypatch) -> None:
    plan_calls: list[dict[str, Any]] = []
    task_updates: list[dict[str, Any]] = []
    recovery_rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    checkpoints: list[dict[str, Any]] = []
    monkeypatch.setattr(
        app_module,
        "latest_task_records",
        lambda: {
            "task-orphaned-project": {
                "task_id": "task-orphaned-project",
                "status": "working",
                "assigned_agent": "missing-pi-worker",
                "objective": "Run the frozen Build",
                "artifact_refs": ["artifact://agent_project_runs/task-orphaned-project.json"],
            }
        },
    )
    monkeypatch.setattr(
        app_module,
        "append_task_checkpoint",
        lambda task_id, **kwargs: checkpoints.append({"task_id": task_id, **kwargs})
        or {"checkpoint_id": f"checkpoint-orphaned-{len(checkpoints)}"},
    )
    monkeypatch.setattr(
        app_module,
        "append_recovery_plan",
        lambda *_args, **kwargs: plan_calls.append(kwargs)
        or {"recovery_plan_id": "plan-orphaned", "artifact_refs": ["artifact://recovery-plan/orphaned"]},
    )
    monkeypatch.setattr(app_module, "release_single_writer_lock", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        app_module,
        "append_task_update",
        lambda task_id, **kwargs: task_updates.append({"task_id": task_id, **kwargs}) or {},
    )
    monkeypatch.setattr(
        app_module,
        "append_recovery_record",
        lambda task_id, **kwargs: recovery_rows.append({"task_id": task_id, **kwargs}) or {},
    )
    monkeypatch.setattr(
        app_module,
        "append_trace",
        lambda task_id, event, **kwargs: traces.append({"task_id": task_id, "event": event, **kwargs}) or {},
    )

    result = app_module.recover_task_action(
        app_module.State(agent=None),
        "task-orphaned-project",
        "retry",
        policy_approved=True,
    )

    assert "不能从旧任务 retry" in result
    assert plan_calls[-1]["replayable"] is False
    assert plan_calls[-1]["replacement_task_expected"] is False
    assert plan_calls[-1]["status"] == "approved_non_replayable"
    assert task_updates[-1]["status"] == "failed"
    assert checkpoints[-1]["reason"] == "agent_project_retry_requires_new_build_confirmation"
    assert recovery_rows[-1]["status"] == "rejected"
    assert traces[-1]["event"] == "agent_project_retry_rejected"


def test_agent_project_mvp_rejects_secret_runtime_lane(tmp_path: Path, monkeypatch) -> None:
    projects_root = tmp_path / "agent-projects"
    monkeypatch.setattr(app_module, "SHUHENG_AGENT_PROJECTS_DIR", str(projects_root))
    created = agent_projects.create_agent_project(projects_root, project_id="standard-only")
    assert created.ok
    state = app_module.State(agent=None)
    state.secret_vault.unlocked = True

    message = app_module.run_local_agent_project(state, "standard-only", "Do a bounded task")

    assert "standard 受管任务通道" in message
    assert state.subagents == {}


def test_agent_project_worker_uses_conservative_single_writer_role(tmp_path: Path, monkeypatch) -> None:
    projects_root = tmp_path / "agent-projects"
    created = agent_projects.create_agent_project(projects_root, project_id="writer-governed")
    assert created.ok
    compiled = agent_projects.compile_agent_project(projects_root / "writer-governed")
    assert compiled.ok and compiled.build is not None
    captured: dict[str, Any] = {}
    worker = object()

    def fake_create_subagent(_state: Any, _name: str, **kwargs: Any) -> object:
        captured.update(kwargs)
        return worker

    monkeypatch.setattr(app_module, "create_subagent", fake_create_subagent)

    result = app_module.agent_project_subagent(app_module.State(agent=None), compiled.build)

    assert result is worker
    assert captured["role"] == "coder"
    assert app_module.is_write_role(captured["role"])


def test_granted_agent_project_authority_uses_repo_write_policy_action(tmp_path: Path, monkeypatch) -> None:
    sub = app_module.SubAgentRuntime(
        agent_id="pi-policy",
        name="Pi Policy",
        home=str(tmp_path / "pi-policy"),
        role="coder",
        runtime_provider_id="pi-native",
        agent_project_id="policy-project",
    )
    monkeypatch.setattr(app_module, "record_policy_decision", lambda decision: decision)

    decision = app_module.policy_gate_for_subagent_task(
        sub,
        "Inspect with the authorized local Tool",
        source="user:agent_project:approved",
        bus_task_id="task-policy",
        queue_if_required=False,
        expected_build_digest="b" * 64,
        agent_project_grant_declared=True,
        action_override="repo_write",
    )

    assert decision.action == "repo_write"
    assert decision.allowed is True
    assert app_module.is_write_role(sub.role)


@pytest.mark.parametrize(("terminal_status", "expected_status"), [("failed", "failed"), ("aborted", "aborted")])
def test_pi_terminal_status_is_preserved_in_task_ledger(
    tmp_path: Path,
    monkeypatch,
    terminal_status: str,
    expected_status: str,
) -> None:
    state = app_module.State(agent=None)
    sub = app_module.SubAgentRuntime(
        agent_id="pi-failure",
        name="Pi Failure",
        home=str(tmp_path / "pi-failure"),
        runtime_provider_id="pi-native",
        agent_project_id="failure-project",
        agent_build_digest="c" * 64,
        status="running",
        active_task_id=1,
        active_bus_task_id="task-pi-failure",
        messages=[
            app_module.Message("user", "Run the worker"),
            app_module.Message("assistant", "", done=False),
        ],
    )
    state.subagents[sub.agent_id] = sub
    terminal_queue: queue.Queue = queue.Queue()
    terminal_text = (
        "[Pi Native] 运行失败: provider unavailable"
        if terminal_status == "failed"
        else "[Pi Native] task aborted"
    )
    terminal_queue.put({"done": terminal_text, "status": terminal_status, "error": "provider unavailable"})
    app_module.consume_stream_queue_to_ui(state, "sub_stream", sub.agent_id, 1, terminal_queue)
    ledger_rows: list[dict[str, Any]] = []
    mail_rows: list[dict[str, Any]] = []
    checkpoint_rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    monkeypatch.setattr(app_module, "write_harness_artifact", lambda *_args, **_kwargs: "artifact://failure")
    monkeypatch.setattr(app_module, "save_subagent_meta", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "save_subagent_chat_session", lambda *_args, **_kwargs: (True, "chat://failure"))
    monkeypatch.setattr(app_module, "mark_subagent_messages_changed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "append_subagent_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "release_single_writer_lock", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        app_module,
        "latest_task_records",
        lambda: {
            "task-pi-failure": {
                "task_id": "task-pi-failure",
                "status": "working",
                "title": "Pi failure",
                "artifact_refs": [
                    "artifact://context/task-pi-failure.json",
                    "artifact://agent_project_runs/task-pi-failure.json",
                ],
                "approval": {
                    "approval_required_for": ["repository write"],
                    "approval_status": "approved",
                    "approval_id": "approval-terminal",
                    "policy_decision_id": "policy-terminal",
                    "policy_action": "repo_write",
                },
            }
        },
    )
    monkeypatch.setattr(app_module, "append_orchestrator_plan", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(app_module, "append_task_ledger", lambda task_id, **kwargs: ledger_rows.append({"task_id": task_id, **kwargs}) or {})
    monkeypatch.setattr(app_module, "update_plan_step_from_child", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        app_module,
        "append_agent_mail",
        lambda **kwargs: mail_rows.append(kwargs) or {},
    )
    monkeypatch.setattr(app_module, "add_system", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        app_module,
        "append_task_checkpoint",
        lambda task_id, **kwargs: checkpoint_rows.append({"task_id": task_id, **kwargs})
        or {"checkpoint_id": "cp-failure"},
    )
    monkeypatch.setattr(
        app_module,
        "append_trace",
        lambda task_id, event, **kwargs: trace_rows.append({"task_id": task_id, "event": event, **kwargs}) or {},
    )
    monkeypatch.setattr(app_module, "maybe_start_next_subagent_task", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_module, "auto_continue_workflows_for_agent_task", lambda *_args, **_kwargs: None)

    assert app_module.process_ui_queue(state)
    assert ledger_rows[-1]["status"] == expected_status
    assert ledger_rows[-1]["error"]
    assert ledger_rows[-1]["approval"]["approval_status"] == "approved"
    assert ledger_rows[-1]["approval"]["approval_id"] == "approval-terminal"
    assert ledger_rows[-1]["artifact_refs"] == [
        "artifact://context/task-pi-failure.json",
        "artifact://agent_project_runs/task-pi-failure.json",
        "artifact://failure",
    ]
    assert mail_rows[-1]["approval"] == ledger_rows[-1]["approval"]
    assert mail_rows[-1]["artifact_refs"] == ledger_rows[-1]["artifact_refs"]
    assert mail_rows[-1]["payload"]["agent_project_id"] == "failure-project"
    assert mail_rows[-1]["payload"]["agent_run_manifest_ref"] == (
        "artifact://agent_project_runs/task-pi-failure.json"
    )
    assert checkpoint_rows[-1]["extra"]["approval_id"] == "approval-terminal"
    assert checkpoint_rows[-1]["extra"]["artifact_refs"] == ledger_rows[-1]["artifact_refs"]
    assert trace_rows[-1]["payload"]["policy_decision_id"] == "policy-terminal"
    assert trace_rows[-1]["payload"]["agent_build_digest"] == "c" * 64
    assert sub.status == "idle"
