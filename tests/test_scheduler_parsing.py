"""Tests for the scheduler cron/interval/timestamp parsers (ga_tui.scheduler).

These cover the pure timing functions: cron field matching, interval parsing,
timestamp normalization, and the due-info decision function.
"""
from __future__ import annotations

import time

import pytest

from ga_tui.scheduler import (
    cron_field_matches,
    cron_matches_now,
    parse_schedule_interval_seconds,
    parse_schedule_timestamp,
    schedule_active,
    schedule_dispatch_contract_for_execution,
    schedule_due_info,
    schedule_execution_error,
    schedule_execution_from_control,
    schedule_record_from_control,
    schedule_record_updates_from_control,
    split_schedule_trigger,
)


class TestCronFieldMatches:
    def test_star_matches_any(self) -> None:
        assert cron_field_matches("*", 5, 0, 59) is True

    def test_single_value(self) -> None:
        assert cron_field_matches("5", 5, 0, 59) is True
        assert cron_field_matches("5", 6, 0, 59) is False

    def test_range(self) -> None:
        assert cron_field_matches("1-5", 3, 0, 59) is True
        assert cron_field_matches("1-5", 6, 0, 59) is False

    def test_list(self) -> None:
        assert cron_field_matches("1,3,5", 3, 0, 59) is True
        assert cron_field_matches("1,3,5", 4, 0, 59) is False

    def test_step(self) -> None:
        assert cron_field_matches("*/15", 0, 0, 59) is True
        assert cron_field_matches("*/15", 15, 0, 59) is True
        assert cron_field_matches("*/15", 30, 0, 59) is True
        assert cron_field_matches("*/15", 7, 0, 59) is False

    def test_range_step(self) -> None:
        assert cron_field_matches("0-30/10", 10, 0, 59) is True
        assert cron_field_matches("0-30/10", 20, 0, 59) is True
        assert cron_field_matches("0-30/10", 35, 0, 59) is False

    def test_empty_returns_false(self) -> None:
        assert cron_field_matches("", 5, 0, 59) is False

    def test_invalid_step_zero(self) -> None:
        assert cron_field_matches("*/0", 5, 0, 59) is False

    def test_weekday_7_normalizes_to_0(self) -> None:
        # Sunday can be 0 or 7 in cron.
        assert cron_field_matches("7", 0, 0, 7, weekday=True) is True

    def test_weekday_wrap_range(self) -> None:
        # 5-2 means Fri-Sun-Mon-Tue (wraps).
        assert cron_field_matches("5-2", 6, 0, 7, weekday=True) is True
        assert cron_field_matches("5-2", 3, 0, 7, weekday=True) is False


class TestCronMatchesNow:
    def test_valid_five_fields(self) -> None:
        ok, err = cron_matches_now("* * * * *", time.time())
        assert ok is True
        assert err == ""

    def test_wrong_field_count(self) -> None:
        ok, err = cron_matches_now("* * *", time.time())
        assert ok is False
        assert "five" in err

    def test_specific_minute_matches(self) -> None:
        # Build a fixed time: 2026-06-23 14:30:00 local -> minute 30.
        t = time.strptime("2026-06-23 14:30:00", "%Y-%m-%d %H:%M:%S")
        epoch = time.mktime(t)
        ok, _ = cron_matches_now("30 * * * *", epoch)
        assert ok is True
        ok, _ = cron_matches_now("31 * * * *", epoch)
        assert ok is False


class TestParseScheduleIntervalSeconds:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("30s", 30.0),
            ("30sec", 30.0),
            ("30seconds", 30.0),
            ("5m", 300.0),
            ("5min", 300.0),
            ("5minutes", 300.0),
            ("2h", 7200.0),
            ("2hours", 7200.0),
            ("1d", 86400.0),
            ("1day", 86400.0),
            ("interval:30s", 30.0),
            ("every 5m", 300.0),
            ("interval=10s", 10.0),
            ("90", 90.0),
        ],
    )
    def test_valid(self, value: str, expected: float) -> None:
        assert parse_schedule_interval_seconds(value) == expected

    def test_empty(self) -> None:
        assert parse_schedule_interval_seconds("") is None

    def test_garbage(self) -> None:
        assert parse_schedule_interval_seconds("not-a-time") is None

    def test_zero_returns_none(self) -> None:
        assert parse_schedule_interval_seconds("0s") is None

    def test_fractional(self) -> None:
        assert parse_schedule_interval_seconds("1.5h") == 5400.0


class TestParseScheduleTimestamp:
    def test_epoch_float(self) -> None:
        assert parse_schedule_timestamp("1700000000") == 1700000000.0

    def test_epoch_int_string(self) -> None:
        assert parse_schedule_timestamp("1700000000") == 1700000000.0

    def test_iso_with_z(self) -> None:
        ts = parse_schedule_timestamp("2026-06-23T14:30:00Z")
        assert ts is not None
        assert ts > 0

    def test_iso_with_offset(self) -> None:
        ts = parse_schedule_timestamp("2026-06-23T14:30:00+08:00")
        assert ts is not None
        assert ts > 0

    def test_date_only(self) -> None:
        ts = parse_schedule_timestamp("2026-06-23")
        assert ts is not None

    def test_empty(self) -> None:
        assert parse_schedule_timestamp("") is None

    def test_garbage(self) -> None:
        assert parse_schedule_timestamp("not-a-date") is None


class TestScheduleActive:
    def test_default_enabled(self) -> None:
        assert schedule_active({}) is True

    def test_enabled(self) -> None:
        assert schedule_active({"status": "enabled"}) is True

    def test_disabled(self) -> None:
        assert schedule_active({"status": "disabled"}) is False

    def test_deleted(self) -> None:
        assert schedule_active({"status": "deleted"}) is False

    def test_cancelled_variants(self) -> None:
        assert schedule_active({"status": "cancelled"}) is False
        assert schedule_active({"status": "canceled"}) is False

    def test_case_insensitive(self) -> None:
        assert schedule_active({"status": "DISABLED"}) is False


class TestSplitScheduleTrigger:
    def test_interval_prefix(self) -> None:
        kind, value = split_schedule_trigger({"trigger": "interval:30s"})
        assert kind == "interval"
        assert value == "30s"

    def test_cron_prefix(self) -> None:
        kind, value = split_schedule_trigger({"trigger": "cron:*/5 * * * *"})
        assert kind == "cron"

    def test_at_prefix(self) -> None:
        kind, value = split_schedule_trigger({"trigger": "at:2026-06-23T14:30:00Z"})
        assert kind == "at"

    def test_field_fallback_interval(self) -> None:
        kind, value = split_schedule_trigger({"interval": "5m"})
        assert kind == "interval"
        assert value == "5m"

    def test_field_fallback_cron(self) -> None:
        kind, _ = split_schedule_trigger({"cron": "0 * * * *"})
        assert kind == "cron"

    def test_field_fallback_at(self) -> None:
        kind, _ = split_schedule_trigger({"at": "2026-06-23"})
        assert kind == "at"

    def test_unknown_when_empty(self) -> None:
        kind, _ = split_schedule_trigger({})
        assert kind == "unknown"


class TestScheduleDueInfo:
    def test_missing_schedule_id_invalid(self) -> None:
        info = schedule_due_info({}, now_epoch=1000)
        assert info["status"] == "invalid"
        assert info["due"] is False

    def test_disabled_schedule_skipped(self) -> None:
        info = schedule_due_info({"schedule_id": "s1", "status": "disabled"}, now_epoch=1000)
        assert info["status"] == "skipped"

    def test_at_trigger_due(self) -> None:
        info = schedule_due_info(
            {"schedule_id": "s1", "trigger": "at:1000"},
            now_epoch=1001,
            seen_keys=set(),
        )
        assert info["due"] is True
        assert info["status"] == "due"
        assert info["idempotency_key"] == "s1:at:1000"

    def test_at_trigger_not_yet(self) -> None:
        info = schedule_due_info(
            {"schedule_id": "s1", "trigger": "at:2000"},
            now_epoch=1000,
            seen_keys=set(),
        )
        assert info["due"] is False
        assert info["status"] == "pending"

    def test_at_trigger_duplicate(self) -> None:
        info = schedule_due_info(
            {"schedule_id": "s1", "trigger": "at:1000"},
            now_epoch=1001,
            seen_keys={"s1:at:1000"},
        )
        assert info["status"] == "duplicate"
        assert info["due"] is False

    def test_interval_trigger_due(self) -> None:
        row = {
            "schedule_id": "s1",
            "trigger": "interval:100s",
            "created_at": "1000",
        }
        info = schedule_due_info(row, now_epoch=1101, last_run=None, seen_keys=set())
        assert info["due"] is True

    def test_interval_trigger_not_yet(self) -> None:
        row = {
            "schedule_id": "s1",
            "trigger": "interval:500s",
            "created_at": "1000",
        }
        info = schedule_due_info(row, now_epoch=1100, last_run=None, seen_keys=set())
        assert info["due"] is False

    def test_invalid_at_trigger(self) -> None:
        info = schedule_due_info(
            {"schedule_id": "s1", "trigger": "at:not-a-date"},
            now_epoch=1000,
        )
        assert info["status"] == "invalid"

    def test_invalid_interval_trigger(self) -> None:
        info = schedule_due_info(
            {"schedule_id": "s1", "trigger": "interval:garbage"},
            now_epoch=1000,
        )
        assert info["status"] == "invalid"

    def test_unsupported_trigger(self) -> None:
        info = schedule_due_info({"schedule_id": "s1"}, now_epoch=1000)
        assert info["status"] == "invalid"
        assert "unsupported" in info["reason"]


class TestWorkflowRunExecution:
    def test_workflow_run_execution_parses_ref_and_inputs(self) -> None:
        execution = schedule_execution_from_control({
            "execution": {
                "mode": "workflow-run",
                "workflow_ref": "research-pack/compare-sources",
                "inputs": {"topic": "workflow"},
            }
        })

        assert execution == {
            "mode": "workflow_run",
            "workflow_ref": "research-pack/compare-sources",
            "inputs": {"topic": "workflow"},
        }
        assert schedule_execution_error(execution) == ""
        assert schedule_dispatch_contract_for_execution(execution) == "workflow_run.v1"

    def test_workflow_run_execution_requires_ref(self) -> None:
        execution = schedule_execution_from_control({"execution": {"mode": "workflow_run"}})

        assert execution["mode"] == "workflow_run"
        assert schedule_execution_error(execution) == "schedule execution missing workflow_ref."

    def test_workflow_run_schedule_record_uses_workflow_dispatch_contract(self) -> None:
        record = schedule_record_from_control(
            {
                "name": "Run Compare Sources",
                "interval": "1h",
                "execution": {
                    "mode": "workflow_run",
                    "workflow_ref": "research-pack/compare-sources",
                    "inputs": {"topic": "daily"},
                },
            },
            schedule_id="sched_workflow",
            status="enabled",
            source="test",
        )

        assert record["dispatch_contract"] == "workflow_run.v1"
        assert record["target"] == ""
        assert record["execution"]["workflow_ref"] == "research-pack/compare-sources"
        assert record["execution"]["inputs"] == {"topic": "daily"}

    def test_workflow_run_schedule_update_preserves_contract(self) -> None:
        updates = schedule_record_updates_from_control(
            {
                "execution": {
                    "mode": "workflow_run",
                    "workflow_ref": "research-pack/compare-sources",
                }
            },
            source="test",
        )

        assert updates["dispatch_contract"] == "workflow_run.v1"
        assert updates["target"] == ""
        assert updates["execution"]["inputs"] == {}
