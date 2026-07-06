# Extract Rendering Process Child Detail Helper

## Goal

Move deterministic process-child detail text shaping out of `src/shuheng/app.py`
and into the curses-free `src/shuheng/rendering.py` helper boundary.

## Scope

- Add a pure helper in `src/shuheng/rendering.py` that formats an already-cleaned
  process detail body plus an already-computed preview into the indented child
  detail block used for expanded process groups.
- Preserve the current truncation limit and truncation suffix.
- Preserve the fallback behavior: when the cleaned detail is empty, use the
  preview text.
- Keep `src/shuheng/app.py` as the compatibility facade with the public
  `process_child_detail(body, limit=12000)` function.
- In the app wrapper, keep app-owned control stripping by applying
  `strip_tui_controls(...)` before delegating.

## Out Of Scope

- Do not move `strip_tui_controls(...)` into `rendering.py`.
- Do not move `process_tools(...)`, JSON-ish payload parsing, interaction
  extraction, ask-user handling, IRC snippets, search-noise detection, or
  `preferred_group_visible_reply(...)`.
- Do not move `append_process_turn(...)`, `render_assistant_text(...)`,
  `message_block_lines(...)`, `message_lines_from_cache(...)`, markdown/plain
  block rendering, curses drawing, mutable `State`, Web Console, dashboard,
  runtime dispatch, storage roots, approvals, artifacts, history ownership, or
  task ledgers.

## Compatibility

- Existing imports from `shuheng.app.process_child_detail` must keep working.
- Existing behavior for visible text, empty fallback, truncation, and indentation
  must remain unchanged.
- `rendering.py` must remain a lower-level dependency and must not import
  `shuheng.app`, curses, mutable TUI state, runtime dispatch, Web Console,
  dashboard, command handlers, or input handlers.

## Verification

- Add or expand `tests/test_rendering.py` coverage for direct helper behavior,
  fallback preview, truncation, indentation, and app wrapper parity.
- Expand `scripts/check_policy_gates.py` so the rendering boundary owns the new
  helper and `app.py` no longer has the local pure implementation.
- Run targeted compile, Ruff, rendering tests, policy gates, full test suite,
  release hygiene, runtime smoke, package build, wheel smoke, `git diff --check`,
  and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline Impact

This should move the system closer to `docs/agent-harness-architecture.md` by
placing another deterministic rendering transform in a restricted lower-level
module while keeping the strong Orchestrator facade responsible for mutation,
runtime side effects, ledgers, approvals, artifacts, history, and external
memory boundaries.
