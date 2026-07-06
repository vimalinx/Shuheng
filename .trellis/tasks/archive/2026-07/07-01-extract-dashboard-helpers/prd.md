# Extract dashboard helper boundaries

## Goal

Start the `dashboard.py` decomposition phase by moving pure dashboard schema and normalization helpers out of `src/shuheng/app.py`, while keeping stateful `State`/`SubAgentRuntime` projections, curses rendering, and home-line construction in `app.py`.

## Requirements

- Create `src/shuheng/dashboard.py`.
- Move pure dashboard helper constants/functions:
  - `SUPPORTED_DASHBOARD_SECTIONS`
  - `DEFAULT_DASHBOARD_SECTIONS`
  - `DEFAULT_SUBAGENT_DASHBOARD_SECTIONS`
  - `bounded_dashboard_text(value, limit=2000)`
  - `normalize_dashboard_sections(raw_sections)`
  - `normalize_dashboard_spec_payload(control, source, target)`
  - `dashboard_cache_signature(raw)`
- Keep `src/shuheng/app.py` compatibility aliases for moved names.
- Preserve current `dashboard.v1` payload shape, section filtering, todo normalization, provenance fields, text bounds, and JSON signature behavior.
- Add unit tests and policy gates for the new module boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the dashboard helper boundary.

## Acceptance Criteria

- [ ] `shuheng.dashboard` imports without `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, `PanelItem`, gateway handlers, runtime dispatch, or draw functions.
- [ ] `app` exposes the moved constants/functions as direct aliases or behavior-identical wrappers.
- [ ] Tests prove section normalization accepts string/dict inputs, filters unsupported sections, bounds title/markdown text, and preserves supported markdown.
- [ ] Tests prove dashboard spec payload normalization includes schema, timestamp, source, target, provenance task/artifact refs, sections, status, todos, and markdown.
- [ ] Tests prove dashboard cache signature is deterministic for JSON-serializable dicts and falls back safely for non-JSON values.
- [ ] Stateful helpers such as `dashboard_spec_for_subagent`, `dashboard_sections_for_subagent`, `dashboard_status_for_subagent`, `main_home_lines_uncached`, and `subagent_home_lines_uncached` remain in `app.py`.
- [ ] Phase exit verification passes.

## Definition of Done

- New module, app aliases, unit tests, policy gate, and spec boundary are implemented.
- No behavior change to dashboard/home rendering or Web Console display.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Use the same extraction pattern as `web_console.py`: create a lower-level module with explicit pure inputs, alias moved names back in `app.py`, and add source-inspection gates preventing reverse imports or UI/runtime dependencies.

## Decision (ADR-lite)

Context: Dashboard functions are split between pure schema normalization and stateful home/rendering construction.

Decision: Move only pure schema/payload helpers first. Leave status projection and home-line rendering in `app.py` because they read live `State`, subagent runtime records, ledgers, and curses render types.

Consequences: Future dashboard/home extraction gets a stable lower-level base without changing current UI behavior.

## Out of Scope

- Moving `dashboard_spec_for_subagent`, `dashboard_sections_for_subagent`, `dashboard_spec_for_main`, `dashboard_sections_for_main`, `dashboard_status_for_subagent`, `dashboard_status_for_main`, `dashboard_todos_for_subagent`, or `dashboard_todos_for_main`.
- Moving `append_home_line`, `append_home_section`, status card rendering, `main_home_lines_uncached`, `subagent_home_lines_uncached`, or home cache signatures that read files/ledgers.
- Changing dashboard schemas, section names, visible copy, status text, history/session behavior, scheduler/task/approval/artifact ownership, or storage roots.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, Phase 6.
- Existing dashboard helper cluster starts around the `SUPPORTED_DASHBOARD_SECTIONS` definition in `src/shuheng/app.py`.
- `normalize_dashboard_spec_payload(...)` needs a timestamp; the new module should use a lower-level time helper and must not import `app.py`.
