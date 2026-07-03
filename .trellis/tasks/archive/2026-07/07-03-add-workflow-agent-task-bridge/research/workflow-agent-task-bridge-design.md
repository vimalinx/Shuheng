# Workflow Agent Task Bridge Design Note

## Question

How should workflow `agent_task` steps execute without bypassing Shuheng's existing Orchestrator governance?

## Evidence

- `start_subagent_task(...)` already owns policy gates, single-writer locks, context packs, task/progress ledgers, mail, checkpoints, traces, runtime dispatch, and result artifact writes.
- `start_subagent_task_structured(...)` returns a structured dispatch result including status and `task_id`.
- `process_ui_queue(...)` updates the task ledger to `completed` or `failed` and records result artifact refs.
- Workflow rows are append-only durable snapshots and should reference subagent task ids instead of duplicating subagent execution state.
- The architecture baseline says workflow orchestration should be a strong Orchestrator plus restricted workers, not a second execution stack.

## Decision

Use the existing subagent task pipeline as the execution authority. Workflow `agent_task` bridge only resolves the target subagent/template, dispatches through `start_subagent_task_structured(...)`, attaches the returned `task_id`, and later interprets the latest task row during explicit `/workflow continue`.

## Guardrails

- Do not create a second task ledger or workflow-owned subagent executor.
- Do not bypass policy gates, approval gates, context packs, single-writer locks, or result artifact provenance.
- Do not dispatch again if a workflow step already has a `task_id`.
- Do not auto-continue the workflow from `/approve` or from subagent completion events in this task.
- Keep `workflows.py` pure and app-side effects in `app.py`.
