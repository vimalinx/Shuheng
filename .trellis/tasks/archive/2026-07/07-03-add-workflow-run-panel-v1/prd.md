# Add Workflow Run Panel V1

## Goal

Turn the existing `/workflows` read-only registry panel into a workflow control center that makes current workflow runs visible and operable from the TUI. Users should be able to enter `/workflows`, see both workflow definitions and latest workflow run states, inspect a run's steps/approval/task/artifact references, and use explicit keys to continue/resume or cancel a selected run through the existing governed command helpers.

## Requirements

* Keep `/workflows` as the entry point; do not add a separate top-level command unless required by existing panel plumbing.
* The panel must include workflow definition rows and workflow run rows.
* Run rows must show latest run id, status, workflow ref, step progress, last update timestamp, and stop reason when present.
* Run row detail must show the same audit-critical fields as `/workflow show <run_id>`: history rows, status, workflow ref, timestamps, execution counters, approval metadata, per-step status, task ids, approval ids, agent ids, artifact refs, and errors.
* Selecting a workflow definition should remain read-only, with existing info/dry-run command hints.
* Selecting a workflow run should expose key hints for continue/resume and cancel.
* Continue action must call existing `continue_workflow_run_v0(run_id, state=state)`.
* Cancel action must call existing `cancel_workflow_run_v0(run_id, reason=...)` with a panel-owned generic reason.
* Refresh must reload plugin registry and workflow run ledgers without mutating execution state.
* The panel must not dispatch subagents, create approvals, append workflow rows, or mutate task/progress/approval/artifact ledgers except through the explicit continue/cancel actions and their existing governed helpers.
* `workflows.py` should stay pure. If new projection/formatting helpers are needed, they may live in `workflows.py` only if they remain deterministic and side-effect-free.
* Update backend spec, tests, and policy gates to make the panel contract executable.

## Acceptance Criteria

* [ ] `/workflows` still opens the existing panel browser route.
* [ ] `workflow_panel_items()` includes definition rows and latest run rows.
* [ ] Run rows have stable `PanelItem.payload` with `item_type="workflow_run"`, `run_id`, `workflow_ref`, `status`, and `history_rows`.
* [ ] Run detail includes `Workflow run: <run_id>`, history count, step statuses, task/approval ids, and artifact refs when present.
* [ ] Pressing continue/resume on a selected run uses `continue_workflow_run_v0(...)` and refreshes panel state.
* [ ] Pressing cancel on a selected run uses `cancel_workflow_run_v0(...)`, appends at most one cancelled workflow row through the existing helper, and refreshes panel state.
* [ ] Pressing action keys on definition/empty/issue rows is a visible no-op.
* [ ] Tests and policy gates prove the panel does not create a second workflow executor or bypass existing helpers.

## Definition Of Done

* Targeted compile, Ruff, workflow tests, and policy gates pass.
* Full test suite passes.
* Release hygiene, source compileall, diff check, build, wheel smoke, runtime smoke, integration doctor, and `shuheng-check` pass.
* Task commit excludes pre-existing untracked `uv.lock`.
* Final report compares this change to `docs/agent-harness-architecture.md`.

## Technical Approach

Add a small projection layer that builds `PanelItem` rows from `workflow_run_records()` and existing `format_workflow_run_detail(...)`. Merge those rows into `workflow_panel_items()` after definition rows. In `open_harness_panel(...)`, add workflow-panel-specific key handling for selected run rows:

* `c` / Enter: continue selected run via `continue_workflow_run_v0(...)`.
* `x`: cancel selected run via `cancel_workflow_run_v0(..., reason="cancelled from workflow panel")`.

The panel should refresh after actions and display the returned helper message in the popup footer/status line. It should not interpret workflow state itself beyond selecting the run id from panel payload.

## Decision (ADR-lite)

**Context**: Workflow runtime capability has outgrown command-only UX. Users can now generate, run, continue, approve, auto-continue, and cancel workflows, but the current `/workflows` panel only shows definitions.

**Decision**: Extend the existing `/workflows` panel instead of creating a parallel UI. Runs are shown as read-model rows built from the append-only workflow ledger. Actions delegate to existing helpers.

**Consequences**: This gives users a visible control surface while preserving the current strong Orchestrator design. The trade-off is that this slice remains keyboard/text-panel based; a richer graph visualization, retry/timeout controls, scheduling, and A2A/MCP service exposure stay out of scope.

## Out Of Scope

* Graph visualization, node canvas, or new curses layout framework.
* Retry, timeout, scheduling, trigger, webhook, or SLA policy.
* Parallel/fan-out/fan-in executor changes.
* Editing workflow JSON from the panel.
* Prompting for custom cancel reason in the panel.
* Auto-approval, Secret Vault workflow execution, direct tool execution, or plugin code execution.
* A2A/MCP workflow service exposure.

## Technical Notes

* Relevant spec: `.trellis/spec/backend/agent-control-protocol.md`.
* Relevant architecture baseline: `docs/agent-harness-architecture.md`.
* Existing UI code: `workflow_panel_items(...)`, `open_harness_panel(...)`, `draw_panel_browser(...)`.
* Existing run helpers: `workflow_run_records(...)`, `latest_workflow_run_records(...)`, `format_workflow_runs(...)`, `format_workflow_run_detail(...)`, `continue_workflow_run_v0(...)`, `cancel_workflow_run_v0(...)`.
