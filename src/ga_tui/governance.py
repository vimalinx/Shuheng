"""Governance record and ledger helpers for the Shuheng control plane.

This module owns durable governance row shaping above ``ledger_store``. It is
intentionally lower-level than the TUI: callers pass paths and runtime facts in
explicitly so tests can retarget the harness without mutating this module.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import unicodedata
from typing import Any, Callable, Optional

try:
    from . import ledger_store
    from .release_readiness import HeuristicEvalInput, heuristic_eval_assessment
    from .text_utils import clean_text, truncate_cells
    from .ui_types import PolicyDecision
except Exception:
    import ledger_store  # type: ignore
    from release_readiness import HeuristicEvalInput, heuristic_eval_assessment  # type: ignore
    from text_utils import clean_text, truncate_cells  # type: ignore
    from ui_types import PolicyDecision  # type: ignore


APPROVAL_REQUIRED_FOR = [
    "external_send",
    "publish",
    "delete_file",
    "delete_memory",
    "write_long_term_memory",
    "deploy",
    "spend_money",
    "external_commitment",
    "high_risk_batch_change",
    "modify_permission_policy",
    "access_secret",
    "secret_export",
    "secret_downgrade",
    "long_running_privilege_escalation",
]


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def short_uid(prefix: str) -> str:
    return f"{prefix}_{time.time_ns():x}_{os.getpid():x}"


def write_text_atomic(path: str, text: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def safe_artifact_segment(text: str, *, fallback: str = "artifact") -> str:
    normalized = unicodedata.normalize("NFKC", text or "").strip().lower()
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"[^a-z0-9._-]+", "", normalized)
    normalized = normalized.strip("._-")
    return normalized[:40] or f"{fallback}-{int(time.time())}"


def harness_artifact_uri(harness_dir: str, path: str) -> str:
    try:
        rel = os.path.relpath(path, harness_dir)
    except (ValueError, TypeError):
        rel = os.path.basename(path)
    return "artifact://" + rel.replace(os.sep, "/")


def artifact_sha256(path: str) -> str:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return "sha256:" + digest.hexdigest()


def append_artifact_index(
    artifact_index_path: str,
    harness_dir: str,
    path: str,
    *,
    artifact_type: str,
    source_task_id: str = "",
    provenance: Optional[dict[str, Any]] = None,
    preview_path: str = "",
    content_type: str = "text/markdown",
) -> dict[str, Any]:
    path = os.path.abspath(path)
    try:
        st = os.stat(path)
    except OSError:
        size = 0
        mtime = time.time()
    else:
        size = int(st.st_size)
        mtime = float(st.st_mtime)
    uri = harness_artifact_uri(harness_dir, path)
    row = {
        "schema_version": "agentartifact.v1",
        "artifact_id": short_uid("art"),
        "timestamp": now_iso(),
        "type": artifact_type or "artifact",
        "uri": uri,
        "path": path,
        "preview_path": preview_path or path,
        "hash": artifact_sha256(path),
        "size_bytes": size,
        "mtime": mtime,
        "source_task_id": source_task_id,
        "provenance": provenance or {},
        "content_type": content_type,
    }
    ledger_store.append_jsonl(artifact_index_path, row)
    return row


def write_harness_artifact(
    artifacts_dir: str,
    harness_dir: str,
    artifact_index_path: str,
    kind: str,
    name: str,
    content: str,
    *,
    source_task_id: str = "",
    provenance: Optional[dict[str, Any]] = None,
    content_type: str = "text/markdown",
) -> str:
    safe_kind = safe_artifact_segment(kind or "artifact", fallback="artifact")
    safe_name = safe_artifact_segment(name or "artifact", fallback="artifact")
    directory = os.path.join(artifacts_dir, safe_kind)
    os.makedirs(directory, exist_ok=True)
    filename = f"{time.strftime('%Y%m%d-%H%M%S')}-{safe_name}-{time.time_ns() % 1_000_000:06d}.md"
    path = os.path.join(directory, filename)
    write_text_atomic(path, content.rstrip() + "\n")
    append_artifact_index(
        artifact_index_path,
        harness_dir,
        path,
        artifact_type=safe_kind,
        source_task_id=source_task_id,
        provenance=provenance,
        content_type=content_type,
    )
    return harness_artifact_uri(harness_dir, path)


def policy_decision_to_dict(decision: PolicyDecision, *, timestamp: str = "") -> dict[str, Any]:
    return {
        "schema_version": "agentpolicy.decision.v1",
        "decision_id": decision.decision_id,
        "timestamp": timestamp or now_iso(),
        "action": decision.action,
        "subject": decision.subject,
        "role": decision.role,
        "source": decision.source,
        "target": decision.target,
        "status": decision.status,
        "allowed": decision.allowed,
        "approval_required": decision.approval_required,
        "approval_required_for": decision.approval_required_for,
        "approval_id": decision.approval_id,
        "risk": decision.risk,
        "reason": decision.reason,
        "payload": decision.payload,
    }


def record_policy_decision(policy_decisions_path: str, decision: PolicyDecision) -> dict[str, Any]:
    row = policy_decision_to_dict(decision)
    ledger_store.append_jsonl(policy_decisions_path, row)
    return row


def approval_metadata(
    *,
    status: str = "not_required",
    approval_required_for: Optional[list[str]] = None,
    approval_id: str = "",
    decision: Optional[PolicyDecision] = None,
    default_required_for: Optional[list[str]] = None,
) -> dict[str, Any]:
    default_required_for = list(default_required_for or APPROVAL_REQUIRED_FOR)
    if decision is not None:
        return {
            "approval_required_for": [decision.approval_required_for] if decision.approval_required_for else default_required_for,
            "approval_status": decision.status if decision.approval_required else ("not_required" if decision.allowed else "rejected"),
            "approval_id": decision.approval_id,
            "policy_decision_id": decision.decision_id,
            "policy_action": decision.action,
        }
    return {
        "approval_required_for": approval_required_for or default_required_for,
        "approval_status": status,
        "approval_id": approval_id,
        "policy_decision_id": "",
        "policy_action": "",
    }


def append_progress_ledger(
    progress_path: str,
    task_row: dict[str, Any],
    *,
    source: str = "task_ledger",
) -> dict[str, Any]:
    task_id = str(task_row.get("task_id") or "")
    row = {
        "schema_version": "agentprogress.v1",
        "progress_id": short_uid("progress"),
        "timestamp": str(task_row.get("timestamp") or now_iso()),
        "task_id": task_id,
        "parent_task_id": str(task_row.get("parent_task_id") or ""),
        "status": str(task_row.get("status") or ""),
        "assigned_agent": str(task_row.get("assigned_agent") or ""),
        "title": str(task_row.get("title") or ""),
        "kind": str(task_row.get("kind") or ""),
        "summary": str(task_row.get("summary") or task_row.get("error") or task_row.get("objective") or ""),
        "error": str(task_row.get("error") or ""),
        "artifact_refs": [str(ref) for ref in (task_row.get("artifact_refs") or []) if str(ref)],
        "source": source,
        "task_ref": task_id,
    }
    ledger_store.append_jsonl(progress_path, row)
    return row


def terminal_task_status(status: str) -> bool:
    return (status or "").lower() in {"completed", "failed", "cancelled", "canceled", "rejected", "aborted"}


def parse_iso_timestamp(value: str) -> float:
    value = (value or "").strip()
    if not value:
        return 0.0
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return time.mktime(time.strptime(value, fmt))
        except Exception:
            continue
    return 0.0


def row_timestamp(row: dict[str, Any]) -> float:
    return parse_iso_timestamp(str(row.get("timestamp") or "")) or float(row.get("ts") or 0.0)


def load_agent_locks(locks_path: str) -> dict[str, Any]:
    try:
        with open(locks_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def save_agent_locks(locks_path: str, data: dict[str, Any]) -> None:
    ledger_store.update_json_dict_file(locks_path, lambda _current: (dict(data), None))


def current_writer_lock(locks_path: str) -> Optional[dict[str, Any]]:
    data = load_agent_locks(locks_path)
    lock = data.get("single_writer")
    return lock if isinstance(lock, dict) and lock.get("task_id") else None


def acquire_single_writer_lock(
    locks_path: str,
    *,
    task_id: str,
    agent_id: str,
    agent_name: str,
    role: str,
    objective: str = "",
    is_write_role: bool = False,
    latest_tasks: Optional[dict[str, dict[str, Any]]] = None,
) -> tuple[bool, str]:
    if not is_write_role:
        return True, ""
    task_id = str(task_id or "")
    latest_tasks = latest_tasks or {}

    def update(data: dict[str, Any]) -> tuple[dict[str, Any], tuple[bool, str]]:
        lock = data.get("single_writer") if isinstance(data.get("single_writer"), dict) else None
        if lock:
            locked_task = str(lock.get("task_id") or "")
            locked_status = str(latest_tasks.get(locked_task, {}).get("status") or "")
            if locked_task == task_id:
                return data, (True, "")
            if not terminal_task_status(locked_status):
                owner = str(lock.get("agent_id") or "-")
                return data, (False, f"single-writer 已被 {owner} 持有，任务 {locked_task} 尚未结束。")
        data["single_writer"] = {
            "task_id": task_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "role": role,
            "objective": truncate_cells(objective, 240),
            "acquired_at": now_iso(),
        }
        return data, (True, "")

    return ledger_store.update_json_dict_file(locks_path, update)


def release_single_writer_lock(locks_path: str, task_id: str) -> bool:
    task_id = str(task_id or "")

    def update(data: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        lock = data.get("single_writer") if isinstance(data.get("single_writer"), dict) else None
        if not lock or str(lock.get("task_id") or "") != task_id:
            return data, False
        data.pop("single_writer", None)
        return data, True

    return ledger_store.update_json_dict_file(locks_path, update)


def refs_from_payload(payload: dict[str, Any]) -> dict[str, list[str]]:
    refs = {
        "artifacts": [],
        "approvals": [],
        "memory_candidates": [],
        "messages": [],
        "tool_calls": [],
        "checkpoints": [],
    }
    for key in ("artifact_ref", "context_pack", "context_pack_ref"):
        value = payload.get(key)
        if isinstance(value, str) and value.startswith("artifact://"):
            refs["artifacts"].append(value)
    for value in payload.get("artifact_refs") or []:
        if isinstance(value, str) and value.startswith("artifact://"):
            refs["artifacts"].append(value)
    approval_id = payload.get("approval_id")
    if approval_id:
        refs["approvals"].append(str(approval_id))
    memory_candidate_id = payload.get("memory_candidate_id")
    if memory_candidate_id:
        refs["memory_candidates"].append(str(memory_candidate_id))
    message_id = payload.get("message_id")
    if message_id:
        refs["messages"].append(str(message_id))
    tool_call_id = payload.get("tool_call_id") or payload.get("tool")
    if tool_call_id:
        refs["tool_calls"].append(str(tool_call_id))
    checkpoint_id = payload.get("checkpoint_id")
    if checkpoint_id:
        refs["checkpoints"].append(str(checkpoint_id))
    return {key: sorted(set(values)) for key, values in refs.items()}


def collect_task_audit_refs(paths: dict[str, str], task_id: str) -> dict[str, list[str]]:
    task_id = str(task_id or "")
    traces = [row for row in ledger_store.read_jsonl(paths.get("traces", "")) if str(row.get("task_id") or "") == task_id]
    artifacts = [row for row in ledger_store.read_jsonl(paths.get("artifacts", "")) if str(row.get("source_task_id") or "") == task_id]
    messages = [row for row in ledger_store.read_jsonl(paths.get("messages", "")) if str(row.get("task_id") or "") == task_id]
    approvals = [
        row for row in ledger_store.read_jsonl(paths.get("approvals", ""))
        if str((row.get("payload") or {}).get("task_id") or "") == task_id
    ]
    memory_candidates = [
        row for row in ledger_store.read_jsonl(paths.get("memory_candidates", ""))
        if str((row.get("memory_candidate") or {}).get("task_id") or row.get("task_id") or "") == task_id
    ]
    plans = [
        row for row in ledger_store.read_jsonl(paths.get("orchestrator_plans", ""))
        if str(row.get("task_id") or "") == task_id
    ]
    tool_trace_refs = [
        str(row.get("trace_id") or "")
        for row in traces
        if "tool" in str(row.get("event") or "").lower() or (row.get("audit_refs") or {}).get("tool_calls")
    ]
    checkpoint_refs = [
        ref
        for row in traces
        for ref in ((row.get("audit_refs") or {}).get("checkpoints") or [])
    ]
    return {
        "plan_versions": [str(row.get("plan_id") or "") for row in plans if row.get("plan_id")],
        "messages": [str(row.get("message_id") or "") for row in messages if row.get("message_id")],
        "tool_calls": [ref for ref in tool_trace_refs if ref],
        "artifacts": [str(row.get("uri") or "") for row in artifacts if row.get("uri")],
        "checkpoints": sorted(set(str(ref) for ref in checkpoint_refs if ref)),
        "approvals": [str(row.get("approval_id") or "") for row in approvals if row.get("approval_id")],
        "memory_candidates": [
            str((row.get("memory_candidate") or {}).get("candidate_id") or row.get("candidate_id") or "")
            for row in memory_candidates
            if (row.get("memory_candidate") or {}).get("candidate_id") or row.get("candidate_id")
        ],
        "traces": [str(row.get("trace_id") or "") for row in traces if row.get("trace_id")],
    }


def append_trace(
    traces_path: str,
    task_id: str,
    event: str,
    *,
    agent_id: str = "",
    status: str = "",
    payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    payload = payload or {}
    audit_refs = refs_from_payload(payload)
    lower_event = str(event or "").lower()
    lower_status = str(status or "").lower()
    row = {
        "schema_version": "agenttrace.v2",
        "trace_id": short_uid("trace"),
        "task_id": task_id,
        "context_id": "ga-tui",
        "timestamp": now_iso(),
        "event": event,
        "phase": lower_event.split("_", 1)[0] if lower_event else "",
        "agent_id": agent_id,
        "actor": {"agent_id": agent_id or "orchestrator.main"},
        "status": status,
        "severity": "error" if lower_status in {"failed", "rejected", "denied"} else ("warning" if lower_status in {"approval_required", "pending"} else "info"),
        "audit_refs": audit_refs,
        "metrics": {
            "tool_calls_delta": len(audit_refs["tool_calls"]),
            "artifact_refs_delta": len(audit_refs["artifacts"]),
            "approval_refs_delta": len(audit_refs["approvals"]),
            "memory_candidate_refs_delta": len(audit_refs["memory_candidates"]),
        },
        "policy": {
            "approval_related": bool(audit_refs["approvals"] or "approval" in lower_event or lower_status == "approval_required"),
            "policy_compliance": lower_status not in {"bypassed", "violation"},
        },
        "payload": payload,
    }
    ledger_store.append_jsonl(traces_path, row)
    return row


def append_task_eval(
    evals_path: str,
    *,
    task_id: str,
    agent_id: str,
    role: str,
    display_text: str,
    artifact_ref: str = "",
    task_row: Optional[dict[str, Any]] = None,
    audit_refs: Optional[dict[str, list[str]]] = None,
    default_budget: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    clean = clean_text(display_text)
    audit_refs = {key: list(values) for key, values in (audit_refs or {}).items()}
    audit_refs.setdefault("traces", [])
    audit_refs.setdefault("messages", [])
    audit_refs.setdefault("artifacts", [])
    audit_refs.setdefault("approvals", [])
    audit_refs.setdefault("memory_candidates", [])
    audit_refs.setdefault("tool_calls", [])
    if artifact_ref and artifact_ref not in audit_refs["artifacts"]:
        audit_refs["artifacts"].append(artifact_ref)
    task_row = task_row or {}
    budget = task_row.get("budget") if isinstance(task_row.get("budget"), dict) else (default_budget or {})
    max_tools = max(1, int(budget.get("max_tool_calls") or 1))
    tool_calls = len(audit_refs["tool_calls"])
    approval_count = len(audit_refs["approvals"])
    artifact_count = len(audit_refs["artifacts"])
    assessment = heuristic_eval_assessment(HeuristicEvalInput(
        has_text=bool(clean.strip()),
        role=role,
        max_tools=max_tools,
        tool_calls=tool_calls,
        approval_count=approval_count,
        artifact_count=artifact_count,
        artifact_recorded=bool(artifact_ref),
    ))
    scores = dict(assessment.get("scores") or {})
    policy_compliance = float(assessment.get("policy_compliance") or scores.get("policy_compliance") or 0.0)
    human_takeover_cost = float(assessment.get("human_takeover_cost") or scores.get("human_takeover_cost") or 0.0)
    row = {
        "schema_version": "agenteval.v2",
        "eval_id": short_uid("eval"),
        "task_id": task_id,
        "context_id": "ga-tui",
        "timestamp": now_iso(),
        "agent_id": agent_id,
        "role": role,
        "scores": scores,
        "score_method": {
            "schema_version": assessment.get("schema_version"),
            "method": assessment.get("method"),
            "basis": assessment.get("basis") or {},
            "limitations": assessment.get("limitations") or [],
        },
        "audit_refs": audit_refs,
        "coverage": {
            "trace_count": len(audit_refs["traces"]),
            "message_count": len(audit_refs["messages"]),
            "artifact_count": artifact_count,
            "approval_count": approval_count,
            "memory_candidate_count": len(audit_refs["memory_candidates"]),
            "tool_call_count": tool_calls,
        },
        "final_state": {
            "status": "completed" if clean.strip() else "empty_result",
            "has_result": bool(clean.strip()),
            "has_evidence": bool(artifact_count),
            "has_citation": bool(artifact_count),
            "has_risk_signal": bool(approval_count),
            "requires_review": bool(approval_count or role in {"coder", "ops"}),
        },
        "policy": {
            "approval_count": approval_count,
            "policy_compliance": policy_compliance,
            "human_takeover_cost": human_takeover_cost,
        },
        "summary": truncate_cells(clean, 240),
        "artifact_refs": [artifact_ref] if artifact_ref else [],
    }
    ledger_store.append_jsonl(evals_path, row)
    return row


ApprovalMailCallback = Callable[[dict[str, Any]], None]


def queue_approval(
    approvals_path: str,
    *,
    approval_type: str,
    summary: str,
    payload: dict[str, Any],
    source: str,
    target: str = "",
    approval_required_for: str = "",
    mail_callback: Optional[ApprovalMailCallback] = None,
) -> str:
    approval_id = short_uid("appr")
    row = {
        "schema_version": "agentapproval.v1",
        "approval_id": approval_id,
        "timestamp": now_iso(),
        "status": "pending",
        "type": approval_type,
        "source": source,
        "target": target,
        "summary": summary,
        "approval_required_for": approval_required_for or approval_type,
        "payload": payload,
    }
    ledger_store.append_jsonl(approvals_path, row)
    if mail_callback is not None:
        mail_callback(row)
    return approval_id


def approval_latest_records(approvals_path: str) -> dict[str, dict[str, Any]]:
    return ledger_store.latest_records_by_id(approvals_path, "approval_id")


def approval_artifact_refs(row: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for value in row.get("artifact_refs") or []:
        if isinstance(value, str) and value:
            refs.append(value)
    payload = row.get("payload") or {}
    if isinstance(payload, dict):
        for value in payload.get("artifact_refs") or []:
            if isinstance(value, str) and value:
                refs.append(value)
        evidence = str(payload.get("evidence_ref") or "")
        if evidence.startswith("artifact://"):
            refs.append(evidence)
    return list(dict.fromkeys(refs))


def approval_status_for_task(approval_rows: list[dict[str, Any]], task_id: str) -> str:
    task_id = str(task_id or "")
    statuses: list[str] = []
    for row in approval_rows:
        payload = row.get("payload") or {}
        if not isinstance(payload, dict):
            payload = {}
        refs = approval_artifact_refs(row)
        if str(payload.get("task_id") or "") == task_id or any(task_id and task_id in ref for ref in refs):
            statuses.append(str(row.get("status") or "pending"))
    if not statuses:
        return "-"
    if "pending" in statuses:
        return "pending"
    return ",".join(sorted(set(statuses)))


def governance_store_paths(
    *,
    messages: str,
    tasks: str,
    progress: str,
    approvals: str,
    artifacts: str,
    policy: str,
    policy_decisions: str,
    orchestrator_plans: str,
    memory_candidates: str,
    traces: str,
    evals: str,
    runtime_evidence: str,
    checkpoints: str,
    checkpoint_store: str,
    recovery: str,
    recovery_plans: str,
    gateway: str,
    governance: str,
    gateway_push_subscriptions: str,
    gateway_push_deliveries: str,
    gateway_daemon_status: str,
    gateway_daemon_pid: str,
    bridges: str,
) -> dict[str, str]:
    return {
        "messages": messages,
        "tasks": tasks,
        "progress": progress,
        "approvals": approvals,
        "artifacts": artifacts,
        "policy": policy,
        "policy_decisions": policy_decisions,
        "orchestrator_plans": orchestrator_plans,
        "memory_candidates": memory_candidates,
        "traces": traces,
        "evals": evals,
        "runtime_evidence": runtime_evidence,
        "checkpoints": checkpoints,
        "checkpoint_store": checkpoint_store,
        "recovery": recovery,
        "recovery_plans": recovery_plans,
        "gateway": gateway,
        "governance": governance,
        "gateway_push_subscriptions": gateway_push_subscriptions,
        "gateway_push_deliveries": gateway_push_deliveries,
        "gateway_daemon_status": gateway_daemon_status,
        "gateway_daemon_pid": gateway_daemon_pid,
        "bridges": bridges,
    }
