# Add Workflow Cancel Command V1

## Goal

Add a first-class manual workflow lifecycle control: `/workflow cancel <run_id> [reason...]`.

The feature lets the Orchestrator mark an active workflow run as cancelled without advancing pending steps, dispatching new subagents, creating approvals, reading artifacts, or mutating unrelated ledgers. This closes a basic production workflow gap discovered during workflow capability analysis: once a workflow is planned, blocked, or waiting, the user needs an explicit terminal control before higher-level automation such as retry, timeout, checkpoint/replay, or auto-recovery is safe.

## Requirements

* Add a TUI command `/workflow cancel <run_id> [reason...]`.
* Unknown `run_id` must render a visible not-found result and append no workflow row.
* A latest row whose workflow status is `completed` must render an already-completed/no-op result and append no workflow row.
* A latest row whose workflow status is terminal (`failed`, `rejected`, `cancelled`, `canceled`, or `aborted`) must render an already-terminal/no-op result and append no workflow row.
* A latest non-terminal row must append exactly one workflow run row with the same `run_id` and terminal status `cancelled`.
* Cancelled rows must preserve workflow provenance and definitions while setting cancellation timestamps and a human-readable cancellation reason.
* Currently blocked or waiting steps may be marked `cancelled`; future pending steps must not be advanced.
* Cancellation must not abort or mutate underlying subagent tasks in this slice. It only stops workflow continuation.
* Cancellation must not write task, progress, approval, or artifact ledger rows.
* `workflows.py` remains pure and owns only deterministic state transformation and formatting.
* `app.py` remains the Orchestrator owner for command routing, latest-row lookup, and ledger append.
* Help/usage text must mention `/workflow cancel`.

## Acceptance Criteria

* [ ] `/workflow cancel <known-active-run>` appends exactly one cancelled workflow run row.
* [ ] `/workflow cancel <unknown-run>` appends no row and tells the user the run was not found.
* [ ] `/workflow cancel <completed-run>` appends no row and tells the user it is already completed.
* [ ] `/workflow cancel <terminal-run>` appends no row and tells the user it is already terminal.
* [ ] Cancelling a blocked or waiting row does not continue later steps.
* [ ] Cancelling a row with side-effect-capable steps writes no task/progress/approval/artifact rows.
* [ ] Unit tests cover pure helper behavior and formatter output.
* [ ] Policy gates assert the command boundary and side-effect invariants.
* [ ] Backend spec records the workflow cancel contract.

## Definition Of Done

* Targeted compile, Ruff, workflow tests, and policy gates pass.
* Full test suite passes.
* Release hygiene, diff whitespace, source compileall, build, wheel smoke, integration doctor, and `shuheng-check` pass.
* Task commit excludes pre-existing untracked `uv.lock`.
* Final report compares this change to `docs/agent-harness-architecture.md`.

## Technical Approach

Add a pure cancel result/helper pair to `src/ga_tui/workflows.py`, then wire it through `src/ga_tui/app.py` as an Orchestrator command. The app helper loads the latest workflow run row, asks the pure workflow helper whether cancellation is meaningful, appends the returned cancelled row when required, and formats the visible result.

The command should mirror `/workflow continue` lifecycle semantics: no-op for missing/completed/terminal rows, exactly one row for a meaningful state transition, and no non-workflow side effects.

## Decision (ADR-lite)

**Context**: Workflow systems need explicit lifecycle controls before reliable automation can be layered on top. Current Shuheng workflow support can plan, run, block, continue, bridge approvals, bridge subagent tasks, pass artifact references, and reject invalid DAGs, but lacks user-controlled cancellation.

**Decision**: Implement manual cancel v1 as a workflow-ledger-only terminal transition. Do not cancel subprocesses, subagent tasks, approvals, retries, timeouts, or checkpoints in this slice.

**Consequences**: The feature is small and safe, keeps `app.py` as the strong Orchestrator, and creates a stable lifecycle primitive. Later work can add task abort, timeout, retry, checkpoint/replay, and fan-out/fan-in semantics on top of this terminal-state contract.

## Out Of Scope

* Auto timeout.
* Retry or retry policy.
* Aborting or killing already-dispatched subagent/runtime tasks.
* Cancelling approval rows.
* Parallel fan-out/fan-in scheduling.
* Checkpoint/replay or recovery.
* Workflow artifact hydration.
* Plugin code execution.
* A2A/MCP workflow service exposure.

## Research References

* [`research/workflow-cancel-patterns.md`](research/workflow-cancel-patterns.md) - Official docs comparison for workflow cancellation/termination patterns.

## Technical Notes

* Relevant spec: `.trellis/spec/backend/agent-control-protocol.md`.
* Relevant architecture baseline: `docs/agent-harness-architecture.md`.
* Relevant code: `src/ga_tui/workflows.py`, `src/ga_tui/app.py`, `tests/test_workflows.py`, `scripts/check_policy_gates.py`.
* Existing terminal statuses include `cancelled`, `canceled`, and `aborted`; this command should write canonical `cancelled`.
