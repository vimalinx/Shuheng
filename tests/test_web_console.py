"""Tests for pure Web Console helper contracts."""
from __future__ import annotations

from shuheng import app as app_module
from shuheng import web_console
from shuheng.governance import parse_iso_timestamp


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


def test_web_console_action_ref_payload_and_message_helpers() -> None:
    task_ref = web_console.web_console_ref("task", "task_raw")
    refs = {task_ref: ("task", "task_raw")}

    assert web_console.web_console_resolve_ref(refs, task_ref, "task") == (True, "task_raw", "")
    assert web_console.web_console_resolve_ref(refs, "", "task") == (False, "", "缺少 ui_ref。")
    assert web_console.web_console_resolve_ref(refs, "task:missing", "task") == (
        False,
        "",
        "找不到这个界面引用，请刷新后重试。",
    )
    assert web_console.web_console_resolve_ref(refs, task_ref, "agent") == (
        False,
        "",
        "界面引用类型不匹配：需要 agent。",
    )
    assert web_console.web_console_action_payload({"payload": {"prompt": "hello"}}) == {"prompt": "hello"}
    assert web_console.web_console_action_payload({"payload": ["not", "dict"]}) == {}
    assert web_console.web_console_action_message("artifact://raw task_internal") == "[artifact] [task]"
    assert web_console.web_console_action_message("") == "动作已执行。"


def test_web_console_model_and_schedule_action_helpers() -> None:
    model_ref = web_console.web_console_ref("model", "deepseek")
    agent_ref = web_console.web_console_ref("agent", "agent-123")
    refs = {
        model_ref: ("model", "deepseek"),
        agent_ref: ("agent", "agent-123"),
    }

    assert web_console.web_console_model_name_from_payload({"model_name": "explicit-model"}, refs) == (
        True,
        "explicit-model",
        "",
    )
    assert web_console.web_console_model_name_from_payload({"model_ref": model_ref}, refs) == (True, "deepseek", "")
    assert web_console.web_console_model_name_from_payload({"model_ref": agent_ref}, refs) == (
        False,
        "",
        "界面引用类型不匹配：需要 model。",
    )

    ok, control, error = web_console.web_console_schedule_control_from_payload(
        {
            "name": "巡检",
            "target_agent_ref": agent_ref,
            "execution": {"mode": "main_prompt", "routing": {"target_selector": {"role": "coder"}}},
        },
        refs,
    )
    assert ok is True
    assert error == ""
    assert control["name"] == "巡检"
    assert control["execution"]["mode"] == "agent_task"
    assert control["execution"]["routing"]["selected_agent"] == "agent-123"
    assert control["execution"]["routing"]["target_selector"] == {"role": "coder", "agent_id": "agent-123"}
    assert "target_agent_ref" not in control

    ok, control, error = web_console.web_console_schedule_control_from_payload({"agent_ref": model_ref}, refs)
    assert ok is False
    assert control == {}
    assert error == "界面引用类型不匹配：需要 agent。"


def test_app_web_console_wrappers_match_module() -> None:
    assert app_module.WEB_CONSOLE_ACTION_REQUEST_SCHEMA == web_console.WEB_CONSOLE_ACTION_REQUEST_SCHEMA
    assert app_module.WEB_CONSOLE_ACTION_RESPONSE_SCHEMA == web_console.WEB_CONSOLE_ACTION_RESPONSE_SCHEMA
    assert app_module.WEB_CONSOLE_REF_KINDS is web_console.WEB_CONSOLE_REF_KINDS
    assert app_module.web_console_ref is web_console.web_console_ref
    assert app_module.web_console_timestamp is web_console.web_console_timestamp
    assert app_module.web_console_clean_visible is web_console.web_console_clean_visible
    assert app_module.web_console_status_label is web_console.web_console_status_label
    assert app_module.web_console_metric is web_console.web_console_metric
    assert app_module.web_console_resolve_ref is web_console.web_console_resolve_ref
    assert app_module.web_console_action_payload is web_console.web_console_action_payload
    assert app_module.web_console_action_message is web_console.web_console_action_message
    assert app_module.web_console_model_name_from_payload is web_console.web_console_model_name_from_payload
    assert app_module.web_console_schedule_control_from_payload is web_console.web_console_schedule_control_from_payload
