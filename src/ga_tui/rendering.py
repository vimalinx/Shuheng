"""Curses-free rendering helper transforms for Shuheng."""
from __future__ import annotations

from collections.abc import Callable
import re

try:
    from . import history_titles as history_title_policy
    from .text_utils import cell_width, clean_text, compact_title, pad_cells, wrap_cells
    from .ui_types import RenderLine
except Exception:
    import history_titles as history_title_policy  # type: ignore
    from text_utils import cell_width, clean_text, compact_title, pad_cells, wrap_cells  # type: ignore
    from ui_types import RenderLine  # type: ignore


SelectionPoint = tuple[int, int]
SelectionPoints = tuple[SelectionPoint, SelectionPoint]
TableLayoutLine = tuple[str, str]
MarkdownLayoutLine = tuple[str, str]
RUN_FRAMES = ("[=     ]", "[==    ]", "[ ===  ]", "[  === ]", "[    ==]", "[     =]")
SUMMARY_RE = history_title_policy.SUMMARY_RE
TURN_MARKER_RE = history_title_policy.TURN_MARKER_RE
TURN_NO_RE = re.compile(r"Turn\s+(\d+)")
LINE_NUMBERED_FILE_RE = re.compile(r"^[ \t]*\d+\|")
FENCE_BOUNDARY_RE = re.compile(r"^[ \t]*(`{3,})(.*)$")
MARKDOWN_FENCE_BOUNDARY_RE = re.compile(r"^\s*(`{3,})(.*)$")
META_BLOCK_RE = history_title_policy.META_BLOCK_RE
DETAIL_FENCE_RE = history_title_policy.DETAIL_FENCE_RE
THINKING_BLOCK_RE = re.compile(r"<(?:thinking|think)>\s*([\s\S]*?)\s*</(?:thinking|think)>", re.IGNORECASE)
TOOL_CALL_RE = re.compile(r"🛠️\s*Tool:\s*`([^`]+)`")
TOOL_USE_NAME_RE = re.compile(r"<tool_use>\s*\{[\s\S]*?\"name\"\s*:\s*\"([^\"]+)\"[\s\S]*?</tool_use>")
TOOL_USE_BLOCK_RE = history_title_policy.TOOL_USE_BLOCK_RE
TOOL_HEADER_RE = history_title_policy.TOOL_HEADER_RE
TOOL_CALL_BLOCK_RE = re.compile(r"🛠️\s*Tool:\s*`[^`]+`\s*📥\s*args:\s*\n`{4}text\n[\s\S]*?^`{4}\s*", re.IGNORECASE | re.MULTILINE)
TOOL_RESULT_FENCE_RE = re.compile(r"^`{5}\s*\n[\s\S]*?^`{5}\s*$", re.MULTILINE)
FINAL_RESPONSE_INFO_RE = re.compile(r"^\s*\[Info\]\s+Final response to user\.\s*$", re.IGNORECASE | re.MULTILINE)
SEARCH_NOISE_MARKERS = (
    "google.com/search",
    "duckduckgo",
    "searching:",
    "search results",
    "google 搜索",
    "[textarea #apjfqb",
    "dom变化量",
    "最显著变化",
    "\"diff\":",
    "result__snippet",
    "queryselectorall",
)


def process_turn_label(marker: str) -> str:
    turn = TURN_NO_RE.search(marker or "")
    return f"Turn {turn.group(1)}" if turn else "Turn"


def process_tool_suffix(tools: list[str], limit: int = 3) -> str:
    visible_tools = [tool for tool in tools if tool][:limit]
    if not visible_tools:
        return ""
    suffix = f" · tool: {', '.join(visible_tools)}"
    extra = len([tool for tool in tools if tool]) - len(visible_tools)
    if extra > 0:
        suffix += f" +{extra}"
    return suffix


def collapsed_process_line_text(marker: str, summary: str, tools: list[str], current: bool) -> str:
    status = "正在执行" if current else "已折叠"
    return f"▸ 过程 {process_turn_label(marker)}: {summary}{process_tool_suffix(tools)} ({status})"


def process_detail_line_text(marker: str, summary: str, tools: list[str], current: bool) -> str:
    title = f": {summary}" if summary else ""
    status = "正在执行" if current else "已折叠"
    return f"▸ 细节 {process_turn_label(marker)}{title}{process_tool_suffix(tools)} ({status})"


def process_speech_header_text(marker: str, tools: list[str]) -> str:
    return f"· 过程 {process_turn_label(marker)}{process_tool_suffix(tools)}"


def process_speech_summary_line_text(marker: str, summary: str, tools: list[str]) -> str:
    return f"· 过程 {process_turn_label(marker)}: {summary}{process_tool_suffix(tools)}"


def expanded_process_header_text(marker: str, summary: str, tools: list[str], current: bool) -> str:
    title = f": {summary}" if summary else ""
    status = "正在等待用户输入" if current else "已展开"
    return f"▾ 过程 {process_turn_label(marker)}{title}{process_tool_suffix(tools)} ({status})"


def process_turn_no(marker: str, fallback: int) -> int:
    turn = TURN_NO_RE.search(marker or "")
    if turn:
        try:
            return int(turn.group(1))
        except ValueError:
            pass
    return fallback


def process_group_header_text(label: str, title: str, tools: list[str], current: bool, expanded: bool) -> str:
    icon = "▾" if expanded else "▸"
    status = "正在执行" if current else ("已展开" if expanded else "已折叠")
    return f"{icon} 过程组 {label}: {title}{process_tool_suffix(tools)} ({status}，点击展开/收起)"


def collapsed_process_child_line_text(label: str, raw_line: str) -> str:
    return "  " + raw_line.replace("▸ 过程 ", f"▸ 过程 {label} ", 1)


def expanded_process_child_header_text(label: str, raw_line: str) -> str:
    return "  " + raw_line.replace("▾ 过程 ", f"▾ 过程 {label} ", 1)


def process_child_detail_text(cleaned_body: str, preview: str, limit: int = 12000) -> str:
    detail = strip_meta_blocks(clean_text(cleaned_body or "")).strip()
    if not detail:
        detail = preview
    if len(detail) > limit:
        detail = detail[:limit].rstrip() + "\n...（详情过长，已截断；需要原文请打开对应 artifact/trace）"
    return "\n".join("    " + line for line in detail.splitlines())


def process_has_tool_call_noise_text(body: str, tools: list[str]) -> bool:
    body = body or ""
    return bool(tools) or "<tool_use>" in body or bool(TOOL_HEADER_RE.search(body))


def process_has_tool_result_noise_text(body: str) -> bool:
    body = body or ""
    return bool(TOOL_RESULT_FENCE_RE.search(body)) or bool(FINAL_RESPONSE_INFO_RE.search(body))


def process_has_tool_noise_text(body: str, tools: list[str]) -> bool:
    return process_has_tool_call_noise_text(body, tools) or process_has_tool_result_noise_text(body)


def process_has_search_noise_text(body: str, tools: list[str]) -> bool:
    body = body or ""
    lowered = body.lower()
    lowered_tools = [tool.lower() for tool in tools]
    if any(
        tool.startswith(("web_", "browser_", "bb_browser"))
        or "search" in tool
        or "query" in tool
        for tool in lowered_tools
    ):
        return True
    return any(marker in lowered for marker in SEARCH_NOISE_MARKERS)


def strip_meta_blocks(text: str) -> str:
    return META_BLOCK_RE.sub("", text or "").strip()


def strip_tool_output_blocks(text: str) -> str:
    text = TOOL_CALL_BLOCK_RE.sub("", text or "")
    text = TOOL_USE_BLOCK_RE.sub("", text)
    text = TOOL_RESULT_FENCE_RE.sub("", text)
    text = TOOL_HEADER_RE.sub("", text)
    text = FINAL_RESPONSE_INFO_RE.sub("", text)
    return text


def strip_standalone_dot_lines(text: str) -> str:
    lines = [
        line
        for line in (text or "").splitlines()
        if line.strip() != "."
    ]
    return "\n".join(lines).strip()


def visible_reply_text(body: str, hide_detail_fences: bool = False) -> str:
    text = strip_meta_blocks(body)
    if hide_detail_fences:
        text = strip_tool_output_blocks(text)
    else:
        text = TOOL_USE_BLOCK_RE.sub("", text)
        text = TOOL_HEADER_RE.sub("", text)
        text = FINAL_RESPONSE_INFO_RE.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return strip_standalone_dot_lines(text)


def strip_inline_markdown(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"[\1]", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<!_)_(?!_)(.*?)(?<!_)_(?!_)", r"\1", text)
    return text


def is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def split_table_row(line: str) -> list[str]:
    raw = line.strip().strip("|")
    return [strip_inline_markdown(cell.strip()) for cell in raw.split("|")]


def table_layout_lines(lines: list[str], width: int) -> list[TableLayoutLine]:
    rows = [split_table_row(line) for line in lines]
    rows = [row for row in rows if not is_table_separator(row)]
    if not rows:
        return []
    cols = max(len(row) for row in rows)
    for row in rows:
        row.extend([""] * (cols - len(row)))
    col_widths = [max(cell_width(row[i]) for row in rows) for i in range(cols)]
    budget = max(8, width - 3 * (cols - 1))
    if sum(col_widths) > budget:
        cap = max(6, budget // max(1, cols))
        col_widths = [min(w, cap) for w in col_widths]
    out: list[TableLayoutLine] = []
    for idx, row in enumerate(rows):
        rendered = " │ ".join(pad_cells(row[i], col_widths[i]) for i in range(cols))
        out.append(("header" if idx == 0 else "body", rendered))
        if idx == 0 and len(rows) > 1:
            sep = "─┼─".join("─" * w for w in col_widths)
            out.append(("separator", sep))
    return out


def markdown_layout_blocks(text: str, width: int) -> list[MarkdownLayoutLine]:
    out: list[MarkdownLayoutLine] = []
    lines = (text or "").splitlines()
    i = 0
    in_code = False
    code_lang = ""
    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()

        fence = re.match(r"^`{3,}(.*)$", stripped)
        if fence:
            if not in_code:
                in_code = True
                code_lang = fence.group(1).strip() or "code"
                out.append(("code_header", "╭─ " + code_lang))
            else:
                in_code = False
                out.append(("code_footer", "╰─"))
            i += 1
            continue
        if in_code:
            for wrapped in wrap_cells(raw, max(8, width - 2)):
                out.append(("code_body", "│ " + wrapped))
            i += 1
            continue

        if "|" in raw and i + 1 < len(lines) and "|" in lines[i + 1]:
            maybe_sep = split_table_row(lines[i + 1])
            if is_table_separator(maybe_sep):
                table_lines = [raw, lines[i + 1]]
                i += 2
                while i < len(lines) and "|" in lines[i] and lines[i].strip():
                    table_lines.append(lines[i])
                    i += 1
                for kind, rendered in table_layout_lines(table_lines, width):
                    out.append((f"table_{kind}", rendered))
                continue

        if not stripped:
            out.append(("blank", ""))
            i += 1
            continue
        if re.fullmatch(r"[-*_]{3,}", stripped):
            out.append(("rule", "─" * min(width, 80)))
            i += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            marker = "█" if level <= 2 else "▪"
            kind = "heading_major" if level <= 2 else "heading_minor"
            for wrapped in wrap_cells(strip_inline_markdown(heading.group(2)), max(8, width - 2)):
                out.append((kind, f"{marker} {wrapped}"))
            i += 1
            continue

        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            for wrapped in wrap_cells(strip_inline_markdown(quote.group(1)), max(8, width - 2)):
                out.append(("quote", "▌ " + wrapped))
            i += 1
            continue

        task = re.match(r"^[-*+]\s+\[([ xX])\]\s+(.+)$", stripped)
        if task:
            mark = "☑" if task.group(1).lower() == "x" else "☐"
            for n, wrapped in enumerate(wrap_cells(strip_inline_markdown(task.group(2)), max(8, width - 4))):
                out.append(("body", ("  " + mark + " " if n == 0 else "    ") + wrapped))
            i += 1
            continue

        bullet = re.match(r"^([-*+])\s+(.+)$", stripped)
        if bullet:
            for n, wrapped in enumerate(wrap_cells(strip_inline_markdown(bullet.group(2)), max(8, width - 4))):
                out.append(("body", ("  • " if n == 0 else "    ") + wrapped))
            i += 1
            continue

        numbered = re.match(r"^(\d+[.)])\s+(.+)$", stripped)
        if numbered:
            label = numbered.group(1)
            indent = " " * (len(label) + 3)
            for n, wrapped in enumerate(wrap_cells(strip_inline_markdown(numbered.group(2)), max(8, width - len(indent)))):
                out.append(("body", (f"  {label} " if n == 0 else indent) + wrapped))
            i += 1
            continue

        for wrapped in wrap_cells(strip_inline_markdown(raw), width):
            out.append(("body", wrapped))
        i += 1
    return out


def plain_layout_lines(text: str, width: int) -> list[str]:
    return wrap_cells(text, width)


def visible_reply_is_substantive(text: str) -> bool:
    clean = strip_inline_markdown(clean_text(text or "")).strip()
    if len(clean) >= 180:
        return True
    markers = ("# ", "## ", "### ", "|", "- ", "1.", "1. ", "✅", "结论", "报告")
    return len(clean) >= 80 and any(marker in (text or "") for marker in markers)


def visible_reply_is_housekeeping_summary(text: str) -> bool:
    clean = strip_inline_markdown(clean_text(text or "")).strip()
    if not clean:
        return False
    first_line = clean.splitlines()[0].strip()
    starts_with_summary = bool(re.match(r"(?i)^(summary|摘要|总结)\s*[\|:：-]", first_line))
    has_confidence = bool(re.search(r"(?im)^\s*(confidence|置信度)\s*[:：]", clean))
    has_completion = any(marker in clean for marker in ("任务完成", "已完成", "complete"))
    return starts_with_summary and (has_confidence or has_completion)


def visible_reply_has_section_shape(text: str) -> bool:
    return bool(re.search(r"(?m)^#{1,3}\s+\S+", text or "")) or "结论" in (text or "")


def preferred_group_visible_reply_text(visible_items: list[str], irc_replies: list[str]) -> str:
    chosen = visible_items[-1] if visible_items else ""
    if chosen and (not visible_reply_is_substantive(chosen) or visible_reply_is_housekeeping_summary(chosen)):
        chosen_len = len(strip_inline_markdown(clean_text(chosen)).strip())
        for candidate in reversed(visible_items[:-1]):
            candidate_len = len(strip_inline_markdown(clean_text(candidate)).strip())
            if (
                visible_reply_is_substantive(candidate)
                and (
                    candidate_len >= max(160, chosen_len * 3)
                    or (visible_reply_has_section_shape(candidate) and candidate_len >= max(80, chosen_len * 2))
                )
            ):
                chosen = candidate
                break
    unique_irc_replies: list[str] = []
    for reply in irc_replies:
        reply = str(reply or "").strip()
        if reply and reply not in unique_irc_replies and reply not in chosen:
            unique_irc_replies.append(reply)
    if unique_irc_replies:
        reply_block = "### IRC 回复\n" + "\n".join(f"- {reply}" for reply in unique_irc_replies)
        chosen = (chosen.rstrip() + "\n\n" + reply_block).strip() if chosen else reply_block
    return chosen


def process_turn_lines(
    final_text: str,
    *,
    has_process_noise: bool,
    has_call_noise: bool,
    fold_details: bool = True,
    collapse_whole: bool = False,
    collapsed_line: str = "",
    speech_header_line: str = "",
    summary_line: str = "",
    detail_line: str = "",
    fallback_summary_line: str = "",
) -> list[str]:
    if final_text:
        visible_text = final_text
        if has_call_noise and fold_details:
            visible_text = close_unbalanced_markdown_fence(visible_text)
        if collapse_whole and has_process_noise:
            lines = [visible_text]
            if fold_details and collapsed_line:
                lines.append(collapsed_line)
            return lines
        lines: list[str] = []
        if has_call_noise:
            if speech_header_line:
                lines.append(speech_header_line)
        elif summary_line:
            lines.append(summary_line)
        lines.append(visible_text)
        if has_call_noise and fold_details and detail_line:
            lines.append(detail_line)
        return lines
    if collapse_whole and has_process_noise:
        return [collapsed_line] if collapsed_line else []
    if fallback_summary_line:
        lines = [fallback_summary_line]
        if has_call_noise and fold_details and detail_line:
            lines.append(detail_line)
        return lines
    if has_process_noise and collapsed_line:
        return [collapsed_line]
    return []


def boxed_user_lines(text: str, width: int) -> list[str]:
    inner_limit = max(8, width - 4)
    body = wrap_cells(text, inner_limit)
    if not body:
        body = [""]
    inner_width = min(inner_limit, max(8, *(cell_width(line) for line in body)))
    top = "┌" + "─" * (inner_width + 2) + "┐"
    bottom = "└" + "─" * (inner_width + 2) + "┘"
    return [top, *("│ " + pad_cells(line, inner_width) + " │" for line in body), bottom]


def latest_visible_reply_text(text: str, has_tool_noise: Callable[[str], bool] | None = None) -> str:
    body_text = text or ""
    parts = split_top_level_turn_markers(body_text)
    if len(parts) >= 3:
        turns: list[tuple[str, str]] = []
        for idx in range(1, len(parts), 2):
            marker = parts[idx]
            body = parts[idx + 1] if idx + 1 < len(parts) else ""
            turns.append((marker, body))
        for _marker, body in reversed(turns):
            visible = visible_reply_text(body, hide_detail_fences=True).strip()
            if visible:
                return visible
    hide_detail_fences = bool(has_tool_noise(body_text)) if has_tool_noise is not None else False
    return visible_reply_text(body_text, hide_detail_fences=hide_detail_fences).strip()


def process_preview(text: str) -> str:
    summaries = SUMMARY_RE.findall(text or "")
    if summaries:
        title = compact_title(summaries[-1], 60)
        if title:
            return title
    preview = DETAIL_FENCE_RE.sub(" ", text or "")
    preview = META_BLOCK_RE.sub(" ", preview)
    preview = TOOL_CALL_RE.sub(" ", preview)
    preview = TOOL_USE_NAME_RE.sub(" ", preview)
    for line in preview.splitlines():
        line = line.strip()
        if not line or line.startswith(("```", "````", "args:", "📥")):
            continue
        title = compact_title(line, 60)
        if title:
            return title
    return "执行中"


def process_summary_text(text: str) -> str:
    summaries = SUMMARY_RE.findall(text or "")
    if not summaries:
        return ""
    summary = history_title_policy.compact_description(summaries[-1], 220)
    if history_title_policy.is_process_only_session_title(summary):
        thinking = THINKING_BLOCK_RE.findall(text or "")
        if thinking:
            return history_title_policy.compact_description(thinking[-1].strip(" \t\r\n\"'“”‘’"), 220)
    return summary


def next_nonblank_line(lines: list[str], start: int) -> str:
    for line in lines[start:]:
        if line.strip():
            return line
    return ""


def line_numbered_file_line(line: str) -> bool:
    return bool(LINE_NUMBERED_FILE_RE.match(line or ""))


def stray_line_numbered_fence_close(line: str, previous_nonblank: str, next_nonblank: str) -> bool:
    boundary = FENCE_BOUNDARY_RE.match(line)
    return bool(
        boundary
        and not boundary.group(2).strip()
        and line_numbered_file_line(previous_nonblank)
        and TURN_MARKER_RE.match(next_nonblank)
    )


def split_top_level_turn_markers(text: str) -> list[str]:
    """Split restored turns while treating fenced tool/file output as opaque data."""
    if not text:
        return [""]
    parts: list[str] = []
    last = 0
    offset = 0
    fence_ticks = ""
    previous_nonblank = ""
    lines = text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if fence_ticks:
            boundary = FENCE_BOUNDARY_RE.match(line)
            if boundary and len(boundary.group(1)) >= len(fence_ticks) and not boundary.group(2).strip():
                fence_ticks = ""
            if line.strip():
                previous_nonblank = line
            offset += len(line)
            continue

        marker = TURN_MARKER_RE.match(line)
        if marker:
            start = offset + marker.start(1)
            end = offset + marker.end(1)
            parts.append(text[last:start])
            parts.append(text[start:end])
            last = end
        else:
            boundary = FENCE_BOUNDARY_RE.match(line)
            if boundary and not stray_line_numbered_fence_close(
                line,
                previous_nonblank,
                next_nonblank_line(lines, idx + 1),
            ):
                fence_ticks = boundary.group(1)
        if line.strip():
            previous_nonblank = line
        offset += len(line)
    parts.append(text[last:])
    return parts


def close_unbalanced_markdown_fence(text: str) -> str:
    in_code = False
    fence_ticks = ""
    for line in (text or "").splitlines():
        boundary = MARKDOWN_FENCE_BOUNDARY_RE.match(line)
        if not boundary:
            continue
        ticks = boundary.group(1)
        suffix = boundary.group(2).strip()
        if not in_code:
            in_code = True
            fence_ticks = ticks
        elif len(ticks) >= len(fence_ticks) and not suffix:
            in_code = False
            fence_ticks = ""
    if in_code and fence_ticks:
        return (text or "").rstrip() + "\n" + fence_ticks
    return text


def scoped_subagent_meta_keys(process_scope: str, expanded_subagent_meta: set[str]) -> set[str]:
    scoped_subagent_meta = set(expanded_subagent_meta)
    if process_scope:
        prefix = f"{process_scope}:submeta:"
        scoped_subagent_meta = {key[len(prefix):] for key in expanded_subagent_meta if key.startswith(prefix)}
    return scoped_subagent_meta


def message_cache_signature(messages: list[object]) -> tuple[tuple[int, str, int, bool], ...]:
    return tuple(
        (
            id(msg),
            str(getattr(msg, "role", "") or ""),
            len(getattr(msg, "content", "") or ""),
            bool(getattr(msg, "done", False)),
        )
        for msg in messages
    )


def message_render_cache_key(
    msg: object,
    msg_index: int,
    width: int,
    fold_process: bool,
    markdown: bool,
    run_frame: int,
    process_scope: str,
    expanded_groups: set[str],
    expanded_turns: set[str],
    scoped_subagent_meta: set[str],
    assistant_label: str = "AI",
) -> tuple[object, ...]:
    return (
        id(msg),
        msg_index,
        str(getattr(msg, "role", "") or ""),
        len(getattr(msg, "content", "") or ""),
        hash(getattr(msg, "content", "") or ""),
        bool(getattr(msg, "done", False)),
        width,
        fold_process,
        markdown,
        process_scope,
        assistant_label,
        tuple(sorted(expanded_groups)),
        tuple(sorted(expanded_turns)),
        tuple(sorted(scoped_subagent_meta)),
    )


def char_index_for_cell(text: str, target_x: int) -> int:
    target_x = max(0, target_x)
    used = 0
    for idx, ch in enumerate(text):
        width = cell_width(ch)
        if target_x <= used:
            return idx
        if used + width > target_x:
            return idx
        used += width
        if used >= target_x:
            return idx + 1
    return len(text)


def ordered_selection_points(
    selection_start: SelectionPoint | None,
    selection_end: SelectionPoint | None,
) -> SelectionPoints | None:
    if selection_start is None or selection_end is None:
        return None
    start, end = sorted((selection_start, selection_end))
    if start == end:
        return None
    return start, end


def selection_span_for_line_points(
    points: SelectionPoints | None,
    line_idx: int,
    text: str,
) -> tuple[int, int] | None:
    if points is None:
        return None
    (start_line, start_col), (end_line, end_col) = points
    if line_idx < start_line or line_idx > end_line:
        return None
    if start_line == end_line:
        start, end = start_col, end_col
    elif line_idx == start_line:
        start, end = start_col, len(text)
    elif line_idx == end_line:
        start, end = 0, end_col
    else:
        start, end = 0, len(text)
    start = max(0, min(start, len(text)))
    end = max(0, min(end, len(text)))
    if start == end:
        return None
    return min(start, end), max(start, end)


def running_indicator(frame: int) -> str:
    return f"{RUN_FRAMES[frame % len(RUN_FRAMES)]} running..."


def running_indicator_cell_width() -> int:
    return max(cell_width(running_indicator(frame)) for frame in range(len(RUN_FRAMES)))


def render_running_indicator_line(line: RenderLine, frame: int) -> str:
    if line.kind != "running_indicator":
        return line.text
    prefix = " " * max(0, int(line.prefix_cells or 0))
    return prefix + running_indicator(frame)
