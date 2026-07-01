"""Pure text and terminal-cell helpers for the Shuheng UI."""
from __future__ import annotations

import re
import unicodedata


ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)")


def cell_width(text: str) -> int:
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def truncate_cells(text: str, width: int) -> str:
    if width <= 0:
        return ""
    out: list[str] = []
    used = 0
    for ch in text:
        w = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
        if used + w > width:
            out.append("…")
            break
        out.append(ch)
        used += w
    return "".join(out)


def pad_cells(text: str, width: int) -> str:
    text = truncate_cells(text, width)
    return text + (" " * max(0, width - cell_width(text)))


def clean_text(text: str) -> str:
    text = ANSI_RE.sub("", text or "")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.rstrip()


def wrap_cells(text: str, width: int) -> list[str]:
    if width <= 4:
        return [truncate_cells(text, max(1, width))]
    lines: list[str] = []
    for raw in (text or "").splitlines() or [""]:
        raw = raw.replace("\t", "    ")
        if not raw:
            lines.append("")
            continue
        current = ""
        current_w = 0
        for ch in raw:
            w = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
            if current and current_w + w > width:
                lines.append(current)
                current = ch
                current_w = w
            else:
                current += ch
                current_w += w
        lines.append(current)
    return lines


def compact_title(text: str, max_width: int = 24) -> str:
    text = clean_text(text)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[*_`#>\[\]{}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -:：。,.，")
    text = re.sub(r"^(用户|User|The user)\s*(问|要求|想要|asked|wants|said)?\s*[:：]?\s*", "", text, flags=re.I)
    text = re.sub(r"^(任务已完成|已完成|总结|结论)\s*[:：]?\s*", "", text)
    if not text:
        return ""
    return truncate_cells(text, max_width).strip(" -:：。,.，")


def compact_category(text: str) -> str:
    text = compact_title(text, 18)
    return "" if text.lower() in {"-", "clear", "none", "null", "未分类"} else text
