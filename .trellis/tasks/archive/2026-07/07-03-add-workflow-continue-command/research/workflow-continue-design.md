# Workflow Continue Design Note

## Question

What is the next safest workflow capability after run inspection?

## Evidence

- Mature workflow engines treat durable run state and event/history ledgers as the source of truth for resume and recovery.
- Shuheng already stores append-only workflow run rows and can inspect the latest row per `run_id`.
- The architecture baseline requires a strong Orchestrator, explicit ledgers, artifact references, approval gates, auditable protocols, and restricted workers.
- Runner v0 intentionally does not dispatch agents, create approvals, evaluate conditions, call tools, or write artifacts.

## Decision

Add `/workflow continue <run_id>` as a bounded command that resumes from the latest row and advances only runner-v0 safe steps.

## Guardrails

- Read all `workflow_runs.jsonl` rows, select latest by ledger order, append at most one new row.
- Do not append when the run is missing, unknown, completed, or cannot make runner-v0 safe progress.
- Do not mutate task, progress, approval, artifact, memory, Secret Vault, provider, runtime, plugin, or subagent state.
- Defer real approval resume and subagent dispatch to later tasks with their own specs and gates.
