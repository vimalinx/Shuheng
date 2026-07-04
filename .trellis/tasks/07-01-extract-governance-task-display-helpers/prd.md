# Extract Governance Task Display Helpers

## Objective

Continue decomposing `src/shuheng/app.py` by moving pure task-ledger display helper logic into `src/shuheng/governance.py`, while keeping `app.py` wrappers responsible for mutable app-owned owner-name lookup.

## Scope

- Move pure helpers into `governance.py`:
  - `task_status_marker(status, approval="-")`
  - `row_looks_like_subagent_task(row, owner)`
  - task row title selection over already-loaded rows and an injected owner display name
- Keep public `app.py` function names compatible:
  - `task_status_marker(...)` delegates directly.
  - `row_looks_like_subagent_task(...)` delegates directly.
  - `task_display_title(row, state=None)` keeps current signature and injects `task_owner_display_name(state, row)` into the lower-level helper.
- Add unit tests for direct helper behavior and wrapper parity.
- Update policy gates and backend spec boundary text.

## Non-Goals

- Do not move `task_owner_display_name(...)`, subagent meta file IO, `State` lookup, rightbar rendering, panel rendering, Web Console payloads, dashboard home-line construction, or command handling.
- Do not change task ledger schemas, approval semantics, or task status values.
- Do not change Unicode status markers or user-visible task title fallback behavior.

## Acceptance Criteria

- `governance.py` owns task status marker, subagent-task row predicate, and pure title selection.
- `app.py` wrappers preserve existing signatures and behavior.
- Tests cover completed/failed/pending/running/default markers, subagent row detection, explicit-title precedence, owner-name fallback, objective fallback, and wrapper parity.
- `scripts/check_policy_gates.py` asserts direct behavior and expanded boundary.
- `.trellis/spec/backend/agent-control-protocol.md` records the task display helper boundary.
- Targeted checks and the full release gate pass before commit.

## Architecture Baseline

This slice should move the system closer to the governed harness baseline by placing task-ledger row interpretation in the governance layer while keeping app-owned runtime state, subagent metadata lookup, UI panels, commands, and rendering in the Orchestrator facade.
