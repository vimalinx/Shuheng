# Add Workflow Panel Run Input Prompt V1

## Goal

Let users run manifest-backed workflow definitions with required inputs directly
from the `/workflows` panel, without dropping to a manually typed command.

## Requirements

- Pressing Enter/c on a workflow definition row with missing required inputs
  must open a small panel-local input prompt instead of immediately producing a
  missing-input rejection.
- The prompt must accept the same `key=value` syntax used by `/workflow run`.
- The submitted inputs must be parsed through the existing
  `parse_workflow_run_command_args(...)` grammar.
- The actual run must still load the workflow through the manifest-backed
  registry and call `create_workflow_run_v0(...)`.
- Safe workflows with no required missing inputs may keep running immediately
  without the prompt.
- Cancelling the prompt must append no workflow row and leave side-effect
  ledgers unchanged.
- Invalid prompt syntax must stay in the panel and show a visible error.

## Acceptance Criteria

- [x] Required workflow inputs are summarized in the definition row detail.
- [x] `workflow_panel_run_action(..., inputs=...)` can run a definition row with
  parsed inputs through the existing runner.
- [x] The `/workflows` panel opens an input prompt for definitions with missing
  required inputs.
- [x] The prompt uses existing workflow input parsing and reports parse errors.
- [x] Cancelled prompts append no workflow/task/progress/approval/artifact rows.
- [x] Tests and policy gates cover successful prompted input runs and the no-op
  cancel/parse-error paths.
- [x] Backend spec records the panel input prompt contract.

## Out Of Scope

- Multi-field form widgets.
- Input validation beyond the existing workflow input resolver.
- Optional input editing for workflows whose required inputs are already
  satisfied by defaults.
- Graph editor UI.
- New workflow executor.
- Plugin mutation.
