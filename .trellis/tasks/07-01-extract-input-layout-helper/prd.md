# Extract Input Layout Helper

## Goal

Continue the `src/ga_tui/app.py` decomposition by moving the pure `input_layout(...)` prompt/input layout helper into `src/ga_tui/input_controller.py` without changing terminal input behavior. This follows the existing input cursor helper extraction and keeps `app.py` as the Orchestrator facade for mutable input state, rendering, command routing, and runtime side effects.

## Requirements

- Move `input_layout(text, width, max_lines, cursor, prompt="> ")` from `src/ga_tui/app.py` into `src/ga_tui/input_controller.py`.
- Preserve the exact public signature and return shape: `tuple[list[str], int, int]`.
- Preserve current behavior exactly:
  - Clamp `max_lines` with `max(1, max_lines)`.
  - Use `input_cursor_info(...)` so raw newlines display as escaped `\\n`.
  - When the cursor segment is below the visible window, compute `first = max(0, min(cursor_line, len(segments) - max_lines))`.
  - Prefix the first logical input line with `prompt`.
  - Prefix wrapped continuation lines with spaces equal to `cell_width(prompt)`.
  - Prefix the first visible scrolled line with `"… "`.
  - Compute cursor x from `cell_width(prefix) + cell_width(display[seg_start:display_cursor])`.
  - Return `lines or [prompt]` for empty layout fallback.
- Keep `src/ga_tui/app.py` exposing `input_layout` as a direct compatibility alias to `input_controller.input_layout`.
- Keep all mutable input state behavior in `app.py`, including `move_input_cursor_vertical(...)`, `clamp_input_cursor(...)`, `mark_dirty(...)`, key/mouse handlers, command completion, and `draw_main(...)`.
- Add or expand tests in `tests/test_input_controller.py` for app alias parity, unwrapped layout, wrapped layout, scrolled layout, hidden first-line prefix, custom prompt cursor x, escaped-newline layout, and wide/combining character cursor x.
- Expand `scripts/check_policy_gates.py` so the input-controller boundary covers `input_layout(...)`.
- Update `.trellis/spec/backend/agent-control-protocol.md` so the input-controller boundary lists `input_layout(...)` as in scope and no longer describes it as a non-goal.

## Acceptance Criteria

- [ ] `src/ga_tui/input_controller.py` owns `input_layout(...)`.
- [ ] `src/ga_tui/app.py` re-exports `input_layout` as a compatibility alias.
- [ ] `move_input_cursor_vertical(...)`, `draw_main(...)`, key/mouse handlers, command routing, mutable `State`, and runtime side effects remain outside `input_controller.py`.
- [ ] `tests/test_input_controller.py` verifies helper behavior and app alias parity.
- [ ] `scripts/check_policy_gates.py` rejects input-controller reverse dependencies on `ga_tui.app`, curses, mutable TUI state, rendering, command handlers, Web Console, dashboard, and runtime dispatch.
- [ ] Targeted compile, Ruff, input-controller tests, and policy gates pass.
- [ ] Full release gate remains green before the implementation slice is committed.
- [ ] Architecture baseline comparison is recorded before claiming the implementation slice done.

## Definition of Done

- The implementation preserves existing terminal input layout behavior.
- The lower-level module remains pure and lower-level: no `ga_tui.app`, curses, `State`, runtime, Web Console, dashboard, command, key/mouse, or rendering imports.
- The backend spec and policy gates document and enforce the new module boundary.
- The work is committed as a focused decomposition commit after verification.

## Technical Approach

Move the function body directly into `input_controller.py` and bind `input_layout = input_controller_helpers.input_layout` in `app.py`, matching the aliases already used for cursor/display helpers. This is a narrow follow-up to the previous input cursor extraction because all dependencies are already present in `input_controller.py`: `input_cursor_info(...)` and `cell_width(...)`.

## Decision (ADR-lite)

Context: `input_layout(...)` was deliberately left out of the previous cursor-helper extraction to keep that slice small. After that extraction, the function is pure and depends only on input geometry helpers plus `cell_width(...)`.

Decision: Extract `input_layout(...)` into `input_controller.py` now as a dedicated slice, while keeping all state mutation, rendering, keyboard/mouse dispatch, command routing, and runtime behavior in `app.py`.

Consequences: `app.py` loses one more pure input helper without creating a second Orchestrator. A later input-controller slice can consider stateful key/mouse behavior only after command and rendering boundaries are more stable.

## Out of Scope

- No changes to `move_input_cursor_vertical(...)`.
- No changes to `draw_main(...)` beyond continuing to call the same public `input_layout(...)` name.
- No key handler, mouse handler, bracketed paste, command completion, command dispatch, rendering, Web Console, dashboard, runtime dispatch, or storage-root changes.
- No behavior rewrite for prompt text, secret input masking, cursor clamping, scrolling policy, or terminal drawing.

## Technical Notes

- Current implementation lives in `src/ga_tui/app.py` near the input cursor aliases and before `draw_text_with_selection(...)`.
- `src/ga_tui/input_controller.py` already owns `raw_cursor_to_display(...)`, `display_cursor_to_raw(...)`, `input_segments(...)`, `display_index_for_cell(...)`, and `input_cursor_info(...)`.
- Existing spec section: `.trellis/spec/backend/agent-control-protocol.md` "Input Controller Helper Module Boundary".
- Existing tests: `tests/test_input_controller.py`.
- Existing policy gate: `assert_input_controller_module_boundary()` in `scripts/check_policy_gates.py`.
