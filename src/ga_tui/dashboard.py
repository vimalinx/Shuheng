"""Pure dashboard schema and normalization helpers."""
from __future__ import annotations

import json
from typing import Any

try:
    from .governance import now_iso
    from .text_utils import cell_width, clean_text, pad_cells, truncate_cells, wrap_cells
except Exception:
    from governance import now_iso  # type: ignore
    from text_utils import cell_width, clean_text, pad_cells, truncate_cells, wrap_cells  # type: ignore


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


def status_card_header_line(title: str, card_width: int) -> str:
    prefix = "╭─ "
    suffix = "╮"
    title_width = max(1, card_width - cell_width(prefix) - cell_width(suffix) - 1)
    label = truncate_cells(str(title or "").strip(), title_width)
    base = f"{prefix}{label} "
    return base + ("─" * max(0, card_width - cell_width(base) - cell_width(suffix))) + suffix


def status_card_divider_line(title: str, card_width: int) -> str:
    prefix = "├─ "
    suffix = "┤"
    title_width = max(1, card_width - cell_width(prefix) - cell_width(suffix) - 1)
    label = truncate_cells(str(title or "").strip(), title_width)
    base = f"{prefix}{label} "
    return base + ("─" * max(0, card_width - cell_width(base) - cell_width(suffix))) + suffix


def status_card_content_line(text: str, card_width: int) -> str:
    inner_width = max(1, card_width - 4)
    return f"│ {pad_cells(text, inner_width)} │"


def status_card_footer_line(card_width: int) -> str:
    return "╰" + ("─" * max(0, card_width - 2)) + "╯"


def status_card_metric_rows(items: list[tuple[str, str]], inner_width: int) -> list[str]:
    rows: list[str] = []
    cleaned = [
        (truncate_cells(str(label or "").strip(), 18), truncate_cells(str(value or "").strip(), 18))
        for label, value in items
        if str(label or "").strip() or str(value or "").strip()
    ]
    if not cleaned:
        return ["暂无指标"]
    max_cols = 4 if inner_width >= 86 else (3 if inner_width >= 66 else (2 if inner_width >= 42 else 1))
    layout_cols = max_cols
    while layout_cols > 1 and ((inner_width - (3 * (layout_cols - 1))) // layout_cols) < 12:
        layout_cols -= 1
    tile_width = max(8, (inner_width - (3 * (layout_cols - 1))) // layout_cols)
    index = 0
    while index < len(cleaned):
        cols = min(layout_cols, len(cleaned) - index)
        chunk = cleaned[index:index + cols]
        tiles = [
            pad_cells(f"{label} {value or '-'}", tile_width)
            for label, value in chunk
        ]
        rows.append(" │ ".join(tiles))
        index += cols
    return rows


def status_card_metric_header(metrics: list[tuple[str, str]]) -> str:
    count = sum(1 for label, value in metrics if str(label or "").strip() or str(value or "").strip())
    return f"核心指标（{count} 项）"


def status_card_detail_rows(items: list[tuple[str, str]], inner_width: int) -> list[str]:
    rows: list[str] = []
    cleaned = [
        (str(label or "").strip(), str(value or "").strip())
        for label, value in items
        if str(label or "").strip() or str(value or "").strip()
    ]
    if not cleaned:
        return ["暂无详情"]
    label_width = min(14, max(4, max((cell_width(label) for label, _value in cleaned), default=4)))
    for label, value in cleaned:
        value = value or "-"
        if not label or inner_width < label_width + 8:
            wrapped = wrap_cells((f"{label}: " if label else "") + value, inner_width)
            rows.extend(wrapped)
            continue
        value_width = max(8, inner_width - label_width - 3)
        label_text = pad_cells(label, label_width)
        wrapped = wrap_cells(value, value_width)
        for idx, part in enumerate(wrapped):
            if idx == 0:
                rows.append(f"{label_text}   {part}")
            else:
                rows.append((" " * (label_width + 3)) + part)
    return rows
