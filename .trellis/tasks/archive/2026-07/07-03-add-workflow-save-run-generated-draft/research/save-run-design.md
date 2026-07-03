# Save-And-Run Generated Workflow Draft Design Note

## Question

How can Shuheng make AI-generated workflows more automatic without weakening the governed workflow architecture?

## Repo Evidence

- `/workflow generate <goal>` uses a `workflow_generate` source and only stores a validated draft in `State`.
- `/workflow save-last <plugin-id>/<workflow-id>` persists the latest valid draft as a normal plugin workflow and refreshes the registry.
- `/workflow run <ref>` validates a manifest-backed workflow, appends normal `workflow_runs.jsonl` rows, and delegates `approval` / `agent_task` side effects to existing app-owned bridges.
- `process_ui_queue(...)` already blocks TUI controls and interaction payloads on workflow generation source paths.

## Options Considered

### Option A: Explicit `/workflow run-last <plugin-id>/<workflow-id>` (recommended)

- Save the latest draft through the existing save path.
- Load the saved workflow through the plugin registry.
- Run it through `create_workflow_run_v0(...)`.

Pros:
- Requires explicit user intent after generation.
- Keeps manifest-backed source of truth.
- Reuses existing runner, approval bridge, agent task bridge, and ledgers.
- Easy to test as save rows plus normal run rows.

Cons:
- Still requires two commands after natural-language generation: generate, then run-last.

### Option B: `/workflow generate-run <plugin-id>/<workflow-id> <goal>`

- Starts a generation task, then automatically saves and runs when the model returns valid JSON.

Pros:
- Fewer user commands.

Cons:
- More asynchronous state coupling.
- Higher risk of accidentally executing a poor model draft.
- Harder to keep generation completion visibly non-executing.

### Option C: Run in-memory draft without saving

- Build a workflow run row from cached draft state directly.

Pros:
- Avoids file writes.

Cons:
- Creates a second workflow source of truth.
- Weakens artifact provenance and registry inspection.

## Decision

Use Option A for this slice. It moves toward automation while keeping execution explicit, saved, inspectable, and governed.

## Guardrails

- Do not run directly from in-memory model output.
- Do not add runner logic to `workflows.py`.
- Do not duplicate approval/subagent bridge logic in the new command.
- Do not write task/progress/approval/artifact ledgers unless the existing workflow runner and bridges do it.
- Do not treat `/workflow generate` completion as permission to run.
