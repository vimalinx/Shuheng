# Add Built-In Example Workflow Pack V1

## Goal

Make a fresh Shuheng install useful immediately by showing at least one
manifest-backed workflow in `/workflows`, `/workflow info`, `/workflow dry-run`,
and `/workflow run` without requiring users to hand-create a plugin package.

## Requirements

- Add a read-only built-in plugin root distributed with the Python package.
- The built-in root must contain a normal `shuheng.plugin.v1` manifest and a
  normal `shuheng.workflow.v1` workflow file.
- The built-in workflow must be safe-only so users can run it without creating
  subagents, approvals, task/progress rows, artifacts, tools, shell, or plugin
  code execution.
- User plugins under `SHUHENG_PLUGINS_DIR` must continue to work unchanged.
- Saving generated workflows must still write only to the user plugin root, not
  the built-in package root.
- Plugin discovery must continue to load workflows only through manifests and
  must not guess workflow paths from refs.
- Package builds and wheel installs must include the built-in plugin data.

## Acceptance Criteria

- [x] Empty user plugin roots still surface the built-in example workflow.
- [x] `/workflow info shuheng-examples/daily-briefing` loads successfully.
- [x] `/workflow dry-run shuheng-examples/daily-briefing` shows the ordered
  plan and `No execution occurred.`
- [x] `/workflow run shuheng-examples/daily-briefing` appends normal planned
  and completed workflow rows and no side-effect ledgers.
- [x] User plugin discovery still supports existing custom workflow packages.
- [x] Wheel smoke or package-data test proves the built-in workflow files are
  included in the built distribution.
- [x] Policy gates lock the built-in root and no-user-directory mutation
  behavior.

## Out Of Scope

- New workflow executor or daemon.
- Graph editor UI.
- Parallel/fan-out/fan-in execution.
- Writing starter files into `~/.shuheng/plugins`.
- Built-in agent templates or executable plugin code.
- Network, tool, shell, or model calls from the example workflow.
