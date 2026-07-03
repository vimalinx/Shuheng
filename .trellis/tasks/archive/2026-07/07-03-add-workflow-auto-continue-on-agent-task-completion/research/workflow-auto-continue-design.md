# Workflow Auto-Continue Design Note

## Question

How should Shuheng make workflows continue automatically after a workflow-owned subagent task completes without creating a second workflow engine?

## External Evidence

- Temporal treats workflow progress as durable event history plus deterministic replay. External work is done by Activities; completed activity results are recorded and reused rather than recomputed.
- LangGraph separates short-term thread checkpoints from longer-term stores. This maps to Shuheng's append-only workflow run rows plus task/artifact ledgers.
- Prefect and Airflow both make workflow runs observable state machines. Tasks are separate units of work, and schedulers/automation should not hide task state.

## Repo Evidence

- `process_ui_queue(...)` is the existing app-side event pump that handles completed `sub_stream` items, writes the terminal task ledger row, writes result artifacts, checkpoints, traces, eval rows, and user notices.
- `continue_workflow_run_v0(...)` already knows how to advance a workflow from a terminal task row: completed tasks copy artifact refs and continue safe steps; failed/rejected/cancelled tasks stop the workflow.
- `workflows.py` is intentionally pure and must not read task ledgers, dispatch subagents, or append workflow rows.
- Workflow rows currently identify waiting agent tasks by step-level `task_id`, which matches the subagent `bus_task_id`.

## Decision

After `process_ui_queue(...)` finishes writing the terminal subagent task row for a non-Secret `sub_stream`, call a small app-owned helper that finds workflow runs waiting on that `task_id` and invokes `continue_workflow_run_v0(run_id, state=state)` once per affected run.

## Guardrails

- Do not auto-continue before the terminal task ledger row exists.
- Do not auto-dispatch new agent tasks from this helper; it only resumes rows that already have the completed/failed `task_id`.
- Do not auto-continue while a subagent task is non-terminal.
- Do not auto-resume approval waits; human approval continuation remains explicit.
- Do not auto-continue Secret Vault workflow tasks in this slice.
- Do not add a scheduler, retry loop, background worker, or workflow-owned executor.
- Keep `workflows.py` pure; app.py owns ledger lookup and workflow row append side effects.

## Consequence

This is a narrow automation layer: completed subagent tasks can unblock workflow runs in the same UI event cycle, while all durable state and provenance still live in the existing workflow, task, progress, artifact, checkpoint, and trace ledgers.
