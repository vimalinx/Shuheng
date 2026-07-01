"""Pure terminal input cursor/display geometry helpers."""
from __future__ import annotations

from collections.abc import Mapping

try:
    from .text_utils import cell_width
except Exception:
    from text_utils import cell_width  # type: ignore

MOUSE_BUTTON_STATES = ("PRESSED", "RELEASED", "CLICKED", "DOUBLE_CLICKED", "TRIPLE_CLICKED")


def _mouse_constant(constants: Mapping[str, object], name: str) -> int:
    try:
        return int(constants.get(name, 0) or 0)
    except (TypeError, ValueError):
        return 0


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


def input_layout(text: str, width: int, max_lines: int, cursor: int, prompt: str = "> ") -> tuple[list[str], int, int]:
    max_lines = max(1, max_lines)
    display, segments, display_cursor, cursor_line, _cursor_x = input_cursor_info(text, width, cursor)
    first = 0
    if len(segments) > max_lines:
        first = max(0, min(cursor_line, len(segments) - max_lines))
    visible = segments[first:first + max_lines]
    lines: list[str] = []
    cursor_y = max(0, cursor_line - first)
    cursor_x = cell_width(prompt)
    for idx, (segment, seg_start, _seg_end) in enumerate(visible):
        actual_idx = first + idx
        prefix = prompt if actual_idx == 0 else " " * cell_width(prompt)
        if first > 0 and idx == 0:
            prefix = "… "
        lines.append(prefix + segment)
        if actual_idx == cursor_line:
            before = display[seg_start:display_cursor]
            cursor_x = cell_width(prefix) + cell_width(before)
    return lines or [prompt], cursor_y, cursor_x


def mouse_button_mask_from_constants(button_no: int, constants: Mapping[str, object]) -> int:
    total = 0
    for state in MOUSE_BUTTON_STATES:
        total |= _mouse_constant(constants, f"BUTTON{int(button_no or 0)}_{state}")
    return total


def mouse_modifier_mask_from_constants(constants: Mapping[str, object]) -> int:
    return (
        _mouse_constant(constants, "BUTTON_SHIFT")
        | _mouse_constant(constants, "BUTTON_CTRL")
        | _mouse_constant(constants, "BUTTON_ALT")
    )


def mouse_known_bstate_mask_from_constants(constants: Mapping[str, object], button_count: int = 5) -> int:
    known = _mouse_constant(constants, "REPORT_MOUSE_POSITION") | mouse_modifier_mask_from_constants(constants)
    for button_no in range(1, max(0, int(button_count or 0)) + 1):
        known |= mouse_button_mask_from_constants(button_no, constants)
    return known


def mouse_auxiliary_or_unknown_event_from_constants(
    bstate: int,
    constants: Mapping[str, object],
    button_count: int = 5,
) -> bool:
    bstate = int(bstate or 0)
    auxiliary = 0
    for button_no in range(2, max(1, int(button_count or 0)) + 1):
        auxiliary |= mouse_button_mask_from_constants(button_no, constants)
    known = mouse_known_bstate_mask_from_constants(constants, button_count=button_count)
    return bool((bstate & auxiliary) or (bstate & ~known))


def clean_button1_action_from_constants(
    bstate: int,
    allowed_button1_mask: int,
    constants: Mapping[str, object],
    button_count: int = 5,
) -> bool:
    bstate = int(bstate or 0)
    allowed_button1_mask = int(allowed_button1_mask or 0)
    if not allowed_button1_mask or not (bstate & allowed_button1_mask):
        return False
    if mouse_auxiliary_or_unknown_event_from_constants(bstate, constants, button_count=button_count):
        return False
    disallowed_button1 = mouse_button_mask_from_constants(1, constants) & ~allowed_button1_mask
    allowed = allowed_button1_mask | mouse_modifier_mask_from_constants(constants)
    return not (bstate & disallowed_button1) and not (bstate & ~allowed)
