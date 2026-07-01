"""Pure subagent identity, home-path, and sidebar-key helpers."""
from __future__ import annotations

import os
import re
import time
from typing import Any, Callable

from .history_titles import compact_description, suggested_session_title
from .text_utils import clean_text, compact_title
from .ui_types import MAIN_HOME_SESSION_KEY, SCHEDULED_REPORTS_SESSION_KEY, SUBAGENT_HOME_SESSION_PREFIX, Message

SUBAGENT_SESSION_PREFIX = "subagent_session:"
SUBAGENT_CHAT_HISTORY_SCOPE = "subagent_chat"
SUBAGENT_CHAT_MESSAGES_META_KEY = "subagent_chat_messages"
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def safe_subagent_ref(value: str, fallback: str = "agent") -> str:
    return _SAFE_ID_RE.sub("-", value or fallback).strip("-") or fallback


def subagent_home_session_key(agent_id: str) -> str:
    return f"{SUBAGENT_HOME_SESSION_PREFIX}{safe_subagent_ref(agent_id)}"


def home_subagent_id_from_key(key: Any) -> str:
    text = str(key or "")
    if not text.startswith(SUBAGENT_HOME_SESSION_PREFIX):
        return ""
    return text[len(SUBAGENT_HOME_SESSION_PREFIX):]


def is_main_home_session_key(key: Any) -> bool:
    return str(key or "") == MAIN_HOME_SESSION_KEY


def is_scheduled_reports_session_key(key: Any) -> bool:
    return str(key or "") == SCHEDULED_REPORTS_SESSION_KEY


def is_home_session_key(key: Any) -> bool:
    text = str(key or "")
    return text in {MAIN_HOME_SESSION_KEY, SCHEDULED_REPORTS_SESSION_KEY} or text.startswith(SUBAGENT_HOME_SESSION_PREFIX)


def subagent_home(agent_id: str, *, subagents_dir: str) -> str:
    return os.path.join(subagents_dir, agent_id)


def secret_subagent_home(agent_id: str) -> str:
    return f"secret://subagents/{safe_subagent_ref(agent_id)}"


def subagent_meta_path(agent_id: str, *, subagents_dir: str) -> str:
    return os.path.join(subagent_home(agent_id, subagents_dir=subagents_dir), "meta.json")


def subagent_profile_path(agent_id: str, *, subagents_dir: str) -> str:
    return os.path.join(subagent_home(agent_id, subagents_dir=subagents_dir), "profile.md")


def subagent_memory_path(agent_id: str, *, subagents_dir: str) -> str:
    return os.path.join(subagent_home(agent_id, subagents_dir=subagents_dir), "memory.md")


def subagent_events_path(agent_id: str, *, subagents_dir: str) -> str:
    return os.path.join(subagent_home(agent_id, subagents_dir=subagents_dir), "events.jsonl")


def subagent_new_chat_session_id() -> str:
    return f"chat_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1_000_000_000:09d}"


def subagent_session_sidebar_key(agent_id: str, session_id: str) -> str:
    return f"{SUBAGENT_SESSION_PREFIX}{safe_subagent_ref(agent_id)}:{safe_subagent_ref(session_id, 'current')}"


def subagent_session_from_sidebar_key(key: Any) -> tuple[str, str]:
    text = str(key or "")
    if not text.startswith(SUBAGENT_SESSION_PREFIX):
        return "", ""
    body = text[len(SUBAGENT_SESSION_PREFIX):]
    agent_id, sep, session_id = body.partition(":")
    return agent_id if sep else "", session_id if sep else ""


def subagent_chat_history_meta_matches(meta: dict[str, Any], agent_id: str, session_id: str = "") -> bool:
    if str(meta.get("conversation_scope") or "") != SUBAGENT_CHAT_HISTORY_SCOPE:
        return False
    if str(meta.get("agent_id") or "") != str(agent_id or ""):
        return False
    if session_id and str(meta.get("subagent_chat_session_id") or "") != session_id:
        return False
    return True


def normalize_loaded_subagent_chat_messages(messages: list[Message]) -> list[Message]:
    if not messages:
        return messages
    last = messages[-1]
    if last.role == "assistant" and not last.done:
        content = (last.content or "").rstrip()
        suffix = "[上一轮子 agent 输出中断，已按恢复记录收尾。]"
        if content:
            content = f"{content}\n\n{suffix}"
        else:
            content = suffix
        messages[-1] = Message("assistant", content, done=True)
    return messages


def subagent_chat_history_preview_messages(messages: list[Message], limit: int = 20) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for msg in messages[-limit:]:
        role = str(msg.role or "")
        if role not in {"user", "assistant", "system"}:
            continue
        content = clean_text(msg.content or "").strip()
        if not content:
            continue
        records.append({"role": role, "content": content})
    return records


def subagent_chat_title_for_messages(
    messages: list[Message],
    chat_title: str,
    agent_name: str,
    *,
    title_width: int = 80,
) -> str:
    return compact_title(suggested_session_title(messages) or chat_title or f"{agent_name} 会话", title_width)


def subagent_chat_history_preview(
    messages: list[Message],
    chat_title: str,
    agent_name: str,
    *,
    preview_width: int = 90,
) -> str:
    title = suggested_session_title(messages)
    if title:
        return compact_title(title, preview_width)
    for msg in messages:
        if msg.role == "user":
            preview = compact_description(msg.content or "", preview_width)
            if preview:
                return preview
    return compact_title(chat_title or f"{agent_name} 会话", preview_width)


def subagent_chat_history_description(
    messages: list[Message],
    preview: str = "",
    *,
    latest_visible_reply_text: Callable[[str], str],
    description_limit: int = 200,
) -> str:
    users = [compact_description(msg.content or "", 90) for msg in messages if msg.role == "user" and (msg.content or "").strip()]
    assistants = [
        compact_description(latest_visible_reply_text(msg.content or ""), 110)
        for msg in messages
        if msg.role == "assistant" and (msg.content or "").strip()
    ]
    snippets: list[str] = []
    if users:
        snippets.append(f"开始：{users[0]}")
        if users[-1] != users[0]:
            snippets.append(f"最近：{users[-1]}")
    if assistants:
        snippets.append(f"摘要：{assistants[-1]}")
    if not snippets and preview:
        snippets.append(preview)
    return compact_description("；".join(snippets), description_limit)


def subagent_chat_history_rounds(messages: list[Message]) -> int:
    return sum(1 for msg in messages if msg.role == "user" and str(msg.content or "").strip())


def subagent_chat_history_last_user_at(messages: list[Message], fallback: float) -> float:
    return fallback if any(msg.role == "user" and str(msg.content or "").strip() for msg in messages) else fallback
