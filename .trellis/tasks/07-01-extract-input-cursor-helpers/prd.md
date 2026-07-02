# Extract Input Cursor Helpers

## Objective

Continue decomposing `src/ga_tui/app.py` by moving pure input cursor/display conversion helpers into a new lower-level `src/ga_tui/input_controller.py` module, while preserving existing TUI behavior and `app.py` compatibility names.

## Scope

- Create `src/ga_tui/input_controller.py` for pure text-input helper functions.
- Move these implementations out of `app.py`:
  - `raw_cursor_to_display(text, cursor)`
  - `display_cursor_to_raw(text, display_cursor)`
  - `input_segments(text, width)`
  - `display_index_for_cell(display, start, end, target_x)`
  - `input_cursor_info(text, width, cursor)`
- Keep `app.py` compatibility aliases/wrappers so existing call sites and imports keep working.
- Preserve current behavior:
  - raw newlines display as the two-character sequence `\n`.
  - raw cursor positions clamp into the valid source-text range.
  - display cursor positions clamp to non-negative values and map back to raw positions.
  - segment wrapping is based on cell width with East Asian full-width handling and combining marks.
  - cursor info returns display text, display segments, display cursor, cursor line, and cursor x using existing cell-width semantics.
- Add direct unit tests for the new module and app wrapper parity.
- Add a policy gate for the new input-controller boundary.
- Update backend spec with the input cursor helper boundary.

## Non-Goals

- Do not move `move_input_cursor_vertical(...)`, `input_layout(...)`, `draw_main(...)`, key handlers, mouse handlers, command completion, rendering, or any state mutation in this slice.
- Do not import curses, `State`, `RenderLine`, command handlers, runtime dispatch, Web Console, or dashboard code into `input_controller.py`.
- Do not change input behavior, cursor math, keyboard shortcuts, selection behavior, or prompt layout.
- Do not change storage roots, history, subagent state, Secret Vault behavior, task ledgers, or runtime dispatch.

## Acceptance Criteria

- `input_controller.py` owns the pure input cursor/display helper implementations and stays lower-level than the TUI.
- `app.py` exposes the same public helper names for compatibility.
- Tests cover newline display mapping, raw/display cursor round-trip behavior, segment wrapping, East Asian width/combining-mark behavior, display-index lookup, cursor info, and app wrapper parity.
- `scripts/check_policy_gates.py` asserts the new module has no reverse dependency on `ga_tui.app`, curses, mutable TUI state, rendering, command handlers, Web Console, dashboard, or runtime dispatch.
- `.trellis/spec/backend/agent-control-protocol.md` records the input cursor helper boundary.
- Targeted checks and the full release gate pass before commit.

## Architecture Baseline

This slice moves deterministic input text geometry into a lower-level module while leaving the strong Orchestrator facade responsible for mutable input state, dirty marking, command handling, rendering, keyboard/mouse dispatch, and runtime side effects.
