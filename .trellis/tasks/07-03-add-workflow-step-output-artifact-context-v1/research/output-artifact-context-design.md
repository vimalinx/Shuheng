# Workflow Step Output Artifact Context Design Note

## Design Question

How can Shuheng let later workflow steps use earlier step outputs without turning workflow execution into an unsafe template engine or artifact reader?

## Current Repo Constraints

- Workflow run rows already store per-step `artifact_refs`, `task_id`, `task_status`, and top-level `artifact_refs`.
- Completed subagent task artifacts are attached through the existing Workflow Agent Task Bridge.
- `workflow_agent_task_prompt(...)` currently returns the user-defined prompt without workflow output context.
- `workflows.py` remains the pure run-row transformation owner; `app.py` remains the only dispatch and ledger owner.

## Comparable Patterns

- Durable workflow systems pass data between steps through explicit state, not hidden chat context.
- Agent systems prefer artifact references over large message copying so the Orchestrator can preserve provenance and hydrate only when needed.
- CI/DAG systems separate dependency references from execution: a downstream job may receive a pointer to an artifact, but artifact fetching is an explicit later operation.

## Options

### Option A: Raw artifact content injection

- How it works: downstream prompts include the text content of upstream artifacts.
- Pros: immediately useful for models.
- Cons: expands scope to file reads, size limits, secret scanning, provenance, and content trust.
- Decision: out of scope for v1.

### Option B: Reference-only context block (recommended)

- How it works: downstream prompts append a bounded section listing completed upstream step ids, task ids, agent ids, and artifact refs.
- Pros: safe, auditable, aligns with artifact-reference-first architecture, and fits existing ledgers.
- Cons: downstream agents must fetch or reason from refs later through governed paths.
- Decision: implement this first.

### Option C: Free-form prompt templating

- How it works: workflow authors write placeholders such as `{{steps.review.output}}`.
- Pros: expressive and familiar.
- Cons: creates a template language, unclear error behavior, and pressure to read artifacts/files/task bodies.
- Decision: reject for v1.

## MVP Contract

- Collect only completed upstream step reference metadata.
- Respect explicit `depends_on` before falling back to prior completed steps.
- Append a deterministic prompt context block only when references exist.
- Do not read artifact files, task bodies, environment, Secret Vault, model output text, or tools.

## Architecture Fit

This moves Shuheng toward the baseline because it makes artifact references first-class in workflow communication while preserving the strong Orchestrator and single-writer model. It avoids "agents chatting" and instead passes bounded, auditable references through workflow run state.
