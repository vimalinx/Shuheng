"""Tests for curses-free rendering helper transforms."""
from __future__ import annotations

from ga_tui import app as app_module
from ga_tui import rendering
from ga_tui.ui_types import RenderLine


def test_running_indicator_frames_wrap_by_modulo() -> None:
    assert rendering.running_indicator(0) == "[=     ] running..."
    assert rendering.running_indicator(1) == "[==    ] running..."
    assert rendering.running_indicator(len(rendering.RUN_FRAMES)) == "[=     ] running..."
    assert rendering.running_indicator(-1) == "[     =] running..."


def test_running_indicator_cell_width_matches_widest_frame() -> None:
    assert rendering.running_indicator_cell_width() == max(
        rendering.cell_width(rendering.running_indicator(frame))
        for frame in range(len(rendering.RUN_FRAMES))
    )


def test_render_running_indicator_line_passthrough_for_regular_lines() -> None:
    line = RenderLine("unchanged", kind="", prefix_cells=4)

    assert rendering.render_running_indicator_line(line, 3) == "unchanged"


def test_render_running_indicator_line_uses_prefix_cells() -> None:
    line = RenderLine("cached text is ignored", kind="running_indicator", prefix_cells=3)

    assert rendering.render_running_indicator_line(line, 0) == "   [=     ] running..."


def test_app_rendering_wrappers_match_module() -> None:
    assert app_module.RUN_FRAMES is rendering.RUN_FRAMES
    assert app_module.running_indicator is rendering.running_indicator
    assert app_module.running_indicator_cell_width is rendering.running_indicator_cell_width
    assert app_module.render_running_indicator_line is rendering.render_running_indicator_line
