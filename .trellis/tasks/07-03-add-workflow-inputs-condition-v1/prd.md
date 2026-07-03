# Add Workflow Inputs and Condition V1

## Goal

Make Shuheng workflows usable for real branching automation by adding first-class run inputs and a small, safe condition v1 evaluator. The feature should let a manifest-backed workflow accept explicit inputs at run time, validate required/defaulted inputs, and let `condition` steps complete or skip based on those inputs without calling tools, executing plugin code, or weakening the Orchestrator-led ledger model.

## What I Already Know

- `workflows.py` already parses `inputs` into `WorkflowInput` records and copies `inputs` into planned workflow run rows.
- `/workflow run <ref>` and `/workflow continue <run_id>` currently pass `{}` as run inputs from `app.create_workflow_run_v0(...)`.
- `advance_workflow_run_v0(...)` currently treats `condition` as a blocking step and explicitly does not evaluate expressions.
- Existing specs require `workflows.py` to stay pure and forbid app/runtime/UI/governance imports, direct ledger writes, tool calls, provider calls, shell execution, plugin code execution, and Secret Vault access.
- The next workflow architecture gap is making generated workflows choose safe paths from user-provided context, not adding a hidden executor.

## Assumptions

- Condition v1 should be declarative JSON predicates, not free-form Python/JS/shell/string expressions.
- String `expression` fields may remain accepted as non-v1 placeholders, but they should not be executed.
- The runner may mark a false condition as `skipped`, and dependent steps should not run unless their dependencies are completed.
- This slice should not add scheduling, retry/timeout, parallel fan-out/fan-in, output templating, or A2A/MCP workflow services.

## Requirements

- Add a pure input resolution helper that combines workflow input definitions, defaults, and explicit run inputs.
- Required inputs without explicit value or default must reject run creation before appending workflow run rows.
- Unknown explicit inputs should be rejected in v1 to catch typos and prevent silent drift.
- Preserve existing `build_workflow_run_record(..., inputs=...)` callers by defaulting to the old behavior when no workflow inputs are declared.
- Add `/workflow run <ref> key=value ...` support for simple CLI input overrides.
- Add `/workflow run-last <plugin-id>/<workflow-id> key=value ...` support so generated workflows can save-and-run with inputs.
- Store resolved inputs in `workflow_runs.jsonl` planned rows.
- Add condition v1 payload support using a safe JSON predicate object under `condition` or `when`.
- Supported predicate operators must be finite and deterministic: `equals`, `not_equals`, `exists`, `truthy`, `in`, plus `all` / `any` / `not` composition.
- Predicate operands may read only `inputs.<id>` in this slice.
- A true condition marks the condition step `completed` and allows later dependencies to continue.
- A false condition marks the condition step `skipped`, sets a visible reason, and stops runner-v0 progress without side-effect ledgers.
- Unsupported condition shapes or non-v1 string expressions must remain blocked with a clear reason and no side effects.
- `workflows.py` remains pure and side-effect-free.
- `app.py` remains the Orchestrator owner for command parsing, run id/timestamps, state mutation, and ledger appends.

## Acceptance Criteria

- [ ] Safe workflow with required input and provided `ready=true` completes `prompt -> condition -> notify`.
- [ ] Missing required input rejects `/workflow run` with no workflow/task/progress/approval/artifact ledger writes.
- [ ] Unknown input rejects `/workflow run` with no workflow run row.
- [ ] Optional/defaulted input is resolved and persisted in the planned row.
- [ ] False condition marks the condition step skipped, stops later dependent steps, and creates no side-effect ledgers.
- [ ] Unsupported/string condition remains blocked and side-effect-free.
- [ ] `/workflow run-last generated-pack/flow ready=true` saves, reloads, and runs with resolved inputs.
- [ ] Policy gate locks input validation, safe condition v1 evaluation, and `workflows.py` purity.

## Definition of Done

- Unit tests in `tests/test_workflows.py` cover input resolution, app command parsing, run-last inputs, true/false/unsupported conditions, and side-effect invariants.
- `scripts/check_policy_gates.py` asserts the new contracts against the real app harness.
- `.trellis/spec/backend/agent-control-protocol.md` adds a seven-section `Workflow Inputs and Condition V1` scenario.
- Targeted compile/Ruff, workflow tests, policy gates, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.
- Final report compares the change to `docs/agent-harness-architecture.md`.
- Existing untracked `uv.lock` remains excluded.

## Out of Scope

- Free-form expression language execution.
- Python/JavaScript/shell condition execution.
- Reading artifacts, task outputs, files, environment, Secret Vault, or model/tool results inside predicates.
- Dynamic prompt templating from inputs.
- Step output references beyond `inputs.<id>`.
- Branch rewiring, fan-out/fan-in, retries, timeouts, scheduling, and backfill.
- UI form entry for workflow inputs.
- A2A/MCP workflow service exposure.

## Technical Notes

- Likely code paths:
  - `src/ga_tui/workflows.py`
  - `src/ga_tui/app.py`
  - `tests/test_workflows.py`
  - `scripts/check_policy_gates.py`
  - `.trellis/spec/backend/agent-control-protocol.md`
- Current runner contract:
  - `Workflow Runner V0` currently classifies `condition` as blocking and side-effect-free.
  - This task changes that contract only for explicit condition v1 JSON predicates.
- Recommended predicate shapes:
  - `{"condition": {"ref": "inputs.ready", "equals": true}}`
  - `{"when": {"all": [{"ref": "inputs.ready", "equals": true}, {"ref": "inputs.mode", "in": ["fast", "safe"]}]}}`
