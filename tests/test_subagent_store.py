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


def test_subagent_store_does_not_own_transcripts() -> None:
    assert not hasattr(subagent_store, "write_subagent_chat_history_transcript")
    assert not hasattr(subagent_store, "save_subagent_chat_messages_to_history")
