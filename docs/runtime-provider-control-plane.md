# Runtime Provider Control Plane

Shuheng is evolving from a GenericAgent-only frontend into a local agent
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

The current public posture is experimental local alpha. Gateway, A2A, MCP,
baseline, eval, and scheduler automation metadata are compatibility surfaces
unless backed by explicit end-to-end client tests.

Runtime providers own narrow execution:

- Accept a bounded work order.
- Run with declared tools, permissions, and model settings.
- Stream events or return a final result.
- Expose artifact refs, status, and interrupt support.

Agent clients that are not launched directly by the TUI, such as OMP plugins,
Codex adapters, or Claude Code adapters, must use a Shuheng-owned bridge instead
of scraping files or writing ledgers. The local bridge entrypoint is
`shuheng-agent-bridge` / `python -m ga_tui.agent_bridge`; it exposes read-only
context retrieval and governed proposal submission while keeping approvals,
memory, schedules, artifacts, and traces in the TUI control plane.

## Storage Boundary

GenericAgent remains a runtime/source dependency, not the owner of Shuheng state.
By default Shuheng stores its durable control-plane data under `~/.shuheng`:

- `model_responses/`: canonical visible conversation history for main sessions and
  non-secret subagent direct chats, plus metadata, names, token usage, and trash.
- `memory/agent_harness/`: task ledgers, agent mail, approvals, artifacts, traces, checkpoints, schedules, gateway metadata, runtime provider metadata, and memory candidates.
- `memory/subagents/`: persistent subagent profiles, memories, events, dashboard/runtime metadata, and refs into canonical history. It must not own non-secret conversation transcripts.
- `temp/subagents/`: temporary/session-bound subagents.
- `memory/secret_vault/`: encrypted Secret Vault state, including encrypted Secret subagent chat history that cannot be copied into normal plaintext history.
- `memory/agent_harness/runtime/ohmypi/agent`: isolated OMP config, models, and active `PI_CODING_AGENT_DIR`.

`SHUHENG_HOME` overrides the whole Shuheng-owned storage root. The legacy
internal `GA_TUI_HOME` compatibility override is still accepted. Targeted test
or bridge runs may override `GA_TUI_HARNESS_DIR` or `GA_TUI_SECRET_VAULT_DIR`,
but normal runtime state must not default back into the GenericAgent checkout.

On the normal default home, Shuheng performs a one-time, non-destructive legacy
bootstrap when old GenericAgent state exists: missing `model_responses*.txt`
files, session sidecars, global memory files, and persistent subagent memories
are copied into `~/.shuheng`. Existing Shuheng files win on conflict, stale
`memory/agent_harness/runtime/**` files are skipped, and the old GenericAgent
tree is left untouched. The marker is `~/.shuheng/.legacy_import.json`.

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

For OMP, the request prompt can include a generated Shuheng context pack. The
context pack is written as a harness artifact under `context_packs/` and passed
by reference in the request. OMP may consume the pack and submit candidates or
proposals, but long-term memory, approvals, task ledgers, and schedule registries
remain Shuheng-owned.

OMP main-runtime context packs use a Shuheng permission profile. The default is
`full`, so the main OMP assistant can advertise practical read/write/search/bash/
browser/eval/task capabilities instead of behaving like a read-only
`specialist`. The main OMP runtime role is `main_orchestrator`; role-bounded
subagent context packs stay on `standard` unless a caller explicitly selects
another profile. Operators can force compatibility mode with
`GA_TUI_OMP_PERMISSION_PROFILE=read_only` or set a process-wide default with
`GA_TUI_DEFAULT_PERMISSION_PROFILE`.

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
installed. Unrestricted provider host tools stay disabled; only Shuheng-injected
read-only and governed proposal tools are allowed.

The isolated OMP config generated by Shuheng defaults `tools.approvalMode` to
`yolo`, so runtime tools run without OMP approval prompts inside the Shuheng-owned
runtime directory under `~/.shuheng/memory/agent_harness/runtime/ohmypi/agent`.
The main `permission_profile:full` context carries no runtime
tool-deny list and no runtime approval-required list. Operators can still force a
narrower OMP mode with `GA_TUI_OMP_APPROVAL_MODE=always-ask|write|yolo`.
OMP binary discovery is `GA_TUI_OHMYPI_BIN`, then `PATH` lookup for `omp`, then
the user-local Bun install at `$HOME/.bun/bin/omp`; Shuheng does not mutate shell
startup files to make this work.

OMP RPC `turn_end` is a turn boundary, not always task completion. When a turn
ends because of tool use, Shuheng waits for the later final assistant message or
`agent_end` before releasing the active prompt, so folded tool output does not
replace the visible final reply.

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
- OMP plugin tools: repo-managed Shuheng plugin
  `integrations/omp-ga-tui-plugin` exposes compatibility tools
  `ga_tui_context_get` and `ga_tui_memory_candidate_submit` by calling the
  local Shuheng bridge CLI.
- MCP resources: `resource://agent-mail/runtime-providers`, `resource://agent-mail/schedules`, and `resource://agent-mail/schedule-runs`.
- TUI commands: `/runtimes`, `/schedules`, and `/scheduler`.
- Release readiness: `/gateway` exposes `release_readiness` with stable local
  surfaces, experimental surfaces, known gaps, and verification commands.

## Design Rules

- Do not let backend-specific APIs leak into orchestration code.
- Do not choose a provider by natural-language name similarity. Use explicit provider/capability metadata.
- Do not let scheduled jobs bypass task ledger, artifact, or approval policy.
- Scheduled jobs must reserve an idempotency key before dispatch, record the run result, and then delegate through `agenttask.v2`.
- Scheduler run rows must record the resolved runtime provider. If a schedule
  omits `provider_id`, the injected runtime registry default is used, which is
  `ohmypi` on this branch.
- Do not let model choice override policy gates. Model routing is subordinate to TUI governance.
- Do not let OMP permission profiles override policy gates. `full` means normal
  runtime tool availability, not direct long-term memory writes or automatic
  approval for high-risk actions.
- Do not describe A2A/MCP as certified protocol implementations without real
  third-party client interoperability tests; use compatibility-surface wording
  until those tests exist.
- Do not bind the Web Console/gateway to a non-loopback interface unless
  `GA_TUI_GATEWAY_ALLOW_REMOTE_BIND=1` is deliberately set and an external
  trusted access boundary is in place. The built-in gateway has no auth layer.
- Keep provider selection explicit and reversible; this experiment branch defaults
  to `ohmypi`, with `genericagent` retained as the fallback adapter.
- Do not make an OMP plugin a new memory owner. Plugin tools may read context and
  submit memory candidates; Shuheng validates, queues approvals, writes durable
  rows, and records provenance.

## Next Providers

Good next adapter candidates:

- Codex CLI: code execution and review tasks, approval-gated write operations.
- Claude Code: clean-context review and long-codebase reading.
- OpenAI Agents SDK: agent-as-tool workers and remote tool-backed specialists.
- A2A remote agents: cross-machine or cross-framework workers discovered through agent cards.

Each new provider should first expose metadata and read-only smoke behavior before
it is allowed to run write or external-send work.
