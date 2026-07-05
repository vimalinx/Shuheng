"""Process-summary-safe history title and description helpers."""
from __future__ import annotations

import re
from typing import Any, Callable

try:
    from .control_protocol import TUI_CONTROL_FENCE_RE, TUI_CONTROL_RE, strip_tui_controls
    from .history_store import assistant_text_from_response_body
    from .text_utils import clean_text, compact_title
except Exception:  # pragma: no cover - supports direct module execution fallback
    from control_protocol import TUI_CONTROL_FENCE_RE, TUI_CONTROL_RE, strip_tui_controls  # type: ignore
    from history_store import assistant_text_from_response_body  # type: ignore
    from text_utils import clean_text, compact_title  # type: ignore


SUMMARY_RE = re.compile(r"<summary>\s*(.*?)\s*</summary>", re.DOTALL)
TURN_MARKER_RE = re.compile(r"(?m)(^[ \t]*\**LLM Running \(Turn \d+\) \.\.\.\**[ \t\r]*$)")
META_BLOCK_RE = re.compile(r"<(?:summary|thinking|think)>[\s\S]*?</(?:summary|thinking|think)>", re.IGNORECASE)
TOOL_USE_BLOCK_RE = re.compile(r"<tool_use>[\s\S]*?</tool_use>", re.IGNORECASE)
TOOL_HEADER_RE = re.compile(r"🛠️\s*Tool:\s*`[^`]+`\s*📥\s*args:\s*", re.IGNORECASE)
DETAIL_FENCE_RE = re.compile(r"`{3,}[^\n]*\n[\s\S]*?\n`{3,}", re.MULTILINE)


def clamp_session_title_chars(title: str, max_chars: int = 16) -> str:
    if max_chars <= 0:
        return ""
    title = compact_title(title, max(1, max_chars * 4))
    if len(title) > max_chars:
        title = title[:max_chars]
    return title.strip(" -:：。,.，")


def short_session_title(text: str, fallback: str = "历史会话", *, title_width: int = 32, title_chars: int = 16) -> str:
    title = clamp_session_title_chars(compact_title(text, title_width), title_chars)
    return title or fallback


def compact_description(text: str, max_chars: int = 200) -> str:
    text = clean_text(text)
    text = TUI_CONTROL_RE.sub(" ", text)
    text = TUI_CONTROL_FENCE_RE.sub(" ", text)
    text = TOOL_USE_BLOCK_RE.sub(" ", text)
    text = DETAIL_FENCE_RE.sub(" ", text)
    text = META_BLOCK_RE.sub(" ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[*_`#>\[\]{}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -:：。,.，")
    if len(text) > max_chars:
        text = text[: max(0, max_chars - 3)].rstrip(" -:：。,.，") + "..."
    return text


def text_has_process_markers(text: str) -> bool:
    lowered = (text or "").lower()
    return (
        bool(TURN_MARKER_RE.search(text or ""))
        or "<thinking>" in lowered
        or "<think>" in lowered
        or bool(TOOL_USE_BLOCK_RE.search(text or ""))
        or bool(TOOL_HEADER_RE.search(text or ""))
    )


def session_summary_titles_from_text(text: str) -> list[str]:
    if text_has_process_markers(text):
        return []
    titles: list[str] = []
    for summary in SUMMARY_RE.findall(text or ""):
        title = short_session_title(summary, "")
        if title:
            titles.append(title)
    return titles


def session_response_preview_text(
    response_body: str,
    max_chars: int = 110,
    *,
    latest_visible_reply_text: Callable[[str], str],
) -> str:
    text = assistant_text_from_response_body(response_body)
    titles = session_summary_titles_from_text(text)
    if titles:
        return titles[-1]
    return compact_description(latest_visible_reply_text(text), max_chars)


def session_preview_from_pairs(
    pairs: list[tuple[str, str]],
    *,
    user_text_from_prompt: Callable[[str], str],
    response_preview_text: Callable[[str, int], str],
) -> str:
    for _prompt, response in reversed(pairs):
        titles = session_summary_titles_from_text(assistant_text_from_response_body(response))
        if titles:
            return titles[-1]
    for prompt, _response in pairs:
        user = compact_description(user_text_from_prompt(prompt), 90)
        if user:
            return user
    for _prompt, response in reversed(pairs):
        preview = response_preview_text(response, 90)
        if preview:
            return preview
    return ""


def is_process_only_session_title(text: str) -> bool:
    title = compact_title(re.sub(r"^（预览）", "", str(text or "")), 80).casefold()
    if not title:
        return False
    if title in {"omp 思考", "思考", "thinking", "执行中", "搜索/浏览输出已折叠"}:
        return True
    return title.startswith(("omp 工具", "调用 omp 工具", "调用工具", "tool "))


def history_cache_has_process_only_preview(meta: dict[str, Any]) -> bool:
    if is_process_only_session_title(str(meta.get("preview") or "")):
        return True
    description = str(meta.get("description") or "")
    if "OMP 思考" in description:
        return True
    raw_preview_messages = meta.get("ui_preview_messages")
    if isinstance(raw_preview_messages, list):
        for item in raw_preview_messages:
            if isinstance(item, dict) and is_process_only_session_title(str(item.get("content") or "")):
                return True
    return False


def message_text_for_metadata_context(
    msg: Any,
    *,
    latest_visible_reply_text: Callable[[str], str],
) -> str:
    if getattr(msg, "role", "") == "assistant":
        return latest_visible_reply_text(getattr(msg, "content", "") or "")
    text = clean_text(strip_tui_controls(getattr(msg, "content", "") or ""))
    text = META_BLOCK_RE.sub(" ", text)
    text = TOOL_USE_BLOCK_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def session_description_from_pairs(
    pairs: list[tuple[str, str]],
    preview: str = "",
    *,
    user_text_from_prompt: Callable[[str], str],
    response_preview_text: Callable[[str, int], str],
    description_limit: int = 200,
) -> str:
    snippets: list[str] = []
    if pairs:
        users: list[str] = []
        summaries: list[str] = []
        for prompt, response in pairs:
            user = compact_description(user_text_from_prompt(prompt), 90)
            if user:
                users.append(user)
            summary_text = response_preview_text(response, 110)
            if summary_text:
                summaries.append(summary_text)
        if users:
            snippets.append(f"开始：{users[0]}")
            if users[-1] != users[0]:
                snippets.append(f"最近：{users[-1]}")
        if summaries:
            snippets.append(f"摘要：{summaries[-1]}")
    if not snippets and preview:
        snippets.append(compact_description(preview, description_limit))
    return compact_description("；".join(snippets), description_limit)


def suggested_session_title(messages: list[Any]) -> str:
    for msg in reversed(messages):
        if getattr(msg, "role", "") != "assistant":
            continue
        for title in reversed(session_summary_titles_from_text(getattr(msg, "content", "") or "")):
            if title:
                return title
    for msg in messages:
        if getattr(msg, "role", "") == "user":
            title = short_session_title(getattr(msg, "content", ""), "")
            if title:
                return title
    return ""
