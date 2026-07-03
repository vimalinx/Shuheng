# Add Workflow Next Action JSON Diagnostics V1

## Goal

Expose the workflow next-action diagnostic as a machine-readable JSON
projection so AI agents, scripts, and future gateway/tool surfaces can decide
the next safe command without parsing human-oriented text.

## What I already know

- `/workflow next <run_id>` and `/workflow diagnose <run_id>` now provide a
  read-only human text projection.
- The current classification logic lives in `workflows.py` and is already
  pure over workflow/task/approval row lists.
- Shuheng already has `tui_query_json_safe(...)` and other structured query
  patterns, but the workflow command stream does not yet expose a JSON
  next-action projection.
- The architecture baseline favors explicit ledgers, auditable protocols,
  strong Orchestrator ownership, and machine-readable boundaries.

## Requirements

- Add `/workflow next-json <run_id>` and `/workflow diagnose-json <run_id>`.
- The JSON output must include:
  - `schema_version`;
  - `run_id`;
  - `found`;
  - current `status`, `workflow_ref`, `history_rows`;
  - `blocked_step` with `step_id` and `type`;
  - `stop_reason`;
  - `next_action`;
  - `commands`;
  - `approval` object with id/status when available;
  - `task` object with id/status when available;
  - `read_only` and `rows_appended:false`.
- Missing or unknown run ids must return JSON with `found:false`, not a text
  not-found string.
- The structured builder must be pure and accept workflow/task/approval rows as
  parameters.
- The existing text formatter should reuse the structured builder so text and
  JSON classifications cannot drift.
- The command must not call `continue_workflow_run_v0(...)`,
  `cancel_workflow_run_v0(...)`, approval decision functions, subagent dispatch,
  or any ledger append helper.
- Existing `/workflow next`, `/workflow diagnose`, trace, continue, and run
  behavior must remain unchanged.

## Acceptance Criteria

- [x] Missing/blank run ids render valid JSON with `found:false`.
- [x] Planned, completed, terminal, approval, task, and condition blockers
  expose the same `next_action` classifications as the text projection.
- [x] JSON commands use existing public commands only.
- [x] Text and JSON outputs are derived from the same pure structured helper.
- [x] `/workflow next-json` and `/workflow diagnose-json` are proven read-only.
- [x] Policy gate and backend spec lock command aliases, JSON schema fields,
  and side-effect invariants.

## Out Of Scope

- Automatically continuing, cancelling, approving, rejecting, retrying, or
  dispatching workflow work.
- A new workflow executor.
- Gateway/MCP/A2A exposure.
- Web/panel graph UI.
- Inlining raw artifacts, trace payloads, task transcripts, or model text.

## Technical Notes

- Likely code:
  - `src/ga_tui/workflows.py`
  - `src/ga_tui/app.py`
  - `tests/test_workflows.py`
  - `scripts/check_policy_gates.py`
  - `.trellis/spec/backend/agent-control-protocol.md`
- Reuse the existing `format_workflow_run_next_action(...)` classification
  rules by moving the data into a shared structured projection helper.
