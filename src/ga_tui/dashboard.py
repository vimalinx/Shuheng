"""Pure dashboard schema and normalization helpers."""
from __future__ import annotations

import json
from typing import Any

try:
    from .governance import now_iso
    from .text_utils import clean_text
except Exception:
    from governance import now_iso  # type: ignore
    from text_utils import clean_text  # type: ignore


SUPPORTED_DASHBOARD_SECTIONS = {
    "function",
    "status_narrative",
    "todos",
    "sessions",
    "schedules",
    "scheduled_reports",
    "tasks",
    "artifacts",
    "approvals",
    "memory",
    "markdown",
}


DEFAULT_DASHBOARD_SECTIONS: list[dict[str, str]] = [
    {"type": "function", "title": "功能描述"},
    {"type": "status_narrative", "title": "当前状态"},
    {"type": "todos", "title": "待办事项"},
    {"type": "schedules", "title": "最近定时任务"},
    {"type": "tasks", "title": "最近任务"},
]


DEFAULT_SUBAGENT_DASHBOARD_SECTIONS: list[dict[str, str]] = [
    {"type": "function", "title": "功能描述"},
    {"type": "status_narrative", "title": "当前状态"},
    {"type": "todos", "title": "待办事项"},
    {"type": "schedules", "title": "最近定时任务"},
    {"type": "scheduled_reports", "title": "定时汇报"},
    {"type": "tasks", "title": "最近任务"},
]


def bounded_dashboard_text(value: Any, limit: int = 2000) -> str:
    return clean_text(str(value or "")).strip()[:limit]


def normalize_dashboard_sections(raw_sections: Any) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    source = raw_sections if isinstance(raw_sections, list) else []
    for item in source[:12]:
        if isinstance(item, str):
            item = {"type": item}
        if not isinstance(item, dict):
            continue
        section_type = str(item.get("type") or item.get("section") or "").strip().lower()
        if section_type not in SUPPORTED_DASHBOARD_SECTIONS:
            continue
        section = {
            "type": section_type,
            "title": bounded_dashboard_text(item.get("title") or item.get("label") or section_type, 80),
        }
        markdown = bounded_dashboard_text(item.get("markdown") or item.get("body") or "", 3000)
        if markdown:
            section["markdown"] = markdown
        sections.append(section)
    return sections


def normalize_dashboard_spec_payload(control: dict[str, Any], *, source: str, target: str) -> dict[str, Any]:
    raw = control.get("dashboard") if isinstance(control.get("dashboard"), dict) else control
    sections = normalize_dashboard_sections(raw.get("sections") if isinstance(raw, dict) else [])
    markdown = bounded_dashboard_text(raw.get("markdown") if isinstance(raw, dict) else control.get("markdown"), 5000)
    status = bounded_dashboard_text(
        (raw.get("status_narrative") or raw.get("status")) if isinstance(raw, dict) else control.get("status_narrative"),
        1000,
    )
    todos_raw = raw.get("todos") if isinstance(raw, dict) else control.get("todos")
    todos: list[str] = []
    if isinstance(todos_raw, list):
        for item in todos_raw[:20]:
            if isinstance(item, dict):
                text = bounded_dashboard_text(item.get("text") or item.get("title") or item.get("task"), 180)
            else:
                text = bounded_dashboard_text(item, 180)
            if text:
                todos.append(text)
    payload = {
        "schema_version": "dashboard.v1",
        "updated_at": now_iso(),
        "source": source,
        "target": target,
        "provenance": {
            "task_id": str(control.get("task_id") or control.get("parent_task_id") or ""),
            "artifact_refs": [str(ref) for ref in (control.get("artifact_refs") or []) if str(ref).strip()][:12],
        },
        "sections": sections,
    }
    if status:
        payload["status_narrative"] = status
    if todos:
        payload["todos"] = todos
    if markdown:
        payload["markdown"] = markdown
    return payload


def dashboard_cache_signature(raw: Any) -> str:
    if not raw:
        return ""
    try:
        return json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        return str(raw)
