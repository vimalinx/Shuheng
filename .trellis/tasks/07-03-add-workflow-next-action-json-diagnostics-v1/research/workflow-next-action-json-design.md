# Workflow Next-Action JSON Diagnostics Design

## Decision

Add a pure structured projection beside the existing text diagnostic and derive
the text formatter from that projection. The command layer should serialize the
projection to pretty JSON for TUI output.

## Rationale

- AI agents should not need brittle text parsing to decide whether to continue,
  wait, approve/reject, inspect, or cancel/edit.
- Reusing one structured helper prevents drift between human text and machine
  JSON outputs.
- Keeping the command read-only preserves the strong Orchestrator boundary:
  diagnostics recommend existing commands; they do not execute them.

## Shape

The projection should include:

- `schema_version: shuheng.workflow_next_action.v1`
- `run_id`
- `found`
- `status`
- `workflow_ref`
- `history_rows`
- `blocked_step`
- `stop_reason`
- `next_action`
- `commands`
- `approval`
- `task`
- `read_only: true`
- `rows_appended: false`

## Boundary

`workflows.py` may classify row lists and return a JSON-safe dict. `app.py`
may read ledgers and serialize the dict. Neither command should continue,
cancel, approve, reject, dispatch, append ledgers, or read raw artifact bodies.
