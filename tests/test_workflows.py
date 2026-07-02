from __future__ import annotations

import json
from pathlib import Path

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
