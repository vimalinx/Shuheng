# Extract Command Completion Helpers

## Goal

Continue Goal 7 by moving deterministic command-completion helpers out of
`src/shuheng/app.py` into a lower-level `src/shuheng/commands.py` module, while
preserving executable behavior and the existing `shuheng.app` compatibility
surface.

## What I Already Know

- `docs/app-py-decomposition-plan.md` names `commands.py` as the eventual owner
  for command parsing and command handlers.
- Full command-handler extraction is not safe yet because several completion
  paths still depend on `State`, `ROLE_TEMPLATES`, history category metadata,
  pending approvals, and runtime-owned side effects.
- The first safe slice is the pure command-completion layer: static command
  option constants, completion insertion text, archived-view completion, and
  workspace completion.
- `app.py` must keep public aliases/wrappers because tests and policy gates
  still import many helpers from `shuheng.app`.

## Requirements

- Add `src/shuheng/commands.py` as a lower-level module for pure command
  completion constants/helpers.
- Move these pure symbols into `commands.py`:
  - `AGENT_SUBCOMMANDS`
  - `AGENT_SUBCOMMANDS_REQUIRING_AGENT`
  - `AGENT_SUBCOMMANDS_SEND_AFTER_AGENT`
  - `WORKSPACE_SUBCOMMANDS`
  - `completion_insert_text(...)`
  - `archived_command_matches(...)`
  - `workspace_command_matches(...)`
- Keep `agent_command_matches(...)`, `subagent_completion_rows(...)`,
  `category_command_matches(...)`, `approval_command_matches(...)`, and
  `command_matches(...)` in `app.py` for now.
- Preserve existing completion output for `/agent`, `/archived`, `/workspace`,
  and `/workspaces` inputs.
- Keep `app.py` compatibility aliases for moved constants/functions.
- Add unit tests for direct `commands.py` behavior and app compatibility parity.
- Add a policy gate proving `commands.py` owns the moved helpers and does not
  import `shuheng.app`, curses, mutable `State`, rendering, runtime dispatch, Web
  Console, dashboard, Secret Vault, governance stores, or history stores.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable
  command-completion boundary.

## Out Of Scope

- Moving command execution handlers.
- Moving `command_matches(...)` dispatch as a whole.
- Moving stateful completion helpers that require `State`, subagent runtime
  objects, role templates, session categories, or pending approvals.
- Changing command grammar, visible labels, sendability, or command behavior.
- Changing storage roots, history/session ownership, approvals, artifacts,
  Secret Vault behavior, Web Console payloads, dashboard rendering, or input
  event handling.

## Acceptance Criteria

- `src/shuheng/commands.py` exists and contains the scoped helpers.
- `src/shuheng/app.py` imports/re-exports the moved helpers and still delegates
  existing completion call sites correctly.
- Targeted tests for `commands.py` pass.
- `scripts/check_policy_gates.py` covers the new command module boundary.
- Full Goal 7 verification passes: targeted compile/Ruff/tests, policy gates,
  full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`,
  full pytest, build, wheel smoke, and `shuheng-check`.

## Architecture Baseline Check

This slice should move the system closer to the governed harness baseline by
turning deterministic command-completion shape logic into a restricted
lower-level module. The strong Orchestrator facade in `app.py` remains the owner
of mutable UI state, approvals, ledgers, artifacts, Secret Vault, Web Console,
dashboard, input handling, command dispatch, and runtime side effects.

## Rollback

Rollback is the single work commit for this task. No runtime state or user data
is migrated by this change.
