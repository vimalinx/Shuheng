# Add Workflow Save-And-Run Generated Draft Command

## Goal

Make AI-generated workflows easier to use by adding one explicit command that saves the latest valid workflow draft as a normal manifest-backed plugin workflow and then immediately runs it through the existing governed workflow runner.

## What I Already Know

- The previous slice added `/workflow generate <goal>` and `/workflow save-last <plugin-id>/<workflow-id>`.
- Generated drafts are validated through `workflows.py` and cached in `State.workflow_draft_payload`.
- Saving already writes `plugin.json` and `workflows/<workflow-id>.json` under `SHUHENG_PLUGINS_DIR`, then refreshes the plugin registry.
- Running already goes through `create_workflow_run_v0(...)`, which appends planned/advanced workflow rows and delegates approval/subagent side effects to app-owned bridges.
- The user wants AI to do more of the workflow work automatically, but the architecture baseline requires a strong Orchestrator, ledgers, approval gates, and no hidden executors.
- `workflows.py` must remain pure; app-owned command routing is the right place for save/run orchestration.

## Requirements

- Add a public command `/workflow run-last <plugin-id>/<workflow-id>`.
- The command must require an explicit target ref; it must not infer unsafe paths or plugin ids from model output.
- The command must require a latest valid draft in `State.workflow_draft_payload`.
- The command must persist the draft using the same manifest-backed save path as `/workflow save-last`.
- After save succeeds, the command must load the saved workflow through `workflow_load_result_for_ref(...)`.
- After load succeeds, the command must invoke the existing governed runner path, not duplicate runner logic.
- The command output must include both the save result and the run result so the user can see what happened.
- Save failure must prevent running.
- Invalid refs or no draft must be no-op and write no files or ledgers.
- Generation completion must remain non-executing; only the explicit `/workflow run-last ...` command may save and run a draft in one step.
- Secret Vault unlocked mode must continue blocking `/workflow` commands.

## Acceptance Criteria

- [ ] `/workflow run-last generated-pack/generated-flow` saves the latest valid draft and appends normal workflow run rows through the existing runner.
- [ ] A safe-only generated workflow ends with planned + completed runner rows.
- [ ] A generated workflow containing `agent_task` still dispatches only through the existing Workflow Agent Task Bridge.
- [ ] A generated workflow containing `approval` still creates approval rows only through the existing Workflow Approval Bridge.
- [ ] No-draft and unsafe-ref cases produce visible no-op messages and do not write files or ledgers.
- [ ] `/workflow generate` completion still stores only a draft and does not run.
- [ ] Policy gates lock the command name, save-before-run order, and no new executor boundary.

## Definition of Done

- Tests cover safe-only run-last, no-draft/unsafe-ref no-op, and save failure prevents run.
- Policy gate covers the new command and proves it uses normal workflow run rows.
- Backend spec adds a `Workflow Generated Draft Save-And-Run` executable scenario with seven sections.
- Targeted compile/Ruff, workflow tests, policy gates, full tests, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.
- Final report compares the implementation to `docs/agent-harness-architecture.md`.
- The unrelated untracked `uv.lock` remains excluded.

## Technical Approach

- Add an app helper that saves the latest workflow draft and returns both a workflow ref and message.
- Refactor `save_latest_workflow_draft(...)` just enough to avoid parsing a status string when run-last needs the saved ref.
- Add `run_latest_workflow_draft(state, ref)` that:
  - validates the target ref,
  - saves the latest draft,
  - loads the saved workflow through the plugin registry,
  - calls `create_workflow_run_v0(result, state=state)`,
  - returns a combined user-visible message.
- Add command routing before `/workflow run <ref>` so `/workflow run-last ...` is not parsed as `run`.
- Keep `workflows.py` unchanged unless a pure helper is genuinely needed.

## Decision (ADR-lite)

**Context**: The user wants AI-generated workflows to become runnable with less manual ceremony, but generating and immediately executing model output in the completion callback would weaken auditability.

**Decision**: Add an explicit `/workflow run-last <plugin-id>/<workflow-id>` command. It saves the latest valid draft into the normal plugin registry first, then invokes the existing runner.

**Consequences**: Users get a one-command path after generation, while generated workflow execution remains auditable, manifest-backed, and governed by existing run/approval/subagent bridges. The command still requires explicit user intent after draft generation.

## Out of Scope

- Auto-running directly at `/workflow generate` completion.
- A combined asynchronous `/workflow generate-run ...` command.
- Running unsaved in-memory drafts.
- Editing or merging existing workflow files beyond replacing the target workflow id entry.
- Parallel/fan-out/fan-in workflow execution.
- Condition expression evaluation.
- Scheduling generated workflows.
- Secret Vault workflow generation/run-last support.
- A2A/MCP workflow service exposure.

## Technical Notes

- Relevant app code:
  - `save_latest_workflow_draft(...)`
  - `create_workflow_run_v0(...)`
  - `handle_workflow_command(...)`
- Relevant tests:
  - `tests/test_workflows.py`
  - `scripts/check_policy_gates.py`
- Relevant spec:
  - `.trellis/spec/backend/agent-control-protocol.md`
- Architecture baseline:
  - `docs/agent-harness-architecture.md`
