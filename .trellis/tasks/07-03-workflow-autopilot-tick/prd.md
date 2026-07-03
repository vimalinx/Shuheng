# PRD: Workflow Autopilot Tick

## Goal

Add a safe workflow autopilot tick that lets Shuheng automatically continue workflow runs whose durable next-action projection says they are ready to continue, while preserving the strong Orchestrator boundary, approval gates, task wait boundaries, and auditability.

## Scope

- Add a pure autopilot planning helper in `src/ga_tui/workflows.py` that inspects workflow run rows plus approval/task state and returns a bounded tick plan.
- Add an app-owned command path in `src/ga_tui/app.py` for `/workflow tick` and `/workflow autopilot` that executes the plan by calling the existing `continue_workflow_run_v0(...)` Orchestrator bridge.
- Continue only runs whose `workflow_run_next_action_projection(...)` reports `next_action=continue`.
- Report but do not mutate runs that require approval, are waiting on subagent tasks, are terminal/completed, missing, or require cancel/edit.
- Append workflow event rows for the tick itself and for each run that was selected, skipped, or failed to continue.
- Expose a dry-run mode so users can inspect what would be advanced before mutating ledgers.
- Keep helper purity: no app imports, JSONL I/O, runtime dispatch, approval writes, task ledger writes, or artifact writes in `workflows.py`.
- Update backend spec, tests, and policy gates.

## Non-Goals

- No workflow-owned executor.
- No direct model/tool/shell/plugin-code execution from workflow steps.
- No daemon, background thread, timer, watcher, scheduler loop, cron integration, or always-on service.
- No bypass of `/approve`, `/reject`, or subagent task terminal status checks.
- No parallel DAG execution or fan-out/fan-in scheduler.
- No A2A/MCP service exposure.
- No Secret Vault tool execution from workflow definitions.

## Acceptance Criteria

1. `/workflow tick` scans current workflow run state and continues only runs whose next action is `continue`.
2. `/workflow tick --dry-run` reports the same plan but appends no workflow run, task, progress, approval, artifact, or workflow event rows.
3. `/workflow autopilot` is accepted as an alias of `/workflow tick`.
4. The tick output reports selected run count, continued run count, skipped run count, and per-run reason/action.
5. Runs waiting for approval produce a skipped item with approval id/status and suggested approval commands; no workflow row is appended.
6. Runs waiting for a non-terminal subagent task produce a skipped item with task id/status; no workflow row is appended.
7. Completed, terminal, and cancel/edit runs are skipped without mutation.
8. Each mutating tick appends a durable event row with schema `shuheng.workflow_event.v1` for tick start/summary and each selected/skipped run.
9. The tick command preserves existing `continue_workflow_run_v0(...)` semantics: all actual advancement, approval bridge creation, task dispatch, retry, and condition handling remain app-owned Orchestrator behavior.
10. Tests cover pure plan generation, dry-run no-mutation behavior, mutating tick continuation, skipped approval/task/terminal runs, command alias, and policy gates.

## Evidence

- `python3 -m compileall -q src scripts tests`
- `ruff check src/ga_tui/workflows.py src/ga_tui/app.py tests/test_workflows.py scripts/check_policy_gates.py`
- `pytest -q tests/test_workflows.py`
- `python3 scripts/check_policy_gates.py`
- `PYTHONPATH=. pytest -q`
