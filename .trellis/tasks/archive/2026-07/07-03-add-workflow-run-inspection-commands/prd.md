# Add Workflow Run Inspection Commands

## Goal

Make workflow automation observable before adding resume/approval dispatch. Users need to list recent workflow runs and inspect one run's latest state/history so `/workflow run` output is not the only way to understand what happened.

## Requirements

- Add `/workflow runs` to list recent workflow run ids, statuses, workflow refs, safe-step progress, and stop reason when present.
- Add `/workflow show <run_id>` to show the latest row for a workflow run, including workflow ref, status, timestamps, execution counters, approval metadata, step statuses, and stop reason.
- `/workflow show <run_id>` must also show history count for that run so append-only progression is visible.
- Commands must read `workflow_runs.jsonl` only; they must not append rows, dispatch subagents, create approvals, execute tools, evaluate conditions, or mutate task/progress/artifact ledgers.
- Formatting helpers belong in `src/ga_tui/workflows.py`; concrete JSONL reads and command routing remain in `src/ga_tui/app.py`.
- Missing/empty run ledger must produce a clear user-facing message, not a traceback.
- Unknown run id must produce a clear not-found message and must not mutate state beyond adding a system message.
- Update tests, policy gates, and `.trellis/spec/backend/agent-control-protocol.md`.

## Acceptance Criteria

- [ ] `/workflow runs` reports no runs when `workflow_runs.jsonl` is empty or missing.
- [ ] `/workflow runs` lists the latest state per run id, not duplicate append-only rows for the same run.
- [ ] `/workflow show <run_id>` displays latest run details and step statuses.
- [ ] `/workflow show <run_id>` reports not found for unknown ids.
- [ ] Existing `/workflow run` behavior remains unchanged.
- [ ] Policy gates assert inspection commands are read-only and do not mutate side-effect ledgers.
- [ ] Targeted tests, policy gate, full tests, build smoke, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.

## Definition of Done

- Tests added/updated for pure formatting and app command behavior.
- Backend spec documents the run inspection command contract with scope, signatures, contracts, validation matrix, good/bad cases, tests, and wrong/correct examples.
- Final report compares the change to the agent harness architecture baseline.

## Technical Approach

Use existing `workflow_run_records(limit=0)` and `latest_workflow_run_records()` in `app.py`. Add pure workflow formatting helpers that accept rows/history records:

- `format_workflow_runs(rows)`
- `format_workflow_run_detail(run_id, rows)`

The app command handler routes `/workflow runs` and `/workflow show <run_id>` to these helpers. The helper groups append-only rows by `run_id`, selects the latest row by ledger order, and shows the history length.

## Decision (ADR-lite)

**Context**: The next workflow feature after runner v0 should support observability and recovery foundations before new side effects.

**Decision**: Implement read-only run inspection first. Do not add resume, real approval rows, agent dispatch, condition evaluation, or artifact writes in this slice.

**Consequences**: Users can understand workflow state and append-only history. `/workflow continue` and approval bridge can build on the same run-id visibility next.

## Out of Scope

- `/workflow continue`.
- Real approval row creation or approval resume.
- Agent task dispatch.
- Artifact index writes.
- Input binding and variable interpolation.
- Retry, timeout, cancellation, scheduling, A2A/MCP exposure, trace/eval UI.

## Technical Notes

- Existing runner v0 helpers live in `src/ga_tui/workflows.py`.
- Existing command routing lives in `src/ga_tui/app.py`.
- Existing executable contract lives in `.trellis/spec/backend/agent-control-protocol.md`.
- Current worktree has unrelated untracked `uv.lock`; it must not be included.
