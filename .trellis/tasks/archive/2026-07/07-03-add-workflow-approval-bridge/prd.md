# Add Workflow Approval Bridge

## Goal

Make workflow `approval` steps use the existing Shuheng approval ledger instead of remaining an in-row placeholder. When runner v0 reaches an approval step, it should create a real `agentapproval.v1` row, attach the approval id to the workflow run row, show it in `/approvals`, and allow `/workflow continue <run_id>` to proceed only after the approval row is approved.

## What I Already Know

- Workflow runner v0 currently stops at `approval` with `status=waiting_approval`, `approval_status=pending`, and no `approval_id`.
- The previous workflow slices added append-only `workflow_runs.jsonl`, `/workflow runs`, `/workflow show <run_id>`, and `/workflow continue|resume <run_id>`.
- Shuheng already has a general approval system:
  - `governance.queue_approval(...)` writes `agentapproval.v1` rows.
  - `app.queue_approval(...)` wraps it and also writes approval inbox mail.
  - `/approvals` displays pending approval rows.
  - `/approve <id>` and `/reject <id>` update approval rows through `decide_approval(...)`.
- Unknown approval types are safe: approval/rejection updates the row and returns a message without running a deferred operation.
- The architecture baseline requires program-level human approval gates and auditable communication, not model-self-approved continuation.

## Requirements

- When `/workflow run <ref>` reaches an `approval` step, create exactly one `agentapproval.v1` row for that step.
- Attach the created `approval_id` to:
  - the workflow run `approval.approval_id`,
  - `approval.approval_required_for`,
  - the blocked workflow step's `approval_id`,
  - execution metadata showing one approval was created.
- The approval row must include enough payload to audit and resume: `run_id`, `workflow_ref`, `workflow_id`, `step_id`, step name/type, and source command context.
- `/approvals` must show the workflow approval because it uses the existing approval ledger.
- `/workflow continue <run_id>` while the approval is pending must report that approval is pending and append no workflow row.
- After `/approve <approval_id>`, `/workflow continue <run_id>` must mark the approval step completed and continue runner-v0 safe steps from the resulting row.
- After `/reject <approval_id>`, `/workflow continue <run_id>` must append a terminal rejected workflow row and must not continue later steps.
- Legacy workflow rows that are `waiting_approval` without an `approval_id` should be bridgeable by `/workflow continue <run_id>` by creating and attaching a real approval row.
- Continue must not dispatch subagents, evaluate conditions, call tools/model providers, execute plugin code, write artifacts, mutate task/progress ledgers, write memory, touch Secret Vault, schedule work, or expose A2A/MCP workflow services.
- Keep `workflows.py` pure: no app imports, no JSONL I/O, no approval ledger writes.
- Update tests, policy gates, and `.trellis/spec/backend/agent-control-protocol.md`.

## Acceptance Criteria

- [ ] `/workflow run` for a workflow with an approval step creates two workflow rows and one approval row.
- [ ] The latest workflow row contains the approval id in both top-level approval metadata and the approval step snapshot.
- [ ] `/approvals` lists the workflow approval.
- [ ] `/workflow continue <run_id>` before approval appends no workflow row and reports pending approval.
- [ ] `/approve <approval_id>` followed by `/workflow continue <run_id>` appends one row where the approval step is completed and later safe steps continue.
- [ ] `/reject <approval_id>` followed by `/workflow continue <run_id>` appends one terminal rejected workflow row.
- [ ] Legacy waiting-approval rows without an approval id are upgraded by `/workflow continue` by creating one approval row and appending one workflow row with that id.
- [ ] Existing agent-task blocked workflows still do not create subagents/task/progress rows.
- [ ] Policy gates assert no subagent/tool/artifact/task/progress side effects occur through approval bridge continuation.
- [ ] Targeted tests, policy gate, full tests, build smoke, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.

## Definition of Done

- Tests cover approval creation, pending no-op, approved continuation, rejected termination, legacy id attachment, and side-effect invariants.
- Backend spec documents the approval bridge command/run contract with seven executable sections.
- Final report compares the change to `docs/agent-harness-architecture.md`.

## Technical Approach

- Add pure workflow helpers to:
  - locate a pending workflow approval step,
  - attach an approval id to a waiting workflow row,
  - apply approved/rejected approval decisions to a workflow row before runner-v0 continuation.
- Keep concrete approval row creation in `app.py` via the existing `queue_approval(...)`.
- Keep `/approve` and `/reject` behavior generic; they update approval rows but do not automatically run workflow continuation.
- Let `/workflow continue` read approval row status and decide whether to wait, reject, or advance.

## Decision

Use a custom approval row type such as `workflow_step_approval`. This makes workflow approvals visible and auditable through existing approval surfaces while avoiding new deferred side effects in `decide_approval(...)`.

## Out of Scope

- Automatic workflow continuation immediately inside `/approve`.
- Real `agent_task` dispatch.
- Condition evaluation.
- Artifact index writes.
- Tool/model provider calls from workflow steps.
- Retry, timeout, cancellation, scheduling, input binding, or MCP/A2A workflow service exposure.

## Technical Notes

- Approval functions live in `src/ga_tui/app.py` and `src/ga_tui/governance.py`.
- Workflow pure helpers live in `src/ga_tui/workflows.py`.
- Existing workflow contracts live in `.trellis/spec/backend/agent-control-protocol.md`.
- Current worktree has unrelated untracked `uv.lock`; it must not be included.
