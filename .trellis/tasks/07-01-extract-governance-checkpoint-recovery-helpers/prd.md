# Extract Governance Checkpoint Recovery Helpers

## Objective

Continue decomposing `src/shuheng/app.py` by moving pure checkpoint/recovery read-model helpers into `src/shuheng/governance.py` while preserving `app.py` compatibility wrappers and existing runtime behavior.

## Scope

- Move path/row-driven checkpoint and recovery helper implementations into `governance.py`:
  - `checkpoint_history`
  - `recovery_history`
  - `recovery_plan_history`
  - `checkpoint_index_by_id`
  - `latest_checkpoint_for_task`
  - `read_checkpoint_snapshot`
  - `recovery_replay_steps`
- Keep same public names in `app.py` as wrappers that inject current app-owned ledger/checkpoint paths.
- Keep helpers lower-level than the TUI: no `shuheng.app` import, no curses import, no mutable `State`, no runtime classes, no rendering/panel/command code.
- Add direct unit tests for the lower-level helpers and wrapper parity checks for retargeted app paths.
- Update policy gates and backend spec boundary text so checkpoint/recovery helper ownership is explicit.

## Non-Goals

- Do not move `append_task_checkpoint`, `append_recovery_plan`, `append_recovery_record`, or `recover_task_action` in this slice.
- Do not change checkpoint, recovery, trace, eval, approval, artifact, or task ledger schemas.
- Do not change runtime recovery behavior, single-writer lock behavior, subagent state mutation, command handling, panel rendering, Web Console payloads, or dashboard rendering.
- Do not migrate storage roots or modify existing user runtime state.

## Acceptance Criteria

- `governance.py` owns the selected checkpoint/recovery helper implementations and remains a lower-level module.
- `app.py` wrappers preserve existing signatures and behavior while injecting `AGENT_CHECKPOINT_INDEX_PATH`, `AGENT_RECOVERY_PATH`, and `AGENT_RECOVERY_PLANS_PATH`.
- Tests cover direct helper behavior, missing/bad checkpoint snapshots, latest-checkpoint selection, replay-step shaping, and app wrapper parity under monkeypatched paths.
- `scripts/check_policy_gates.py` asserts the expanded governance module boundary.
- `.trellis/spec/backend/agent-control-protocol.md` records the new checkpoint/recovery helper boundary.
- Targeted checks and the full release gate pass before commit.

## Architecture Baseline

This slice should move the system closer to the governed harness baseline by making checkpoint/recovery read-model logic a lower-level governance boundary above `ledger_store.py`, while keeping Orchestrator-owned mutation, approvals, runtime recovery side effects, panel rendering, commands, and compatibility wiring in `app.py`.
