#!/usr/bin/env python3
"""Isolated runtime/e2e smoke for Shuheng governance evidence."""

from __future__ import annotations

import json
import os
import queue
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class ContextFakeAgent:
    log_path = ""


class SequencedFakeAgent:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.prompts: list[tuple[str, str]] = []
        self.log_path = ""

    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        self.prompts.append((prompt, source))
        response = self.responses.pop(0) if self.responses else ""
        dq: queue.Queue = queue.Queue()
        dq.put({"done": response})
        return dq


def import_isolated_app(shuheng_home: str):
    os.environ["SHUHENG_HOME"] = shuheng_home
    os.environ["SHUHENG_HARNESS_DIR"] = os.path.join(shuheng_home, "memory", "agent_harness")
    os.environ.setdefault("SHUHENG_RUNTIME_PROVIDER", "ohmypi")
    sys.path.insert(0, str(SRC))
    from shuheng import app as a  # noqa: PLC0415

    return a


def drain_ui(a: Any, state: Any) -> None:
    time.sleep(0.1)
    for _ in range(10):
        changed = a.process_ui_queue(state)
        if not changed:
            break
        time.sleep(0.02)


def latest_approval(a: Any, *, approval_type: str) -> dict[str, Any]:
    rows = [row for row in a.read_jsonl(a.AGENT_APPROVALS_PATH) if row.get("type") == approval_type]
    if not rows:
        raise AssertionError(f"missing approval_type={approval_type}")
    return rows[-1]


def record_evidence(
    a: Any,
    *,
    target_items: list[str],
    check_id: str,
    level: str,
    summary: str,
    evidence_refs: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return a.append_runtime_evidence(
        target_items=target_items,
        check_id=check_id,
        level=level,
        passed=True,
        summary=summary,
        source="scripts/runtime_smoke.py",
        command="python3 scripts/runtime_smoke.py",
        evidence_refs=evidence_refs or [],
        details=details or {},
    )


def run_subagent_chat_smoke(a: Any, state: Any) -> None:
    sub = a.create_subagent(state, "Runtime Smoke Chat", role="researcher")
    sub.agent = SequencedFakeAgent([
        "direct smoke reply\n<ga-subagent-memory>\n- runtime smoke stable memory\n</ga-subagent-memory>"
    ])
    state.selected_session = sub.agent_id
    a.submit(state, "hello runtime smoke")
    drain_ui(a, state)

    entries = a.subagent_chat_session_entries(state, sub)
    if not entries:
        raise AssertionError("direct subagent chat did not create history-backed entries")
    if not a.path_is_within(entries[0]["history_path"], a.MODEL_RESPONSES_DIR):
        raise AssertionError(entries[0])
    per_agent_sessions = list(Path(a.subagent_sessions_dir(sub)).glob("*.json"))
    if per_agent_sessions:
        raise AssertionError("non-secret subagent chat wrote per-agent transcript JSON")

    reloaded = a.State(agent=ContextFakeAgent())
    reloaded.running = True
    if not a.load_subagents(reloaded):
        raise AssertionError("subagents did not reload")
    reloaded_sub = reloaded.subagents.get(sub.agent_id)
    if reloaded_sub is None:
        raise AssertionError("chat subagent missing after reload")
    restored = [msg.content for msg in reloaded_sub.messages]
    if "hello runtime smoke" not in restored or "direct smoke reply" not in restored:
        raise AssertionError(restored)
    record_evidence(
        a,
        target_items=["shared_ledgers", "context_engineering"],
        check_id="subagent_direct_chat_history_restore",
        level="e2e",
        summary="Direct subagent chat persisted to canonical history and restored after reload without per-agent transcript storage.",
        evidence_refs=[f"history://{Path(entries[0]['history_path']).name}"],
        details={"agent_id": sub.agent_id, "message_count": entries[0]["message_count"]},
    )


def run_memory_candidate_smoke(a: Any, state: Any) -> None:
    sub = a.create_subagent(state, "Runtime Smoke Memory", role="memory_curator")
    result = a.queue_curated_memory_candidate(
        state,
        sub,
        "Runtime smoke memory candidates remain approval gated and evidence referenced.",
        source="runtime_smoke",
        evidence_ref="trace://runtime_smoke_memory",
        task_id="task_runtime_smoke_memory",
    )
    if "等待审批" not in result:
        raise AssertionError(result)
    memory_request = latest_approval(a, approval_type="memory_write_request")
    candidates = [
        row for row in a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)
        if (row.get("memory_candidate") or {}).get("task_id") == "task_runtime_smoke_memory"
    ]
    if not candidates:
        raise AssertionError("memory candidate row was not persisted")
    record_evidence(
        a,
        target_items=["external_memory"],
        check_id="memory_candidate_approval_only",
        level="runtime",
        summary="Memory candidate API persisted candidate/artifact refs and queued human approval instead of writing memory directly.",
        evidence_refs=[f"approval://{memory_request['approval_id']}", "trace://runtime_smoke_memory"],
        details={"candidate_id": candidates[-1].get("candidate_id"), "target_subagent": sub.agent_id},
    )


def run_approval_smoke(a: Any, state: Any) -> None:
    ops = a.create_subagent(state, "Runtime Smoke Ops", role="ops")
    result = a.start_subagent_task(state, ops, "deploy production with sudo", source="runtime_smoke")
    if not result.startswith("APPROVAL_REQUIRED"):
        raise AssertionError(result)
    approval = latest_approval(a, approval_type="policy_approval_request")
    task_id = str((approval.get("payload") or {}).get("task_id") or "")
    task_rows = [row for row in a.read_jsonl(a.AGENT_TASK_LEDGER_PATH) if row.get("task_id") == task_id]
    if not task_rows or task_rows[-1].get("status") != "approval_required":
        raise AssertionError(task_rows)
    checkpoints = [row for row in a.read_jsonl(a.AGENT_CHECKPOINT_INDEX_PATH) if row.get("task_id") == task_id]
    if not checkpoints:
        raise AssertionError("approval-required task did not write checkpoint")
    record_evidence(
        a,
        target_items=["restricted_subagents", "approval_gates", "checkpoint_recovery"],
        check_id="approval_required_ops_task",
        level="e2e",
        summary="Risky ops task was blocked by program approval gate and recorded task/checkpoint evidence.",
        evidence_refs=[f"task://{task_id}", f"approval://{approval['approval_id']}"],
        details={"task_status": task_rows[-1].get("status"), "checkpoints": len(checkpoints)},
    )


def run_subagent_task_smoke(a: Any, state: Any) -> str:
    reader = a.create_subagent(state, "Runtime Smoke Reader", role="researcher")
    reader.agent = SequencedFakeAgent(["runtime task summary with evidence refs"])
    result = a.start_subagent_task(state, reader, "read local docs and summarize", source="runtime_smoke")
    if not result.startswith("已启动子 agent"):
        raise AssertionError(result)
    drain_ui(a, state)
    completed = [
        row for row in a.read_jsonl(a.AGENT_TASK_LEDGER_PATH)
        if row.get("assigned_agent") == reader.agent_id and row.get("status") == "completed"
    ]
    if not completed:
        raise AssertionError("subagent task did not complete")
    task_id = str(completed[-1]["task_id"])
    artifacts = [row for row in a.read_jsonl(a.AGENT_ARTIFACT_INDEX_PATH) if row.get("source_task_id") == task_id]
    traces = [row for row in a.read_jsonl(a.AGENT_TRACES_PATH) if row.get("task_id") == task_id]
    evals = [row for row in a.read_jsonl(a.AGENT_EVALS_PATH) if row.get("task_id") == task_id]
    checkpoints = [row for row in a.read_jsonl(a.AGENT_CHECKPOINT_INDEX_PATH) if row.get("task_id") == task_id]
    if not artifacts or not traces or not evals or not checkpoints:
        raise AssertionError({"artifacts": artifacts, "traces": traces, "evals": evals, "checkpoints": checkpoints})
    record_evidence(
        a,
        target_items=[
            "strong_orchestrator",
            "governance_components",
            "shared_ledgers",
            "artifact_store",
            "eval_trace",
            "checkpoint_recovery",
        ],
        check_id="subagent_task_artifact_eval_trace",
        level="e2e",
        summary="Governed subagent task completed with task/progress ledgers, artifacts, traces, eval, and checkpoints.",
        evidence_refs=[f"task://{task_id}"] + [str(row.get("uri")) for row in artifacts if row.get("uri")],
        details={"artifact_count": len(artifacts), "trace_count": len(traces), "eval_count": len(evals)},
    )
    return task_id


def run_scheduler_smoke(a: Any, state: Any) -> None:
    scheduled = a.create_subagent(state, "Runtime Smoke Scheduler", role="researcher")
    scheduled.agent = SequencedFakeAgent(["scheduled runtime smoke result"])
    schedule_id = "sched_runtime_smoke"
    created = a.apply_schedule_control(
        state,
        "schedule_create",
        "",
        "",
        {
            "schedule_id": schedule_id,
            "name": "Runtime Smoke Schedule",
            "at": "2026-01-01T00:00:00+00:00",
            "execution": {
                "mode": "agent_task",
                "routing": {"selected_agent": scheduled.agent_id},
                "work_order": {"objective": "produce a scheduled runtime smoke report"},
                "capability_contract": {"tools_allowed": ["read"], "write_policy": "none"},
                "context_contract": {"history_mode": "summary", "artifact_reference_only": True},
                "output_contract": {"format": "structured_markdown", "required_sections": ["summary"]},
            },
        },
        source="runtime_smoke",
    )
    if "已登记定时任务" not in str(created):
        raise AssertionError(created)
    tick = a.scheduler_tick(state, now_epoch=1780000000.0, source="runtime_smoke", target_schedule_id=schedule_id)
    runs = [row for row in tick["runs"] if row.get("schedule_id") == schedule_id]
    if not runs or runs[-1].get("status") not in {"dispatched", "completed", "queued"}:
        raise AssertionError(tick)
    record_evidence(
        a,
        target_items=["strong_orchestrator", "shared_ledgers", "checkpoint_recovery"],
        check_id="scheduler_dispatches_governed_subagent_task",
        level="runtime",
        summary="Scheduler tick dispatched a due agent-task schedule through governed subagent task path.",
        evidence_refs=[f"schedule://{schedule_id}", f"task://{runs[-1].get('task_id', '')}"],
        details={"run_status": runs[-1].get("status"), "run_id": runs[-1].get("run_id")},
    )


def run_local_protocol_registry_smoke(a: Any, state: Any, completed_task_id: str) -> None:
    for removed in (
        "GatewayRequestHandler",
        "make_gateway_http_server",
        "serve_gateway",
        "start_gateway_daemon",
        "stop_gateway_daemon",
        "web_console_snapshot",
        "web_console_apply_action",
    ):
        if hasattr(a, removed):
            raise AssertionError(f"removed Web/HTTP surface still exists: {removed}")

    registry = a.ensure_local_protocol_registry(state)
    if registry.get("schema_version") != "agentgateway.v1":
        raise AssertionError(registry)
    directory = registry.get("agent_directory") or {}
    if directory.get("schema_version") != "shuheng.agent_directory.v1" or not directory.get("roles"):
        raise AssertionError(directory)
    a2a = registry.get("a2a_gateway") or {}
    if a2a.get("delivery", {}).get("mode") != "agent_mail_inbox":
        raise AssertionError(a2a)
    task_ids = {str(item.get("id") or "") for item in (a2a.get("tasks") or []) if isinstance(item, dict)}
    if completed_task_id not in task_ids:
        raise AssertionError(a2a)
    mcp = registry.get("mcp_gateway") or {}
    resources = mcp.get("resources") or []
    if not any(item.get("uri") == "resource://agent-mail/runtime-evidence" for item in resources):
        raise AssertionError(mcp)
    if any(item.get("uri") in {"resource://agent-mail/context-inspector", "resource://agent-mail/permission-matrix"} for item in resources):
        raise AssertionError(mcp)
    record_evidence(
        a,
        target_items=["local_protocol_records"],
        check_id="local_protocol_registry_smoke",
        level="runtime",
        summary="Local protocol registry projected Agent Mail, task, runtime-evidence, and discovery records without starting any Web/HTTP server.",
        evidence_refs=[f"task://{completed_task_id}", "resource://agent-mail/runtime-evidence"],
        details={"registry_schema": registry["schema_version"], "directory_roles": len(directory.get("roles") or [])},
    )


def run_smoke(shuheng_home: str) -> dict[str, Any]:
    a = import_isolated_app(shuheng_home)
    state = a.State(agent=ContextFakeAgent())
    state.running = True
    run_subagent_chat_smoke(a, state)
    run_memory_candidate_smoke(a, state)
    run_approval_smoke(a, state)
    completed_task_id = run_subagent_task_smoke(a, state)
    run_scheduler_smoke(a, state)
    run_local_protocol_registry_smoke(a, state, completed_task_id)
    report = a.architecture_baseline_report(state)
    summary = report["summary"]["strongest_evidence_levels"]
    if summary.get("runtime", 0) + summary.get("e2e", 0) <= 0:
        raise AssertionError(report["summary"])
    records = a.runtime_evidence_records(passed=True, min_level="runtime")
    return {
        "home": shuheng_home,
        "runtime_evidence_path": a.AGENT_RUNTIME_EVIDENCE_PATH,
        "baseline_report_path": a.AGENT_BASELINE_REPORT_PATH,
        "evidence_rows": len(records),
        "strongest_evidence_levels": summary,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="shuheng_runtime_smoke_") as tmp:
        result = run_smoke(tmp)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
