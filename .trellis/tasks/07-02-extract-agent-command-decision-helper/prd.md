# Extract Agent Command Decision Helper

## Requirement

Continue Goal 7 app decomposition by moving deterministic `/agent` command completion decision logic from `src/ga_tui/app.py` into the lower-level `src/ga_tui/commands.py` module.

This slice must preserve existing command-completion behavior while making `commands.py` responsible for deciding what kind of `/agent` completion is requested from raw input text. `app.py` remains the Orchestrator facade that expands those decisions using mutable UI/runtime state.

## Scope

- Add a pure `/agent` completion decision helper in `src/ga_tui/commands.py`.
- Keep command metadata already extracted in `commands.py`.
- Keep dynamic stateful expansion in `src/ga_tui/app.py`:
  - current subagent rows
  - role template rows
  - category rows
  - approval rows
  - top-level command dispatch
  - command execution side effects
- Preserve public compatibility names exported from `app.py`.
- Add focused tests for direct helper behavior and app wrapper parity.
- Extend policy gates to lock the new boundary and prevent reverse dependencies.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable command-decision boundary.

## Behavior To Preserve

- Text that is not `/agent` or `/agent ...` produces no `/agent` matches.
- `/agent` returns the sendable command row for `/agent`.
- `/agent ` returns all static subcommand rows.
- `/agent <prefix>` filters static subcommands by lowercase prefix.
- Unknown subcommands produce no matches.
- Static subcommands that do not require an agent do not request dynamic subagent rows after a complete subcommand plus trailing space.
- Subcommands requiring an agent request subagent completion when the agent argument is missing or partial.
- `role` with an agent and role prefix requests role-template completion, leaving role-template ownership in `app.py`.
- Inputs with too many tokens produce no matches.
- Existing `/workspaces ` and `/workspace ...` behavior from Task 170 remains unchanged.

## Exclusions

- Do not move `subagent_completion_rows(...)` into `commands.py`.
- Do not move `ROLE_TEMPLATES`, role-template policy, or role normalization into `commands.py`.
- Do not move `State`, command handlers, input handlers, curses integration, Web Console, dashboard, Secret Vault, history ownership, ledgers, approvals, artifacts, runtime dispatch, or command side effects into `commands.py`.
- Do not change command execution behavior.
- Do not alter history/session/subagent storage ownership.

## Verification

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

## Architecture Direction

This should move the implementation closer to `docs/agent-harness-architecture.md`: `commands.py` remains a restricted lower-level parser/decision boundary with no reverse import of `app.py`, while the strong Orchestrator facade retains mutable state, command execution, human approval gates, ledgers, artifacts, history, Secret Vault, Web Console, dashboard, runtime side effects, and curses drawing.
