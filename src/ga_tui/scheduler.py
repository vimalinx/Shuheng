"""TUI-owned scheduled task registry and dispatch helpers."""
from __future__ import annotations

import hashlib
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

try:
    from .control_protocol import AGENT_TASK_SCHEMA, execution_control_from_v2
except Exception:
    from control_protocol import AGENT_TASK_SCHEMA, execution_control_from_v2  # type: ignore


SCHEDULE_RUN_ATTEMPT_STATUSES = {"starting", "dispatched", "queued", "approval_required", "failed", "rejected"}
try:
    SCHEDULER_TICK_SECONDS = max(5.0, float(os.environ.get("GA_TUI_SCHEDULER_TICK_SECONDS", "30") or "30"))
except ValueError:
    SCHEDULER_TICK_SECONDS = 30.0


@dataclass
class SchedulerDispatchResult:
    status: str
    message: str
    task_id: str = ""
    approval_id: str = ""
    error: str = ""
    provider_id: str = ""


@dataclass
class SchedulerRuntime:
    schedules_path: str = ""
    runs_path: str = ""
    task_ledger_path: str = ""
    agent_mail_path: str = ""
    read_jsonl: Optional[Callable[[str, int], list[dict[str, Any]]]] = None
    append_jsonl: Optional[Callable[[str, dict[str, Any]], None]] = None
    now_iso: Callable[[], str] = lambda: time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
    json_safe: Callable[[Any], Any] = lambda value: _json_safe(value)
    default_provider_id: Callable[[], str] = lambda: "ohmypi"
    truncate_cells: Callable[[str, int], str] = lambda text, width: str(text or "")[: max(0, width)]
    emit_tui_beep: Optional[Callable[[], str]] = None
    resolve_subagent: Optional[Callable[[Any, str], Any]] = None
    dispatch_subagent_task: Optional[Callable[[Any, Any, dict[str, Any], str, str, dict[str, Any]], SchedulerDispatchResult]] = None


_runtime = SchedulerRuntime()


def configure_scheduler_runtime(**kwargs: Any) -> None:
    for key, value in kwargs.items():
        if not hasattr(_runtime, key):
            raise TypeError(f"unknown scheduler runtime option: {key}")
        setattr(_runtime, key, value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _read_jsonl(path: str, limit: int = 0) -> list[dict[str, Any]]:
    if _runtime.read_jsonl is None:
        raise RuntimeError("scheduler runtime read_jsonl is not configured")
    return _runtime.read_jsonl(path, limit)


def _append_jsonl(path: str, payload: dict[str, Any]) -> None:
    if _runtime.append_jsonl is None:
        raise RuntimeError("scheduler runtime append_jsonl is not configured")
    _runtime.append_jsonl(path, payload)


def _now_iso() -> str:
    return _runtime.now_iso()


def _short_uid(prefix: str) -> str:
    return f"{prefix}_{time.time_ns():x}_{os.getpid():x}"


def _schedules_path() -> str:
    if not _runtime.schedules_path:
        raise RuntimeError("scheduler runtime schedules_path is not configured")
    return _runtime.schedules_path


def _runs_path() -> str:
    if not _runtime.runs_path:
        raise RuntimeError("scheduler runtime runs_path is not configured")
    return _runtime.runs_path


def scheduled_task_registry(state: Optional[Any] = None) -> dict[str, Any]:
    del state
    run_rows = latest_schedule_run_records()
    last_runs = latest_schedule_runs_by_schedule_id()
    last_attempts = latest_schedule_attempt_runs_by_schedule_id()
    seen_keys = {str(row.get("idempotency_key") or "").strip() for row in run_rows if row.get("idempotency_key")}
    jobs = []
    for row in latest_schedule_records().values():
        job = dict(row)
        schedule_id = str(job.get("schedule_id") or "")
        due = schedule_due_info(job, last_run=last_attempts.get(schedule_id), seen_keys=seen_keys)
        job["scheduler"] = {
            "due": bool(due.get("due")),
            "status": due.get("status", ""),
            "reason": due.get("reason", ""),
            "trigger_kind": due.get("trigger_kind", ""),
            "due_at": due.get("due_at", ""),
            "idempotency_key": due.get("idempotency_key", ""),
            "last_run": last_runs.get(schedule_id) or {},
            "last_attempt": last_attempts.get(schedule_id) or {},
        }
        jobs.append(job)
    jobs.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""))
    active_jobs = [
        row for row in jobs
        if str(row.get("status") or "enabled").lower() not in {"disabled", "deleted", "cancelled", "canceled"}
    ]
    return {
        "schema_version": "scheduledtask.registry.v1",
        "owner": "ga-tui.control_plane",
        "status": "registry_ready",
        "schedules_path": _runtime.schedules_path,
        "runs_path": _runtime.runs_path,
        "job_count": len(jobs),
        "active_job_count": len(active_jobs),
        "run_count": len(run_rows),
        "jobs": jobs[-50:],
        "dispatch": {
            "contract": "agenttask.v2",
            "runtime_provider_selection": "explicit provider_id or registry default",
            "task_ledger": _runtime.task_ledger_path,
            "agent_mail": _runtime.agent_mail_path,
            "artifact_policy": "artifact_refs_required",
        },
        "capabilities": {
            "register_recurring_jobs": True,
            "dispatch_to_runtime_provider": True,
            "audit_each_run": True,
            "approval_gates_before_risky_runs": True,
        },
    }


def latest_schedule_records() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(_schedules_path(), limit=500):
        schedule_id = str(row.get("schedule_id") or row.get("id") or "").strip()
        if not schedule_id:
            continue
        records[schedule_id] = row
    return records


def append_schedule_record(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload.setdefault("schema_version", "scheduledtask.v1")
    payload.setdefault("updated_at", _now_iso())
    _append_jsonl(_schedules_path(), payload)
    return payload


def latest_schedule_run_records(limit: int = 1000) -> list[dict[str, Any]]:
    return _read_jsonl(_runs_path(), limit=limit)


def latest_schedule_runs_by_schedule_id(limit: int = 1000, statuses: Optional[set[str]] = None) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    allowed = {str(item).strip().lower() for item in statuses} if statuses is not None else None
    for row in latest_schedule_run_records(limit=limit):
        status = str(row.get("status") or "").strip().lower()
        if allowed is not None and status not in allowed:
            continue
        schedule_id = str(row.get("schedule_id") or "").strip()
        if schedule_id:
            latest[schedule_id] = row
    return latest


def latest_schedule_attempt_runs_by_schedule_id(limit: int = 1000) -> dict[str, dict[str, Any]]:
    return latest_schedule_runs_by_schedule_id(limit=limit, statuses=SCHEDULE_RUN_ATTEMPT_STATUSES)


def schedule_run_idempotency_keys(limit: int = 2000) -> set[str]:
    keys: set[str] = set()
    for row in latest_schedule_run_records(limit=limit):
        key = str(row.get("idempotency_key") or "").strip()
        if key:
            keys.add(key)
    return keys


def append_schedule_run(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload.setdefault("schema_version", "scheduledtask.run.v1")
    payload.setdefault("run_id", _short_uid("schedrun"))
    payload.setdefault("timestamp", _now_iso())
    _append_jsonl(_runs_path(), payload)
    return payload


def schedule_record_trigger(row: dict[str, Any]) -> str:
    for key in ("cron", "interval", "at", "trigger"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def parse_schedule_timestamp(value: Any) -> Optional[float]:
    text = str(value or "").strip()
    if not text:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        try:
            return float(text)
        except ValueError:
            return None
    normalized = text.replace("Z", "+00:00")
    if re.search(r"[+-]\d{4}$", normalized):
        normalized = normalized[:-5] + normalized[-5:-2] + ":" + normalized[-2:]
    for candidate in (normalized, normalized.replace(" ", "T", 1)):
        try:
            return datetime.fromisoformat(candidate).timestamp()
        except ValueError:
            pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return time.mktime(time.strptime(text, fmt))
        except ValueError:
            pass
    return None


def parse_schedule_interval_seconds(value: Any) -> Optional[float]:
    text = str(value or "").strip().lower()
    if not text:
        return None
    text = re.sub(r"^(interval|every)\s*[:=]?\s*", "", text).strip()
    match = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days)?",
        text,
    )
    if not match:
        return None
    amount = float(match.group(1))
    unit = match.group(2) or "s"
    factor = 1.0
    if unit.startswith("m"):
        factor = 60.0
    elif unit.startswith("h") or unit in {"hr", "hrs"}:
        factor = 3600.0
    elif unit.startswith("d"):
        factor = 86400.0
    seconds = amount * factor
    return seconds if seconds > 0 else None


def split_schedule_trigger(row: dict[str, Any]) -> tuple[str, str]:
    trigger = schedule_record_trigger(row)
    lowered = trigger.lower().strip()
    for prefix in ("interval", "cron", "at"):
        for sep in (":", "="):
            marker = prefix + sep
            if lowered.startswith(marker):
                return prefix, trigger[len(marker):].strip()
        if lowered.startswith(prefix + " "):
            return prefix, trigger[len(prefix):].strip()
    if row.get("interval"):
        return "interval", str(row.get("interval") or "").strip()
    if row.get("cron"):
        return "cron", str(row.get("cron") or "").strip()
    if row.get("at"):
        return "at", str(row.get("at") or "").strip()
    return "unknown", trigger


def cron_field_matches(expr: str, value: int, minimum: int, maximum: int, *, weekday: bool = False) -> bool:
    expr = (expr or "").strip()
    if not expr:
        return False
    for part in expr.split(","):
        part = part.strip()
        if not part:
            continue
        step = 1
        if "/" in part:
            part, step_text = part.split("/", 1)
            if not step_text.isdigit() or int(step_text) <= 0:
                return False
            step = int(step_text)
        if part in {"", "*"}:
            start, end = minimum, maximum
        elif "-" in part:
            start_text, end_text = part.split("-", 1)
            if not start_text.isdigit() or not end_text.isdigit():
                return False
            start, end = int(start_text), int(end_text)
        elif part.isdigit():
            start = end = int(part)
        else:
            return False
        if weekday:
            if start == 7:
                start = 0
            if end == 7:
                end = 0
            if start > end:
                values = list(range(start, maximum + 1)) + list(range(minimum, end + 1))
            else:
                values = list(range(start, end + 1))
            if value in values and ((value - values[0]) % step == 0):
                return True
            continue
        if start < minimum or end > maximum or start > end:
            return False
        if start <= value <= end and ((value - start) % step == 0):
            return True
    return False


def cron_matches_now(expr: str, now_epoch: float) -> tuple[bool, str]:
    fields = (expr or "").split()
    if len(fields) != 5:
        return False, "cron must contain five fields"
    current = time.localtime(now_epoch)
    cron_weekday = (current.tm_wday + 1) % 7
    checks = [
        cron_field_matches(fields[0], current.tm_min, 0, 59),
        cron_field_matches(fields[1], current.tm_hour, 0, 23),
        cron_field_matches(fields[2], current.tm_mday, 1, 31),
        cron_field_matches(fields[3], current.tm_mon, 1, 12),
        cron_field_matches(fields[4], cron_weekday, 0, 7, weekday=True),
    ]
    return all(checks), ""


def schedule_active(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "enabled").strip().lower()
    return status not in {"disabled", "deleted", "cancelled", "canceled"}


def schedule_due_info(
    row: dict[str, Any],
    *,
    now_epoch: Optional[float] = None,
    last_run: Optional[dict[str, Any]] = None,
    seen_keys: Optional[set[str]] = None,
) -> dict[str, Any]:
    now_epoch = time.time() if now_epoch is None else float(now_epoch)
    schedule_id = str(row.get("schedule_id") or row.get("id") or "").strip()
    status = str(row.get("status") or "enabled").strip().lower()
    trigger_kind, trigger_value = split_schedule_trigger(row)
    info: dict[str, Any] = {
        "schedule_id": schedule_id,
        "status": "pending",
        "due": False,
        "trigger_kind": trigger_kind,
        "trigger": trigger_value,
        "reason": "",
        "due_at_epoch": None,
        "due_at": "",
        "idempotency_key": "",
    }
    if not schedule_id:
        info.update(status="invalid", reason="missing schedule_id")
        return info
    if not schedule_active(row):
        info.update(status="skipped", reason=f"schedule status is {status or 'inactive'}")
        return info
    keys = seen_keys if seen_keys is not None else schedule_run_idempotency_keys()
    if trigger_kind == "at":
        due_epoch = parse_schedule_timestamp(trigger_value)
        if due_epoch is None:
            info.update(status="invalid", reason=f"invalid at trigger: {trigger_value}")
            return info
        key = f"{schedule_id}:at:{int(due_epoch)}"
        info.update(due_at_epoch=due_epoch, due_at=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(due_epoch)), idempotency_key=key)
        if key in keys:
            info.update(status="duplicate", reason="one-shot schedule already ran")
            return info
        if now_epoch >= due_epoch:
            info.update(status="due", due=True, reason="at trigger reached")
        else:
            info.update(status="pending", reason="at trigger not reached")
        return info
    if trigger_kind == "interval":
        seconds = parse_schedule_interval_seconds(trigger_value)
        if seconds is None:
            info.update(status="invalid", reason=f"invalid interval trigger: {trigger_value}")
            return info
        last_epoch = parse_schedule_timestamp((last_run or {}).get("timestamp") or (last_run or {}).get("started_at"))
        anchor_epoch = last_epoch or parse_schedule_timestamp(row.get("created_at")) or parse_schedule_timestamp(row.get("updated_at")) or now_epoch
        due_epoch = anchor_epoch + seconds
        key = f"{schedule_id}:interval:{int(due_epoch)}"
        info.update(due_at_epoch=due_epoch, due_at=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(due_epoch)), idempotency_key=key)
        if key in keys:
            info.update(status="duplicate", reason="interval slot already ran")
            return info
        if now_epoch >= due_epoch:
            info.update(status="due", due=True, reason="interval elapsed")
        else:
            info.update(status="pending", reason="interval not elapsed")
        return info
    if trigger_kind == "cron":
        matched, error = cron_matches_now(trigger_value, now_epoch)
        if error:
            info.update(status="invalid", reason=error)
            return info
        due_epoch = int(now_epoch // 60) * 60
        key = f"{schedule_id}:cron:{time.strftime('%Y%m%d%H%M', time.localtime(due_epoch))}"
        info.update(due_at_epoch=due_epoch, due_at=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(due_epoch)), idempotency_key=key)
        if key in keys:
            info.update(status="duplicate", reason="cron minute already ran")
            return info
        if matched:
            info.update(status="due", due=True, reason="cron matched current minute")
        else:
            info.update(status="pending", reason="cron does not match current minute")
        return info
    info.update(status="invalid", reason=f"unsupported trigger: {schedule_record_trigger(row) or '-'}")
    return info


def schedule_trigger_from_control(control: dict[str, Any]) -> str:
    for key in ("cron", "interval", "trigger", "at"):
        value = str(control.get(key) or "").strip()
        if value:
            return value
    return ""


def schedule_execution_from_control(control: dict[str, Any]) -> dict[str, Any]:
    raw = control.get("execution") if isinstance(control.get("execution"), dict) else {}
    mode = str(raw.get("mode") or "").strip().lower().replace("-", "_")
    if mode == "tui_action":
        action = str(raw.get("action") or "").strip().lower().replace("-", "_")
        execution: dict[str, Any] = {"mode": "tui_action", "action": action}
        message = str(raw.get("message") or "").strip()
        if message:
            execution["message"] = message
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        if payload:
            execution["payload"] = _runtime.json_safe(payload)
        return execution
    if mode == "agent_task":
        return {
            "mode": "agent_task",
            "routing": raw.get("routing") if isinstance(raw.get("routing"), dict) else {},
            "work_order": raw.get("work_order") if isinstance(raw.get("work_order"), dict) else {},
            "capability_contract": raw.get("capability_contract") if isinstance(raw.get("capability_contract"), dict) else {},
            "context_contract": raw.get("context_contract") if isinstance(raw.get("context_contract"), dict) else {},
            "output_contract": raw.get("output_contract") if isinstance(raw.get("output_contract"), dict) else {},
        }
    return {}


def schedule_execution_target(execution: dict[str, Any]) -> str:
    routing = execution.get("routing") if isinstance(execution.get("routing"), dict) else {}
    selector = routing.get("target_selector") if isinstance(routing.get("target_selector"), dict) else {}
    return str(
        routing.get("selected_agent")
        or selector.get("agent_id")
        or selector.get("target")
        or selector.get("name")
        or ""
    ).strip()


def schedule_execution_error(execution: dict[str, Any]) -> str:
    mode = str(execution.get("mode") or "").strip().lower()
    if mode == "tui_action":
        action = str(execution.get("action") or "").strip().lower()
        if action == "beep":
            return ""
        return "schedule execution action is unsupported."
    if mode == "agent_task":
        work_order = execution.get("work_order") if isinstance(execution.get("work_order"), dict) else {}
        if not str(work_order.get("objective") or "").strip():
            return "schedule execution missing work_order.objective."
        if not schedule_execution_target(execution):
            return "schedule execution missing routing.selected_agent."
        return ""
    return "schedule execution mode is required."


def schedule_record_from_control(control: dict[str, Any], *, schedule_id: str, status: str, source: str) -> dict[str, Any]:
    provider_id = str(control.get("provider_id") or control.get("runtime_provider_id") or "").strip()
    execution = schedule_execution_from_control(control)
    target = schedule_execution_target(execution)
    mode = str(execution.get("mode") or "").strip().lower()
    dispatch_contract = "tui_action.v1" if mode == "tui_action" else "agenttask.v2"
    record = {
        "schema_version": "scheduledtask.v1",
        "schedule_id": schedule_id,
        "name": str(control.get("name") or control.get("title") or schedule_id).strip(),
        "status": status,
        "trigger": schedule_trigger_from_control(control),
        "timezone": str(control.get("timezone") or control.get("tz") or "").strip(),
        "provider_id": provider_id or _runtime.default_provider_id(),
        "dispatch_contract": dispatch_contract,
        "execution": _runtime.json_safe(execution),
        "target": target,
        "created_at": str(control.get("created_at") or _now_iso()),
        "updated_at": _now_iso(),
        "source": source,
    }
    for key in ("cron", "interval", "at"):
        value = str(control.get(key) or "").strip()
        if value:
            record[key] = value
    return record


def schedule_record_updates_from_control(control: dict[str, Any], *, source: str) -> dict[str, Any]:
    updates: dict[str, Any] = {"updated_at": _now_iso(), "source": source}
    name = str(control.get("name") or control.get("title") or "").strip()
    if name:
        updates["name"] = name
    status = str(control.get("status") or "").strip()
    if status:
        updates["status"] = status
    if "timezone" in control or "tz" in control:
        updates["timezone"] = str(control.get("timezone") or control.get("tz") or "").strip()
    if "provider_id" in control or "runtime_provider_id" in control:
        provider_id = str(control.get("provider_id") or control.get("runtime_provider_id") or "").strip()
        if provider_id:
            updates["provider_id"] = provider_id
    if schedule_trigger_from_control(control):
        for key in ("cron", "interval", "at", "trigger"):
            updates[key] = ""
        updates["trigger"] = schedule_trigger_from_control(control)
        for key in ("cron", "interval", "at"):
            value = str(control.get(key) or "").strip()
            if value:
                updates[key] = value
    if isinstance(control.get("execution"), dict):
        execution = schedule_execution_from_control(control)
        mode = str(execution.get("mode") or "").strip().lower()
        updates["execution"] = _runtime.json_safe(execution)
        updates["target"] = schedule_execution_target(execution)
        updates["dispatch_contract"] = "tui_action.v1" if mode == "tui_action" else "agenttask.v2"
    return updates


def apply_schedule_control(state: Any, action: str, target: str, value: str, control: dict[str, Any], source: str = "agent") -> Optional[str]:
    del state, value
    action = (action or "").strip().lower().replace("-", "_")
    if action not in {"schedule_create", "schedule_update", "schedule_enable", "schedule_disable", "schedule_delete"}:
        return None
    records = latest_schedule_records()
    if action == "schedule_create":
        schedule_id = str(control.get("schedule_id") or control.get("id") or _short_uid("sched")).strip()
        trigger = schedule_trigger_from_control(control)
        if not trigger:
            return "缺少 schedule 触发器：需要 cron、interval、trigger 或 at。"
        row = schedule_record_from_control(control, schedule_id=schedule_id, status=str(control.get("status") or "enabled"), source=source)
        execution_error = schedule_execution_error(row.get("execution") if isinstance(row.get("execution"), dict) else {})
        if execution_error:
            return execution_error
        append_schedule_record(row)
        return f"已登记定时任务：{row['name']} ({schedule_id}) · {trigger}"
    schedule_id = str(target or control.get("schedule_id") or control.get("id") or "").strip()
    if not schedule_id:
        return "缺少 schedule target。"
    existing = records.get(schedule_id)
    if existing is None:
        return f"找不到定时任务：{schedule_id}"
    if action == "schedule_update":
        row = dict(existing)
        row.update(schedule_record_updates_from_control(control, source=source))
        row["created_at"] = existing.get("created_at") or row.get("created_at") or _now_iso()
        row["updated_at"] = _now_iso()
        execution_error = schedule_execution_error(row.get("execution") if isinstance(row.get("execution"), dict) else {})
        if execution_error:
            return execution_error
        append_schedule_record(row)
        return f"已更新定时任务：{row.get('name') or schedule_id}"
    status = {
        "schedule_enable": "enabled",
        "schedule_disable": "disabled",
        "schedule_delete": "deleted",
    }[action]
    row = dict(existing)
    row["status"] = status
    row["updated_at"] = _now_iso()
    row["source"] = source
    append_schedule_record(row)
    label = {"enabled": "启用", "disabled": "停用", "deleted": "删除"}[status]
    return f"已{label}定时任务：{row.get('name') or schedule_id}"


def schedule_agenttask_control(row: dict[str, Any]) -> dict[str, Any]:
    execution = row.get("execution") if isinstance(row.get("execution"), dict) else {}
    work_order = execution.get("work_order") if isinstance(execution.get("work_order"), dict) else {}
    routing = execution.get("routing") if isinstance(execution.get("routing"), dict) else {}
    routing = dict(routing)
    target = str(row.get("target") or "").strip()
    if target and not routing.get("selected_agent"):
        routing["selected_agent"] = target
    return {
        "schema_version": AGENT_TASK_SCHEMA,
        "action": "delegate.create",
        "parent_task_id": str(row.get("parent_task_id") or row.get("task_id") or ""),
        "routing": routing,
        "work_order": work_order,
        "capability_contract": execution.get("capability_contract") if isinstance(execution.get("capability_contract"), dict) else {},
        "context_contract": execution.get("context_contract") if isinstance(execution.get("context_contract"), dict) else {},
        "output_contract": execution.get("output_contract") if isinstance(execution.get("output_contract"), dict) else {},
        "task_title": str(row.get("name") or row.get("title") or row.get("schedule_id") or "Scheduled task"),
        "schedule_id": str(row.get("schedule_id") or ""),
        "provider_id": str(row.get("provider_id") or _runtime.default_provider_id() or "ohmypi"),
    }


def update_schedule_last_run(row: dict[str, Any], run: dict[str, Any]) -> None:
    schedule = dict(row)
    schedule.pop("scheduler", None)
    schedule["last_run_id"] = run.get("run_id", "")
    schedule["last_run_status"] = run.get("status", "")
    schedule["last_run_at"] = run.get("timestamp") or _now_iso()
    schedule["last_idempotency_key"] = run.get("idempotency_key", "")
    schedule["updated_at"] = _now_iso()
    append_schedule_record(schedule)


def append_schedule_skip_run(row: dict[str, Any], info: dict[str, Any], *, status: str, reason: str) -> dict[str, Any]:
    schedule_id = str(row.get("schedule_id") or row.get("id") or "").strip()
    trigger = schedule_record_trigger(row)
    base_key = info.get("idempotency_key") or f"{schedule_id}:{status}:{hashlib.sha1((trigger + reason).encode('utf-8')).hexdigest()[:16]}"
    key = f"{base_key}:{status}"
    if key in schedule_run_idempotency_keys():
        return {}
    run = append_schedule_run({
        "schedule_id": schedule_id,
        "schedule_name": row.get("name") or schedule_id,
        "status": status,
        "reason": reason,
        "trigger": trigger,
        "trigger_kind": info.get("trigger_kind", ""),
        "due_at": info.get("due_at", ""),
        "idempotency_key": key,
        "provider_id": row.get("provider_id", ""),
        "dispatch_contract": row.get("dispatch_contract") or "agenttask.v2",
    })
    update_schedule_last_run(row, run)
    return run


def dispatch_schedule_tui_action(row: dict[str, Any], started: dict[str, Any]) -> Optional[dict[str, Any]]:
    execution = row.get("execution") if isinstance(row.get("execution"), dict) else {}
    if str(execution.get("mode") or "").strip().lower() != "tui_action":
        return None
    action_type = str(execution.get("action") or "").strip().lower().replace("-", "_")
    if action_type == "beep":
        result = _runtime.emit_tui_beep() if _runtime.emit_tui_beep is not None else "beep failed: scheduler beep callback is not configured"
        status = "completed" if "failed" not in result.lower() else "failed"
        finished = dict(started)
        finished.update({
            "status": status,
            "finished_at": _now_iso(),
            "execution": _runtime.json_safe(execution),
            "result": result,
        })
        if status == "failed":
            finished["error"] = result
        append_schedule_run(finished)
        update_schedule_last_run(row, finished)
        return finished
    finished = dict(started)
    finished.update({
        "status": "failed",
        "finished_at": _now_iso(),
        "execution": _runtime.json_safe(execution),
        "error": f"unsupported schedule execution action: {action_type or '-'}",
    })
    append_schedule_run(finished)
    update_schedule_last_run(row, finished)
    return finished


def dispatch_schedule_run(state: Any, row: dict[str, Any], info: dict[str, Any], *, source: str = "scheduler") -> dict[str, Any]:
    schedule_id = str(row.get("schedule_id") or row.get("id") or "").strip()
    idempotency_key = str(info.get("idempotency_key") or "").strip()
    provider_id = str(row.get("provider_id") or _runtime.default_provider_id() or "ohmypi").strip()
    if not schedule_id:
        return append_schedule_run({"status": "failed", "reason": "missing schedule_id", "idempotency_key": idempotency_key})
    if idempotency_key and idempotency_key in schedule_run_idempotency_keys():
        return append_schedule_skip_run(row, info, status="duplicate", reason="idempotency key already exists")
    run_id = _short_uid("schedrun")
    started = append_schedule_run({
        "run_id": run_id,
        "schedule_id": schedule_id,
        "schedule_name": row.get("name") or schedule_id,
        "status": "starting",
        "reason": info.get("reason", ""),
        "trigger": schedule_record_trigger(row),
        "trigger_kind": info.get("trigger_kind", ""),
        "due_at": info.get("due_at", ""),
        "idempotency_key": idempotency_key,
        "provider_id": provider_id,
        "dispatch_contract": row.get("dispatch_contract") or "agenttask.v2",
        "source": source,
    })
    tui_action_run = dispatch_schedule_tui_action(row, started)
    if tui_action_run is not None:
        return tui_action_run
    execution = row.get("execution") if isinstance(row.get("execution"), dict) else {}
    execution_error = schedule_execution_error(execution)
    if execution_error:
        finished = dict(started)
        finished.update({"status": "failed", "finished_at": _now_iso(), "error": execution_error})
        append_schedule_run(finished)
        update_schedule_last_run(row, finished)
        return finished
    control = schedule_agenttask_control(row)
    work_order = control.get("work_order") if isinstance(control.get("work_order"), dict) else {}
    if not str(work_order.get("objective") or "").strip():
        finished = dict(started)
        finished.update({"status": "failed", "finished_at": _now_iso(), "error": "missing work_order.objective"})
        append_schedule_run(finished)
        update_schedule_last_run(row, finished)
        return finished
    mapped = execution_control_from_v2(control)
    if not mapped:
        finished = dict(started)
        finished.update({"status": "failed", "finished_at": _now_iso(), "error": "could not map schedule to agenttask.v2 delegate.create"})
        append_schedule_run(finished)
        update_schedule_last_run(row, finished)
        return finished
    target = str(mapped.get("target") or "").strip()
    if not target:
        finished = dict(started)
        finished.update({"status": "failed", "finished_at": _now_iso(), "error": "missing routing.selected_agent or schedule target"})
        append_schedule_run(finished)
        update_schedule_last_run(row, finished)
        return finished
    if _runtime.resolve_subagent is None:
        finished = dict(started)
        finished.update({"status": "failed", "finished_at": _now_iso(), "target": target, "error": "scheduler resolve_subagent callback is not configured"})
        append_schedule_run(finished)
        update_schedule_last_run(row, finished)
        return finished
    sub = _runtime.resolve_subagent(state, target)
    if sub is None:
        finished = dict(started)
        finished.update({"status": "failed", "finished_at": _now_iso(), "target": target, "error": f"subagent not found: {target}"})
        append_schedule_run(finished)
        update_schedule_last_run(row, finished)
        return finished
    if _runtime.dispatch_subagent_task is None:
        dispatch = SchedulerDispatchResult(status="failed", message="scheduler dispatch_subagent_task callback is not configured", error="scheduler dispatch_subagent_task callback is not configured")
    else:
        try:
            dispatch = _runtime.dispatch_subagent_task(state, sub, mapped, source, schedule_id, row)
        except Exception as exc:
            dispatch = SchedulerDispatchResult(status="failed", message=f"{type(exc).__name__}: {exc}", error=f"{type(exc).__name__}: {exc}")
    finished = dict(started)
    finished.update({
        "status": dispatch.status,
        "finished_at": _now_iso(),
        "target": getattr(sub, "agent_id", target),
        "target_name": getattr(sub, "name", target),
        "result": dispatch.message,
        "task_id": dispatch.task_id,
        "runtime_provider_id": dispatch.provider_id or provider_id,
    })
    if dispatch.approval_id:
        finished["approval_id"] = dispatch.approval_id
    if dispatch.status in {"failed", "rejected"}:
        finished["error"] = dispatch.error or dispatch.message
    append_schedule_run(finished)
    update_schedule_last_run(row, finished)
    return finished


def scheduler_tick(
    state: Any,
    *,
    now_epoch: Optional[float] = None,
    source: str = "scheduler",
    target_schedule_id: str = "",
    force: bool = False,
    record_skips: bool = False,
) -> dict[str, Any]:
    now_epoch = time.time() if now_epoch is None else float(now_epoch)
    records = latest_schedule_records()
    last_runs = latest_schedule_attempt_runs_by_schedule_id()
    seen_keys = schedule_run_idempotency_keys()
    result = {
        "schema_version": "scheduledtask.tick.v1",
        "timestamp": _now_iso(),
        "source": source,
        "checked": 0,
        "due": 0,
        "dispatched": 0,
        "failed": 0,
        "skipped": 0,
        "invalid": 0,
        "duplicates": 0,
        "runs": [],
    }
    for schedule_id, row in sorted(records.items(), key=lambda item: str(item[1].get("updated_at") or item[1].get("created_at") or "")):
        if target_schedule_id and schedule_id != target_schedule_id:
            continue
        result["checked"] += 1
        info = schedule_due_info(row, now_epoch=now_epoch, last_run=last_runs.get(schedule_id), seen_keys=seen_keys)
        if force and schedule_active(row):
            info.update(
                status="due",
                due=True,
                reason="manual scheduler run",
                due_at_epoch=now_epoch,
                due_at=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now_epoch)),
                idempotency_key=f"{schedule_id}:manual:{int(now_epoch)}:{time.time_ns()}",
            )
        status = str(info.get("status") or "")
        if info.get("due"):
            result["due"] += 1
            run = dispatch_schedule_run(state, row, info, source=source)
            if run:
                result["runs"].append(run)
                seen_keys.add(str(run.get("idempotency_key") or ""))
            if str(run.get("status") or "") in {"failed", "rejected"}:
                result["failed"] += 1
            else:
                result["dispatched"] += 1
            continue
        if status == "invalid":
            result["invalid"] += 1
            trigger_hash = hashlib.sha1(schedule_record_trigger(row).encode("utf-8")).hexdigest()[:16]
            invalid_key = f"{schedule_id}:invalid:{trigger_hash}"
            if invalid_key not in seen_keys:
                run = append_schedule_skip_run(row, {**info, "idempotency_key": invalid_key}, status="invalid", reason=str(info.get("reason") or "invalid schedule"))
                if run:
                    result["runs"].append(run)
                    seen_keys.add(str(run.get("idempotency_key") or ""))
            continue
        if status == "duplicate":
            result["duplicates"] += 1
            if record_skips:
                run = append_schedule_skip_run(row, info, status="duplicate", reason=str(info.get("reason") or "duplicate schedule slot"))
                if run:
                    result["runs"].append(run)
            continue
        result["skipped"] += 1
        if record_skips and (target_schedule_id or force):
            run = append_schedule_skip_run(row, info, status="skipped", reason=str(info.get("reason") or status or "not due"))
            if run:
                result["runs"].append(run)
    return result


def format_scheduler_tick_result(result: dict[str, Any]) -> str:
    lines = [
        "Scheduler",
        f"checked: {result.get('checked', 0)} · due: {result.get('due', 0)} · dispatched: {result.get('dispatched', 0)} · failed: {result.get('failed', 0)}",
        f"skipped: {result.get('skipped', 0)} · invalid: {result.get('invalid', 0)} · duplicate: {result.get('duplicates', 0)}",
    ]
    for run in (result.get("runs") or [])[-12:]:
        lines.append(
            f"- {run.get('schedule_id') or '-'} · {run.get('status') or '-'} · "
            f"{_runtime.truncate_cells(str(run.get('result') or run.get('error') or run.get('reason') or ''), 180)}"
        )
    return "\n".join(lines).rstrip()


def format_scheduled_task_registry(data: dict[str, Any]) -> str:
    lines = [
        "Scheduled Tasks",
        f"status: {data.get('status')}",
        f"jobs: {data.get('active_job_count', 0)} active / {data.get('job_count', 0)} total",
        f"store: {data.get('schedules_path') or _runtime.schedules_path}",
        f"runs: {data.get('run_count', 0)} · {data.get('runs_path') or _runtime.runs_path}",
        f"dispatch: {(data.get('dispatch') or {}).get('contract', '-')}",
        "",
    ]
    jobs = data.get("jobs") or []
    if not jobs:
        lines.append("No scheduled jobs registered yet. Future jobs should dispatch via agenttask.v2 and audit each run into the task ledger.")
    for row in jobs[-20:]:
        scheduler = row.get("scheduler") if isinstance(row.get("scheduler"), dict) else {}
        work_order = row.get("work_order") if isinstance(row.get("work_order"), dict) else {}
        last_run = scheduler.get("last_run") if isinstance(scheduler.get("last_run"), dict) else {}
        objective = str(work_order.get("objective") or row.get("objective") or row.get("task") or "")
        run_suffix = f" · last:{last_run.get('status')}" if last_run else ""
        due_suffix = f" · {scheduler.get('status') or '-'}"
        if scheduler.get("due_at"):
            due_suffix += f" @{scheduler.get('due_at')}"
        lines.append(
            f"- {row.get('schedule_id') or row.get('id') or '-'} · {row.get('status', 'enabled')} · "
            f"{schedule_record_trigger(row) or '-'}{due_suffix}{run_suffix} · {_runtime.truncate_cells(objective, 140)}"
        )
    return "\n".join(lines).rstrip()
