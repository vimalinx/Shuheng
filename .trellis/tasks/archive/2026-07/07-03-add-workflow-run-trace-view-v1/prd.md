# Add Workflow Run Trace View V1

## Goal

Add a read-only workflow run trace/provenance view so users can audit what
happened inside a workflow run without manually stitching together
`workflow_runs.jsonl`, task rows, approval rows, artifact refs, and trace rows.
This moves workflow v0 closer to a governed engineering system with explicit
ledgers, artifact references, provenance, and auditable protocol boundaries.

## What I already know

- Current workflow v0 already has `/workflow runs`, `/workflow show <run_id>`,
  `/workflow continue|resume <run_id>`, `/workflow cancel <run_id>`, and a
  `/workflows` panel.
- `workflows.py` owns pure workflow projection/formatting helpers and must stay
  side-effect free.
- `app.py` owns ledger reads, workflow command routing, approval bridge, and
  agent-task bridge.
- Previous external benchmark favored run observability, resumability, artifact
  provenance, and human approval before graph editing or arbitrary tool
  execution.
- Architecture baseline requires strong Orchestrator, shared ledgers, artifact
  refs and provenance, single-writer enforcement, human approval gates, and
  auditable agent communication.

## Requirements

- Add `/workflow trace <run_id>` and `/workflow provenance <run_id>` aliases.
- The command must be read-only and append no workflow/task/progress/approval/
  artifact/trace rows.
- The command must render:
  - latest workflow run status, workflow ref, history row count, timestamps,
    and stop reason;
  - append-only run timeline with row index, status, updated timestamp,
    completed/total steps, blocked step/type, and reason;
  - step-level latest state including task ids, approval ids, agent ids,
    retry counters, artifact refs, and errors;
  - linked task rows for task ids referenced by workflow steps, including
    status, assigned agent, summary/error, and artifact refs when present;
  - linked approval rows for approval ids referenced by workflow rows/steps,
    including status, action, risk, and task id when present;
  - linked artifact refs from workflow rows, steps, linked task rows, and
    matching artifact index rows by URI;
  - linked trace refs for task ids referenced by workflow steps.
- Missing or blank run id must render the same not-found semantics as existing
  workflow inspection commands.
- The pure formatter must accept rows as parameters; it must not read files,
  import app/runtime/UI owners, or mutate any ledger.
- App command wiring must perform ledger reads and delegate rendering to the
  pure formatter.
- Existing `/workflow show` behavior remains unchanged.

## Acceptance Criteria

- [x] `workflows.format_workflow_run_trace(...)` formats a missing run as not
  found.
- [x] `workflows.format_workflow_run_trace(...)` formats run timeline, latest
  step state, linked task rows, linked approval rows, artifact refs, and trace
  refs from provided row lists.
- [x] `/workflow trace <run_id>` and `/workflow provenance <run_id>` route to
  the formatter and are read-only.
- [x] Tests prove the command does not append workflow/task/progress/approval/
  artifact/trace rows.
- [x] Policy gate locks the command alias, pure formatter ownership, and
  read-only side-effect invariants.
- [x] Backend spec records the workflow run trace/provenance contract.

## Out Of Scope

- New workflow executor or state transition.
- Auto-recovery, retry dispatch, approval decisions, or task continuation.
- Raw artifact content or raw trace payload inlining.
- Graph editor, graph visualization, timeline TUI panel, or web UI.
- MCP/A2A workflow gateway.

## Technical Notes

- Likely code:
  - `src/ga_tui/workflows.py`
  - `src/ga_tui/app.py`
  - `tests/test_workflows.py`
  - `scripts/check_policy_gates.py`
  - `.trellis/spec/backend/agent-control-protocol.md`
- Prior benchmark notes:
  - `.trellis/tasks/archive/2026-07/07-03-add-workflow-panel-run-input-prompt-v1/research/workflow-benchmark.md`
- Required architecture comparison:
  - `docs/agent-harness-architecture.md`
