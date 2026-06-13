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

## Scenario: Unified Model Command Surface

### 1. Scope / Trigger

- Trigger: The TUI model command surface must expose one visible command while preserving compatibility for older muscle-memory commands.
- Applies to: command help, command completion, direct command execution, model-manager rendering, model config persistence, model probing, model health checks, current-session switching, and default-model selection.
- Non-goal: This does not change `mykey.py` storage shape, provider API probing endpoints, or GenericAgent runtime model semantics.

### 2. Signatures

- Visible TUI command: `/model`
- Hidden compatible execution aliases: `/llm`, `/models`
- Main entrypoint: `open_model_manager(stdscr, state, manage_configs=True)`
- Rendering entrypoint: `draw_model_manager(..., active_category="<provider-tab-label>")`
- Category helpers: `model_entry_category(entry)`, `model_entry_categories(entries)`, `model_entry_indices_for_category(entries, category)`
- Model-manager virtual category helpers: `model_manager_category_index(entries, recent_names, health)`, `model_manager_categories(entries, recent_names)`, `model_manager_entry_indices_for_category(entries, category, recent_names)`, `model_manager_category_status(entries, category, health, recent_names)`

### 3. Contracts

- `COMMANDS` must include `/model` exactly once for the model surface.
- `COMMANDS` must not include `/llm` or `/models`; hidden aliases execute only through explicit command handling.
- `command_matches("/mo", state)` may return `/model`; `command_matches("/ll", state)` and `command_matches("/models", state)` must return no model alias rows.
- `/model`, `/llm`, and `/models` all open the unified model manager with config-management actions enabled.
- The unified manager must keep current-session switching, default selection, recent-model jumping, add/edit/delete, model extraction, single-model test, batch health check, and reload actions.
- Model rows are grouped by concrete provider tabs, not broad protocol categories.
- Provider labels must render as a vertical provider rail inside the model manager, with model rows rendered beside the rail. Do not collapse providers back into one horizontal `供应商 Tabs: A / B / C` line.
- Recent/frequently used models must render as a `常用` virtual rail category parallel to provider categories when matching configured models exist.
- Provider rail colors must summarize category state: configured/no-known-failure is blue, no configured model is grey, and any known failed health/test result is yellow.
- Hot rendering/navigation paths must use a precomputed model-manager category index instead of recalculating provider category membership once per rail row.
- Provider tabs must include configured providers plus the common-provider set derived from template order: `Anthropic`, `OpenAI`, `DeepSeek`, `Kimi`, `Qwen`, and `Zhipu` when those provider templates exist.
- Known provider identity should prefer normalized provider-template `apibase` matches, then provider/template name matches. Unknown/custom providers should fall back to a stable endpoint host label or config display name.
- Non-common template providers must not appear as empty tabs; they appear only after the user configures a model/API for that provider.
- Generated `mykey.py` comments and user-facing empty-state errors must point users to `/model`, not `/llm`.

### 4. Validation & Error Matrix

- User types `/llm` or `/models` -> open unified `/model` manager as a hidden compatibility alias.
- User requests command completion for `/ll` or `/models` -> do not show hidden aliases.
- No configured models -> `/model` manager displays an empty-state message that says to add a provider/API with `/model`.
- Selected row belongs to a different active tab after reload/edit/delete -> normalize selection to the first visible row in the active category.
- Active provider tab has no visible rows -> display a no-models-in-provider message and keep navigation safe.
- Active `常用` tab -> display configured recent models in recent order and keep provider switching/navigation behavior unchanged.
- Many provider tabs -> vertical rail scrolls around the active provider without changing model-selection up/down behavior.
- Runtime cannot find a named model -> error tells the user to reload from `/model`.

### 5. Good/Base/Bad Cases

- Good: `/model` opens one panel where the user can switch the current dialogue model, set the default, add a provider, extract provider models, test a model, and batch validate all models grouped by supplier.
- Good: Providers render as a left-side vertical list, and the filtered model list renders to the right.
- Good: `常用` appears as a peer rail item when recent configured models exist, while empty common providers stay grey until configured.
- Good: DeepSeek and OpenAI-compatible entries with known template base URLs appear under `DeepSeek` and `OpenAI`, not together under one broad `OpenAI` protocol category.
- Base: `/llm` and `/models` still work for users who type them directly, but they are absent from `/help`, README command tables, and command completion.
- Base: A custom endpoint such as `https://api.example.invalid/v1` appears under a stable `example.invalid` tab.
- Bad: `/llm` appears as a normal command row, because that splits the visible command ontology again.
- Bad: `/model` opens a switch-only panel that cannot add/edit/delete or probe provider models.
- Bad: The model panel shows every known provider template as an empty tab.
- Bad: Provider labels are rendered as one long horizontal tab line that truncates useful providers on narrower terminals.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `/model` is present in `COMMANDS` and `/llm` / `/models` are absent.
- `scripts/check_policy_gates.py` must assert `/mo` completes to `/model` and hidden aliases do not complete.
- `scripts/check_policy_gates.py` must assert `/llm`, `/model`, and `/models` help text describes the unified manager and compatibility aliases.
- `scripts/check_policy_gates.py` must assert model category helpers group OpenAI, DeepSeek, custom endpoint, common-provider, and non-common configured providers correctly.
- `scripts/check_policy_gates.py` must assert the model manager renders a vertical provider rail and does not render the old horizontal `供应商 Tabs:` line.
- `scripts/check_policy_gates.py` must assert the model manager exposes `常用` as a virtual category and renders provider rail status colors for configured, empty, and failed categories.
- `scripts/check_policy_gates.py` must assert `draw_model_manager(...)` can render from a supplied precomputed category index without recalculating provider categories.
- README command tables must document `/model` as the single visible model command.

### 7. Wrong vs Correct

#### Wrong

```python
COMMANDS = [
    ("/llm", "", "manage model configs", True),
    ("/model", "", "switch current model", True),
    ("/models", "", "alias for /model", True),
]
```

#### Correct

```python
COMMANDS = [
    ("/model", "", "manage/switch/extract/test/default", True),
]

if text.strip().lower() in {"/llm", "/models", "/model"}:
    open_model_manager(stdscr, state, manage_configs=True)
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

## Scenario: GenericAgent Provider Adapter Boundary

### 1. Scope / Trigger

- Trigger: GenericAgent-specific runtime integration code is needed for tool schema injection, `GenericAgentHandler` method patching, TUI state binding, control-hint installation, or agent lifecycle startup.
- Applies to: `src/ga_tui/genericagent_provider.py`, compatibility re-exports from `src/ga_tui/app.py`, runtime provider registration, model switching, subagent runtime preparation, query tools, and schedule tools.
- Non-goal: The provider module must not own TUI state mutation, curses rendering, ledgers, scheduler registries, Secret Vault storage, or subagent query implementation details.

### 2. Signatures

- Provider module: `src/ga_tui/genericagent_provider.py`.
- Runtime configuration entrypoint: `configure_genericagent_provider_runtime(agentmain, generic_agent_cls, step_outcome_cls, is_state, tool_handlers, thread_factory=...)`.
- Compatibility re-exports from `app.py`: `TUI_AGENT_CONTROL_HINT`, `TUI_QUERY_TOOL_SCHEMAS`, `TUI_SCHEDULE_TOOL_SCHEMAS`, `install_tui_query_runtime()`, `install_tui_control_hint()`, and `GenericAgentRuntimeAdapter`.
- Handler methods installed on `agentmain.GenericAgentHandler`: `do_agent_list`, `do_agent_get`, `do_agent_match`, `do_task_list`, `do_task_get`, `do_approval_list`, `do_artifact_list`, `do_capability_list`, `do_schedule_create`, and `do_schedule_list`.

### 3. Contracts

- `genericagent_provider.py` owns the active GenericAgent-facing control hint, query tool schemas, schedule tool schemas, tool schema injection, `agentmain.load_tool_schema()` wrapping, `GenericAgentHandler` patching, `_ga_tui_state` binding, `install_tui_control_hint()`, and `GenericAgentRuntimeAdapter`.
- `app.py` may re-export provider names for compatibility, but must not locally redefine the moved installers, handler patch functions, control-hint installer, or `GenericAgentRuntimeAdapter`.
- The provider module must not import `ga_tui.app`, curses, or mutable TUI `State`. App-layer behavior is injected through `configure_genericagent_provider_runtime()`.
- Tool handlers remain app-layer callbacks because they read TUI state, subagent registries, ledgers, approvals, artifacts, Secret Vault state, gateway capabilities, and scheduler registries.
- Repeated `install_tui_query_runtime()` calls must append each query/schedule schema at most once and must not add duplicate handler side effects.
- A GenericAgent tool schema reload must re-append TUI tool schemas exactly once.
- Handler methods must return the configured `StepOutcome` class with `next_prompt:"\n"`.
- `GenericAgentRuntimeAdapter.create_agent()` creates the configured GenericAgent class, installs the tool runtime, and sets `inc_out:true`; `prepare_agent()` installs tools and the current control hint; `start_agent()` starts `agent.run()` in a daemon thread.

### 4. Validation & Error Matrix

- Provider module imported before configuration -> runtime installation and adapter creation fail explicitly with a configuration error.
- Missing bound TUI state on a handler call -> injected app-layer tool callback returns the standard TUI tool/query error response.
- Unknown tool kind -> provider returns a JSON-safe `ga-tui.query.v1` error response instead of mutating state.
- Repeated provider configuration -> subsequent handler calls use the latest injected callback map because handler methods dispatch through provider runtime state.
- Provider source imports `ga_tui.app`, curses, or TUI `State` -> boundary violation.
- `app.py` locally defines moved GenericAgent glue after the extraction -> boundary violation.

### 5. Good/Base/Bad Cases

- Good: `app.py` configures the provider with `agentmain`, `GenericAgent`, `StepOutcome`, `isinstance(value, State)`, and a map of `tui_tool_*` callbacks; the provider installs schemas and handler methods.
- Good: Model switching calls the provider's compatibility re-exported `install_tui_query_runtime()` and `install_tui_control_hint()` after selecting the backend model.
- Base: A future runtime provider adds its own adapter without importing curses or TUI state classes.
- Bad: `app.py` defines a second local `GenericAgentRuntimeAdapter` or local `do_agent_list` patch method.
- Bad: `genericagent_provider.py` imports `ga_tui.app` to call `tui_tool_agent_list()` directly, creating a reverse dependency from provider to composition.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert app compatibility re-exports are identical to `ga_tui.genericagent_provider` names.
- Tests must assert moved functions and `GenericAgentRuntimeAdapter` have `__module__ == "ga_tui.genericagent_provider"`.
- Tests must assert `genericagent_provider.py` has no reverse import into `app.py` and no curses import.
- Tests must assert `app.py` no longer locally defines the moved GenericAgent glue functions or adapter class.
- Tests must preserve query/schedule schema idempotency, handler method presence, `StepOutcome(next_prompt:"\n")`, state-bound tool dispatch, and control-hint de-duplication checks.
- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/genericagent_provider.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# app.py
def install_tui_query_handler_methods():
    setattr(agentmain.GenericAgentHandler, "do_agent_list", ...)
```

#### Correct

```python
# app.py
configure_genericagent_provider_runtime(
    agentmain=agentmain,
    generic_agent_cls=GenericAgent,
    step_outcome_cls=StepOutcome,
    is_state=lambda value: isinstance(value, State),
    tool_handlers={"agent_list": tui_tool_agent_list},
)
```

## Scenario: Oh My Pi Runtime Provider

### 1. Scope / Trigger

- Trigger: GenericAgent-TUI integrates Oh My Pi as the experiment-branch default local runtime provider.
- Applies to: `src/ga_tui/ohmypi_provider.py`, runtime provider registration in `src/ga_tui/app.py`, runtime registry records, provider selection, GA/TUI memory prompt injection, app-injected TUI host tool registration, governed proposal routing, memory candidate signaling, and RPC queue/event mapping.
- Non-goal: This provider must not own curses rendering, mutable TUI `State`, GenericAgent tool schema injection, TUI approval storage, scheduler registries, or first-class TUI subagent ledger mutation.

### 2. Signatures

- Provider module: `src/ga_tui/ohmypi_provider.py`.
- Provider id: `ohmypi`.
- Runtime adapter: `OhMyPiRuntimeAdapter(RuntimeAdapter)`.
- Queue-compatible wrapper: `OhMyPiRpcAgent`.
- Provider metadata helper: `ohmypi_provider_spec(root_dir, harness_dir, recent_models_path, schedules_path, binary=None, command=None)`.
- RPC command helper: `ohmypi_rpc_command(binary=None, extra_args=None, append_system_prompt=None)`.
- Memory append prompt helpers: `write_ohmypi_memory_prompt(root_dir, harness_dir)` and `ohmypi_memory_prompt_path(harness_dir)`.
- TUI host tools exposed to OMP: `ga_tui_query` and `ga_tui_propose`.
- Read-only host tool definition helper: `ohmypi_tui_readonly_host_tool_definitions()`.
- Governed proposal host tool definition helper: `ohmypi_tui_proposal_host_tool_definition()`.
- Combined host tool definition helper: `ohmypi_tui_host_tool_definitions()`.
- Combined host tool callback helper: `ohmypi_tui_host_tool_handler(state=None)`.
- Backward-compatible query callback helper: `ohmypi_tui_query_host_tool_handler(state=None)`.
- Environment keys:
  - unset `GA_TUI_RUNTIME_PROVIDER` selects `ohmypi` on this experiment branch.
  - `GA_TUI_RUNTIME_PROVIDER=genericagent` selects the fallback GenericAgent adapter.
  - `GA_TUI_OHMYPI_BIN` overrides the executable, default `omp`.
  - `GA_TUI_OHMYPI_ARGS` appends shell-split extra CLI arguments.
- Default RPC command shape: `omp --mode rpc --no-title --approval-mode always-ask --append-system-prompt <generated-memory-file>`.

### 3. Contracts

- `OhMyPiRpcAgent.put_task(prompt, source="", images=None)` must return a `queue.Queue` immediately.
- Oh My Pi RPC `message_update` frames with `assistantMessageEvent.type:"text_delta"` map to queue items shaped as `{"next": <delta>, "source": "ohmypi"}`.
- Oh My Pi RPC terminal frames `agent_end` or `turn_end` map to one queue item shaped as `{"done": <buffer>, "source": "ohmypi"}`.
- Startup, prompt, or missing-binary failures must map to a queue `done` item instead of raising into the TUI caller after `put_task()` returns.
- The wrapper must expose the current GenericAgent-shaped compatibility surface used by existing TUI hot paths: `put_task()`, `abort()`, `get_llm_name()`, `list_llms()`, `load_llm_sessions()`, `next_llm()`, `is_running`, `task_queue.unfinished_tasks`, `log_path`, `llmclient.backend`, and `llmclients`.
- `OhMyPiRuntimeAdapter.start_agent()` must not block on model or network startup. RPC process startup is lazy and happens on first prompt.
- The provider module must not import `ga_tui.app`, curses, or mutable TUI `State`.
- Oh My Pi unrestricted host tools remain disabled in provider metadata: `capabilities.host_tools:false`.
- The only allowed host tool bridge is app-injected TUI governance querying and governed proposal routing: `capabilities.tui_readonly_host_tools:true` and `capabilities.tui_governed_proposal_tools:true`.
- `OhMyPiRpcAgent` may register host tools through `set_host_tools` only from definitions injected by `app.py`; provider code must not invent writable tools or import TUI `State`.
- `ga_tui_query` is read-only and must never mutate sessions, tasks, agents, approvals, artifacts, memory, or files.
- `ga_tui_propose` accepts only bounded proposal payloads with `proposal_type:"ga_control"` or `proposal_type:"memory_candidate"`.
- `ga_tui_propose` with `proposal_type:"ga_control"` must require a current-schema `ga-control.v2` envelope or `agenttask.v2` action object, validate that it maps to known current controls, and route execution through `apply_tui_controls_from_text(..., source="agent:ohmypi_host_tool")` so existing policy gates and ledgers remain the source of truth.
- `ga_tui_propose` with `proposal_type:"memory_candidate"` must resolve the target subagent from the bound TUI `State` and call `queue_curated_memory_candidate(...)`; direct long-term memory writes remain forbidden.
- `ga_tui_propose` results use `schema_version:"ga-tui.proposal.v1"` and return JSON-safe `status`, `kind`, result lines/messages, ids, and artifact refs where available.
- Host tool registration must happen after OMP emits `{"type":"ready"}` and before the first prompt command is sent for that process.
- OMP `host_tool_call` frames must be answered with `host_tool_result` using the same frame `id`.
- Host tool result payloads must be AgentToolResult-shaped JSON, with bounded redacted text under `content:[{"type":"text","text":"..."}]`.
- Unknown tools, missing handlers, invalid arguments, and callback failures must return `host_tool_result` with `isError:true` instead of crashing the stdout reader or active prompt.
- OMP `host_tool_cancel` frames must be accepted safely and must not mutate TUI state.
- Host URI schemes and TUI approval mapping remain disabled until a separate explicit task designs those governance contracts.
- On this experiment branch, Oh My Pi is the default runtime provider when `GA_TUI_RUNTIME_PROVIDER` is unset.
- GenericAgent must remain selectable with `GA_TUI_RUNTIME_PROVIDER=genericagent`.
- The TUI should generate a bounded `GA/TUI Memory Guidance` append prompt from GA/TUI memory sources and pass it through `--append-system-prompt`.
- Oh My Pi completion output may emit memory candidate signals, and `ga_tui_propose` may submit curated memory candidates, but long-term memory writes remain governed by TUI memory candidate records and human approval.

### 4. Validation & Error Matrix

- `omp` executable missing -> provider spec status is `missing`; prompt queue receives a user-visible startup failure.
- RPC process does not emit `{"type":"ready"}` before timeout -> prompt queue receives an RPC ready timeout failure and the process is terminated.
- Prompt command receives `success:false` -> active prompt queue receives `RPC prompt failed: ...`.
- Concurrent `put_task()` while one prompt is active -> second queue receives a user-visible concurrency error.
- RPC stdout emits non-JSON -> line is recorded in provider stderr tail and ignored.
- RPC extension UI request `confirm` -> provider replies `confirmed:false`.
- RPC extension UI request `select`, `input`, or `editor` -> provider replies `cancelled:true`.
- `abort()` called during a prompt -> provider sends RPC `abort`, emits a queue `done` item, clears `is_running`, and decrements `task_queue.unfinished_tasks`.
- OMP `ready` with configured app-injected TUI tools -> provider sends `set_host_tools` before the prompt frame.
- OMP `host_tool_call` for `ga_tui_query` -> provider runs the app-injected read-only callback and sends a JSON-safe `host_tool_result`.
- OMP `host_tool_call` for `ga_tui_propose` memory candidate -> app callback routes through `queue_curated_memory_candidate(...)` and returns a JSON-safe proposal result with candidate/approval/artifact refs when queued.
- OMP `host_tool_call` for `ga_tui_propose` current-schema control -> app callback routes through `apply_tui_controls_from_text(...)` and returns control result lines.
- OMP `host_tool_call` for `ga_tui_propose` with unknown proposal type, missing required fields, missing TUI state, unresolved target, invalid schema, or no known action -> callback returns `schema_version:"ga-tui.proposal.v1"` with `status:"error"`.
- OMP `host_tool_call` for an unregistered tool -> provider sends `host_tool_result` with `isError:true`.
- OMP `host_tool_call` whose callback raises -> provider sends `host_tool_result` with `isError:true`.
- OMP `host_tool_cancel` -> provider records the cancellation safely and continues normal prompt handling.

### 5. Good/Base/Bad Cases

- Good: unset `GA_TUI_RUNTIME_PROVIDER` selects `OhMyPiRuntimeAdapter`, starts `omp --mode rpc` lazily with the generated memory append prompt, streams text deltas into the existing TUI message renderer, and keeps GenericAgent available as an explicit fallback.
- Good: Missing `omp` produces an assistant-visible error message instead of crashing startup.
- Base: `/runtimes` shows both `genericagent` and `ohmypi`, while the experiment-branch default is `ohmypi`.
- Base: Oh My Pi can query bounded TUI governance facts through `ga_tui_query` without mutating task ledgers, approvals, artifacts, or long-term memory.
- Base: Oh My Pi can propose current-schema actions through `ga_tui_propose`, while GenericAgent-TUI remains the Orchestrator and policy/ledger owner.
- Base: Oh My Pi can submit a durable memory candidate through `ga_tui_propose`, while the TUI Memory Curator creates artifacts and a human approval request before any long-term memory write.
- Base: A durable completed Oh My Pi output records a memory candidate signal for later approval instead of writing long-term memory directly.
- Base: Oh My Pi internal task/subagent events are provider-owned details until a future ledger-mapping feature is implemented.
- Bad: The provider imports `app.py` to read TUI state or mutate ledgers directly.
- Bad: The adapter enables arbitrary OMP host tools, host URI schemes, writable operations, or auto-approval before TUI policy gates can audit and approve those operations.
- Bad: `app.py` contains Oh My Pi RPC parsing logic instead of provider-local parsing.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `ohmypi` appears in the runtime registry and is the experiment-branch default.
- Tests must assert `GA_TUI_RUNTIME_PROVIDER=genericagent` selects the GenericAgent fallback adapter.
- Tests must assert `ohmypi_provider.py` has no reverse import into `app.py` and no curses import.
- Tests must assert the generated memory append prompt is bounded, redacted, and passed to `omp` through `--append-system-prompt`.
- Tests must assert completed Oh My Pi output can produce a governed memory candidate signal and that empty, too-short, and secret-looking outputs are skipped.
- Tests must assert a fake RPC process maps `ready`, `prompt` ack, `message_update` deltas, and `agent_end` into queue `next`/`done` items.
- Tests must assert a fake RPC process receives app-injected `set_host_tools` definitions before the prompt frame.
- Tests must assert fake `host_tool_call` frames receive `host_tool_result` success frames.
- Tests must assert unknown or failing host tool calls receive `host_tool_result` with `isError:true`.
- Tests must assert `host_tool_cancel` frames are handled safely.
- Tests must assert `ga_tui_query` remains read-only and `ga_tui_propose` supports governed `ga_control` and `memory_candidate` proposals.
- Tests must assert `ga_tui_propose` memory candidates create existing memory approval artifacts/approval rows and invalid proposals return structured errors.
- Tests must assert provider metadata advertises `tui_readonly_host_tools:true` and `tui_governed_proposal_tools:true` while keeping unrestricted `host_tools:false`.
- Tests must assert missing binary failure and `abort()` cleanup decrement unfinished task state.
- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/ohmypi_provider.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# app.py
if provider_id == "ohmypi":
    line = process.stdout.readline()
    frame = json.loads(line)
```

#### Correct

```python
# ohmypi_provider.py
class OhMyPiRuntimeAdapter(RuntimeAdapter):
    def create_agent(self) -> OhMyPiRpcAgent:
        return OhMyPiRpcAgent()
```

#### Wrong

```python
# ohmypi_provider.py
def handle_memory_candidate(statement):
    from ga_tui.app import queue_curated_memory_candidate
    queue_curated_memory_candidate(...)
```

#### Correct

```python
# app.py
def ohmypi_tui_propose_host_tool_handler(state, args):
    if args["proposal_type"] == "memory_candidate":
        return ohmypi_tui_propose_memory_candidate(state, args)
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
- Implementation module: `src/ga_tui/scheduler.py` owns schedule registry helpers, trigger parsing, due calculation, run audit shaping, tick aggregation, and scheduler text formatting.
- Composition module: `src/ga_tui/app.py` may re-export scheduler helpers for compatibility, but it supplies mutable TUI dependencies through `configure_scheduler_runtime()` instead of being imported by `scheduler.py`.
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
- `src/ga_tui/scheduler.py` must not import curses, GenericAgent runtime classes, `StepOutcome`, mutable TUI `State`, or `ga_tui.app`.
- App-layer dependencies required by scheduler execution must be injected through scheduler runtime configuration: JSONL readers/writers, paths, `now_iso`, JSON-safe conversion, default provider lookup, text truncation, TUI beep callback, subagent resolver, and structured subagent dispatch callback.
- TUI beep emission stays in `app.py` or another UI composition layer; scheduler dispatch calls it through an injected callback so the scheduler module remains UI-free.

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
- Tests must assert `app.py` re-exports key scheduler helpers from `ga_tui.scheduler` and that `src/ga_tui/scheduler.py` does not import curses, GenericAgent runtime classes, `StepOutcome`, mutable TUI `State`, or `ga_tui.app`.
- Tests that retarget harness paths must reconfigure scheduler runtime paths in the same step, otherwise scheduler JSONL helpers can silently write to the previous harness directory.
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
