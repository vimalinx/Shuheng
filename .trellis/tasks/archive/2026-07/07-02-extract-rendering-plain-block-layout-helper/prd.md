# Extract Rendering Plain Block Layout Helper

## Goal

Continue Goal 7 by moving the deterministic plain-text block layout logic out of `src/shuheng/app.py` and into the curses-free `src/shuheng/rendering.py` helper boundary, preserving existing behavior and app compatibility.

## Requirements

- Add `rendering.plain_layout_lines(text, width)` as the lower-level owner for plain text wrapping.
- Keep `app.plain_blocks(text, width)` as the legacy compatibility wrapper that converts each plain layout string into `RenderLine(line, cp(2))`.
- Re-export `plain_layout_lines` from `app.py` as a compatibility alias, matching the recent `table_layout_lines` and `markdown_layout_blocks` pattern.
- Keep `RenderLine`, `cp(...)`, curses attrs, mutable `State`, message caches, message block dispatch, Web Console, dashboard, runtime dispatch, commands, input handlers, storage roots, ledgers, approvals, artifacts, Secret Vault behavior, and history ownership outside `rendering.py`.
- Preserve the existing `plain_blocks(...)` output for empty text, wrapping, wide characters, and any `wrap_cells(...)` edge behavior.
- Update tests, policy gates, and backend spec text so this boundary remains executable and policy-enforced.

## Acceptance Criteria

- [ ] `src/shuheng/rendering.py` owns `plain_layout_lines(...)`.
- [ ] `src/shuheng/app.py` has no local pure implementation for plain layout beyond the `plain_blocks(...)` `RenderLine` wrapper.
- [ ] `app.plain_layout_lines is rendering.plain_layout_lines`.
- [ ] Unit tests cover direct helper output and wrapper attr conversion.
- [ ] `scripts/check_policy_gates.py` asserts helper ownership, representative behavior, app alias parity, and absence of a local `def plain_layout_lines` in `app.py`.
- [ ] `.trellis/spec/backend/agent-control-protocol.md` documents the plain layout boundary alongside markdown/table layout helpers.
- [ ] Targeted and full release gates pass.

## Definition Of Done

- Targeted py_compile, Ruff, rendering tests, policy gates, full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel smoke, and `shuheng-check` pass.
- The change is committed as one coherent work commit.
- `goal-7/tasks.md` records Task 150 and the associated verification.
- The result moves the implementation closer to `docs/agent-harness-architecture.md` by keeping deterministic rendering transforms in a restricted lower-level module while preserving `app.py` as the Orchestrator/compatibility facade for mutation and side effects.

## Technical Approach

Implement the smallest possible slice:

1. Add `plain_layout_lines(text, width) -> list[str]` to `rendering.py`, delegating to existing `wrap_cells(...)`.
2. Add `plain_layout_lines = rendering_helpers.plain_layout_lines` in `app.py`.
3. Reduce `plain_blocks(...)` to `[RenderLine(line, cp(2)) for line in plain_layout_lines(text, width)]`.
4. Extend rendering tests and policy gates with direct helper and wrapper parity checks.
5. Update the backend spec where `table_layout_lines(...)` and `markdown_layout_blocks(...)` are already documented.

## Decision

Context: `markdown_blocks(...)` was just split into neutral layout records in `rendering.py`; `plain_blocks(...)` is the adjacent plain-text equivalent and is currently still app-local.

Decision: Extract only the pure string layout into `rendering.py`, leaving `RenderLine` allocation and color attrs in `app.py`.

Consequences: This is a low-risk step toward splitting message rendering without prematurely moving message cache ownership, subagent result cards, or curses drawing.

## Out Of Scope

- Moving `message_block_lines(...)`, `message_lines_from_cache(...)`, subagent result metadata/card rendering, process folding, or render cache mutation.
- Moving `RenderLine` attr selection for plain blocks into `rendering.py`.
- Changing storage roots, history ownership, subagent homes, ledgers, approvals, artifacts, Web Console, dashboard, commands, input handling, or runtime dispatch.

## Technical Notes

- Relevant plan: `docs/app-py-decomposition-plan.md`.
- Architecture baseline: `docs/agent-harness-architecture.md`.
- Existing adjacent helpers: `rendering.table_layout_lines(...)`, `rendering.markdown_layout_blocks(...)`, `app.render_table(...)`, and `app.markdown_blocks(...)`.
- The invariant remains: lower-level rendering helpers must not import `shuheng.app`, curses, mutable `State`, Web Console, dashboard, runtime dispatch, command/input handlers, storage roots, ledgers, approvals, artifacts, Secret Vault behavior, or history ownership.
