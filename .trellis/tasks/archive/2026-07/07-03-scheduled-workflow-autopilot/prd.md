# PRD: Scheduled Workflow Autopilot

## Goal

Let Shuheng's existing scheduler periodically run the safe workflow autopilot tick, so workflow runs that become ready can advance automatically without introducing a new daemon or bypassing the strong Orchestrator.

## Scope

- Add scheduler execution mode `workflow_autopilot`.
- Add scheduler dispatch contract `workflow_autopilot.v1`.
- Parse optional execution fields:
  - `run_ids`: explicit list of workflow run ids to consider.
  - `limit`: maximum run ids considered per scheduler dispatch.
  - `dry_run`: optional boolean diagnostic mode.
- Add app-owned scheduler callback that calls existing `run_workflow_autopilot_tick(...)`.
- Record schedule run rows that include selected/continued/skipped counts and linked workflow event count.
- Keep scheduler and workflow helper boundaries:
  - `scheduler.py` parses and dispatches through callbacks only.
  - `app.py` owns workflow ledgers, workflow event writes, and calls `continue_workflow_run_v0(...)`.
  - `workflows.py` remains pure.
- Update backend spec, tests, and policy gates.

## Non-Goals

- No new daemon, background thread, timer, or always-on loop beyond the existing scheduler tick path.
- No direct workflow runner calls from `scheduler.py`.
- No direct approval decisions, subagent task dispatch, task-result application, or retry logic in scheduler.
- No automatic approval/rejection.
- No duplicate subagent dispatch while a task is still non-terminal.
- No A2A/MCP workflow service exposure.

## Acceptance Criteria

1. `schedule_execution_from_control(...)` accepts `{"mode":"workflow_autopilot"}` and preserves `run_ids`, `limit`, and `dry_run`.
2. `schedule_dispatch_contract_for_execution(...)` returns `workflow_autopilot.v1` for autopilot schedules.
3. `schedule_execution_error(...)` accepts valid autopilot execution and rejects invalid `limit <= 0`.
4. `scheduler_tick(...)` can dispatch a due autopilot schedule through a configured runtime callback.
5. App callback calls `run_workflow_autopilot_tick(...)` and records selected/continued/skipped/event counts in the schedule run row.
6. Dry-run autopilot schedules append schedule-run audit rows but append no workflow run/task/progress/approval/artifact/workflow-event rows.
7. Mutating autopilot schedules continue only runs selected by the existing autopilot tick plan and skip pending approvals/tasks.
8. Existing `workflow_run` scheduled execution remains compatible.
9. Tests cover pure scheduler parsing, app scheduled autopilot dispatch, dry-run no-mutation, pending approval skip, and policy gates.

## Evidence

- `python3 -m compileall -q src scripts tests`
- `ruff check src/ga_tui/scheduler.py src/ga_tui/app.py tests/test_scheduler_parsing.py tests/test_workflows.py scripts/check_policy_gates.py`
- `pytest -q tests/test_scheduler_parsing.py tests/test_workflows.py`
- `python3 scripts/check_policy_gates.py`
- `PYTHONPATH=. pytest -q`
