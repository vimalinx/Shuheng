# Add Workflow Next Action Diagnostics V1

## Goal

Add a read-only workflow next-action diagnostic command so users and AI agents
can quickly understand what a workflow run is waiting on and which existing
command should be used next. This improves workflow recovery and usability
without creating a hidden executor or bypassing approval/task gates.

## What I already know

- Workflow v0 already has `/workflow runs`, `/workflow show`, `/workflow trace`,
  `/workflow continue|resume`, and `/workflow cancel`.
- `continue_workflow_run_v0(...)` already owns real state transitions,
  approval observation, agent-task dispatch/retry, and append-only workflow row
  writes.
- `format_workflow_run_trace(...)` already provides evidence/provenance, but it
  is not optimized for deciding what to do next.
- The architecture baseline favors explicit ledgers, human approval gates,
  auditable protocols, and strong Orchestrator ownership.

## Requirements

- Add `/workflow next <run_id>` and `/workflow diagnose <run_id>` aliases.
- The command must be read-only and append no workflow/task/progress/approval/
  artifact/trace rows.
- The output must include:
  - current run status, workflow ref, history row count, and stop reason;
  - current blocker step id/type when present;
  - a classification of next action such as `continue`, `wait_task`,
    `approve_or_reject`, `inspect_trace`, `cancel_or_edit`, or `none`;
  - concrete command suggestions using existing commands only;
  - relevant task id/status or approval id/status when available.
- The formatter must be pure and accept workflow/task/approval rows as
  parameters.
- The command must not call `continue_workflow_run_v0(...)`, `cancel_workflow_run_v0(...)`,
  approval decision functions, subagent dispatch, or any ledger append helper.
- Existing workflow commands and trace output must remain unchanged.

## Acceptance Criteria

- [x] Missing/blank run ids render the existing not-found style.
- [x] Completed and terminal runs recommend inspection/rerun rather than
  continuing.
- [x] Waiting approval runs recommend `/approve` or `/reject` for pending
  approvals and `/workflow continue` for approved/rejected approvals.
- [x] Waiting task runs recommend waiting when task is non-terminal and
  `/workflow continue` when the task is terminal.
- [x] Planned runs recommend `/workflow continue`.
- [x] Condition or unsupported blockers recommend trace/cancel/edit rather
  than pretending safe progress exists.
- [x] `/workflow next` and `/workflow diagnose` are proven read-only.
- [x] Policy gate and backend spec lock command aliases and side-effect
  invariants.

## Out Of Scope

- Automatically continuing, cancelling, approving, rejecting, retrying, or
  dispatching workflow work.
- New scheduler behavior.
- New workflow executor.
- Graph UI or web UI.
- MCP/A2A gateway exposure.

## Technical Notes

- Likely code:
  - `src/ga_tui/workflows.py`
  - `src/ga_tui/app.py`
  - `tests/test_workflows.py`
  - `scripts/check_policy_gates.py`
  - `.trellis/spec/backend/agent-control-protocol.md`
- Related previous task:
  - `.trellis/tasks/archive/2026-07/07-03-add-workflow-run-trace-view-v1/`
