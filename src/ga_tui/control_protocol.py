"""Current GenericAgent-TUI control protocol parsing helpers."""
from __future__ import annotations

import json
import re
from typing import Any, Optional

try:
    from .compat_legacy import strip_retired_tui_markup
except Exception:
    from compat_legacy import strip_retired_tui_markup  # type: ignore


TUI_CONTROL_RE = re.compile(r"(?<!`)<ga[-_]control>\s*([\s\S]*?)\s*</ga[-_]control>", re.IGNORECASE)
TUI_CONTROL_FENCE_RE = re.compile(r"```ga[-_]control\s*([\s\S]*?)```", re.IGNORECASE)
TUI_CONTROL_JSON_FENCE_RE = re.compile(r"```(?:json|js|javascript|code)?[ \t]*\n([\s\S]*?)(?:^```|\Z)", re.IGNORECASE | re.MULTILINE)
TUI_GENERIC_CODE_FENCE_RE = re.compile(r"```[^\n`]*\n[\s\S]*?(?:^```[ \t]*(?:\n|\Z)|\Z)", re.MULTILINE)

GA_CONTROL_SCHEMA = "ga-control.v2"
AGENT_TASK_SCHEMA = "agenttask.v2"

CURRENT_TUI_CONTROL_ACTIONS = {
    "session.pin",
    "session.unpin",
    "session.category",
    "session.filter",
    "session.clear_filter",
    "session.collapse_category",
    "session.expand_category",
    "session.archive",
    "session.unarchive",
    "session.delete",
    "session.rename",
    "session.show_archived",
    "session.hide_archived",
    "task.plan.create",
    "task.update",
    "task.done",
    "task.start",
    "task.fail",
    "task.cancel",
    "schedule.create",
    "schedule.update",
    "schedule.enable",
    "schedule.disable",
    "schedule.delete",
    "dashboard.update",
    "agent.create",
    "agent.profile.update",
    "agent.role.update",
    "agent.model.update",
    "agent.skill.update",
    "agent.skills.update",
    "agent.stop",
    "agent.delete",
    "delegate.create",
    "memory.candidate",
}

SESSION_V2_TO_EXECUTION_ACTION = {
    "session_pin": "pin",
    "session_unpin": "unpin",
    "session_category": "category",
    "session_filter": "filter",
    "session_clear_filter": "clear_filter",
    "session_collapse_category": "collapse_category",
    "session_expand_category": "expand_category",
    "session_archive": "archive",
    "session_unarchive": "unarchive",
    "session_delete": "delete",
    "session_rename": "rename",
    "session_show_archived": "show_archived",
    "session_hide_archived": "hide_archived",
}


def control_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "持久", "长期"}


def control_falsey(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return not bool(value)
    return str(value or "").strip().lower() in {"0", "false", "no", "n", "off", "none", "null", "不要", "不"}


def normalized_control_action(control: dict[str, Any]) -> str:
    return str(control.get("action") or control.get("op") or "").strip().lower().replace("-", "_").replace(".", "_")


def known_tui_control(control: dict[str, Any]) -> bool:
    action = str(control.get("action") or "").strip().lower()
    return action in CURRENT_TUI_CONTROL_ACTIONS


def action_schema_valid(control: dict[str, Any]) -> bool:
    schema = str(control.get("schema_version") or "").strip().lower()
    return schema in {"", AGENT_TASK_SCHEMA}


def coerce_ga_control_action(action: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not isinstance(action, dict):
        return None
    item = dict(action)
    if not item.get("schema_version"):
        item["schema_version"] = AGENT_TASK_SCHEMA
    if not action_schema_valid(item) or not known_tui_control(item):
        return None
    return item


def agenttask_work_order(control: dict[str, Any]) -> dict[str, Any]:
    value = control.get("work_order")
    if isinstance(value, dict):
        return value
    value = control.get("task")
    return value if isinstance(value, dict) else {}


def agenttask_routing(control: dict[str, Any]) -> dict[str, Any]:
    value = control.get("routing")
    return value if isinstance(value, dict) else {}


def agenttask_target_selector(control: dict[str, Any]) -> dict[str, Any]:
    routing = agenttask_routing(control)
    value = routing.get("target_selector")
    return value if isinstance(value, dict) else {}


def agenttask_contract(control: dict[str, Any], key: str) -> dict[str, Any]:
    value = control.get(key)
    return value if isinstance(value, dict) else {}


def lifecycle_is_persistent(control: dict[str, Any]) -> Optional[bool]:
    for key in ("persistent", "durable", "long_term"):
        if key in control:
            return control_truthy(control.get(key))
    lifecycle = str(control.get("lifecycle") or control.get("scope") or "").strip().lower()
    if lifecycle in {"persistent", "durable", "long_term", "long-term", "permanent", "正式", "持久", "长期", "永久"}:
        return True
    if lifecycle in {"ephemeral", "temporary", "temp", "session", "session_only", "临时", "暂时"}:
        return False
    return None


def force_new_from_v2(control: dict[str, Any]) -> bool:
    if control_truthy(control.get("force_new")) or control_truthy(control.get("create_new")):
        return True
    reuse_policy = str(control.get("reuse_policy") or "").strip().lower().replace("-", "_")
    selector = agenttask_target_selector(control)
    selector_policy = str(selector.get("reuse_policy") or "").strip().lower().replace("-", "_")
    return reuse_policy in {"force_new", "never", "none", "no_reuse"} or selector_policy in {"force_new", "never", "none", "no_reuse"}


def subagent_control_persistence_intent(
    control: dict[str, Any],
    target: str,
    value: str,
    name: str,
    profile: str,
) -> tuple[bool, bool]:
    del target, value, name, profile
    persistent = lifecycle_is_persistent(control)
    if persistent is not None:
        return bool(persistent), not bool(persistent)
    for key in ("temporary", "temp", "ephemeral", "session_only", "session_scoped"):
        if key in control and control_truthy(control.get(key)):
            return False, True
    return False, True


def subagent_control_force_new_intent(
    control: dict[str, Any],
    target: str,
    value: str,
    name: str,
    profile: str,
    context_text: str = "",
) -> bool:
    del target, value, name, profile, context_text
    for key in ("force_new", "create_new", "fresh", "separate"):
        if key in control and control_truthy(control.get(key)):
            return True
    for key in ("reuse", "reuse_existing", "allow_reuse", "dedupe"):
        if key in control and control_falsey(control.get(key)):
            return True
    if "new" in control and isinstance(control.get("new"), (bool, int, float, str)) and control_truthy(control.get("new")):
        return True
    reuse_policy = str(control.get("reuse_policy") or "").strip().lower().replace("-", "_")
    return reuse_policy in {"force_new", "never", "none", "no_reuse"}


def agenttask_objective(control: dict[str, Any]) -> str:
    work_order = agenttask_work_order(control)
    return str(
        work_order.get("objective")
        or control.get("objective")
        or control.get("prompt")
        or control.get("message")
        or ""
    ).strip()


def format_agenttask_worker_prompt(control: dict[str, Any]) -> str:
    objective = agenttask_objective(control)
    work_order = agenttask_work_order(control)
    output_contract = agenttask_contract(control, "output_contract")
    payload = json.dumps(control, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    sections = [
        "[GA TUI AgentTask Envelope v2]",
        payload,
        "[/GA TUI AgentTask Envelope v2]",
        "",
        "[Work Order]",
        f"objective: {objective}",
    ]
    background = str(work_order.get("background") or "").strip()
    if background:
        sections.append(f"background: {background}")
    non_goals = work_order.get("non_goals")
    if isinstance(non_goals, list) and non_goals:
        sections.append("non_goals:")
        sections.extend(f"- {item}" for item in non_goals)
    success = work_order.get("success_criteria")
    if isinstance(success, list) and success:
        sections.append("success_criteria:")
        sections.extend(f"- {item}" for item in success)
    stop_condition = str(work_order.get("stop_condition") or "").strip()
    if stop_condition:
        sections.append(f"stop_condition: {stop_condition}")
    required = output_contract.get("required_sections")
    if isinstance(required, list) and required:
        sections.append("required_output_sections:")
        sections.extend(f"- {item}" for item in required)
    sections.append("[/Work Order]")
    return "\n".join(str(item) for item in sections).strip()


def execution_control_from_v2(control: dict[str, Any]) -> Optional[dict[str, Any]]:
    action = normalized_control_action(control)
    common = {
        "_ga_control_schema_version": str(control.get("schema_version") or AGENT_TASK_SCHEMA),
        "_ga_control_external_action": str(control.get("action") or ""),
        "_ga_control_envelope": dict(control),
    }
    if action in SESSION_V2_TO_EXECUTION_ACTION:
        mapped = dict(control)
        mapped.update(common)
        mapped["action"] = SESSION_V2_TO_EXECUTION_ACTION[action]
        return mapped
    if action == "task_plan_create":
        mapped = dict(common)
        work_order = agenttask_work_order(control)
        mapped.update({
            "action": "task_plan",
            "title": control.get("title") or work_order.get("title") or control.get("name") or "任务计划",
            "steps": control.get("steps") or work_order.get("steps") or control.get("tasks") or control.get("items") or [],
        })
        return mapped
    if action in {"task_update", "task_done", "task_start", "task_fail", "task_cancel"}:
        mapped = dict(control)
        mapped.update(common)
        mapped["action"] = action
        mapped["target"] = control.get("target") or control.get("task_id") or control.get("parent_task_id") or ""
        return mapped
    if action in {"schedule_create", "schedule_update", "schedule_enable", "schedule_disable", "schedule_delete"}:
        mapped = dict(control)
        mapped.update(common)
        mapped["action"] = action
        mapped["target"] = control.get("target") or control.get("schedule_id") or control.get("id") or ""
        return mapped
    if action == "dashboard_update":
        mapped = dict(control)
        mapped.update(common)
        mapped["action"] = "dashboard_update"
        mapped["target"] = control.get("target") or control.get("agent_id") or control.get("agent") or ""
        return mapped
    if action in {"agent_skill_update", "agent_skills_update"}:
        mapped = dict(control)
        mapped.update(common)
        mapped["action"] = "agent_skill"
        mapped["target"] = control.get("target") or control.get("agent_id") or control.get("agent") or ""
        mapped["skill_refs"] = control.get("skill_refs") or control.get("skills") or control.get("skill") or []
        return mapped
    if action == "agent_create":
        selector = agenttask_target_selector(control)
        persistent = lifecycle_is_persistent(control)
        if persistent is None:
            persistent = lifecycle_is_persistent(selector)
        mapped = dict(common)
        mapped.update({
            "action": "subagent_create",
            "name": control.get("name") or selector.get("name") or control.get("title") or selector.get("role") or "subagent",
            "profile": control.get("profile") or control.get("description") or selector.get("profile") or selector.get("description") or "",
            "role": control.get("role") or selector.get("role") or "specialist",
            "model": control.get("model") or control.get("default_model") or control.get("model_name") or selector.get("model") or selector.get("default_model") or "",
            "skill_refs": control.get("skill_refs") or control.get("skills") or control.get("skill") or selector.get("skill_refs") or selector.get("skills") or selector.get("skill") or [],
            "plan_step_id": control.get("plan_step_id") or control.get("parent_task_id") or control.get("step") or "",
            "force_new": force_new_from_v2(control),
        })
        if persistent is not None:
            mapped["persistent"] = bool(persistent)
            mapped["temporary"] = not bool(persistent)
        return mapped
    if action == "delegate_create":
        routing = agenttask_routing(control)
        selector = agenttask_target_selector(control)
        selected = (
            routing.get("selected_agent")
            or selector.get("agent_id")
            or selector.get("target")
            or selector.get("name")
            or control.get("target")
            or control.get("agent")
            or ""
        )
        mapped = dict(common)
        mapped.update({
            "action": "subagent_ask",
            "target": selected,
            "prompt": format_agenttask_worker_prompt(control),
            "parent_task_id": control.get("parent_task_id") or control.get("plan_step_id") or control.get("step") or "",
            "task_title": control.get("task_title") or control.get("title") or agenttask_objective(control),
        })
        return mapped
    if action == "memory_candidate":
        mapped = dict(common)
        mapped.update({
            "action": "subagent_remember",
            "target": control.get("target") or control.get("agent_id") or control.get("agent") or "",
            "memory": control.get("memory") or control.get("statement") or control.get("note") or "",
        })
        return mapped
    if action in {"agent_profile_update", "agent_role_update", "agent_model_update", "agent_stop", "agent_delete", "agent_remove"}:
        mapped = dict(control)
        mapped.update(common)
        mapped["target"] = control.get("target") or control.get("agent_id") or control.get("agent") or ""
        mapped["action"] = {
            "agent_profile_update": "subagent_profile",
            "agent_role_update": "subagent_role",
            "agent_model_update": "subagent_model",
            "agent_stop": "subagent_stop",
            "agent_delete": "subagent_delete",
            "agent_remove": "subagent_delete",
        }[action]
        return mapped
    return None


def controls_from_json_payload(payload: Any, *, require_known: bool = False) -> list[dict[str, Any]]:
    raw_items: list[Any] = []
    if isinstance(payload, dict) and str(payload.get("schema_version") or "").strip().lower() == GA_CONTROL_SCHEMA:
        batch_metadata = {
            key: payload[key]
            for key in (
                "continue_after",
                "next_action_required",
                "requires_continuation",
                "workflow_state",
                "orchestrator_state",
                "workflow_id",
                "phase_id",
                "next_action",
            )
            if key in payload
        }
        actions = payload.get("actions")
        if isinstance(actions, list):
            raw_items = [
                {**batch_metadata, **item} if isinstance(item, dict) else item
                for item in actions
            ]
        elif payload.get("action"):
            item = dict(payload)
            item["schema_version"] = AGENT_TASK_SCHEMA
            raw_items = [item]
    elif isinstance(payload, dict) and str(payload.get("schema_version") or "").strip().lower() == AGENT_TASK_SCHEMA:
        raw_items = [payload]
    elif isinstance(payload, list):
        raw_items = [item for item in payload if isinstance(item, dict) and str(item.get("schema_version") or "").strip().lower() == AGENT_TASK_SCHEMA]
    controls = [coerced for item in raw_items if isinstance(item, dict) for coerced in [coerce_ga_control_action(item)] if coerced is not None]
    if require_known:
        controls = [item for item in controls if known_tui_control(item)]
    execution_controls = []
    for control in controls:
        mapped = execution_control_from_v2(control)
        if mapped is not None:
            execution_controls.append(mapped)
    return execution_controls


def repair_json_missing_tail(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    stack: list[str] = []
    in_string = False
    escape = False
    for ch in text:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in {"}", "]"}:
            if not stack or stack[-1] != ch:
                return ""
            stack.pop()
    if in_string or escape or not stack:
        return ""
    return text.rstrip() + "".join(reversed(stack))


def load_ga_control_json_text(raw: str) -> tuple[Any, bool, str]:
    text = (raw or "").strip()
    if not text:
        return None, False, "empty control block"
    try:
        return json.loads(text), False, ""
    except json.JSONDecodeError as exc:
        repaired = repair_json_missing_tail(text)
        if repaired:
            try:
                return json.loads(repaired), True, ""
            except json.JSONDecodeError:
                pass
        return None, False, f"JSON parse error at line {exc.lineno} column {exc.colno}: {exc.msg}"
    except Exception as exc:
        return None, False, f"JSON parse error: {type(exc).__name__}: {exc}"


def controls_from_json_text(raw: str, *, require_known: bool = False) -> list[dict[str, Any]]:
    payload, _repaired, _error = load_ga_control_json_text(raw)
    if payload is None:
        return []
    return controls_from_json_payload(payload, require_known=require_known)


def _code_fence_spans(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in TUI_GENERIC_CODE_FENCE_RE.finditer(text or "")]


def _outside_code_fence_regions(text: str) -> list[tuple[int, int]]:
    regions: list[tuple[int, int]] = []
    cursor = 0
    for start, end in _code_fence_spans(text):
        if cursor < start:
            regions.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < len(text):
        regions.append((cursor, len(text)))
    return regions


def _tag_control_blocks_outside_code_fences(text: str) -> list[str]:
    blocks: list[str] = []
    for start, end in _outside_code_fence_regions(text or ""):
        blocks.extend(TUI_CONTROL_RE.findall((text or "")[start:end]))
    return blocks


def _executable_control_blocks(text: str) -> list[str]:
    text = text or ""
    return _tag_control_blocks_outside_code_fences(text) + TUI_CONTROL_FENCE_RE.findall(text)


def _sub_outside_code_fences(pattern: re.Pattern[str], repl: str, text: str) -> str:
    text = text or ""
    if not text:
        return ""
    spans = _code_fence_spans(text)
    if not spans:
        return pattern.sub(repl, text)
    pieces: list[str] = []
    cursor = 0
    for start, end in spans:
        if cursor < start:
            pieces.append(pattern.sub(repl, text[cursor:start]))
        pieces.append(text[start:end])
        cursor = end
    if cursor < len(text):
        pieces.append(pattern.sub(repl, text[cursor:]))
    return "".join(pieces)


def tui_control_parse_errors(text: str, *, allow_json_fences: bool = False) -> list[str]:
    errors: list[str] = []
    blocks = _executable_control_blocks(text or "")
    if allow_json_fences:
        blocks.extend(TUI_CONTROL_JSON_FENCE_RE.findall(text or ""))
    for raw in blocks:
        payload, _repaired, error = load_ga_control_json_text(raw)
        if error:
            errors.append(error)
            continue
        if payload is not None and not controls_from_json_payload(payload, require_known=allow_json_fences):
            errors.append("control JSON parsed but no known ga-control.v2 or agenttask.v2 action was found")
    return errors


def extract_tui_controls(text: str, *, allow_json_fences: bool = False) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(raw: str, *, require_known: bool = False) -> None:
        for control in controls_from_json_text(raw, require_known=require_known):
            signature = json.dumps(control, ensure_ascii=False, sort_keys=True, default=str)
            if signature in seen:
                continue
            seen.add(signature)
            controls.append(control)

    for raw in _executable_control_blocks(text or ""):
        add(raw)
    if allow_json_fences:
        for raw in TUI_CONTROL_JSON_FENCE_RE.findall(text or ""):
            add(raw, require_known=True)
    return controls


def strip_tui_controls(text: str, *, allow_json_fences: bool = False) -> str:
    text = text or ""
    if allow_json_fences:
        def strip_json_control_fence(match: re.Match[str]) -> str:
            block = match.group(1) or ""
            if controls_from_json_text(block, require_known=True) or extract_tui_controls(match.group(0)):
                return ""
            return match.group(0)
        text = TUI_CONTROL_JSON_FENCE_RE.sub(strip_json_control_fence, text)
    text = _sub_outside_code_fences(TUI_CONTROL_RE, "", text)
    text = TUI_CONTROL_FENCE_RE.sub("", text)
    text = strip_retired_tui_markup(text)
    text = _sub_outside_code_fences(re.compile(r"(?<!`)<ga[-_]control>[\s\S]*$", re.IGNORECASE), "", text)
    text = re.sub(r"```ga[-_]control[\s\S]*$", "", text, flags=re.IGNORECASE)
    return text.strip()
