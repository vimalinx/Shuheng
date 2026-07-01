"""Tests for pure Web Console helper contracts."""
from __future__ import annotations

from ga_tui import app as app_module
from ga_tui import web_console
from ga_tui.governance import parse_iso_timestamp


def test_web_console_ref_is_stable_opaque_and_kind_checked() -> None:
    first = web_console.web_console_ref("task", "task_sensitive_id")
    second = web_console.web_console_ref(" task ", " task_sensitive_id ")

    assert first == second
    assert first.startswith("task:")
    assert "task_sensitive_id" not in first
    assert web_console.web_console_ref("unknown", "task_sensitive_id") == ""
    assert web_console.web_console_ref("task", "") == ""


def test_web_console_timestamp_uses_iso_fields_before_mtime() -> None:
    timestamp = "2026-07-01T12:30:00+0800"
    row = {
        "timestamp": timestamp,
        "updated_at": "2026-07-01T12:31:00+0800",
        "mtime": "123.5",
    }

    assert web_console.web_console_timestamp(row) == parse_iso_timestamp(timestamp)
    assert web_console.web_console_timestamp({"updated_at": timestamp, "mtime": "123.5"}) == parse_iso_timestamp(
        timestamp
    )
    assert web_console.web_console_timestamp({"mtime": "123.5"}) == 123.5
    assert web_console.web_console_timestamp({"mtime": "not-a-number"}) == 0.0


def test_web_console_clean_visible_sanitizes_internal_refs_and_markers() -> None:
    raw = "\n".join(
        [
            "APPROVAL_REQUIRED should not be shown",
            "**See** artifact://agent_harness/artifacts/raw.md",
            "approval=appr_hidden appr_123 task_abc schedrun_123 sched_456 agent-123 tmp-agent-abc",
            "`inline` [link](https://example.invalid/path)",
        ]
    )

    cleaned = web_console.web_console_clean_visible(raw, limit=500)

    assert "APPROVAL_REQUIRED" not in cleaned
    assert "artifact://" not in cleaned
    assert "appr_" not in cleaned
    assert "approval=appr_hidden" not in cleaned
    assert "task_abc" not in cleaned
    assert "schedrun_123" not in cleaned
    assert "sched_456" not in cleaned
    assert "agent-123" not in cleaned
    assert "tmp-agent-abc" not in cleaned
    assert "[artifact]" in cleaned
    assert "[approval]" in cleaned
    assert "approval=[hidden]" in cleaned
    assert "[task]" in cleaned
    assert "[schedule-run]" in cleaned
    assert "[schedule]" in cleaned
    assert "子代理" in cleaned
    assert "临时代理" in cleaned
    assert "See" in cleaned
    assert "inline" in cleaned
    assert "link (https://example.invalid/path)" in cleaned


def test_web_console_status_labels_and_metric_shape() -> None:
    assert web_console.web_console_status_label("approval_required") == "待审批"
    assert web_console.web_console_status_label("completed") == "完成"
    assert web_console.web_console_status_label("running") == "运行中"
    assert web_console.web_console_status_label("cancelled") == "已取消"
    assert web_console.web_console_status_label("task_internal") == "[task]"
    assert web_console.web_console_status_label("") == "-"

    assert web_console.web_console_metric("待审批", 3, "warn") == {
        "label": "待审批",
        "value": "3",
        "tone": "warn",
    }


def test_app_web_console_wrappers_match_module() -> None:
    assert app_module.WEB_CONSOLE_ACTION_REQUEST_SCHEMA == web_console.WEB_CONSOLE_ACTION_REQUEST_SCHEMA
    assert app_module.WEB_CONSOLE_ACTION_RESPONSE_SCHEMA == web_console.WEB_CONSOLE_ACTION_RESPONSE_SCHEMA
    assert app_module.WEB_CONSOLE_REF_KINDS is web_console.WEB_CONSOLE_REF_KINDS
    assert app_module.web_console_ref is web_console.web_console_ref
    assert app_module.web_console_timestamp is web_console.web_console_timestamp
    assert app_module.web_console_clean_visible is web_console.web_console_clean_visible
    assert app_module.web_console_status_label is web_console.web_console_status_label
    assert app_module.web_console_metric is web_console.web_console_metric
