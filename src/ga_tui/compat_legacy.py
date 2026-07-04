"""Quarantined helpers for historical TUI artifacts.

This module is intentionally not a source of current control protocol truth.
It only strips or matches retired markup that may appear in old persisted
session files so hidden artifacts are not rehydrated into the live UI.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional


RETIRED_TUI_CONTROL_RE = re.compile(r"(?<!`)<ga[-_]tui>\s*([\s\S]*?)\s*</ga[-_]tui>", re.IGNORECASE)
RETIRED_TUI_CONTROL_FENCE_RE = re.compile(r"```ga[-_]tui\s*([\s\S]*?)```", re.IGNORECASE)
HISTORICAL_SUBAGENT_BACKFILL_WINDOW_SECONDS = 2 * 60 * 60


def strip_retired_tui_markup(text: str) -> str:
    text = RETIRED_TUI_CONTROL_RE.sub("", text or "")
    text = RETIRED_TUI_CONTROL_FENCE_RE.sub("", text)
    text = re.sub(r"(?<!`)<ga[-_]tui>[\s\S]*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```ga[-_]tui[\s\S]*$", "", text, flags=re.IGNORECASE)
    return text


def parse_timestamp_value(text: str) -> float:
    value = str(text or "").strip()
    if not value:
        return 0.0
    for candidate, fmt in (
        (value[:19], "%Y-%m-%dT%H:%M:%S"),
        (value[:19], "%Y-%m-%d %H:%M:%S"),
        (value[:24], "%Y-%m-%dT%H:%M:%S%z"),
    ):
        try:
            return datetime.strptime(candidate, fmt).timestamp()
        except Exception:
            continue
    return 0.0


def historical_match_text(text: str) -> str:
    text = str(text or "")
    text = text.replace("\\n", " ").replace('\\"', '"').replace("\\'", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def session_control_blocks_with_historical_markers(path: str, response_block_re: re.Pattern[str]) -> list[tuple[float, str]]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError:
        return []
    blocks: list[tuple[float, str]] = []
    action_markers = (
        "delegate.create",
        "agenttask.v2",
        "subagent_ask",
        "subagent_run",
        "subagent_input",
        "agent_ask",
        "agent_run",
    )
    for timestamp, response_body in response_block_re.findall(content):
        if not any(marker in response_body for marker in action_markers):
            continue
        blocks.append((parse_timestamp_value(timestamp), historical_match_text(response_body)))
    return blocks


def historical_subagent_row_matches_session(
    row: dict[str, Any],
    first_task_timestamp: float,
    control_blocks: Optional[list[tuple[float, str]]] = None,
) -> bool:
    if str(row.get("session_key") or "").strip():
        return False
    objective = historical_match_text(row.get("objective") or "")
    if len(objective) < 8:
        return False
    blocks = control_blocks or []
    for anchor_timestamp, response_body in blocks:
        if objective not in response_body:
            continue
        if anchor_timestamp > 0 and first_task_timestamp > 0:
            if first_task_timestamp < anchor_timestamp - 5:
                continue
            if first_task_timestamp > anchor_timestamp + HISTORICAL_SUBAGENT_BACKFILL_WINDOW_SECONDS:
                continue
        return True
    return False
