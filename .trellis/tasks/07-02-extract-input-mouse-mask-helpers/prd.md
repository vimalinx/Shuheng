# Extract Input Mouse Mask Helpers

## Objective

Continue Goal 7 app.py decomposition by moving deterministic mouse bitmask
classification logic out of `src/shuheng/app.py` and into the lower-level
`src/shuheng/input_controller.py` helper boundary, while preserving existing
`app.py` compatibility names and mouse behavior.

## Scope

- Add pure helpers in `src/shuheng/input_controller.py` that compute:
  - button-state masks for a given button number from explicit constants
  - modifier masks from explicit constants
  - known bstate masks from explicit constants
  - auxiliary-or-unknown mouse event detection
  - clean button-1 action detection
- Keep `src/shuheng/app.py` responsible for reading curses constants and exposing
  the existing public helper names:
  - `mouse_button_mask(button_no)`
  - `mouse_modifier_mask()`
  - `mouse_known_bstate_mask()`
  - `mouse_auxiliary_or_unknown_event(bstate)`
  - `clean_button1_action(bstate, allowed_button1_mask)`
- Preserve existing `handle_mouse(...)` behavior and all call sites.
- Add unit tests for direct `input_controller.py` behavior and app wrapper
  parity.
- Update policy gates so the helper ownership and `input_controller.py`
  no-reverse-dependency boundary stay executable.
- Update `.trellis/spec/backend/agent-control-protocol.md` if this becomes a
  durable input-controller contract.

## Out Of Scope

- Do not move `handle_mouse(...)`, `toggle_process_at_line(...)`, mouse-driven
  selection mutation, sidebar activation, popup handling, input focus behavior,
  clipboard/Secret copy gates, draw functions, or curses event-loop code.
- Do not import `shuheng.app`, curses, mutable `State`, `RenderLine`,
  Web Console, dashboard, runtime dispatch, command handlers, storage roots,
  ledgers, approvals, artifacts, Secret Vault behavior, or history ownership
  from `input_controller.py`.
- Do not change curses mouse masks, modifier semantics, selection behavior, or
  public helper names.

## Compatibility Requirements

- Existing callers of `app.mouse_button_mask(...)`,
  `app.mouse_modifier_mask()`, `app.mouse_known_bstate_mask()`,
  `app.mouse_auxiliary_or_unknown_event(...)`, and
  `app.clean_button1_action(...)` must keep working.
- `input_controller.py` helpers must be deterministic over explicit integer
  constants and must not read curses globals directly.
- `app.py` may remain the owner of curses constant lookup and inject those
  values into pure helpers.
- `handle_mouse(...)` must still call the same app-level helper names so this is
  a mechanical extraction, not an input behavior rewrite.

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
placing deterministic input event classification behind a restricted
lower-level helper boundary while keeping the strong Orchestrator/app facade as
the owner of curses integration, mutable UI state, selection mutation, command
dispatch, runtime side effects, ledgers, approvals, artifacts, history,
Secret Vault, Web Console, dashboard, and draw behavior.

## Rollback

Revert the scoped commit or restore the mouse helper bodies in
`src/shuheng/app.py` if the extraction changes mouse behavior or introduces an
input-controller dependency on app/curses/state owners.
