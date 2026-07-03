# Add Workflow Step Output Artifact Context V1

## Goal

Make Shuheng workflows more useful for multi-step automation by letting later workflow `agent_task` steps receive a small, auditable context block that references completed upstream step outputs. The first version should pass artifact refs and task refs forward by reference, not by copying artifact contents or executing a template language.

## What I Already Know

- `apply_workflow_agent_task_result(...)` already copies a completed subagent task row's `artifact_refs` into the workflow step and top-level workflow run row.
- `workflow_agent_task_prompt(...)` currently returns only the step prompt, step description, or workflow description.
- `bridge_workflow_agent_task(...)` is the only app-owned path that dispatches workflow `agent_task` steps to `start_subagent_task_structured(...)`.
- `workflows.py` must stay pure and side-effect-free; `app.py` remains the Orchestrator owner for state, command parsing, registry refresh, and ledger appends.
- The architecture baseline prefers artifact references over message copying, shared ledgers, single-writer behavior, and explicit bridge protocols.

## Assumptions

- Later steps need provenance-rich refs more urgently than raw output text.
- V1 should not read artifact files because that would expand workflow execution into file/content hydration and Secret Vault boundary questions.
- V1 should not implement arbitrary prompt templating. It can append a deterministic context section to the prompt before dispatch.
- Only completed upstream steps should contribute context. Pending, blocked, failed, rejected, or skipped steps should not.

## Requirements

- Add a pure helper that collects completed upstream workflow step context from a run row and target step.
- Context must include only reference data: completed upstream step ids, task ids, artifact refs, and optionally source agent ids.
- Dependency scoping should prefer the target step's declared `depends_on`; if no dependencies are declared, the helper may use completed prior steps in run order.
- The helper must dedupe refs and preserve stable order.
- Add an app-owned prompt wrapper for workflow `agent_task` dispatch that appends a bounded context block to the base prompt when upstream refs exist.
- The context block must be clearly labeled as reference-only workflow context.
- The context block must not read artifact contents, task output bodies, files, environment variables, Secret Vault, model outputs, or tools.
- Existing workflows with no upstream refs must preserve the current prompt string exactly.
- Existing approval, condition, run-last, auto-continue, and workflow inspection behavior must remain unchanged.
- The workflow run row remains the source of truth; no new ledger type is introduced.

## Acceptance Criteria

- [ ] A workflow `agent_task` that depends on an earlier completed `agent_task` receives a prompt containing the upstream step id, task id, and artifact refs.
- [ ] If the later step has explicit `depends_on`, unrelated completed prior steps are not included.
- [ ] If the later step has no explicit `depends_on`, completed prior step refs are included in run order.
- [ ] Duplicate artifact refs are deduped while preserving first-seen order.
- [ ] Missing upstream refs do not add an empty context block and do not change the base prompt.
- [ ] The context helper is pure and does not import app/runtime/UI/governance owners.
- [ ] Policy gates assert the context injection path and the no-read/no-side-effect boundary.

## Definition of Done

- Unit tests in `tests/test_workflows.py` cover pure context collection, prompt context formatting, scoped dependency behavior, and bridge dispatch prompt behavior.
- `scripts/check_policy_gates.py` locks the workflow output context contract against the real app harness.
- `.trellis/spec/backend/agent-control-protocol.md` gains a seven-section `Workflow Step Output Artifact Context V1` scenario.
- Targeted compile/Ruff, workflow tests, policy gates, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.
- Final report compares the change to `docs/agent-harness-architecture.md`.
- Existing untracked `uv.lock` remains excluded.

## Out of Scope

- Reading artifact file contents.
- Passing raw subagent transcripts or model response bodies.
- Free-form prompt templating, expression evaluation, or variable interpolation.
- Step output references beyond artifact/task/agent ids.
- Fan-out/fan-in, retries, timeout policies, scheduling, webhooks, and A2A/MCP workflow service exposure.
- UI workflow builder changes.

## Technical Notes

- Likely code paths:
  - `src/ga_tui/workflows.py`
  - `src/ga_tui/app.py`
  - `tests/test_workflows.py`
  - `scripts/check_policy_gates.py`
  - `.trellis/spec/backend/agent-control-protocol.md`
- Current bridge path:
  - `app.workflow_agent_task_prompt(...)`
  - `app.bridge_workflow_agent_task(...)`
  - `workflows.apply_workflow_agent_task_result(...)`
- The core invariant is reference passing, not content hydration.
