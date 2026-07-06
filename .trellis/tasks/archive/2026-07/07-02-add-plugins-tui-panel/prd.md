# Add Plugins TUI Panel

## Goal

Make `/plugins` open a dedicated plugin browser inside the TUI, so users can inspect installed declarative plugins, contributed skills/templates/workflows, validation issues, and local plugin roots without reading a plain chat message.

## What I Already Know

- The declarative plugin MVP already exists in `src/shuheng/plugins.py`.
- Current `/plugins` is handled by `handle_plugin_command(...)` and returns `format_plugin_list(...)` as a system message.
- Existing harness panels use `PanelItem` plus `open_harness_panel(...)` for `/tasks`, `/approvals`, `/artifacts`, `/recover`, `/evals`, `/gateway`, and `/baseline`.
- Curses Enter handling opens harness panels before falling back to `submit(...)`.
- The plugin system must remain declarative-only and must not add plugin execution, plugin tools, or permission grants.

## Assumptions

- `/plugins` should open the modal panel only in the interactive curses path.
- Non-curses command handling may keep returning the text summary, preserving tests and simple command behavior.
- The panel should be read-only in this slice; plugin add/remove/create actions remain command-based.

## Requirements

- Add a plugin panel reachable by typing `/plugins` in the TUI.
- Reuse the existing harness panel browser rather than introducing a new UI framework.
- Show one row per valid plugin with bounded details for root, manifest, skills, agent templates, workflows, permissions, and validation issues.
- Show validation issue rows for invalid manifests or plugin-level warnings.
- Show a helpful empty-state row when no plugins are found.
- Keep `/plugin info`, `/plugin template`, `/plugin create`, and `/agent plugin ...` behavior unchanged.
- Preserve Secret Vault isolation by treating `/plugins` as a normal harness panel command when the vault is unlocked.

## Acceptance Criteria

- [x] `/plugins` is included in the TUI Enter path that calls `open_harness_panel(...)`.
- [x] `open_harness_panel(..., "plugins")` renders plugin `PanelItem` rows.
- [x] `plugin_panel_items(...)` exposes plugin metadata without plugin skill body text.
- [x] Invalid plugin manifests and validation issues are visible as panel rows.
- [x] Empty plugin root shows a useful no-plugin row instead of a blank popup.
- [x] Policy gates cover the `/plugins` panel route and plugin panel item content.
- [x] Existing declarative plugin tests and policy gates remain green.

## Implementation Notes

- Added `plugin_panel_items()` in `app.py` to turn declarative plugin registry records and validation issues into read-only `PanelItem` rows.
- Wired `open_harness_panel(..., "plugins")` with title `Plugins` and refresh behavior that clears the plugin registry cache.
- Added `/plugins` to the interactive Enter path so typing `/plugins` opens the panel in curses.
- Kept non-interactive `/plugins` handling as the existing text summary through `handle_plugin_command(...)`.
- Added `/plugins` and `/plugin` to Secret Vault normal-panel isolation while unlocked.
- Updated the `Declarative User Plugins` spec with the panel contract.

## Definition Of Done

- Code implemented with existing panel/browser patterns.
- Backend spec updated for `/plugins` panel behavior.
- Targeted tests and policy gates pass.
- Full release-quality gate subset passes.
- Commit created for this slice.

## Out Of Scope

- Plugin marketplace or install UI.
- Editing plugin manifests from the TUI.
- Executing workflow prompts from the panel.
- Mouse/click actions inside the panel.
- Web Console plugin UI.

## Technical Notes

- Relevant code: `src/shuheng/app.py`, `src/shuheng/plugins.py`, `scripts/check_policy_gates.py`, `.trellis/spec/backend/agent-control-protocol.md`.
- Existing panel primitives: `PanelItem`, `draw_panel_browser(...)`, `open_harness_panel(...)`.
- Existing plugin contract: `.trellis/spec/backend/agent-control-protocol.md` Scenario `Declarative User Plugins`.
