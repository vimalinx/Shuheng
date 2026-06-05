# Extract Scheduler Module From App.py

## Goal

Extract the TUI-owned scheduler logic from the monolithic `src/ga_tui/app.py` into a focused scheduler module while preserving the current governed scheduling behavior. The task should make scheduler changes easier to reason about without weakening `ga-control.v2`, task-ledger dispatch, approval gates, schedule-run audit rows, TUI commands, MCP/gateway registry data, or daemon tick behavior.

## What I Already Know

* `src/ga_tui/app.py` currently owns UI, state, Secret Vault, subagents, task ledgers, gateway registries, runtime provider metadata, prompt injection, and scheduler behavior.
* Scheduler-related definitions are concentrated around `app.py` line 5817 through 6645, including schedule registry reads/writes, trigger parsing, due calculation, run audit rows, TUI beep dispatch, agent-task dispatch, tick aggregation, and text formatting.
* Scheduler behavior is already documented in `.trellis/spec/backend/agent-control-protocol.md` under `TUI Governed Schedule Tools` and `Scheduled Task Scheduler`.
* Schedule creation can enter through both `ga-control.v2` actions and GenericAgent function tools `schedule_create` / `schedule_list`.
* Scheduler execution has two current modes: `execution.mode:"tui_action"` for bounded local TUI actions such as `beep`, and `execution.mode:"agent_task"` for governed `agenttask.v2` delegation.
* Agent-task schedule execution must continue to enter `start_subagent_task_structured()` / `start_subagent_task()` so task ledger rows, mail, approvals, checkpoints, traces, and artifact refs remain active.
* Current tests in `scripts/check_policy_gates.py` cover schedule tools, control actions, scheduler tick, duplicate idempotency, interval anchoring, TUI beep, agent-task dispatch, approval-required dispatch, invalid schedules, MCP/gateway registry paths, and formatted registry output.
* The previous extraction task moved current control-protocol helpers into `src/ga_tui/control_protocol.py`; this scheduler task should follow the same "current source of truth, no broad behavior rewrite" approach.

## Assumptions

* This task is a scheduler module extraction, not a full `app.py` decomposition.
* Behavior should remain compatible unless the existing code already violates the scheduler spec and a narrow correction is required to preserve governed scheduling.
* `src/ga_tui/scheduler.py` should not import curses, mutable `State`, GenericAgent runtime classes, or `src.ga_tui.app`.
* Stateful execution dependencies may stay in `app.py` initially or be passed into the scheduler module through explicit callbacks/dependency objects.
* The extraction should avoid prompt rewrites except where necessary to keep current schedule vocabulary and retired-vocabulary absence invariants intact.
* The task should not introduce external scheduler files, background daemons, or legacy GenericAgent scheduler behavior.

## Requirements

* Add a focused scheduler module, tentatively `src/ga_tui/scheduler.py`, for current scheduler contracts that can be owned independently from curses UI code.
* Move pure scheduler logic out of `app.py` where feasible: registry row shaping, trigger parsing, due calculation, idempotency helpers, schedule row construction/update helpers, run-row shaping, tick aggregation, and text formatting helpers.
* Keep `app.py` as the composition layer for mutable TUI state, UI commands, daemon-loop integration, GenericAgent tool handlers, subagent resolution, TUI beep emission, and task dispatch unless those dependencies are explicitly injected.
* Preserve public compatibility for existing callers/tests by importing or re-exporting the scheduler helpers that currently appear under `ga_tui.app`.
* Preserve JSONL append-only semantics for `schedules.jsonl` and `schedule_runs.jsonl`.
* Preserve `ga-control.v2` schedule actions: `schedule.create`, `schedule.update`, `schedule.enable`, `schedule.disable`, and `schedule.delete`.
* Preserve tool behavior for `schedule_create` and `schedule_list`, including shared registration path, `scheduledtask.v1` rows, `scheduledtask.registry.v1` snapshots, inactive filtering, and tool response schemas.
* Preserve `/schedules` and `/scheduler [status|tick|run <id>]` command behavior.
* Preserve daemon tick behavior while TUI is open, including the `GA_TUI_SCHEDULER_TICK_SECONDS` minimum/default behavior.
* Preserve dispatch semantics for TUI beep schedules and agent-task schedules, including approval-required structured dispatch status.
* Preserve MCP/gateway registry data for `resource://agent-mail/schedules` and `resource://agent-mail/schedule-runs`.
* Add or update tests so the new module boundary is directly checked, not only indirectly covered through `app.py`.

## Acceptance Criteria

* [x] `src/ga_tui/scheduler.py` exists and owns the extracted scheduler source of truth without importing curses, GenericAgent runtime classes, mutable `State`, or `ga_tui.app`.
* [x] `src/ga_tui/app.py` no longer locally defines the moved pure scheduler helpers, but existing tests/callers can still access required helper names through imports or re-exports.
* [x] Existing schedule behavior remains compatible across control actions, tool calls, TUI commands, daemon ticks, MCP/gateway registry data, and policy-gate tests.
* [x] `scheduledtask.v1` and `scheduledtask.run.v1` JSONL append-only semantics remain unchanged.
* [x] Trigger parsing and due calculation still cover `at`, `interval`, `cron`, prefixed `trigger`, unsupported triggers, duplicate keys, and interval anchoring by real dispatch attempts only.
* [x] TUI beep schedules still create schedule-run audit rows and no task-ledger rows.
* [x] Agent-task schedules still dispatch through the governed subagent/task path and preserve task ledger, mail, approval, trace, checkpoint, and artifact behavior.
* [x] Risky scheduled work still records `approval_required` with matching `task_id` and `approval_id` from structured dispatch results.
* [x] Active prompt/schema vocabulary stays current and does not introduce retired scheduler or retired control vocabulary into active runtime guidance.
* [x] Secret Vault, runtime provider registry, gateway panels, baseline reporting, and normal session behavior are not regressed.
* [x] The implementation is compared with `docs/agent-harness-architecture.md` before final reporting.

## Acceptance Plan

The detailed acceptance and verification plan is captured in [`acceptance-plan.md`](acceptance-plan.md). Future implementation and checking should use that file as the contract for what must be verified before this task can be called complete.

## Definition Of Done

* Requirements and acceptance plan are confirmed before implementation starts.
* Relevant Trellis specs are loaded before code edits.
* The extraction is behavior-preserving except for narrow spec-aligned fixes explicitly called out in the implementation notes.
* Project verification passes: `py_compile`, `compileall`, `scripts/check_policy_gates.py`, `ga-tui-check` when the sibling GenericAgent checkout exists, and `git diff --check`.
* Architecture baseline comparison is reported.
* Work is committed only after verification and user-approved commit grouping, then the task can be archived and journaled.

## Out Of Scope

* Rewriting the schedule protocol or changing `scheduledtask.v1` / `scheduledtask.run.v1` schemas.
* Adding an external scheduler daemon that runs after the TUI is closed.
* Reintroducing or documenting retired schedule/control vocabulary as active behavior.
* Moving Secret Vault, subagent lifecycle, task-ledger storage, approvals, runtime provider adapters, or gateway server code out of `app.py`.
* Redesigning the GenericAgent tool patching layer.
* Splitting all UI rendering or `State` into separate modules in this task.

## Technical Notes

* Candidate extraction targets include `scheduled_task_registry`, `latest_schedule_records`, `append_schedule_record`, `latest_schedule_run_records`, `latest_schedule_runs_by_schedule_id`, `latest_schedule_attempt_runs_by_schedule_id`, `schedule_run_idempotency_keys`, `append_schedule_run`, `schedule_record_trigger`, `parse_schedule_timestamp`, `parse_schedule_interval_seconds`, `split_schedule_trigger`, `cron_field_matches`, `cron_matches_now`, `schedule_active`, `schedule_due_info`, `schedule_trigger_from_control`, `schedule_execution_from_control`, `schedule_execution_target`, `schedule_execution_error`, `schedule_record_from_control`, `schedule_record_updates_from_control`, `schedule_agenttask_control`, `update_schedule_last_run`, `append_schedule_skip_run`, `dispatch_schedule_tui_action` if emitted-beep is injected, `dispatch_schedule_run` if task dispatch is injected, `scheduler_tick`, `format_scheduler_tick_result`, and `format_scheduled_task_registry`.
* Likely app-layer dependencies include `State`, `mark_dirty`, `add_system`, `resolve_subagent`, `start_subagent_task_structured`, `SubagentDispatchResult`, `emit_tui_beep`, `agent_runtime_registry`, `execution_control_from_v2`, `tui_query_json_safe`, `truncate_cells`, `read_jsonl`, `append_jsonl`, `now_iso`, and path constants.
* If moving JSONL helpers would cause broad churn, the scheduler module may use explicit store/dependency callbacks instead of importing from `app.py`.
* The strongest boundary is: scheduler module decides schedule math and row contracts; `app.py` supplies TUI state, UI side effects, and governed task dispatch.

## Completion Notes

* Added `src/ga_tui/scheduler.py` as the scheduler source of truth for schedule registry helpers, trigger parsing, due calculation, run audit rows, dispatch shaping, tick aggregation, and scheduler formatting.
* Updated `src/ga_tui/app.py` to import/re-export scheduler helpers while keeping UI-specific beep emission, mutable `State`, subagent resolution, and structured task dispatch in the app composition layer.
* Added `configure_scheduler_runtime()` wiring so scheduler storage paths, JSONL helpers, provider lookup, JSON-safe conversion, text truncation, TUI beep callback, subagent resolver, and dispatch callback are injected rather than imported from `app.py`.
* Updated `scripts/check_policy_gates.py` to assert scheduler module boundaries and to reconfigure scheduler runtime paths when the test harness is retargeted.
* Updated `.trellis/spec/backend/agent-control-protocol.md` with the scheduler module boundary and retargeting contract.

## Verification

* `python3 -m py_compile src/ga_tui/app.py src/ga_tui/scheduler.py src/ga_tui/control_protocol.py src/ga_tui/runtime.py scripts/check_policy_gates.py`
* `python3 scripts/check_policy_gates.py`
* `python3 -m compileall -q src scripts`
* `git diff --check`
* `ga-tui-check --root /home/vimalinx/Programs/GenericAgent`

## Architecture Baseline Comparison

This change moves the system closer to `docs/agent-harness-architecture.md`: scheduled agent work still enters governed `agenttask.v2` delegation, task ledgers, approval gates, mail, traces, checkpoints, and artifact refs; the extraction reduces `app.py` patchification risk by giving scheduler behavior a focused module. Remaining known gaps are unchanged: scheduler lifetime is still tied to an open TUI process, and future long-running recurring agent tasks still need an explicit schedule-level concurrency policy.
