# Extract Subagent Settings Target Command Helper

## Goal

Continue Goal 7 by moving the deterministic `/agent settings|model` target parser out of `src/shuheng/app.py` into the lower-level `src/shuheng/commands.py` helper module, while preserving public compatibility and executable behavior.

## What I Already Know

- `src/shuheng/app.py` still owns `subagent_settings_target_from_command(text)`.
- The helper is a pure string parser: it returns the `<agent>` token for `/agent settings|setting|config|detail|details|prefs <agent>` and `/agent model <agent>`, otherwise `""`.
- The only current call site is in input/key handling when deciding whether to open the subagent settings/model modal.
- `src/shuheng/commands.py` already owns deterministic command-completion and command-input parsing helpers with app-level compatibility aliases.
- The command helper boundary requires `commands.py` to avoid imports of `shuheng.app`, curses, mutable `State`, runtime dispatch, rendering, history, governance, Secret Vault, Web Console, dashboard, input handlers, storage roots, ledgers, or artifacts.

## Requirements

- Move the implementation of `subagent_settings_target_from_command(text)` into `src/shuheng/commands.py`.
- Keep `src/shuheng/app.py` exposing the same public name as a compatibility alias.
- Preserve existing behavior exactly:
  - Match `/agent settings <agent>` and aliases `setting`, `config`, `detail`, `details`, and `prefs`.
  - Match `/agent model <agent>`.
  - Matching is case-insensitive for command words.
  - Surrounding whitespace is ignored.
  - Extra trailing words do not match because the parser expects a single non-space target token.
  - Non-matching input returns `""`.
- Keep command execution, modal opening, `State`, subagent resolution, model setting, runtime dispatch, input/key handling, and storage roots in `app.py`.
- Update `tests/test_commands.py`, `scripts/check_policy_gates.py`, and `.trellis/spec/backend/agent-control-protocol.md` for the new durable helper boundary.
- Do not touch unrelated untracked task directories or `uv.lock`.

## Out Of Scope

- Moving `COMMANDS`.
- Moving `command_matches(...)`, `agent_command_matches(...)`, or `subagent_completion_rows(...)`.
- Moving `handle_subagent_command(...)` or any command execution handlers.
- Moving input/key handling or modal rendering.
- Changing `/agent model` behavior or adding new aliases.
- Changing subagent session/history ownership.

## Acceptance Criteria

- `commands.subagent_settings_target_from_command(...)` owns the parser.
- `app.subagent_settings_target_from_command is commands.subagent_settings_target_from_command`.
- Unit tests cover settings aliases, model command, case-insensitive commands, whitespace, extra trailing args, and non-matching input.
- Policy gate asserts helper ownership, alias parity, representative behavior, duplicate-definition absence in `app.py`, and no reverse dependency from `commands.py`.
- Backend spec documents this parser as part of the command helper boundary.
- Targeted compile, targeted Ruff, `tests/test_commands.py`, policy gates, full release-quality checks, package smoke, and `shuheng-check` pass before commit when feasible.

## Rollback

- Revert only the task commit if behavior or boundary checks regress.
- Because this is a compatibility-alias extraction, rollback restores the original app-local helper without storage or runtime migration.
