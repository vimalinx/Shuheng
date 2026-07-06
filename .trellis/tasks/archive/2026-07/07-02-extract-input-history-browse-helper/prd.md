# Extract Input History Browse Helper

## Goal

Continue Goal 7 app.py decomposition by moving deterministic input-history
browse target calculation out of `src/shuheng/app.py` and into the lower-level
`src/shuheng/input_controller.py` helper boundary, while preserving the existing
public `browse_input_history(state, direction)` behavior in `app.py`.

## Requirements

- Add a pure helper to `src/shuheng/input_controller.py` that receives explicit
  input history state:
  - history entries
  - current input text and cursor
  - current browse index
  - draft text and draft cursor
  - direction
- Return a deterministic result describing:
  - whether the key was consumed
  - the next input text and cursor to apply
  - the next browse index
  - the next draft text and draft cursor
- Preserve the existing behavior exactly:
  - empty history returns no consumption
  - pressing Down before browsing returns no consumption
  - first Up stores the current input draft/cursor and selects the latest history item
  - further Up clamps at the oldest history item
  - Down moves toward newer items
  - moving beyond the newest item restores the saved draft and clears browse state
  - every consumed browse event resets the command index and marks the UI dirty in `app.py`
- Keep `src/shuheng/app.py` as the compatibility and Orchestrator facade:
  - `browse_input_history(state, direction)` still owns `State` mutation,
    `set_input_text(...)`, `state.command_index = 0`, and `mark_dirty(state)`.

## Acceptance Criteria

- `src/shuheng/input_controller.py` owns the pure history-browse result helper.
- `src/shuheng/app.py` exposes the helper as a compatibility alias or wrapper and
  no longer keeps duplicate pure index/draft transition logic inline.
- Existing public helper names and key-handler call sites keep working.
- Policy gates fail if `input_controller.py` imports `shuheng.app`, curses,
  mutable `State`, rendering types, command handlers, Web Console, dashboard, or
  runtime-dispatch owners.

## Out Of Scope

- Do not move `browse_input_history(...)` itself out of `app.py`.
- Do not move `handle_key(...)`, `input_width_for_key(...)`,
  `read_terminal_key(...)`, `modal_read_key(...)`, bracketed paste setup,
  TTY escape helpers, mouse handlers, command routing, or curses event-loop
  behavior.
- Do not move mutable input fields out of `State`.
- Do not change command completion, interaction selection, scrolling, or
  submission behavior.
- Do not import `State`, curses, `RenderLine`, Web Console, dashboard, runtime
  dispatch, command handlers, storage roots, ledgers, approvals, artifacts,
  Secret Vault behavior, or history ownership from `input_controller.py`.

## Technical Approach

- Use a small immutable dataclass or tuple result in `input_controller.py` for
  the browse transition.
- Keep the helper deterministic over plain values and built-in collections only.
- In `app.browse_input_history(...)`, delegate transition calculation, then
  apply the returned text/cursor through existing `set_input_text(...)` so cursor
  clamping remains app-compatible.

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
placing deterministic input-history transition logic behind a restricted
lower-level helper boundary while keeping the strong Orchestrator/app facade as
the owner of terminal integration, mutable UI state, key dispatch, command
dispatch, runtime side effects, ledgers, approvals, artifacts, history, Secret
Vault, Web Console, dashboard, and drawing.

## Rollback

Revert the scoped commit or restore the transition body in
`src/shuheng/app.py` if input-history browsing changes or `input_controller.py`
gains forbidden dependencies.
