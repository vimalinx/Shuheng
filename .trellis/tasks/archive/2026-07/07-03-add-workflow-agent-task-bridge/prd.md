# Add Workflow Agent Task Bridge

## Goal

Make workflow `agent_task` steps create and track real governed subagent tasks so workflows can start doing AI work automatically. This is the next step after workflow run ledgers, continue/resume, and the approval bridge: the workflow runner should dispatch one subagent task for an `agent_task` step, record the returned `task_id`, wait while the task is running or approval-gated, and continue runner-v0 safe steps after the subagent task reaches a terminal result.

## What I Already Know

- Workflow runner v0 currently completes safe steps and blocks at `agent_task` with no subagent/task/progress side effects.
- The approval bridge already allows `approval` steps to create real `agentapproval.v1` rows and continue only after `/approve`.
- Shuheng already has a governed subagent task path:
  - `start_subagent_task(...)` owns policy gates, single-writer locks, context packs, task ledger rows, progress rows, mail, checkpoints, traces, runtime dispatch, and result artifact writes.
  - `start_subagent_task_structured(...)` wraps `start_subagent_task(...)` and returns status/task_id/provider metadata.
  - `process_ui_queue(...)` marks subagent task rows `completed` or `failed` and writes result artifacts.
  - `latest_task_records()` gives the latest task row by `task_id`.
- Plugin agent templates already exist and can create real subagents through `create_subagent_from_plugin_template(...)`.
- Architecture baseline requires a strong Orchestrator, restricted subagents, shared task/progress ledgers, artifact refs, single-writer enforcement, human approvals, and auditable communication.

## Requirements

- When `/workflow run <ref>` or `/workflow continue <run_id>` reaches an `agent_task` step, dispatch exactly one governed subagent task through the existing subagent task path.
- Attach the created `task_id` to the blocked workflow step snapshot.
- Move the workflow run to a waiting status while the subagent task is non-terminal.
- `/workflow continue <run_id>` while the subagent task is still `working`, `running`, `pending`, `created`, `queued`, or `approval_required` must append no workflow row and must report the current task status.
- If the subagent task reaches `completed`, `/workflow continue <run_id>` must mark the workflow step completed, copy artifact refs from the task row into the workflow step and top-level `artifact_refs`, then continue runner-v0 safe steps.
- If the subagent task reaches `failed`, `rejected`, `cancelled`, `canceled`, or `aborted`, `/workflow continue <run_id>` must append one terminal workflow row with the corresponding failed/rejected/cancelled status and must not continue later steps.
- If the `agent_task.agent` value resolves to an existing subagent id/name, use that subagent.
- If the `agent_task.agent` value is a plugin agent template ref, create a real subagent from the template once at dispatch time and use that subagent for the task.
- If the workflow row already has a `task_id`, continuation must never dispatch another subagent task for the same step.
- Keep `workflows.py` pure: no app imports, no JSONL I/O, no subagent/runtime dispatch, no ledger writes.
- Keep concrete side effects in `app.py` under the existing Orchestrator-owned subagent/task path.
- Update tests, policy gates, and `.trellis/spec/backend/agent-control-protocol.md`.

## Acceptance Criteria

- [ ] A workflow with `prompt -> agent_task -> notify` creates two workflow rows on `/workflow run`: `planned` and `waiting_task`.
- [ ] The latest workflow row has the subagent task id attached to the `agent_task` step.
- [ ] Task/progress ledgers contain the real subagent task rows produced by `start_subagent_task(...)`.
- [ ] `/workflow continue <run_id>` before the subagent result appends no workflow row and reports that the task is still pending/working.
- [ ] After the subagent result is processed as `completed`, `/workflow continue <run_id>` appends one workflow row where the `agent_task` step is completed, artifact refs are copied, and later safe steps continue.
- [ ] If the subagent result is `failed`, `/workflow continue <run_id>` appends one terminal failed workflow row and leaves later steps pending.
- [ ] A plugin template agent ref can auto-create one scoped subagent and dispatch to it.
- [ ] Re-running `/workflow continue` for a waiting task does not create duplicate subagents or duplicate task ids.
- [ ] Existing approval bridge behavior remains unchanged.
- [ ] `condition` steps still do not evaluate expressions.
- [ ] Secret Vault stays out of scope for this bridge.
- [ ] Targeted tests, policy gate, full tests, build smoke, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.

## Definition of Done

- Tests cover dispatch, pending no-op, completed continuation, failed termination, plugin template creation, duplicate-dispatch prevention, and existing approval/condition invariants.
- Backend spec documents the workflow agent task bridge in seven executable sections.
- Final report compares the change to `docs/agent-harness-architecture.md`.
- The unrelated untracked `uv.lock` remains excluded.

## Technical Approach

- Add pure workflow helpers to:
  - locate a pending `agent_task` step,
  - read an existing workflow step `task_id`,
  - attach a subagent task id to a workflow row,
  - apply terminal task results to a workflow row before runner-v0 continuation.
- Add app helpers to:
  - resolve existing subagents or plugin template refs for an `agent_task` step,
  - dispatch one subagent task through `start_subagent_task_structured(...)`,
  - append the waiting workflow row with `task_id`,
  - consult `latest_task_records()` during `/workflow continue`.
- Reuse existing subagent governance instead of creating a parallel workflow task executor.
- Keep `/workflow continue` explicit; a subagent completion event should not auto-continue the workflow in this task.

## Decision (ADR-lite)

**Context**: The user wants workflow automation to move beyond dry-run and ledger-only safe steps. `agent_task` is the first real AI-work step, but Shuheng already has a governed subagent task pipeline.

**Decision**: Bridge workflow `agent_task` into the existing subagent task pipeline and store only `task_id` plus task status/artifact refs in workflow rows.

**Consequences**: This keeps Orchestrator governance, policy gates, single-writer locks, context packs, and artifact provenance intact. The trade-off is that workflow continuation remains explicit and step-by-step for now; automatic background workflow resumption, retry policy, and scheduler integration stay out of scope.

## Out of Scope

- Condition evaluation.
- Parallel/fan-out/fan-in workflow execution.
- Automatic workflow continuation when a subagent finishes.
- Retry, timeout, cancellation UI, or scheduled workflow execution.
- Direct tool/model provider calls from workflow steps.
- Secret Vault workflow agent tasks.
- A2A/MCP workflow service exposure.
- Cross-process recovery of active runtime streams beyond existing task-ledger inspection.

## Technical Notes

- Existing workflow code: `src/ga_tui/workflows.py`, `src/ga_tui/app.py`.
- Existing subagent task path: `start_subagent_task(...)`, `start_subagent_task_structured(...)`, `process_ui_queue(...)`, `latest_task_records()`.
- Existing plugin template path: `plugin_agent_template_for_ref(...)`, `create_subagent_from_plugin_template(...)`.
- Existing spec section: `.trellis/spec/backend/agent-control-protocol.md`.
- Architecture baseline: `docs/agent-harness-architecture.md`.
