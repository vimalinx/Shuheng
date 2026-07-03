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
            "steps": [{"id": "plan", "type": "prompt", "prompt": "Plan."}],
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

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/compare-sources") is True

    assert "Workflow run planned:" in state.messages[-1].content
    assert "No workflow steps executed." in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 1
    assert rows[0]["status"] == "planned"
    assert rows[0]["workflow_ref"] == "plugin://research-pack/workflows/compare-sources"
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []
    assert len(state.subagents) == 0
