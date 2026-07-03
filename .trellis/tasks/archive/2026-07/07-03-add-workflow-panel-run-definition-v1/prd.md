# Add Workflow Panel Definition Run Action V1

## Goal

Make `/workflows` usable as a control surface, not only a registry viewer, by
letting users run a workflow definition directly from the panel.

## Requirements

- Selecting a workflow definition row in the Workflows panel and pressing
  Enter/c must start a workflow run through the existing app-owned runner.
- Workflow run rows must keep the existing Enter/c continue behavior.
- Workflow run rows must keep the existing x cancel behavior.
- Definition-row execution must call `create_workflow_run_v0(...)` after loading
  the workflow through the manifest-backed plugin registry.
- Definition-row execution must not duplicate runner logic, build workflow rows
  directly, bypass manifest refs, or mutate plugin files.
- Safe workflows with defaults may complete immediately; workflows needing
  inputs or approval/task bridges must use existing runner behavior and errors.
- The panel footer/help must communicate that definition rows can be run.

## Acceptance Criteria

- [x] `workflow_panel_run_action(..., action="continue")` on a workflow
  definition row creates normal planned/completed rows for a safe workflow.
- [x] The action message identifies that the run was started from the workflow
  panel and includes the existing runner result text.
- [x] The action writes no task/progress/approval/artifact ledgers for a safe
  workflow.
- [x] Existing run-row continue and cancel behavior remains compatible.
- [x] Policy gates assert the panel route can run a definition through
  `create_workflow_run_v0(...)` and does not write side-effect ledgers for safe
  workflows.
- [x] Backend spec records the panel definition run contract.

## Out Of Scope

- Input form UI.
- Graph editor UI.
- New workflow executor.
- Plugin mutation.
- Keyboard remapping beyond reusing Enter/c for definition rows.
