# Extract Rendering Message Cache Helpers

## Problem

`src/shuheng/app.py` still owns small pure rendering helper logic that computes
message-render cache signatures and scoped subagent metadata keys. These helpers
belong with the curses-free rendering transforms in `src/shuheng/rendering.py`,
not in the app Orchestrator facade.

## Scope

- Move `scoped_subagent_meta_keys(process_scope, expanded_subagent_meta)` into
  `src/shuheng/rendering.py`.
- Move `message_render_cache_key(...)` into `src/shuheng/rendering.py`.
- Keep `src/shuheng/app.py` compatibility names so existing tests/imports and
  call sites continue to work.
- Keep mutable message block cache ownership in `app.py`.
- Add tests for direct rendering helper behavior and app compatibility parity.
- Expand the rendering policy gate so the new helpers are locked behind the
  no-reverse-dependency boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the rendering
  boundary description needs to mention the cache-key ownership.

## Non-Goals

- Do not move `message_lines_from_cache(...)`; it mutates `State`.
- Do not move `message_block_lines(...)`; it still depends on curses attrs,
  `cp(...)`, `RenderLine`, subagent-result cards, and process folding.
- Do not move `markdown_blocks(...)`, `plain_blocks(...)`, sidebar/rightbar
  drawing, `draw_main(...)`, `draw_text_with_selection(...)`, or process
  folding in this slice.
- Do not change message rendering behavior, cache invalidation semantics,
  subagent transcript ownership, storage roots, command handlers, runtime
  dispatch, Web Console behavior, dashboard behavior, or task ledgers.
- Do not include old untracked Trellis task directories or `uv.lock` in the work
  commit.

## Acceptance Criteria

- `src/shuheng/rendering.py` owns the two pure helper implementations.
- `src/shuheng/app.py` retains compatibility aliases or wrappers with unchanged
  public behavior.
- `message_render_cache_key(...)` continues to include the same cache-stable
  fields and intentionally does not include `run_frame`.
- `scoped_subagent_meta_keys(...)` preserves unscoped passthrough and scoped
  prefix filtering behavior.
- The rendering module remains lower-level: it must not import `shuheng.app`,
  curses, mutable `State`, `SubAgentRuntime`, Web Console, dashboard,
  runtime dispatch, input controller, command handlers, or drawing functions.
- Targeted tests, policy gates, full tests, release hygiene, build/wheel smoke,
  and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.

## Verification Plan

- `python3 -m py_compile src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full project Ruff, release hygiene, runtime smoke, compileall, `git diff --check`,
  full pytest, build, wheel smoke, and `shuheng-check`.
