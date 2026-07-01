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


def test_process_preview_prefers_summary_then_clean_visible_line() -> None:
    assert rendering.process_preview("<summary>真实进展</summary>\n<chunk>ignored</chunk>") == "真实进展"
    assert rendering.process_preview(
        "````text\nhidden block\n````\n"
        "🛠️ Tool: `web.search`\n"
        "📥 args: {}\n"
        "args: skipped\n"
        "  可以展示的过程标题  "
    ) == "可以展示的过程标题"
    assert rendering.process_preview("<thinking>   </thinking>") == "执行中"


def test_process_summary_text_uses_thinking_for_legacy_process_only_summary() -> None:
    assert rendering.process_summary_text("<summary>完成整理</summary>") == "完成整理"
    assert rendering.process_summary_text("<summary>OMP 思考</summary><thinking>分析下一步边界</thinking>") == "分析下一步边界"
    assert rendering.process_summary_text("no summary here") == ""


def test_strip_meta_blocks_removes_process_metadata() -> None:
    assert rendering.strip_meta_blocks("before <summary>hidden</summary> after") == "before  after"
    assert rendering.strip_meta_blocks("<thinking>hidden</thinking>\nvisible") == "visible"


def test_split_top_level_turn_markers_handles_empty_and_top_level_turns() -> None:
    assert rendering.split_top_level_turn_markers("") == [""]

    text = (
        "preamble\n"
        "LLM Running (Turn 1) ...\n"
        "first body\n"
        "LLM Running (Turn 2) ...\n"
        "second body\n"
    )

    assert rendering.split_top_level_turn_markers(text) == [
        "preamble\n",
        "LLM Running (Turn 1) ...",
        "\nfirst body\n",
        "LLM Running (Turn 2) ...",
        "\nsecond body\n",
    ]


def test_split_top_level_turn_markers_treats_fenced_markers_as_content() -> None:
    text = (
        "before\n"
        "```text\n"
        "LLM Running (Turn 99) ...\n"
        "```\n"
        "LLM Running (Turn 1) ...\n"
        "real body\n"
    )

    assert rendering.split_top_level_turn_markers(text) == [
        "before\n```text\nLLM Running (Turn 99) ...\n```\n",
        "LLM Running (Turn 1) ...",
        "\nreal body\n",
    ]


def test_stray_line_numbered_fence_close_does_not_swallow_next_turn_marker() -> None:
    marker = "LLM Running (Turn 1) ...\n"

    assert rendering.line_numbered_file_line("  42| print('x')\n")
    assert rendering.next_nonblank_line(["\n", "  \n", marker], 0) == marker
    assert rendering.stray_line_numbered_fence_close("```\n", "42| print('x')\n", marker)

    text = "1| file output\n```\nLLM Running (Turn 1) ...\nbody\n"
    assert rendering.split_top_level_turn_markers(text) == [
        "1| file output\n```\n",
        "LLM Running (Turn 1) ...",
        "\nbody\n",
    ]


def test_close_unbalanced_markdown_fence_preserves_balanced_and_empty_text() -> None:
    balanced = "intro\n```python\nprint('x')\n```\nfinal"

    assert rendering.close_unbalanced_markdown_fence("") == ""
    assert rendering.close_unbalanced_markdown_fence(balanced) == balanced


def test_close_unbalanced_markdown_fence_appends_opening_tick_sequence() -> None:
    assert rendering.close_unbalanced_markdown_fence("intro\n```python\nprint('x')") == (
        "intro\n```python\nprint('x')\n```"
    )
    assert rendering.close_unbalanced_markdown_fence("intro\n````text\nbody") == "intro\n````text\nbody\n````"


def test_close_unbalanced_markdown_fence_requires_suffixless_sufficient_close() -> None:
    suffix_close = "intro\n```python\nbody\n```python"
    short_close = "intro\n````python\nbody\n```"

    assert rendering.close_unbalanced_markdown_fence(suffix_close) == suffix_close + "\n```"
    assert rendering.close_unbalanced_markdown_fence(short_close) == short_close + "\n````"


def test_visible_reply_text_default_keeps_result_fences_but_hides_meta_and_headers() -> None:
    body = (
        "<summary>hidden process</summary>\n"
        "Visible answer\n"
        "<tool_use>{\"name\":\"web.search\"}</tool_use>\n"
        "🛠️ Tool: `web.search` 📥 args:\n"
        "[Info] Final response to user.\n"
        "`````\n"
        "raw result stays by default\n"
        "`````\n"
        ".\n"
        "\n\n"
        "Next line"
    )

    visible = rendering.visible_reply_text(body)

    assert "hidden process" not in visible
    assert "<tool_use>" not in visible
    assert "Tool:" not in visible
    assert "[Info]" not in visible
    assert "." not in visible.splitlines()
    assert visible == "Visible answer\n\n`````\nraw result stays by default\n`````\n\nNext line"


def test_visible_reply_text_hide_detail_fences_removes_tool_blocks_and_result_fences() -> None:
    body = (
        "Visible answer\n"
        "🛠️ Tool: `web.search` 📥 args:\n"
        "````text\n"
        "{\"q\":\"needle\"}\n"
        "````\n"
        "<tool_use>{\"name\":\"web.search\"}</tool_use>\n"
        "`````\n"
        "raw result hidden\n"
        "`````\n"
        "[Info] Final response to user.\n"
        ".\n"
    )

    assert rendering.visible_reply_text(body, hide_detail_fences=True) == "Visible answer"


def test_strip_standalone_dot_lines_keeps_decimal_and_sentence_punctuation() -> None:
    assert rendering.strip_standalone_dot_lines("A\n.\n3.14\nend.\n . \nB") == "A\n3.14\nend.\nB"


def test_visible_reply_text_collapses_three_or_more_newlines() -> None:
    assert rendering.visible_reply_text("A\n\n\n\nB") == "A\n\nB"


def test_visible_reply_policy_identifies_substantive_content() -> None:
    long_plain = "这是一段完整可见答复。" * 20
    structured = "# 结论\n" + ("这是结构化报告内容。" * 10)

    assert rendering.visible_reply_is_substantive(long_plain)
    assert rendering.visible_reply_is_substantive(structured)
    assert not rendering.visible_reply_is_substantive("短答复")


def test_visible_reply_policy_identifies_housekeeping_summary() -> None:
    assert rendering.visible_reply_is_housekeeping_summary("Summary: task complete\nConfidence: high")
    assert rendering.visible_reply_is_housekeeping_summary("摘要：任务完成\n置信度：高")
    assert not rendering.visible_reply_is_housekeeping_summary("Summary: useful answer without completion marker")
    assert not rendering.visible_reply_is_housekeeping_summary("")


def test_visible_reply_policy_identifies_section_shape() -> None:
    assert rendering.visible_reply_has_section_shape("## 方案\n正文")
    assert rendering.visible_reply_has_section_shape("最终结论：可以继续")
    assert not rendering.visible_reply_has_section_shape("plain paragraph")


def test_latest_visible_reply_text_prefers_latest_nonempty_turn_body() -> None:
    text = (
        "LLM Running (Turn 1) ...\n"
        "First answer\n"
        "LLM Running (Turn 2) ...\n"
        "<summary>hidden</summary>\n"
        "Second answer\n"
    )

    assert rendering.latest_visible_reply_text(text) == "Second answer"


def test_latest_visible_reply_text_falls_back_to_earlier_visible_turn() -> None:
    text = (
        "LLM Running (Turn 1) ...\n"
        "Earlier visible answer\n"
        "LLM Running (Turn 2) ...\n"
        "<summary>hidden</summary>\n"
        "🛠️ Tool: `web.search` 📥 args:\n"
        "````text\n"
        "{\"q\":\"needle\"}\n"
        "````\n"
        "`````\n"
        "raw result hidden\n"
        "`````\n"
        "[Info] Final response to user.\n"
        ".\n"
    )

    assert rendering.latest_visible_reply_text(text) == "Earlier visible answer"


def test_latest_visible_reply_text_uses_injected_tool_noise_for_fallback() -> None:
    body = "Final answer\n`````\nraw result\n`````"

    assert rendering.latest_visible_reply_text(body) == body
    assert rendering.latest_visible_reply_text(body, has_tool_noise=lambda _text: True) == "Final answer"
    assert rendering.latest_visible_reply_text(body, has_tool_noise=lambda _text: False) == body


def test_app_latest_visible_reply_wrapper_injects_app_tool_noise_predicate() -> None:
    body = "Final answer\n`````\nraw result\n`````"

    assert app_module.latest_visible_reply_text(body) == rendering.latest_visible_reply_text(
        body,
        has_tool_noise=app_module.process_has_tool_noise,
    )
    assert app_module.latest_visible_reply_text(body) == "Final answer"


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
    assert app_module.strip_meta_blocks is rendering.strip_meta_blocks
    assert app_module.process_preview is rendering.process_preview
    assert app_module.process_summary_text is rendering.process_summary_text
    assert app_module.LINE_NUMBERED_FILE_RE is rendering.LINE_NUMBERED_FILE_RE
    assert app_module.FENCE_BOUNDARY_RE is rendering.FENCE_BOUNDARY_RE
    assert app_module.next_nonblank_line is rendering.next_nonblank_line
    assert app_module.line_numbered_file_line is rendering.line_numbered_file_line
    assert app_module.stray_line_numbered_fence_close is rendering.stray_line_numbered_fence_close
    assert app_module.split_top_level_turn_markers is rendering.split_top_level_turn_markers
    assert app_module.close_unbalanced_markdown_fence is rendering.close_unbalanced_markdown_fence
    assert app_module.TOOL_CALL_BLOCK_RE is rendering.TOOL_CALL_BLOCK_RE
    assert app_module.TOOL_RESULT_FENCE_RE is rendering.TOOL_RESULT_FENCE_RE
    assert app_module.FINAL_RESPONSE_INFO_RE is rendering.FINAL_RESPONSE_INFO_RE
    assert app_module.strip_tool_output_blocks is rendering.strip_tool_output_blocks
    assert app_module.strip_standalone_dot_lines is rendering.strip_standalone_dot_lines
    assert app_module.visible_reply_text is rendering.visible_reply_text
    assert app_module.visible_reply_is_substantive is rendering.visible_reply_is_substantive
    assert app_module.visible_reply_is_housekeeping_summary is rendering.visible_reply_is_housekeeping_summary
    assert app_module.visible_reply_has_section_shape is rendering.visible_reply_has_section_shape
    assert app_module.latest_visible_reply_text("plain") == rendering.latest_visible_reply_text(
        "plain",
        has_tool_noise=app_module.process_has_tool_noise,
    )
    assert app_module.running_indicator is rendering.running_indicator
    assert app_module.running_indicator_cell_width is rendering.running_indicator_cell_width
    assert app_module.render_running_indicator_line is rendering.render_running_indicator_line
