# Add Workflow Registry And Dry-Run

## Goal

Introduce a governed workflow surface for Shuheng by turning plugin-declared workflow metadata into parseable, inspectable, and dry-runnable workflow definitions. This gives users a dedicated `/workflows` view and `/workflow dry-run ...` command without adding a workflow runner or executable plugin code.

## What I Already Know

- Shuheng already has a declarative plugin registry in `src/ga_tui/plugins.py`.
- `PluginWorkflow` already exists and plugin manifests can contribute `plugin://<plugin-id>/workflows/<workflow-id>` metadata.
- `/plugins` now opens a read-only harness panel using `PanelItem` and `open_harness_panel(...)`.
- The agent harness architecture baseline favors a strong Orchestrator, bounded workers, explicit ledgers, approval gates, artifact refs, and auditable protocols.
- Existing plugin contracts forbid executable plugin code, runtime permission grants, plugin-native tools, and global body-text injection.

## Research References

- [`research/workflow-design.md`](research/workflow-design.md) - Workflow design references and repo constraints.

## Requirements

- Add a pure workflow definition parser owned outside `app.py`.
- Support plugin workflow refs shaped as `plugin://<plugin-id>/workflows/<workflow-id>`.
- Load workflow definitions only from manifest-declared workflow files already validated by the plugin registry.
- Support a minimal declarative schema version, `shuheng.workflow.v1`.
- Validate workflow ids, input ids, step ids, step types, duplicate ids, and malformed files.
- Add `/workflows` as an interactive harness panel command.
- Add non-interactive command handling for `/workflows`, `/workflow info <ref>`, and `/workflow dry-run <ref>`.
- Dry-run must render a bounded execution plan and validation findings without dispatching agents, creating approvals, writing ledgers, or executing tools.
- Keep Secret Vault isolation consistent: `/workflows` and `/workflow` are normal harness commands while the vault is unlocked.
- Update backend spec and policy gates so workflow remains declarative-only.

## Acceptance Criteria

- [ ] `plugins.py` can resolve and parse workflow refs without direct filesystem guessing.
- [ ] Valid workflow definitions show inputs, permissions metadata, and ordered steps.
- [ ] Invalid or missing workflow definitions produce visible validation issues, not crashes.
- [ ] `/workflows` opens a read-only panel in the curses Enter path.
- [ ] `/workflow info <ref>` reports workflow metadata and validation issues.
- [ ] `/workflow dry-run <ref>` reports the planned steps and explicitly says no execution occurred.
- [ ] Policy gates prove dry-run does not dispatch subagents, approvals, tools, ledgers, or artifacts.
- [ ] Existing plugin tests and policy gates remain green.

## Technical Approach

- Add workflow dataclasses and parsing helpers in a pure module, likely `src/ga_tui/workflows.py`.
- Reuse plugin registry records as the source of truth for workflow file paths.
- Accept JSON workflow definitions for MVP, with a small Markdown fallback only if cheap and low risk.
- Add app-level wrappers for workflow registry/panel/commands while keeping orchestration and UI ownership in `app.py`.
- Add tests for pure parsing and command/policy behavior.
- Extend `.trellis/spec/backend/agent-control-protocol.md` with an executable workflow registry/dry-run contract.

## Decision (ADR-lite)

**Context**: Workflow is the next layer above plugins, but adding execution too early would create new side effects and governance bypass risk.

**Decision**: Implement declarative registry, panel, info, and dry-run first. Defer the runner and run ledger.

**Consequences**: Users can inspect and validate workflows now, while the execution model can be designed against a stable schema later. This intentionally does not automate work yet.

## Out Of Scope

- Running workflow steps.
- Creating workflow run records.
- Dispatching subagents from workflow steps.
- Creating approval requests from workflow steps.
- Executing tools, shell, Python, JavaScript, or plugin-native code.
- Parallel branches, conditionals, loops, retries, resume, or scheduling.
- Remote marketplace install or sync.

## Technical Notes

- Relevant files: `src/ga_tui/plugins.py`, `src/ga_tui/app.py`, `tests/test_plugins.py`, `scripts/check_policy_gates.py`, `.trellis/spec/backend/agent-control-protocol.md`.
- Existing panel pattern: `PanelItem`, `draw_panel_browser(...)`, `open_harness_panel(...)`.
- Existing command pattern: `COMMANDS`, `submit(...)`, specialized `handle_*_command(...)` helpers.
- Existing policy gate pattern: `assert_declarative_plugins_are_agent_scoped()`.
