# Extract Input Text Edit Helpers

## Goal

Move deterministic text-edit transition calculations out of `src/ga_tui/app.py`
into `src/ga_tui/input_controller.py` while preserving the existing TUI
behavior and compatibility surface.

## Scope

- Add a small immutable result type for input text/cursor transitions.
- Add pure helpers for:
  - inserting text at a clamped cursor;
  - deleting the character before the cursor;
  - deleting the character at the cursor;
  - moving the cursor by a horizontal delta with clamping.
- Re-export the moved helpers from `src/ga_tui/app.py` as compatibility aliases.
- Update app-owned wrappers/call sites to delegate to the helpers while keeping
  existing mutation, command-index reset, history-browse reset, dirty marking,
  paste-mode handling, and curses key dispatch in `app.py`.
- Extend `tests/test_input_controller.py`, `scripts/check_policy_gates.py`, and
  `.trellis/spec/backend/agent-control-protocol.md`.

## Non-Goals

- Do not move `handle_key(...)`, `handle_mouse(...)`, command completion,
  command routing, interaction selection, paste-mode state, curses constants,
  mutable `State`, rendering, Web Console, dashboard, runtime dispatch, ledgers,
  approvals, artifacts, Secret Vault behavior, or history ownership.
- Do not change public command behavior or submit behavior.
- Do not change storage roots or session transcript semantics.
- Do not introduce reverse imports from `input_controller.py` into `app.py`.

## Behavior Requirements

- Empty insertion returns the original text/cursor and reports no edit.
- Non-empty insertion clamps the source cursor, inserts at that point, and moves
  the cursor by the inserted text length.
- Backspace-style deletion clamps the source cursor, removes the character before
  the cursor only when the cursor is greater than zero, and otherwise leaves text
  unchanged.
- Delete-style deletion clamps the source cursor, removes the character at the
  cursor only when the cursor is before the end of the text, and otherwise leaves
  text unchanged.
- Horizontal cursor movement clamps the result into `[0, len(text)]`.
- Existing app behavior remains: backspace/delete keys still reset command
  completion, reset input-history browsing, mark dirty even when the text is
  unchanged, and printable input still inserts one printable key.

## Verification

- Targeted compile and Ruff for touched files.
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_input_controller.py -p no:cacheprovider`.
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`.
- Full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`,
  full pytest, package build, wheel/sdist smoke, and `shuheng-check`.
- Compare the change against `docs/agent-harness-architecture.md` before
  claiming the slice is complete.
