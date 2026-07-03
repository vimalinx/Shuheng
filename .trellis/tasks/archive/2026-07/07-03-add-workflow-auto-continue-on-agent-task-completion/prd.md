# Add Workflow Auto-Continue On Agent Task Completion

## Goal

Make workflow `agent_task` steps actually feel automatic: after a workflow-owned subagent task finishes and `process_ui_queue(...)` records the terminal task result, Shuheng should automatically continue any workflow run waiting on that task id. This should use the existing workflow continuation and governed subagent task pipeline, not a new executor.

## What I Already Know

- Previous slice added workflow `agent_task` bridge:
  - `/workflow run` can dispatch a governed subagent task.
  - workflow rows store step-level `task_id`, `task_status`, `agent_id`, and artifact refs.
  - `/workflow continue <run_id>` can advance after the task reaches a terminal status.
- Current remaining usability gap: users still have to manually run `/workflow continue <run_id>` after the subagent task completes.
- `process_ui_queue(...)` is the authoritative event pump that writes terminal subagent task rows and result artifacts.
- `continue_workflow_run_v0(...)` already implements the correct terminal-task behavior.
- Architecture baseline requires a strong Orchestrator, explicit ledgers, artifact refs, approval gates, and auditable protocols.

## Research References

- [`research/workflow-auto-continue-design.md`](research/workflow-auto-continue-design.md) — auto-continuation should be a narrow app-side event bridge after terminal task ledger writes, not a new workflow engine.

## Requirements

- When a non-Secret subagent task completes through `process_ui_queue(...)`, detect workflow runs whose latest row is waiting on that task id.
- For each affected workflow run, call the existing `continue_workflow_run_v0(run_id, state=state)` after the task ledger has the terminal row.
- If the task completed successfully, auto-continuation must append one workflow run row that marks the `agent_task` step completed, copies artifact refs, and advances later runner-v0 safe steps.
- If the task failed, was rejected, cancelled, canceled, or aborted, auto-continuation must append one terminal workflow run row and leave later steps pending.
- If no workflow run is waiting on the task id, do nothing.
- If the workflow already has a terminal latest row, do nothing.
- If a workflow waiting row's task is still non-terminal, do nothing.
- Auto-continuation must not duplicate-dispatch agent tasks.
- Auto-continuation must not resume approval waits, self-approve, or create approval rows.
- Auto-continuation must not run for Secret Vault subagent task results in this slice.
- Keep `workflows.py` pure.
- Update tests, policy gates, and `.trellis/spec/backend/agent-control-protocol.md`.

## Acceptance Criteria

- [ ] A workflow `prompt -> agent_task -> notify` reaches `waiting_task` after `/workflow run`.
- [ ] After the subagent task result is processed by `process_ui_queue(...)`, the workflow automatically appends a completed row without the user running `/workflow continue`.
- [ ] The auto-completed workflow row copies the subagent result artifact refs and completes later safe steps.
- [ ] A failed subagent result automatically appends one failed workflow row and leaves later steps pending.
- [ ] Calling `/workflow continue <run_id>` after auto-completion reports already completed and appends no extra row.
- [ ] Auto-continuation does nothing for unrelated completed subagent tasks.
- [ ] Auto-continuation does not duplicate-dispatch or create a second task id for the same workflow step.
- [ ] Existing explicit `/workflow continue` behavior still works.
- [ ] Existing approval bridge behavior remains explicit and unchanged.
- [ ] Targeted tests, policy gate, full tests, build smoke, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.

## Definition of Done

- Tests cover successful auto-continuation, failed auto-termination, unrelated task no-op, duplicate prevention, and explicit continue compatibility.
- Backend spec documents the workflow auto-continue event bridge in seven executable sections.
- Final report compares the change to `docs/agent-harness-architecture.md`.
- The unrelated untracked `uv.lock` remains excluded.

## Technical Approach

- Add app-owned helpers:
  - find latest workflow rows whose pending `agent_task` step has the completed `task_id`;
  - auto-continue those runs once via `continue_workflow_run_v0(...)`;
  - optionally add a short system notice so users can see that workflow continuation happened automatically.
- Call the helper from the non-Secret `sub_stream` done branch in `process_ui_queue(...)` after `append_task_ledger(...)` writes the terminal row and before/around existing orchestrator continuation notices.
- Reuse `continue_workflow_run_v0(...)` instead of duplicating terminal task result logic.

## Out of Scope

- Automatic workflow start from schedule/timer.
- Retry, timeout, cancel UI, or backoff policies.
- Parallel/fan-out/fan-in workflow graphs.
- Condition expression evaluation.
- Secret Vault workflow task auto-continuation.
- A2A/MCP workflow service exposure.
- Cross-process daemon recovery beyond append-only row inspection in the current UI process.

## Technical Notes

- Existing workflow code: `src/ga_tui/workflows.py`, `src/ga_tui/app.py`.
- Existing completion event path: `process_ui_queue(...)` `kind == "sub_stream"` and `done`.
- Existing continuation path: `continue_workflow_run_v0(...)`.
- Existing tests: `tests/test_workflows.py`.
- Existing policy gate: `scripts/check_policy_gates.py`.
- Spec target: `.trellis/spec/backend/agent-control-protocol.md`.
- Architecture baseline: `docs/agent-harness-architecture.md`.
