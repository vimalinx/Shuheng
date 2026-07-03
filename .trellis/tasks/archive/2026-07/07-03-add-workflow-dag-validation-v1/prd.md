# Add Workflow DAG Validation V1

## Goal

Make Shuheng workflow definitions enforce the basic DAG invariant before a run row can be created. Workflow `depends_on` must describe a directed acyclic graph: no self-dependency, no dependency cycles, no duplicate dependency entries, and no missing dependencies.

## What I Already Know

- Current workflow parsing validates step ids, duplicate step ids, supported step types, and missing dependencies in `src/ga_tui/workflows.py`.
- Current parsing does not reject self-dependencies or multi-step cycles.
- Workflow runner v0 advances pending steps by scanning current step order and checking whether dependencies are completed.
- Future workflow features such as fan-out/fan-in, retries, recovery, and scheduling depend on the workflow graph being valid before execution starts.
- `workflows.py` must remain pure and side-effect-free; `app.py` remains the Orchestrator owner for command parsing, ledger writes, bridges, and runtime effects.

## Assumptions

- DAG validation belongs at workflow definition load time, not at `/workflow run` execution time.
- A cyclic workflow should be treated as an invalid workflow definition and rejected before any workflow run row is appended.
- V1 should report clear validation issues, but does not need to auto-rewrite or reorder workflow steps.

## Requirements

- Detect a step that depends on itself.
- Detect duplicate dependency ids inside a single step's `depends_on` / `after` list.
- Detect direct and transitive dependency cycles across workflow steps.
- Keep existing missing dependency validation.
- Keep valid DAGs accepted, including fan-in-shaped dependency declarations, even though runner v0 remains sequential.
- Keep `workflows.py` pure: no app/runtime/UI/governance imports, no ledger writes, no dispatch, no tools/providers, no subprocess.
- Do not change `/workflow run`, approval bridge, agent-task bridge, auto-continue, generated draft, inputs, condition, or upstream artifact context semantics except that invalid cyclic definitions are rejected earlier.

## Acceptance Criteria

- [ ] A workflow with `{"id":"plan","depends_on":["plan"]}` reports a visible self-dependency validation issue and app `/workflow run` appends no workflow rows.
- [ ] A workflow with `a -> b -> a` reports a visible dependency cycle validation issue and app `/workflow run` appends no workflow rows.
- [ ] A workflow with duplicate dependency entries on one step reports a visible duplicate-dependency validation issue.
- [ ] A valid fan-in workflow such as `collect_a`, `collect_b`, then `review depends_on ["collect_a","collect_b"]` still loads with no issues.
- [ ] Existing missing dependency errors remain intact.
- [ ] Tests and policy gates assert that cyclic DAGs do not create workflow run rows or side-effect ledgers.

## Definition of Done

- Unit tests in `tests/test_workflows.py` cover self-dependency, direct/transitive cycles, duplicate dependencies, and valid fan-in.
- `scripts/check_policy_gates.py` locks the no-run-row/no-side-effect behavior for invalid cyclic workflow definitions.
- `.trellis/spec/backend/agent-control-protocol.md` gains a seven-section scenario for Workflow DAG Validation V1.
- Targeted compile/Ruff, workflow tests, policy gates, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.
- Final report compares the change to `docs/agent-harness-architecture.md`.
- Existing untracked `uv.lock` remains excluded.

## Out of Scope

- Topological reordering of workflow steps.
- Parallel fan-out/fan-in execution.
- Retry, timeout, cancellation, scheduling, webhooks, checkpoint/replay, A2A/MCP workflow service exposure.
- UI workflow builder changes.
- Reading artifact files, task bodies, model outputs, environment variables, Secret Vault, or tools.

## Technical Notes

- Likely code paths:
  - `src/ga_tui/workflows.py`
  - `tests/test_workflows.py`
  - `scripts/check_policy_gates.py`
  - `.trellis/spec/backend/agent-control-protocol.md`
- Current parser entry point:
  - `workflows._parse_steps(...)`
- Current loader path:
  - `workflow_load_result_from_payload(...)`
  - `workflow_load_result_for_ref(...)`
- Core invariant: workflow definitions must be DAG-valid before any run ledger row can be created.
