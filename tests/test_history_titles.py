"""Tests for process-summary-safe history title policy helpers."""
from __future__ import annotations

from shuheng import app as app_module
from shuheng import history_titles
from shuheng.ui_types import Message


def _prompt(text: str) -> str:
    return '{"content":[{"type":"text","text":"' + text + '"}]}'


def test_process_marked_summary_is_not_title_candidate() -> None:
    text = (
        "**LLM Running (Turn 1) ...**\n\n"
        "<summary>OMP 思考</summary>\n"
        "<thinking>Hidden OMP reasoning</thinking>\n"
        "已完成历史会话标题修复"
    )

    assert history_titles.session_summary_titles_from_text(text) == []
    assert app_module.session_summary_titles_from_text(text) == []


def test_session_titles_are_clamped_to_16_chars() -> None:
    long_title = "修复左侧历史会话自动标题更新性能优化"

    assert history_titles.clamp_session_title_chars(long_title) == "修复左侧历史会话自动标题更新性能"
    assert len(history_titles.short_session_title(long_title)) <= 16
    assert len(app_module.short_session_title(long_title)) <= app_module.SESSION_TITLE_CHARS
    assert len(app_module.normalize_session_title("标题： " + long_title)) <= app_module.SESSION_TITLE_CHARS
    assert app_module.clean_ai_session_title("标题： " + long_title) == "修复左侧历史会话自动标题更新性能"


def test_normal_summary_can_title_preview() -> None:
    text = "最终响应\n<summary>整理历史标题策略</summary>"
    body = repr([{"type": "text", "text": text}])

    assert history_titles.session_summary_titles_from_text(text) == ["整理历史标题策略"]
    assert history_titles.session_response_preview_text(
        body,
        latest_visible_reply_text=lambda value: value,
    ) == "整理历史标题策略"
    assert app_module.session_response_preview_text(body) == "整理历史标题策略"


def test_response_preview_uses_visible_text_for_process_marked_response() -> None:
    body = repr([{
        "type": "text",
        "text": (
            "**LLM Running (Turn 1) ...**\n\n"
            "<summary>OMP 思考</summary>\n"
            "<thinking>Hidden OMP reasoning</thinking>\n\n"
            "最终可见答复"
        ),
    }])

    assert history_titles.session_response_preview_text(
        body,
        latest_visible_reply_text=lambda _text: "最终可见答复",
    ) == "最终可见答复"
    assert app_module.session_response_preview_text(body) == "最终可见答复"


def test_session_preview_and_description_from_pairs() -> None:
    pairs = [
        (_prompt("第一个用户问题"), "plain"),
        (_prompt("最近用户问题"), repr([{"type": "text", "text": "<summary>有效摘要</summary>"}])),
    ]

    preview = history_titles.session_preview_from_pairs(
        pairs,
        user_text_from_prompt=app_module._user_text,
        response_preview_text=lambda response, limit: history_titles.session_response_preview_text(
            response,
            limit,
            latest_visible_reply_text=lambda value: value,
        ),
    )
    description = history_titles.session_description_from_pairs(
        pairs,
        preview,
        user_text_from_prompt=app_module._user_text,
        response_preview_text=lambda response, limit: history_titles.session_response_preview_text(
            response,
            limit,
            latest_visible_reply_text=lambda value: value,
        ),
    )

    assert preview == "有效摘要"
    assert description == "开始：第一个用户问题；最近：最近用户问题；摘要：有效摘要"
    assert app_module.session_preview_from_pairs(pairs) == "有效摘要"
    assert app_module.session_description_from_pairs(pairs, preview) == description


def test_history_cache_detects_process_only_preview_markers() -> None:
    meta = {
        "preview": "正常预览",
        "description": "开始：修复左栏历史会话标题；摘要：OMP 思考",
        "ui_preview_messages": [{"role": "assistant", "content": "（预览）执行中"}],
    }

    assert history_titles.history_cache_has_process_only_preview(meta)
    assert app_module.history_cache_has_process_only_preview(meta)
    assert history_titles.is_process_only_session_title("调用工具: browser.open")
    assert app_module.is_process_only_session_title("（预览）OMP 思考")


def test_message_text_for_metadata_context_strips_process_and_control_text() -> None:
    user = Message(
        "user",
        "公开问题 <shuheng-control>{\"action\":\"x\"}</shuheng-control> "
        "<thinking>Hidden</thinking> <tool_use>{\"name\":\"x\"}</tool_use>",
    )
    assistant = Message("assistant", "<thinking>Hidden</thinking>\n最终回答")

    user_text = history_titles.message_text_for_metadata_context(
        user,
        latest_visible_reply_text=lambda text: text,
    )
    assistant_text = history_titles.message_text_for_metadata_context(
        assistant,
        latest_visible_reply_text=lambda _text: "最终回答",
    )

    assert user_text == "公开问题"
    assert assistant_text == "最终回答"
    assert app_module.message_text_for_metadata_context(user) == "公开问题"


def test_suggested_title_prefers_non_process_summary_then_user_fallback() -> None:
    summary_messages = [
        Message("user", "用户问题"),
        Message("assistant", "<summary>有效会话标题</summary>"),
    ]
    process_messages = [
        Message("user", "修复左栏历史会话标题"),
        Message("assistant", "**LLM Running (Turn 1) ...**\n<summary>OMP 思考</summary>"),
    ]

    assert history_titles.suggested_session_title(summary_messages) == "有效会话标题"
    assert app_module.suggested_session_title(summary_messages) == "有效会话标题"
    assert history_titles.suggested_session_title(process_messages) == "修复左栏历史会话标题"
    assert app_module.suggested_session_title(process_messages) == "修复左栏历史会话标题"
