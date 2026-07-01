"""Curses-free rendering helper transforms for Shuheng."""
from __future__ import annotations

try:
    from .text_utils import cell_width
    from .ui_types import RenderLine
except Exception:
    from text_utils import cell_width  # type: ignore
    from ui_types import RenderLine  # type: ignore


RUN_FRAMES = ("[=     ]", "[==    ]", "[ ===  ]", "[  === ]", "[    ==]", "[     =]")


def running_indicator(frame: int) -> str:
    return f"{RUN_FRAMES[frame % len(RUN_FRAMES)]} running..."


def running_indicator_cell_width() -> int:
    return max(cell_width(running_indicator(frame)) for frame in range(len(RUN_FRAMES)))


def render_running_indicator_line(line: RenderLine, frame: int) -> str:
    if line.kind != "running_indicator":
        return line.text
    prefix = " " * max(0, int(line.prefix_cells or 0))
    return prefix + running_indicator(frame)
