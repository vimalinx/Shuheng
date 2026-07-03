# Add Workflow Continue Command

## Goal

Make workflow runs recoverable at the command level by adding `/workflow continue <run_id>`. The command should resume from the latest append-only `workflow_runs.jsonl` row for that run id, advance only runner-v0 safe steps, append exactly one new workflow run row when progress is possible, and preserve the current no-side-effect boundaries.

## What I Already Know

- Workflow definitions are plugin-contributed and validated through `shuheng.workflow.v1`.
- `/workflow run <ref>` currently appends a planned row, advances runner v0 once, and appends an advanced row with the same `run_id`.
- `/workflow runs` and `/workflow show <run_id>` can inspect append-only run history without mutating ledgers.
- Runner v0 can complete safe step types: `prompt`, `artifact_summary`, `pause`, and `notify`.
- Runner v0 blocks at `approval`, `agent_task`, `condition`, unsupported future step types, or unmet dependencies.
- `workflows.py` must remain pure; app-level JSONL reads/writes stay in `app.py`.

## Requirements

- Add `/workflow continue <run_id>` and alias `/workflow resume <run_id>`.
- The command must read the latest row for the given `run_id` from `workflow_runs.jsonl`.
- Missing, blank, or unknown run ids must produce a clear user-facing message and must not append rows.
- If the latest row is already `completed`, the command must report that no continuation is needed and must not append a row.
- If the latest row is blocked/waiting and runner v0 can make safe progress from that row, append exactly one new row with the same `run_id`.
- The appended row must preserve append-only history and update step statuses, timestamps, execution metadata, and stop reason through the existing runner-v0 semantics.
- The command must not dispatch subagents, create approval rows, call tools/model providers, evaluate conditions, run plugin code, write artifacts, mutate task/progress ledgers, write memory, touch Secret Vault, schedule work, or expose A2A/MCP services.
- Formatting helpers belong in `src/ga_tui/workflows.py`; concrete JSONL reads/writes and command routing remain in `src/ga_tui/app.py`.
- Update tests, policy gates, and `.trellis/spec/backend/agent-control-protocol.md`.

## Acceptance Criteria

- [ ] `/workflow continue <run_id>` reports not found for unknown ids without mutating any ledger.
- [ ] `/workflow continue <run_id>` reports no-op for already completed runs without appending a row.
- [ ] `/workflow continue <run_id>` appends exactly one new row when a run has newly unblocked safe steps.
- [ ] `/workflow continue <run_id>` preserves the run id and append-only history.
- [ ] `/workflow resume <run_id>` behaves as the same command.
- [ ] Side-effect ledgers remain unchanged: tasks, progress, approvals, artifacts, subagent state.
- [ ] Existing `/workflow run`, `/workflow runs`, and `/workflow show` behavior remains unchanged.
- [ ] Policy gates assert the command is bounded to runner-v0 safe continuation and does not cross approval/subagent/tool/artifact boundaries.
- [ ] Targeted tests, policy gate, full tests, build smoke, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.

## Definition of Done

- Tests added/updated for pure formatter behavior and app command behavior.
- Backend spec documents the workflow continue command contract with scope, signatures, contracts, validation matrix, cases, tests, and wrong/correct examples.
- Final report compares the change to `docs/agent-harness-architecture.md`.

## Technical Approach

- Add a pure `format_workflow_continue_result(...)` helper in `workflows.py`, or reuse `format_workflow_run_advanced(...)` with explicit continuation text if cleaner.
- Add an app-level helper such as `continue_workflow_run_v0(run_id)` that:
  - Loads all rows from `workflow_runs.jsonl`.
  - Selects the latest row by ledger order for the target `run_id`.
  - Rejects missing/unknown/completed cases without appending rows.
  - Calls `advance_workflow_run_v0(latest_row, timestamp=now_iso())`.
  - Appends the advanced row only when continuation is valid and should be recorded.
- Ensure continuation does not append a duplicate no-progress row when runner v0 immediately returns the same terminal block. If no step changes and the latest row is not completed, report the current stop reason.

## Decision

Implement only runner-v0 continuation. Do not implement real approval resume, subagent dispatch, condition evaluation, artifact writes, retry, cancellation, scheduling, input binding, or MCP/A2A exposure in this slice.

## Out of Scope

- Real approval bridge.
- Agent task dispatch.
- Condition evaluation.
- Artifact index writes.
- Retry, timeout, cancellation, scheduling, cron, or queue workers.
- Workflow UI panel changes.
- A2A/MCP workflow service exposure.

## Technical Notes

- Existing runner helpers live in `src/ga_tui/workflows.py`.
- Existing command routing and JSONL ownership live in `src/ga_tui/app.py`.
- Existing executable contract lives in `.trellis/spec/backend/agent-control-protocol.md`.
- Current worktree has unrelated untracked `uv.lock`; it must not be included.
