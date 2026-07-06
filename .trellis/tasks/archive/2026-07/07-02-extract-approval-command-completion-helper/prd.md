# Extract Approval Command Completion Helper

## Summary

Continue Goal 7 by moving deterministic `/approve` and `/reject` command completion row shaping from `src/shuheng/app.py` into `src/shuheng/commands.py`, while keeping approval ledger/state access and summary truncation policy in the app facade.

## Problem

`src/shuheng/app.py` still mixes app-owned pending approval retrieval with deterministic command row formatting. The approval source of truth must remain app-owned because it may depend on `State`, ledgers, and approval governance. The pure row matching over explicit approval candidates can be tested in `commands.py`.

## Scope

- Add a pure helper in `src/shuheng/commands.py` for `/approve` and `/reject` completion rows.
- The helper must accept raw command text and an explicit iterable of `(approval_id, summary)` values.
- Preserve existing prefix filtering and command casing behavior.
- Keep `approval_command_matches(text, state)` in `src/shuheng/app.py` as the compatibility wrapper that reads app-owned pending approvals and applies `truncate_cells(..., 70)` before delegation.
- Re-export the new helper from `src/shuheng/app.py`.
- Expand command unit tests and policy gates.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the new boundary.

## Out Of Scope

- Do not move `pending_approvals(...)`, approval ledger reads, approval/reject execution, policy decisions, mutable `State`, or governance stores into `commands.py`.
- Do not move `truncate_cells(...)` or summary width policy into `commands.py`.
- Do not change command routing order, top-level command fallback, `/agent`, `/workspace(s)`, `/archived`, category commands, input handling, rendering, Web Console, dashboard, Secret Vault, ledgers, artifacts, storage roots, or history ownership.

## Behavior Requirements

- Non-matching text returns `[]`.
- `/approve ` and `/reject ` return rows for all injected approval candidates.
- Prefix filtering remains case-sensitive by `approval_id.startswith(prefix)`, matching the existing behavior.
- Returned rows have `cmd` as `/{approve|reject} {approval_id}`, empty args, injected summary as description, and `sendable=True`.
- App wrapper still returns `[]` when no pending approvals are supplied.
- App wrapper still truncates summaries with existing cell-width policy before passing summaries to the pure helper.

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

This moves the code closer to `docs/agent-harness-architecture.md`: deterministic approval command row shaping becomes a restricted lower-level helper, while the strong Orchestrator facade keeps approval source-of-truth access, policy gates, ledger semantics, mutable UI state, command execution, runtime side effects, artifacts, Secret Vault, Web Console, dashboard, and rendering.
