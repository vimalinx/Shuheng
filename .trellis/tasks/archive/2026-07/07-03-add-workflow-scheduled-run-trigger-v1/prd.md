# Add Workflow Scheduled Run Trigger V1

## Goal

Allow Shuheng's existing scheduler to trigger governed workflow runs from
`scheduledtask.v1` records without introducing a separate workflow executor.
Scheduled workflow execution must reuse the current app-owned
`create_workflow_run_v0(...)` path so workflow runs, approval waits,
subagent dispatch, retries, artifacts, and append-only ledgers keep the same
semantics as manual `/workflow run`.

## What I Already Know

- `src/ga_tui/workflows.py` owns pure declarative workflow parsing and runner
  state helpers.
- `src/ga_tui/app.py` owns workflow command routing, workflow run JSONL
  appends, approval bridging, agent-task bridging, and auto-continuation after
  subagent task completion.
- `src/ga_tui/scheduler.py` owns schedule registry helpers, trigger parsing,
  due calculation, idempotency, schedule run audit rows, and injected runtime
  callbacks.
- The scheduler currently supports `execution.mode:"tui_action"` and
  `execution.mode:"agent_task"`, but not workflow runs.
- Architecture baseline requires a strong Orchestrator, restricted subagents,
  append-only ledgers, human approval gates, artifact refs, and auditable
  protocol boundaries.

## Requirements

- Add scheduler support for `execution.mode:"workflow_run"`.
- A workflow schedule must accept:
  - `execution.workflow_ref`: a plugin workflow ref or accepted shorthand.
  - `execution.inputs`: optional object passed to workflow input resolution.
- Schedule create/update validation must reject workflow-run schedules without a
  workflow ref.
- Workflow-run schedule records must use a distinct dispatch contract such as
  `workflow_run.v1`.
- `dispatch_schedule_run(...)` must write the normal `scheduledtask.run.v1`
  `starting` row, delegate workflow dispatch through an injected app-owned
  callback, and append a final run row with workflow provenance.
- The app-owned callback must load the workflow through the existing plugin
  registry and call `create_workflow_run_v0(...)`.
- Schedule run final rows should record at least:
  - `workflow_run_id`
  - `workflow_ref`
  - `result` or `error`
  - existing schedule idempotency, trigger, provider/source metadata
- Manual `/scheduler run <schedule_id>` and normal scheduler tick must both use
  the same workflow-run dispatch path.
- `scheduler.py` must remain free of `app.py`, curses, mutable TUI `State`,
  workflow helper imports, direct task/progress/artifact/approval writes, and
  runtime provider classes.
- Existing `agent_task` and `tui_action` schedule behavior must remain
  compatible.

## Acceptance Criteria

- [x] Creating a schedule with `execution.mode:"workflow_run"` and valid
  `workflow_ref` stores `dispatch_contract:"workflow_run.v1"`.
- [x] Missing `workflow_ref` returns a visible creation/update validation
  error and appends no schedule row.
- [x] A forced scheduler run for a workflow schedule appends `starting` and
  final `scheduledtask.run.v1` rows, then appends normal `shuheng.workflow_run.v1`
  rows through `create_workflow_run_v0(...)`.
- [x] A schedule pointing at a missing/invalid workflow produces a failed
  schedule-run final row and no workflow run rows.
- [x] The final schedule-run row links to the created workflow run id and
  workflow ref.
- [x] Existing scheduler agent-task tests still pass.
- [x] Policy gates assert scheduler workflow mode ownership and purity.
- [x] `.trellis/spec/backend/agent-control-protocol.md` documents the new
  executable contract.

## Out Of Scope

- New workflow executor or daemon.
- Direct workflow execution inside `scheduler.py`.
- Parallel/fan-out/fan-in DAG execution.
- Workflow-specific backoff or timeout policy.
- Graph editing UI.
- Approval auto-resume from `/approve`.
- Plugin code, shell, tool, or model execution outside existing subagent task
  pipeline.
- A2A/MCP workflow service exposure.

## Technical Notes

- Relevant implementation files:
  - `src/ga_tui/scheduler.py`
  - `src/ga_tui/app.py`
  - `tests/test_scheduler_parsing.py`
  - `tests/test_workflows.py`
  - `scripts/check_policy_gates.py`
  - `.trellis/spec/backend/agent-control-protocol.md`
- The callback shape should mirror existing scheduler dependency injection:
  `SchedulerRuntime` receives a workflow dispatch callback from `app.py`.
- The schedule mode parser should preserve `inputs` with JSON-safe conversion
  but must not interpret workflow inputs itself.
- The app callback is the only layer allowed to resolve workflow refs or append
  workflow run rows.

## Definition Of Done

- Targeted compile, Ruff, scheduler tests, workflow tests, and policy gates are
  green.
- Full repo quality gates are green before commit.
- Work commit excludes pre-existing untracked `uv.lock`.
- Architecture baseline comparison says this moves Shuheng closer to the
  governed Orchestrator model.
