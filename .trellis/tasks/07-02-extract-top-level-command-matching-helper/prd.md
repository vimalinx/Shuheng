# Extract Top-Level Command Matching Helper

## Objective

Move deterministic top-level command prefix matching out of `src/ga_tui/app.py` into `src/ga_tui/commands.py`, preserving the current completion behavior and keeping `app.py` as the Orchestrator facade for dynamic/stateful command completion and command execution.

## Scope

- Add a pure helper in `src/ga_tui/commands.py` that receives explicit command candidates and returns matching top-level command completion rows.
- Preserve existing top-level completion behavior:
  - Non-slash input returns no matches.
  - Slash input containing a space after stripping returns no top-level fallback matches.
  - Matching is case-insensitive.
  - `/mo` matches the visible `/model` row through the existing `COMMANDS` catalog.
  - Hidden model aliases such as `/ll` and `/models` do not appear unless they are present in the injected visible command catalog.
- Keep `src/ga_tui/app.py` as the owner of:
  - `COMMANDS` visible command catalog.
  - `/agent` dynamic subagent and role completion expansion.
  - `/workspace(s)`, `/archived`, `/filter`, `/collapse`, `/expand`, `/approve`, and `/reject` stateful or specialized completion routing.
  - Command handlers, input handling, mutable `State`, runtime side effects, ledgers, approvals, artifacts, Secret Vault behavior, storage roots, history ownership, Web Console, dashboard, and curses rendering.
- Keep compatibility exports or wrappers in `app.py` so existing import/test surfaces do not break.

## Non-Goals

- Do not move `COMMANDS` into `commands.py`.
- Do not move any command handlers or execution side effects.
- Do not change visible command labels, descriptions, sendability, or insertion text semantics.
- Do not alter hidden model alias handling.
- Do not alter category, approval, workspace, archived, agent, or subagent completion behavior beyond delegating the final static top-level fallback.

## Acceptance Criteria

- `src/ga_tui/commands.py` owns the pure top-level command prefix helper.
- `src/ga_tui/app.py` delegates the final top-level fallback in `command_matches(...)` to the new helper.
- `tests/test_commands.py` covers direct helper behavior and app wrapper/dispatch parity for slash, non-slash, spaces, case-insensitive matching, `/mo`, and hidden-alias exclusion.
- `scripts/check_policy_gates.py` locks helper ownership, representative behavior, app compatibility, duplicate-definition absence in `app.py`, and the commands no-reverse-dependency boundary.
- `.trellis/spec/backend/agent-control-protocol.md` documents the durable command module boundary update.
- Goal 7 `tasks.md` records this task, verification, commit hash, and architecture-baseline direction.

## Verification Plan

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/commands.py tests/test_commands.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/commands.py tests/test_commands.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_commands.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 gate before commit:
  - full Ruff
  - release hygiene
  - runtime smoke
  - compileall
  - `git diff --check`
  - full pytest
  - package build
  - wheel/sdist smoke
  - `shuheng-check --root /home/vimalinx/Programs/GenericAgent`

## Architecture Baseline

This slice should move the system closer to `docs/agent-harness-architecture.md` by keeping deterministic command parsing in a restricted lower-level helper module while preserving the strong Orchestrator facade in `app.py` for mutable state, human approval gates, ledgers, artifacts, runtime side effects, history, Secret Vault, Web Console, dashboard, and rendering.
