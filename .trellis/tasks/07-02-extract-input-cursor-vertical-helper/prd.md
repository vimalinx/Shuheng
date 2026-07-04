# Extract Input Cursor Vertical Helper

## Goal

Continue Goal 7 app.py decomposition by moving the deterministic vertical input
cursor target calculation out of `src/shuheng/app.py` and into the lower-level
`src/shuheng/input_controller.py` helper boundary, while preserving the existing
`move_input_cursor_vertical(...)` public behavior in `app.py`.

## Requirements

- Add a pure helper to `src/shuheng/input_controller.py` that calculates the next
  raw cursor index for vertical input movement over explicit text, width, cursor,
  and direction inputs.
- Preserve the existing behavior exactly:
  - empty text returns no movement
  - single-line display input returns no movement
  - moving beyond the first or last wrapped display line consumes the key but
    keeps the cursor unchanged
  - moving to an available wrapped line keeps the same display cell x as closely
    as possible, including wide and combining characters
  - raw cursor output is clamped to the source text length
- Keep `src/shuheng/app.py` as the compatibility and Orchestrator facade:
  - `move_input_cursor_vertical(state, width, direction)` still mutates
    `state.input_cursor`, calls `clamp_input_cursor(state)`, calls
    `mark_dirty(state)` whenever an in-range target cursor is produced, and
    returns the existing boolean key-consumption result.
- Add unit tests for direct helper behavior and app wrapper parity.
- Update policy gates and backend spec so this boundary remains executable.

## Acceptance Criteria

- `src/shuheng/input_controller.py` owns the pure vertical cursor target helper.
- `src/shuheng/app.py` exposes the helper as a compatibility alias or wrapper and
  no longer keeps duplicate pure target-calculation logic inline.
- `move_input_cursor_vertical(...)` continues to own only app state mutation,
  dirty marking, and compatibility behavior.
- Existing public helper names and key-handler call sites keep working.
- Policy gates fail if `input_controller.py` imports `shuheng.app`, curses,
  mutable `State`, rendering types, command handlers, Web Console, dashboard, or
  runtime-dispatch owners.

## Out Of Scope

- Do not move `handle_key(...)`, `input_width_for_key(...)`,
  `read_terminal_key(...)`, `modal_read_key(...)`, `drain_pending_keys(...)`,
  bracketed paste setup, TTY escape helpers, mouse handlers, command routing, or
  curses event-loop behavior.
- Do not move mutable input fields out of `State`.
- Do not change command completion, input history browsing, interaction
  selection, scrolling, or submission behavior.
- Do not import `State`, curses, `RenderLine`, Web Console, dashboard, runtime
  dispatch, command handlers, storage roots, ledgers, approvals, artifacts,
  Secret Vault behavior, or history ownership from `input_controller.py`.

## Technical Approach

- Introduce a small immutable result for pure vertical cursor movement, or a
  tuple that carries:
  - whether the key was consumed
  - whether the raw cursor should change
  - the target raw cursor index
- Reuse the already-extracted input geometry helpers in `input_controller.py`:
  `input_cursor_info(...)`, `display_index_for_cell(...)`, and
  `display_cursor_to_raw(...)`.
- Keep `app.move_input_cursor_vertical(...)` as a thin wrapper that delegates to
  the pure helper, applies mutation only when a target cursor is returned, then
  clamps and marks dirty.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/input_controller.py tests/test_input_controller.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/input_controller.py tests/test_input_controller.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_input_controller.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 gate before commit: full Ruff, release hygiene, runtime smoke,
  compileall, `git diff --check`, full pytest, package build, wheel/sdist smoke,
  and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline

This should move the system closer to `docs/agent-harness-architecture.md` by
placing deterministic input cursor geometry behind a restricted lower-level
helper boundary while keeping the strong Orchestrator/app facade as the owner of
terminal integration, mutable UI state, key dispatch, command dispatch, runtime
side effects, ledgers, approvals, artifacts, history, Secret Vault, Web Console,
dashboard, and drawing.

## Rollback

Revert the scoped commit or restore the target-calculation body in
`src/shuheng/app.py` if vertical cursor movement changes or
`input_controller.py` gains forbidden dependencies.
