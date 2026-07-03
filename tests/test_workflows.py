from __future__ import annotations

import json
import queue
import time
from pathlib import Path

from ga_tui import app as app_module
from ga_tui import plugins, workflows


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class SequencedWorkflowAgent:
    log_path = ""

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.prompts: list[tuple[str, str]] = []

    def get_llm_name(self, *, model: bool = False) -> str:
        return "workflow-test-model" if model else "Workflow Test Model"

    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        self.prompts.append((prompt, source))
        response = self.responses.pop(0) if self.responses else "workflow task result"
        result: queue.Queue = queue.Queue()
        result.put({"done": response})
        return result


def create_workflow_plugin(
    tmp_path: Path,
    workflow_payload: dict | str,
    *,
    workflow_name: str = "compare-sources",
    agent_templates: list[dict] | None = None,
):
    plugin_root = tmp_path / "plugins" / "research-pack"
    workflow_path = plugin_root / "workflows" / f"{workflow_name}.json"
    workflow_path.parent.mkdir(parents=True)
    if isinstance(workflow_payload, str):
        workflow_path.write_text(workflow_payload, encoding="utf-8")
    else:
        write_json(workflow_path, workflow_payload)
    contributes = {
        "workflows": [
            {
                "id": workflow_name,
                "name": "Compare Sources",
                "description": "Compare research evidence.",
                "path": f"workflows/{workflow_name}.json",
            }
        ]
    }
    if agent_templates is not None:
        contributes["agent_templates"] = agent_templates
    write_json(
        plugin_root / "plugin.json",
        {
            "schema_version": "shuheng.plugin.v1",
            "id": "research-pack",
            "name": "Research Pack",
            "contributes": contributes,
        },
    )
    registry = plugins.discover_plugins([str(tmp_path / "plugins")])
    return registry, workflow_path


def configure_app_workflow_harness(tmp_path: Path, monkeypatch, plugin_root: Path) -> Path:
    harness_dir = tmp_path / "harness"
    memory_dir = tmp_path / "memory"
    temp_dir = tmp_path / "temp"
    monkeypatch.setattr(app_module, "SHUHENG_PLUGINS_DIR", str(plugin_root))
    monkeypatch.setattr(app_module, "SHUHENG_MEMORY_DIR", str(memory_dir))
    monkeypatch.setattr(app_module, "SHUHENG_TEMP_DIR", str(temp_dir))
    monkeypatch.setattr(app_module, "AGENT_HARNESS_DIR", str(harness_dir))
    monkeypatch.setattr(app_module, "AGENT_WORKFLOW_RUNS_PATH", str(harness_dir / "workflow_runs.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_TASK_LEDGER_PATH", str(harness_dir / "tasks.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_PROGRESS_LEDGER_PATH", str(harness_dir / "progress.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_APPROVALS_PATH", str(harness_dir / "approvals.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_MAIL_PATH", str(harness_dir / "messages.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_ARTIFACTS_DIR", str(harness_dir / "artifacts"))
    monkeypatch.setattr(app_module, "AGENT_ARTIFACT_INDEX_PATH", str(harness_dir / "artifacts.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_CONTEXT_PACKS_DIR", str(harness_dir / "context_packs"))
    monkeypatch.setattr(app_module, "AGENT_TRACES_PATH", str(harness_dir / "traces.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_EVALS_PATH", str(harness_dir / "evals.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_LOCKS_PATH", str(harness_dir / "locks.json"))
    monkeypatch.setattr(app_module, "AGENT_POLICY_PATH", str(harness_dir / "policy.json"))
    monkeypatch.setattr(app_module, "AGENT_POLICY_DECISIONS_PATH", str(harness_dir / "policy_decisions.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_ORCHESTRATOR_PLANS_PATH", str(harness_dir / "orchestrator_plans.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_MEMORY_CANDIDATES_PATH", str(harness_dir / "memory_candidates.jsonl"))
    monkeypatch.setattr(app_module, "AGENT_CHECKPOINTS_DIR", str(harness_dir / "checkpoints"))
    monkeypatch.setattr(app_module, "AGENT_CHECKPOINT_INDEX_PATH", str(harness_dir / "checkpoints.jsonl"))
    monkeypatch.setattr(app_module, "SUBAGENTS_DIR", str(memory_dir / "subagents"))
    monkeypatch.setattr(app_module, "TEMP_SUBAGENTS_DIR", str(temp_dir / "subagents"))
    app_module.clear_plugin_registry_cache()
    return harness_dir


def drain_app_ui_queue(state: app_module.State, *, attempts: int = 20) -> None:
    for _ in range(attempts):
        if app_module.process_ui_queue(state):
            return
        time.sleep(0.01)


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


def test_workflow_definition_rejects_self_duplicate_and_cyclic_dependencies(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "cyclic-flow",
            "steps": [
                {"id": "self", "type": "prompt", "depends_on": ["self"]},
                {"id": "collect", "type": "prompt"},
                {"id": "review", "type": "notify", "depends_on": ["collect", "collect"]},
                {"id": "cycle_a", "type": "prompt", "depends_on": ["cycle_b"]},
                {"id": "cycle_b", "type": "notify", "depends_on": ["cycle_a"]},
            ],
        },
        workflow_name="cyclic-flow",
    )

    result = workflows.workflow_load_result_for_ref("research-pack/workflows/cyclic-flow", registry)

    messages = "\n".join(issue.message for issue in result.issues)
    assert "steps[self] depends on itself" in messages
    assert "steps[review] duplicates dependency collect" in messages
    assert "workflow dependency cycle detected: cycle_a -> cycle_b -> cycle_a" in messages
    assert "No execution occurred." in workflows.format_workflow_dry_run(result)


def test_workflow_definition_accepts_valid_fan_in_dependencies(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "fan-in-flow",
            "steps": [
                {"id": "collect_a", "type": "prompt"},
                {"id": "collect_b", "type": "prompt"},
                {"id": "review", "type": "notify", "depends_on": ["collect_a", "collect_b"]},
            ],
        },
        workflow_name="fan-in-flow",
    )

    result = workflows.workflow_load_result_for_ref("research-pack/workflows/fan-in-flow", registry)

    assert not result.issues
    assert result.definition is not None
    assert result.definition.steps[2].depends_on == ("collect_a", "collect_b")


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


def test_workflow_generate_and_save_last_persists_manifest_backed_workflow(tmp_path: Path, monkeypatch) -> None:
    plugin_root = tmp_path / "plugins"
    configure_app_workflow_harness(tmp_path, monkeypatch, plugin_root)
    draft_payload = {
        "schema_version": "shuheng.workflow.v1",
        "id": "generated-flow",
        "name": "Generated Flow",
        "description": "Generated from natural language.",
        "steps": [
            {"id": "plan", "type": "prompt", "prompt": "Plan the work."},
            {"id": "notify", "type": "notify", "depends_on": ["plan"]},
        ],
    }
    state = app_module.State(agent=SequencedWorkflowAgent([json.dumps(draft_payload)]))

    assert app_module.handle_workflow_command(state, "/workflow generate summarize a research project") is True
    assert state.agent.prompts
    assert state.agent.prompts[0][1].startswith("workflow_generate")
    assert "Return ONLY one JSON object" in state.agent.prompts[0][0]
    assert "summarize a research project" in state.agent.prompts[0][0]

    drain_app_ui_queue(state)

    assert state.workflow_draft_payload is not None
    assert state.workflow_draft_payload["id"] == "generated-flow"
    assert "Workflow draft ready." in state.messages[-1].content
    assert "No workflow was saved or executed." in state.messages[-1].content
    assert app_module.workflow_run_records() == []
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []

    assert app_module.handle_workflow_command(state, "/workflow save-last generated-pack/saved-flow") is True

    manifest_path = plugin_root / "generated-pack" / "plugin.json"
    workflow_path = plugin_root / "generated-pack" / "workflows" / "saved-flow.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    saved_workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "shuheng.plugin.v1"
    assert manifest["id"] == "generated-pack"
    assert manifest["contributes"]["workflows"][0]["id"] == "saved-flow"
    assert manifest["contributes"]["workflows"][0]["path"] == "workflows/saved-flow.json"
    assert saved_workflow["id"] == "saved-flow"
    assert "Workflow draft saved." in state.messages[-1].content
    result = app_module.workflow_load_result_for_ref(
        "generated-pack/saved-flow",
        app_module.user_plugin_registry(force=True),
    )
    assert result.definition is not None
    assert not result.issues
    assert "No execution occurred." in app_module.format_workflow_dry_run(result)
    assert app_module.workflow_run_records() == []
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []


def test_workflow_run_last_saves_and_runs_safe_generated_draft(tmp_path: Path, monkeypatch) -> None:
    plugin_root = tmp_path / "plugins"
    configure_app_workflow_harness(tmp_path, monkeypatch, plugin_root)
    state = app_module.State(agent=SequencedWorkflowAgent([]))
    state.workflow_draft_payload = {
        "schema_version": "shuheng.workflow.v1",
        "id": "draft-safe-flow",
        "name": "Draft Safe Flow",
        "inputs": {"ready": {"type": "boolean", "required": True}},
        "steps": [
            {"id": "plan", "type": "prompt", "prompt": "Plan."},
            {"id": "check", "type": "condition", "depends_on": ["plan"], "condition": {"ref": "inputs.ready", "equals": True}},
            {"id": "notify", "type": "notify", "depends_on": ["check"]},
        ],
    }

    assert app_module.handle_workflow_command(state, "/workflow run-last generated-pack/safe-flow ready=true") is True

    assert "Workflow draft saved and run started." in state.messages[-1].content
    assert "Workflow draft saved." in state.messages[-1].content
    assert "Workflow run advanced:" in state.messages[-1].content
    assert "status: completed" in state.messages[-1].content
    workflow_path = plugin_root / "generated-pack" / "workflows" / "safe-flow.json"
    assert workflow_path.exists()
    assert json.loads(workflow_path.read_text(encoding="utf-8"))["id"] == "safe-flow"
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    assert rows[0]["status"] == "planned"
    assert rows[1]["status"] == "completed"
    assert rows[0]["inputs"] == {"ready": True}
    assert rows[0]["workflow_ref"] == "plugin://generated-pack/workflows/safe-flow"
    assert rows[1]["run_id"] == rows[0]["run_id"]
    assert [step["status"] for step in rows[1]["steps"]] == ["completed", "completed", "completed"]
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []


def test_workflow_run_last_uses_existing_approval_bridge(tmp_path: Path, monkeypatch) -> None:
    plugin_root = tmp_path / "plugins"
    configure_app_workflow_harness(tmp_path, monkeypatch, plugin_root)
    state = app_module.State(agent=SequencedWorkflowAgent([]))
    state.workflow_draft_payload = {
        "schema_version": "shuheng.workflow.v1",
        "id": "draft-approval-flow",
        "name": "Draft Approval Flow",
        "steps": [
            {"id": "plan", "type": "prompt", "prompt": "Plan."},
            {"id": "approve", "type": "approval", "depends_on": ["plan"]},
            {"id": "notify", "type": "notify", "depends_on": ["approve"]},
        ],
    }

    assert app_module.handle_workflow_command(state, "/workflow run-last generated-pack/approval-flow") is True

    assert "Workflow draft saved and run started." in state.messages[-1].content
    assert "Approvals created: 1" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    assert rows[-1]["status"] == "waiting_approval"
    approval_id = rows[-1]["approval"]["approval_id"]
    assert approval_id
    approval_rows = app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)
    assert len(approval_rows) == 1
    assert approval_rows[0]["approval_id"] == approval_id
    assert approval_rows[0]["type"] == "workflow_step_approval"
    assert approval_rows[0]["payload"]["workflow_ref"] == "plugin://generated-pack/workflows/approval-flow"
    assert approval_rows[0]["payload"]["source_command"] == "/workflow run-last generated-pack/approval-flow"
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []


def test_workflow_auto_generates_saves_and_runs_safe_workflow(tmp_path: Path, monkeypatch) -> None:
    plugin_root = tmp_path / "plugins"
    configure_app_workflow_harness(tmp_path, monkeypatch, plugin_root)
    draft_payload = {
        "schema_version": "shuheng.workflow.v1",
        "id": "draft-auto-flow",
        "name": "Draft Auto Flow",
        "inputs": {"ready": {"type": "boolean", "required": True}},
        "steps": [
            {"id": "plan", "type": "prompt", "prompt": "Plan."},
            {"id": "check", "type": "condition", "depends_on": ["plan"], "condition": {"ref": "inputs.ready", "equals": True}},
            {"id": "notify", "type": "notify", "depends_on": ["check"]},
        ],
    }
    state = app_module.State(agent=SequencedWorkflowAgent([json.dumps(draft_payload)]))

    assert app_module.handle_workflow_command(
        state,
        "/workflow auto generated-pack/auto-flow summarize sources -- ready=true",
    ) is True

    assert state.agent.prompts
    assert state.agent.prompts[0][1].startswith("workflow_generate:auto:")
    assert "summarize sources" in state.agent.prompts[0][0]
    assert state.workflow_auto_run_ref == "plugin://generated-pack/workflows/auto-flow"
    assert state.workflow_auto_run_inputs == {"ready": True}

    drain_app_ui_queue(state)

    assert state.workflow_auto_run_ref == ""
    assert state.workflow_auto_run_inputs == {}
    assert "Workflow auto generated and run started." in state.messages[-1].content
    assert "Workflow draft saved and run started." in state.messages[-1].content
    assert "Workflow run advanced:" in state.messages[-1].content
    assert "status: completed" in state.messages[-1].content
    workflow_path = plugin_root / "generated-pack" / "workflows" / "auto-flow.json"
    assert workflow_path.exists()
    assert json.loads(workflow_path.read_text(encoding="utf-8"))["id"] == "auto-flow"
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    assert rows[0]["workflow_ref"] == "plugin://generated-pack/workflows/auto-flow"
    assert rows[0]["inputs"] == {"ready": True}
    assert rows[0]["status"] == "planned"
    assert rows[1]["status"] == "completed"
    assert [step["status"] for step in rows[1]["steps"]] == ["completed", "completed", "completed"]
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []


def test_workflow_auto_uses_existing_approval_bridge(tmp_path: Path, monkeypatch) -> None:
    plugin_root = tmp_path / "plugins"
    configure_app_workflow_harness(tmp_path, monkeypatch, plugin_root)
    draft_payload = {
        "schema_version": "shuheng.workflow.v1",
        "id": "draft-auto-approval",
        "name": "Draft Auto Approval",
        "steps": [
            {"id": "plan", "type": "prompt", "prompt": "Plan."},
            {"id": "approve", "type": "approval", "depends_on": ["plan"]},
            {"id": "notify", "type": "notify", "depends_on": ["approve"]},
        ],
    }
    state = app_module.State(agent=SequencedWorkflowAgent([json.dumps(draft_payload)]))

    assert app_module.handle_workflow_command(
        state,
        "/workflow auto generated-pack/auto-approval deploy after review",
    ) is True
    drain_app_ui_queue(state)

    assert "Workflow auto generated and run started." in state.messages[-1].content
    assert "Approvals created: 1" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    assert rows[-1]["status"] == "waiting_approval"
    approval_id = rows[-1]["approval"]["approval_id"]
    approval_rows = app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)
    assert len(approval_rows) == 1
    assert approval_rows[0]["approval_id"] == approval_id
    assert approval_rows[0]["payload"]["workflow_ref"] == "plugin://generated-pack/workflows/auto-approval"
    assert approval_rows[0]["payload"]["source_command"] == "/workflow auto generated-pack/auto-approval deploy after review"
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []


def test_workflow_auto_invalid_output_and_unsafe_ref_are_noops(tmp_path: Path, monkeypatch) -> None:
    plugin_root = tmp_path / "plugins"
    configure_app_workflow_harness(tmp_path, monkeypatch, plugin_root)
    state = app_module.State(agent=SequencedWorkflowAgent(["not workflow json"]))
    state.workflow_draft_payload = {
        "schema_version": "shuheng.workflow.v1",
        "id": "previous-valid",
        "steps": [{"id": "plan", "type": "prompt", "prompt": "Plan."}],
    }
    previous = dict(state.workflow_draft_payload)

    assert app_module.handle_workflow_command(state, "/workflow auto ../escape/auto-flow summarize sources") is True
    assert "用法：/workflow auto" in state.messages[-1].content
    assert state.agent.prompts == []
    assert app_module.workflow_run_records() == []
    assert not plugin_root.exists()

    assert app_module.handle_workflow_command(state, "/workflow auto generated-pack/auto-flow summarize sources") is True
    drain_app_ui_queue(state)

    assert state.workflow_draft_payload == previous
    assert state.workflow_auto_run_ref == ""
    assert "Workflow draft rejected." in state.messages[-1].content
    assert "No workflow was saved or executed." in state.messages[-1].content
    assert app_module.workflow_run_records() == []
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []

    state.agent = SequencedWorkflowAgent([json.dumps(previous)])
    assert app_module.handle_workflow_command(state, "/workflow generate ordinary draft only") is True
    assert state.workflow_auto_run_ref == ""
    drain_app_ui_queue(state)
    assert "Workflow draft ready." in state.messages[-1].content
    assert "No workflow was saved or executed." in state.messages[-1].content
    assert app_module.workflow_run_records() == []


def test_workflow_generate_invalid_output_does_not_overwrite_previous_valid_draft(tmp_path: Path, monkeypatch) -> None:
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    valid_payload = {
        "schema_version": "shuheng.workflow.v1",
        "id": "valid-draft",
        "name": "Valid Draft",
        "steps": [{"id": "plan", "type": "prompt", "prompt": "Plan."}],
    }
    state = app_module.State(agent=SequencedWorkflowAgent([json.dumps(valid_payload)]))

    assert app_module.handle_workflow_command(state, "/workflow generate valid workflow") is True
    drain_app_ui_queue(state)
    assert state.workflow_draft_payload is not None
    previous = dict(state.workflow_draft_payload)

    state.agent = SequencedWorkflowAgent(["not workflow json"])
    assert app_module.handle_workflow_command(state, "/workflow generate invalid workflow") is True
    drain_app_ui_queue(state)

    assert state.workflow_draft_payload == previous
    assert "Workflow draft rejected." in state.messages[-1].content
    assert "No workflow was saved or executed." in state.messages[-1].content
    assert app_module.workflow_run_records() == []


def test_workflow_save_last_without_draft_and_unsafe_ids_write_no_files(tmp_path: Path, monkeypatch) -> None:
    plugin_root = tmp_path / "plugins"
    configure_app_workflow_harness(tmp_path, monkeypatch, plugin_root)
    state = app_module.State(agent=SequencedWorkflowAgent([]))

    assert app_module.handle_workflow_command(state, "/workflow save-last generated-pack/saved-flow") is True
    assert "No valid workflow draft is available" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, "/workflow run-last generated-pack/saved-flow") is True
    assert "Workflow draft was not run." in state.messages[-1].content
    assert "No valid workflow draft is available" in state.messages[-1].content
    assert not plugin_root.exists()

    state.workflow_draft_payload = {
        "schema_version": "shuheng.workflow.v1",
        "id": "valid-draft",
        "steps": [{"id": "plan", "type": "prompt", "prompt": "Plan."}],
    }
    assert app_module.handle_workflow_command(state, "/workflow save-last ../escape/saved-flow") is True
    assert "filesystem-safe" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, "/workflow run-last ../escape/saved-flow") is True
    assert "Workflow draft was not run." in state.messages[-1].content
    assert "filesystem-safe" in state.messages[-1].content
    assert not plugin_root.exists()
    assert app_module.workflow_run_records() == []
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []


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


def test_workflow_inputs_resolve_defaults_and_reject_missing_or_unknown(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "inputs": {
                "ready": {"type": "boolean", "required": True},
                "mode": {"type": "string", "required": False, "default": "safe"},
            },
            "steps": [{"id": "plan", "type": "prompt", "prompt": "Plan."}],
        },
    )
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)

    built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-inputs",
        timestamp="2026-07-03T00:00:00+0800",
        inputs={"ready": True},
    )
    missing = workflows.build_workflow_run_record(
        result,
        run_id="wfr-missing",
        timestamp="2026-07-03T00:00:00+0800",
        inputs={},
    )
    unknown = workflows.build_workflow_run_record(
        result,
        run_id="wfr-unknown",
        timestamp="2026-07-03T00:00:00+0800",
        inputs={"ready": True, "typo": "x"},
    )

    assert built.record is not None
    assert built.record["inputs"] == {"ready": True, "mode": "safe"}
    assert missing.record is None
    assert "required workflow input is missing: ready" in workflows.format_workflow_run_rejected(result, missing.issues)
    assert unknown.record is None
    assert "unknown workflow input: typo" in workflows.format_workflow_run_rejected(result, unknown.issues)


def test_workflow_condition_v1_evaluates_true_false_and_unsupported(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "compare-sources",
            "inputs": {
                "ready": {"type": "boolean", "required": True},
                "mode": {"type": "string", "required": False, "default": "safe"},
            },
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "check",
                    "type": "condition",
                    "depends_on": ["plan"],
                    "condition": {
                        "all": [
                            {"ref": "inputs.ready", "equals": True},
                            {"ref": "inputs.mode", "in": ["safe", "fast"]},
                        ]
                    },
                },
                {"id": "notify", "type": "notify", "depends_on": ["check"]},
            ],
        },
    )
    result = workflows.workflow_load_result_for_ref("research-pack/compare-sources", registry)
    true_built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-condition-true",
        timestamp="2026-07-03T00:00:00+0800",
        inputs={"ready": True},
    )
    false_built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-condition-false",
        timestamp="2026-07-03T00:00:00+0800",
        inputs={"ready": False},
    )
    assert true_built.record is not None
    assert false_built.record is not None

    true_advanced = workflows.advance_workflow_run_v0(
        true_built.record,
        timestamp="2026-07-03T00:00:01+0800",
    )
    false_advanced = workflows.advance_workflow_run_v0(
        false_built.record,
        timestamp="2026-07-03T00:00:01+0800",
    )

    assert true_advanced.status == "completed"
    assert true_advanced.completed_step_ids == ("plan", "check", "notify")
    assert [step["status"] for step in true_advanced.record["steps"]] == ["completed", "completed", "completed"]
    assert false_advanced.status == "blocked"
    assert false_advanced.blocked_step_id == "check"
    assert [step["status"] for step in false_advanced.record["steps"]] == ["completed", "skipped", "pending"]
    assert false_advanced.record["execution"]["subagents_dispatched"] == 0
    assert false_advanced.record["execution"]["approvals_created"] == 0
    assert false_advanced.record["execution"]["task_ledger_rows_written"] == 0

    unsupported_record = dict(true_built.record)
    unsupported_record["steps"] = [
        {
            **true_built.record["steps"][1],
            "status": "pending",
            "started_at": "",
            "completed_at": "",
            "depends_on": [],
            "condition": {"ref": "artifacts.output", "truthy": True},
        }
    ]
    unsupported = workflows.advance_workflow_run_v0(
        unsupported_record,
        timestamp="2026-07-03T00:00:02+0800",
    )
    assert unsupported.status == "blocked"
    assert unsupported.record["steps"][0]["status"] == "blocked"
    assert "inputs.<id>" in unsupported.blocked_reason


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


def test_workflow_cancel_helper_marks_current_blocker_only(tmp_path: Path) -> None:
    registry, _workflow_path = create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "cancel-flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {"id": "gate", "type": "condition", "depends_on": ["plan"], "expression": "inputs.ready == true"},
                {"id": "notify", "type": "notify", "depends_on": ["gate"]},
            ],
        },
        workflow_name="cancel-flow",
    )
    result = workflows.workflow_load_result_for_ref("research-pack/cancel-flow", registry)
    built = workflows.build_workflow_run_record(
        result,
        run_id="wfr-cancel",
        timestamp="2026-07-03T00:00:00+0800",
    )
    assert built.record is not None
    advanced = workflows.advance_workflow_run_v0(
        built.record,
        timestamp="2026-07-03T00:00:01+0800",
    )

    cancelled = workflows.cancel_workflow_run_v0(
        advanced.record,
        timestamp="2026-07-03T00:00:02+0800",
        reason="user stopped this run",
    )
    formatted = workflows.format_workflow_cancel_result(
        workflows.WorkflowRunCancelResult(
            run_id="wfr-cancel",
            status="cancelled",
            record=cancelled.record,
            history_rows=3,
            reason=cancelled.reason,
            run_status="cancelled",
        )
    )

    assert cancelled.record is not None
    assert cancelled.status == "cancelled"
    assert cancelled.record["status"] == "cancelled"
    assert cancelled.record["error"] == "user stopped this run"
    assert [step["status"] for step in cancelled.record["steps"]] == ["completed", "cancelled", "pending"]
    assert cancelled.record["execution"]["blocked_step_id"] == "gate"
    assert cancelled.record["execution"]["blocked_reason"] == "user stopped this run"
    assert "Workflow run cancelled: wfr-cancel" in formatted
    assert "No workflow steps were continued." in formatted
    assert "No subagents, approvals, tools, artifacts, task ledger rows, or progress ledger rows were created." in formatted


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


def test_workflow_run_command_keeps_condition_side_effect_free(tmp_path: Path, monkeypatch) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "condition-flow",
            "name": "Condition Flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {"id": "check", "type": "condition", "depends_on": ["plan"], "expression": "inputs.ready == true"},
            ],
        },
        workflow_name="condition-flow",
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)

    assert app_module.handle_workflow_command(state, "/workflow runs") is True
    assert "- (none)" in state.messages[-1].content

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/condition-flow") is True

    assert "Workflow run advanced:" in state.messages[-1].content
    assert "safe steps completed: 1" in state.messages[-1].content
    assert "requires condition evaluation" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    assert rows[0]["status"] == "planned"
    assert rows[1]["status"] == "blocked"
    assert rows[0]["run_id"] == rows[1]["run_id"]
    assert rows[1]["workflow_ref"] == "plugin://research-pack/workflows/condition-flow"
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
    assert "requires condition evaluation" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, f"/workflow show {rows[1]['run_id']}") is True
    assert f"Workflow run: {rows[1]['run_id']}" in state.messages[-1].content
    assert "history_rows: 2" in state.messages[-1].content
    assert "2:check" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, "/workflow show missing-run") is True
    assert "Workflow run not found: missing-run" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, f"/workflow continue {rows[1]['run_id']}") is True
    assert "Workflow run cannot continue with runner v0" in state.messages[-1].content
    assert "requires condition evaluation" in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == 2
    assert len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH)) == task_rows_after_run
    assert len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH)) == progress_rows_after_run
    assert len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)) == approval_rows_after_run
    assert len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH)) == artifact_rows_after_run
    assert len(state.subagents) == 0


def test_workflow_cancel_command_appends_once_and_keeps_side_effects_free(tmp_path: Path, monkeypatch) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "cancel-flow",
            "name": "Cancel Flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {"id": "gate", "type": "condition", "depends_on": ["plan"], "expression": "inputs.ready == true"},
                {"id": "notify", "type": "notify", "depends_on": ["gate"]},
            ],
        },
        workflow_name="cancel-flow",
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/cancel-flow") is True
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    run_id = rows[-1]["run_id"]
    task_rows_before_cancel = len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH))
    progress_rows_before_cancel = len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH))
    approval_rows_before_cancel = len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH))
    artifact_rows_before_cancel = len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH))

    assert app_module.handle_workflow_command(state, "/workflow cancel missing-run") is True
    assert "Workflow run not found: missing-run" in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == 2

    assert app_module.handle_workflow_command(state, f"/workflow cancel {run_id} no longer needed") is True
    assert "Workflow run cancelled:" in state.messages[-1].content
    assert "reason: no longer needed" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 3
    assert rows[-1]["run_id"] == run_id
    assert rows[-1]["status"] == "cancelled"
    assert rows[-1]["error"] == "no longer needed"
    assert [step["status"] for step in rows[-1]["steps"]] == ["completed", "cancelled", "pending"]
    assert len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH)) == task_rows_before_cancel
    assert len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH)) == progress_rows_before_cancel
    assert len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)) == approval_rows_before_cancel
    assert len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH)) == artifact_rows_before_cancel
    assert len(state.subagents) == 0

    assert app_module.handle_workflow_command(state, f"/workflow cancel {run_id}") is True
    assert "Workflow run already terminal:" in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == 3

    completed = dict(rows[0])
    completed["run_id"] = "wfr-completed-cancel-noop"
    completed["status"] = "completed"
    completed["completed_at"] = "2026-07-03T00:00:03+0800"
    app_module.append_workflow_run(completed)
    assert app_module.handle_workflow_command(state, "/workflow cancel wfr-completed-cancel-noop") is True
    assert "Workflow run already completed: wfr-completed-cancel-noop" in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == 4


def test_workflow_run_command_resolves_inputs_and_condition_v1(tmp_path: Path, monkeypatch) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "condition-input-flow",
            "name": "Condition Input Flow",
            "inputs": {
                "ready": {"type": "boolean", "required": True},
                "mode": {"type": "string", "required": False, "default": "safe"},
            },
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "check",
                    "type": "condition",
                    "depends_on": ["plan"],
                    "condition": {
                        "all": [
                            {"ref": "inputs.ready", "equals": True},
                            {"ref": "inputs.mode", "in": ["safe"]},
                        ]
                    },
                },
                {"id": "notify", "type": "notify", "depends_on": ["check"]},
            ],
        },
        workflow_name="condition-input-flow",
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/condition-input-flow") is True
    assert "required workflow input is missing: ready" in state.messages[-1].content
    assert app_module.workflow_run_records() == []

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/condition-input-flow ready=true typo=x") is True
    assert "unknown workflow input: typo" in state.messages[-1].content
    assert app_module.workflow_run_records() == []

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/condition-input-flow ready=true") is True
    assert "status: completed" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    assert rows[0]["inputs"] == {"ready": True, "mode": "safe"}
    assert rows[1]["status"] == "completed"
    assert [step["status"] for step in rows[1]["steps"]] == ["completed", "completed", "completed"]
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []

    rows_after_true = len(app_module.workflow_run_records())
    assert app_module.handle_workflow_command(state, "/workflow run research-pack/condition-input-flow ready=false") is True
    false_rows = app_module.workflow_run_records()
    assert len(false_rows) == rows_after_true + 2
    assert false_rows[-1]["status"] == "blocked"
    assert [step["status"] for step in false_rows[-1]["steps"]] == ["completed", "skipped", "pending"]
    assert app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH) == []
    assert app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH) == []


def test_workflow_upstream_step_output_context_scopes_formats_and_dedupes() -> None:
    row = {
        "steps": [
            {"step_id": "plan", "type": "prompt", "status": "completed", "artifact_refs": []},
            {
                "step_id": "collect",
                "type": "agent_task",
                "status": "completed",
                "task_id": "task_collect",
                "agent_id": "agent_collect",
                "artifact_refs": ["artifact://a", "artifact://dup", "artifact://a"],
            },
            {
                "step_id": "unrelated",
                "type": "agent_task",
                "status": "completed",
                "task_id": "task_unrelated",
                "agent_id": "agent_unrelated",
                "artifact_refs": ["artifact://unrelated"],
            },
            {
                "step_id": "review",
                "type": "agent_task",
                "status": "blocked",
                "depends_on": ["collect"],
                "prompt": "Review source quality.",
            },
            {
                "step_id": "final",
                "type": "agent_task",
                "status": "pending",
                "depends_on": [],
                "prompt": "Summarize everything.",
            },
        ]
    }

    explicit = workflows.workflow_upstream_step_output_context(row, row["steps"][3])
    assert len(explicit) == 1
    assert explicit[0].step_id == "collect"
    assert explicit[0].task_id == "task_collect"
    assert explicit[0].agent_id == "agent_collect"
    assert explicit[0].artifact_refs == ("artifact://a", "artifact://dup")

    formatted = workflows.format_workflow_step_output_context(explicit)
    assert "Workflow upstream context (reference-only; artifact contents are not loaded):" in formatted
    assert "step: collect [agent_task]" in formatted
    assert "task_id: task_collect" in formatted
    assert "agent_id: agent_collect" in formatted
    assert "artifact://a" in formatted
    assert "artifact://unrelated" not in formatted

    fallback = workflows.workflow_upstream_step_output_context(row, row["steps"][4])
    assert [item.step_id for item in fallback] == ["collect", "unrelated"]


def test_workflow_agent_task_prompt_preserves_base_without_upstream_context() -> None:
    row = {"workflow_description": "Workflow fallback.", "steps": []}
    step = {"step_id": "review", "type": "agent_task", "prompt": "Review source quality."}

    assert app_module.workflow_agent_task_prompt(row, step) == "Review source quality."


def test_workflow_agent_task_prompt_appends_reference_only_context() -> None:
    row = {
        "workflow_description": "Workflow fallback.",
        "steps": [
            {
                "step_id": "collect",
                "type": "agent_task",
                "status": "completed",
                "task_id": "task_collect",
                "agent_id": "agent_collect",
                "artifact_refs": ["artifact://collect-report"],
            },
            {
                "step_id": "review",
                "type": "agent_task",
                "status": "blocked",
                "depends_on": ["collect"],
                "prompt": "Review source quality.",
            },
        ],
    }

    prompt = app_module.workflow_agent_task_prompt(row, row["steps"][1])

    assert prompt.startswith("Review source quality.\n\nWorkflow upstream context")
    assert "step: collect [agent_task]" in prompt
    assert "task_id: task_collect" in prompt
    assert "agent_id: agent_collect" in prompt
    assert "artifact://collect-report" in prompt


def test_workflow_cancel_waiting_agent_task_does_not_abort_task(tmp_path: Path, monkeypatch) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "agent-cancel-flow",
            "name": "Agent Cancel Flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "Workflow Agent",
                    "depends_on": ["plan"],
                    "prompt": "Review source quality.",
                },
                {"id": "notify", "type": "notify", "depends_on": ["review"]},
            ],
        },
        workflow_name="agent-cancel-flow",
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)
    sub = app_module.create_subagent(
        state,
        "Workflow Agent",
        "Reviews source quality without writing files.",
        role="researcher",
        persistent=True,
    )
    sub.agent = SequencedWorkflowAgent(["agent task result"])

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/agent-cancel-flow") is True
    waiting = app_module.workflow_run_records()[-1]
    run_id = waiting["run_id"]
    task_id = waiting["steps"][1]["task_id"]
    assert waiting["status"] == "waiting_task"
    task_rows_after_dispatch = len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH))
    progress_rows_after_dispatch = len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH))
    approval_rows_after_dispatch = len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH))
    artifact_rows_after_dispatch = len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH))

    assert app_module.handle_workflow_command(state, f"/workflow cancel {run_id} stop waiting") is True
    assert "Workflow run cancelled:" in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 3
    assert rows[-1]["status"] == "cancelled"
    assert [step["status"] for step in rows[-1]["steps"]] == ["completed", "cancelled", "pending"]
    assert rows[-1]["steps"][1]["task_id"] == task_id
    assert app_module.latest_task_records()[task_id]["status"] == "working"
    assert len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH)) == task_rows_after_dispatch
    assert len(app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH)) == progress_rows_after_dispatch
    assert len(app_module.read_jsonl(app_module.AGENT_APPROVALS_PATH)) == approval_rows_after_dispatch
    assert len(app_module.read_jsonl(app_module.AGENT_ARTIFACT_INDEX_PATH)) == artifact_rows_after_dispatch
    assert state.subagents[sub.agent_id].active_bus_task_id == task_id

    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    assert "Workflow run already terminal:" in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == 3


def test_workflow_agent_task_bridge_dispatches_waits_and_continues(tmp_path: Path, monkeypatch) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "agent-flow",
            "name": "Agent Flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "Workflow Agent",
                    "depends_on": ["plan"],
                    "prompt": "Review source quality.",
                },
                {"id": "notify", "type": "notify", "depends_on": ["review"]},
            ],
        },
        workflow_name="agent-flow",
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)
    sub = app_module.create_subagent(
        state,
        "Workflow Agent",
        "Reviews source quality without writing files.",
        role="researcher",
        persistent=True,
    )
    sub.agent = SequencedWorkflowAgent(["agent task result"])

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/agent-flow") is True
    assert "Workflow run advanced:" in state.messages[-1].content
    assert "Subagents dispatched: 1." in state.messages[-1].content
    rows = app_module.workflow_run_records()
    assert len(rows) == 2
    run_id = rows[-1]["run_id"]
    waiting = rows[-1]
    task_id = waiting["steps"][1]["task_id"]
    assert waiting["status"] == "waiting_task"
    assert waiting["steps"][1]["status"] == "waiting_task"
    assert waiting["steps"][1]["agent_id"] == sub.agent_id
    assert task_id
    assert waiting["execution"]["subagents_dispatched"] == 1
    assert waiting["execution"]["task_ledger_rows_written"] == 1
    assert waiting["execution"]["progress_ledger_rows_written"] == 1
    task_rows = app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH)
    progress_rows = app_module.read_jsonl(app_module.AGENT_PROGRESS_LEDGER_PATH)
    assert task_rows and task_rows[-1]["task_id"] == task_id
    assert task_rows[-1]["status"] == "working"
    assert progress_rows and progress_rows[-1]["task_id"] == task_id
    assert len(sub.agent.prompts) == 1
    assert "Review source quality." in sub.agent.prompts[0][0]

    rows_after_dispatch = len(app_module.workflow_run_records())
    task_rows_after_dispatch = len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH))
    subagent_count_after_dispatch = len(state.subagents)
    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    assert "Workflow run waiting for subagent task:" in state.messages[-1].content
    assert task_id in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == rows_after_dispatch
    assert len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH)) == task_rows_after_dispatch
    assert len(state.subagents) == subagent_count_after_dispatch

    drain_app_ui_queue(state)
    assert app_module.latest_task_records()[task_id]["status"] == "completed"
    rows = app_module.workflow_run_records()
    assert len(rows) == rows_after_dispatch + 1
    completed = rows[-1]
    assert completed["status"] == "completed"
    assert [step["status"] for step in completed["steps"]] == ["completed", "completed", "completed"]
    assert completed["steps"][1]["task_id"] == task_id
    assert completed["steps"][1]["task_status"] == "completed"
    assert completed["steps"][1]["artifact_refs"]
    assert completed["artifact_refs"] == completed["steps"][1]["artifact_refs"]
    assert "Workflow auto-continued after subagent task:" in state.messages[-1].content
    assert run_id in state.messages[-1].content

    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    assert "Workflow run already completed:" in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == rows_after_dispatch + 1


def test_workflow_agent_task_bridge_passes_upstream_artifact_context_to_later_agent_task(
    tmp_path: Path,
    monkeypatch,
) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "multi-agent-flow",
            "name": "Multi Agent Flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "collect",
                    "type": "agent_task",
                    "agent": "Collect Workflow Agent",
                    "depends_on": ["plan"],
                    "prompt": "Collect evidence refs.",
                },
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "Review Workflow Agent",
                    "depends_on": ["collect"],
                    "prompt": "Use upstream refs.",
                },
                {"id": "notify", "type": "notify", "depends_on": ["review"]},
            ],
        },
        workflow_name="multi-agent-flow",
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)
    collect_sub = app_module.create_subagent(
        state,
        "Collect Workflow Agent",
        "Collects evidence references.",
        role="researcher",
        persistent=True,
    )
    review_sub = app_module.create_subagent(
        state,
        "Review Workflow Agent",
        "Reviews evidence references.",
        role="researcher",
        persistent=True,
    )
    collect_sub.agent = SequencedWorkflowAgent(["first upstream result"])
    review_sub.agent = SequencedWorkflowAgent(["second review result"])

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/multi-agent-flow") is True
    waiting = app_module.workflow_run_records()[-1]
    run_id = waiting["run_id"]
    collect_task_id = waiting["steps"][1]["task_id"]
    assert waiting["status"] == "waiting_task"
    assert collect_task_id
    assert len(collect_sub.agent.prompts) == 1
    assert len(review_sub.agent.prompts) == 0

    drain_app_ui_queue(state)

    after_collect = app_module.workflow_run_records()[-1]
    assert after_collect["status"] == "blocked"
    assert after_collect["steps"][1]["status"] == "completed"
    assert after_collect["steps"][2]["status"] == "blocked"
    upstream_refs = after_collect["steps"][1]["artifact_refs"]
    assert upstream_refs

    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    after_review_dispatch = app_module.workflow_run_records()[-1]
    review_task_id = after_review_dispatch["steps"][2]["task_id"]
    assert after_review_dispatch["status"] == "waiting_task"
    assert review_task_id
    assert len(review_sub.agent.prompts) == 1
    review_prompt = review_sub.agent.prompts[0][0]
    assert "Use upstream refs.\n\nWorkflow upstream context" in review_prompt
    assert "reference-only; artifact contents are not loaded" in review_prompt
    assert "step: collect [agent_task]" in review_prompt
    assert f"task_id: {collect_task_id}" in review_prompt
    assert f"agent_id: {collect_sub.agent_id}" in review_prompt
    assert upstream_refs[0] in review_prompt
    assert "first upstream result" not in review_prompt


def test_workflow_agent_task_bridge_stops_on_failed_task(tmp_path: Path, monkeypatch) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "agent-fail-flow",
            "name": "Agent Fail Flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "Failing Workflow Agent",
                    "depends_on": ["plan"],
                    "prompt": "Review source quality.",
                },
                {"id": "notify", "type": "notify", "depends_on": ["review"]},
            ],
        },
        workflow_name="agent-fail-flow",
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)
    sub = app_module.create_subagent(
        state,
        "Failing Workflow Agent",
        "Fails source review for workflow bridge tests.",
        role="researcher",
        persistent=True,
    )
    sub.agent = SequencedWorkflowAgent(["[ERROR] boom"])

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/agent-fail-flow") is True
    waiting = app_module.workflow_run_records()[-1]
    run_id = waiting["run_id"]
    task_id = waiting["steps"][1]["task_id"]
    assert waiting["status"] == "waiting_task"

    drain_app_ui_queue(state)
    assert app_module.latest_task_records()[task_id]["status"] == "failed"
    rows = app_module.workflow_run_records()
    failed = rows[-1]
    assert failed["status"] == "failed"
    assert failed["steps"][1]["status"] == "failed"
    assert failed["steps"][1]["task_status"] == "failed"
    assert failed["steps"][2]["status"] == "pending"
    assert "boom" in failed["error"]
    assert "Workflow auto-continued after subagent task:" in state.messages[-1].content

    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    assert "Workflow run already terminal:" in state.messages[-1].content
    assert "status: failed" in state.messages[-1].content
    assert len(app_module.workflow_run_records()) == len(rows)


def test_workflow_agent_task_bridge_creates_plugin_template_subagent(tmp_path: Path, monkeypatch) -> None:
    create_workflow_plugin(
        tmp_path,
        {
            "schema_version": "shuheng.workflow.v1",
            "id": "plugin-agent-flow",
            "name": "Plugin Agent Flow",
            "steps": [
                {"id": "plan", "type": "prompt", "prompt": "Plan."},
                {
                    "id": "review",
                    "type": "agent_task",
                    "agent": "plugin://research-pack/agents/evidence-researcher",
                    "depends_on": ["plan"],
                    "prompt": "Review source quality.",
                },
                {"id": "notify", "type": "notify", "depends_on": ["review"]},
            ],
        },
        workflow_name="plugin-agent-flow",
        agent_templates=[
            {
                "id": "evidence-researcher",
                "name": "Evidence Researcher",
                "description": "Researcher from a declarative plugin template.",
                "role": "researcher",
                "profile": "Collect evidence without writing files.",
            }
        ],
    )
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    created_agent = SequencedWorkflowAgent(["plugin template result"])
    monkeypatch.setattr(app_module, "new_agent", lambda log_path=None: created_agent)
    state = app_module.State(agent=None)

    assert app_module.handle_workflow_command(state, "/workflow run research-pack/plugin-agent-flow") is True
    rows = app_module.workflow_run_records()
    waiting = rows[-1]
    run_id = waiting["run_id"]
    task_id = waiting["steps"][1]["task_id"]
    assert waiting["status"] == "waiting_task"
    assert len(state.subagents) == 1
    sub = next(iter(state.subagents.values()))
    assert sub.name == "Evidence Researcher"
    assert sub.role == "researcher"
    assert waiting["steps"][1]["agent_id"] == sub.agent_id
    assert task_id == sub.active_bus_task_id
    assert len(created_agent.prompts) == 1

    task_rows_after_dispatch = len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH))
    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    assert "Workflow run waiting for subagent task:" in state.messages[-1].content
    assert len(app_module.read_jsonl(app_module.AGENT_TASK_LEDGER_PATH)) == task_rows_after_dispatch
    assert len(state.subagents) == 1

    drain_app_ui_queue(state)
    assert app_module.latest_task_records()[task_id]["status"] == "completed"
    assert app_module.workflow_run_records()[-1]["status"] == "completed"
    assert "Workflow auto-continued after subagent task:" in state.messages[-1].content
    assert app_module.handle_workflow_command(state, f"/workflow continue {run_id}") is True
    assert "Workflow run already completed:" in state.messages[-1].content


def test_workflow_auto_continue_ignores_unrelated_subagent_task(tmp_path: Path, monkeypatch) -> None:
    configure_app_workflow_harness(tmp_path, monkeypatch, tmp_path / "plugins")
    state = app_module.State(agent=None)
    sub = app_module.create_subagent(
        state,
        "Unrelated Agent",
        "Runs outside any workflow.",
        role="researcher",
        persistent=True,
    )
    sub.agent = SequencedWorkflowAgent(["unrelated result"])

    dispatch = app_module.start_subagent_task_structured(
        state,
        sub,
        "Do unrelated work.",
        source="test:unrelated",
        task_title="Unrelated task",
    )
    assert dispatch.task_id
    assert app_module.workflow_run_records() == []

    drain_app_ui_queue(state)

    assert app_module.latest_task_records()[dispatch.task_id]["status"] == "completed"
    assert app_module.workflow_run_records() == []
    assert not any("Workflow auto-continued after subagent task:" in message.content for message in state.messages)


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
