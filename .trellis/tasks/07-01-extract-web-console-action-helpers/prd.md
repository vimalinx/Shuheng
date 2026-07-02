# Extract Web Console action helpers

## Goal

Move pure Web Console action helper logic out of `src/ga_tui/app.py` into `ga_tui.web_console` without moving the governed `/gui/action` mutation dispatcher, runtime pump, snapshot refresh, HTTP handler, or any ledger/model/subagent mutation path.

## Requirements

- Move these pure helpers to `src/ga_tui/web_console.py`:
  - `web_console_resolve_ref(refs, ui_ref, expected_kind)`
  - `web_console_action_payload(payload)`
  - `web_console_action_message(text)`
  - `web_console_model_name_from_payload(action_data, refs)`
  - `web_console_schedule_control_from_payload(action_data, refs)`
- Keep `src/ga_tui/app.py` compatibility aliases for the moved names.
- Preserve the current server-side sanitized `ui_ref` resolution behavior and Chinese user-facing errors.
- Preserve schedule target-agent ref resolution into `execution.routing.selected_agent` and `target_selector.agent_id`.
- Expand unit tests and policy gates so the new module boundary remains pure and app-compatible.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the expanded helper boundary.

## Acceptance Criteria

- [ ] `ga_tui.web_console` still imports without `ga_tui.app`, curses, mutable TUI state, runtime classes, rendering types, gateway handlers, or mutation helpers.
- [ ] `app.web_console_resolve_ref`, `app.web_console_action_payload`, `app.web_console_action_message`, `app.web_console_model_name_from_payload`, and `app.web_console_schedule_control_from_payload` are direct aliases or behavior-identical wrappers.
- [ ] Tests cover successful ref resolution, missing refs, unknown refs, kind mismatch, and model-name extraction from either payload value or model `ui_ref`.
- [ ] Tests cover schedule target-agent ref mapping into the existing scheduler control shape.
- [ ] `web_console_apply_action(...)` remains in `app.py` and keeps calling existing governed functions for approvals, schedules, models, tasks, and subagents.
- [ ] Phase exit verification passes.

## Definition of Done

- Tests added or updated for moved action helpers and compatibility surface.
- Policy gate validates the expanded helper boundary.
- Backend spec records the helper boundary and out-of-scope mutation dispatcher.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Use the existing `ga_tui.web_console` helper module. Add pure functions that operate only on explicit payload/ref dictionaries and do not read or mutate runtime state. Replace local app implementations with compatibility aliases. Keep `web_console_action_error`, `web_console_action_response`, `web_console_apply_action`, `web_console_snapshot`, and runtime pump functions in `app.py`.

## Decision (ADR-lite)

Context: `web_console_apply_action(...)` contains a mix of pure payload/ref shaping and governed mutation dispatch. Moving the whole function would create a second app facade or force callback injection too early.

Decision: Move only pure payload/ref/action helper logic now. Leave mutation dispatch and snapshot response generation in `app.py`.

Consequences: The module boundary becomes more useful for future `/gui/action` extraction, while all side effects still flow through the existing orchestrator-owned app paths.

## Out of Scope

- Moving `web_console_apply_action(...)`.
- Moving `web_console_action_response(...)` or snapshot refresh logic.
- Moving runtime pump helpers.
- Moving `GatewayRequestHandler`.
- Changing browser action schemas, supported action names, ref format, schedule execution schema, or model/subagent/task/approval behavior.
- Changing history ownership, storage roots, Secret Vault behavior, or standalone GUI files.

## Technical Notes

- Prior helper extraction commit: `59f9587 refactor: extract web console helpers`.
- Relevant current functions are still in the Web Console block of `src/ga_tui/app.py`.
- This is a bridge slice before a later task can split stateful Web Console adapters through explicit callbacks or state facades.
