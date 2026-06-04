# Agent Control Protocol

> Executable contract for GenericAgent-TUI control blocks and governed subagent delegation.

## Scenario: ga-control v2 Delegation

### 1. Scope / Trigger

- Trigger: Main-agent TUI controls, subagent creation, task planning, and subagent delegation must use the `ga-control.v2` / `agenttask.v2` contract.
- Applies to: hidden control blocks emitted by the main agent, JSON code-fence controls in recovery paths, auto-continuation prompts, and policy-gate regression tests.
- Historical markup cleanup belongs in quarantine compatibility code only; it must not define executable external protocol behavior.

### 2. Signatures

- Hidden block: `<ga-control>{...}</ga-control>`
- Fenced block: ````ga-control`
- Implementation module: `src/ga_tui/control_protocol.py` owns the current protocol regexes, schema constants, action sets, JSON repair/parsing, extraction, stripping, lifecycle/reuse field parsing, and v2-to-internal-action coercion.
- Execution module: `src/ga_tui/app.py` may re-export protocol helpers for compatibility, but state-mutating execution functions stay in `app.py` unless they are extracted behind an explicit state boundary.
- Batch envelope:

```json
{
  "schema_version": "ga-control.v2",
  "actions": []
}
```

- Single action item:

```json
{
  "schema_version": "agenttask.v2",
  "action": "delegate.create"
}
```

### 3. Contracts

- `ga-control.v2.actions[]` accepts strong typed dotted action names only.
- Supported session actions: `session.pin`, `session.unpin`, `session.category`, `session.filter`, `session.clear_filter`, `session.collapse_category`, `session.expand_category`, `session.archive`, `session.unarchive`, `session.delete`, `session.rename`, `session.show_archived`, `session.hide_archived`.
- Supported task actions: `task.plan.create`, `task.update`, `task.done`, `task.start`, `task.fail`, `task.cancel`.
- Supported agent actions: `agent.create`, `agent.profile.update`, `agent.role.update`, `agent.model.update`, `agent.stop`, `agent.delete`.
- Supported delegation action: `delegate.create`.
- Supported memory action: `memory.candidate`.
- `delegate.create` must carry `routing`, `work_order`, `capability_contract`, `context_contract`, and `output_contract`.
- `delegate.create.work_order.objective` is the policy-gate source of truth. Capability fields such as `tools_forbidden:["deploy","email.send"]` must not trigger deployment or external-send approval by themselves.
- `agent.create` is ephemeral by default. Long-running, scheduled, recurring, or dedicated responsibilities must be expressed with explicit structured fields such as `lifecycle:"persistent"` or `persistent:true`; the runtime must not infer lifecycle from `name`, `profile`, visible prose, or other natural-language descriptions.
- Reuse intent must be explicit. `reuse_policy:"force_new"` / `force_new:true` forces a new agent; visible prose such as "do not reuse" is not a runtime signal unless the model also emits the structured field.
- Plan binding must be explicit. Controls that belong to a plan step must carry `plan_step_id`, `parent_task_id`, or an equivalent explicit step reference; the runtime must not bind steps by matching words like "self-introduction", "chat", or "summary".
- Executable `<ga-control>` blocks are only for real operations. Capability explanations, tutorials, and examples must not include literal executable tags; use escaped text such as `&lt;ga-control&gt;...&lt;/ga-control&gt;` or show only the JSON payload.
- When a real control block is needed, append it after all user-visible prose. Do not place hidden controls in the middle of a visible section, because stripping the control block will leave the visible answer looking truncated.
- Inline-code labels such as `` `<ga-control>` `` in visible prose are not executable control starts and must not consume a later real closing tag.
- `install_tui_control_hint()` must replace any previous GenericAgent-TUI hint block before installing the current `ga-control.v2` hint, and repeated installation must leave exactly one current hint block per backend prompt.
- Protocol parser helpers must have one source of truth in `src/ga_tui/control_protocol.py`; do not redefine `extract_tui_controls()`, `strip_tui_controls()`, `lifecycle_is_persistent()`, `agenttask_*()` helpers, or schema/action constants inside `app.py`.
- `src/ga_tui/control_protocol.py` must not import curses, GenericAgent runtime classes, or mutable TUI `State`. It may depend on quarantined compatibility cleanup from `compat_legacy.py` to strip retired markup without making retired vocabulary executable.

### 4. Validation & Error Matrix

- Missing `schema_version:"ga-control.v2"` on a batch envelope -> no controls are extracted.
- Missing `schema_version:"agenttask.v2"` on a standalone action -> no controls are extracted.
- Unknown action -> ignored during extraction.
- Historical hidden markup -> stripped by quarantine compatibility cleanup only, not executed.
- Previous system hint block present in a backend extra prompt -> removed before the current hint is installed.
- Current hint already present in a backend extra prompt -> do not append another copy.
- Invalid JSON -> ignored.
- `agent.create` with explicit lifecycle markers such as `lifecycle:"ephemeral"` / `temporary:true` -> creates an ephemeral session agent.
- `agent.create` with recurring/daily/archive-building responsibility language but without explicit persistent lifecycle fields -> remains ephemeral.
- `agent.create` with `lifecycle:"persistent"` / `persistent:true` -> creates a persistent subagent under `SUBAGENTS_DIR`.
- `ga-control` JSON that only misses trailing `}` / `]` closers -> repair the missing tail and execute if it parses into known actions.
- Visible prose containing inline-code `` `<ga-control>` `` followed by a real control block -> parse and execute only the real control block, keep the inline label visible, and do not report parse_error.
- Unrepairable `ga-control` JSON -> add an `Agent 控制结果` parse-error message instead of silently swallowing the control block.
- `delegate.create` without a resolvable target -> runtime reports missing subagent target.
- `agent.delete` on a running or aborting subagent -> runtime refuses deletion and asks for a stop first.
- `agent.delete` on an idle subagent -> soft-delete from the TUI list, retain the original directory for audit, and persist `deleted:true`.
- Risky work-order objective -> policy gate queues or rejects according to policy rules.

### 5. Good/Base/Bad Cases

- Good: Batch envelope creates a plan, creates a researcher, then delegates with full routing/work/output contracts.
- Good: A user asks "what can subagents do?" and the assistant answers in visible prose without emitting `<ga-control>`.
- Base: Single `agenttask.v2` action in a JSON fence is extracted only when the action is known.
- Bad: A visible "example" section contains a literal `<ga-control>` block; the runtime will execute and strip it, leaving the section blank.
- Base: A visible diagnosis says `` `<ga-control>` 标签没正确闭合 `` and then appends a real `<ga-control>{...}</ga-control>` block; the inline label is display text only.
- Bad: Bare JSON without the required current schema envelope is ignored.
- Bad: A current envelope with an unknown or non-dotted action name is ignored by the generic schema boundary.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `ga-control.v2` extraction, JSON-fence extraction, current hint install de-duplicates and replaces previous hints, auto-continuation prompt examples, subagent creation, explicit lifecycle handling, soft deletion, delegation, secret-control isolation, and policy-gate behavior.
- Quarantine checks may assert that historical hidden markup is stripped but must not treat it as an executable protocol.
- `scripts/check_policy_gates.py` must assert common missing-tail JSON repair for `<ga-control>` and visible parse-error reporting for unrepairable control JSON.
- `scripts/check_policy_gates.py` must assert inline-code `<ga-control>` labels do not capture later real control blocks.
- `scripts/check_policy_gates.py` must assert `app.py` re-exports key protocol helpers from `ga_tui.control_protocol` and that the protocol module does not import curses.
- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/control_protocol.py scripts/check_policy_gates.py` must pass.
- `python3 scripts/check_policy_gates.py` must pass.
- `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` must pass when the sibling GenericAgent checkout exists.

### 7. Wrong vs Correct

#### Wrong

```json
{"schema_version":"agenttask.v2","action":"delegate_create","target":"研究员","prompt":"查一下这个库"}
```

#### Correct

```json
{
  "schema_version": "agenttask.v2",
  "action": "delegate.create",
  "routing": {
    "mode": "agent_as_tool",
    "selected_agent": "研究员",
    "target_selector": {
      "role": "researcher",
      "capabilities_required": ["web.search", "source.verify"],
      "reuse_policy": "prefer_existing",
      "security_context": "standard"
    }
  },
  "work_order": {
    "objective": "查一下这个库",
    "success_criteria": ["cite evidence", "return risks"],
    "stop_condition": "return structured result and stop"
  },
  "capability_contract": {
    "tools_allowed": ["web.search", "read"],
    "tools_forbidden": ["repo.write", "deploy", "email.send"],
    "write_policy": "none",
    "max_subagents": 0
  },
  "context_contract": {
    "history_mode": "summary",
    "artifact_reference_only": true,
    "include_raw_logs": false
  },
  "output_contract": {
    "format": "structured_markdown",
    "required_sections": ["summary", "findings", "evidence_refs", "risks", "artifact_refs", "confidence"],
    "schema_validation": "strict"
  }
}
```

## Scenario: TUI Read-Only Query Tools

### 1. Scope / Trigger

- Trigger: The main agent needs current TUI dashboard facts before creating, reusing, stopping, or delegating to subagents.
- Applies to: GenericAgent tool schema injection, GenericAgentHandler `do_*` dispatch methods, bound TUI `State`, shared task ledger queries, approval summaries, artifact metadata, and capability discovery.
- Non-goal: These tools must never mutate sessions, tasks, agents, approvals, artifacts, memory, or files. Real state changes still require `ga-control.v2`.

### 2. Signatures

- Tool names exposed to the model are snake_case function tools: `agent_list`, `agent_get`, `agent_match`, `task_list`, `task_get`, `approval_list`, `artifact_list`, `capability_list`.
- User-facing documentation may refer to dotted names: `agent.list`, `agent.get`, `agent.match`, `task.list`, `task.get`, `approval.list`, `artifact.list`, `capability.list`.
- `agent_get` requires `target`.
- `agent_match` requires `objective`.
- `task_get` requires `task_id`.

### 3. Contracts

- Every response is JSON-safe and starts with `schema_version:"ga-tui.query.v1"` plus `status:"ok"` or `status:"error"`.
- Query tools are installed by wrapping `agentmain.load_tool_schema()` and appending TUI schemas idempotently after every GenericAgent schema reload.
- Query handlers are installed by patching `agentmain.GenericAgentHandler` with `do_<tool_name>` methods.
- Runtime state is provided through `agent._ga_tui_state`; if a handler has no bound state, the tool returns an error response instead of guessing.
- `agent_list` returns bounded agent records: id, name, role, lifecycle, status, busy reason, security context, capabilities, write policy, permissions, queues, active task refs, and profile summary.
- `agent_get` returns one detailed bounded record with profile summary/full bounded profile, memory summary, output contract, queue previews, and recent assigned tasks.
- `agent_match` scores current agents using structured selectors only: explicit target, role, capability, security context, lifecycle, and busy state. It must not score arbitrary natural-language objective/profile similarity.
- `task_list` returns latest ledger rows with terminal rows hidden by default unless `include_completed:true`.
- `task_get` returns latest row, bounded history, child tasks, recent traces, approval refs, and artifact refs.
- `approval_list` returns approval metadata and payload keys only; it must not inline raw approval payload bodies.
- `artifact_list` returns artifact metadata and refs only; artifact contents must be read by explicit artifact/file reads.
- `capability_list` returns role templates, permissions, write policies, and registered agents from the gateway capability registry.

### 4. Validation & Error Matrix

- Missing bound TUI state -> `status:"error"` with a clear runtime-binding message.
- `agent_get` target missing, ambiguous, or not found -> `status:"error"`.
- `agent_match` without objective -> `status:"error"`.
- `task_get` without `task_id` or unknown task -> `status:"error"`.
- Repeated `install_tui_query_runtime()` calls -> no duplicate tool schemas and no duplicate handler side effects.
- GenericAgent model switch or `load_tool_schema()` reload -> query schemas are re-appended exactly once.
- Secret Vault unlocked -> subagent query refresh uses Secret subagents instead of normal `memory/subagents/`.

### 5. Good/Base/Bad Cases

- Good: Before answering "which subagent should handle this?", call `agent_match`, then emit `delegate.create` only if execution is intended.
- Good: Before saying "that task is blocked", call `task_get` and `approval_list` to inspect ledger and approval gates.
- Base: A capability explanation calls `capability_list` or `agent_list` and answers in prose without a control block.
- Bad: A query tool creates an agent, starts a task, approves a gate, writes memory, or reads full artifact contents.
- Bad: The model emits `<ga-control>` while only explaining available subagent capabilities.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert all query tool schemas are installed exactly once.
- Tests must assert handler methods exist and return `StepOutcome` with `next_prompt:"\n"`.
- Tests must assert `agent_list`, `agent_get`, and `agent_match` expose current subagent records and recommend reuse when a matching idle agent exists.
- Tests must assert `task_list` hides terminal tasks by default and includes them with `include_completed:true`.
- Tests must assert `task_get` returns latest ledger details and approval references.
- Tests must assert `approval_list` does not inline raw payload bodies.
- `python3 -m py_compile src/ga_tui/app.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```text
The model guesses there is no suitable researcher, creates another subagent, and delegates immediately.
```

#### Correct

```text
Call agent_match(objective="...", role="researcher", capabilities_required=["web.search", "read"]) first.
If the recommendation is reuse_existing, emit delegate.create targeting that agent.
If the recommendation is create_new and the user asked for execution, create a bounded agent and delegate with full agenttask.v2 contracts.
```

## Scenario: TUI Governed Schedule Tools

### 1. Scope / Trigger

- Trigger: The main model needs to create or inspect scheduled work from a natural-language user request.
- Applies to: GenericAgent tool schema injection, GenericAgentHandler `do_*` dispatch methods, `scheduledtask.v1` registry writes, schedule registry reads, and prompt guidance.
- Non-goal: The model must not inspect, modify, or start external scheduler files, external scheduler SOPs, or another program's scheduler directory to satisfy TUI scheduling requests.

### 2. Signatures

- Tool names exposed to the model are snake_case function tools: `schedule_create` and `schedule_list`.
- User-facing documentation may refer to dotted names: `schedule.create` and `schedule.list`.
- `schedule_create` accepts the current `ScheduleCreate` trigger schema: `cron`, `interval`, `at`, or standardized `trigger` strings prefixed as `cron:`, `interval:`, or `at:`.
- `schedule_create` must include a discriminated `execution` object.
- `execution.mode:"tui_action"` runs a bounded local TUI action. The current supported action is `action:"beep"` for audible reminders that do not require a subagent.
- `execution.mode:"agent_task"` dispatches governed work through `agenttask.v2` and carries `routing`, `work_order`, `capability_contract`, `context_contract`, and `output_contract`.
- `schedule_create` response uses `schema_version:"ga-tui.tool.v1"` and returns the appended `scheduledtask.v1` row plus the current schedule registry snapshot.
- `schedule_list` response uses `schema_version:"ga-tui.tool.v1"` and returns the TUI `scheduledtask.registry.v1` snapshot.

### 3. Contracts

- `schedule_create` is a governed state-changing TUI tool, not a read-only query tool.
- `schedule_create` must call the same schedule registration path used by `ga-control.v2` `schedule.create`.
- Created schedule rows must carry `schema_version:"scheduledtask.v1"`, an explicit `execution` object, a matching `dispatch_contract`, and `source:"tool:schedule_create"`.
- Agent-task schedule rows use `dispatch_contract:"agenttask.v2"` and keep agent routing plus work/capability/context/output contracts under `execution`.
- TUI-action reminder rows use `dispatch_contract:"tui_action.v1"` plus the bounded TUI action data under `execution`. They are audited through `scheduledtask.run.v1` rows but do not create task-ledger rows.
- `schedule_list` reads only the TUI schedule registry and schedule-run audit data.
- Natural-language timing is translated by the model into the current positive trigger schema before tool invocation.
- Schema-outside fields are handled by the generic boundary. Active prompts, docs, runtime, user-facing errors, and normal tests should not enumerate retired trigger vocabulary.

### 4. Validation & Error Matrix

- Missing bound TUI state on `schedule_create` -> `status:"error"`.
- Missing current trigger field -> generic missing-trigger error.
- Missing `execution.mode` -> creation/update error.
- `execution.mode:"tui_action"` with `action:"beep"` -> valid TUI reminder schedule.
- Unsupported TUI action -> creation/update error; an already-persisted invalid row records a failed schedule-run row at dispatch time.
- `execution.mode:"agent_task"` without `work_order.objective` -> creation/update error.
- `execution.mode:"agent_task"` without an explicit structured routing target -> creation/update error.
- `schedule_list include_inactive:false` hides disabled, deleted, cancelled, and canceled rows from the returned jobs list.
- Repeated `install_tui_query_runtime()` calls -> no duplicate schedule tool schemas and no duplicate handler side effects.

### 5. Tests Required

- `scripts/check_policy_gates.py` must assert `schedule_create` and `schedule_list` schemas are installed exactly once.
- Tests must assert handler methods exist and return `StepOutcome` with `next_prompt:"\n"`.
- Tests must assert `schedule_create` appends `scheduledtask.v1` rows through the shared registry path for both execution modes.
- Tests must assert an agent-task schedule stores `execution.mode:"agent_task"` and `dispatch_contract:"agenttask.v2"`.
- Tests must assert a TUI beep schedule stores `execution.mode:"tui_action"`, writes `dispatch_contract:"tui_action.v1"`, and appends a completed schedule-run row without requiring an agent target.
- Tests must assert `schedule.update` without an execution object preserves the existing execution contract, and trigger updates leave one current trigger source of truth.
- Tests must assert `schedule_list` reports the TUI schedule registry without requiring any external scheduler file.
- Tests should assert current schedule tool/schema vocabulary and active-prompt absence invariants without locking exact prose.

## Scenario: Control Result Continuation

### 1. Scope / Trigger

- Trigger: The main agent emits real `ga-control.v2` controls for an intermediate workflow step and explicitly requests continuation with structured metadata such as `continue_after:true` or `workflow_state:"in_progress"`, but does not create an executable task ledger and does not emit the next delegation/configuration controls.
- Applies to: normal non-Secret main-agent turns after `apply_tui_controls_from_text()` has executed controls.
- Non-goal: This must not manually execute the business workflow in the TUI. It only feeds control results back to the main agent so the orchestrator can continue emitting governed controls.

### 2. Signatures

- Auto continuation source: `ga-tui:auto_control_continue`.
- Continuation prompt block: `[GA TUI Control Result Continuation] ... [/GA TUI Control Result Continuation]`.
- State counters: per-signature `auto_control_continue_attempts`, session cap `auto_control_continue_count`.
- Structured continuation fields: `continue_after`, `next_action_required`, `requires_continuation`, `workflow_state`, `orchestrator_state`, and `next_action`.

### 3. Contracts

- `apply_tui_controls_from_text()` returns formatted control result lines while still adding the visible `Agent 控制结果` system message.
- The continuation only runs when the executed control envelope or action explicitly carries continuation metadata such as `continue_after:true`, `next_action_required:true`, `requires_continuation:true`, `workflow_state:"in_progress"`, or a non-empty `next_action`.
- Visible prose must never trigger continuation by itself.
- Controls that already delegated child work, such as `delegate.create`, must not trigger this fallback because the next event should be the subagent result.
- If an executable task plan exists, `maybe_queue_orchestrator_plan_continuation()` remains the primary mechanism and this fallback does not run.
- New user-started main tasks reset the control-continuation counters.

### 4. Validation & Error Matrix

- No real controls -> no continuation.
- Active plan exists -> use plan continuation instead.
- Active subagent work, pending interaction, or non-idle main state -> no continuation.
- Same control result signature repeats -> stop after one retry and add an `orchestrator_auto_continue_blocked` system message.
- Session reaches the continuation cap -> stop and add an `orchestrator_auto_continue_blocked` system message.

### 5. Good/Base/Bad Cases

- Good: The assistant emits `agent.create` with `continue_after:true`; TUI creates the agent, then starts `ga-tui:auto_control_continue` with the control result so the assistant can continue with ledger/delegation/configuration.
- Base: The assistant creates an agent as a complete one-step user request without structured continuation metadata; no auto continuation fires.
- Base: The assistant creates an agent and writes "Step 1" in visible prose but omits structured continuation metadata; no auto continuation fires.
- Bad: The assistant emits `delegate.create` and TUI immediately starts another main turn before the subagent result arrives.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert structured continuation metadata plus `agent.create` starts a second main-agent prompt with source `ga-tui:auto_control_continue`.
- The continuation prompt must include the control result, the created agent name, and instruction to continue the approved workflow without repeating controls.
- Existing auto-plan continuation tests must continue to pass and remain primary when a task ledger exists.

### 7. Wrong vs Correct

#### Wrong

```text
Visible text says "Step 1.1 create agent" but the control has no continuation metadata -> Agent 控制结果 shows success -> main agent stops because the control did not request continuation.
```

#### Correct

```text
agent.create includes continue_after:true -> Agent 控制结果 shows success -> ga-tui:auto_control_continue feeds the result back to the orchestrator -> orchestrator emits the next governed controls.
```

## Scenario: Scheduled Task Scheduler

### 1. Scope / Trigger

- Trigger: TUI schedule records must execute recurring or one-shot work without bypassing the governed subagent/task protocol.
- Applies to: `schedule.create`, `schedule.update`, `schedule.enable`, `schedule.disable`, `schedule.delete`, `/schedules`, `/scheduler`, MCP schedule resources, runtime provider registry metadata, and scheduler tick tests.
- Non-goal: A schedule must not directly call `agent.put_task()` or choose a worker from natural-language similarity.

### 2. Signatures

- Schedule registry path: `AGENT_SCHEDULES_PATH`, JSONL rows with `schema_version:"scheduledtask.v1"`.
- Schedule run audit path: `AGENT_SCHEDULE_RUNS_PATH`, JSONL rows with `schema_version:"scheduledtask.run.v1"`.
- TUI commands:
  - `/schedules` shows registry, due state, run count, and last-run state.
  - `/scheduler status` shows scheduler state.
  - `/scheduler tick` evaluates due jobs and records manual skip/invalid outcomes.
  - `/scheduler run <schedule_id>` force-runs one enabled schedule.
- Supported trigger fields: `at`, `interval`, `cron`, and standardized `trigger` strings prefixed as `at:...`, `interval:...`, or `cron:...`.
- Users express scheduling intent in natural language. The main model translates that intent into the current `ScheduleCreate` trigger schema before emitting `ga-control.v2`. Schema-outside fields are handled by the generic boundary; active runtime, prompts, docs, user-facing errors, and normal tests should not enumerate retired field names.
- Daemon tick interval env: `GA_TUI_SCHEDULER_TICK_SECONDS`, minimum 5 seconds, default 30 seconds.
- MCP resources include `resource://agent-mail/schedules` and `resource://agent-mail/schedule-runs`.

### 3. Contracts

- Agent-work schedule dispatch must build an explicit `agenttask.v2` `delegate.create` envelope and reuse the existing delegation path.
- TUI-local reminder dispatch must execute only explicit `execution.mode:"tui_action"` rows and write schedule-run audit rows; it must not infer actions from schedule names or natural-language objectives.
- A dispatchable agent-task schedule must include `execution.work_order.objective` and an explicit structured routing target.
- A TUI-action reminder schedule must include `execution.action`; it does not require `work_order.objective` or an agent target.
- Due jobs reserve an `idempotency_key` by appending a `starting` run row before dispatching.
- Final run rows reuse the same `run_id` and append status such as `dispatched`, `queued`, `approval_required`, `failed`, `rejected`, `duplicate`, `skipped`, or `invalid`.
- Agent-task final run status must come from a structured dispatch result (`status`, `message`, `task_id`, `approval_id`, `error`) rather than parsing localized UI text returned to ordinary callers.
- After each run row, the latest schedule record is updated append-only with `last_run_id`, `last_run_status`, `last_run_at`, and `last_idempotency_key`.
- Due calculation for interval schedules must use the latest real dispatch attempt (`starting`, `dispatched`, `queued`, `approval_required`, `failed`, or `rejected`) as its anchor. Observation-only rows such as `duplicate`, `skipped`, and `invalid` may be displayed as the latest run, but must not move the next interval due time.
- Disabled, deleted, cancelled, and canceled schedules are not dispatched.
- Schedule execution must enter `start_subagent_task()` so policy gates, single-writer locks, task ledger, agent mail, checkpoints, traces, and artifacts remain active.

### 4. Validation & Error Matrix

- Missing `schedule_id` -> invalid/failed run row.
- Unsupported trigger -> `invalid` run row with reason.
- `at` trigger already ran -> duplicate, no dispatch.
- Cron minute already ran -> duplicate, no dispatch.
- Interval slot already ran -> duplicate, no dispatch.
- Explicitly provided `seen_keys:set()` -> use that set exactly, even when empty; do not fall back to global persisted idempotency keys.
- Input outside the current trigger schema -> generic missing trigger or unsupported field handling.
- Unprefixed free-form `trigger` text -> unsupported trigger / invalid; the model should emit current schema fields such as `interval:"1m"` instead.
- Disabled/deleted schedule -> skipped, no dispatch.
- Missing `execution.mode` -> failed run row, no dispatch.
- Agent-task execution without `work_order.objective` -> failed run row, no dispatch.
- Agent-task execution without a structured routing target -> failed run row, no natural-language fallback.
- Unsupported TUI action -> failed run row.
- Target subagent not found -> failed run row.
- Risky scheduled work -> governed subagent dispatch queues approval and writes a final schedule-run row with `status:"approval_required"`, `task_id`, and `approval_id`.

### 5. Good/Base/Bad Cases

- Good: A due `at` schedule with `routing.selected_agent` dispatches through `start_subagent_task()`, writes task ledger rows, and records `starting` then `dispatched` schedule-run rows.
- Good: A due TUI beep schedule executes the local TUI action, writes `starting` then `completed` schedule-run rows, and creates no task-ledger row.
- Base: A disabled schedule is shown in `/schedules` and may record a manual skip, but it never dispatches.
- Base: A cron schedule is evaluated once per matching minute and idempotency prevents repeat dispatch inside that minute.
- Base: A manual skip/duplicate row appears in the audit log and `/schedules`, but the next interval due time is still anchored to the latest real dispatch attempt.
- Good: The user says "every morning at 8"; the main model emits `cron:"0 8 * * *"` in `schedule.create`.
- Bad: Scheduler calls backend `put_task()` directly and skips task ledger / approval gates.
- Bad: The latest `skipped` or `duplicate` row is used as the interval anchor, pushing the next due time forward.
- Bad: The runtime parses free-form prose or schema-outside fields to guess schedule intent.
- Bad: Scheduler sees `role:"researcher"` and guesses a worker by fuzzy matching the objective text.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert schedule registration still records `dispatch_contract:"agenttask.v2"`.
- Tests must assert a due enabled schedule writes `scheduledtask.run.v1` rows and delegates to a fake subagent through the existing task ledger.
- Tests must assert risky scheduled work records `approval_required` from structured dispatch fields and includes the matching task/approval ids.
- Tests must assert duplicate scheduler ticks do not dispatch a second task for the same idempotency key.
- Tests must assert observation-only rows do not change interval due anchors.
- Tests must assert the positive trigger schema and generic schema-boundary behavior without behavior-testing retired field names.
- Tests must assert the control hint tells the main model to translate natural user intent into new `cron` / `interval` / `at` fields.
- Tests must assert disabled schedules skip and invalid schedules write audit records without dispatching.
- Tests must assert MCP/gateway registries include both schedule registry and schedule-run audit paths.
- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/runtime.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```text
At 08:00, scheduler calls agent.put_task("Generate daily digest") directly and stores only the visible result.
```

#### Correct

```text
At 08:00, scheduler writes scheduledtask.run.v1 starting, converts the schedule to agenttask.v2 delegate.create, calls start_subagent_task(), then appends the final run status and relies on task ledger/artifact refs for execution evidence.
```

## Scenario: TUI Session Registry And Archive-Backed Sidebar Rows

### 1. Scope / Trigger

- Trigger: The TUI sidebar needs to show known history sessions even when the raw `model_responses*.txt` source file has been physically archived or is missing.
- Applies to: `load_history()`, `cached_session_rows()`, `session_meta.json`, `session_names.json`, sidebar display, and history restore behavior.
- Non-goal: This bridge must not unzip archives, reconstruct raw logs, or perform destructive filesystem changes.

### 2. Signatures

- Raw session rows are still read from `MODEL_RESPONSES_DIR/model_responses*.txt`.
- Missing-source rows are synthesized from TUI metadata keys whose basename matches `model_responses*.txt` and whose source file is absent.
- Missing-source metadata fields:
  - `source_missing:true`
  - `archive_backed:true`
  - `source_state:"missing"`
  - `source_path`
  - `original_basename`

### 3. Contracts

- Physical archival must not remove a known sidebar row when TUI metadata still knows the session.
- Missing-source rows may use metadata preview, description, rounds, last-user timestamp, and display name to remain visible.
- Missing-source rows must not pretend to be normal raw sessions.
- `restore_history()` must refuse direct restore when the source path is absent and must leave the active runtime untouched.
- When a raw source file reappears, cached raw-session processing clears missing-source markers.

### 4. Tests Required

- `scripts/check_policy_gates.py` must assert `load_history()` includes a missing-source row from `session_meta.json`.
- Tests must assert the row is marked `source_missing:true` and `archive_backed:true`.
- Tests must assert direct restore of a missing-source row reports a clear error and does not bind the active agent log path to the missing file.

## Scenario: Temporary Non-Persistent Main Sessions

### 1. Scope / Trigger

- Trigger: A user enters `/temp` to start a temporary main-agent session.
- Applies to: command routing, main-agent log path binding, session metadata, automatic naming/description/category jobs, durable UI system messages, memory candidate creation, token usage persistence, and background session switching.
- Non-goal: This is not a Secret Vault session and does not encrypt or restore temporary content. It is an in-memory session that disappears when closed or replaced.

### 2. Signatures

- Command: `/temp`.
- Runtime state field: `State.temporary_session:true`.
- Backend log path: `os.devnull`.
- UI title: `临时会话`.

### 3. Contracts

- `/temp` starts a fresh main-agent context and binds the active agent plus LLM backends to `os.devnull`.
- Temporary sessions must not create `model_responses*.txt` history logs.
- Temporary sessions must not write `session_meta.json`, session names, automatic title/description/category metadata, durable UI system messages, token usage registry rows, memory candidates, or direct subagent memory updates.
- If a normal task is running, `/temp` may park it as a background session and then open a temporary active session.
- If a temporary session is parked in the background and later restored, it remains temporary and keeps `os.devnull` as its backend log path.
- `/new` exits temporary mode and creates a normal persistent session log path.
- Secret Vault mode blocks `/temp`; the user must lock Secret Vault before opening a normal temporary session.

### 4. Validation & Error Matrix

- `/temp` while a subagent chat is selected -> user-visible message asking to return to the main orchestrator first.
- `/temp` while Secret Vault is unlocked -> blocked by the normal-command isolation rule.
- Durable UI system message persistence in temporary mode -> no-op.
- Memory candidate or subagent memory write in temporary mode -> user-visible no-op.
- Automatic naming/description/category jobs in temporary mode -> no-op.

### 5. Tests Required

- `scripts/check_policy_gates.py` must assert `/temp` sets `State.temporary_session:true`, binds the active agent/client/backend log path to `os.devnull`, and exposes the command in completions.
- Tests must assert durable UI system message persistence writes no session metadata during temporary sessions.
- Tests must assert memory candidate creation writes no memory candidate or approval rows during temporary sessions.
- Tests must assert `/new` exits temporary mode and restores a normal `model_responses_*.txt` log path.
