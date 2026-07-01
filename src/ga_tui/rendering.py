"""Curses-free rendering helper transforms for Shuheng."""
from __future__ import annotations

import re

try:
    from . import history_titles as history_title_policy
    from .text_utils import cell_width, compact_title
    from .ui_types import RenderLine
except Exception:
    import history_titles as history_title_policy  # type: ignore
    from text_utils import cell_width, compact_title  # type: ignore
    from ui_types import RenderLine  # type: ignore


SelectionPoint = tuple[int, int]
SelectionPoints = tuple[SelectionPoint, SelectionPoint]
RUN_FRAMES = ("[=     ]", "[==    ]", "[ ===  ]", "[  === ]", "[    ==]", "[     =]")
SUMMARY_RE = history_title_policy.SUMMARY_RE
META_BLOCK_RE = history_title_policy.META_BLOCK_RE
DETAIL_FENCE_RE = history_title_policy.DETAIL_FENCE_RE
THINKING_BLOCK_RE = re.compile(r"<(?:thinking|think)>\s*([\s\S]*?)\s*</(?:thinking|think)>", re.IGNORECASE)
TOOL_CALL_RE = re.compile(r"🛠️\s*Tool:\s*`([^`]+)`")
TOOL_USE_NAME_RE = re.compile(r"<tool_use>\s*\{[\s\S]*?\"name\"\s*:\s*\"([^\"]+)\"[\s\S]*?</tool_use>")


def strip_meta_blocks(text: str) -> str:
    return META_BLOCK_RE.sub("", text or "").strip()


def process_preview(text: str) -> str:
    summaries = SUMMARY_RE.findall(text or "")
    if summaries:
        title = compact_title(summaries[-1], 60)
        if title:
            return title
    preview = DETAIL_FENCE_RE.sub(" ", text or "")
    preview = META_BLOCK_RE.sub(" ", preview)
    preview = TOOL_CALL_RE.sub(" ", preview)
    preview = TOOL_USE_NAME_RE.sub(" ", preview)
    for line in preview.splitlines():
        line = line.strip()
        if not line or line.startswith(("```", "````", "args:", "📥")):
            continue
        title = compact_title(line, 60)
        if title:
            return title
    return "执行中"


def process_summary_text(text: str) -> str:
    summaries = SUMMARY_RE.findall(text or "")
    if not summaries:
        return ""
    summary = history_title_policy.compact_description(summaries[-1], 220)
    if history_title_policy.is_process_only_session_title(summary):
        thinking = THINKING_BLOCK_RE.findall(text or "")
        if thinking:
            return history_title_policy.compact_description(thinking[-1].strip(" \t\r\n\"'“”‘’"), 220)
    return summary


def scoped_subagent_meta_keys(process_scope: str, expanded_subagent_meta: set[str]) -> set[str]:
    scoped_subagent_meta = set(expanded_subagent_meta)
    if process_scope:
        prefix = f"{process_scope}:submeta:"
        scoped_subagent_meta = {key[len(prefix):] for key in expanded_subagent_meta if key.startswith(prefix)}
    return scoped_subagent_meta


def message_render_cache_key(
    msg: object,
    msg_index: int,
    width: int,
    fold_process: bool,
    markdown: bool,
    run_frame: int,
    process_scope: str,
    expanded_groups: set[str],
    expanded_turns: set[str],
    scoped_subagent_meta: set[str],
    assistant_label: str = "AI",
) -> tuple[object, ...]:
    return (
        id(msg),
        msg_index,
        str(getattr(msg, "role", "") or ""),
        len(getattr(msg, "content", "") or ""),
        hash(getattr(msg, "content", "") or ""),
        bool(getattr(msg, "done", False)),
        width,
        fold_process,
        markdown,
        process_scope,
        assistant_label,
        tuple(sorted(expanded_groups)),
        tuple(sorted(expanded_turns)),
        tuple(sorted(scoped_subagent_meta)),
    )


def char_index_for_cell(text: str, target_x: int) -> int:
    target_x = max(0, target_x)
    used = 0
    for idx, ch in enumerate(text):
        width = cell_width(ch)
        if target_x <= used:
            return idx
        if used + width > target_x:
            return idx
        used += width
        if used >= target_x:
            return idx + 1
    return len(text)


def ordered_selection_points(
    selection_start: SelectionPoint | None,
    selection_end: SelectionPoint | None,
) -> SelectionPoints | None:
    if selection_start is None or selection_end is None:
        return None
    start, end = sorted((selection_start, selection_end))
    if start == end:
        return None
    return start, end


def selection_span_for_line_points(
    points: SelectionPoints | None,
    line_idx: int,
    text: str,
) -> tuple[int, int] | None:
    if points is None:
        return None
    (start_line, start_col), (end_line, end_col) = points
    if line_idx < start_line or line_idx > end_line:
        return None
    if start_line == end_line:
        start, end = start_col, end_col
    elif line_idx == start_line:
        start, end = start_col, len(text)
    elif line_idx == end_line:
        start, end = 0, end_col
    else:
        start, end = 0, len(text)
    start = max(0, min(start, len(text)))
    end = max(0, min(end, len(text)))
    if start == end:
        return None
    return min(start, end), max(start, end)


def running_indicator(frame: int) -> str:
    return f"{RUN_FRAMES[frame % len(RUN_FRAMES)]} running..."


def running_indicator_cell_width() -> int:
    return max(cell_width(running_indicator(frame)) for frame in range(len(RUN_FRAMES)))


def render_running_indicator_line(line: RenderLine, frame: int) -> str:
    if line.kind != "running_indicator":
        return line.text
    prefix = " " * max(0, int(line.prefix_cells or 0))
    return prefix + running_indicator(frame)
