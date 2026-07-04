"""Pure subagent identity, home-path, and sidebar-key helpers."""
from __future__ import annotations

import os
import re
import time
import unicodedata
from collections.abc import Collection
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


def clean_subagent_id(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9._-]+", "", text)
    text = text.strip("._-")
    return text[:40] or f"agent-{int(time.time())}"


def normalize_subagent_identity_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = re.sub(r"[#*_`>\[\](){}:：,，.。;；!?！？|/\\\"'“”‘’、\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact_identity_text(text: str) -> str:
    return re.sub(r"\s+", "", normalize_subagent_identity_text(text))


def subagent_control_alias_keys(*values: Any) -> list[str]:
    keys: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in {"current", "now", "selected"}:
            continue
        for key in (text, text.lower(), compact_identity_text(text)):
            if key and key not in keys:
                keys.append(key)
    return keys


def resolve_subagent_control_alias(alias_map: dict[str, str], target: str) -> str:
    for key in subagent_control_alias_keys(target):
        if key in alias_map:
            return alias_map[key]
    return target


def unique_subagent_id(name: str, *, subagents_dir: str) -> str:
    base = clean_subagent_id(name)
    candidate = base
    counter = 2
    while os.path.exists(subagent_home(candidate, subagents_dir=subagents_dir)):
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def unique_secret_subagent_id(name: str, *, existing_ids: Collection[str]) -> str:
    base = clean_subagent_id(name)
    candidate = base
    counter = 2
    existing = set(existing_ids)
    while candidate in existing:
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def unique_runtime_subagent_id(name: str, *, existing_ids: Collection[str]) -> str:
    base = "tmp-" + clean_subagent_id(name)
    candidate = f"{base}-{time.time_ns() % 1_000_000_000_000}"
    counter = 2
    existing = set(existing_ids)
    while candidate in existing:
        candidate = f"{base}-{time.time_ns() % 1_000_000_000_000}-{counter}"
        counter += 1
    return candidate


def normalize_subagent_skill_refs(value: Any, limit: int | None = None) -> list[str]:
    raw_items: list[str] = []
    if isinstance(value, str):
        text = value.strip()
        if "," in text or "\n" in text:
            raw_items.extend(part.strip() for part in re.split(r"[,\n]+", text))
        else:
            raw_items.extend(part.strip() for part in text.split())
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, dict):
                raw_items.append(str(item.get("ref") or item.get("name") or item.get("skill") or item.get("path") or ""))
            else:
                raw_items.append(str(item or ""))
    elif isinstance(value, dict):
        raw_items.extend(str(key) for key, enabled in value.items() if enabled)
    seen: set[str] = set()
    refs: list[str] = []
    for item in raw_items:
        ref = clean_text(str(item or "")).strip()
        ref = ref.removeprefix("skill://").strip()
        ref = re.sub(r"\s+", " ", ref)
        if not ref or len(ref) > 220:
            continue
        key = ref.casefold()
        if key in seen:
            continue
        seen.add(key)
        refs.append(ref)
        if limit is not None and limit > 0 and len(refs) >= limit:
            break
    return refs


def parse_subagent_new_body(
    body: str,
    *,
    supported_roles: Collection[str] = (),
    normalize_role: Callable[[str], tuple[str, str]] | None = None,
) -> tuple[str, str, str, bool, str]:
    body = (body or "").strip()
    persistent = False
    for flag in ("--persistent", "--persist", "--long-term", "--long_term", "--permanent", "--durable"):
        if re.search(rf"(^|\s){re.escape(flag)}(\s|$)", body, flags=re.IGNORECASE):
            persistent = True
            body = re.sub(rf"(^|\s){re.escape(flag)}(\s|$)", " ", body, flags=re.IGNORECASE).strip()
    for flag in ("--temp", "--temporary", "--ephemeral"):
        if re.search(rf"(^|\s){re.escape(flag)}(\s|$)", body, flags=re.IGNORECASE):
            persistent = False
            body = re.sub(rf"(^|\s){re.escape(flag)}(\s|$)", " ", body, flags=re.IGNORECASE).strip()
    if "|" in body:
        name, profile = [part.strip() for part in body.split("|", 1)]
    else:
        name, profile = body, ""
    for prefix in ("persistent", "persist", "permanent", "durable", "long_term", "long-term", "长期", "持久", "永久"):
        for sep in (":", "："):
            marker = prefix + sep
            if name.lower().startswith(marker):
                persistent = True
                name = name[len(marker):].strip()
                break
        else:
            continue
        break
    for prefix in ("temp", "temporary", "ephemeral", "临时", "暂时"):
        for sep in (":", "："):
            marker = prefix + sep
            if name.lower().startswith(marker):
                persistent = False
                name = name[len(marker):].strip()
                break
        else:
            continue
        break
    role = "specialist"
    role_note = ""
    supported_role_keys = {clean_subagent_id(str(item)).replace("-", "_") for item in supported_roles}
    for sep in (":", "："):
        if sep in name:
            maybe_role, maybe_name = [part.strip() for part in name.split(sep, 1)]
            role_key = clean_subagent_id(maybe_role).replace("-", "_")
            if role_key in supported_role_keys:
                role, role_note = normalize_role(maybe_role) if normalize_role else (role_key, "")
                name = maybe_name
                break
    return name.strip(), profile.strip(), role, persistent, role_note


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
