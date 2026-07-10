"""Shuheng-owned fallbacks for legacy GenericAgent frontend helpers."""
from __future__ import annotations

import ast
import json
import os
import re
from types import SimpleNamespace
from typing import Any

try:
    from .history_store import assistant_text_from_response_body
    from .text_utils import clean_text
except Exception:  # pragma: no cover - direct execution fallback
    from history_store import assistant_text_from_response_body  # type: ignore
    from text_utils import clean_text  # type: ignore


PROMPT_RESPONSE_RE = re.compile(
    r"^=== Prompt ===[^\n]*\n(?P<prompt>.*?)(?:\n+)?^=== Response ===[^\n]*\n(?P<response>.*?)(?=^=== Prompt ===|\Z)",
    re.DOTALL | re.MULTILINE,
)


def _parse_structured_text(text: str) -> Any:
    raw = str(text or "").strip()
    if not raw:
        return None
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(raw)
        except Exception:
            pass
    return raw


def _content_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return clean_text(value).strip()
    if isinstance(value, dict):
        if value.get("type") == "text" and "text" in value:
            return clean_text(str(value.get("text") or "")).strip()
        if "content" in value:
            return _content_text(value.get("content"))
        if "text" in value:
            return clean_text(str(value.get("text") or "")).strip()
        return ""
    if isinstance(value, list):
        parts = [_content_text(item) for item in value]
        return "\n".join(part for part in parts if part).strip()
    return clean_text(str(value)).strip()


def pairs(content: str) -> list[tuple[str, str]]:
    return [(match.group("prompt").strip(), match.group("response").strip()) for match in PROMPT_RESPONSE_RE.finditer(content or "")]


def user_text(prompt: str) -> str:
    parsed = _parse_structured_text(prompt)
    if isinstance(parsed, dict):
        return _content_text(parsed.get("content") if "content" in parsed else parsed)
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict) and str(item.get("role") or "") == "user":
                text = _content_text(item.get("content"))
                if text:
                    return text
        return _content_text(parsed)
    return _content_text(parsed)


def tool_results_from_prompt(prompt: str) -> dict[str, str]:
    parsed = _parse_structured_text(prompt)
    rows = parsed if isinstance(parsed, list) else [parsed]
    results: dict[str, str] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "")
        if role not in {"tool", "tool_result"}:
            continue
        key = str(item.get("tool_call_id") or item.get("id") or len(results))
        text = _content_text(item.get("content") if "content" in item else item)
        if text:
            results[key] = text
    return results


def format_response_segment(response: str, tool_results: dict[str, str] | None = None) -> str:
    text = assistant_text_from_response_body(response)
    if tool_results:
        tool_text = "\n".join(f"[tool:{key}] {value}" for key, value in tool_results.items() if value)
        if tool_text:
            text = (text.rstrip() + "\n\n" + tool_text).strip()
    return clean_text(text).strip()


def preview_text(parsed_pairs: list[tuple[str, str]]) -> str:
    for prompt, _response in parsed_pairs:
        text = user_text(prompt)
        if text:
            return text[:110]
    for _prompt, response in reversed(parsed_pairs):
        text = format_response_segment(response, {})
        if text:
            return text[:110]
    return ""


def parse_native_history(parsed_pairs: list[tuple[str, str]]) -> list[dict[str, Any]] | None:
    history: list[dict[str, Any]] = []
    for prompt, response in parsed_pairs:
        user = user_text(prompt)
        if user:
            history.append({"role": "user", "content": user})
        assistant = format_response_segment(response, {})
        if assistant:
            history.append({"role": "assistant", "content": assistant})
    return history or None


def reset_conversation(agent: Any, message: Any = None) -> None:
    del message
    if agent is None:
        return
    try:
        agent.abort()
    except Exception:
        pass
    if hasattr(agent, "history"):
        try:
            agent.history = []
        except Exception:
            pass
    for client in getattr(agent, "llmclients", []) or []:
        backend = getattr(client, "backend", None)
        if backend is not None and hasattr(backend, "history"):
            try:
                backend.history = []
            except Exception:
                pass


def restore(agent: Any, path: str) -> tuple[str, bool]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            parsed_pairs = pairs(fh.read())
    except Exception as exc:
        return f"恢复失败: {type(exc).__name__}: {exc}", False
    history = parse_native_history(parsed_pairs)
    if history is None:
        return "恢复失败: history is empty or unsupported", False
    for client in getattr(agent, "llmclients", []) or []:
        backend = getattr(client, "backend", None)
        if backend is not None and hasattr(backend, "history"):
            try:
                backend.history = list(history)
            except Exception:
                pass
    return f"已恢复完整上下文：{len(parsed_pairs)} 轮", True


def _default_model_responses_dir() -> str:
    shuheng_home = os.environ.get("SHUHENG_HOME") or "~/.shuheng"
    return os.path.join(os.path.abspath(os.path.expanduser(shuheng_home)), "model_responses")


def fallback_continue_cmd_module(log_dir: str = "") -> SimpleNamespace:
    log_dir = os.path.abspath(os.path.expanduser(log_dir or _default_model_responses_dir()))
    return SimpleNamespace(
        _LOG_DIR=log_dir,
        _LOG_GLOB=os.path.join(log_dir, "model_responses_*.txt"),
        _ROUNDS_CACHE_PATH=os.path.join(os.path.dirname(log_dir), "continue_rounds_cache.json"),
        _rounds_cache=None,
        _rounds_cache_dirty=False,
        _format_response_segment=format_response_segment,
        _pairs=pairs,
        _parse_native_history=parse_native_history,
        _preview_text=preview_text,
        _tool_results_from_prompt=tool_results_from_prompt,
        _user_text=user_text,
        reset_conversation=reset_conversation,
        restore=restore,
    )


class FallbackSessionNames:
    def __init__(self, log_dir: str = "") -> None:
        self._LOG_DIR = os.path.abspath(os.path.expanduser(log_dir or _default_model_responses_dir()))
        self._REG_PATH = os.path.join(self._LOG_DIR, "session_names.json")

    def _load(self) -> dict[str, str]:
        try:
            with open(self._REG_PATH, encoding="utf-8") as fh:
                raw = json.load(fh)
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        return {str(key): str(value) for key, value in raw.items() if str(value or "").strip()}

    def _save(self, data: dict[str, str]) -> None:
        os.makedirs(os.path.dirname(self._REG_PATH), exist_ok=True)
        tmp = self._REG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, self._REG_PATH)

    def name_for(self, path: str) -> str:
        return self._load().get(os.path.basename(path or ""), "")

    def set_name(self, path: str, name: str) -> None:
        key = os.path.basename(path or "")
        if not key:
            return
        data = self._load()
        clean_name = str(name or "").strip()
        if clean_name:
            data[key] = clean_name
        else:
            data.pop(key, None)
        self._save(data)


def fallback_session_names(log_dir: str = "") -> FallbackSessionNames:
    return FallbackSessionNames(log_dir)


__all__ = [
    "FallbackSessionNames",
    "fallback_continue_cmd_module",
    "fallback_session_names",
    "format_response_segment",
    "pairs",
    "parse_native_history",
    "preview_text",
    "reset_conversation",
    "restore",
    "tool_results_from_prompt",
    "user_text",
]
