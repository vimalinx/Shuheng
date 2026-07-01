"""Pure terminal input cursor/display geometry helpers."""
from __future__ import annotations

try:
    from .text_utils import cell_width
except Exception:
    from text_utils import cell_width  # type: ignore


def raw_cursor_to_display(text: str, cursor: int) -> int:
    raw = text or ""
    return len(raw[:max(0, min(cursor, len(raw)))].replace("\n", "\\n"))


def display_cursor_to_raw(text: str, display_cursor: int) -> int:
    raw = text or ""
    display_cursor = max(0, display_cursor)
    display_pos = 0
    for idx, ch in enumerate(raw):
        width = 2 if ch == "\n" else 1
        if display_cursor <= display_pos:
            return idx
        display_pos += width
        if display_cursor <= display_pos:
            return idx + 1
    return len(raw)


def input_segments(text: str, width: int) -> tuple[str, list[tuple[str, int, int]]]:
    body_width = max(1, width - 2)
    display = (text or "").replace("\n", "\\n")
    segments: list[tuple[str, int, int]] = []
    current = ""
    current_w = 0
    start = 0
    for idx, ch in enumerate(display):
        w = cell_width(ch)
        if current and current_w + w > body_width:
            segments.append((current, start, idx))
            current = ch
            current_w = w
            start = idx
        else:
            current += ch
            current_w += w
    segments.append((current, start, len(display)))
    return display, segments


def display_index_for_cell(display: str, start: int, end: int, target_x: int) -> int:
    target_x = max(0, target_x)
    used = 0
    for idx in range(start, end):
        ch = display[idx]
        width = cell_width(ch)
        if used + width > target_x:
            return idx
        used += width
        if used >= target_x:
            return idx + 1
    return end


def input_cursor_info(text: str, width: int, cursor: int) -> tuple[str, list[tuple[str, int, int]], int, int, int]:
    raw = text or ""
    cursor = max(0, min(cursor, len(raw)))
    display, segments = input_segments(raw, width)
    display_cursor = raw_cursor_to_display(raw, cursor)

    cursor_line = len(segments) - 1
    for idx, (_segment, seg_start, seg_end) in enumerate(segments):
        if seg_start <= display_cursor < seg_end or (display_cursor == seg_end and idx == len(segments) - 1):
            cursor_line = idx
            break
    _segment, seg_start, _seg_end = segments[cursor_line]
    cursor_x = cell_width(display[seg_start:display_cursor])
    return display, segments, display_cursor, cursor_line, cursor_x
