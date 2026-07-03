# Add Workflow Auto Run Command V1

## Goal

Add an explicit one-command path for AI-assisted workflow automation: `/workflow auto <plugin-id>/<workflow-id> <goal> [-- key=value ...]`.

The command should ask the main model to generate a declarative workflow from a natural-language goal, validate the generated workflow JSON, save it as a normal manifest-backed plugin workflow, and then run it through the existing governed workflow runner. This directly addresses the user request for AI to "automatically do it" while preserving Shuheng's strong Orchestrator, plugin registry, approval, task ledger, and artifact provenance boundaries.

## Requirements

* Add `/workflow auto <plugin-id>/<workflow-id> <goal> [-- key=value ...]`.
* The first token after `auto` is the save/run target ref. The text before optional `--` is the generation goal. The tokens after `--` are workflow input overrides parsed as existing `key=value` workflow run inputs.
* The command starts a normal workflow-generation main-agent task and must not save or run anything until model output completes and validates.
* Valid generated output must be parsed through the existing pure workflow draft parser.
* Valid generated output must be saved through `save_latest_workflow_draft_result(...)`.
* The saved manifest-backed workflow must be run through `run_latest_workflow_draft(...)` / `create_workflow_run_v0(...)`; no second runner implementation.
* Invalid generated output must render the existing rejection message and must not save, run, or overwrite a previous valid draft.
* Unsafe target refs or malformed command syntax must fail before starting a model task.
* Normal `/workflow generate` remains non-executing and must not inherit stale auto-run state.
* Auto-run must keep existing side-effect ownership: safe workflows write only workflow run rows, approval workflows use the approval bridge, agent-task workflows use the governed subagent task bridge.
* Help/usage text must mention `/workflow auto`.

## Acceptance Criteria

* [ ] `/workflow auto generated-pack/safe-flow summarize sources -- ready=true` starts a workflow-generation task with a `workflow_generate` source.
* [ ] When the model returns a valid safe workflow, Shuheng saves `plugins/generated-pack/workflows/safe-flow.json` and appends normal planned + completed workflow run rows.
* [ ] When the model returns a valid approval workflow, auto-run reuses the existing approval bridge and records the source command.
* [ ] Invalid generated output saves no workflow, appends no workflow run row, and does not overwrite the previous valid draft.
* [ ] Unsafe target ref fails before model task start.
* [ ] Normal `/workflow generate` still only creates a draft and leaves auto-run state clear.
* [ ] Policy gates assert the command exists and does not bypass `save_latest_workflow_draft_result(...)` or `create_workflow_run_v0(...)`.

## Definition Of Done

* Targeted compile, Ruff, workflow tests, and policy gates pass.
* Full test suite passes.
* Release hygiene, source compileall, diff check, build, wheel smoke, runtime smoke, integration doctor, and `shuheng-check` pass.
* Task commit excludes pre-existing untracked `uv.lock`.
* Final report compares this change to `docs/agent-harness-architecture.md`.

## Technical Approach

Store a pending auto-run request on `State` while the workflow generation task is active. On generation completion, `handle_completed_workflow_generation(...)` validates the draft as it already does today. If and only if the completed generation source matches the pending auto-run request, it then calls `run_latest_workflow_draft(...)` with the saved target ref and parsed input overrides.

The command should reuse existing prompt, parse, save, run, bridge, and formatter paths. The new code should be app-layer orchestration only; `workflows.py` should not gain model, file-write, registry, or ledger ownership for auto-run.

## Decision (ADR-lite)

**Context**: Users can already run `/workflow generate`, inspect/save, and then `/workflow run-last`, but that still requires multiple manual commands. The requested product behavior is that AI can automatically create and execute a workflow from a goal.

**Decision**: Add an explicit auto command that combines generation and save-and-run after validation. Keep `/workflow generate` conservative and non-executing.

**Consequences**: The user gets a one-command automation path, while dangerous ambiguity remains contained by explicit command intent, manifest-backed persistence, existing workflow validation, approval gates, and governed subagent task dispatch.

## Out Of Scope

* Auto-running ordinary `/workflow generate`.
* Running in-memory drafts without saving to plugin manifests.
* Retrying generation on invalid model output.
* Auto-selecting plugin/workflow ids.
* Auto timeout, retry, checkpoint/replay, workflow cancellation, or task abort.
* Parallel fan-out/fan-in executor changes.
* New workflow-owned model/tool/plugin-code execution.
* A2A/MCP workflow service exposure.

## Technical Notes

* Relevant spec: `.trellis/spec/backend/agent-control-protocol.md`.
* Relevant architecture baseline: `docs/agent-harness-architecture.md`.
* Relevant code: `src/ga_tui/ui_types.py`, `src/ga_tui/app.py`, `tests/test_workflows.py`, `scripts/check_policy_gates.py`.
* Existing helpers to reuse: `workflow_generation_prompt(...)`, `start_workflow_generation(...)`, `handle_completed_workflow_generation(...)`, `parse_workflow_run_command_args(...)`, `save_latest_workflow_draft_result(...)`, `run_latest_workflow_draft(...)`, `create_workflow_run_v0(...)`.
