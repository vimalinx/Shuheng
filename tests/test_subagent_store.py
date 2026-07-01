from __future__ import annotations

import re
from pathlib import Path

import pytest

import ga_tui.app as app_module
from ga_tui import subagent_store


def test_home_session_keys_and_app_aliases() -> None:
    key = subagent_store.subagent_home_session_key("research agent/中文")

    assert key == "__home__:sub:research-agent"
    assert subagent_store.home_subagent_id_from_key(key) == "research-agent"
    assert subagent_store.home_subagent_id_from_key("history") == ""
    assert subagent_store.is_main_home_session_key("__home__:main")
    assert subagent_store.is_scheduled_reports_session_key("__home__:scheduled_reports")
    assert subagent_store.is_home_session_key(key)
    assert app_module.subagent_home_session_key is subagent_store.subagent_home_session_key
    assert app_module.home_subagent_id_from_key is subagent_store.home_subagent_id_from_key
    assert app_module.is_home_session_key is subagent_store.is_home_session_key


def test_parameterized_paths_and_app_wrappers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "subagents"
    monkeypatch.setattr(app_module, "SUBAGENTS_DIR", str(root))

    assert subagent_store.subagent_home("agent/raw", subagents_dir=str(root)) == str(root / "agent/raw")
    assert app_module.subagent_home("agent/raw") == str(root / "agent/raw")
    assert app_module.subagent_meta_path("agent/raw") == str(root / "agent/raw" / "meta.json")
    assert app_module.subagent_profile_path("agent/raw") == str(root / "agent/raw" / "profile.md")
    assert app_module.subagent_memory_path("agent/raw") == str(root / "agent/raw" / "memory.md")
    assert app_module.subagent_events_path("agent/raw") == str(root / "agent/raw" / "events.jsonl")


def test_secret_home_and_sidebar_key_round_trip() -> None:
    assert app_module.SUBAGENT_SESSION_PREFIX == subagent_store.SUBAGENT_SESSION_PREFIX
    assert subagent_store.secret_subagent_home("agent/中文") == "secret://subagents/agent"

    key = subagent_store.subagent_session_sidebar_key("agent one/中文", "chat id/1")

    assert key == "subagent_session:agent-one:chat-id-1"
    assert subagent_store.subagent_session_from_sidebar_key(key) == ("agent-one", "chat-id-1")
    assert subagent_store.subagent_session_from_sidebar_key("subagent_session:broken") == ("", "")
    assert subagent_store.subagent_session_from_sidebar_key("history") == ("", "")
    assert app_module.subagent_session_sidebar_key is subagent_store.subagent_session_sidebar_key
    assert app_module.subagent_session_from_sidebar_key is subagent_store.subagent_session_from_sidebar_key
    assert app_module.secret_subagent_home is subagent_store.secret_subagent_home


def test_subagent_identity_helpers_and_app_wrappers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "subagents"
    (root / "researcher").mkdir(parents=True)
    state = app_module.State(agent=None)
    state.subagents = {
        "researcher": app_module.SubAgentRuntime(agent_id="researcher", name="Researcher", home="/tmp/researcher"),
        "tmp-researcher-234567890123": app_module.SubAgentRuntime(
            agent_id="tmp-researcher-234567890123",
            name="Researcher",
            home="/tmp/researcher",
        ),
    }
    monkeypatch.setattr(app_module, "SUBAGENTS_DIR", str(root))
    monkeypatch.setattr(subagent_store.time, "time_ns", lambda: 1_234_567_890_123)

    assert app_module.clean_subagent_id is subagent_store.clean_subagent_id
    assert app_module.normalize_subagent_identity_text is subagent_store.normalize_subagent_identity_text
    assert app_module.compact_identity_text is subagent_store.compact_identity_text
    assert subagent_store.clean_subagent_id("Ａgent / 研究") == "agent"
    assert subagent_store.normalize_subagent_identity_text("Agent：Code-Reviewer!") == "agent code reviewer"
    assert subagent_store.compact_identity_text("Agent：Code-Reviewer!") == "agentcodereviewer"
    assert subagent_store.unique_subagent_id("Researcher", subagents_dir=str(root)) == "researcher-2"
    assert app_module.unique_subagent_id("Researcher") == "researcher-2"
    assert subagent_store.unique_secret_subagent_id("Researcher", existing_ids=state.subagents) == "researcher-2"
    assert app_module.unique_secret_subagent_id(state, "Researcher") == "researcher-2"
    assert subagent_store.unique_runtime_subagent_id("Researcher", existing_ids=state.subagents) == "tmp-researcher-234567890123-2"
    assert app_module.unique_runtime_subagent_id(state, "Researcher") == "tmp-researcher-234567890123-2"


def test_subagent_new_chat_session_id_shape() -> None:
    session_id = subagent_store.subagent_new_chat_session_id()

    assert re.fullmatch(r"chat_\d{8}_\d{6}_\d{9}", session_id)
    assert app_module.subagent_new_chat_session_id is subagent_store.subagent_new_chat_session_id


def test_subagent_chat_history_meta_matches_and_app_wrapper() -> None:
    meta = {
        "conversation_scope": subagent_store.SUBAGENT_CHAT_HISTORY_SCOPE,
        "agent_id": "researcher",
        "subagent_chat_session_id": "chat_20260701_120000_000000001",
    }
    sub = app_module.SubAgentRuntime(agent_id="researcher", name="Researcher", home="/tmp/researcher")

    assert app_module.SUBAGENT_CHAT_HISTORY_SCOPE == subagent_store.SUBAGENT_CHAT_HISTORY_SCOPE
    assert app_module.SUBAGENT_CHAT_MESSAGES_META_KEY == subagent_store.SUBAGENT_CHAT_MESSAGES_META_KEY
    assert subagent_store.subagent_chat_history_meta_matches(meta, "researcher")
    assert subagent_store.subagent_chat_history_meta_matches(meta, "researcher", session_id="chat_20260701_120000_000000001")
    assert not subagent_store.subagent_chat_history_meta_matches(meta, "researcher", session_id="other")
    assert not subagent_store.subagent_chat_history_meta_matches(meta, "other")
    assert not subagent_store.subagent_chat_history_meta_matches({**meta, "conversation_scope": "other"}, "researcher")
    assert app_module.subagent_chat_history_meta_matches(meta, sub)
    assert app_module.subagent_chat_history_meta_matches(meta, sub, "chat_20260701_120000_000000001")


def test_normalize_loaded_subagent_chat_messages_closes_interrupted_assistant() -> None:
    messages = [
        app_module.Message("user", "继续"),
        app_module.Message("assistant", "partial  \n", done=False),
    ]

    normalized = subagent_store.normalize_loaded_subagent_chat_messages(messages)

    assert normalized is messages
    assert normalized[-1].done is True
    assert normalized[-1].role == "assistant"
    assert normalized[-1].content == "partial\n\n[上一轮子 agent 输出中断，已按恢复记录收尾。]"
    assert app_module.normalize_loaded_subagent_chat_messages is subagent_store.normalize_loaded_subagent_chat_messages


def test_subagent_chat_history_preview_messages_filters_and_limits() -> None:
    messages = [
        app_module.Message("user", "old"),
        app_module.Message("tool", "ignored"),
        app_module.Message("user", " \x1b[31mnew user "),
        app_module.Message("assistant", "  "),
        app_module.Message("system", "notice"),
        app_module.Message("assistant", "new reply"),
    ]

    records = subagent_store.subagent_chat_history_preview_messages(messages, limit=4)

    assert records == [
        {"role": "user", "content": "new user"},
        {"role": "system", "content": "notice"},
        {"role": "assistant", "content": "new reply"},
    ]
    assert app_module.subagent_chat_history_preview_messages is subagent_store.subagent_chat_history_preview_messages


def test_subagent_chat_title_preview_and_description_helpers() -> None:
    messages = [
        app_module.Message("user", "first task"),
        app_module.Message("assistant", "<summary>有效子会话标题</summary>\nvisible"),
        app_module.Message("user", "latest task"),
        app_module.Message("assistant", "**LLM Running (Turn 1) ...**\n<summary>OMP 思考</summary>\n最终回复"),
    ]
    sub = app_module.SubAgentRuntime(agent_id="researcher", name="Researcher", home="/tmp/researcher")

    assert subagent_store.subagent_chat_title_for_messages(messages, "", "Researcher") == "有效子会话标题"
    assert app_module.subagent_chat_title_for_messages(sub, messages) == "有效子会话标题"
    assert subagent_store.subagent_chat_history_preview(messages, "", "Researcher") == "有效子会话标题"
    assert app_module.subagent_chat_history_preview(messages, sub) == "有效子会话标题"

    description = subagent_store.subagent_chat_history_description(
        messages,
        "fallback preview",
        latest_visible_reply_text=lambda text: app_module.latest_visible_reply_text(text),
    )

    assert description == "开始：first task；最近：latest task；摘要：最终回复"
    assert app_module.subagent_chat_history_description(messages, "fallback preview") == description


def test_subagent_chat_title_helpers_ignore_process_only_summary_and_fallback() -> None:
    process_messages = [
        app_module.Message("user", "修复子 agent 会话标题"),
        app_module.Message("assistant", "**LLM Running (Turn 1) ...**\n<summary>OMP 思考</summary>"),
    ]
    empty_messages: list[app_module.Message] = []
    sub = app_module.SubAgentRuntime(agent_id="ops", name="Ops Agent", home="/tmp/ops", chat_title="既有标题")

    assert subagent_store.subagent_chat_title_for_messages(process_messages, "", "Ops Agent") == "修复子 agent 会话标题"
    assert app_module.subagent_chat_title_for_messages(sub, process_messages) == "修复子 agent 会话标题"
    assert subagent_store.subagent_chat_history_preview(process_messages, "", "Ops Agent") == "修复子 agent 会话标题"
    assert subagent_store.subagent_chat_title_for_messages(empty_messages, "既有标题", "Ops Agent") == "既有标题"
    assert subagent_store.subagent_chat_history_preview(empty_messages, "", "Ops Agent") == "Ops Agent 会话"
    assert app_module.subagent_chat_history_preview(empty_messages, sub) == "既有标题"


def test_subagent_chat_history_rounds_and_last_user_at() -> None:
    messages = [
        app_module.Message("user", "first"),
        app_module.Message("assistant", "reply"),
        app_module.Message("user", " "),
        app_module.Message("user", "latest"),
    ]

    assert subagent_store.subagent_chat_history_rounds(messages) == 2
    assert subagent_store.subagent_chat_history_last_user_at(messages, 123.5) == 123.5
    assert subagent_store.subagent_chat_history_last_user_at([], 42.0) == 42.0
    assert app_module.subagent_chat_history_rounds is subagent_store.subagent_chat_history_rounds
    assert app_module.subagent_chat_history_last_user_at is subagent_store.subagent_chat_history_last_user_at


def test_subagent_store_does_not_own_transcripts() -> None:
    assert not hasattr(subagent_store, "write_subagent_chat_history_transcript")
    assert not hasattr(subagent_store, "save_subagent_chat_messages_to_history")
