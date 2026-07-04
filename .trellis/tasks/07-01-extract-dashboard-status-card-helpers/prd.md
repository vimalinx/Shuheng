# Extract dashboard status card helpers

## Goal

Continue the `dashboard.py` decomposition by moving pure status-card text layout helpers out of `src/shuheng/app.py`, while keeping curses attributes, `RenderLine` construction, home section assembly, runtime state reads, ledger reads, and action panels in `app.py`.

## Requirements

- Extend `src/shuheng/dashboard.py`.
- Move only pure status-card helper functions:
  - `status_card_header_line(title, card_width)`
  - `status_card_divider_line(title, card_width)`
  - `status_card_content_line(text, card_width)`
  - `status_card_footer_line(card_width)`
  - `status_card_metric_rows(items, inner_width)`
  - `status_card_metric_header(metrics)`
  - `status_card_detail_rows(items, inner_width)`
- Keep `src/shuheng/app.py` compatibility aliases for moved names.
- Preserve current box-drawing output, cell-width-aware truncation/padding, metric layout column behavior, empty metric/detail fallbacks, and detail-row wrapping.
- Add unit tests and policy gates for the expanded `dashboard.py` boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the status-card helper boundary.

## Acceptance Criteria

- [ ] `shuheng.dashboard` owns the moved status-card helper functions.
- [ ] `shuheng.app` exposes the moved status-card helpers as direct aliases or behavior-identical wrappers.
- [ ] `dashboard.py` still does not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, `PanelItem`, gateway handlers, runtime dispatch, draw functions, home-line appenders, ledgers, schedulers, or approval/action dispatch.
- [ ] `append_status_card(...)` and `append_home_action_panel(...)` remain in `app.py` because they create `RenderLine` values and use curses attrs.
- [ ] Tests prove header/divider/footer/content line construction, metric column fallback/layout, metric header counts, detail wrapping, empty metric/detail fallbacks, and app alias parity.
- [ ] Existing dashboard helper tests continue to pass.
- [ ] Phase exit verification passes.

## Definition of Done

- New helpers, app aliases, unit tests, policy gate, and spec boundary updates are implemented.
- No behavior change to dashboard/home rendering.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Use the same aliasing pattern as the previous dashboard helper extraction. Move only functions that accept plain strings/tuples/widths and return strings/lists of strings. Do not move functions that allocate `RenderLine`, call `cp(...)`, use curses attributes, read `State`, inspect subagents, query ledgers, or build home sections.

## Decision (ADR-lite)

Context: Dashboard home rendering has pure card-string layout mixed with stateful rendering functions.

Decision: Extract status-card string layout helpers into `dashboard.py` now. Leave `append_status_card(...)` and `append_home_action_panel(...)` in `app.py` until rendering types and curses attributes are separated.

Consequences: `dashboard.py` gains another pure lower-level boundary useful for future home rendering extraction without weakening Orchestrator/runtime ownership.

## Out of Scope

- Moving `append_home_line`, `append_home_section`, `append_status_card`, `append_home_action_panel`, `main_home_section_body`, `main_home_lines_uncached`, `scheduled_reports_home_lines_uncached`, `subagent_home_section_body`, `subagent_home_lines_uncached`, or cache-key functions.
- Moving `RenderLine`, `State`, `SubAgentRuntime`, curses drawing, command handlers, Web Console handlers, ledgers, approvals, artifacts, scheduler runtime, or history/session storage.
- Changing visible dashboard copy, status-card styling, section ordering, scheduler/task/approval/artifact ownership, history/session behavior, or storage roots.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, Phase 6 and Phase 7.
- Relevant existing spec scenario: `.trellis/spec/backend/agent-control-protocol.md`, `Dashboard Helper Module Boundary`.
- Existing helper cluster starts at `status_card_header_line(...)` in `src/shuheng/app.py`.
