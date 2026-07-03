# AI Workflow Generation Design Note

## Question

How should Shuheng let AI create workflows while preserving the governed workflow/plugin architecture?

## Repo Evidence

- Existing workflows are manifest-backed plugin data under `plugin://<plugin-id>/workflows/<workflow-id>`.
- `workflows.py` already validates schema version, workflow id, inputs, steps, dependencies, supported step types, and JSON/fenced-JSON bodies.
- `/workflow dry-run` is side-effect-free, while `/workflow run` is the governed entry point that appends workflow run rows and delegates approval/agent_task side effects to app-owned bridges.
- The latest auto-continue bridge already gives workflow `agent_task` steps the expected "AI keeps going after subagent completion" feel after a workflow exists.
- `app.py` is the only acceptable owner for model calls, state mutation, file writes, plugin registry refresh, and user-visible command side effects.

## Options Considered

### Option A: Draft then save as plugin workflow (recommended)

- `/workflow generate <goal>` asks the model for a bounded JSON workflow draft.
- Shuheng parses/validates the draft and stores it in state.
- `/workflow save-last <plugin-id>/<workflow-id>` writes `plugin.json` and `workflows/<workflow-id>.json`.
- Existing `/workflow dry-run` and `/workflow run` own all later behavior.

Pros:
- Preserves manifest-backed source of truth.
- Keeps AI output inspectable before execution.
- Avoids a hidden workflow executor or separate storage model.
- Makes regression tests straightforward.

Cons:
- Requires a second save command before running.

### Option B: Generate and run immediately

- Model output is parsed and run in one command.

Pros:
- Lowest friction for the user.

Cons:
- Harder to audit.
- Makes accidental execution more likely.
- Blurs model generation, file persistence, and workflow execution boundaries.

### Option C: Hidden draft store only

- Store generated workflows in a separate JSONL draft ledger and run from draft ids.

Pros:
- Avoids writing plugin files.

Cons:
- Creates a second workflow source of truth.
- Existing registry/panel/dry-run commands would not automatically see generated workflows.

## Decision

Use Option A. AI generation produces only a validated declarative draft. Saving converts the draft into a normal plugin workflow file. Running stays in the existing workflow command path.

## Guardrails

- Do not execute model output directly.
- Do not accept shell/Python/JS/plugin-code fields as executable.
- Do not write outside the user plugin root.
- Do not overwrite unrelated plugin metadata except adding/updating the target workflow entry.
- Do not dispatch subagents, create approvals, or append workflow run/task/progress ledgers during generate or save.
- Preserve explicit user action before run: `/workflow run <plugin-id>/<workflow-id>`.
