# Add Workflow Runner V0

## Goal

Let `/workflow run <ref>` automatically advance the safe, declarative part of a workflow so users can see AI-owned workflow progress without bypassing the agent harness governance model.

## Requirements

- `/workflow run <ref>` must still validate workflow definitions through the existing manifest-backed loader before any run row is written.
- A valid run must append workflow run ledger rows only; it must not mutate task, progress, approval, artifact, memory, provider, plugin, or runtime-dispatch state.
- The v0 runner may complete only intrinsically safe step types in the workflow run snapshot: `prompt`, `notify`, `pause`, and `artifact_summary`.
- `condition` is declarative but not safely evaluable in v0, so it must stop the runner as an unsupported blocking step.
- `approval` must stop the runner with a waiting-approval status and metadata on the workflow run row, but it must not create a real approval row yet.
- `agent_task` must stop the runner as a dispatch-required step and must not create a subagent, task ledger row, runtime dispatch request, or plugin execution.
- The run ledger must remain append-only: create one initial row, then append an advanced row for the same `run_id` that captures completed safe steps and the terminal status.
- User-facing output must state what advanced, where the run stopped, and that no subagents, approvals, tools, artifacts, task ledger rows, or progress rows were created.
- Pure workflow runner logic belongs in `src/ga_tui/workflows.py`; concrete path selection and JSONL appends remain in `src/ga_tui/app.py`.
- The executable contract must be recorded in `.trellis/spec/backend/agent-control-protocol.md` and protected by `scripts/check_policy_gates.py`.

## Acceptance Criteria

- [ ] A safe-only workflow run completes safe steps and ends with `completed`.
- [ ] A workflow with an `approval` step completes prior safe steps, appends an advanced row with `waiting_approval`, and does not write `approvals.jsonl`.
- [ ] A workflow with an `agent_task` step completes prior safe steps, appends an advanced row with `blocked`, and does not create subagents or task/progress rows.
- [ ] A workflow with a `condition` step stops without evaluating arbitrary expressions.
- [ ] Invalid workflow definitions still reject without appending workflow run rows.
- [ ] `workflows.py` stays pure and does not import app/runtime/UI/governance/ledger/subprocess owners.
- [ ] Targeted tests, policy gate, full tests, build smoke, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.

## Definition of Done

- Tests added/updated for pure runner behavior and app command side effects.
- Policy gate asserts the v0 runner cannot dispatch subagents, create approvals, call tools, execute plugin code, or mutate task/progress/artifact ledgers.
- Backend spec documents the v0 runner scenario with scope, signatures, contracts, validation matrix, good/bad cases, tests, and wrong/correct examples.
- Final architecture comparison confirms the change moves Shuheng closer to the strong-Orchestrator governed harness baseline.

## Technical Approach

Use the existing `build_workflow_run_record(...)` row as the starting snapshot. Add a pure `advance_workflow_run_v0(...)` helper that returns a copied advanced row plus structured step effects. The helper marks safe steps completed until the first unresolved dependency or gated step, then sets the run status to `completed`, `waiting_approval`, or `blocked`.

`app.py` will replace the planned-only wrapper with a run-and-advance wrapper that appends the initial row and then the advanced row for the same `run_id`. All side-effect counters except safe step count remain zero. The append-only ledger shape preserves auditability and lets `latest_records_by_id(..., "run_id")` resolve the newest run state.

## Decision (ADR-lite)

**Context**: Users want AI to automatically do workflow work, but Shuheng's architecture baseline requires strong Orchestrator control, ledger-first progress, approval gates, and bounded workers.

**Decision**: Implement workflow runner v0 as ledger-only progression over safe declarative steps. Block on approval, agent dispatch, condition evaluation, or unsupported execution rather than silently escalating.

**Consequences**: Users get visible automatic workflow advancement now. Real subagent dispatch, approval queue creation, artifact production, plugin execution, condition evaluation, resume commands, and scheduler integration remain explicit future tasks with separate governance contracts.

## Out of Scope

- Creating real approval rows.
- Dispatching subagents or runtime requests.
- Executing tools, shell commands, Python, JavaScript, plugin code, or model calls.
- Mutating task/progress ledgers, artifact indexes, memory queues, Secret Vault, provider state, or A2A/MCP gateways.
- Workflow input binding beyond the existing empty input snapshot.
- `/workflow continue`, scheduled workflows, retries, rollback, or recovery.

## Technical Notes

- Active architecture baseline: `docs/agent-harness-architecture.md`.
- Active backend contract: `.trellis/spec/backend/agent-control-protocol.md`.
- Existing implementation: `src/ga_tui/workflows.py`, `src/ga_tui/app.py`, `tests/test_workflows.py`, `scripts/check_policy_gates.py`.
- Research reference: `research/workflow-runner-v0-design.md`.
