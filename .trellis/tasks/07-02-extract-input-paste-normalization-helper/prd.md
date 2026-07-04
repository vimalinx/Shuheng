# Extract Input Paste Normalization Helper

## Objective

Continue Goal 7 app.py decomposition by moving deterministic pasted-text
normalization out of `src/shuheng/app.py` and into the lower-level
`src/shuheng/input_controller.py` helper boundary, while preserving existing
paste behavior and `app.py` compatibility.

## Scope

- Add `normalize_pasted_text(text)` to `src/shuheng/input_controller.py`.
- Preserve the existing behavior exactly:
  - collapse one or more CR/LF runs plus surrounding spaces/tabs into one
    literal space
  - replace remaining tabs with four spaces
  - keep other text unchanged
- Re-export `normalize_pasted_text` from `src/shuheng/app.py` as a compatibility
  alias.
- Keep bracketed paste mode, paste buffer state, `handle_key(...)`,
  `read_terminal_key(...)`, `PASTE_START` / `PASTE_END` detection, TTY escape
  setup, curses polling, mutable `State`, and input insertion in `app.py`.
- Add unit tests for direct helper behavior and app alias parity.
- Update policy gates and backend spec so this boundary remains executable.

## Out Of Scope

- Do not move `handle_key(...)`, `read_terminal_key(...)`, `modal_read_key(...)`,
  `drain_pending_keys(...)`, `tty_escape(...)`, `enable_bracketed_paste(...)`,
  `disable_bracketed_paste(...)`, `enable_mouse_drag(...)`,
  `disable_mouse_drag(...)`, or TTY/curses event-loop behavior.
- Do not move paste buffer fields or mutation out of `State`.
- Do not import `shuheng.app`, curses, mutable `State`, `RenderLine`, Web Console,
  dashboard, runtime dispatch, command handlers, storage roots, ledgers,
  approvals, artifacts, Secret Vault behavior, or history ownership from
  `input_controller.py`.
- Do not change paste normalization semantics.

## Compatibility Requirements

- Existing callers of `app.normalize_pasted_text(text)` must keep working.
- `handle_key(...)` must still call `normalize_pasted_text(...)` by the same
  app-level name.
- `input_controller.py` helper must be deterministic over explicit text and must
  not read terminal state, curses, or mutable TUI state.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/input_controller.py tests/test_input_controller.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/input_controller.py tests/test_input_controller.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_input_controller.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 gate before commit: full Ruff, release hygiene, runtime smoke,
  compileall, `git diff --check`, full pytest, package build, wheel/sdist
  smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline

This should move the system closer to `docs/agent-harness-architecture.md` by
placing deterministic input text cleanup behind a restricted lower-level helper
boundary while keeping the strong Orchestrator/app facade as the owner of
terminal integration, mutable UI state, paste-mode state, key dispatch, command
dispatch, runtime side effects, ledgers, approvals, artifacts, history,
Secret Vault, Web Console, dashboard, and drawing.

## Rollback

Revert the scoped commit or restore the helper body in `src/shuheng/app.py` if
paste behavior changes or `input_controller.py` gains forbidden dependencies.
