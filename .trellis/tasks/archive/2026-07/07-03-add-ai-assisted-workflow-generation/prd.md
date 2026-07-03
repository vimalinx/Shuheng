# Add AI-Assisted Workflow Generation

## Goal

Let users ask Shuheng to design a workflow in natural language and turn the AI-produced workflow draft into a normal manifest-backed plugin workflow that can be inspected, dry-run, and run through the existing governed workflow runner.

## What I Already Know

- Users currently must hand-write plugin workflow JSON files before `/workflow dry-run` or `/workflow run` can work.
- The user explicitly asked whether AI can do the workflow work automatically.
- Current workflow runtime already supports manifest-backed workflow discovery, dry-run, planned/advanced workflow rows, approval bridge, agent_task bridge, and event-driven auto-continue after subagent task completion.
- `workflows.py` is pure and must remain responsible for parsing, validation, formatting, and data-only helpers.
- `app.py` owns Orchestrator side effects, command routing, plugin/workflow file writes, model calls, ledgers, approvals, and user-visible system messages.
- Plugin workflow files are data-only JSON objects with schema version `shuheng.workflow.v1`; executable plugin code, arbitrary shell/Python/JS, hidden tool calls, permission overrides, and approval bypasses are forbidden.
- Prior workflow design research and specs show the correct architecture is deterministic workflow state plus governed side-effect bridges, not a hidden workflow executor.

## Research References

- `.trellis/tasks/archive/2026-07/07-03-add-workflow-registry-dry-run/research/workflow-design.md` - workflows should start as declarative manifest-backed data, not executable plugin code.
- `.trellis/tasks/archive/2026-07/07-03-add-workflow-runner-v0/research/workflow-runner-v0-design.md` - runner v0 advances safe ledger steps and delegates side effects to app-owned bridges.
- `research/ai-workflow-generation-design.md` - this task's local design note for AI draft generation and save boundaries.

## Requirements

- Add a command that asks the active AI runtime to generate a workflow draft from a natural-language goal.
- The AI generation prompt must require a single JSON object using schema version `shuheng.workflow.v1`.
- The generated draft must be parsed through existing workflow validation logic before it is presented as usable.
- Store the latest generated draft in app state so a follow-up save command can persist it without asking the model again.
- Add a save command that writes the latest valid draft into the user plugin root under a manifest-backed plugin package.
- Saving must update or create the plugin `plugin.json` workflow entry and write the workflow file inside the plugin root.
- Saved workflows must immediately be visible to `/workflows`, `/workflow info`, `/workflow dry-run`, and `/workflow run`.
- Generated workflow ids, plugin ids, and file paths must be filesystem-safe and use the existing plugin id rules.
- The generation/save flow must never execute workflow steps, dispatch subagents, create approvals, write workflow run rows, write task/progress rows, or call tools by itself.
- Existing `/workflow run`, continue, approval, agent_task, and auto-continue behavior must remain unchanged.
- Secret Vault unlocked mode must continue blocking `/workflow` commands.

## Acceptance Criteria

- [ ] `/workflow generate <goal>` sends a bounded workflow-generation prompt to the active AI runtime.
- [ ] When the runtime returns valid JSON, Shuheng stores a latest workflow draft and shows a visible preview with validation status.
- [ ] `/workflow save-last <plugin-id>/<workflow-id>` writes `plugin.json` and `workflows/<workflow-id>.json` under the user plugin root.
- [ ] The saved workflow can be loaded via `workflow_load_result_for_ref(...)` and dry-run without manual file edits.
- [ ] Invalid AI output is reported visibly and does not overwrite the previous valid draft.
- [ ] Saving without a valid latest draft reports a no-op message and writes no files.
- [ ] Save path traversal or unsafe ids are rejected.
- [ ] Generation and save do not write workflow run rows, task/progress rows, approval rows, or artifacts.
- [ ] Policy gates and tests lock the command contract and the `workflows.py` purity boundary.

## Definition of Done

- Tests cover valid generation, invalid generation no-overwrite, save-last persistence, path/id rejection, and side-effect ledger invariants.
- Backend spec adds an executable `Workflow AI Draft Generation` scenario.
- Targeted compile/Ruff, workflow tests, policy gates, full tests, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.
- Final report compares the implementation to `docs/agent-harness-architecture.md`.
- The unrelated untracked `uv.lock` remains excluded.

## Technical Approach

- Add pure helper(s) in `workflows.py` for extracting a JSON object from model text and normalizing a draft for validation.
- Add app-owned state for the latest generated workflow draft and its source goal.
- Add app-owned command handling:
  - `/workflow generate <goal>`: start a normal main-agent task with a strict workflow JSON prompt and a workflow-generation source tag.
  - `process_ui_queue(...)`: when the tagged model task completes, parse/validate the JSON, store the latest valid draft, and show preview text.
  - `/workflow save-last <plugin-id>/<workflow-id>`: persist the latest valid draft into the user plugin root as a declarative plugin workflow.
- Reuse existing plugin registry and workflow parser after save; do not invent a separate workflow storage system.
- Keep automatic running out of scope for this slice: save first, then users can run `/workflow run <plugin-id>/<workflow-id>` through the existing governed runner.

## Decision (ADR-lite)

**Context**: AI-generated workflows could either directly execute from a model response, write a hidden workflow store, or become normal plugin workflow files.

**Decision**: Use a two-step draft/save flow. AI produces only declarative JSON. Shuheng validates and stores the latest draft in state. A separate save command writes it into a manifest-backed user plugin package, after which existing workflow commands are the only execution path.

**Consequences**: This avoids hidden executors and preserves the plugin/workflow source-of-truth model. It requires one extra save command before running, but makes generated workflows inspectable, reusable, auditable, and rollback-friendly.

## Out of Scope

- Automatically running the generated workflow in the same command.
- Editing existing workflow files in-place with merge semantics.
- Parallel/fan-out/fan-in graph generation beyond the existing sequential/dependency schema.
- Condition expression evaluation.
- Scheduled workflow generation or execution.
- Secret Vault workflow generation/save flow.
- Remote marketplace publishing.
- A2A/MCP workflow service exposure.

## Technical Notes

- Relevant code: `src/ga_tui/app.py`, `src/ga_tui/workflows.py`, `src/ga_tui/plugins.py`, `tests/test_workflows.py`, `scripts/check_policy_gates.py`.
- Relevant specs: `.trellis/spec/backend/agent-control-protocol.md`.
- Prior completed commits: `f191443 feat: add workflow agent task bridge`, `cb19d63 feat: auto-continue workflow agent tasks`.
- Existing command routing lives in `handle_workflow_command(...)`.
- Existing workflow loader requires plugin manifest workflow metadata, so save must update `plugin.json`, not only write a JSON file.
