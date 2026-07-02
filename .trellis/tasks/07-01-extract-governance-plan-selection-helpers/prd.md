# Extract Governance Plan Selection Helpers

## Objective

Continue decomposing `src/ga_tui/app.py` by moving pure active-plan selection over already-loaded task rows into `src/ga_tui/governance.py`, while preserving `app.py` compatibility wrappers and runtime behavior.

## Scope

- Move the implementation of `selected_plan_id_from_rows(rows, preferred_plan_id="", require_active=False)` into `governance.py`.
- Keep the public `app.py` function name as a compatibility wrapper delegating to `governance.py`.
- Preserve existing behavior:
  - only rows with `kind == "plan"` are candidates.
  - a preferred plan id wins when present in the candidates.
  - active plans are rows whose status is not terminal.
  - `require_active=True` returns `""` when no active plan exists.
  - fallback chooses the newest candidate by existing `row_timestamp(...)` ordering.
- Add unit tests for direct helper behavior and app wrapper parity.
- Update policy gates and backend spec boundary text.

## Non-Goals

- Do not move `rightbar_selected_plan_id(...)`, `hydrate_active_plan_from_ledger(...)`, `resolve_plan_step_id(...)`, `create_task_plan(...)`, active plan state mutation, rightbar rendering, command/control handlers, task ledger writes, or storage roots.
- Do not change plan/task ledger schemas or terminal status semantics.
- Do not change active plan hydration side effects or auto-continue reset behavior.

## Acceptance Criteria

- `governance.py` owns `selected_plan_id_from_rows(...)` and remains lower-level than the TUI.
- `app.py` compatibility wrapper preserves the old signature and behavior.
- Tests cover preferred id, active-vs-terminal selection, require-active empty fallback, newest fallback, non-plan filtering, and wrapper parity.
- `scripts/check_policy_gates.py` asserts the expanded governance boundary.
- `.trellis/spec/backend/agent-control-protocol.md` records the plan-selection helper boundary.
- Targeted checks and the full release gate pass before commit.

## Architecture Baseline

This slice moves task-ledger plan row interpretation toward the governance layer while leaving the strong Orchestrator facade responsible for live TUI state, plan hydration, task ledger writes, rightbar rendering, command handling, and runtime side effects.
