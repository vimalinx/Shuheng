"""Low-level history metadata and transcript storage helpers."""
from __future__ import annotations

import ast
import json
import os
import time
from typing import Any, Callable

from . import path_utils
from .scheduler import parse_schedule_timestamp
from .text_utils import clean_text
from .ui_types import Message


def session_key(path: str) -> str:
    return os.path.basename(path or "")


def load_session_meta_registry(path: str) -> dict[str, dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    meta: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, dict):
            meta[key] = dict(value)
    return meta


def save_session_meta_registry(path: str, meta: dict[str, dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, path)


def recent_history_items(
    history_entries: list[tuple[int, tuple[str, float, str, int]]],
    used_paths: set[str],
    limit: int,
) -> list[tuple[int, tuple[str, float, str, int]]]:
    recent_candidates = [
        (idx, item, float(item[1] or 0.0))
        for idx, item in history_entries
        if float(item[1] or 0.0) > 0
        and path_utils.normalized_path(item[0]) not in used_paths
    ]
    recent_candidates.sort(key=lambda entry: entry[2], reverse=True)
    return [(idx, item) for idx, item, _activity_at in recent_candidates[:limit]]


def compact_ui_preview_messages_from_pairs(
    pairs: list[tuple[str, str]],
    rounds: int,
    *,
    default_rounds: int,
    user_text_from_prompt: Callable[[str], str],
    response_preview_text: Callable[[str], str],
) -> tuple[list[dict[str, str]], int, int, int]:
    user_rounds = sum(1 for prompt, _response in pairs if user_text_from_prompt(prompt))
    total_rounds = user_rounds or len(pairs)
    if total_rounds <= 0:
        return [], 0, 0, 0
    loaded_rounds = max(1, min(int(rounds or default_rounds), total_rounds))
    start = 0
    seen = 0
    for idx in range(len(pairs) - 1, -1, -1):
        if user_text_from_prompt(pairs[idx][0]):
            seen += 1
            start = idx
            if seen >= loaded_rounds:
                break
    messages: list[dict[str, str]] = []
    for prompt, response in pairs[start:]:
        user = user_text_from_prompt(prompt)
        if user:
            messages.append({"role": "user", "content": user})
        summary = response_preview_text(response)
        if summary and summary != "执行中":
            messages.append({"role": "assistant", "content": f"（预览）{summary}"})
    return messages, loaded_rounds, total_rounds, len(messages)


def parse_log_time(text: str) -> float:
    text = (text or "").strip()
    if not text:
        return 0.0
    stamp = text[:19]
    try:
        return time.mktime(time.strptime(stamp, "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return 0.0


def session_last_user_time_from_content(
    content: str,
    fallback: float,
    prompt_re: Any,
    user_text_from_prompt: Callable[[str], str],
) -> float:
    last = 0.0
    for timestamp, prompt_body in prompt_re.findall(content):
        if user_text_from_prompt(prompt_body):
            last = parse_log_time(timestamp) or last
    return last or fallback


def session_last_user_time(
    path: str,
    fallback: float,
    prompt_re: Any,
    user_text_from_prompt: Callable[[str], str],
) -> float:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except Exception:
        return fallback
    return session_last_user_time_from_content(content, fallback, prompt_re, user_text_from_prompt)


def is_model_response_basename(key: str) -> bool:
    base = os.path.basename(key or "")
    return base.startswith("model_responses") and base.endswith(".txt")


def session_meta_epoch(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    try:
        parsed = parse_schedule_timestamp(value)
    except Exception:
        parsed = None
    return float(parsed or 0.0)


def clear_missing_source_session_meta(meta: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if not any(key in meta for key in ("source_missing", "archive_backed", "source_state")):
        return meta, False
    entry = dict(meta)
    for key in ("source_missing", "archive_backed", "source_state"):
        entry.pop(key, None)
    return entry, entry != meta


def sample_file_text(path: str, limit: int = 65536) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except Exception:
        return ""


def is_subagent_session_log_sample(text: str) -> bool:
    if not text:
        return False
    if "[GA TUI SubAgent Profile]" in text:
        return True
    if "[GA TUI Context Pack]" not in text or "[/GA TUI Context Pack]" not in text:
        return False
    return "\nagent:" in text or "\\nagent:" in text


def append_model_response_transcript_turn(
    path: str,
    user_text: str,
    assistant_text: str,
    *,
    normal_session_log_path: bool,
) -> bool:
    user_text = clean_text(user_text).strip()
    if not user_text or not normal_session_log_path:
        return False
    response_text = clean_text(assistant_text)
    prompt = {"role": "user", "content": [{"type": "text", "text": user_text}]}
    response = [{"type": "text", "text": response_text}]
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", errors="replace") as fh:
        fh.write(f"=== Prompt === {now}\n")
        fh.write(json.dumps(prompt, ensure_ascii=False, indent=2))
        fh.write(f"\n\n=== Response === {now}\n")
        fh.write(repr(response))
        fh.write("\n\n")
    try:
        os.utime(path, None)
    except OSError:
        pass
    return True


def latest_user_message_text(messages: list[Message]) -> str:
    for msg in reversed(messages or []):
        if msg.role == "user" and str(msg.content or "").strip():
            return str(msg.content or "").strip()
    return ""


def subagent_chat_message_pairs(messages: list[Message]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    pending_user: str | None = None
    for msg in messages:
        role = str(msg.role or "")
        content = clean_text(msg.content or "")
        if role == "user":
            if pending_user is not None:
                pairs.append((pending_user, ""))
            pending_user = content
        elif role == "assistant" and pending_user is not None:
            pairs.append((pending_user, content))
            pending_user = None
    if pending_user is not None:
        pairs.append((pending_user, ""))
    return pairs


def write_text_atomic(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def write_subagent_chat_history_transcript(path: str, messages: list[Message]) -> None:
    lines: list[str] = []
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    for user_text, assistant_text in subagent_chat_message_pairs(messages):
        if not clean_text(user_text).strip():
            continue
        prompt = {"role": "user", "content": [{"type": "text", "text": clean_text(user_text)}]}
        response = [{"type": "text", "text": clean_text(assistant_text)}]
        lines.append(f"=== Prompt === {now}\n{json.dumps(prompt, ensure_ascii=False, indent=2)}")
        lines.append(f"=== Response === {now}\n{repr(response)}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_text_atomic(path, "\n\n".join(lines).rstrip() + ("\n\n" if lines else ""))
    try:
        os.utime(path, None)
    except OSError:
        pass


def assistant_text_from_response_body(response_body: str) -> str:
    try:
        blocks = ast.literal_eval(response_body)
    except Exception:
        return clean_text(response_body)
    if isinstance(blocks, list):
        parts: list[str] = []
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(part for part in parts if part)
    if isinstance(blocks, dict):
        content = blocks.get("content")
        if isinstance(content, list):
            parts = [
                str(item.get("text") or "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            return "\n".join(part for part in parts if part)
        return str(content or blocks.get("text") or "")
    return clean_text(str(blocks or ""))


def messages_from_preview_dicts(raw: Any) -> list[Message]:
    if not isinstance(raw, list):
        return []
    messages: list[Message] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        content = str(item.get("content") or "")
        if role in {"user", "assistant", "system"} and content.strip():
            messages.append(Message(role, content))
    return messages
