# PRD: Workflow Durable Run Event History

## Goal

Add the first durable workflow core slice by recording explicit workflow run events that can later support replay, recovery, diagnostics, and idempotent continuation.

## Scope

- Add a pure workflow event schema and helper functions in `src/shuheng/workflows.py`.
- Add an app-owned append-only workflow event ledger in `src/shuheng/app.py`.
- Emit workflow events when a run is planned, advanced, continued, cancelled, bridged to approval, bridged to agent task, retried, or reaches a terminal/no-progress state.
- Add idempotency keys to event rows so later durable execution can reason about duplicate lifecycle transitions.
- Include workflow events in `/workflow trace <run-id>` without inlining raw payloads.
- Keep `workflows.py` pure: no app imports, no JSONL writes, no runtime dispatch, no approvals/task/artifact writes.
- Update backend spec, tests, and policy gates to lock the new boundary.

## Non-Goals

- No workflow-owned executor.
- No direct model/tool/shell/plugin-code execution from workflow steps.
- No parallel DAG scheduling, fan-out/fan-in execution, timers, sleeps, timeout engine, webhook/event bus service, or A2A/MCP workflow service exposure.
- No change to existing approval or agent-task bridge ownership.
- No mutation of legacy workflow run row semantics beyond adding durable event references/metadata needed by this slice.

## Acceptance Criteria

1. A successful `/workflow run <ref>` appends workflow run rows as before and also appends event rows for the initial planned transition and subsequent runner/bridge transition.
2. `/workflow continue <run-id>` appends at most one workflow run row as before and records a matching event for continued, no-progress, waiting, approval, task, retry, terminal, or completed outcomes.
3. `/workflow cancel <run-id>` records a cancellation event, including already-terminal/no-op cancellation outcomes.
4. Event rows use schema `shuheng.workflow_event.v1`, include `event_id`, `run_id`, `workflow_ref`, `timestamp`, `event_type`, `status`, `idempotency_key`, `source_command`, `row_index`, `step_id`, `step_type`, `approval_id`, `task_id`, `artifact_refs`, and bounded `message`.
5. `idempotency_key` is deterministic for the same run/status/blocker/source transition shape and does not contain raw prompts or secret-like payloads.
6. `/workflow trace <run-id>` includes linked workflow events and keeps raw event payloads out of the normal trace rendering.
7. `workflows.py` remains pure and does not import app/runtime/UI/governance owners or perform I/O.
8. Tests cover pure event construction, app event append behavior, trace rendering, cancel/continue edge cases, and policy gates.

## Evidence

- Targeted pytest for workflow behavior.
- `python3 scripts/check_policy_gates.py`.
- `python3 -m compileall -q src scripts`.
- `ruff check src/shuheng/workflows.py src/shuheng/app.py tests/test_workflows.py scripts/check_policy_gates.py`.
