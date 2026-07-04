"""Tests for curses-free rendering helper transforms."""
from __future__ import annotations

from shuheng import app as app_module
from shuheng import rendering
from shuheng.ui_types import Message, RenderLine


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


def test_interaction_card_formats_candidate_and_approval_prompts() -> None:
    assert rendering.sanitize_interaction_candidates(['1) 继续', '["继续"]', "2、稍后", ""]) == ["继续", "稍后"]
    assert rendering.render_interaction_card(
        {
            "tool": "ask_user",
            "question": "选择下一步\n请确认",
            "candidates": ["1) 继续", "2) 稍后"],
        }
    ) == (
        "╭─ 需要你输入 · ask_user\n"
        "│ 问题：\n"
        "│   选择下一步\n"
        "│   请确认\n"
        "│\n"
        "│ 候选项：\n"
        "│   1) 继续\n"
        "│   2) 稍后\n"
        "│\n"
        "│ 在底部回答框用 ↑/↓ 选择，Enter 提交；也可输入 1-2 或直接打字。\n"
        "╰─"
    )
    assert rendering.render_interaction_card(
        {"tool": "approval", "question": "批准写入？", "candidates": ["批准", "拒绝"]}
    ).splitlines()[-2] == "│ 在底部回答框用 ↑/↓ 选择，Enter 执行；选“稍后处理”会保留待审批项。"


def test_interaction_card_formats_request_user_input_and_fallback() -> None:
    default_card = (
        "╭─ 需要你输入 · interactive\n"
        "│ 问题：\n"
        "│   工具正在等待你的输入。\n"
        "│\n"
        "│ 在底部回答框直接输入答案，Enter 发送。\n"
        "╰─"
    )
    assert rendering.render_interaction_card(
        {
            "tool": "request_user_input",
            "questions": [
                {"header": "范围", "question": "要处理哪些文件？", "options": ["1) 全部", "2) 仅核心"]},
                {"question": "是否提交？"},
            ],
        }
    ) == (
        "╭─ 需要你输入 · request_user_input\n"
        "│ 1. 范围\n"
        "│    要处理哪些文件？\n"
        "│    1) 全部\n"
        "│    2) 仅核心\n"
        "│ 2. 问题 2\n"
        "│    是否提交？\n"
        "│\n"
        "│ request_user_input 会在底部显示独立 qN> 输入口，逐题记录后统一发送。\n"
        "╰─"
    )
    assert rendering.render_interaction_card({}) == default_card
    assert rendering.visible_ask_user_card_text(None) == default_card
    payload = {"tool": "ask_user", "question": "选择下一步", "candidates": ["继续"]}
    assert rendering.visible_ask_user_card_text(payload) == rendering.render_interaction_card(payload)
    tool_use = '<tool_use>{"name":"ask_user","arguments":{"question":"选择下一步","candidates":["继续"]}}</tool_use>'
    assert app_module.visible_ask_user_text(tool_use) == rendering.render_interaction_card(payload)
    assert app_module.visible_ask_user_text("ask_user") == default_card


def test_interaction_answer_helpers_preserve_candidate_and_prompt_behavior() -> None:
    candidates = ["1) 批准并执行", "2) 拒绝", "3) 稍后处理"]

    assert rendering.interaction_answer_from_text("2", candidates, selected=0) == "拒绝"
    assert rendering.interaction_answer_from_text("手动回答", candidates, selected=0) == "手动回答"
    assert rendering.interaction_answer_from_text("", candidates, selected=2) == "稍后处理"
    assert rendering.interaction_answer_from_text("", candidates, selected=99) == "稍后处理"
    assert rendering.interaction_answer_from_text("", [], selected=0) == ""
    assert rendering.interaction_input_prompt_text(False) == "> "
    assert rendering.interaction_input_prompt_text(True, is_approval=True) == "approval> "
    assert rendering.interaction_input_prompt_text(True, current_question_index=1) == "q2> "
    assert rendering.interaction_input_prompt_text(True) == "? "
    assert rendering.interaction_footer_text(False) == ""
    assert (
        rendering.interaction_footer_text(True, has_candidates=True, is_approval=True)
        == "↑/↓ 选择，空输入 Enter 执行选中审批动作；选“稍后处理”保留待审批项。"
    )
    assert (
        rendering.interaction_footer_text(True, has_candidates=True)
        == "↑/↓ 选择，空输入 Enter 提交选中项；也可以直接打字回答。"
    )
    assert (
        rendering.interaction_footer_text(True, has_questions=True)
        == "request_user_input 独立输入口：输入本题答案，Enter 记录并进入下一题。"
    )
    assert rendering.interaction_footer_text(True) == "等待你的输入：直接在下面回答；Enter 发送。"

    payload = {"candidates": candidates, "_selection": 2}
    assert app_module.interaction_answer_from_input(payload, "") == "稍后处理"
    assert app_module.interaction_answer_from_input(payload, "1") == "批准并执行"
    assert app_module.interaction_input_prompt({"tool": "approval", "approval_id": "appr_test"}) == "approval> "
    assert app_module.interaction_input_prompt({"questions": [{"question": "A"}, {"question": "B"}], "_current": 1}) == "q2> "
    assert app_module.interaction_footer(None) == rendering.interaction_footer_text(False)
    assert app_module.interaction_footer(payload) == rendering.interaction_footer_text(True, has_candidates=True)
    assert app_module.interaction_footer({"questions": [{"question": "A"}]}) == rendering.interaction_footer_text(
        True,
        has_questions=True,
    )
    assert app_module.interaction_footer({"tool": "approval", "approval_id": "appr_test", "candidates": candidates}) == (
        rendering.interaction_footer_text(True, has_candidates=True, is_approval=True)
    )


def test_interaction_hint_layout_lines_preserve_prompt_candidates_and_footer() -> None:
    assert rendering.interaction_hint_layout_lines(False, width=60) == []
    assert rendering.interaction_hint_layout_lines(
        True,
        width=60,
        tool="ask_user",
        title_source="选择下一步",
        candidates=["继续", "稍后"],
        selected=1,
        footer="footer text",
    ) == [
        ("header", "? ask_user: 选择下一步"),
        ("candidate", "  1) 继续"),
        ("candidate_selected", "> 2) 稍后"),
        ("footer", "footer text"),
    ]
    assert rendering.interaction_hint_layout_lines(
        True,
        width=60,
        title_source="请填写",
        questions_count=2,
        current_question_index=1,
        current_question_text="第二题问题",
        footer="question footer",
    ) == [
        ("header", "? request_user_input 2/2: 请填写"),
        ("body", "  第二题问题"),
        ("footer", "question footer"),
    ]


def test_interaction_hint_layout_lines_preserve_approval_preview_and_candidate_window() -> None:
    lines = rendering.interaction_hint_layout_lines(
        True,
        width=48,
        tool="approval",
        title_source="审批 appr_test",
        approval_preview_text="\n".join(f"预览 {idx}" for idx in range(1, 9)),
        is_approval=True,
        candidates=[f"选项 {idx}" for idx in range(1, 9)],
        selected=7,
        footer="approval footer",
    )

    assert lines[:2] == [
        ("header", "? approval: 审批 appr test"),
        ("body", "  预览 1"),
    ]
    assert ("muted", "  ... /approvals 可查看完整候选记忆") in lines
    assert ("candidate", "  3) 选项 3") in lines
    assert ("candidate_selected", "> 8) 选项 8") in lines
    assert ("muted", "  ... 8 个选项，当前 8/8") in lines
    assert lines[-1] == ("footer", "approval footer")


def test_app_interaction_hint_wrapper_injects_payload_facts_and_attrs() -> None:
    payload = {
        "tool": "approval",
        "approval_id": "appr_test",
        "question": "审批 appr_test\n第一行\n第二行",
        "candidates": ["批准并执行", "拒绝", "稍后处理"],
        "_selection": 1,
    }
    expected_layout = rendering.interaction_hint_layout_lines(
        True,
        width=60,
        tool="approval",
        title_source="审批 appr_test",
        approval_preview_text="第一行\n第二行",
        is_approval=True,
        candidates=rendering.sanitize_interaction_candidates(payload["candidates"]),
        selected=1,
        footer=rendering.interaction_footer_text(True, has_candidates=True, is_approval=True),
    )
    attr_by_kind = {
        "header": app_module.cp(7) | app_module.curses.A_BOLD,
        "body": app_module.cp(2),
        "candidate": app_module.cp(2),
        "candidate_selected": app_module.cp(11) | app_module.curses.A_BOLD,
        "muted": app_module.cp(1),
        "footer": app_module.cp(1),
    }

    assert app_module.interaction_hint_lines(payload, 60) == [
        (text, attr_by_kind[kind]) for kind, text in expected_layout
    ]


def test_compose_request_user_input_answer_formats_questions() -> None:
    payload = {
        "questions": [
            {"header": "范围", "question": "要处理哪些文件？"},
            {"header": "确认", "question": "确认"},
            {"question": "是否提交？"},
        ]
    }

    assert rendering.compose_request_user_input_answer(payload, ["全部", "是"]) == (
        "1. 范围: 要处理哪些文件？\n"
        "答案：全部\n\n"
        "2. 确认\n"
        "答案：是\n\n"
        "3. 问题 3: 是否提交？\n"
        "答案："
    )
    assert app_module.compose_request_user_input_answer is rendering.compose_request_user_input_answer


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


def test_subagent_result_notice_format_helpers_shape_body_notice_and_detail_lines() -> None:
    notice = {
        "name": "研究员",
        "agent_id": "agent-research",
        "task_id": "task_123",
        "artifact_ref": "artifact://subagent-results/report.md",
        "body": "",
    }

    assert rendering.subagent_result_notice_body_text(
        "raw result",
        "rendered result",
        "",
        False,
        6000,
    ) == "rendered result"
    assert rendering.subagent_result_notice_body_text(
        "raw result",
        "rendered result too long",
        "final visible answer",
        True,
        5,
    ) == "▸ 工具/过程输出已折叠，完整过程见 artifact。\n\nfinal visible answer"
    assert rendering.subagent_result_notice_body_text(
        "raw result is too long",
        "",
        "",
        False,
        10,
    ) == "raw result\n...（结果过长，完整内容见 artifact）"
    assert rendering.format_subagent_result_notice_text(
        "研究员",
        "agent-research",
        "task_123",
        "artifact://subagent-results/report.md",
        "body text",
    ) == (
        "子 agent 回复 · 研究员 (agent-research)\n"
        "Task: task_123\n"
        "Artifact: artifact://subagent-results/report.md\n\n"
        "body text"
    )
    assert rendering.subagent_result_metadata_detail_lines(notice, ["Confidence: 高"], 80) == [
        "│   Task: task_123",
        "│   Artifact: artifact://subagent-results/report.md",
        "│   Confidence: 高",
    ]


def test_app_subagent_result_notice_format_wrappers_delegate_to_rendering_helpers() -> None:
    notice = {
        "name": "研究员",
        "agent_id": "agent-research",
        "task_id": "task_123",
        "artifact_ref": "artifact://subagent-results/report.md",
        "body": "",
    }
    metadata_lines = ["Confidence: 高"]
    blocks = app_module.subagent_result_metadata_detail_blocks(notice, metadata_lines, 80)

    assert [line.text for line in blocks] == rendering.subagent_result_metadata_detail_lines(
        notice,
        metadata_lines,
        80,
    )
    assert [line.attr for line in blocks] == [app_module.cp(9), app_module.cp(9), app_module.cp(9)]

    raw = app_module.clean_text("plain subagent result").strip() or "(empty result)"
    rendered = app_module.render_assistant_text(raw, True, True).strip()
    final_reply = "" if rendered and len(rendered) <= 6000 else app_module.latest_visible_reply_text(raw)
    has_tool_noise = app_module.process_has_tool_noise(raw) if final_reply else False
    assert app_module.subagent_result_notice_body("plain subagent result", 6000) == (
        rendering.subagent_result_notice_body_text(raw, rendered, final_reply, has_tool_noise, 6000)
    )

    body = app_module.subagent_result_notice_body("plain subagent result", 6000)
    assert app_module.format_subagent_result_notice_parts(
        "研究员",
        "agent-research",
        "task_123",
        "artifact://subagent-results/report.md",
        "plain subagent result",
    ) == rendering.format_subagent_result_notice_text(
        "研究员",
        "agent-research",
        "task_123",
        "artifact://subagent-results/report.md",
        body,
    )


def test_subagent_result_context_update_helpers_shape_excerpt_confidence_and_budget() -> None:
    rendered = (
        "可见回复正文\n"
        "\n"
        "---\n"
        "Findings:\n"
        "1. 发现一\n"
        "Confidence: **高**\n"
    )
    excerpt, metadata_lines = rendering.subagent_result_reply_excerpt_text(rendered, 80)

    assert excerpt == "可见回复正文"
    assert metadata_lines == ["Findings:", "1. 发现一", "Confidence: **高**"]
    assert rendering.subagent_result_reply_excerpt_text("abcdef", 3) == (
        "abc\n...（回复过长，完整内容见 artifact）",
        [],
    )
    assert rendering.subagent_result_reply_excerpt_text("", 80) == ("(empty result)", [])
    assert rendering.subagent_result_context_confidence(metadata_lines) == "高"
    assert rendering.subagent_result_context_confidence(["Risks: 无"]) == ""

    update = rendering.format_subagent_result_context_update_text(
        name="研究员",
        agent_id="agent-research",
        bus_task_id="task_123",
        artifact_ref="artifact://subagent-results/report.md",
        reply=excerpt,
        session_key_value="model_responses_1.txt",
        parent_task_id="task_parent",
        plan_id="plan_root",
        role="researcher",
        confidence="高",
    )
    assert update == (
        "Subagent result available in current session context:\n"
        "- session_key: model_responses_1.txt\n"
        "- subagent: 研究员 (agent-research)\n"
        "- task_id: task_123\n"
        "- status: completed\n"
        "- role: researcher\n"
        "- parent_task_id: task_parent\n"
        "- plan_id: plan_root\n"
        "- artifact_ref: artifact://subagent-results/report.md\n"
        "- confidence: 高\n"
        "- instruction: Use this scoped current-session result directly for follow-up status questions; do not search historical session logs unless the user asks for archives.\n"
        "\n"
        "Reply excerpt:\n"
        "可见回复正文"
    )
    assert rendering.bounded_subagent_context_updates(
        ["old", "duplicate", "middle", "duplicate", "new"],
        3,
        100,
    ) == "duplicate\n\nmiddle\n\nnew"
    assert rendering.bounded_subagent_context_updates(
        ["first", "second-long", "third"],
        3,
        len("third") + 2 + 1,
    ) == "third"


def test_app_subagent_result_context_update_wrappers_delegate_to_rendering_helpers() -> None:
    body = "可见回复正文\n\n---\nConfidence: **高**"
    rendered = app_module.render_subagent_result_body(body, fold_process=True)
    reply, metadata_lines = rendering.subagent_result_reply_excerpt_text(
        rendered,
        app_module.SUBAGENT_CONTEXT_REPLY_LIMIT,
    )

    assert app_module.subagent_result_reply_excerpt(body) == (reply, metadata_lines)
    assert app_module.format_subagent_result_context_update(
        "研究员",
        "agent-research",
        "task_123",
        "artifact://subagent-results/report.md",
        body,
        session_key_value="model_responses_1.txt",
        parent_task_id="task_parent",
        plan_id="plan_root",
        role="researcher",
    ) == rendering.format_subagent_result_context_update_text(
        name="研究员",
        agent_id="agent-research",
        bus_task_id="task_123",
        artifact_ref="artifact://subagent-results/report.md",
        reply=reply,
        session_key_value="model_responses_1.txt",
        parent_task_id="task_parent",
        plan_id="plan_root",
        role="researcher",
        confidence=rendering.subagent_result_context_confidence(metadata_lines),
    )

    notice = app_module.format_subagent_result_notice_parts(
        "研究员",
        "agent-research",
        "task_123",
        "artifact://subagent-results/report.md",
        body,
    )
    assert "Subagent result available in current session context" in app_module.subagent_result_context_update_from_notice(
        notice,
        session_key_value="model_responses_1.txt",
    )

    messages = [
        app_module.Message("system", notice),
        app_module.Message("assistant", "ignored"),
        app_module.Message("system", notice),
    ]
    updates = [
        app_module.subagent_result_context_update_from_notice(notice, session_key_value="model_responses_1.txt"),
        app_module.subagent_result_context_update_from_notice(notice, session_key_value="model_responses_1.txt"),
    ]
    assert app_module.subagent_context_updates_from_messages(messages, "/tmp/model_responses_1.txt") == (
        rendering.bounded_subagent_context_updates(
            updates,
            app_module.SUBAGENT_CONTEXT_UPDATE_LIMIT,
            app_module.SUBAGENT_CONTEXT_TOTAL_LIMIT,
        )
    )


def test_subagent_result_card_layout_lines_shape_card_chrome_and_metadata_state() -> None:
    notice = rendering.parse_subagent_result_notice(
        "子 agent 回复 · 研究员 (agent-research)\n"
        "Task: task_123\n"
        "Artifact: artifact://subagent-results/report.md\n"
        "\n"
        "可见回复\n"
        "\n"
        "---\n"
        "Findings:\n"
        "1. 第一项\n"
        "2. 第二项\n"
        "Confidence: 高\n"
    )
    assert notice is not None
    reply_body, metadata_lines = rendering.split_subagent_result_reply_and_metadata(notice["body"])
    assert reply_body == "可见回复"
    meta_label = rendering.subagent_meta_label(notice)

    assert rendering.subagent_result_card_layout_lines(notice, metadata_lines, set(), 120) == [
        ("title", "╭─ 子 agent 回复 · 研究员 (agent-research)"),
        (
            "metadata_summary",
            f"│ ▸ 元信息 {meta_label} (已折叠，点击) · Confidence: 高 · Findings: 2 · Task · Artifact",
        ),
        ("reply_header", "├─ 回复"),
        ("footer", "╰─"),
    ]
    assert rendering.subagent_result_card_layout_lines(notice, metadata_lines, {meta_label}, 120) == [
        ("title", "╭─ 子 agent 回复 · 研究员 (agent-research)"),
        (
            "metadata_summary",
            f"│ ▾ 元信息 {meta_label} (已展开，点击) · Confidence: 高 · Findings: 2 · Task · Artifact",
        ),
        ("metadata_detail", ""),
        ("reply_header", "├─ 回复"),
        ("footer", "╰─"),
    ]


def test_subagent_result_card_layout_lines_omits_empty_metadata_region() -> None:
    notice = rendering.parse_subagent_result_notice("子 agent 回复 · Worker (agent-x)\n\nplain body")
    assert notice is not None

    assert rendering.subagent_result_card_layout_lines(notice, [], set(), 120) == [
        ("title", "╭─ 子 agent 回复 · Worker (agent-x)"),
        ("reply_header", "├─ 回复"),
        ("footer", "╰─"),
    ]


def test_app_subagent_result_card_blocks_delegate_chrome_to_rendering_layout() -> None:
    notice_text = (
        "子 agent 回复 · 研究员 (agent-research)\n"
        "Task: task_123\n"
        "Artifact: artifact://subagent-results/report.md\n"
        "\n"
        "可见回复\n"
        "\n"
        "---\n"
        "Confidence: 高\n"
    )
    notice = rendering.parse_subagent_result_notice(notice_text)
    assert notice is not None
    meta_label = rendering.subagent_meta_label(notice)

    collapsed_blocks = app_module.subagent_result_card_blocks(
        notice_text,
        124,
        markdown=False,
        fold_process=True,
        expanded_meta=set(),
    )
    collapsed_text = [line.text for line in collapsed_blocks]
    assert collapsed_text == [
        "╭─ 子 agent 回复 · 研究员 (agent-research)",
        f"│ ▸ 元信息 {meta_label} (已折叠，点击) · Confidence: 高 · Task · Artifact",
        "├─ 回复",
        "│ 可见回复",
        "╰─",
    ]
    assert collapsed_blocks[0].attr == app_module.cp(10) | app_module.curses.A_BOLD
    assert collapsed_blocks[1].attr == app_module.cp(9)
    assert collapsed_blocks[2].attr == app_module.cp(10)
    assert collapsed_blocks[3].attr == app_module.cp(2)
    assert collapsed_blocks[4].attr == app_module.cp(10)

    expanded_text = [
        line.text
        for line in app_module.subagent_result_card_blocks(
            notice_text,
            124,
            markdown=False,
            fold_process=True,
            expanded_meta={meta_label},
        )
    ]
    assert expanded_text == [
        "╭─ 子 agent 回复 · 研究员 (agent-research)",
        f"│ ▾ 元信息 {meta_label} (已展开，点击) · Confidence: 高 · Task · Artifact",
        "│   Task: task_123",
        "│   Artifact: artifact://subagent-results/report.md",
        "│   Confidence: 高",
        "├─ 回复",
        "│ 可见回复",
        "╰─",
    ]


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
        "subagent_result_metadata_detail_lines",
        "subagent_result_notice_body_text",
        "format_subagent_result_notice_text",
        "subagent_result_reply_excerpt_text",
        "subagent_result_context_confidence",
        "format_subagent_result_context_update_text",
        "bounded_subagent_context_updates",
        "subagent_result_card_layout_lines",
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


def test_process_scope_key_helpers_preserve_legacy_key_shapes() -> None:
    assert rendering.process_group_scope_key("session:main", "G2") == "session:main:G2"
    assert rendering.process_turn_scope_key("session:main", "G2T7") == "session:main:G2:G2T7"
    assert rendering.process_turn_scope_key("session:main", "Turn7") == "session:main::Turn7"
    assert rendering.subagent_meta_scope_key("session:main", "S1234abcd") == "session:main:submeta:S1234abcd"


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


def test_process_title_text_from_parts_preserves_title_priority() -> None:
    assert rendering.process_title_text_from_parts("整理完成", True, "预览") == "整理完成"
    assert rendering.process_title_text_from_parts("", True, "预览") == "搜索/浏览输出已折叠"
    assert rendering.process_title_text_from_parts("", False, "预览") == "预览"

    summary_body = "<summary>整理完成</summary>\n🛠️ Tool: `web.search`"
    search_body = "🛠️ Tool: `web.search`\n📥 args: {}\nraw visible line"
    preview_body = "raw visible line"
    assert app_module.process_title_text(summary_body) == rendering.process_title_text_from_parts(
        app_module.process_summary_text(summary_body),
        app_module.process_has_search_noise(summary_body),
        app_module.process_preview(summary_body),
    )
    assert app_module.process_title_text(search_body) == "搜索/浏览输出已折叠"
    assert app_module.process_title_text(preview_body) == "raw visible line"


def test_process_display_summary_text_prefers_summary_and_suppresses_running() -> None:
    assert rendering.process_display_summary_text("整理完成", "预览") == "整理完成"
    assert rendering.process_display_summary_text("", "预览") == "预览"
    assert rendering.process_display_summary_text("执行中", "预览") == ""
    assert rendering.process_display_summary_text("", "执行中") == ""
    assert rendering.process_display_summary_text("", "") == ""


def test_render_assistant_text_uses_display_summary_policy_for_no_final_text() -> None:
    rendered = app_module.render_assistant_text(
        "LLM Running (Turn 1) ...\n<summary>整理完成</summary>\n",
        done=True,
        fold_process=True,
    )
    running = app_module.render_assistant_text(
        "LLM Running (Turn 1) ...\n<summary>执行中</summary>\n",
        done=False,
        fold_process=True,
    )

    assert rendered == "· 过程 Turn 1: 整理完成"
    assert "· 过程 Turn 1: 执行中" not in running
    assert running == "▸ 过程 Turn 1: 执行中 (正在执行)"


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
    assert rendering.process_summary_append_lines("整理结果", "summary row") == ["summary row"]
    assert rendering.process_summary_append_lines("", "summary row") == []
    assert rendering.process_summary_append_lines("执行中", "summary row") == []
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


def test_process_group_header_parts_dedupes_summaries_and_caps_tools() -> None:
    assert rendering.process_group_header_parts(
        ["整理结果", "整理结果", "", "复核输出"],
        [["web.search", "irc"], ["irc", "todo", "code"], ["ignored"]],
        4,
    ) == ("整理结果 / 复核输出", ["web.search", "irc", "todo"])
    assert rendering.process_group_header_parts(["", ""], [[], ["web.search"]], 2) == ("2 条过程", ["web.search"])


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
    display_summary = app_module.process_display_summary_text(summary, "")
    fallback_summary = app_module.process_display_summary_text(title_summary, "")
    assert rendered == rendering.process_turn_lines(
        final_text,
        has_process_noise=has_process_noise,
        has_call_noise=has_call_noise,
        fold_details=True,
        collapse_whole=False,
        collapsed_line=app_module.collapsed_process_line(marker, body, current=True),
        speech_header_line=app_module.process_speech_header(marker, body),
        summary_line=app_module.process_speech_summary_line(marker, body, display_summary) if display_summary else "",
        detail_line=app_module.process_detail_line(marker, body, current=True),
        fallback_summary_line=app_module.process_speech_summary_line(marker, body, fallback_summary)
        if fallback_summary
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
    assert app_module.process_display_summary_text("整理结果", "fallback") == rendering.process_display_summary_text(
        "整理结果",
        "fallback",
    )
    rendered_summary: list[str] = []
    assert app_module.append_process_summary_line(rendered_summary, marker, body)
    assert rendered_summary == rendering.process_summary_append_lines(
        app_module.process_summary_text(body),
        app_module.process_speech_summary_line(marker, body, app_module.process_summary_text(body)),
    )
    pending_summary: list[str] = []
    assert not app_module.append_process_summary_line(pending_summary, marker, "<summary>执行中</summary>")
    assert pending_summary == []
    assert app_module.expanded_process_header(marker, body, True) == rendering.expanded_process_header_text(
        marker,
        app_module.process_summary_text(body),
        tools,
        True,
    )
    group_turns = [
        (marker, body),
        (
            "**LLM Running (Turn 8) ...**",
            "<summary>复核输出</summary>\n<tool_use>{\"name\":\"todo\"}</tool_use>\n",
        ),
    ]
    title, group_tools = rendering.process_group_header_parts(
        [app_module.process_summary_text(turn_body) for _turn_marker, turn_body in group_turns],
        [app_module.process_tools(turn_body) for _turn_marker, turn_body in group_turns],
        len(group_turns),
    )
    assert app_module.process_group_header("G2", group_turns, False, True) == rendering.process_group_header_text(
        "G2",
        title,
        group_tools,
        False,
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
        "<shuheng-control>{\"action\":\"agent.create\",\"params\":{\"name\":\"Hidden\"}}</shuheng-control>\n"
        "<summary>hidden summary</summary>"
    )

    detail = app_module.process_child_detail(body)

    assert detail == rendering.process_child_detail_text(
        app_module.strip_tui_controls(body),
        app_module.process_preview(body),
    )
    assert "shuheng-control" not in detail
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


def test_app_process_scope_key_wrappers_inject_display_scope() -> None:
    state = app_module.State(agent=None)
    scope = app_module.display_scope_key(state)

    assert app_module.process_group_key(state, "G2") == rendering.process_group_scope_key(scope, "G2")
    assert app_module.process_turn_key(state, "G2T7") == rendering.process_turn_scope_key(scope, "G2T7")
    assert app_module.process_turn_key(state, "Turn7") == rendering.process_turn_scope_key(scope, "Turn7")
    assert app_module.subagent_meta_key(state, "S1234abcd") == rendering.subagent_meta_scope_key(
        scope,
        "S1234abcd",
    )


def test_app_rendering_wrappers_match_module() -> None:
    assert app_module.RUN_FRAMES is rendering.RUN_FRAMES
    assert app_module.char_index_for_cell is rendering.char_index_for_cell
    assert app_module.scoped_subagent_meta_keys is rendering.scoped_subagent_meta_keys
    assert app_module.process_group_scope_key is rendering.process_group_scope_key
    assert app_module.process_turn_scope_key is rendering.process_turn_scope_key
    assert app_module.subagent_meta_scope_key is rendering.subagent_meta_scope_key
    assert app_module.message_cache_signature is rendering.message_cache_signature
    assert app_module.message_render_cache_key is rendering.message_render_cache_key
    assert app_module.strip_meta_blocks is rendering.strip_meta_blocks
    assert app_module.process_preview is rendering.process_preview
    assert app_module.process_summary_text is rendering.process_summary_text
    assert app_module.process_title_text_from_parts is rendering.process_title_text_from_parts
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
    assert app_module.sanitize_interaction_candidates is rendering.sanitize_interaction_candidates
    assert app_module.render_interaction_card is rendering.render_interaction_card
    assert app_module.visible_ask_user_card_text is rendering.visible_ask_user_card_text
    assert app_module.interaction_answer_from_text is rendering.interaction_answer_from_text
    assert app_module.compose_request_user_input_answer is rendering.compose_request_user_input_answer
    assert app_module.interaction_input_prompt_text is rendering.interaction_input_prompt_text
    assert app_module.interaction_footer_text is rendering.interaction_footer_text
    assert app_module.interaction_hint_layout_lines is rendering.interaction_hint_layout_lines
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
    assert app_module.process_display_summary_text is rendering.process_display_summary_text
    assert app_module.process_summary_append_lines is rendering.process_summary_append_lines
    assert app_module.expanded_process_header_text is rendering.expanded_process_header_text
    assert app_module.process_group_header_parts is rendering.process_group_header_parts
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
