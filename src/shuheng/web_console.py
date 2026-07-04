"""Pure Web Console helper contracts.

This module owns browser-facing schema constants, opaque UI refs, visible-text
sanitization, timestamp sorting, and small display records. Snapshot,
action, HTTP, and runtime-pump orchestration stays in the composition layer.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

try:
    from .governance import parse_iso_timestamp
    from .text_utils import clean_text, truncate_cells
except Exception:
    from governance import parse_iso_timestamp  # type: ignore
    from text_utils import clean_text, truncate_cells  # type: ignore


WEB_CONSOLE_ACTION_REQUEST_SCHEMA = "shuheng.web_console.action_request.v1"
WEB_CONSOLE_ACTION_RESPONSE_SCHEMA = "shuheng.web_console.action_response.v1"
WEB_CONSOLE_REF_KINDS = {"agent", "approval", "artifact", "model", "schedule", "session", "task"}


def web_console_ref(kind: str, raw_id: Any) -> str:
    kind = str(kind or "").strip().lower()
    raw = str(raw_id or "").strip()
    if kind not in WEB_CONSOLE_REF_KINDS or not raw:
        return ""
    digest = hashlib.sha256(f"shuheng.web_console.v1\0{kind}\0{raw}".encode("utf-8", errors="replace")).hexdigest()[:16]
    return f"{kind}:{digest}"


def web_console_timestamp(row: dict[str, Any]) -> float:
    for key in ("timestamp", "updated_at", "created_at", "finished_at"):
        parsed = parse_iso_timestamp(str(row.get(key) or ""))
        if parsed:
            return parsed
    try:
        return float(row.get("mtime") or 0.0)
    except Exception:
        return 0.0


def _strip_inline_markdown(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"[\1]", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<!_)_(?!_)(.*?)(?<!_)_(?!_)", r"\1", text)
    return text


def _mask_internal_refs(text: str) -> str:
    text = re.sub(r"artifact://\S+", "[artifact]", text)
    text = re.sub(r"\bappr[_0-9][A-Za-z0-9_:-]+\b", "[approval]", text)
    text = re.sub(r"\bapproval=[^\s,;，；]+", "approval=[hidden]", text)
    text = re.sub(r"\btask_[A-Za-z0-9_:-]+\b", "[task]", text)
    text = re.sub(r"\bschedrun_[A-Za-z0-9_:-]+\b", "[schedule-run]", text)
    text = re.sub(r"\bsched_[A-Za-z0-9_:-]+\b", "[schedule]", text)
    text = re.sub(r"\bagent-\d+\b", "子代理", text)
    text = re.sub(r"\btmp-agent-[A-Za-z0-9_.:-]+\b", "临时代理", text)
    return text


def web_console_clean_visible(value: Any, limit: int = 320) -> str:
    kept_lines: list[str] = []
    for raw_line in str(value or "").splitlines():
        if "APPROVAL_REQUIRED" in raw_line:
            continue
        kept_lines.append(raw_line)
    text = clean_text(_mask_internal_refs("\n".join(kept_lines))).strip()
    text = _mask_internal_refs(_strip_inline_markdown(text))
    return truncate_cells(text, limit).strip()


def web_console_status_label(status: Any) -> str:
    raw = str(status or "").strip()
    mapping = {
        "approval_required": "待审批",
        "completed": "完成",
        "working": "进行中",
        "running": "运行中",
        "created": "待开始",
        "pending": "待处理",
        "cancelled": "已取消",
        "canceled": "已取消",
        "failed": "失败",
        "rejected": "已拒绝",
        "enabled": "启用",
        "disabled": "停用",
    }
    return mapping.get(raw.lower(), web_console_clean_visible(raw or "-", 60) or "-")


def web_console_metric(label: str, value: Any, tone: str = "") -> dict[str, str]:
    return {"label": str(label), "value": str(value), "tone": str(tone)}


def web_console_resolve_ref(
    refs: dict[str, tuple[str, str]],
    ui_ref: Any,
    expected_kind: str,
) -> tuple[bool, str, str]:
    ref = str(ui_ref or "").strip()
    if not ref:
        return False, "", "缺少 ui_ref。"
    resolved = refs.get(ref)
    if resolved is None:
        return False, "", "找不到这个界面引用，请刷新后重试。"
    kind, raw = resolved
    if expected_kind and kind != expected_kind:
        return False, "", f"界面引用类型不匹配：需要 {expected_kind}。"
    return True, raw, ""


def web_console_action_payload(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("payload")
    return dict(value) if isinstance(value, dict) else {}


def web_console_action_message(text: Any) -> str:
    return web_console_clean_visible(text, 900) or "动作已执行。"


def web_console_model_name_from_payload(
    action_data: dict[str, Any],
    refs: dict[str, tuple[str, str]],
) -> tuple[bool, str, str]:
    model_name = str(action_data.get("model_name") or action_data.get("model") or "").strip()
    if model_name:
        return True, model_name, ""
    model_ref = str(action_data.get("model_ref") or action_data.get("model_ui_ref") or "").strip()
    if model_ref:
        return web_console_resolve_ref(refs, model_ref, "model")
    return True, "", ""


def web_console_schedule_control_from_payload(
    action_data: dict[str, Any],
    refs: dict[str, tuple[str, str]],
) -> tuple[bool, dict[str, Any], str]:
    control = dict(action_data)
    target_agent_ref = str(
        control.pop("target_agent_ref", "")
        or control.pop("agent_ref", "")
        or control.pop("agent_ui_ref", "")
        or ""
    ).strip()
    if not target_agent_ref:
        return True, control, ""
    ok_ref, agent_id, error = web_console_resolve_ref(refs, target_agent_ref, "agent")
    if not ok_ref:
        return False, {}, error
    execution = control.get("execution") if isinstance(control.get("execution"), dict) else {}
    execution = dict(execution)
    if str(execution.get("mode") or "").strip().lower().replace("-", "_") != "agent_task":
        execution["mode"] = "agent_task"
    routing = execution.get("routing") if isinstance(execution.get("routing"), dict) else {}
    routing = dict(routing)
    routing["selected_agent"] = agent_id
    selector = routing.get("target_selector") if isinstance(routing.get("target_selector"), dict) else {}
    selector = dict(selector)
    selector.setdefault("agent_id", agent_id)
    routing["target_selector"] = selector
    execution["routing"] = routing
    control["execution"] = execution
    return True, control, ""
