# Runtime Provider Control Plane

GenericAgent-TUI is evolving from a GenericAgent-only frontend into a local agent
control plane. The TUI owns orchestration and governance; concrete agent systems
plug in as runtime providers.

## Ownership

The TUI owns these top-level responsibilities:

- Session navigation, recovery, and transcript display.
- Task ledgers, progress ledgers, checkpoints, traces, evals, and artifacts.
- Human approval gates and single-writer enforcement.
- Runtime provider selection and capability discovery.
- Model routing, model validation, recent/default model records, and per-agent default model assignment.
- Scheduled task registry and recurring dispatch through governed `agenttask.v2` delegation.
- A2A/MCP gateway metadata for external agents and tools.

Runtime providers own narrow execution:

- Accept a bounded work order.
- Run with declared tools, permissions, and model settings.
- Stream events or return a final result.
- Expose artifact refs, status, and interrupt support.

## Runtime Task Boundary

New OMP-first orchestration paths use provider-neutral task records before they
cross into any concrete runtime:

- `runtime.task_request.v1`: `task_id`, `parent_task_id`, `provider_id`,
  `agent_id`, `role`, `objective`, `source`, `prompt_preview`, `prompt_chars`,
  `context_pack_ref`, `model`, permissions, approval policy, output contract,
  artifact refs, and provider metadata. The in-memory request object carries the
  full prompt for runtime dispatch, but durable records should use bounded prompt
  previews plus artifact refs.
- `runtime.task_event.v1`: normalized provider events such as
  `runtime_task_requested`, `runtime_host_tool_call`,
  `runtime_host_tool_result`, `runtime_task_completed`,
  `runtime_task_failed`, and `runtime_task_aborted`.

For OMP, the request prompt can include a generated GA-TUI context pack. The
context pack is written as a harness artifact under `context_packs/` and passed
by reference in the request. OMP may consume the pack and submit candidates or
proposals, but long-term memory, approvals, task ledgers, and schedule registries
remain GA-TUI-owned.

## Provider Contract

The executable Python contract is `RuntimeAdapter` in `src/ga_tui/runtime.py`.
The discoverable metadata contract is `RuntimeProviderSpec`.

Provider metadata must include:

- `provider_id`: Stable id such as `genericagent`, `codex`, or `a2a.remote.researcher`.
- `capabilities`: Streaming, interrupt, session restore, tool calling, artifact refs, memory candidates, and approval support.
- `model_routing`: Whether the provider supports current-session switching, defaults, per-agent defaults, and how model selection is addressed.
- `scheduler`: How scheduled jobs dispatch into the provider, normally through `agenttask.v2`.
- `policy`: Approval owner, memory write policy, and risky action classes.
- `a2a` / `mcp`: Gateway compatibility metadata.

The first implemented provider is `genericagent`. On the
`experiment/ohmypi-runtime-memory` branch, `ohmypi` is the default runtime while
`genericagent` remains available as an explicit fallback through
`GA_TUI_RUNTIME_PROVIDER=genericagent`.

OMP provider metadata must advertise `tui_typed_host_tools`,
`runtime_task_requests`, and `runtime_task_events` when the app-layer bridge is
installed. Unrestricted provider host tools stay disabled; only GA-TUI-injected
read-only and governed proposal tools are allowed.

## Registry Surfaces

Runtime and top-level control metadata are exposed through:

- `runtime_registry`: `agentruntime.registry.v1`, persisted at `runtime_providers.json`.
- `model_orchestration`: `model_orchestration.v1`, built from the TUI model manager state.
- `scheduled_task_registry`: `scheduledtask.registry.v1`, persisted at `schedules.jsonl`.
- `scheduledtask.run.v1`: Scheduler run audit rows persisted at `schedule_runs.jsonl`.
- `ga-control.v2` schedule actions: `schedule.create`, `schedule.update`, `schedule.enable`, `schedule.disable`, and `schedule.delete`.
- `capability_registry.runtime_providers`: Provider details available to query tools.
- OMP host tools: compatibility aliases `ga_tui_query` / `ga_tui_propose` plus
  typed tools such as `agent_list`, `task_get`, `schedule_list`,
  `memory_context_get`, `memory_candidate_submit`, and `schedule_create`.
- MCP resources: `resource://agent-mail/runtime-providers`, `resource://agent-mail/schedules`, and `resource://agent-mail/schedule-runs`.
- TUI commands: `/runtimes`, `/schedules`, and `/scheduler`.

## Design Rules

- Do not let backend-specific APIs leak into orchestration code.
- Do not choose a provider by natural-language name similarity. Use explicit provider/capability metadata.
- Do not let scheduled jobs bypass task ledger, artifact, or approval policy.
- Scheduled jobs must reserve an idempotency key before dispatch, record the run result, and then delegate through `agenttask.v2`.
- Scheduler run rows must record the resolved runtime provider. If a schedule
  omits `provider_id`, the injected runtime registry default is used, which is
  `ohmypi` on this branch.
- Do not let model choice override policy gates. Model routing is subordinate to TUI governance.
- Keep provider selection explicit and reversible; this experiment branch defaults
  to `ohmypi`, with `genericagent` retained as the fallback adapter.

## Next Providers

Good next adapter candidates:

- Codex CLI: code execution and review tasks, approval-gated write operations.
- Claude Code: clean-context review and long-codebase reading.
- OpenAI Agents SDK: agent-as-tool workers and remote tool-backed specialists.
- A2A remote agents: cross-machine or cross-framework workers discovered through agent cards.

Each new provider should first expose metadata and read-only smoke behavior before
it is allowed to run write or external-send work.
