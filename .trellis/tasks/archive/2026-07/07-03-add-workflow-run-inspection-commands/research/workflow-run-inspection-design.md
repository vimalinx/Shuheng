# Workflow Run Inspection Design Note

## Question

What is the next safest workflow capability after runner v0?

## Evidence

- Current Shuheng runner v0 appends two rows per successful `/workflow run`: an initial `planned` row and an advanced row with the same `run_id`.
- Mature systems such as Temporal, LangGraph, OpenAI Agents SDK, and Prefect all treat run state visibility as foundational for durable/resumable workflow execution.
- Shuheng's architecture baseline emphasizes append-only ledgers, artifact references, human approval gates, and auditable protocols before autonomous side effects.

## Decision

Add read-only workflow run inspection commands before resume or dispatch:

- `/workflow runs`: latest row per run id.
- `/workflow show <run_id>`: latest row plus append-only history count and step details.

## Guardrails

- Inspection commands read only `workflow_runs.jsonl`.
- No mutation of workflow, task, progress, approval, artifact, memory, Secret Vault, provider, runtime, or plugin state.
- No hidden continuation, retry, approval creation, subagent dispatch, condition evaluation, or tool execution.
