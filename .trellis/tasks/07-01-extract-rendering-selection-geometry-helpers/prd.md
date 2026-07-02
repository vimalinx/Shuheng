# Extract Rendering Selection Geometry Helpers

## Objective

Continue decomposing `src/ga_tui/app.py` by moving curses-free selection geometry helpers into `src/ga_tui/rendering.py`, while preserving existing behavior and public compatibility names in `app.py`.

## Scope

- Move `char_index_for_cell(text, target_x)` into `src/ga_tui/rendering.py`.
- Add a pure rendering helper for ordering explicit selection points without reading `State`.
- Add a pure rendering helper for computing the selected character span for one rendered line from explicit selection points.
- Keep `src/ga_tui/app.py` compatibility names so existing tests and callers can continue importing from `ga_tui.app`.
- Keep app-owned wrappers for helpers whose existing public signatures accept `State`.
- Add unit coverage for direct rendering helpers and app wrapper parity.
- Expand policy gates so `rendering.py` remains a lower-level curses-free helper boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the new selection geometry boundary.

## Non-Goals

- Do not move `clear_selection(...)`, `selected_text(...)`, `shift_selection_lines(...)`, `main_pos_at_mouse(...)`, `update_selection_end_from_mouse(...)`, or selection auto-scroll helpers.
- Do not move `draw_text_with_selection(...)`, `draw_main(...)`, `record_running_indicator_rect(...)`, or any curses drawing.
- Do not change selection behavior, clipboard behavior, Secret copy gates, mouse handling, scrolling, command routing, Web Console, dashboard, runtime dispatch, storage roots, ledgers, approvals, artifacts, history, or external memory.
- Do not introduce imports from `ga_tui.app`, curses, mutable `State`, `SubAgentRuntime`, gateway handlers, Web Console, dashboard, command handlers, input handlers, or draw functions into `rendering.py`.

## Compatibility Contract

- `app.char_index_for_cell(...)` must remain available and match `rendering.char_index_for_cell(...)`.
- `app.ordered_selection_points(state)` must keep the same public signature and delegate to a pure helper using `state.selection_start` and `state.selection_end`.
- `app.selection_span_for_line(state, line_idx, text)` must keep the same public signature and delegate to a pure helper using explicit ordered points.
- Existing selection ranges, clamping, same-point empty selection behavior, wide-character cell targeting, and combining-character handling must be preserved.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py tests/test_cell_utils.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release gate from `goal-7/plan.md`, including full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline

This slice should move the system closer to `docs/agent-harness-architecture.md` by keeping deterministic rendering geometry in a lower-level policy-gated module while preserving the strong Orchestrator facade in `app.py` for mutable UI state, redraw decisions, curses drawing, command/input dispatch, runtime side effects, ledgers, approvals, artifacts, history, and external-memory boundaries.
