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

## Registry Surfaces

Runtime and top-level control metadata are exposed through:

- `runtime_registry`: `agentruntime.registry.v1`, persisted at `runtime_providers.json`.
- `model_orchestration`: `model_orchestration.v1`, built from the TUI model manager state.
- `scheduled_task_registry`: `scheduledtask.registry.v1`, persisted at `schedules.jsonl`.
- `scheduledtask.run.v1`: Scheduler run audit rows persisted at `schedule_runs.jsonl`.
- `ga-control.v2` schedule actions: `schedule.create`, `schedule.update`, `schedule.enable`, `schedule.disable`, and `schedule.delete`.
- `capability_registry.runtime_providers`: Provider details available to query tools.
- MCP resources: `resource://agent-mail/runtime-providers`, `resource://agent-mail/schedules`, and `resource://agent-mail/schedule-runs`.
- TUI commands: `/runtimes`, `/schedules`, and `/scheduler`.

## Design Rules

- Do not let backend-specific APIs leak into orchestration code.
- Do not choose a provider by natural-language name similarity. Use explicit provider/capability metadata.
- Do not let scheduled jobs bypass task ledger, artifact, or approval policy.
- Scheduled jobs must reserve an idempotency key before dispatch, record the run result, and then delegate through `agenttask.v2`.
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
