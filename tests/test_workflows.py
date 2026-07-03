from __future__ import annotations

import json
from pathlib import Path

from ga_tui import app as app_module
from ga_tui import plugins, workflows


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def create_workflow_plugin(tmp_path: Path, workflow_payload: dict | str, *, workflow_name: str = "compare-sources"):
    plugin_root = tmp_path / "plugins" / "research-pack"
    workflow_path = plugin_root / "workflows" / f"{workflow_name}.json"
    workflow_path.parent.mkdir(parents=True)
    if isinstance(workflow_payload, str):
        workflow_path.write_text(workflow_payload, encoding="utf-8")
    else:
        write_json(workflow_path, workflow_payload)
    write_json(
        plugin_root / "plugin.json",
        {
            "schema_version": "shuheng.plugin.v1",
            "id": "research-pack",
            "name": "Research Pack",
            "contributes": {
                "workflows": [
                    {
                        "id": workflow_name,
                        "name": "Compare Sources",
                        "description": "Compare research evidence.",
                        "path": f"workflows/{workflow_name}.json",
                    }
                ]
            },
        },
    )
    registry = plugins.discover_plugins([str(tmp_path / "plugins")])
    return registry, workflow_path


def configure_app_workflow_harness(tmp_path: Path, monkeypatch, plugin_root: Path) -> Path:
    harness_dir = tmp_path / "harness"
    monkeypatch.setattr(app_module, "SHUHENG_PLUGINS_DIR", str(plugin_root))
    monkeypatch.setattr(app_module, "AGENT_HARNESS_DIR", str(harness_dir))
    monkeypatch.setattr(app_module, "AGENT_WORKFLOW_RUNS_PATH", str(harness_dir / "workflow_runs.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_TASK_LEDGER_PATH", str(harness_dir / "tasks.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_PROGRESS_LEDGER_PATH", str(harness_dir / "progress.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_APPROVALS_PATH", str(harness_dir / "approvals.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_ARTIFACT_INDEX_PATH", str(harness_dir / "artifacts.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_MAIL_PATH", str(harness_dir / "mail.jsonl"))
    app_module.clear_plugin_registry_cache()
    return harness_dir


def test_workflow_definition_loads_from_manifest_declared_file(tmp_path: Path) -> None:
    marker = "WORKFLOW_DRY_RUN_TEST_MARKER"
    registry, workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "name": "Compare Sources",
            "description": "Compare research evidence.",
            "inputs": {
                "topic": {
                    "type": "string",
                    "required": True,
                    "description": "Research topic.",
                }
            },
            "permissions": {"writes": "none"},
            "steps": [
                {
                    "id": "plan",
                    "type": "prompt",
                    "prompt": f"Plan the comparison. {marker}",
                },
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "plugin://research-pack/agents/evidence-researcher",
                    "depends_on": ["plan"],
                    "prompt": "Review sources.",
                },
                {
                    "id": "summary",
                    "type": "artifact_summary",
                    "depends_on": ["review"],
                },
            ],
        },
    )

    ref = "plugin://research-pack/workflows/compare-sources"
    assert plugins.plugin_workflow_file_for_ref(ref, registry) == str(workflow_path)
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)

    assert not result.issues
    assert result.definition is not None
    assert result.definition.workflow_ref == ref
    assert result.definition.inputs[0].input_id == "topic"
    assert [step.step_id for step in result.definition.steps] == ["plan", "review", "summary"]
    info = workflows.format_workflow_info(result)
    dry_run = workflows.format_workflow_dry_run(result)
    assert "Compare Sources" in info
    assert "No execution occurred." in dry_run
    assert marker in dry_run


def test_workflow_definition_reports_validation_issues(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "wrong.version",
            "id": "compare-sources",
            "inputs": [{"id": "topic"}, {"id": "topic"}],
            "steps": [
                {"id": "plan", "type": "unknown"},
                {"id": "plan", "type": "prompt"},
                {"id": "review", "type": "agent_task", "depends_on": ["missing"]},
            ],
        },
    )

    result = workflows.workflow_load_result_for_ref("research-pack/workflows/compare-sources", registry)

    messages = "\n".join(issue.message for issue in result.issues)
    assert "schema_version must be shuheng.workflow.v1" in messages
    assert "inputs[2] duplicates id topic" in messages
    assert "steps[1] has unsupported type unknown" in messages
    assert "steps[2] duplicates id plan" in messages
    assert "depends on missing step missing" in messages
    assert "No execution occurred." in workflows.format_workflow_dry_run(result)


def test_workflow_definition_accepts_fenced_json(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        """# Compare Sources

```json
{"schema_version":"shuheng.workflow.v1","id":"compare-sources","steps":[{"id":"plan","type":"prompt"}]}
```
""",
    )

    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)

    assert not result.issues
    assert result.definition is not None
    assert result.definition.steps[0].step_id == "plan"


def test_workflow_definition_rejects_non_json_bodies(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(tmp_path, "# Compare Sources\n")

    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)

    assert result.definition is None
    assert result.issues
    assert "must be JSON" in result.issues[0].message


def test_workflow_run_record_is_planned_only(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "name": "Compare Sources",
            "inputs": {"topic": {"type": "string", "required": True}},
            "permissions": {"writes": "none"},
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "plugin://research-pack/agents/evidence-researcher",
                    "depends_on": ["plan"],
                    "prompt": "Review.",
                },
            ],
        },
    )
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)

    built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-test",
        timestamp="2026-07-03T00:00:00+0800",
        inputs={"topic": "workflow safety"},
    )

    assert not built.issues
    assert built.record is not None
    assert built.record["schema_version"] == "shuheng.workflow_run.v1"
    assert built.record["status"] == "planned"
    assert built.record["workflow_ref"] == "plugin://research-pack/workflows/compare-sources"
    assert built.record["inputs"] == {"topic": "workflow safety"}
    assert [step["status"] for step in built.record["steps"]] == ["pending", "pending"]
    assert built.record["steps"][1]["agent"] == "plugin://research-pack/agents/evidence-researcher"
    assert built.record["execution"]["steps_executed"] == 0
    assert built.record["execution"]["subagents_dispatched"] == 0
    assert built.record["execution"]["approvals_created"] == 0
    assert built.record["execution"]["artifacts_written"] == 0
    assert built.record["execution"]["task_ledger_rows_written"] == 0
    assert built.record["execution"]["progress_ledger_rows_written"] == 0
    assert "No workflow steps executed." in workflows.format_workflow_run_created(built.record)


def test_workflow_runner_v0_completes_safe_steps(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {"id": "pause", "type": "pause", "depends_on": ["plan"]},
                {"id": "notify", "type": "notify", "depends_on": ["pause"]},
                {"id": "summary", "type": "artifact_summary", "depends_on": ["notify"]},
            ],
        },
    )
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)
    built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-safe",
        timestamp="2026-07-03T00:00:00+0800",
    )
    assert built.record is not None

    advanced = workflows.advance_workflow_run_v0(
        built.record,
        timestamp="2026-07-03T00:00:01+0800",
    )

    assert advanced.status == "completed"
    assert advanced.completed_step_ids == ("plan", "pause", "notify", "summary")
    assert [step["status"] for step in advanced.record["steps"]] == ["completed", "completed", "completed", "completed"]
    assert advanced.record["execution"]["mode"] == "workflow_runner_v0"
    assert advanced.record["execution"]["runner_started"] is True
    assert advanced.record["execution"]["steps_executed"] == 4
    assert advanced.record["execution"]["subagents_dispatched"] == 0
    assert advanced.record["execution"]["approvals_created"] == 0
    assert advanced.record["execution"]["artifacts_written"] == 0
    assert "safe steps completed: 4" in workflows.format_workflow_run_advanced(advanced)


def test_workflow_runner_v0_stops_for_approval_without_approval_row(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {"id": "deploy_gate", "type": "approval", "depends_on": ["plan"]},
                {"id": "notify", "type": "notify", "depends_on": ["deploy_gate"]},
            ],
        },
    )
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)
    built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-approval",
        timestamp="2026-07-03T00:00:00+0800",
    )
    assert built.record is not None

    advanced = workflows.advance_workflow_run_v0(
        built.record,
        timestamp="2026-07-03T00:00:01+0800",
    )

    assert advanced.status == "waiting_approval"
    assert advanced.completed_step_ids == ("plan",)
    assert [step["status"] for step in advanced.record["steps"]] == ["completed", "waiting_approval", "pending"]
    assert advanced.record["approval"]["approval_status"] == "pending"
    assert advanced.record["approval"]["approval_required_for"] == ["deploy_gate"]
    assert advanced.record["execution"]["approvals_created"] == 0
    assert "requires human approval" in advanced.blocked_reason


def test_workflow_runner_v0_blocks_agent_task_and_condition(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "plugin://research-pack/agents/evidence-researcher",
                    "depends_on": ["plan"],
                    "prompt": "Review.",
                },
                {"id": "condition", "type": "condition", "depends_on": ["review"]},
            ],
        },
    )
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)
    built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-agent-task",
        timestamp="2026-07-03T00:00:00+0800",
    )
    assert built.record is not None

    advanced = workflows.advance_workflow_run_v0(
        built.record,
        timestamp="2026-07-03T00:00:01+0800",
    )

    assert advanced.status == "blocked"
    assert advanced.blocked_step_id == "review"
    assert [step["status"] for step in advanced.record["steps"]] == ["completed", "blocked", "pending"]
    assert advanced.record["execution"]["subagents_dispatched"] == 0
    assert advanced.record["execution"]["task_ledger_rows_written"] == 0
    assert "requires subagent dispatch" in advanced.blocked_reason

    condition_record = dict(built.record)
    condition_record["steps"] = [
        {
            "step_id": "condition",
            "order": 1,
            "type": "condition",
            "name": "condition",
            "description": "",
            "depends_on": [],
            "agent": "",
            "ref": "",
            "prompt": "",
            "status": "pending",
            "started_at": "",
            "completed_at": "",
            "artifact_refs": [],
            "approval_id": "",
            "task_id": "",
            "error": "",
        }
    ]
    condition_advanced = workflows.advance_workflow_run_v0(
        condition_record,
        timestamp="2026-07-03T00:00:02+0800",
    )
    assert condition_advanced.status == "blocked"
    assert condition_advanced.blocked_step_id == "condition"
    assert condition_advanced.record["steps"][0]["status"] == "blocked"
    assert "requires condition evaluation" in condition_advanced.blocked_reason


def test_workflow_run_inspection_formatters_show_latest_rows(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "plugin://research-pack/agents/evidence-researcher",
                    "depends_on": ["plan"],
                    "prompt": "Review.",
                },
            ],
        },
    )
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)
    built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-inspect",
        timestamp="2026-07-03T00:00:00+0800",
    )
    assert built.record is not None
    advanced = workflows.advance_workflow_run_v0(
        built.record,
        timestamp="2026-07-03T00:00:01+0800",
    )

    empty_listing = workflows.format_workflow_runs([])
    listing = workflows.format_workflow_runs([built.record, advanced.record])
    detail = workflows.format_workflow_run_detail("wfr-inspect", [built.record, advanced.record])
    missing = workflows.format_workflow_run_detail("missing-run", [built.record, advanced.record])

    assert "- (none)" in empty_listing
    assert listing.count("wfr-inspect") == 1
    assert "blocked" in listing
    assert "steps:1/2" in listing
    assert "requires subagent dispatch" in listing
    assert "Workflow run: wfr-inspect" in detail
    assert "history_rows: 2" in detail
    assert "steps: 1/2 completed" in detail
    assert "1:plan" in detail and "status=completed" in detail
    assert "2:review" in detail and "status=blocked" in detail
    assert "Workflow run not found: missing-run" in missing


def test_workflow_continue_formatters_detect_meaningful_transitions(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "plugin://research-pack/agents/evidence-researcher",
                    "depends_on": ["plan"],
                    "prompt": "Review.",
                },
            ],
        },
    )
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)
    built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-continue",
        timestamp="2026-07-03T00:00:00+0800",
    )
    assert built.record is not None
    advanced = workflows.advance_workflow_run_v0(
        built.record,
        timestamp="2026-07-03T00:00:01+0800",
    )
    repeated = workflows.advance_workflow_run_v0(
        advanced.record,
        timestamp="2026-07-03T00:00:02+0800",
    )

    continued = workflows.format_workflow_continue_result(
        workflows.WorkflowRunContinueResult(
            run_id="wfr-continue",
            status="continued",
            record=advanced.record,
            advanced=advanced,
            history_rows=2,
        )
    )
    no_progress = workflows.format_workflow_continue_result(
        workflows.WorkflowRunContinueResult(
            run_id="wfr-continue",
            status="no_progress",
            record=advanced.record,
            history_rows=2,
            reason=advanced.blocked_reason,
        )
    )

    assert workflows.workflow_run_has_meaningful_transition(built.record, advanced.record)
    assert not workflows.workflow_run_has_meaningful_transition(advanced.record, repeated.record)
    assert "Workflow run continued: wfr-continue" in continued
    assert "history_rows: 2" in continued
    assert "requires subagent dispatch" in continued
    assert "Workflow run cannot continue with runner v0: wfr-continue" in no_progress
    assert "No workflow run row was appended." in no_progress


def test_workflow_run_record_rejects_invalid_workflow(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "wrong.version",
            "id": "compare-sources",
            "steps": [{"id": "plan", "type": "prompt"}],
        },
    )
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)

    built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-test",
        timestamp="2026-07-03T00:00:00+0800",
    )

    assert built.record is None
    assert built.issues
    assert "schema_version must be shuheng.workflow.v1" in workflows.format_workflow_run_rejected(result, built.issues)


def test_workflow_run_command_appends_only_workflow_run_ledger(tmp_path: Path, monkeypatch) -> None:
    plugin_root = tmp_path / "plugins"
    workflow_plugin_root = plugin_root / "research-pack"
    workflow_path = workflow_plugin_root / "workflows" / "compare-sources.json"
    workflow_path.parent.mkdir(parents=True)
    write_json(
        workflow_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "name": "Compare Sources",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "plugin://research-pack/agents/evidence-researcher",
                    "depends_on": ["plan"],
                    "prompt": "Review.",
                },
            ],
        },
    )
    write_json(
        workflow_plugin_root / "plugin.json",
        {
            "schema_version": "shuheng.plugin.v1",
            "id": "research-pack",
            "name": "Research Pack",
            "contributes": {
                "workflows": [
                    {"id": "compare-sources", "path": "workflows/compare-sources.json"}
                ]
            },
        },
    )
    harness_dir = tmp_path / "harness"
    monkeypatch.setattr(app_module, "SHUHENG_PLUGINS_DIR", str(plugin_root))
    monkeypatch.setattr(app_module, "AGENT_HARNESS_DIR", str(harness_dir))
    monkeypatch.setattr(app_module, "AGENT_WORKFLOW_RUNS_PATH", str(harness_dir / "workflow_runs.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_TASK_LEDGER_PATH", str(harness_dir / "tasks.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_PROGRESS_LEDGER_PATH", str(harness_dir / "progress.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_APPROVALS_PATH", str(harness_dir / "approvals.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_ARTIFACT_INDEX_PATH", str(harness_dir / "artifacts.jsonl"))
    app_module.clear_plugin_registry_cache()
    state = app_module.State(agent=None)

    assert app_module.handle_workflow_command(state, "/workflow runs") is True
    assert "- (none)" in state.messages[-1].content

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/compare-sources") is True

    assert "Workflow run advanced:" in state.messages[-1].content
    assert "safe steps completed: 1" in state.messages[-1].content
    assert "requires subagent dispatch" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    assert rows[0]["status"] == "planned"
    assert rows[1]["status"] == "blocked"
    assert rows[0]["run_id"] == rows[1]["run_id"]
    assert rows[1]["workflow_ref"] == "plugin://research-pack/workflows/compare-sources"
    assert rows[1]["execution"]["steps_executed"] == 1
    assert rows[1]["execution"]["subagents_dispatched"] == 0
    assert rows[1]["execution"]["task_ledger_rows_written"] == 0
    assert rows[1]["execution"]["progress_ledger_rows_written"] == 0
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []
    assert len(state.subagents) == 0
    task_rows_after_run = len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH))
    progress_rows_after_run = len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH))
    approval_rows_after_run = len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH))
    artifact_rows_after_run = len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH))

    assert app_module.handle_workflow_command(state, "/workflow runs") is True
    assert rows[1]["run_id"] in state.messages[-1].content
    assert "steps:1/2" in state.messages[-1].content
    assert "requires subagent dispatch" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, f"/workflow show {rows[1]['run_id']}") is True
    assert f"Workflow run: {rows[1]['run_id']}" in state.messages[-1].content
    assert "history_rows: 2" in state.messages[-1].content
    assert "2:review" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, "/workflow show missing-run") is True
    assert "Workflow run not found: missing-run" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, f"/workflow continue {rows[1]['run_id']}") is True
    assert "Workflow run cannot continue with runner v0" in state.messages[-1].content
    assert "requires subagent dispatch" in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == 2
    assert len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH)) == task_rows_after_run
    assert len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH)) == progress_rows_after_run
    assert len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)) == approval_rows_after_run
    assert len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH)) == artifact_rows_after_run
    assert len(state.subagents) == 0


def test_workflow_continue_command_advances_planned_run_only(tmp_path: Path, monkeypatch) -> None:
    plugin_root = tmp_path / "plugins"
    workflow_plugin_root = plugin_root / "research-pack"
    workflow_path = workflow_plugin_root / "workflows" / "safe-steps.json"
    workflow_path.parent.mkdir(parents=True)
    write_json(
        workflow_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "safe-steps",
            "name": "Safe Steps",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {"id": "pause", "type": "pause", "depends_on": ["plan"]},
                {"id": "notify", "type": "notify", "depends_on": ["pause"]},
            ],
        },
    )
    write_json(
        workflow_plugin_root / "plugin.json",
        {
            "schema_version": "shuheng.plugin.v1",
            "id": "research-pack",
            "name": "Research Pack",
            "contributes": {
                "workflows": [
                    {"id": "safe-steps", "path": "workflows/safe-steps.json"}
                ]
            },
        },
    )
    harness_dir = tmp_path / "harness"
    monkeypatch.setattr(app_module, "SHUHENG_PLUGINS_DIR", str(plugin_root))
    monkeypatch.setattr(app_module, "AGENT_HARNESS_DIR", str(harness_dir))
    monkeypatch.setattr(app_module, "AGENT_WORKFLOW_RUNS_PATH", str(harness_dir / "workflow_runs.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_TASK_LEDGER_PATH", str(harness_dir / "tasks.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_PROGRESS_LEDGER_PATH", str(harness_dir / "progress.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_APPROVALS_PATH", str(harness_dir / "approvals.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_ARTIFACT_INDEX_PATH", str(harness_dir / "artifacts.jsonl"))
    app_module.clear_plugin_registry_cache()
    state = app_module.State(agent=None)

    result = app_module.workflow_load_result_for_ref(
        "research-pack/safe-steps",
        app_module.user_plugin_registry(force=True),
    )
    planned, planned_message = app_module.create_planned_workflow_run(result)
    assert planned is not None
    assert "Workflow run planned:" in planned_message
    run_id = planned["run_id"]
    task_rows_before_continue = len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH))
    progress_rows_before_continue = len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH))
    approval_rows_before_continue = len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH))
    artifact_rows_before_continue = len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH))

    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    assert "Workflow run continued:" in state.messages[-1].content
    assert "status: completed" in state.messages[-1].content
    assert "safe steps completed: 3" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    assert rows[0]["status"] == "planned"
    assert rows[1]["run_id"] == run_id
    assert rows[1]["status"] == "completed"
    assert [step["status"] for step in rows[1]["steps"]] == ["completed", "completed", "completed"]

    assert app_module.handle_workflow_command(state, f"/workflow resume {run_id}") is True
    assert "Workflow run already completed:" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, "/workflow continue missing-run") is True
    assert "Workflow run not found: missing-run" in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == 2
    assert len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH)) == task_rows_before_continue
    assert len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH)) == progress_rows_before_continue
    assert len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)) == approval_rows_before_continue
    assert len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH)) == artifact_rows_before_continue
    assert len(state.subagents) == 0


def test_workflow_approval_bridge_creates_pending_approval_and_continues_after_approval(
    tmp_path: Path,
    monkeypatch,
) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "approval-flow",
            "name": "Approval Flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {"id": "deploy_gate", "type": "approval", "name": "Deploy Gate", "depends_on": ["plan"]},
                {"id": "notify", "type": "notify", "depends_on": ["deploy_gate"]},
            ],
        },
        workflow_name="approval-flow",
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/approval-flow") is True
    assert "Workflow run advanced:" in state.messages[-1].content
    assert "Approvals created: 1" in state.messages[-1].content

    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    run_id = rows[-1]["run_id"]
    approval_id = rows[-1]["approval"]["approval_id"]
    assert rows[0]["status"] == "planned"
    assert rows[1]["status"] == "waiting_approval"
    assert approval_id
    assert rows[1]["approval"]["approval_required_for"] == ["deploy_gate"]
    assert rows[1]["steps"][1]["approval_id"] == approval_id
    assert rows[1]["steps"][1]["status"] == "waiting_approval"
    assert rows[1]["execution"]["approvals_created"] == 1

    approval_rows = app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)
    assert len(approval_rows) == 1
    assert approval_rows[0]["approval_id"] == approval_id
    assert approval_rows[0]["type"] == "workflow_step_approval"
    assert approval_rows[0]["payload"]["run_id"] == run_id
    assert approval_rows[0]["payload"]["workflow_ref"] == "plugin://research-pack/workflows/approval-flow"
    assert approval_rows[0]["payload"]["step_id"] == "deploy_gate"
    assert approval_id in app_module.format_approvals(state)
    assert "workflow_step_approval" in app_module.format_approvals(state)

    task_rows_after_run = len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH))
    progress_rows_after_run = len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH))
    artifact_rows_after_run = len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH))
    approval_rows_after_run = len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH))

    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    assert "Workflow run waiting for approval:" in state.messages[-1].content
    assert approval_id in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == 2
    assert len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)) == approval_rows_after_run

    approved_message = app_module.decide_approval(state, approval_id, True)
    assert f"已批准：{approval_id}" in approved_message
    assert app_module.approval_latest_records()[approval_id]["status"] == "approved"

    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    assert "Workflow run continued:" in state.messages[-1].content
    assert "status: completed" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 3
    assert rows[-1]["status"] == "completed"
    assert rows[-1]["approval"]["approval_id"] == approval_id
    assert rows[-1]["approval"]["approval_status"] == "approved"
    assert [step["status"] for step in rows[-1]["steps"]] == ["completed", "completed", "completed"]
    assert rows[-1]["steps"][1]["approval_id"] == approval_id
    assert len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH)) == task_rows_after_run
    assert len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH)) == progress_rows_after_run
    assert len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH)) == artifact_rows_after_run
    assert len(state.subagents) == 0


def test_workflow_approval_bridge_rejects_and_upgrades_legacy_waiting_rows(
    tmp_path: Path,
    monkeypatch,
) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "approval-flow",
            "name": "Approval Flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {"id": "deploy_gate", "type": "approval", "name": "Deploy Gate", "depends_on": ["plan"]},
                {"id": "notify", "type": "notify", "depends_on": ["deploy_gate"]},
            ],
        },
        workflow_name="approval-flow",
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/approval-flow") is True
    rejected_wait = app_module.workflow_run_records()[-1]
    rejected_run_id = rejected_wait["run_id"]
    rejected_approval_id = rejected_wait["approval"]["approval_id"]
    assert rejected_approval_id
    reject_message = app_module.decide_approval(state, rejected_approval_id, False)
    assert f"已拒绝：{rejected_approval_id}" in reject_message
    assert app_module.handle_workflow_command(state, f"/workflow continue {rejected_run_id}") is True
    assert "Workflow run rejected by approval:" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 3
    assert rows[-1]["status"] == "rejected"
    assert rows[-1]["approval"]["approval_status"] == "rejected"
    assert rows[-1]["steps"][1]["status"] == "rejected"
    assert rows[-1]["steps"][2]["status"] == "pending"

    result = app_module.workflow_load_result_for_ref(
        "research-pack/approval-flow",
        app_module.user_plugin_registry(force=True),
    )
    planned, planned_message = app_module.create_planned_workflow_run(result)
    assert planned is not None, planned_message
    legacy_run_id = planned["run_id"]
    legacy_wait = app_module.advance_workflow_run_v0(planned, timestamp="2026-07-03T00:00:00+0800")
    assert legacy_wait.record["status"] == "waiting_approval"
    assert legacy_wait.record["approval"]["approval_id"] == ""
    app_module.append_workflow_run(legacy_wait.record)
    approval_rows_before_legacy_bridge = len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH))

    assert app_module.handle_workflow_command(state, f"/workflow continue {legacy_run_id}") is True
    assert "Workflow approval created:" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 6
    legacy_bridged = rows[-1]
    legacy_approval_id = legacy_bridged["approval"]["approval_id"]
    assert legacy_bridged["status"] == "waiting_approval"
    assert legacy_approval_id
    assert legacy_bridged["steps"][1]["approval_id"] == legacy_approval_id
    assert legacy_bridged["execution"]["approvals_created"] == 1
    assert len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)) == approval_rows_before_legacy_bridge + 1
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []
    assert len(state.subagents) == 0
