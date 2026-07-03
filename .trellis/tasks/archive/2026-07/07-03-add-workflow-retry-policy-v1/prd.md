# Add Workflow Retry Policy V1

## Goal

Add a governed retry policy for workflow `agent_task` steps so AI-generated workflows can recover from transient subagent failures without users manually reconstructing a run. This is the next automation slice after `/workflow auto`, workflow auto-continue, cancellation, and the `/workflows` run panel.

## Requirements

* Workflow step JSON may declare retry policy with `retry.max_attempts`.
* `max_attempts` means total dispatch attempts for that step, including the first attempt.
* Omitted retry policy means `max_attempts=1` and no retry.
* Reject invalid retry policies during workflow validation: non-object retry values, non-integer `max_attempts`, values below 1, and runaway values above a small bounded maximum.
* Run step snapshots must preserve a normalized retry policy and attempt counters so `/workflow show` and `/workflows` can audit retry behavior.
* `attach_workflow_agent_task(...)` must increment the attempt counter whenever it dispatches a task for the step.
* When a workflow is waiting on an `agent_task` and its task reaches a failed/rejected/cancelled terminal state:
  * If attempts remain, prepare the same step for retry, preserve previous task provenance, and redispatch via the existing `bridge_workflow_agent_task(...)` path.
  * If attempts are exhausted, keep current terminal behavior.
* Auto-continue after terminal task ledger writes must reuse the same continue path and therefore inherit retry behavior.
* Retry must not create a second workflow executor, bypass subagent task ledgers, mutate approval/artifact ledgers directly, or run plugin code.
* `workflows.py` must remain pure: deterministic dictionary transforms only, no app/runtime/UI/governance imports, no ledger writes, no subagent dispatch.
* Update backend spec, tests, and policy gates to make the retry contract executable.

## Acceptance Criteria

* A workflow with `agent_task.retry.max_attempts=2` dispatches attempt 1, records a failed task result, then auto/explicit continue dispatches attempt 2 through the existing subagent task pipeline.
* The workflow row produced for retry keeps the same run id, step id, and dependency state, increments the retry attempt counter, and preserves prior task id/status/error in step provenance.
* A second failed attempt with `max_attempts=2` appends a terminal workflow row and does not dispatch a third task.
* A workflow without retry policy preserves existing terminal-failure behavior.
* Invalid retry policy prevents run creation and reports validation issues.
* Existing cancellation semantics remain unchanged: cancelling a waiting retry-capable step does not abort the underlying subagent task and does not retry.
* Tests and policy gates prove retry uses `continue_workflow_run_v0(...)` and `bridge_workflow_agent_task(...)`, not a hidden executor.

## Definition Of Done

* Targeted compile, Ruff, workflow tests, and policy gates pass.
* Full test suite passes.
* Release hygiene, source compileall, diff check, build, wheel smoke, runtime smoke, integration doctor, and `shuheng-check` pass.
* Task commit excludes pre-existing untracked `uv.lock`.
* Final report compares this change to `docs/agent-harness-architecture.md`.

## Out Of Scope

* Timeout timers, wall-clock expiry, SLA policy, or automatic cancellation of long-running tasks.
* Parallel fan-out/fan-in executor changes.
* Retrying workflow `approval`, `condition`, `prompt`, `pause`, `notify`, or `artifact_summary` steps.
* Retrying Secret Vault subagent tasks.
* Killing or aborting existing subagent runtimes.
* Backoff timers, jitter, schedule-based retry, webhook triggers, or A2A/MCP workflow service exposure.

## Technical Approach

Normalize retry policy in `workflows.py` during workflow validation and step snapshot creation. Track fields on each run step:

* `retry.max_attempts`
* `retry.attempt`
* `retry.remaining_attempts`
* `retry.task_attempts`

On each `attach_workflow_agent_task(...)`, increment `retry.attempt`. On failed terminal task result, use a pure helper to decide whether retry is available and reset the step to `blocked` with prior task provenance copied into `retry.task_attempts`. Then app-owned `continue_workflow_run_v0(...)` can call `bridge_workflow_agent_task(...)` exactly as it does for first dispatch.

## Architecture Decision

Retry belongs to the workflow ledger state machine, not a new executor. The Orchestrator remains the only side-effect owner; `workflows.py` only prepares deterministic retry state, while `app.py` delegates dispatch through the existing subagent task pipeline.
