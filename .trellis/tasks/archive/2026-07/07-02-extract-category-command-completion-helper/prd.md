# Extract Category Command Completion Helper

## Summary

Continue Goal 7 by moving the deterministic `/filter`, `/collapse`, and `/expand` completion row shaping out of `src/shuheng/app.py` into `src/shuheng/commands.py`, without moving history access, `State`, command execution, or category metadata ownership.

## Problem

`src/shuheng/app.py` still owns both the app-specific category source of truth and the deterministic command-completion row formatting for category commands. The history/category source must stay app-owned because it reads `State.history`, `session_meta_for(...)`, `session_category_label(...)`, `category_key(...)`, and `category_sort_key(...)`, but row shaping over explicit category counts can be tested as a pure command helper.

## Scope

- Add a pure helper in `src/shuheng/commands.py` that accepts raw command text and explicit category counts.
- Preserve the existing public completion rows for `/filter`, `/collapse`, and `/expand`.
- Keep `category_command_matches(text, state)` in `src/shuheng/app.py` as the compatibility wrapper that reads app-owned history/meta and delegates row shaping.
- Re-export the new helper from `src/shuheng/app.py` for compatibility.
- Expand command unit tests and policy gates.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the durable command-helper boundary.

## Out Of Scope

- Do not move `State`, `state.history`, `session_meta_for(...)`, `session_category_label(...)`, `category_key(...)`, or `category_sort_key(...)` into `commands.py`.
- Do not move command execution handlers.
- Do not move `/approve` or `/reject` completion.
- Do not change `COMMANDS`, top-level routing order, hidden `/llm` or `/models` alias behavior, input handling, rendering, Web Console, dashboard, Secret Vault, ledgers, approvals, artifacts, storage roots, or history ownership.

## Behavior Requirements

- Non-matching text returns `[]`.
- Missing `state` at the app wrapper level still returns `[]`.
- `/filter ` includes `/filter off` and category rows.
- `/filter o` includes `/filter off` when the prefix matches.
- `/collapse ` and `/expand ` include their `all` static row and category rows.
- Prefix filtering remains case-insensitive against category labels.
- Category row descriptions stay in the existing `"{count} 个会话"` format.
- Category row ordering remains determined by app-owned category sort keys before the helper is called.
- `commands.py` must remain free of `shuheng.app`, curses, mutable `State`, runtime classes, rendering, input-controller, governance, history-store, Secret Vault, Web Console, dashboard, and handlers.

## Verification

- Targeted compile for touched files.
- Targeted Ruff for touched files.
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_commands.py -p no:cacheprovider`.
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`.
- Full Goal 7 quality gate before commit:
  - full Ruff
  - release hygiene
  - runtime smoke
  - compileall
  - `git diff --check`
  - full pytest
  - build sdist/wheel
  - wheel smoke
  - `shuheng-check --root /home/vimalinx/Programs/GenericAgent`

## Architecture Direction

This should move the implementation closer to `docs/agent-harness-architecture.md`: deterministic command row shaping becomes a restricted lower-level helper, while the strong Orchestrator facade keeps history ownership, mutable UI state, command execution, ledgers, approvals, artifacts, Secret Vault, Web Console, dashboard, and runtime side effects.
