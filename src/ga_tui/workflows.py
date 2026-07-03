"""Pure declarative workflow definition helpers for Shuheng."""
from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

try:
    from . import plugins as plugin_helpers
except Exception:  # pragma: no cover - script-mode compatibility
    import plugins as plugin_helpers  # type: ignore


WORKFLOW_SCHEMA_VERSION = "shuheng.workflow.v1"
WORKFLOW_RUN_SCHEMA_VERSION = "shuheng.workflow_run.v1"
WORKFLOW_RUNNER_V0_SAFE_STEP_TYPES = frozenset({
    "prompt",
    "artifact_summary",
    "pause",
    "notify",
})
WORKFLOW_STEP_TYPES = frozenset({
    "prompt",
    "agent_task",
    "approval",
    "artifact_summary",
    "pause",
    "notify",
    "condition",
})
_JSON_FENCE_RE = re.compile(r"```(?:json|workflow-json)?\s*(\{[\s\S]*?\})\s*```", re.I)


@dataclass(frozen=True)
class WorkflowIssue:
    workflow_ref: str
    path: str
    message: str


@dataclass(frozen=True)
class WorkflowInput:
    input_id: str
    input_type: str
    required: bool
    description: str
    default: Any = None


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    step_type: str
    name: str
    description: str
    depends_on: tuple[str, ...] = ()
    agent: str = ""
    prompt: str = ""
    ref: str = ""
    payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_ref: str
    plugin_id: str
    workflow_id: str
    name: str
    description: str
    path: str
    inputs: tuple[WorkflowInput, ...] = ()
    steps: tuple[WorkflowStep, ...] = ()
    permissions: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkflowLoadResult:
    workflow_ref: str
    path: str
    definition: WorkflowDefinition | None = None
    issues: tuple[WorkflowIssue, ...] = ()


@dataclass(frozen=True)
class WorkflowRunBuildResult:
    record: dict[str, Any] | None = None
    issues: tuple[WorkflowIssue, ...] = ()


@dataclass(frozen=True)
class WorkflowRunAdvanceResult:
    record: dict[str, Any]
    status: str
    completed_step_ids: tuple[str, ...] = ()
    blocked_step_id: str = ""
    blocked_step_type: str = ""
    blocked_reason: str = ""


def workflow_issue(workflow_ref: str, path: str, message: str) -> WorkflowIssue:
    return WorkflowIssue(workflow_ref=workflow_ref or "(unknown)", path=path, message=message)


def _string_items(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        if "," in value or "\n" in value:
            return tuple(part.strip() for part in re.split(r"[,\n]+", value) if part.strip())
        return tuple(part.strip() for part in value.split() if part.strip())
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item or "").strip() for item in value if str(item or "").strip())
    return (str(value).strip(),) if str(value or "").strip() else ()


def _payload_from_text(text: str, workflow_ref: str, path: str) -> tuple[dict[str, Any] | None, tuple[WorkflowIssue, ...]]:
    body = (text or "").strip()
    if body.startswith("{"):
        try:
            payload = json.loads(body)
        except Exception as exc:
            return None, (workflow_issue(workflow_ref, path, f"workflow JSON is invalid: {exc}"),)
        if not isinstance(payload, dict):
            return None, (workflow_issue(workflow_ref, path, "workflow file must contain a JSON object"),)
        return payload, ()
    match = _JSON_FENCE_RE.search(body)
    if not match:
        return None, (workflow_issue(workflow_ref, path, "workflow file must be JSON or contain a fenced JSON object"),)
    try:
        payload = json.loads(match.group(1))
    except Exception as exc:
        return None, (workflow_issue(workflow_ref, path, f"workflow JSON fence is invalid: {exc}"),)
    if not isinstance(payload, dict):
        return None, (workflow_issue(workflow_ref, path, "workflow JSON fence must contain an object"),)
    return payload, ()


def _parse_inputs(value: Any, workflow_ref: str, path: str) -> tuple[tuple[WorkflowInput, ...], list[WorkflowIssue]]:
    if value in (None, ""):
        return (), []
    entries: list[tuple[str, Any]] = []
    issues: list[WorkflowIssue] = []
    if isinstance(value, dict):
        entries = [(str(key), raw) for key, raw in value.items()]
    elif isinstance(value, list):
        for index, raw in enumerate(value, 1):
            if not isinstance(raw, dict):
                issues.append(workflow_issue(workflow_ref, path, f"inputs[{index}] must be an object"))
                continue
            entries.append((str(raw.get("id") or raw.get("name") or ""), raw))
    else:
        return (), [workflow_issue(workflow_ref, path, "inputs must be an object or list")]
    inputs: list[WorkflowInput] = []
    seen: set[str] = set()
    for index, (raw_id, raw) in enumerate(entries, 1):
        input_id = plugin_helpers.safe_plugin_id(raw_id)
        if not input_id:
            issues.append(workflow_issue(workflow_ref, path, f"inputs[{index}] has an invalid id"))
            continue
        key = input_id.casefold()
        if key in seen:
            issues.append(workflow_issue(workflow_ref, path, f"inputs[{index}] duplicates id {input_id}"))
            continue
        seen.add(key)
        payload = raw if isinstance(raw, dict) else {}
        default = payload.get("default") if isinstance(payload, dict) else None
        inputs.append(
            WorkflowInput(
                input_id=input_id,
                input_type=str(payload.get("type") or "string").strip() or "string",
                required=bool(payload.get("required", default is None)),
                description=str(payload.get("description") or "").strip(),
                default=default,
            )
        )
    return tuple(inputs), issues


def _parse_steps(value: Any, workflow_ref: str, path: str) -> tuple[tuple[WorkflowStep, ...], list[WorkflowIssue]]:
    if not isinstance(value, list):
        return (), [workflow_issue(workflow_ref, path, "steps must be a list")]
    steps: list[WorkflowStep] = []
    issues: list[WorkflowIssue] = []
    seen: set[str] = set()
    for index, raw in enumerate(value, 1):
        if not isinstance(raw, dict):
            issues.append(workflow_issue(workflow_ref, path, f"steps[{index}] must be an object"))
            continue
        step_id = plugin_helpers.safe_plugin_id(raw.get("id"))
        if not step_id:
            issues.append(workflow_issue(workflow_ref, path, f"steps[{index}] has an invalid id"))
            continue
        key = step_id.casefold()
        if key in seen:
            issues.append(workflow_issue(workflow_ref, path, f"steps[{index}] duplicates id {step_id}"))
            continue
        seen.add(key)
        step_type = str(raw.get("type") or "").strip()
        if step_type not in WORKFLOW_STEP_TYPES:
            issues.append(workflow_issue(workflow_ref, path, f"steps[{index}] has unsupported type {step_type or '(missing)'}"))
        steps.append(
            WorkflowStep(
                step_id=step_id,
                step_type=step_type,
                name=str(raw.get("name") or step_id).strip() or step_id,
                description=str(raw.get("description") or "").strip(),
                depends_on=_string_items(raw.get("depends_on", raw.get("after", []))),
                agent=str(raw.get("agent") or raw.get("target_agent") or "").strip(),
                prompt=str(raw.get("prompt") or "").strip(),
                ref=str(raw.get("ref") or raw.get("from") or "").strip(),
                payload=dict(raw),
            )
        )
    step_ids = {step.step_id for step in steps}
    for step in steps:
        for dependency in step.depends_on:
            if dependency not in step_ids:
                issues.append(workflow_issue(workflow_ref, path, f"steps[{step.step_id}] depends on missing step {dependency}"))
    if not steps:
        issues.append(workflow_issue(workflow_ref, path, "steps must include at least one step"))
    return tuple(steps), issues


def load_workflow_definition(workflow: plugin_helpers.PluginWorkflow) -> WorkflowLoadResult:
    workflow_ref = workflow.ref
    path = workflow.path
    if not workflow.exists or not os.path.isfile(path):
        return WorkflowLoadResult(
            workflow_ref=workflow_ref,
            path=path,
            issues=(workflow_issue(workflow_ref, path, "workflow file does not exist"),),
        )
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except Exception as exc:
        return WorkflowLoadResult(
            workflow_ref=workflow_ref,
            path=path,
            issues=(workflow_issue(workflow_ref, path, f"workflow file cannot be read: {exc}"),),
        )
    payload, payload_issues = _payload_from_text(text, workflow_ref, path)
    if payload is None:
        return WorkflowLoadResult(workflow_ref=workflow_ref, path=path, issues=payload_issues)
    issues = list(payload_issues)
    if payload.get("schema_version") != WORKFLOW_SCHEMA_VERSION:
        issues.append(workflow_issue(workflow_ref, path, f"schema_version must be {WORKFLOW_SCHEMA_VERSION}"))
    workflow_id = plugin_helpers.safe_plugin_id(payload.get("id"))
    if not workflow_id:
        issues.append(workflow_issue(workflow_ref, path, "workflow id is required and must be filesystem-safe"))
        workflow_id = workflow.workflow_id
    elif workflow_id != workflow.workflow_id:
        issues.append(workflow_issue(workflow_ref, path, f"workflow id {workflow_id} does not match manifest id {workflow.workflow_id}"))
    inputs, input_issues = _parse_inputs(payload.get("inputs"), workflow_ref, path)
    issues.extend(input_issues)
    steps, step_issues = _parse_steps(payload.get("steps"), workflow_ref, path)
    issues.extend(step_issues)
    permissions = payload.get("permissions") if isinstance(payload.get("permissions"), dict) else {}
    definition = WorkflowDefinition(
        workflow_ref=workflow_ref,
        plugin_id=workflow.plugin_id,
        workflow_id=workflow_id,
        name=str(payload.get("name") or workflow.name or workflow_id).strip() or workflow_id,
        description=str(payload.get("description") or workflow.description or "").strip(),
        path=path,
        inputs=inputs,
        steps=steps,
        permissions=dict(permissions),
    )
    return WorkflowLoadResult(workflow_ref=workflow_ref, path=path, definition=definition, issues=tuple(issues))


def workflow_load_result_for_ref(ref: Any, registry: plugin_helpers.PluginRegistry) -> WorkflowLoadResult:
    text = str(ref or "").strip()
    workflow = plugin_helpers.plugin_workflow_for_ref(text, registry)
    if workflow is None:
        return WorkflowLoadResult(
            workflow_ref=text or "(missing)",
            path="",
            issues=(workflow_issue(text or "(missing)", "", f"Workflow not found: {text or '(missing)'}"),),
        )
    return load_workflow_definition(workflow)


def all_workflow_load_results(registry: plugin_helpers.PluginRegistry) -> tuple[WorkflowLoadResult, ...]:
    results: list[WorkflowLoadResult] = []
    for plugin_id in sorted(registry.plugins):
        plugin = registry.plugins[plugin_id]
        for workflow in sorted(plugin.workflows, key=lambda item: item.workflow_id):
            results.append(load_workflow_definition(workflow))
    return tuple(results)


def workflow_result_status(result: WorkflowLoadResult) -> str:
    if result.definition is None:
        return "error"
    if result.issues:
        return "warning"
    return "ok"


def _json_block(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {}, ensure_ascii=False, indent=2, sort_keys=True)


def format_workflow_list(registry: plugin_helpers.PluginRegistry) -> str:
    results = all_workflow_load_results(registry)
    lines: list[str] = []
    if not results:
        lines.append("No workflows found.")
    else:
        lines.append("Workflows:")
        for result in results:
            status = workflow_result_status(result)
            definition = result.definition
            if definition is None:
                lines.append(f"- {result.workflow_ref} - {status}")
            else:
                lines.append(f"- {definition.workflow_ref} - {definition.name} - {status} - steps:{len(definition.steps)}")
                if definition.description:
                    lines.append(f"  {definition.description}")
    issues = [issue for result in results for issue in result.issues]
    if issues:
        lines.append("Validation issues:")
        for issue in issues[:20]:
            lines.append(f"- {issue.workflow_ref}: {issue.message}")
    return "\n".join(lines)


def format_workflow_info(result: WorkflowLoadResult) -> str:
    definition = result.definition
    lines: list[str] = []
    if definition is None:
        lines.extend([
            f"workflow: {result.workflow_ref}",
            f"path: {result.path or '(none)'}",
            "status: error",
        ])
    else:
        lines.extend([
            f"workflow: {definition.workflow_ref}",
            f"name: {definition.name}",
            f"description: {definition.description or '(none)'}",
            f"path: {definition.path}",
            f"status: {workflow_result_status(result)}",
            "inputs:",
        ])
        if definition.inputs:
            for item in definition.inputs:
                default = "" if item.default is None else f" default={item.default!r}"
                required = "required" if item.required else "optional"
                desc = f" - {item.description}" if item.description else ""
                lines.append(f"- {item.input_id}: {item.input_type} {required}{default}{desc}")
        else:
            lines.append("- (none)")
        lines.append("permissions:")
        lines.append(_json_block(definition.permissions))
        lines.append("steps:")
        for index, step in enumerate(definition.steps, 1):
            target = f" agent={step.agent}" if step.agent else ""
            dependency = f" after={','.join(step.depends_on)}" if step.depends_on else ""
            lines.append(f"{index}. {step.step_id} [{step.step_type}]{target}{dependency} - {step.name}")
            if step.description:
                lines.append(f"   {step.description}")
    if result.issues:
        lines.append("validation_issues:")
        for issue in result.issues[:20]:
            lines.append(f"- {issue.message}")
    return "\n".join(lines)


def format_workflow_dry_run(result: WorkflowLoadResult) -> str:
    definition = result.definition
    lines = [
        f"Workflow dry-run: {result.workflow_ref}",
        "No execution occurred.",
        "",
    ]
    if definition is None:
        lines.extend([
            "Status: error",
            f"Path: {result.path or '(none)'}",
        ])
    else:
        lines.extend([
            f"Status: {workflow_result_status(result)}",
            f"Name: {definition.name}",
            f"Path: {definition.path}",
            "",
            "Inputs:",
        ])
        if definition.inputs:
            for item in definition.inputs:
                required = "required" if item.required else "optional"
                lines.append(f"- {item.input_id} ({item.input_type}, {required})")
        else:
            lines.append("- (none)")
        lines.extend(["", "Planned steps:"])
        for index, step in enumerate(definition.steps, 1):
            pieces = [f"{index}. {step.step_id}", f"type={step.step_type}"]
            if step.agent:
                pieces.append(f"agent={step.agent}")
            if step.depends_on:
                pieces.append(f"after={','.join(step.depends_on)}")
            if step.ref:
                pieces.append(f"ref={step.ref}")
            lines.append(" - ".join(pieces))
            if step.prompt:
                lines.append(f"   prompt: {step.prompt}")
            if step.description:
                lines.append(f"   description: {step.description}")
    if result.issues:
        lines.extend(["", "Validation issues:"])
        for issue in result.issues[:20]:
            lines.append(f"- {issue.message}")
    return "\n".join(lines)


def workflow_step_run_snapshot(step: WorkflowStep, *, order: int) -> dict[str, Any]:
    return {
        "step_id": step.step_id,
        "order": order,
        "type": step.step_type,
        "name": step.name,
        "description": step.description,
        "depends_on": list(step.depends_on),
        "agent": step.agent,
        "ref": step.ref,
        "prompt": step.prompt,
        "status": "pending",
        "started_at": "",
        "completed_at": "",
        "artifact_refs": [],
        "approval_id": "",
        "task_id": "",
        "error": "",
    }


def build_workflow_run_record(
    result: WorkflowLoadResult,
    *,
    run_id: str,
    timestamp: str,
    inputs: dict[str, Any] | None = None,
    source: str = "workflow_command",
) -> WorkflowRunBuildResult:
    issues = tuple(result.issues)
    definition = result.definition
    if definition is None:
        return WorkflowRunBuildResult(record=None, issues=issues or (
            workflow_issue(result.workflow_ref, result.path, "workflow definition is missing"),
        ))
    if issues:
        return WorkflowRunBuildResult(record=None, issues=issues)
    safe_run_id = plugin_helpers.safe_plugin_id(run_id)
    if not safe_run_id:
        return WorkflowRunBuildResult(record=None, issues=(
            workflow_issue(definition.workflow_ref, definition.path, "run_id is required and must be filesystem-safe"),
        ))
    row = {
        "schema_version": WORKFLOW_RUN_SCHEMA_VERSION,
        "run_id": safe_run_id,
        "timestamp": timestamp,
        "status": "planned",
        "source": source,
        "workflow_ref": definition.workflow_ref,
        "plugin_id": definition.plugin_id,
        "workflow_id": definition.workflow_id,
        "workflow_name": definition.name,
        "workflow_description": definition.description,
        "workflow_path": definition.path,
        "inputs": dict(inputs or {}),
        "permissions": dict(definition.permissions or {}),
        "validation_issues": [],
        "steps": [
            workflow_step_run_snapshot(step, order=index)
            for index, step in enumerate(definition.steps, 1)
        ],
        "execution": {
            "mode": "planned_only",
            "steps_executed": 0,
            "subagents_dispatched": 0,
            "approvals_created": 0,
            "tools_called": 0,
            "artifacts_written": 0,
            "task_ledger_rows_written": 0,
            "progress_ledger_rows_written": 0,
            "plugin_code_executed": False,
            "runner_started": False,
        },
        "approval": {
            "approval_status": "not_required",
            "approval_id": "",
            "approval_required_for": [],
        },
        "artifact_refs": [],
        "task_refs": [],
        "error": "",
    }
    return WorkflowRunBuildResult(record=row, issues=())


def _completed_step_ids(steps: list[Any]) -> set[str]:
    completed: set[str] = set()
    for raw in steps:
        if not isinstance(raw, dict):
            continue
        if raw.get("status") == "completed" and str(raw.get("step_id") or "").strip():
            completed.add(str(raw.get("step_id")).strip())
    return completed


def _workflow_run_status_for_blocked_step(step: dict[str, Any]) -> tuple[str, str]:
    step_id = str(step.get("step_id") or "").strip() or "(unknown)"
    step_type = str(step.get("type") or "").strip()
    if step_type == "approval":
        return "waiting_approval", f"step {step_id} requires human approval"
    if step_type == "agent_task":
        return "blocked", f"step {step_id} requires subagent dispatch, which workflow runner v0 does not perform"
    if step_type == "condition":
        return "blocked", f"step {step_id} requires condition evaluation, which workflow runner v0 does not perform"
    return "blocked", f"step {step_id} has unsupported runner v0 type {step_type or '(missing)'}"


def advance_workflow_run_v0(row: dict[str, Any], *, timestamp: str) -> WorkflowRunAdvanceResult:
    advanced = deepcopy(row)
    steps = advanced.get("steps") if isinstance(advanced.get("steps"), list) else []
    completed_step_ids: list[str] = []
    blocked_step: dict[str, Any] | None = None
    blocked_reason = ""
    completed = _completed_step_ids(steps)
    for raw_step in steps:
        if not isinstance(raw_step, dict):
            continue
        step_id = str(raw_step.get("step_id") or "").strip()
        step_type = str(raw_step.get("type") or "").strip()
        if not step_id or raw_step.get("status") == "completed":
            continue
        dependencies = [
            str(item or "").strip()
            for item in raw_step.get("depends_on", [])
            if str(item or "").strip()
        ]
        missing_dependencies = [dependency for dependency in dependencies if dependency not in completed]
        if missing_dependencies:
            blocked_step = raw_step
            blocked_reason = (
                f"step {step_id} is waiting for incomplete dependencies: "
                + ", ".join(missing_dependencies)
            )
            raw_step["status"] = "blocked"
            raw_step["error"] = blocked_reason
            break
        if step_type in WORKFLOW_RUNNER_V0_SAFE_STEP_TYPES:
            raw_step["status"] = "completed"
            raw_step["started_at"] = timestamp
            raw_step["completed_at"] = timestamp
            raw_step["error"] = ""
            completed.add(step_id)
            completed_step_ids.append(step_id)
            continue
        blocked_step = raw_step
        status, blocked_reason = _workflow_run_status_for_blocked_step(raw_step)
        raw_step["status"] = status
        raw_step["error"] = blocked_reason
        break
    if blocked_step is None:
        status = "completed"
        blocked_step_id = ""
        blocked_step_type = ""
        completed_at = timestamp
    else:
        status = str(blocked_step.get("status") or "blocked")
        blocked_step_id = str(blocked_step.get("step_id") or "").strip()
        blocked_step_type = str(blocked_step.get("type") or "").strip()
        completed_at = ""
    execution = dict(advanced.get("execution") if isinstance(advanced.get("execution"), dict) else {})
    execution.update({
        "mode": "workflow_runner_v0",
        "runner_started": True,
        "runner_version": "workflow_runner_v0",
        "runner_started_at": timestamp,
        "runner_updated_at": timestamp,
        "runner_completed_at": completed_at,
        "steps_executed": len(completed_step_ids),
        "subagents_dispatched": 0,
        "approvals_created": 0,
        "tools_called": 0,
        "artifacts_written": 0,
        "task_ledger_rows_written": 0,
        "progress_ledger_rows_written": 0,
        "plugin_code_executed": False,
        "blocked_step_id": blocked_step_id,
        "blocked_step_type": blocked_step_type,
        "blocked_reason": blocked_reason,
    })
    advanced["execution"] = execution
    advanced["status"] = status
    advanced["updated_at"] = timestamp
    advanced["completed_at"] = completed_at
    advanced["error"] = blocked_reason
    approval = dict(advanced.get("approval") if isinstance(advanced.get("approval"), dict) else {})
    if status == "waiting_approval":
        approval.update({
            "approval_status": "pending",
            "approval_id": "",
            "approval_required_for": [blocked_step_id] if blocked_step_id else [],
        })
    else:
        approval.update({
            "approval_status": "not_required",
            "approval_id": "",
            "approval_required_for": [],
        })
    advanced["approval"] = approval
    return WorkflowRunAdvanceResult(
        record=advanced,
        status=status,
        completed_step_ids=tuple(completed_step_ids),
        blocked_step_id=blocked_step_id,
        blocked_step_type=blocked_step_type,
        blocked_reason=blocked_reason,
    )


def format_workflow_run_created(row: dict[str, Any]) -> str:
    run_id = str(row.get("run_id") or "-")
    workflow_ref = str(row.get("workflow_ref") or "-")
    steps = row.get("steps") if isinstance(row.get("steps"), list) else []
    return "\n".join([
        f"Workflow run planned: {run_id}",
        f"status: {row.get('status') or 'planned'}",
        f"workflow: {workflow_ref}",
        f"steps: {len(steps)} pending",
        "No workflow steps executed.",
        "No subagents, approvals, tools, artifacts, task ledger rows, or progress ledger rows were created.",
    ])


def format_workflow_run_advanced(result: WorkflowRunAdvanceResult) -> str:
    row = result.record
    run_id = str(row.get("run_id") or "-")
    workflow_ref = str(row.get("workflow_ref") or "-")
    lines = [
        f"Workflow run advanced: {run_id}",
        f"status: {result.status}",
        f"workflow: {workflow_ref}",
        f"safe steps completed: {len(result.completed_step_ids)}",
    ]
    if result.completed_step_ids:
        lines.append("completed: " + ", ".join(result.completed_step_ids))
    if result.blocked_step_id:
        lines.append(f"stopped_at: {result.blocked_step_id} [{result.blocked_step_type or 'unknown'}]")
        lines.append(f"reason: {result.blocked_reason}")
    elif result.status == "completed":
        lines.append("All workflow runner v0 safe steps completed.")
    lines.append("No subagents, approvals, tools, artifacts, task ledger rows, or progress ledger rows were created.")
    return "\n".join(lines)


def format_workflow_run_rejected(result: WorkflowLoadResult, issues: tuple[WorkflowIssue, ...]) -> str:
    lines = [
        f"Workflow run rejected: {result.workflow_ref}",
        "No workflow run record was created.",
        "Validation issues:",
    ]
    for issue in issues[:20]:
        lines.append(f"- {issue.message}")
    return "\n".join(lines)
