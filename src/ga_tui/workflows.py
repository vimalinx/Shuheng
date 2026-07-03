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
WORKFLOW_RUN_TERMINAL_STATUSES = frozenset({
    "completed",
    "failed",
    "rejected",
    "cancelled",
    "canceled",
    "aborted",
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
class WorkflowDraftResult:
    payload: dict[str, Any] | None
    load_result: WorkflowLoadResult


@dataclass(frozen=True)
class WorkflowRunBuildResult:
    record: dict[str, Any] | None = None
    issues: tuple[WorkflowIssue, ...] = ()


@dataclass(frozen=True)
class WorkflowInputResolveResult:
    inputs: dict[str, Any]
    issues: tuple[WorkflowIssue, ...] = ()


@dataclass(frozen=True)
class WorkflowRunAdvanceResult:
    record: dict[str, Any]
    status: str
    completed_step_ids: tuple[str, ...] = ()
    blocked_step_id: str = ""
    blocked_step_type: str = ""
    blocked_reason: str = ""


@dataclass(frozen=True)
class WorkflowRunContinueResult:
    run_id: str
    status: str
    record: dict[str, Any] | None = None
    advanced: WorkflowRunAdvanceResult | None = None
    history_rows: int = 0
    reason: str = ""
    approval_id: str = ""
    task_id: str = ""
    task_status: str = ""
    run_status: str = ""


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


def workflow_load_result_from_payload(
    payload: dict[str, Any],
    *,
    plugin_id: str,
    workflow_id: str,
    workflow_ref: str = "",
    path: str = "(draft)",
    name: str = "",
    description: str = "",
) -> WorkflowLoadResult:
    target_workflow_id = plugin_helpers.safe_plugin_id(workflow_id)
    target_plugin_id = plugin_helpers.safe_plugin_id(plugin_id)
    ref = workflow_ref or plugin_helpers.plugin_workflow_ref(target_plugin_id, target_workflow_id)
    issues: list[WorkflowIssue] = []
    if not isinstance(payload, dict):
        return WorkflowLoadResult(
            workflow_ref=ref or "(draft)",
            path=path,
            issues=(workflow_issue(ref or "(draft)", path, "workflow payload must contain a JSON object"),),
        )
    if payload.get("schema_version") != WORKFLOW_SCHEMA_VERSION:
        issues.append(workflow_issue(ref, path, f"schema_version must be {WORKFLOW_SCHEMA_VERSION}"))
    parsed_workflow_id = plugin_helpers.safe_plugin_id(payload.get("id"))
    if not parsed_workflow_id:
        issues.append(workflow_issue(ref, path, "workflow id is required and must be filesystem-safe"))
        parsed_workflow_id = target_workflow_id
    elif target_workflow_id and parsed_workflow_id != target_workflow_id:
        issues.append(workflow_issue(ref, path, f"workflow id {parsed_workflow_id} does not match manifest id {target_workflow_id}"))
    inputs, input_issues = _parse_inputs(payload.get("inputs"), ref, path)
    issues.extend(input_issues)
    steps, step_issues = _parse_steps(payload.get("steps"), ref, path)
    issues.extend(step_issues)
    permissions = payload.get("permissions") if isinstance(payload.get("permissions"), dict) else {}
    resolved_workflow_id = parsed_workflow_id or target_workflow_id
    definition = WorkflowDefinition(
        workflow_ref=ref,
        plugin_id=target_plugin_id,
        workflow_id=resolved_workflow_id,
        name=str(payload.get("name") or name or resolved_workflow_id).strip() or resolved_workflow_id,
        description=str(payload.get("description") or description or "").strip(),
        path=path,
        inputs=inputs,
        steps=steps,
        permissions=dict(permissions),
    )
    return WorkflowLoadResult(workflow_ref=ref, path=path, definition=definition, issues=tuple(issues))


def workflow_draft_load_result_from_text(text: str, *, workflow_ref: str = "workflow-draft", path: str = "(model)") -> WorkflowLoadResult:
    return workflow_draft_result_from_text(text, workflow_ref=workflow_ref, path=path).load_result


def workflow_draft_result_from_text(text: str, *, workflow_ref: str = "workflow-draft", path: str = "(model)") -> WorkflowDraftResult:
    payload, payload_issues = _payload_from_text(text, workflow_ref, path)
    if payload is None:
        return WorkflowDraftResult(
            payload=None,
            load_result=WorkflowLoadResult(workflow_ref=workflow_ref, path=path, issues=payload_issues),
        )
    workflow_id = plugin_helpers.safe_plugin_id(payload.get("id")) or "generated-workflow"
    plugin_id, parsed_workflow_id = plugin_helpers.parse_plugin_workflow_ref(workflow_ref)
    if parsed_workflow_id:
        workflow_id = parsed_workflow_id
    result_ref = workflow_ref if plugin_id and parsed_workflow_id else f"draft://workflow/{workflow_id}"
    return WorkflowDraftResult(
        payload=payload,
        load_result=workflow_load_result_from_payload(
            payload,
            plugin_id=plugin_id or "draft",
            workflow_id=workflow_id,
            workflow_ref=result_ref,
            path=path,
        ),
    )


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
    return workflow_load_result_from_payload(
        payload,
        plugin_id=workflow.plugin_id,
        workflow_id=workflow.workflow_id,
        workflow_ref=workflow_ref,
        path=path,
        name=workflow.name,
        description=workflow.description,
    )


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
    snapshot = {
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
    payload = step.payload if isinstance(step.payload, dict) else {}
    for key in ("condition", "when", "expression"):
        if key in payload:
            snapshot[key] = deepcopy(payload.get(key))
    return snapshot


def resolve_workflow_run_inputs(
    definition: WorkflowDefinition,
    inputs: dict[str, Any] | None = None,
) -> WorkflowInputResolveResult:
    explicit = dict(inputs or {})
    if not definition.inputs:
        return WorkflowInputResolveResult(inputs=explicit)

    declared = {item.input_id: item for item in definition.inputs}
    issues: list[WorkflowIssue] = []
    for key in explicit:
        input_id = plugin_helpers.safe_plugin_id(key)
        if not input_id:
            issues.append(workflow_issue(definition.workflow_ref, definition.path, f"workflow input key is invalid: {key}"))
        elif input_id not in declared:
            issues.append(workflow_issue(definition.workflow_ref, definition.path, f"unknown workflow input: {input_id}"))
    if issues:
        return WorkflowInputResolveResult(inputs={}, issues=tuple(issues))

    resolved: dict[str, Any] = {}
    for item in definition.inputs:
        if item.input_id in explicit:
            resolved[item.input_id] = explicit[item.input_id]
            continue
        if item.default is not None:
            resolved[item.input_id] = deepcopy(item.default)
            continue
        if item.required:
            issues.append(workflow_issue(definition.workflow_ref, definition.path, f"required workflow input is missing: {item.input_id}"))
    if issues:
        return WorkflowInputResolveResult(inputs={}, issues=tuple(issues))
    return WorkflowInputResolveResult(inputs=resolved)


@dataclass(frozen=True)
class _WorkflowConditionEvaluation:
    supported: bool
    passed: bool
    reason: str = ""


def _condition_ref_value(ref: Any, inputs: dict[str, Any]) -> tuple[bool, bool, Any, str]:
    text = str(ref or "").strip()
    if not text.startswith("inputs."):
        return False, False, None, f"condition ref must read inputs.<id>, got {text or '(missing)'}"
    input_id = text[len("inputs.") :]
    if not plugin_helpers.safe_plugin_id(input_id):
        return False, False, None, f"condition ref has invalid input id: {text}"
    return True, input_id in inputs, inputs.get(input_id), ""


def _evaluate_condition_predicate(predicate: Any, inputs: dict[str, Any]) -> _WorkflowConditionEvaluation:
    if not isinstance(predicate, dict):
        return _WorkflowConditionEvaluation(
            supported=False,
            passed=False,
            reason="condition requires condition evaluation via condition v1 JSON predicate object",
        )

    if "all" in predicate:
        children = predicate.get("all")
        if not isinstance(children, list):
            return _WorkflowConditionEvaluation(False, False, "condition all operator must contain a list")
        for child in children:
            result = _evaluate_condition_predicate(child, inputs)
            if not result.supported or not result.passed:
                return result
        return _WorkflowConditionEvaluation(True, True, "condition evaluated true")

    if "any" in predicate:
        children = predicate.get("any")
        if not isinstance(children, list):
            return _WorkflowConditionEvaluation(False, False, "condition any operator must contain a list")
        false_reasons: list[str] = []
        for child in children:
            result = _evaluate_condition_predicate(child, inputs)
            if not result.supported:
                return result
            if result.passed:
                return _WorkflowConditionEvaluation(True, True, "condition evaluated true")
            if result.reason:
                false_reasons.append(result.reason)
        reason = false_reasons[0] if false_reasons else "condition any operator had no matching predicate"
        return _WorkflowConditionEvaluation(True, False, reason)

    if "not" in predicate:
        result = _evaluate_condition_predicate(predicate.get("not"), inputs)
        if not result.supported:
            return result
        return _WorkflowConditionEvaluation(True, not result.passed, "condition evaluated true" if not result.passed else "condition not predicate evaluated false")

    if "ref" not in predicate:
        return _WorkflowConditionEvaluation(False, False, "condition predicate must include ref or all/any/not")

    ok, exists, value, reason = _condition_ref_value(predicate.get("ref"), inputs)
    if not ok:
        return _WorkflowConditionEvaluation(False, False, reason)

    operator_keys = [
        key
        for key in ("equals", "not_equals", "exists", "truthy", "in")
        if key in predicate
    ]
    if len(operator_keys) != 1:
        return _WorkflowConditionEvaluation(False, False, "condition predicate must include exactly one supported operator")

    operator = operator_keys[0]
    ref = str(predicate.get("ref") or "").strip()
    if operator == "exists":
        expected = bool(predicate.get("exists"))
        passed = exists is expected
        reason = "condition evaluated true" if passed else f"condition {ref} exists={exists}, expected {expected}"
        return _WorkflowConditionEvaluation(True, passed, reason)
    if not exists:
        return _WorkflowConditionEvaluation(True, False, f"condition {ref} is missing")
    if operator == "truthy":
        expected = bool(predicate.get("truthy"))
        actual = bool(value)
        passed = actual is expected
        reason = "condition evaluated true" if passed else f"condition {ref} truthy={actual}, expected {expected}"
        return _WorkflowConditionEvaluation(True, passed, reason)
    if operator == "equals":
        expected = predicate.get("equals")
        passed = value == expected
        reason = "condition evaluated true" if passed else f"condition {ref} value did not equal {expected!r}"
        return _WorkflowConditionEvaluation(True, passed, reason)
    if operator == "not_equals":
        expected = predicate.get("not_equals")
        passed = value != expected
        reason = "condition evaluated true" if passed else f"condition {ref} value unexpectedly equaled {expected!r}"
        return _WorkflowConditionEvaluation(True, passed, reason)
    options = predicate.get("in")
    if not isinstance(options, list):
        return _WorkflowConditionEvaluation(False, False, "condition in operator must contain a list")
    passed = value in options
    reason = "condition evaluated true" if passed else f"condition {ref} value was not in allowed list"
    return _WorkflowConditionEvaluation(True, passed, reason)


def _evaluate_condition_step_v1(step: dict[str, Any], inputs: dict[str, Any]) -> _WorkflowConditionEvaluation:
    if isinstance(step.get("condition"), dict):
        return _evaluate_condition_predicate(step.get("condition"), inputs)
    if isinstance(step.get("when"), dict):
        return _evaluate_condition_predicate(step.get("when"), inputs)
    if "condition" in step and not isinstance(step.get("condition"), dict):
        return _WorkflowConditionEvaluation(
            supported=False,
            passed=False,
            reason="condition requires condition evaluation via condition v1 JSON predicate object",
        )
    if "when" in step and not isinstance(step.get("when"), dict):
        return _WorkflowConditionEvaluation(
            supported=False,
            passed=False,
            reason="condition requires condition evaluation via condition v1 JSON predicate object",
        )
    if str(step.get("expression") or "").strip():
        return _WorkflowConditionEvaluation(
            supported=False,
            passed=False,
            reason="condition requires condition evaluation via condition v1 JSON predicate; string expressions are not supported",
        )
    return _WorkflowConditionEvaluation(
        supported=False,
        passed=False,
        reason="condition requires condition evaluation via condition v1 JSON predicate",
    )


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
    resolved_inputs = resolve_workflow_run_inputs(definition, inputs)
    if resolved_inputs.issues:
        return WorkflowRunBuildResult(record=None, issues=resolved_inputs.issues)
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
        "inputs": dict(resolved_inputs.inputs),
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
    inputs = advanced.get("inputs") if isinstance(advanced.get("inputs"), dict) else {}
    completed_step_ids: list[str] = []
    blocked_step: dict[str, Any] | None = None
    blocked_reason = ""
    blocked_status = ""
    completed = _completed_step_ids(steps)
    for raw_step in steps:
        if not isinstance(raw_step, dict):
            continue
        step_id = str(raw_step.get("step_id") or "").strip()
        step_type = str(raw_step.get("type") or "").strip()
        step_status = str(raw_step.get("status") or "").strip()
        if not step_id or step_status == "completed":
            continue
        if step_status == "skipped":
            blocked_step = raw_step
            blocked_status = "blocked"
            blocked_reason = str(raw_step.get("error") or f"step {step_id} was skipped")
            break
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
        if step_type == "condition":
            condition = _evaluate_condition_step_v1(raw_step, inputs)
            if not condition.supported:
                blocked_step = raw_step
                blocked_status = "blocked"
                blocked_reason = condition.reason
                raw_step["status"] = "blocked"
                raw_step["error"] = blocked_reason
                break
            raw_step["started_at"] = raw_step.get("started_at") or timestamp
            raw_step["completed_at"] = timestamp
            if condition.passed:
                raw_step["status"] = "completed"
                raw_step["error"] = ""
                completed.add(step_id)
                completed_step_ids.append(step_id)
                continue
            blocked_step = raw_step
            blocked_status = "blocked"
            blocked_reason = condition.reason or f"condition step {step_id} evaluated false"
            raw_step["status"] = "skipped"
            raw_step["error"] = blocked_reason
            break
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
        status = blocked_status or str(blocked_step.get("status") or "blocked")
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
    existing_approval_id = str(approval.get("approval_id") or "").strip()
    existing_approval_status = str(approval.get("approval_status") or "").strip()
    if status == "waiting_approval":
        step_approval_id = str(blocked_step.get("approval_id") or "").strip() if blocked_step else ""
        approval.update({
            "approval_status": "pending",
            "approval_id": existing_approval_id or step_approval_id,
            "approval_required_for": [blocked_step_id] if blocked_step_id else [],
        })
    elif existing_approval_id and existing_approval_status in {"approved", "rejected"}:
        approval.update({
            "approval_status": existing_approval_status,
            "approval_id": existing_approval_id,
            "approval_required_for": approval.get("approval_required_for") or [],
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


def pending_workflow_approval_step(row: dict[str, Any]) -> dict[str, Any] | None:
    if str(row.get("status") or "").strip() != "waiting_approval":
        return None
    execution = row.get("execution") if isinstance(row.get("execution"), dict) else {}
    blocked_step_id = str(execution.get("blocked_step_id") or "").strip()
    steps = row.get("steps") if isinstance(row.get("steps"), list) else []
    fallback: dict[str, Any] | None = None
    for step in steps:
        if not isinstance(step, dict):
            continue
        if str(step.get("type") or "").strip() != "approval":
            continue
        if str(step.get("status") or "").strip() != "waiting_approval":
            continue
        if blocked_step_id and str(step.get("step_id") or "").strip() == blocked_step_id:
            return step
        if fallback is None:
            fallback = step
    return fallback


def workflow_approval_id(row: dict[str, Any]) -> str:
    approval = row.get("approval") if isinstance(row.get("approval"), dict) else {}
    approval_id = str(approval.get("approval_id") or "").strip()
    if approval_id:
        return approval_id
    step = pending_workflow_approval_step(row)
    return str(step.get("approval_id") or "").strip() if step else ""


def pending_workflow_agent_task_step(row: dict[str, Any]) -> dict[str, Any] | None:
    status = str(row.get("status") or "").strip()
    if status not in {"blocked", "waiting_task"}:
        return None
    execution = row.get("execution") if isinstance(row.get("execution"), dict) else {}
    blocked_step_id = str(execution.get("blocked_step_id") or "").strip()
    steps = row.get("steps") if isinstance(row.get("steps"), list) else []
    fallback: dict[str, Any] | None = None
    for step in steps:
        if not isinstance(step, dict):
            continue
        if str(step.get("type") or "").strip() != "agent_task":
            continue
        if str(step.get("status") or "").strip() not in {"blocked", "waiting_task"}:
            continue
        if blocked_step_id and str(step.get("step_id") or "").strip() == blocked_step_id:
            return step
        if fallback is None:
            fallback = step
    return fallback


def workflow_agent_task_id(row: dict[str, Any]) -> str:
    step = pending_workflow_agent_task_step(row)
    return str(step.get("task_id") or "").strip() if step else ""


def _at_least_int(value: Any, minimum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = 0
    return max(parsed, minimum)


def attach_workflow_step_approval(row: dict[str, Any], *, approval_id: str, timestamp: str) -> dict[str, Any]:
    safe_approval_id = str(approval_id or "").strip()
    updated = deepcopy(row)
    if not safe_approval_id:
        return updated
    step = pending_workflow_approval_step(updated)
    if step is None:
        return updated
    step_id = str(step.get("step_id") or "").strip()
    step["approval_id"] = safe_approval_id
    step["status"] = "waiting_approval"
    approval = dict(updated.get("approval") if isinstance(updated.get("approval"), dict) else {})
    approval.update({
        "approval_status": "pending",
        "approval_id": safe_approval_id,
        "approval_required_for": [step_id] if step_id else [],
    })
    updated["approval"] = approval
    execution = dict(updated.get("execution") if isinstance(updated.get("execution"), dict) else {})
    execution["approvals_created"] = _at_least_int(execution.get("approvals_created"), 1)
    execution["blocked_step_id"] = step_id
    execution["blocked_step_type"] = "approval"
    execution["blocked_reason"] = execution.get("blocked_reason") or step.get("error") or (
        f"step {step_id} requires human approval" if step_id else "workflow step requires human approval"
    )
    updated["execution"] = execution
    updated["updated_at"] = timestamp
    updated["status"] = "waiting_approval"
    updated["completed_at"] = ""
    updated["error"] = str(execution.get("blocked_reason") or "")
    return updated


def attach_workflow_agent_task(
    row: dict[str, Any],
    *,
    task_id: str,
    timestamp: str,
    agent_id: str = "",
    task_status: str = "working",
    message: str = "",
) -> dict[str, Any]:
    safe_task_id = str(task_id or "").strip()
    updated = deepcopy(row)
    if not safe_task_id:
        return updated
    step = pending_workflow_agent_task_step(updated)
    if step is None:
        return updated
    step_id = str(step.get("step_id") or "").strip()
    step["task_id"] = safe_task_id
    if agent_id:
        step["agent_id"] = str(agent_id)
    step["task_status"] = str(task_status or "working")
    step["status"] = "waiting_task"
    step["error"] = ""
    if not step.get("started_at"):
        step["started_at"] = timestamp
    execution = dict(updated.get("execution") if isinstance(updated.get("execution"), dict) else {})
    execution["subagents_dispatched"] = _at_least_int(execution.get("subagents_dispatched"), 1)
    execution["task_ledger_rows_written"] = _at_least_int(execution.get("task_ledger_rows_written"), 1)
    execution["progress_ledger_rows_written"] = _at_least_int(execution.get("progress_ledger_rows_written"), 1)
    execution["blocked_step_id"] = step_id
    execution["blocked_step_type"] = "agent_task"
    execution["blocked_reason"] = message or (
        f"step {step_id} is waiting for subagent task {safe_task_id}"
        if step_id else f"workflow is waiting for subagent task {safe_task_id}"
    )
    updated["execution"] = execution
    updated["status"] = "waiting_task"
    updated["updated_at"] = timestamp
    updated["completed_at"] = ""
    updated["error"] = str(execution.get("blocked_reason") or "")
    return updated


def fail_workflow_agent_task_dispatch(
    row: dict[str, Any],
    *,
    timestamp: str,
    error: str,
    status: str = "failed",
) -> dict[str, Any]:
    updated = deepcopy(row)
    step = pending_workflow_agent_task_step(updated)
    if step is None:
        return updated
    terminal_status = str(status or "failed").strip() or "failed"
    step_id = str(step.get("step_id") or "").strip()
    reason = str(error or "workflow agent_task dispatch failed")
    step["status"] = terminal_status
    step["task_status"] = terminal_status
    step["completed_at"] = timestamp
    step["error"] = reason
    execution = dict(updated.get("execution") if isinstance(updated.get("execution"), dict) else {})
    execution["blocked_step_id"] = step_id
    execution["blocked_step_type"] = "agent_task"
    execution["blocked_reason"] = reason
    updated["execution"] = execution
    updated["status"] = terminal_status
    updated["updated_at"] = timestamp
    updated["completed_at"] = timestamp
    updated["error"] = reason
    return updated


def _unique_strings(*groups: Any) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        if isinstance(group, str):
            iterable = [group]
        elif isinstance(group, (list, tuple, set)):
            iterable = group
        else:
            iterable = []
        for raw in iterable:
            value = str(raw or "").strip()
            if value and value not in seen:
                seen.add(value)
                values.append(value)
    return values


def apply_workflow_agent_task_result(
    row: dict[str, Any],
    *,
    task_row: dict[str, Any],
    timestamp: str,
) -> dict[str, Any]:
    updated = deepcopy(row)
    step = pending_workflow_agent_task_step(updated)
    if step is None:
        return updated
    step_id = str(step.get("step_id") or "").strip()
    task_id = str(task_row.get("task_id") or step.get("task_id") or "").strip()
    task_status = str(task_row.get("status") or "").strip().lower()
    artifacts = _unique_strings(step.get("artifact_refs"), task_row.get("artifact_refs"))
    step["task_id"] = task_id
    step["task_status"] = task_status
    step["artifact_refs"] = artifacts
    if str(task_row.get("assigned_agent") or "").strip():
        step["agent_id"] = str(task_row.get("assigned_agent") or "").strip()
    execution = dict(updated.get("execution") if isinstance(updated.get("execution"), dict) else {})
    execution["subagents_dispatched"] = _at_least_int(execution.get("subagents_dispatched"), 1)
    execution["task_ledger_rows_written"] = _at_least_int(execution.get("task_ledger_rows_written"), 1)
    execution["progress_ledger_rows_written"] = _at_least_int(execution.get("progress_ledger_rows_written"), 1)
    updated["artifact_refs"] = _unique_strings(updated.get("artifact_refs"), artifacts)
    if task_status == "completed":
        step["status"] = "completed"
        step["started_at"] = step.get("started_at") or str(task_row.get("timestamp") or timestamp)
        step["completed_at"] = timestamp
        step["error"] = ""
        execution["blocked_step_id"] = ""
        execution["blocked_step_type"] = ""
        execution["blocked_reason"] = ""
        updated["execution"] = execution
        updated["error"] = ""
        updated["updated_at"] = timestamp
        return updated
    terminal_status = "cancelled" if task_status == "canceled" else (task_status or "failed")
    reason = str(task_row.get("error") or task_row.get("summary") or f"subagent task {task_id} ended with {terminal_status}")
    step["status"] = terminal_status
    step["completed_at"] = timestamp
    step["error"] = reason
    execution["blocked_step_id"] = step_id
    execution["blocked_step_type"] = "agent_task"
    execution["blocked_reason"] = reason
    updated["execution"] = execution
    updated["status"] = terminal_status
    updated["updated_at"] = timestamp
    updated["completed_at"] = timestamp
    updated["error"] = reason
    return updated


def apply_workflow_step_approval_decision(
    row: dict[str, Any],
    *,
    approval_id: str,
    approved: bool,
    timestamp: str,
    reason: str = "",
) -> dict[str, Any]:
    safe_approval_id = str(approval_id or "").strip()
    updated = deepcopy(row)
    step = pending_workflow_approval_step(updated)
    if step is None:
        return updated
    step_id = str(step.get("step_id") or "").strip()
    approval = dict(updated.get("approval") if isinstance(updated.get("approval"), dict) else {})
    approval.update({
        "approval_status": "approved" if approved else "rejected",
        "approval_id": safe_approval_id or str(approval.get("approval_id") or step.get("approval_id") or ""),
        "approval_required_for": [step_id] if step_id else [],
    })
    updated["approval"] = approval
    execution = dict(updated.get("execution") if isinstance(updated.get("execution"), dict) else {})
    execution["approvals_created"] = _at_least_int(execution.get("approvals_created"), 1)
    if approved:
        step["status"] = "completed"
        step["approval_id"] = approval["approval_id"]
        step["started_at"] = step.get("started_at") or timestamp
        step["completed_at"] = timestamp
        step["error"] = ""
        execution["blocked_step_id"] = ""
        execution["blocked_step_type"] = ""
        execution["blocked_reason"] = ""
        updated["execution"] = execution
        updated["error"] = ""
        updated["updated_at"] = timestamp
        return updated
    rejected_reason = reason or f"workflow approval rejected: {approval['approval_id'] or step_id}"
    step["status"] = "rejected"
    step["approval_id"] = approval["approval_id"]
    step["started_at"] = step.get("started_at") or timestamp
    step["completed_at"] = timestamp
    step["error"] = rejected_reason
    execution["blocked_step_id"] = step_id
    execution["blocked_step_type"] = "approval"
    execution["blocked_reason"] = rejected_reason
    updated["execution"] = execution
    updated["status"] = "rejected"
    updated["updated_at"] = timestamp
    updated["completed_at"] = timestamp
    updated["error"] = rejected_reason
    return updated


def _workflow_side_effect_footer(row: dict[str, Any]) -> str:
    execution = row.get("execution") if isinstance(row.get("execution"), dict) else {}
    approvals_created = _at_least_int(execution.get("approvals_created"), 0)
    subagents_dispatched = _at_least_int(execution.get("subagents_dispatched"), 0)
    if subagents_dispatched:
        approval_note = f" Approvals created: {approvals_created}." if approvals_created else ""
        return (
            f"Subagents dispatched: {subagents_dispatched}."
            f"{approval_note} "
            "Subagent task pipeline owns task/progress/artifact ledgers; no workflow-owned tools were called."
        )
    if approvals_created:
        return (
            f"Approvals created: {approvals_created}. "
            "No subagents, tools, artifacts, task ledger rows, or progress ledger rows were created."
        )
    return "No subagents, approvals, tools, artifacts, task ledger rows, or progress ledger rows were created."


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
    lines.append(_workflow_side_effect_footer(row))
    return "\n".join(lines)


def _workflow_step_signature(step: Any) -> tuple[Any, ...]:
    if not isinstance(step, dict):
        return ()
    return (
        step.get("step_id"),
        step.get("status"),
        step.get("started_at"),
        step.get("completed_at"),
        step.get("artifact_refs"),
        step.get("approval_id"),
        step.get("task_id"),
        step.get("task_status"),
        step.get("agent_id"),
        step.get("error"),
    )


def workflow_run_has_meaningful_transition(before: dict[str, Any], after: dict[str, Any]) -> bool:
    before_steps = before.get("steps") if isinstance(before.get("steps"), list) else []
    after_steps = after.get("steps") if isinstance(after.get("steps"), list) else []
    before_execution = before.get("execution") if isinstance(before.get("execution"), dict) else {}
    after_execution = after.get("execution") if isinstance(after.get("execution"), dict) else {}
    before_approval = before.get("approval") if isinstance(before.get("approval"), dict) else {}
    after_approval = after.get("approval") if isinstance(after.get("approval"), dict) else {}
    return (
        before.get("status") != after.get("status")
        or before.get("completed_at") != after.get("completed_at")
        or before.get("error") != after.get("error")
        or [_workflow_step_signature(step) for step in before_steps] != [
            _workflow_step_signature(step) for step in after_steps
        ]
        or before_execution.get("blocked_step_id") != after_execution.get("blocked_step_id")
        or before_execution.get("blocked_step_type") != after_execution.get("blocked_step_type")
        or before_execution.get("blocked_reason") != after_execution.get("blocked_reason")
        or before_approval != after_approval
    )


def format_workflow_continue_result(result: WorkflowRunContinueResult) -> str:
    run_id = result.run_id or "(missing)"
    if result.status == "not_found":
        return f"Workflow run not found: {run_id}"
    if result.status == "already_completed":
        return "\n".join([
            f"Workflow run already completed: {run_id}",
            f"history_rows: {result.history_rows}",
            "No workflow run row was appended.",
        ])
    if result.status == "already_terminal":
        lines = [
            f"Workflow run already terminal: {run_id}",
            f"status: {result.run_status or '-'}",
            f"history_rows: {result.history_rows}",
        ]
        if result.reason:
            lines.append(f"reason: {result.reason}")
        lines.append("No workflow run row was appended.")
        return "\n".join(lines)
    if result.status == "no_progress":
        lines = [
            f"Workflow run cannot continue with runner v0: {run_id}",
            f"history_rows: {result.history_rows}",
        ]
        if result.reason:
            lines.append(f"reason: {result.reason}")
        lines.append("No workflow run row was appended.")
        return "\n".join(lines)
    if result.status == "approval_created":
        lines = [
            f"Workflow approval created: {run_id}",
            f"approval_id: {result.approval_id or '-'}",
            f"history_rows: {result.history_rows}",
            "Approve with /approve <approval_id>, then run /workflow continue <run_id>.",
            "No subagents, tools, artifacts, task ledger rows, or progress ledger rows were created.",
        ]
        return "\n".join(lines)
    if result.status == "approval_pending":
        lines = [
            f"Workflow run waiting for approval: {run_id}",
            f"approval_id: {result.approval_id or '-'}",
            f"history_rows: {result.history_rows}",
        ]
        if result.reason:
            lines.append(f"reason: {result.reason}")
        lines.append("No workflow run row was appended.")
        return "\n".join(lines)
    if result.status == "approval_rejected":
        lines = [
            f"Workflow run rejected by approval: {run_id}",
            f"approval_id: {result.approval_id or '-'}",
            f"history_rows: {result.history_rows}",
        ]
        if result.reason:
            lines.append(f"reason: {result.reason}")
        lines.append("No later workflow steps were continued.")
        return "\n".join(lines)
    if result.status == "task_dispatched":
        lines = [
            f"Workflow agent task dispatched: {run_id}",
            f"task_id: {result.task_id or '-'}",
            f"task_status: {result.task_status or '-'}",
            f"history_rows: {result.history_rows}",
            "Run /workflow continue <run_id> after the subagent task reaches a terminal status.",
        ]
        if result.reason:
            lines.append(f"reason: {result.reason}")
        return "\n".join(lines)
    if result.status == "task_pending":
        lines = [
            f"Workflow run waiting for subagent task: {run_id}",
            f"task_id: {result.task_id or '-'}",
            f"task_status: {result.task_status or '-'}",
            f"history_rows: {result.history_rows}",
            "No workflow run row was appended.",
        ]
        if result.reason:
            lines.append(f"reason: {result.reason}")
        return "\n".join(lines)
    if result.status == "task_terminal":
        lines = [
            f"Workflow run stopped by subagent task: {run_id}",
            f"task_id: {result.task_id or '-'}",
            f"task_status: {result.task_status or '-'}",
            f"history_rows: {result.history_rows}",
            "No later workflow steps were continued.",
        ]
        if result.reason:
            lines.append(f"reason: {result.reason}")
        return "\n".join(lines)
    if result.advanced is None or result.record is None:
        return f"Workflow run continuation failed: {run_id}"
    advanced = result.advanced
    row = result.record
    lines = [
        f"Workflow run continued: {run_id}",
        f"status: {advanced.status}",
        f"workflow: {row.get('workflow_ref') or '-'}",
        f"history_rows: {result.history_rows}",
        f"safe steps completed: {len(advanced.completed_step_ids)}",
    ]
    if advanced.completed_step_ids:
        lines.append("completed: " + ", ".join(advanced.completed_step_ids))
    if advanced.blocked_step_id:
        lines.append(f"stopped_at: {advanced.blocked_step_id} [{advanced.blocked_step_type or 'unknown'}]")
        lines.append(f"reason: {advanced.blocked_reason}")
    elif advanced.status == "completed":
        lines.append("All workflow runner v0 safe steps completed.")
    lines.append(_workflow_side_effect_footer(row))
    return "\n".join(lines)


def _workflow_run_id(row: dict[str, Any]) -> str:
    return str(row.get("run_id") or "").strip()


def _latest_workflow_run_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    order: dict[str, int] = {}
    for index, row in enumerate(rows):
        run_id = _workflow_run_id(row)
        if not run_id:
            continue
        latest[run_id] = row
        order[run_id] = index
    return [
        latest[run_id]
        for run_id in sorted(order, key=lambda item: order[item], reverse=True)
    ]


def _workflow_run_step_counts(row: dict[str, Any]) -> tuple[int, int]:
    steps = row.get("steps") if isinstance(row.get("steps"), list) else []
    total = len([step for step in steps if isinstance(step, dict)])
    completed = len([
        step for step in steps
        if isinstance(step, dict) and step.get("status") == "completed"
    ])
    return completed, total


def _workflow_run_stop_reason(row: dict[str, Any]) -> str:
    execution = row.get("execution") if isinstance(row.get("execution"), dict) else {}
    return str(execution.get("blocked_reason") or row.get("error") or "").strip()


def format_workflow_runs(rows: list[dict[str, Any]], *, limit: int = 20) -> str:
    latest_rows = _latest_workflow_run_rows(rows)
    if not latest_rows:
        return "\n".join([
            "Workflow runs:",
            "- (none)",
            "Run /workflow run <plugin-id>/<workflow-id> to create a workflow run.",
        ])
    lines = ["Workflow runs:"]
    for row in latest_rows[: max(1, limit)]:
        run_id = _workflow_run_id(row) or "(missing)"
        completed, total = _workflow_run_step_counts(row)
        status = str(row.get("status") or "unknown")
        workflow_ref = str(row.get("workflow_ref") or "-")
        updated_at = str(row.get("updated_at") or row.get("timestamp") or "")
        detail = f"- {run_id} - {status} - {workflow_ref} - steps:{completed}/{total}"
        if updated_at:
            detail += f" - updated:{updated_at}"
        reason = _workflow_run_stop_reason(row)
        if reason:
            detail += f" - stop:{reason}"
        lines.append(detail)
    if len(latest_rows) > limit:
        lines.append(f"... {len(latest_rows) - limit} older run(s) hidden")
    lines.append("Use /workflow show <run_id> for details.")
    return "\n".join(lines)


def format_workflow_run_detail(run_id: str, rows: list[dict[str, Any]]) -> str:
    target = str(run_id or "").strip()
    if not target:
        return "Workflow run not found: (missing)"
    history = [row for row in rows if _workflow_run_id(row) == target]
    if not history:
        return f"Workflow run not found: {target}"
    row = history[-1]
    completed, total = _workflow_run_step_counts(row)
    execution = row.get("execution") if isinstance(row.get("execution"), dict) else {}
    approval = row.get("approval") if isinstance(row.get("approval"), dict) else {}
    lines = [
        f"Workflow run: {target}",
        f"status: {row.get('status') or 'unknown'}",
        f"workflow: {row.get('workflow_ref') or '-'}",
        f"history_rows: {len(history)}",
        f"timestamp: {row.get('timestamp') or ''}",
        f"updated_at: {row.get('updated_at') or ''}",
        f"completed_at: {row.get('completed_at') or ''}",
        f"steps: {completed}/{total} completed",
        "execution:",
        f"- mode: {execution.get('mode') or ''}",
        f"- steps_executed: {execution.get('steps_executed', 0)}",
        f"- subagents_dispatched: {execution.get('subagents_dispatched', 0)}",
        f"- approvals_created: {execution.get('approvals_created', 0)}",
        f"- tools_called: {execution.get('tools_called', 0)}",
        f"- artifacts_written: {execution.get('artifacts_written', 0)}",
        f"- task_ledger_rows_written: {execution.get('task_ledger_rows_written', 0)}",
        f"- progress_ledger_rows_written: {execution.get('progress_ledger_rows_written', 0)}",
        "approval:",
        f"- status: {approval.get('approval_status') or ''}",
        f"- approval_id: {approval.get('approval_id') or ''}",
    ]
    approval_required_for = approval.get("approval_required_for")
    if isinstance(approval_required_for, list):
        lines.append("- required_for: " + (", ".join(str(item) for item in approval_required_for) or "[]"))
    else:
        lines.append(f"- required_for: {approval_required_for or '[]'}")
    reason = _workflow_run_stop_reason(row)
    if reason:
        lines.append(f"stop_reason: {reason}")
    lines.append("steps:")
    steps = row.get("steps") if isinstance(row.get("steps"), list) else []
    if not steps:
        lines.append("- (none)")
    else:
        for step in steps:
            if not isinstance(step, dict):
                continue
            pieces = [
                f"- {step.get('order') or '?'}:{step.get('step_id') or '(missing)'}",
                f"type={step.get('type') or ''}",
                f"status={step.get('status') or 'unknown'}",
            ]
            if step.get("agent"):
                pieces.append(f"agent={step.get('agent')}")
            if step.get("task_id"):
                pieces.append(f"task_id={step.get('task_id')}")
            if step.get("task_status"):
                pieces.append(f"task_status={step.get('task_status')}")
            if step.get("agent_id"):
                pieces.append(f"agent_id={step.get('agent_id')}")
            if step.get("approval_id"):
                pieces.append(f"approval_id={step.get('approval_id')}")
            if step.get("error"):
                pieces.append(f"error={step.get('error')}")
            lines.append(" | ".join(pieces))
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
