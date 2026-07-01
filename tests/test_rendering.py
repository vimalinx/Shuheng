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


def test_boxed_user_lines_preserves_min_width_empty_and_wrapping() -> None:
    assert rendering.boxed_user_lines("hi", 20) == [
        "┌──────────┐",
        "│ hi       │",
        "└──────────┘",
    ]
    assert rendering.boxed_user_lines("", 4) == [
        "┌──────────┐",
        "│          │",
        "└──────────┘",
    ]
    assert rendering.boxed_user_lines("abcdefghij", 10) == [
        "┌──────────┐",
        "│ abcdefgh │",
        "│ ij       │",
        "└──────────┘",
    ]


def test_boxed_user_lines_pads_wide_text_by_cells() -> None:
    lines = rendering.boxed_user_lines("中文abc", 8)

    assert lines == [
        "┌──────────┐",
        "│ 中文abc  │",
        "└──────────┘",
    ]
    assert len({rendering.cell_width(line) for line in lines}) == 1


def test_strip_inline_markdown_cleans_inline_markup() -> None:
    assert rendering.strip_inline_markdown("![alt](https://example.invalid/img.png)") == "[alt]"
    assert rendering.strip_inline_markdown("[docs](https://example.invalid)") == "docs (https://example.invalid)"
    assert rendering.strip_inline_markdown("run `cmd --flag` now") == "run cmd --flag now"
    assert rendering.strip_inline_markdown("**bold** __strong__ *italic* _em_") == "bold strong italic em"


def test_is_table_separator_detects_markdown_alignment_rows() -> None:
    assert rendering.is_table_separator(["---", ":---", "---:", ":---:"])
    assert rendering.is_table_separator([" --- ", " :---: "])
    assert not rendering.is_table_separator([])
    assert not rendering.is_table_separator(["--"])
    assert not rendering.is_table_separator(["---", "value"])


def test_split_table_row_trims_edges_and_cleans_inline_markdown() -> None:
    row = "| **Name** | [Doc](https://example.invalid) | `cmd --flag` |"

    assert rendering.split_table_row(row) == [
        "Name",
        "Doc (https://example.invalid)",
        "cmd --flag",
    ]
    assert rendering.split_table_row(" name | _value_ ") == ["name", "value"]


def test_table_layout_lines_formats_header_separator_and_body_rows() -> None:
    lines = [
        "| **Name** | Count |",
        "| --- | ---: |",
        "| Alpha | 3 |",
        "| 中文 | 20 |",
    ]

    assert rendering.table_layout_lines(lines, 24) == [
        ("header", "Name  │ Count"),
        ("separator", "──────┼──────"),
        ("body", "Alpha │ 3    "),
        ("body", "中文  │ 20   "),
    ]


def test_table_layout_lines_returns_empty_for_separator_only_tables() -> None:
    assert rendering.table_layout_lines(["| --- | :---: |"], 80) == []


def test_table_layout_lines_caps_columns_to_available_width() -> None:
    lines = [
        "| First column is long | Second column is long |",
        "| --- | --- |",
        "| alpha beta gamma | delta epsilon zeta |",
    ]

    assert rendering.table_layout_lines(lines, 15) == [
        ("header", "First … │ Second…"),
        ("separator", "───────┼───────"),
        ("body", "alpha … │ delta …"),
    ]


def test_app_render_table_wrapper_converts_layout_records_to_render_lines() -> None:
    lines = [
        "| Name | Count |",
        "| --- | ---: |",
        "| Alpha | 3 |",
    ]

    rendered = app_module.render_table(lines, 24)

    assert [line.text for line in rendered] == [text for _kind, text in rendering.table_layout_lines(lines, 24)]
    assert [line.attr for line in rendered] == [
        app_module.cp(7) | app_module.curses.A_BOLD,
        app_module.cp(10),
        app_module.cp(2),
    ]


def test_markdown_layout_blocks_covers_markdown_block_shapes() -> None:
    text = "\n".join(
        [
            "```python",
            "print('枢衡')",
            "```",
            "",
            "| **Name** | Count |",
            "| --- | ---: |",
            "| Alpha | 3 |",
            "---",
            "## **Heading**",
            "### Minor",
            "> quote *text*",
            "- [x] done",
            "- [ ] todo",
            "* bullet **item**",
            "12. numbered `item`",
            "plain body",
        ]
    )

    assert rendering.markdown_layout_blocks(text, 32) == [
        ("code_header", "╭─ python"),
        ("code_body", "│ print('枢衡')"),
        ("code_footer", "╰─"),
        ("blank", ""),
        ("table_header", "Name  │ Count"),
        ("table_separator", "──────┼──────"),
        ("table_body", "Alpha │ 3    "),
        ("rule", "────────────────────────────────"),
        ("heading_major", "█ Heading"),
        ("heading_minor", "▪ Minor"),
        ("quote", "▌ quote text"),
        ("body", "  ☑ done"),
        ("body", "  ☐ todo"),
        ("body", "  • bullet item"),
        ("body", "  12. numbered item"),
        ("body", "plain body"),
    ]


def test_app_markdown_blocks_wrapper_converts_layout_records_to_render_lines() -> None:
    text = "\n".join(
        [
            "```python",
            "print('x')",
            "```",
            "",
            "| Name | Count |",
            "| --- | ---: |",
            "| Alpha | 3 |",
            "---",
            "## Heading",
            "### Minor",
            "> quote",
            "- [x] done",
        ]
    )

    rendered = app_module.markdown_blocks(text, 32)
    layout = rendering.markdown_layout_blocks(text, 32)

    assert [line.text for line in rendered] == [line for _kind, line in layout]
    assert [line.attr for line in rendered] == [
        app_module.cp(10) | app_module.curses.A_BOLD,
        app_module.cp(2),
        app_module.cp(10),
        0,
        app_module.cp(7) | app_module.curses.A_BOLD,
        app_module.cp(10),
        app_module.cp(2),
        app_module.cp(10),
        app_module.cp(7) | app_module.curses.A_BOLD,
        app_module.cp(1) | app_module.curses.A_BOLD,
        app_module.cp(10),
        app_module.cp(2),
    ]
    assert app_module.markdown_layout_blocks is rendering.markdown_layout_blocks


def test_plain_layout_lines_wraps_plain_text() -> None:
    assert rendering.plain_layout_lines("", 20) == [""]
    assert rendering.plain_layout_lines("abcdefghij", 4) == ["abcd…"]
    assert rendering.plain_layout_lines("abcdefghij", 5) == ["abcde", "fghij"]
    assert rendering.plain_layout_lines("中文abc", 5) == ["中文a", "bc"]


def test_app_plain_blocks_wrapper_converts_plain_layout_to_render_lines() -> None:
    rendered = app_module.plain_blocks("中文abc", 5)

    assert [line.text for line in rendered] == rendering.plain_layout_lines("中文abc", 5)
    assert [line.attr for line in rendered] == [app_module.cp(2), app_module.cp(2)]
    assert app_module.plain_layout_lines is rendering.plain_layout_lines


def test_parse_subagent_result_notice_extracts_headers_and_body() -> None:
    notice = rendering.parse_subagent_result_notice(
        "子 agent 回复 · 研究员 (agent-research)\n"
        "Task: task_123\n"
        "Artifact: artifact://subagent-results/report.md\n"
        "\n"
        "主体回复\n"
        "第二行\n"
    )

    assert notice == {
        "name": "研究员",
        "agent_id": "agent-research",
        "task_id": "task_123",
        "artifact_ref": "artifact://subagent-results/report.md",
        "body": "主体回复\n第二行",
    }
    assert rendering.parse_subagent_result_notice("ordinary system message") is None


def test_subagent_result_metadata_helpers_split_entries_and_summary() -> None:
    notice = {
        "name": "研究员",
        "agent_id": "agent-research",
        "task_id": "task_123",
        "artifact_ref": "artifact://subagent-results/report.md",
        "body": "",
    }
    reply, metadata_lines = rendering.split_subagent_result_reply_and_metadata(
        "可见回复\n"
        "\n"
        "---\n"
        "Findings:\n"
        "1. 第一项\n"
        "2. 第二项\n"
        "Confidence: 高\n"
        "Risks: 无\n"
    )

    assert reply == "可见回复"
    assert metadata_lines == [
        "Findings:",
        "1. 第一项",
        "2. 第二项",
        "Confidence: 高",
        "Risks: 无",
    ]
    assert rendering.subagent_result_metadata_entries(metadata_lines) == [
        ("Findings", "1. 第一项\n2. 第二项"),
        ("Confidence", "高"),
        ("Risks", "无"),
    ]
    assert rendering.subagent_result_metadata_labels(notice, metadata_lines) == [
        "Task",
        "Artifact",
        "Findings",
        "Confidence",
        "Risks",
    ]
    assert rendering.count_list_like_metadata_value("a, b, c") == 3
    assert rendering.count_list_like_metadata_value("无") == 0
    assert rendering.subagent_result_metadata_summary(notice, metadata_lines) == (
        "Confidence: 高 · Findings: 2 · Risks: 0 · Task · Artifact"
    )
    assert rendering.subagent_meta_label(notice).startswith("S")
    assert len(rendering.subagent_meta_label(notice)) == 9


def test_app_subagent_result_notice_helpers_are_rendering_aliases() -> None:
    for name in (
        "SUBAGENT_RESULT_HEADER_RE",
        "SUBAGENT_RESULT_META_LABEL_RE",
        "parse_subagent_result_notice",
        "subagent_result_metadata_separator",
        "subagent_result_metadata_label",
        "subagent_result_metadata_value",
        "split_subagent_result_reply_and_metadata",
        "subagent_result_metadata_labels",
        "count_list_like_metadata_value",
        "subagent_result_metadata_entries",
        "subagent_result_metadata_summary",
        "subagent_meta_label",
    ):
        assert getattr(app_module, name) is getattr(rendering, name), name


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


def test_message_cache_signature_tracks_identity_role_length_and_done() -> None:
    msg = Message("assistant", "streaming body", done=False)
    same_text = Message("assistant", "streaming body", done=False)
    changed_role = Message("user", "streaming body", done=False)
    changed_length = Message("assistant", "streaming body!", done=False)
    changed_done = Message("assistant", "streaming body", done=True)

    signature = rendering.message_cache_signature([msg])

    assert signature == ((id(msg), "assistant", len("streaming body"), False),)
    assert rendering.message_cache_signature([same_text]) != signature
    assert rendering.message_cache_signature([changed_role]) != signature
    assert rendering.message_cache_signature([changed_length]) != signature
    assert rendering.message_cache_signature([changed_done]) != signature


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


def test_process_line_format_helpers_render_expected_strings() -> None:
    marker = "**LLM Running (Turn 7) ...**"

    assert rendering.process_turn_label(marker) == "Turn 7"
    assert rendering.process_turn_label("no marker") == "Turn"
    assert rendering.process_turn_no(marker, 99) == 7
    assert rendering.process_turn_no("no marker", 99) == 99
    assert rendering.process_tool_suffix([]) == ""
    assert rendering.process_tool_suffix(["web.search", "irc", "todo", "code"]) == " · tool: web.search, irc, todo +1"
    assert rendering.collapsed_process_line_text(marker, "整理结果", ["web.search"], True) == (
        "▸ 过程 Turn 7: 整理结果 · tool: web.search (正在执行)"
    )
    assert rendering.process_detail_line_text(marker, "整理结果", ["web.search"], False) == (
        "▸ 细节 Turn 7: 整理结果 · tool: web.search (已折叠)"
    )
    assert rendering.process_speech_header_text(marker, ["web.search"]) == "· 过程 Turn 7 · tool: web.search"
    assert rendering.process_speech_summary_line_text(marker, "整理结果", ["web.search"]) == (
        "· 过程 Turn 7: 整理结果 · tool: web.search"
    )
    assert rendering.expanded_process_header_text(marker, "整理结果", ["web.search"], True) == (
        "▾ 过程 Turn 7: 整理结果 · tool: web.search (正在等待用户输入)"
    )
    assert rendering.process_group_header_text("G2", "整理结果 / 查询资料", ["web.search", "irc"], False, True) == (
        "▾ 过程组 G2: 整理结果 / 查询资料 · tool: web.search, irc (已展开，点击展开/收起)"
    )
    assert rendering.collapsed_process_child_line_text("G2T7", "▸ 过程 Turn 7: 整理结果 (已折叠)") == (
        "  ▸ 过程 G2T7 Turn 7: 整理结果 (已折叠)"
    )
    assert rendering.expanded_process_child_header_text("G2T7", "▾ 过程 Turn 7: 整理结果 (已展开)") == (
        "  ▾ 过程 G2T7 Turn 7: 整理结果 (已展开)"
    )


def test_process_child_detail_text_formats_fallback_truncation_and_indent() -> None:
    assert rendering.process_child_detail_text(
        "<summary>hidden</summary>\nVisible line\nSecond line",
        "fallback",
    ) == "    Visible line\n    Second line"
    assert rendering.process_child_detail_text("<summary>hidden</summary>", "fallback") == "    fallback"
    assert rendering.process_child_detail_text("", "") == ""
    assert rendering.process_child_detail_text("abcdef", "fallback", limit=3) == (
        "    abc\n    ...（详情过长，已截断；需要原文请打开对应 artifact/trace）"
    )


def test_process_noise_helpers_use_explicit_tool_names_and_markers() -> None:
    tool_call_body = "plain body"
    tool_header_body = "🛠️ Tool: `web.search` 📥 args:\n"
    tool_result_body = "`````\nraw result\n`````\n[Info] Final response to user."

    assert rendering.process_has_tool_call_noise_text(tool_call_body, ["web.search"])
    assert rendering.process_has_tool_call_noise_text("<tool_use>{}</tool_use>", [])
    assert rendering.process_has_tool_call_noise_text(tool_header_body, [])
    assert not rendering.process_has_tool_call_noise_text(tool_call_body, [])
    assert rendering.process_has_tool_result_noise_text(tool_result_body)
    assert not rendering.process_has_tool_result_noise_text("visible answer")
    assert rendering.process_has_tool_noise_text(tool_result_body, [])
    assert rendering.process_has_tool_noise_text(tool_call_body, ["query"])
    assert not rendering.process_has_tool_noise_text("visible answer", [])


def test_process_search_noise_helper_uses_tools_and_body_markers() -> None:
    assert rendering.process_has_search_noise_text("plain", ["web_search"])
    assert rendering.process_has_search_noise_text("plain", ["browser_open"])
    assert rendering.process_has_search_noise_text("plain", ["bb_browser"])
    assert rendering.process_has_search_noise_text("plain", ["vector_query"])
    assert rendering.process_has_search_noise_text("Search results\nitem", [])
    assert rendering.process_has_search_noise_text("DOM变化量 很大", [])
    assert not rendering.process_has_search_noise_text("visible answer", ["irc"])


def test_preferred_group_visible_reply_text_prefers_latest_visible_reply() -> None:
    first = "First answer. " * 20
    second = "Second answer. " * 20

    assert rendering.preferred_group_visible_reply_text([first, second], []) == second


def test_preferred_group_visible_reply_text_prefers_richer_earlier_reply_over_housekeeping() -> None:
    rich = "## 方案\n" + ("这里是结构化、可读、对用户有用的完整内容。" * 12)
    housekeeping = "Summary: task complete\nConfidence: high"

    assert rendering.preferred_group_visible_reply_text([rich, housekeeping], []) == rich


def test_preferred_group_visible_reply_text_appends_deduped_irc_replies() -> None:
    chosen = "Final answer mentions Bob: already handled"

    assert rendering.preferred_group_visible_reply_text(
        [chosen],
        ["Alice: hello", "Alice: hello", "Bob: already handled", ""],
    ) == "Final answer mentions Bob: already handled\n\n### IRC 回复\n- Alice: hello"
    assert rendering.preferred_group_visible_reply_text([], ["Alice: hello"]) == "### IRC 回复\n- Alice: hello"


def test_process_turn_lines_closes_final_text_and_adds_header_detail() -> None:
    assert rendering.process_turn_lines(
        "```python\nprint('x')",
        has_process_noise=True,
        has_call_noise=True,
        fold_details=True,
        collapsed_line="collapsed",
        speech_header_line="header",
        detail_line="detail",
    ) == [
        "header",
        "```python\nprint('x')\n```",
        "detail",
    ]


def test_process_turn_lines_collapses_whole_process_output() -> None:
    folded = rendering.process_turn_lines(
        "visible answer",
        has_process_noise=True,
        has_call_noise=False,
        fold_details=True,
        collapse_whole=True,
        collapsed_line="collapsed",
        summary_line="summary",
    )
    unfolded = rendering.process_turn_lines(
        "visible answer",
        has_process_noise=True,
        has_call_noise=False,
        fold_details=False,
        collapse_whole=True,
        collapsed_line="collapsed",
        summary_line="summary",
    )

    assert folded == ["visible answer", "collapsed"]
    assert unfolded == ["visible answer"]


def test_process_turn_lines_uses_fallback_summary_or_collapsed_noise() -> None:
    assert rendering.process_turn_lines(
        "",
        has_process_noise=True,
        has_call_noise=True,
        fold_details=True,
        collapsed_line="collapsed",
        detail_line="detail",
        fallback_summary_line="fallback summary",
    ) == ["fallback summary", "detail"]
    assert rendering.process_turn_lines(
        "",
        has_process_noise=True,
        has_call_noise=False,
        collapsed_line="collapsed",
    ) == ["collapsed"]
    assert rendering.process_turn_lines(
        "",
        has_process_noise=False,
        has_call_noise=False,
        fallback_summary_line="fallback summary",
    ) == ["fallback summary"]


def test_app_append_process_turn_wrapper_delegates_line_selection_to_rendering() -> None:
    marker = "**LLM Running (Turn 9) ...**"
    body = (
        "<summary>查询资料</summary>\n"
        "Final answer\n"
        "🛠️ Tool: `web.search` 📥 args:\n"
        "````text\n"
        "{\"q\":\"needle\"}\n"
        "````\n"
    )
    rendered: list[str] = []

    app_module.append_process_turn(rendered, marker, body, current=True)

    has_process_noise = app_module.process_has_tool_noise(body)
    has_call_noise = app_module.process_has_tool_call_noise(body)
    final_text = app_module.visible_reply_text(body, hide_detail_fences=has_process_noise)
    summary = app_module.process_summary_text(body)
    title_summary = app_module.process_title_text(body)
    assert rendered == rendering.process_turn_lines(
        final_text,
        has_process_noise=has_process_noise,
        has_call_noise=has_call_noise,
        fold_details=True,
        collapse_whole=False,
        collapsed_line=app_module.collapsed_process_line(marker, body, current=True),
        speech_header_line=app_module.process_speech_header(marker, body),
        summary_line=app_module.process_speech_summary_line(marker, body, summary)
        if summary and summary != "执行中"
        else "",
        detail_line=app_module.process_detail_line(marker, body, current=True),
        fallback_summary_line=app_module.process_speech_summary_line(marker, body, title_summary)
        if title_summary and title_summary != "执行中"
        else "",
    )


def test_app_process_line_wrappers_inject_app_owned_dependencies() -> None:
    marker = "**LLM Running (Turn 7) ...**"
    body = (
        "<summary>整理结果</summary>\n"
        "🛠️ Tool: `web.search` 📥 args:\n"
        "````text\n{}\n````\n"
        "<tool_use>{\"name\":\"irc\"}</tool_use>\n"
    )
    tools = app_module.process_tools(body)

    assert app_module.collapsed_process_line(marker, body, True) == rendering.collapsed_process_line_text(
        marker,
        app_module.process_title_text(body),
        tools,
        True,
    )
    assert app_module.process_detail_line(marker, body, False) == rendering.process_detail_line_text(
        marker,
        app_module.process_summary_text(body),
        tools,
        False,
    )
    assert app_module.process_speech_header(marker, body) == rendering.process_speech_header_text(marker, tools)
    assert app_module.process_speech_summary_line(marker, body, "人工摘要") == rendering.process_speech_summary_line_text(
        marker,
        "人工摘要",
        tools,
    )
    assert app_module.expanded_process_header(marker, body, True) == rendering.expanded_process_header_text(
        marker,
        app_module.process_summary_text(body),
        tools,
        True,
    )
    assert app_module.process_turn_no(marker, 99) == rendering.process_turn_no(marker, 99)
    assert app_module.collapsed_process_child_line("G2T7", marker, body, False) == rendering.collapsed_process_child_line_text(
        "G2T7",
        app_module.collapsed_process_line(marker, body, False),
    )
    assert app_module.expanded_process_child_header("G2T7", marker, body, False) == rendering.expanded_process_child_header_text(
        "G2T7",
        app_module.expanded_process_header(marker, body, False),
    )
    assert app_module.process_child_detail(body) == rendering.process_child_detail_text(
        app_module.strip_tui_controls(body),
        app_module.process_preview(body),
    )


def test_app_process_child_detail_wrapper_keeps_control_stripping_app_owned() -> None:
    body = (
        "Visible detail\n"
        "<ga-control>{\"action\":\"agent.create\",\"params\":{\"name\":\"Hidden\"}}</ga-control>\n"
        "<summary>hidden summary</summary>"
    )

    detail = app_module.process_child_detail(body)

    assert detail == rendering.process_child_detail_text(
        app_module.strip_tui_controls(body),
        app_module.process_preview(body),
    )
    assert "ga-control" not in detail
    assert "Hidden" not in detail


def test_app_process_noise_wrappers_inject_process_tools() -> None:
    body = (
        "<summary>查询资料</summary>\n"
        "🛠️ Tool: `web.search` 📥 args:\n"
        "````text\n{\"q\":\"needle\"}\n````\n"
        "`````\nraw result\n`````\n"
    )
    tools = app_module.process_tools(body)

    assert app_module.process_has_tool_call_noise(body) == rendering.process_has_tool_call_noise_text(body, tools)
    assert app_module.process_has_tool_result_noise(body) == rendering.process_has_tool_result_noise_text(body)
    assert app_module.process_has_tool_noise(body) == rendering.process_has_tool_noise_text(body, tools)
    assert app_module.process_has_search_noise(body) == rendering.process_has_search_noise_text(body, tools)
    assert app_module.process_has_search_noise("google.com/search?q=needle")


def test_app_preferred_group_visible_reply_wrapper_delegates_selection_to_rendering() -> None:
    rich = "## 方案\n" + ("这里是结构化、可读、对用户有用的完整内容。" * 12)
    housekeeping = "Summary: task complete\nConfidence: high"
    turns = [
        ("**LLM Running (Turn 1) ...**", rich),
        ("**LLM Running (Turn 2) ...**", housekeeping),
    ]
    visible_items = [
        rendering.visible_reply_text(body, hide_detail_fences=app_module.process_has_tool_noise(body)).strip()
        for _marker, body in turns
    ]

    assert app_module.preferred_group_visible_reply(turns) == rendering.preferred_group_visible_reply_text(
        visible_items,
        [],
    )


def test_app_preferred_group_visible_reply_wrapper_keeps_irc_parsing_app_owned() -> None:
    body = (
        "🛠️ Tool: `irc` 📥 args:\n"
        "````text\n{}\n````\n"
        "`````\n"
        "{\"content\":[{\"text\":\"Reply from Alice: hello\"}]}\n"
        "`````\n"
    )
    turns = [("**LLM Running (Turn 3) ...**", body)]
    irc_replies = app_module.irc_reply_snippets_from_process_body(body)

    assert irc_replies == ["Alice: hello"]
    assert app_module.preferred_group_visible_reply(turns) == rendering.preferred_group_visible_reply_text(
        [],
        irc_replies,
    )


def test_app_process_group_header_wrapper_preserves_summary_and_tool_selection() -> None:
    turns = [
        (
            "**LLM Running (Turn 1) ...**",
            "<summary>查询资料</summary>\n🛠️ Tool: `web.search` 📥 args:\n````text\n{}\n````",
        ),
        (
            "**LLM Running (Turn 2) ...**",
            "<summary>整理结果</summary>\n🛠️ Tool: `irc` 📥 args:\n````text\n{}\n````",
        ),
    ]

    assert app_module.process_group_header("G4", turns, current=False, expanded=False) == (
        "▸ 过程组 G4: 查询资料 / 整理结果 · tool: web.search, irc (已折叠，点击展开/收起)"
    )


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
    assert app_module.message_cache_signature is rendering.message_cache_signature
    assert app_module.message_render_cache_key is rendering.message_render_cache_key
    assert app_module.strip_meta_blocks is rendering.strip_meta_blocks
    assert app_module.process_preview is rendering.process_preview
    assert app_module.process_summary_text is rendering.process_summary_text
    assert app_module.strip_inline_markdown is rendering.strip_inline_markdown
    assert app_module.is_table_separator is rendering.is_table_separator
    assert app_module.split_table_row is rendering.split_table_row
    assert app_module.table_layout_lines is rendering.table_layout_lines
    assert app_module.markdown_layout_blocks is rendering.markdown_layout_blocks
    assert app_module.plain_layout_lines is rendering.plain_layout_lines
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
    assert app_module.preferred_group_visible_reply_text is rendering.preferred_group_visible_reply_text
    assert app_module.process_turn_lines is rendering.process_turn_lines
    assert app_module.boxed_user_lines is rendering.boxed_user_lines
    assert app_module.TURN_NO_RE is rendering.TURN_NO_RE
    assert app_module.process_turn_label is rendering.process_turn_label
    assert app_module.process_tool_suffix is rendering.process_tool_suffix
    assert app_module.process_turn_no is rendering.process_turn_no
    assert app_module.collapsed_process_line_text is rendering.collapsed_process_line_text
    assert app_module.process_detail_line_text is rendering.process_detail_line_text
    assert app_module.process_speech_header_text is rendering.process_speech_header_text
    assert app_module.process_speech_summary_line_text is rendering.process_speech_summary_line_text
    assert app_module.expanded_process_header_text is rendering.expanded_process_header_text
    assert app_module.process_group_header_text is rendering.process_group_header_text
    assert app_module.collapsed_process_child_line_text is rendering.collapsed_process_child_line_text
    assert app_module.expanded_process_child_header_text is rendering.expanded_process_child_header_text
    assert app_module.process_child_detail_text is rendering.process_child_detail_text
    assert app_module.process_has_tool_call_noise_text is rendering.process_has_tool_call_noise_text
    assert app_module.process_has_tool_result_noise_text is rendering.process_has_tool_result_noise_text
    assert app_module.process_has_tool_noise_text is rendering.process_has_tool_noise_text
    assert app_module.process_has_search_noise_text is rendering.process_has_search_noise_text
    assert app_module.latest_visible_reply_text("plain") == rendering.latest_visible_reply_text(
        "plain",
        has_tool_noise=app_module.process_has_tool_noise,
    )
    assert app_module.running_indicator is rendering.running_indicator
    assert app_module.running_indicator_cell_width is rendering.running_indicator_cell_width
    assert app_module.render_running_indicator_line is rendering.render_running_indicator_line
