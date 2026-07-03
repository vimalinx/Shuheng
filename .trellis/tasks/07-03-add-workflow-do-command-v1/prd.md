# Add Workflow Do Command V1

## Goal

Let users ask Shuheng to build and run a workflow from natural language without
first choosing a plugin id or workflow id.

## Requirements

- Add a public command shaped like `/workflow do <goal> [-- key=value ...]`.
- The command must derive a safe manifest-backed workflow ref automatically.
- Generated workflows must be saved under the normal user plugin root, not the
  read-only built-in plugin root.
- The command must reuse the existing AI generation, save, registry reload, and
  governed workflow runner path.
- The command must not create an in-memory workflow executor, guess workflow
  paths, bypass manifest loading, or run model output directly.
- Existing `/workflow auto <plugin-id>/<workflow-id> <goal> [-- ...]` behavior
  must remain compatible.
- Side effects after generation must remain owned by the existing workflow
  runner/approval/task bridges.

## Acceptance Criteria

- [x] `/workflow do summarize sources` starts a workflow generation task with a
  generated ref under a default user plugin.
- [x] The generated ref is stable, filesystem-safe, and visible in the pending
  auto-run state.
- [x] After valid model output, the draft is saved as a normal manifest-backed
  user plugin workflow and then run through `create_workflow_run_v0(...)`.
- [x] The command accepts optional run inputs after `--`.
- [x] Blank goals are rejected with usage text and no model task.
- [x] Existing `/workflow auto <plugin-id>/<workflow-id> ...` tests still pass.
- [x] Policy gates assert the new command is routed through the existing
  save-and-run path and does not write to built-in plugin data.

## Out Of Scope

- New workflow executor.
- Graph editing UI.
- Workflow marketplace or remote templates.
- Provider/tool/shell/plugin-code execution outside the existing runner.
- Built-in plugin mutation.
