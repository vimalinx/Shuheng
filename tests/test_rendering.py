"""Tests for curses-free rendering helper transforms."""
from __future__ import annotations

from ga_tui import app as app_module
from ga_tui import rendering
from ga_tui.ui_types import Message, RenderLine


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


def test_char_index_for_cell_handles_ascii_wide_and_combining_text() -> None:
    assert rendering.char_index_for_cell("abc", -4) == 0
    assert rendering.char_index_for_cell("abc", 0) == 0
    assert rendering.char_index_for_cell("abc", 1) == 1
    assert rendering.char_index_for_cell("abc", 3) == 3
    assert rendering.char_index_for_cell("a中b", 2) == 1
    assert rendering.char_index_for_cell("a中b", 3) == 2
    assert rendering.char_index_for_cell("a\u0301b", 1) == 1
    assert rendering.char_index_for_cell("a\u0301b", 2) == 3


def test_ordered_selection_points_normalizes_missing_equal_and_reverse_ranges() -> None:
    assert rendering.ordered_selection_points(None, (0, 1)) is None
    assert rendering.ordered_selection_points((1, 2), None) is None
    assert rendering.ordered_selection_points((1, 2), (1, 2)) is None
    assert rendering.ordered_selection_points((3, 4), (1, 2)) == ((1, 2), (3, 4))
    assert rendering.ordered_selection_points((1, 5), (1, 2)) == ((1, 2), (1, 5))


def test_selection_span_for_line_points_handles_single_and_multiline_ranges() -> None:
    points = rendering.ordered_selection_points((1, 2), (3, 4))

    assert rendering.selection_span_for_line_points(points, 0, "zero") is None
    assert rendering.selection_span_for_line_points(points, 1, "abcdef") == (2, 6)
    assert rendering.selection_span_for_line_points(points, 2, "middle") == (0, 6)
    assert rendering.selection_span_for_line_points(points, 3, "abcdef") == (0, 4)
    assert rendering.selection_span_for_line_points(points, 4, "after") is None


def test_selection_span_for_line_points_clamps_columns_and_ignores_empty_ranges() -> None:
    assert rendering.selection_span_for_line_points(((1, -5), (1, 99)), 1, "abc") == (0, 3)
    assert rendering.selection_span_for_line_points(((1, -5), (1, 0)), 1, "abc") is None
    assert rendering.selection_span_for_line_points(((1, 6), (1, 99)), 1, "abc") is None
    assert rendering.selection_span_for_line_points(None, 1, "abc") is None


def test_scoped_subagent_meta_keys_filters_only_current_scope() -> None:
    expanded = {
        "unscoped",
        "scope-a:submeta:agent-1",
        "scope-a:submeta:agent-2",
        "scope-b:submeta:agent-3",
    }

    assert rendering.scoped_subagent_meta_keys("", expanded) == expanded
    assert rendering.scoped_subagent_meta_keys("scope-a", expanded) == {"agent-1", "agent-2"}
    assert rendering.scoped_subagent_meta_keys("missing", expanded) == set()


def test_message_render_cache_key_ignores_run_frame_and_sorts_expansions() -> None:
    msg = Message("assistant", "streaming body", done=False)

    key0 = rendering.message_render_cache_key(
        msg,
        2,
        80,
        True,
        True,
        0,
        "scope-a",
        {"g2", "g1"},
        {"t2", "t1"},
        {"meta-b", "meta-a"},
        "Worker",
    )
    key1 = rendering.message_render_cache_key(
        msg,
        2,
        80,
        True,
        True,
        99,
        "scope-a",
        {"g1", "g2"},
        {"t1", "t2"},
        {"meta-a", "meta-b"},
        "Worker",
    )
    changed_width = rendering.message_render_cache_key(
        msg,
        2,
        81,
        True,
        True,
        0,
        "scope-a",
        {"g1", "g2"},
        {"t1", "t2"},
        {"meta-a", "meta-b"},
        "Worker",
    )

    assert key1 == key0
    assert changed_width != key0
    assert ("g1", "g2") in key0
    assert ("t1", "t2") in key0
    assert ("meta-a", "meta-b") in key0


def test_app_selection_wrappers_delegate_to_rendering_helpers() -> None:
    state = app_module.State(agent=None)
    state.selection_start = (4, 5)
    state.selection_end = (2, 1)

    assert app_module.char_index_for_cell is rendering.char_index_for_cell
    assert app_module.ordered_selection_points(state) == rendering.ordered_selection_points((4, 5), (2, 1))
    assert app_module.selection_span_for_line(state, 2, "abcdef") == rendering.selection_span_for_line_points(
        rendering.ordered_selection_points((4, 5), (2, 1)),
        2,
        "abcdef",
    )


def test_app_rendering_wrappers_match_module() -> None:
    assert app_module.RUN_FRAMES is rendering.RUN_FRAMES
    assert app_module.char_index_for_cell is rendering.char_index_for_cell
    assert app_module.scoped_subagent_meta_keys is rendering.scoped_subagent_meta_keys
    assert app_module.message_render_cache_key is rendering.message_render_cache_key
    assert app_module.running_indicator is rendering.running_indicator
    assert app_module.running_indicator_cell_width is rendering.running_indicator_cell_width
    assert app_module.render_running_indicator_line is rendering.render_running_indicator_line
