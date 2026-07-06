# Extract Web Console helpers

## Goal

Move the first low-risk Web Console helper slice out of `src/shuheng/app.py` into a lower-level `shuheng.web_console` module, reducing the monolith while preserving all current Web Console behavior, browser contracts, compatibility imports, policy gates, and release checks.

## Requirements

- Create `src/shuheng/web_console.py` as the owner for pure Web Console constants and helper functions:
  - `WEB_CONSOLE_ACTION_REQUEST_SCHEMA`
  - `WEB_CONSOLE_ACTION_RESPONSE_SCHEMA`
  - `WEB_CONSOLE_REF_KINDS`
  - `web_console_ref(...)`
  - `web_console_timestamp(...)`
  - `web_console_clean_visible(...)`
  - `web_console_status_label(...)`
  - `web_console_metric(...)`
- Keep `src/shuheng/app.py` compatibility aliases or wrappers so existing imports and tests continue to work.
- Preserve current sanitized `ui_ref` behavior exactly enough for existing Web Console rows/actions to resolve server-side refs after a browser refresh.
- Preserve visible text sanitization for raw artifact refs, approvals, tasks, schedule ids, temporary agents, raw agent ids, and approval-required process markers.
- Add unit tests that cover helper behavior and app-wrapper parity.
- Add or extend policy gates so `web_console.py` cannot become a second monolith or reverse-import the app layer.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the new durable Web Console helper module boundary.

## Acceptance Criteria

- [ ] `shuheng.web_console` imports successfully without importing `shuheng.app`, curses, mutable TUI state, runtime classes, rendering types, draw functions, command handlers, or `GatewayRequestHandler`.
- [ ] `app.WEB_CONSOLE_ACTION_REQUEST_SCHEMA`, `app.WEB_CONSOLE_ACTION_RESPONSE_SCHEMA`, and `app.WEB_CONSOLE_REF_KINDS` are the same public values as the new module.
- [ ] `app.web_console_ref`, `app.web_console_timestamp`, `app.web_console_clean_visible`, `app.web_console_status_label`, and `app.web_console_metric` delegate to the new module or are direct aliases.
- [ ] Tests prove opaque refs are stable, reject unknown kinds/blank ids, and do not expose raw ids.
- [ ] Tests prove visible text cleaning removes or masks `artifact://...`, `appr_...`, `approval=...`, `task_...`, `schedrun_...`, `sched_...`, `agent-N`, `tmp-agent-*`, and `APPROVAL_REQUIRED`.
- [ ] Tests prove timestamp fallback order still handles ISO timestamp fields and `mtime`.
- [ ] Tests prove known status labels map to the current Chinese labels and unknown statuses are sanitized.
- [ ] Existing `/gui`, `/gui/snapshot`, `/gui/action`, runtime dispatch, and dashboard behavior remains unchanged by this helper extraction.
- [ ] Phase exit verification passes.

## Definition of Done

- Tests added or updated for the moved helpers and compatibility surface.
- `scripts/check_policy_gates.py` includes a Web Console module-boundary assertion.
- `.trellis/spec/backend/agent-control-protocol.md` records the extracted helper boundary and tests required.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Use the same proven pattern as the `context_packs.py` and `runtime_dispatch.py` extractions:

- Add a lower-level module with pure functions and explicit dependencies.
- Import helper names into `app.py` with private aliases, then expose same-named wrappers or constants for compatibility.
- Keep stateful Web Console orchestration in `app.py` for now.
- Add tests against both module functions and app wrappers so the compatibility facade cannot drift.
- Add source-inspection policy gates for forbidden imports/symbols.

## Decision (ADR-lite)

Context: Phase 6 of `docs/app-py-decomposition-plan.md` says Web Console payload shaping should move to `web_console.py`, but the existing Web Console block includes both pure sanitization/ref helpers and stateful snapshot/action/runtime dispatch code.

Decision: Extract only pure helper constants/functions first. Keep `web_console_state`, `web_console_ref_map`, `web_console_resolve_ref`, `web_console_snapshot`, `web_console_action_response`, `web_console_apply_action`, runtime pump helpers, and `GatewayRequestHandler` in `app.py` until a later task defines a callback/state boundary.

Consequences: This reduces `app.py` safely and establishes the module boundary, but does not complete the full Web Console extraction. Future slices can move row/payload builders and action adapters once dependencies can be passed explicitly.

## Out of Scope

- Moving `/gui/action` mutation routing.
- Moving `GatewayRequestHandler`.
- Moving runtime pump/background work helpers.
- Moving `web_console_state`, state construction, subagent loading, or model config mutation.
- Moving snapshot builders that still require `State`, ledgers, model config, scheduler registries, or runtime queues.
- Changing Web Console schemas, UI refs, visible copy, HTTP routes, storage roots, subagent chat ownership, or history/session semantics.
- Rewriting browser UI or standalone GUI loading.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, Phase 6.
- Relevant spec: `.trellis/spec/backend/agent-control-protocol.md`, Scenario `Local Web Console Gateway`.
- Current helper cluster begins around `src/shuheng/app.py` Web Console constants and helper functions.
- The extracted module must follow the no-reverse-import rule used by existing extracted modules.
- Phase verification should include targeted helper tests, policy gates, full pytest, release hygiene, runtime smoke, package build, wheel smoke, and `shuheng-check`.
