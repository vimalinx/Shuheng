# Extract Rendering Markdown Fence Helper

## Goal

Continue Goal 7 app.py decomposition by moving the pure markdown fence balancing helper into `src/ga_tui/rendering.py`, while preserving existing rendering behavior and app-level compatibility.

## Requirements

- Move `close_unbalanced_markdown_fence(text)` from `src/ga_tui/app.py` into `src/ga_tui/rendering.py`.
- Keep `src/ga_tui/app.py` exposing `close_unbalanced_markdown_fence` as a compatibility alias.
- Preserve current semantics:
  - Return the original text when markdown code fences are balanced.
  - Append the opening fence tick sequence when a fence remains open.
  - Treat a closing fence as valid only when it has at least the opening tick length and no suffix.
  - Handle empty or `None`-like input the same way as the existing implementation.
- Add tests in `tests/test_rendering.py` for direct helper behavior and app alias parity.
- Extend `scripts/check_policy_gates.py` so the rendering helper ownership and behavior stay policy-gated.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document that markdown fence balancing is part of the curses-free rendering helper boundary.

## Acceptance Criteria

- `src/ga_tui/rendering.py` owns the implementation.
- `src/ga_tui/app.py` has no local implementation body for `close_unbalanced_markdown_fence`.
- `append_process_turn(...)`, full assistant rendering, latest-visible-reply extraction, process tool parsing, process grouping/folding, message block rendering, mutable `State`, curses drawing, Web Console, dashboard, runtime dispatch, storage roots, and ledgers remain outside `rendering.py`.
- Rendering tests cover balanced, unbalanced, longer closing fence, suffix-bearing closing fence, empty input, and app alias parity.
- Policy gates verify no reverse dependency from `rendering.py` to app/UI/runtime owners and verify the markdown fence helper behavior.

## Definition of Done

- Targeted compile, Ruff, rendering tests, policy gates, full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel smoke, and `shuheng-check` pass.
- `docs/agent-harness-architecture.md` comparison is recorded before claiming completion.
- The work is committed as one coherent refactor commit, excluding unrelated untracked Trellis directories, `goal-7/*`, and `uv.lock`.

## Technical Approach

The helper is a deterministic string transform and already uses only `re`. Move it to `rendering.py`, keep a direct alias in `app.py`, and lock both direct behavior and compatibility through tests and policy gates.

## Out of Scope

- Do not move `visible_reply_text(...)`, `latest_visible_reply_text(...)`, `render_assistant_text(...)`, `process_tools(...)`, JSON-ish tool parsing, interaction parsing, process grouping/folding, markdown/plain block rendering, curses drawing, command/input handling, storage roots, task ledgers, or runtime dispatch.
- Do not change user-visible assistant rendering behavior.
- Do not change history ownership or subagent session storage.

## Technical Notes

- Current app line count before this slice: 26,226.
- Previous rendering slices already moved running indicator, selection geometry, message cache keys, process summary cleanup, and turn marker splitting into `src/ga_tui/rendering.py`.
- The architecture baseline is `docs/agent-harness-architecture.md`: app remains the strong Orchestrator/composition facade for mutable UI state, side effects, ledgers, approvals, artifacts, history, and external memory.
