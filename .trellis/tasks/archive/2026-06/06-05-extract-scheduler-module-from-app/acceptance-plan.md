# Scheduler Extraction Acceptance Plan

## Purpose

This document is the acceptance contract for extracting scheduler logic from `src/ga_tui/app.py` into a focused scheduler module. The primary goal is not to add scheduler features. The goal is to preserve all current governed scheduler behavior while reducing `app.py` ownership and making future scheduler changes less patch-like.

## Success Standard

The task is acceptable only if all of the following are true:

* Scheduler code has a clear module boundary and no longer depends on the curses UI mega-file for pure scheduling logic.
* All existing schedule entry points still behave the same: `ga-control.v2`, GenericAgent function tools, TUI commands, daemon tick, MCP resources, and gateway registry panels.
* Governed execution is not weakened: agent-task schedules still pass through subagent task dispatch, task ledgers, approval gates, agent mail, traces, checkpoints, and artifact refs.
* Local TUI reminders remain bounded: `tui_action` schedules can beep and write run audit rows without creating subagent tasks.
* Active vocabulary remains current: no retired protocol or retired scheduler concept is added to active prompts, docs, normal runtime branches, or normal behavior tests.

## Scope Map

### Primary Code Surface

* `src/ga_tui/app.py`: current owner of scheduler helpers, TUI composition, command routing, GenericAgent tool handlers, daemon loop, and stateful dispatch.
* `src/ga_tui/scheduler.py`: new focused scheduler module to be added.
* `scripts/check_policy_gates.py`: primary behavior regression script.
* `.trellis/spec/backend/agent-control-protocol.md`: executable scheduler contract.

### Related Surfaces That Must Not Regress

* GenericAgent tool schema injection for `schedule_create` and `schedule_list`.
* GenericAgent handler methods `do_schedule_create` and `do_schedule_list`.
* `ga-control.v2` schedule actions in `apply_tui_controls_from_text()`.
* `/schedules` and `/scheduler [status|tick|run <id>]` TUI commands.
* Main curses loop daemon tick while the TUI is open.
* MCP resources `resource://agent-mail/schedules` and `resource://agent-mail/schedule-runs`.
* Gateway panel data containing `scheduled_task_registry`.
* Runtime provider registry metadata that advertises scheduler dispatch contracts.
* Task ledger, agent mail, approval gate, trace, checkpoint, eval, and artifact code paths reached by scheduled agent work.
* Secret Vault isolation tests and normal-session behavior.
* Current prompt/schema vocabulary and retired-vocabulary quarantine checks.

## Module-Boundary Acceptance

### Required Boundary

`src/ga_tui/scheduler.py` must be the current source of truth for scheduler contracts that do not intrinsically require live TUI state.

The new module may own:

* Schedule row and run row shaping.
* Trigger normalization and parsing.
* Timestamp and interval parsing.
* Cron field matching.
* Active/inactive status checks.
* Due calculation and idempotency key derivation.
* Latest schedule/run index construction.
* `scheduledtask.registry.v1` snapshot shaping.
* `scheduledtask.tick.v1` aggregation.
* `scheduledtask.v1` create/update row generation.
* `scheduledtask.run.v1` starting/final/skip row generation.
* Formatting helpers if they only need scheduler data plus injected truncation behavior.

The new module must not import:

* `curses`
* mutable `State`
* `GenericAgent`, `GenericAgentHandler`, `StepOutcome`, or backend runtime classes
* `src.ga_tui.app`

`app.py` should remain responsible for:

* TUI command routing and `add_system()`.
* Main-loop scheduling cadence.
* Binding GenericAgent tools to live `State`.
* Resolving target subagents.
* Calling `start_subagent_task_structured()`.
* Emitting a real TUI beep or terminal bell.
* Mutating dirty UI state after schedule tool calls.

### Boundary Verification

* `scripts/check_policy_gates.py` must assert that scheduler helpers are defined in or delegated from `ga_tui.scheduler`.
* A direct import test must import `ga_tui.scheduler` without importing curses or constructing `State`.
* A source inspection assertion should fail if `src/ga_tui/scheduler.py` imports `ga_tui.app`, `curses`, or GenericAgent runtime classes.
* `app.py` re-export compatibility should be checked for helper names still used by tests or external callers.

## Scheduler Storage Acceptance

### Schedule Registry

`schedules.jsonl` behavior must remain append-only.

Accepted `scheduledtask.v1` rows must preserve:

* `schema_version:"scheduledtask.v1"`
* `schedule_id`
* `name`
* `status`
* one current trigger source of truth through `cron`, `interval`, `at`, or standardized `trigger`
* `timezone`
* `provider_id`
* `dispatch_contract`
* explicit `execution`
* `target`
* `created_at`
* `updated_at`
* `source`
* last-run metadata appended by `update_schedule_last_run()`

### Schedule Run Audit

`schedule_runs.jsonl` behavior must remain append-only.

Accepted `scheduledtask.run.v1` rows must preserve:

* `schema_version:"scheduledtask.run.v1"`
* `run_id`
* `schedule_id`
* `schedule_name`
* `status`
* `reason`
* `trigger`
* `trigger_kind`
* `due_at`
* `idempotency_key`
* `provider_id`
* `dispatch_contract`
* `source`
* final status fields such as `finished_at`, `target`, `target_name`, `result`, `task_id`, `approval_id`, and `error` when applicable

### Storage Verification

* Creating, updating, enabling, disabling, and deleting schedules must append rows instead of mutating old rows in place.
* A final run row must reuse the same `run_id` as its starting row.
* Latest-record readers must still return the newest row per `schedule_id`.
* Latest-run readers must distinguish latest visible run from latest dispatch attempt.
* `latest_schedule_attempt_runs_by_schedule_id()` must only anchor interval schedules on real attempt statuses: `starting`, `dispatched`, `queued`, `approval_required`, `failed`, and `rejected`.
* Observation-only statuses such as `duplicate`, `skipped`, and `invalid` must not move the next interval due time.

## Trigger And Due Calculation Acceptance

### Supported Current Trigger Schema

The scheduler must keep supporting:

* `at`
* `interval`
* `cron`
* standardized `trigger` strings prefixed as `at:`, `interval:`, or `cron:`

### `at` Acceptance

* ISO timestamps, numeric epoch strings, `Z`, compact timezone offsets, space-separated datetime strings, and date-only strings remain accepted where the current parser accepts them.
* A due one-shot schedule gets idempotency key `<schedule_id>:at:<due_epoch>`.
* Once that idempotency key exists, later ticks report duplicate and do not dispatch again.
* Future `at` schedules remain pending.
* Invalid `at` values produce invalid status and an audit row when tick policy records invalid schedules.

### `interval` Acceptance

* Seconds, minutes, hours, and days remain accepted with current suffixes such as `30s`, `1m`, `2h`, and `1d`.
* Current string normalization for `interval` / `every` prefixes remains compatible.
* Next due time is anchored to the latest real dispatch attempt row if one exists.
* If no attempt row exists, next due time falls back to `created_at`, then `updated_at`, then current time, matching existing behavior.
* Duplicate/skipped/invalid observation rows do not push the next due time forward.
* Duplicate interval idempotency keys prevent repeat dispatch for the same due slot.

### `cron` Acceptance

* Five-field cron expressions remain supported.
* `*`, comma lists, ranges, steps, and weekday `7 -> 0` normalization remain compatible.
* Matching is evaluated in local time exactly as current code does.
* Idempotency key remains minute-scoped with `<schedule_id>:cron:<YYYYMMDDHHMM>`.
* Non-matching cron schedules remain pending.
* Malformed cron schedules become invalid with an audit row when applicable.

### Unsupported Trigger Acceptance

* Unsupported or unprefixed free-form trigger text remains unsupported.
* The active runtime must not add special branches for retired trigger names.
* Generic schema-boundary behavior should handle schema-outside fields.

## Control Action Acceptance

`ga-control.v2` schedule actions must remain behavior-compatible.

### `schedule.create`

* Requires a current trigger field.
* Requires valid `execution.mode`.
* Writes a `scheduledtask.v1` row through the same registration path used by tools.
* `execution.mode:"tui_action"` with `action:"beep"` writes `dispatch_contract:"tui_action.v1"`.
* `execution.mode:"agent_task"` writes `dispatch_contract:"agenttask.v2"`.
* Agent-task creation requires `work_order.objective` and a structured routing target.
* Missing or invalid execution returns the same user-facing failure category as current behavior.

### `schedule.update`

* Requires an existing target schedule.
* Preserves existing execution when no new `execution` object is provided.
* Updates trigger fields so there is one current trigger source of truth.
* Revalidates execution after updates.
* Preserves original `created_at`.
* Appends a new schedule row with fresh `updated_at`.

### `schedule.enable`, `schedule.disable`, `schedule.delete`

* Require an existing target schedule.
* Append a new row with status `enabled`, `disabled`, or `deleted`.
* Disabled, deleted, cancelled, and canceled schedules are not dispatched.

### Control Verification

* A `ga-control.v2` batch can create, update, disable, enable, and delete schedules.
* Missing trigger, missing schedule target, unknown schedule, missing execution mode, missing work-order objective, and missing routing target remain covered.
* Existing control-result formatting and `Agent 控制结果` messages remain compatible.

## GenericAgent Tool Acceptance

### `schedule_create`

* Tool schema remains installed exactly once after repeated runtime installation.
* Handler method `do_schedule_create` remains present.
* Missing bound TUI state returns `schema_version:"ga-tui.tool.v1"` with `status:"error"`.
* Successful calls invoke the same schedule registration path as `ga-control.v2`.
* Response returns the appended schedule row and current `scheduledtask.registry.v1` snapshot.
* The tool remains state-changing and does not pretend to be read-only.

### `schedule_list`

* Tool schema remains installed exactly once.
* Handler method `do_schedule_list` remains present.
* Response returns `schema_version:"ga-tui.tool.v1"` and the TUI registry snapshot.
* `include_inactive:false` hides disabled, deleted, cancelled, and canceled rows.
* `limit` bounding remains compatible.
* The tool does not inspect, modify, or start any external scheduler files.

## TUI Command Acceptance

### `/schedules`

* Opens/reports the Scheduled Tasks panel text.
* Shows registry status, active/total job count, schedule store path, run count, run audit path, dispatch contract, due state, and last run state.

### `/scheduler status`

* Reports scheduler state using the same registry formatter.

### `/scheduler tick`

* Evaluates due jobs immediately.
* Records manual skip/invalid outcomes when current behavior does.
* Returns formatted tick counts and recent run summaries.

### `/scheduler run <schedule_id>`

* Force-runs only an existing enabled schedule.
* Reports unknown schedule ids without dispatch.
* Uses a manual idempotency key that does not collide with daemon ticks.

### Command Verification

* Command text and behavior remain stable enough for existing user workflows.
* Formatter extraction does not lose Chinese user-facing status messages where they currently exist.

## Daemon Tick Acceptance

* Main loop still starts the first scheduler tick after `min(5.0, SCHEDULER_TICK_SECONDS)`.
* `GA_TUI_SCHEDULER_TICK_SECONDS` still has a minimum of 5 seconds and default 30 seconds.
* Daemon tick runs only while the TUI process is open.
* Daemon tick adds a persisted system message only when runs/due/failed counters indicate useful output, matching current behavior.
* The extraction does not introduce a background daemon or external scheduler dependency.

## TUI Action Schedule Acceptance

### Beep Path

* `execution.mode:"tui_action"` plus `action:"beep"` emits one bounded local beep action.
* A starting run row is written before execution.
* A final completed run row is written with `result:"beep emitted"` when successful.
* A final failed run row is written with `error` when beep emission fails.
* Completed TUI beep runs do not create task-ledger rows and do not include `task_id`.
* Unsupported TUI actions write failed schedule-run rows and do not dispatch agent work.

### Dependency Boundary

* If beep emission remains in `app.py`, scheduler dispatch must use an explicit callback instead of importing curses.
* Tests may monkeypatch the beep callback or `emit_tui_beep()` compatibility name to verify one beep call.

## Agent-Task Schedule Acceptance

### Dispatch Contract

* `execution.mode:"agent_task"` schedules convert into `agenttask.v2` `delegate.create` controls.
* The conversion preserves `routing`, `work_order`, `capability_contract`, `context_contract`, `output_contract`, `task_title`, `schedule_id`, and `provider_id`.
* Explicit `routing.selected_agent` or structured target selector remains required.
* The scheduler must not pick workers by natural-language similarity.
* The scheduler must not call backend `put_task()` directly.

### Governed Execution

* Due schedules resolve the target subagent through the TUI state.
* Dispatch enters `start_subagent_task_structured()` or an equivalent app-layer wrapper.
* Policy gates remain active.
* Single-writer/task-ledger semantics remain active.
* Worker-visible prompts still hide internal envelope fields where current tests require it.
* Actual backend prompts still include the internal `agenttask.v2` envelope where current tests require it.
* Final schedule-run status comes from structured dispatch results: `status`, `message`, `task_id`, `approval_id`, and `error`.
* Localized UI text must not be parsed as control flow.

### Expected Final Statuses

The scheduler must continue to handle:

* `dispatched`
* `queued`
* `approval_required`
* `failed`
* `rejected`
* `completed` for TUI action completion
* `duplicate`
* `skipped`
* `invalid`

## Approval And Risk Acceptance

* Risky scheduled work must queue or require approval according to existing policy gates.
* A risky scheduled run must write a final run row with `status:"approval_required"`.
* The final run row must include the matching `task_id` and `approval_id`.
* The corresponding task ledger row must also show `status:"approval_required"` and matching approval metadata.
* Approval payload bodies remain protected by existing approval-list redaction behavior.

## Failure And Invalid Schedule Acceptance

The scheduler must write clear audit rows and avoid dispatch for:

* Missing `schedule_id`.
* Unsupported trigger.
* Malformed cron.
* Invalid `at` timestamp.
* Invalid interval.
* Disabled/deleted/cancelled/canceled schedule.
* Duplicate one-shot, interval, or cron slot.
* Missing `execution.mode`.
* Missing `work_order.objective`.
* Missing structured routing target.
* Unsupported TUI action.
* Target subagent not found.
* Exception during task dispatch.

## Gateway, MCP, And Runtime Registry Acceptance

* MCP registry still includes `resource://agent-mail/schedules`.
* MCP registry still includes `resource://agent-mail/schedule-runs`.
* Gateway registry still exposes internal mail paths for `schedules` and `schedule_runs`.
* Gateway panel items still include `scheduled_task_registry`.
* `scheduled_task_registry` still reports `schema_version:"scheduledtask.registry.v1"`, owner, paths, job counts, run counts, dispatch contract, and capabilities.
* Runtime provider registry text still reports scheduler dispatch metadata.
* A2A/MCP compatibility is not weakened by scheduler extraction.

## Prompt And Ontology Acceptance

* Active schedule guidance remains positive and current: current schema fields are `cron`, `interval`, `at`, and standardized prefixed `trigger`.
* Active prompt guidance must not add retired scheduler concepts as "do not use X" branches.
* Active runtime, user-facing errors, normal tests, docs, and comments must not introduce retired control vocabulary as active ontology.
* If retired vocabulary must be protected, it stays isolated in quarantine/absence tests rather than behavior-tested as normal protocol behavior.
* Existing current-control absence checks must continue to pass.

## Secret Vault Non-Regression

Scheduler extraction must not change:

* Secret Vault unlock/lock behavior.
* Secret session sidebar behavior.
* Secret subagent persistence and encryption boundaries.
* Normal-command isolation while Secret Vault is active.
* Approval behavior for secret-like work.
* Memory candidate and subagent memory behavior in Secret and non-Secret modes.

Existing Secret Vault checks in `scripts/check_policy_gates.py` must pass unchanged unless the scheduler extraction reveals a real bug that is then documented.

## Runtime Provider Non-Regression

Scheduler extraction must not change:

* Runtime provider registry defaults.
* GenericAgent provider registration.
* Model routing metadata.
* Tool schema installation idempotency.
* `schedule_create` provider selection from explicit `provider_id` or registry default.
* Runtime/provider fields in schedule rows and registry snapshots.

## Session And UI Non-Regression

Scheduler extraction must not change:

* Normal session history load/restore behavior.
* Temporary session behavior.
* Sidebar registry behavior.
* Token usage persistence.
* Existing command completion entries for `/schedules` and `/scheduler`.
* Existing render/panel data structures not related to scheduler.

## Architecture Baseline Acceptance

Before final reporting, compare the implementation with `docs/agent-harness-architecture.md`.

The change should move closer to the baseline by:

* Strengthening the orchestrator/control-plane boundary.
* Keeping scheduled agent work as governed `agenttask.v2` delegation.
* Preserving shared task/progress ledgers.
* Preserving artifact-reference expectations.
* Preserving single-writer and approval-gate enforcement.
* Preserving auditable schedule-run communication.
* Preserving A2A/MCP gateway visibility.
* Reducing `app.py` patchification risk by extracting a coherent module.

Any newly discovered gaps must be called out explicitly, especially around:

* Scheduler-level concurrency policy for long-running recurring agent tasks.
* Whether scheduler execution should continue only while TUI is open or require a future daemon.
* Further split candidates such as task ledger, policy gates, subagents, and gateway modules.

## Test Plan

### Required Automated Verification

Run all commands from the repository root:

```bash
python3 -m py_compile src/ga_tui/app.py src/ga_tui/scheduler.py src/ga_tui/control_protocol.py scripts/check_policy_gates.py
python3 scripts/check_policy_gates.py
python3 -m compileall -q src scripts
git diff --check
ga-tui-check --root /home/vimalinx/Programs/GenericAgent
```

If the sibling GenericAgent checkout is missing, record that `ga-tui-check` could not be run and why.

### Required Targeted Test Additions Or Updates

`scripts/check_policy_gates.py` should directly verify:

* `ga_tui.scheduler` imports cleanly without importing curses or `ga_tui.app`.
* `app.py` re-exports or delegates scheduler helper names required by existing tests.
* Schedule creation through `ga-control.v2` still records `dispatch_contract:"agenttask.v2"` for agent-task execution.
* `schedule_create` tool still records through the shared `scheduledtask.v1` path.
* TUI beep schedule writes starting and completed run rows and no task ledger row.
* Agent-task schedule writes starting and dispatched/queued/approval-required run rows and creates task ledger evidence.
* Risky scheduled work records `approval_required` with matching task and approval ids.
* Duplicate scheduler ticks do not dispatch a second task for the same idempotency key.
* Observation-only run rows do not move interval anchors.
* Disabled schedules skip and invalid schedules write audit rows without dispatch.
* MCP/gateway registries include schedules and schedule-runs paths.
* Active prompt/schema vocabulary stays current without exact prose locking beyond necessary current-schema tokens and absence invariants.

### Manual/Scenario Verification

If a short interactive smoke is feasible after automated tests:

* Start the TUI and create a short `tui_action` beep schedule for a near-future `at` time.
* Confirm it fires only once while TUI is open.
* Confirm `/schedules` shows the schedule and last completed run.
* Confirm `/scheduler status` reports current registry state.
* Confirm `/scheduler run <id>` force-runs an enabled schedule and reports a run.
* Confirm a disabled schedule does not dispatch.

Manual smoke is optional if automated policy gates already cover the same paths, but any skipped manual smoke should be reported.

## Diff Review Checklist

Before final acceptance, inspect the diff for:

* No broad unrelated edits.
* No `app.py` local duplicate definitions of moved scheduler helpers.
* No circular imports between `app.py` and `scheduler.py`.
* No scheduler module dependency on UI, mutable `State`, curses, or GenericAgent runtime classes.
* No new active prompt mentions of retired concepts.
* No behavior changes to Secret Vault, runtime registry, session registry, or gateway code unless explicitly justified.
* No destructive filesystem operations.
* No external scheduler integration.
* No hidden status inference from localized UI text.

## Rollback Plan

If extraction causes regressions:

* Revert only the scheduler extraction changes for this task, preserving unrelated user or prior task changes.
* Restore `app.py` scheduler helper definitions from the pre-task state if needed.
* Remove `src/ga_tui/scheduler.py` only if no longer referenced.
* Keep any failing evidence in the task notes before retrying with a smaller extraction slice.
* Do not use destructive git commands without explicit user approval.

## Completion Evidence Required

The final report for the implementation phase must include:

* Files changed at a high level.
* Verification commands run and whether each passed.
* Whether the change moved closer to or farther from `docs/agent-harness-architecture.md`.
* Any residual risks or follow-up tasks, especially daemon lifetime and concurrency policy.
* Confirmation that no implementation began before this acceptance plan was written.
