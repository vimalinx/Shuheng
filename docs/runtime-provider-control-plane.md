# Runtime Provider Control Plane

Shuheng is an OhMyPi/OMP-anchored local agent control plane. OMP is the
permanent strong main/general Agent and the default conversational entry for
general reasoning, decomposition, and synthesis. The TUI also permits an
operator to start an explicit governed Agent Project assignment directly; that
manual path records and injects the result into OMP context but does not promise
an automatic OMP synthesis turn. The TUI/control plane owns governance and
durable state; bounded worker systems plug in as runtime providers. A worker
provider is not a replacement candidate for the OMP base layer.

## Ownership

The TUI owns these top-level responsibilities:

- Session navigation, recovery, and transcript display.
- Task ledgers, progress ledgers, checkpoints, traces, evals, and artifacts.
- Human approval gates and single-writer enforcement.
- Runtime provider selection and capability discovery.
- Model routing, model validation, recent/default model records, and per-agent default model assignment.
- Scheduled task registry and recurring dispatch through governed `agenttask.v2` delegation.
- Local protocol-shaped records for agent/tool discovery metadata.

OMP owns the main conversational and Orchestrator role inside those control
boundaries. The `ohmypi` provider therefore remains both permanent and the
default. Pi-native is a separate, experimental worker path for user-authored
Agent Projects. It can execute an explicit assignment, but it cannot become the
main session or grant itself declared runtime authority. Shuheng governs task
admission, ledgers, and normal control-plane APIs. An explicitly authorized
custom Tool is trusted host code and is not contained by those API-level claims;
the unsandboxed boundary is documented below.

The current public posture is experimental local alpha. The supported surfaces
are the local curses TUI, local JSONL stdio gateway, Agent Mail, and resource
registries. A2A/MCP-shaped data is local registry metadata.

Runtime providers own narrow execution:

- Accept a bounded work order.
- Run with declared tools, permissions, and model settings.
- Stream events or return a final result.
- Expose artifact refs, status, and interrupt support.

The resulting topology is intentionally hierarchical:

```text
User -> Shuheng TUI/control plane -> permanent OMP main Agent
                                      -> governed assignment
                                         -> bounded Pi-native Agent Project worker
```

This is an Orchestrator-worker system, not a peer chat mesh or unbounded swarm.

Agent clients that are not launched directly by the TUI, such as OMP plugins,
Codex adapters, or Claude Code adapters, must use a Shuheng-owned bridge instead
of scraping files or writing ledgers. The local bridge entrypoint is
`shuheng-agent-bridge` / `python -m shuheng.agent_bridge`; it exposes read-only
context retrieval and governed proposal submission while keeping approvals,
memory, schedules, artifacts, and traces in the TUI control plane.

For external agents that need a long-lived local gateway, Shuheng exposes
`shuheng-agent-gateway`. It is the public JSONL stdio gateway; the
`shuheng-agent-bridge` command and `python -m shuheng.agent_bridge` are trusted
internal integration surfaces and must not be handed to an untrusted client.
`register` writes the local registration record, `serve --stdio` keeps
the process alive, `agent-directory` exposes purpose-only agent discovery,
`message-send` dispatches through the Orchestrator-owned subagent task path, and
`task-status` reads ledger status.

`shuheng install-agent-gateway-skill` installs Shuheng's bundled
`shuheng-agent-gateway` skill into the shared local skill root. That skill is an
agent-facing usage guide for the stdio gateway only: it may teach discovery,
message dispatch, and task-status reads, but must not expose internal contexts,
ledgers, secrets, permission matrices, or private filesystem paths.

`scripts/dogfood_stdio_gateway.py` is the executable end-to-end proof for this
surface. It starts a real `serve --stdio` subprocess under an isolated
`SHUHENG_HOME`, sends JSONL `agent_directory`, `message_send`, and `task_status`
requests over the same process, and verifies task, approval, and trace ledgers.

## Storage Boundary

External compatibility providers are not the owner of Shuheng state and are not
required for normal startup. By default Shuheng stores its durable control-plane
data under `~/.shuheng`:

- `model_responses/`: canonical visible conversation history for main sessions and
  non-secret subagent direct chats, plus metadata, names, token usage, and trash.
- `memory/agent_harness/`: task ledgers (`tasks.jsonl`), progress ledgers (`progress.jsonl`), agent mail, approvals, artifacts, traces, checkpoints, schedules, local protocol metadata, runtime provider metadata, and memory candidates.
- `memory/subagents/`: persistent subagent profiles, memories, events, dashboard/runtime metadata, and refs into canonical history. It must not own non-secret conversation transcripts.
- `temp/subagents/`: temporary/session-bound subagents.
- `memory/secret_vault/`: encrypted Secret Vault state, including encrypted Secret subagent chat history that cannot be copied into normal plaintext history.
- `memory/agent_harness/runtime/ohmypi/agent`: isolated OMP config, models, and active `PI_CODING_AGENT_DIR`.
- `agent_projects/<project-id>/`: user-owned Agent Project source. These are
  normal editable files and remain visible to Git, external editors, and the TUI
  workspace; they are not duplicated into an opaque authoring database.
- `memory/agent_harness/runtime/pi-native/`: Pi-native adapter control state only.
  Each task gets a fresh sidecar process and a mode-`0700` operating-system
  temporary directory; frozen Prompt, Skill, and Tool materialization is removed
  before the terminal result is delivered.

`SHUHENG_HOME` overrides the whole Shuheng-owned storage root. Targeted test or
bridge runs may override `SHUHENG_HARNESS_DIR` or `SHUHENG_SECRET_VAULT_DIR`,
but normal runtime state must not default back into an external runtime
checkout.

On the normal default home, Shuheng may perform a one-time, non-destructive
legacy bootstrap from an older local runtime checkout: missing
`model_responses*.txt` files, session sidecars, global memory files, and
persistent subagent memories are copied into `~/.shuheng`. Existing Shuheng
files win on conflict, stale `memory/agent_harness/runtime/**` files are
skipped, and the source tree is left untouched. The marker is
`~/.shuheng/.legacy_import.json`.

## Runtime Task Boundary

Governed orchestration paths use provider-neutral task records before they cross
into any concrete runtime:

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

The request also has a transient in-memory `runtime_payload` for provider inputs
that must not be copied into the durable task row. Pi-native dispatch uses this
channel for the frozen `shuheng.agent_build.v1` and
`shuheng.agent_run_manifest.v1` records. `RuntimeTaskRequest.to_record()` omits
the payload, so Prompt, Skill, and Tool source bytes do not leak into task
metadata or ordinary trace rows. Durable records retain the build digest,
causation, and Shuheng-owned artifact refs; a provider must never reopen mutable
Agent Project source to reconstruct an already-started run.

For OMP, the request prompt can include a generated Shuheng context pack. The
context pack is written as a harness artifact under `context_packs/` and passed
by reference in the request. OMP may consume the pack and submit candidates or
proposals, but long-term memory, approvals, task ledgers, and schedule registries
remain Shuheng-owned.

OMP main-runtime context packs use a Shuheng permission profile. The main role
remains `main_orchestrator`, but its public default is `standard`; role-bounded
subagents also default to `standard`. Operators can select
`SHUHENG_OMP_PERMISSION_PROFILE=read_only` for a narrower context or explicitly
opt into `SHUHENG_OMP_PERMISSION_PROFILE=full` when broad local host authority
is intended. A missing or malformed value must fail back to `standard`, never
to the broad profile.

## Agent Project Boundary

An Agent Project is the local, user-editable definition of one task-oriented
worker. Its authoring source is a directory of ordinary files. The MVP exposes:

- `shuheng.agent_project.v1`: project identity, entry Blueprint, default runtime,
  runtime revision constraint, and optional test refs.
- `shuheng.agent_blueprint.v1`: Prompt, Skills, explicit project-local Tools,
  requested capabilities, delegation limits, budget, and output contract.
- `shuheng.agent_build.v1`: deterministic, content-addressed snapshot of every
  referenced source blob, including path, role, size, SHA-256, and frozen bytes.
- `shuheng.agent_run_manifest.v1`: assignment and causation refs, Build digest,
  provider revision, workspace, budget/output contract, and resolved authority.

The Build is the execution input. Editing Prompt, Skill, or Tool source changes
the next Build digest but cannot mutate a Build already dispatched. Paths are
validated inside the project root; undeclared files and mutable source paths are
not runtime inputs.

Authoring authority and execution authority are deliberately different. A
Blueprint can request capabilities and Tool IDs, the control plane can grant a
bounded set for a particular assignment, and only the intersection is effective:

```text
requested ∩ granted = effective
```

A project-local Tool is executable code. It must be declared in the Blueprint,
captured by the Build digest, explicitly granted in the Run Manifest, and loaded
from digest-verified frozen bytes inside a per-run temporary directory. The
human Tool grant and the task policy approval are separate gates, and both remain
bound to the confirmed Build digest through approval and queueing. A Skill
is an inert prompt/resource until the selected worker loads it. An OMP plugin is
an extension of the permanent OMP runtime and remains behind the OMP/Shuheng
plugin bridge; it is not an Agent Project Skill, Tool grant, or new owner of
state. Full Pi Extension/Hook lifecycles and arbitrary MCP discovery remain
outside this MVP.

The local authoring loop is create, fork, edit, validate/build, and run. The TUI
offers a minimal single-file Agent Project workspace while the same files remain
editable through the filesystem, Git, or an external editor. The embedded editor
provides a project/file view, cursor editing, dirty state, save, undo, diagnostics,
and external-change conflict protection. It is not an IDE: multi-tab editing,
completion, LSP, debugging, and an embedded terminal are not part of the current
contract. Import, export, publishing, package distribution, and a marketplace are
also not part of the local MVP.

Every Agent Project assignment is admitted through `/agent-project run`, which
shows and binds the current frozen Build digest. Generic `/agent ask`, scheduler,
and recovery-retry lanes cannot execute a Project without that confirmation
token. Because frozen bytes are transient, an old Project task cannot be replayed
from mutable current source; recovery directs the operator through a new Build
confirmation instead.

## Provider Contract

The executable Python contract is `RuntimeAdapter` in `src/shuheng/runtime.py`.
The discoverable metadata contract is `RuntimeProviderSpec`.

Provider metadata must include:

- `provider_id`: Stable id such as `ohmypi`, `codex`, or `local.researcher`.
- `capabilities`: Streaming, interrupt, session restore, tool calling, artifact refs, memory candidates, and approval support.
- `model_routing`: Whether the provider supports current-session switching, defaults, per-agent defaults, and how model selection is addressed.
- `scheduler`: How scheduled jobs dispatch into the provider, normally through `agenttask.v2`.
- `policy`: Approval owner, memory write policy, and risky action classes.
- `a2a` / `mcp`: Local protocol-shaped metadata over Agent Mail and resources.

The default provider is permanently `ohmypi`. An optional provider specification
may remain discoverable while reporting itself unavailable, but its adapter may
launch only when the required sidecar/binary and dependency revision are
available. Registration never makes a worker eligible for the main session.

The `pi-native` provider is limited to Agent Project worker assignments. Its
Python adapter speaks normalized runtime events over a JSONL stdio sidecar. The
repo-managed sidecar pins the upstream `@earendil-works/pi-coding-agent` SDK,
disables implicit Extension, Prompt, context-file, Theme, and global/project
Skill discovery, and supplies only Build-resolved resources and effective Tools.
It must not read ambient `~/.pi`, `~/.omp`, or project-ancestor configuration.
Every assignment starts a fresh sidecar process, so imported Tool globals,
listeners, SDK mutations, and module caches cannot cross into the next Build.

OMP provider metadata must advertise `tui_typed_host_tools`,
`runtime_task_requests`, and `runtime_task_events` when the app-layer bridge is
installed. Unrestricted provider host tools stay disabled; only Shuheng-injected
read-only and governed proposal tools are allowed.

The isolated OMP config generated by Shuheng defaults `tools.approvalMode` to
`write`. Combined with the default `standard` permission profile, write-capable
runtime Tools fail closed unless the operator chooses the required authority.
`always-ask` remains available; `full` plus `yolo` is an explicit expert opt-in
through `SHUHENG_OMP_PERMISSION_PROFILE=full` and
`SHUHENG_OMP_APPROVAL_MODE=yolo`. A lone `yolo` request is downgraded to
`write`; `full + write/always-ask` may auto-admit only bounded local edit/write
Tools. Shell, browser, eval, task, unknown, and textually high-risk prompts fail
closed at the program-level gate.

The OMP subprocess receives a narrow runtime environment rather than a copy of
the host process environment. Shuheng supplies the isolated agent directory,
basic process/locale/certificate variables, and generated
`SHUHENG_OMP_API_KEY_*` values. Proxy settings, enterprise variables, or other
named values require explicit `SHUHENG_OMP_INHERIT_ENV=NAME_A,NAME_B` opt-in;
the variable names are inherited, but the allowlist directive itself is not
forwarded to OMP.

OMP binary discovery is `SHUHENG_OHMYPI_BIN`, then `PATH` lookup for `omp`, then
the user-local Bun install at `$HOME/.bun/bin/omp`; Shuheng does not mutate shell
startup files to make this work.

OMP RPC `turn_end` is a turn boundary, not always task completion. When a turn
ends because of tool use, Shuheng waits for the later final assistant message or
`agent_end` before releasing the active prompt, so folded tool output does not
replace the visible final reply.

OMP remains the execution kernel for the permanent main/general Agent and for
OMP's own agent loop, tool loop, retry, compaction, plugin execution, session
lifecycle, and native subagent lifecycle. A Pi-native worker has its own bounded
SDK session behind the provider contract; this does not transfer main-Agent or
control-plane ownership to Pi.
Shuheng exposes OMP native RPC output/control surfaces such as
`set_subagent_subscription`, `get_subagents`, `get_subagent_messages`, and
`extension_ui_request` observability through the provider adapter. These surfaces
are passthrough output facts: they do not let Shuheng synthesize OMP-native
subagent state from its own ledgers, and they do not transfer approval, memory,
schedule, artifact, or local protocol execution ownership away from the control plane.

## Registry Surfaces

Runtime and top-level control metadata are exposed through:

- `runtime_registry`: `agentruntime.registry.v1`, persisted at `runtime_providers.json`.
- `model_orchestration`: `model_orchestration.v1`, built from the TUI model manager state.
- `scheduled_task_registry`: `scheduledtask.registry.v1`, persisted at `schedules.jsonl`.
- `scheduledtask.run.v1`: Scheduler run audit rows persisted at `schedule_runs.jsonl`.
- `agent_directory`: `shuheng.agent_directory.v1`, stored as a local discovery
  record for other adapters to inspect through explicit local integration.
- `context_inspector`: `shuheng.context_inspector.v1`, kept as an internal
  TUI/control-plane projection for local operator inspection.
- `permission_matrix`: `shuheng.permission_matrix.v1`, kept as an internal
  TUI/control-plane projection for local operator inspection.
- `shuheng-control.v2` schedule actions: `schedule.create`, `schedule.update`, `schedule.enable`, `schedule.disable`, and `schedule.delete`.
- `capability_registry.runtime_providers`: Provider details available to query tools.
- Agent Project records: local project/Blueprint source compiles to immutable
  Build and Run Manifest records before `pi-native` dispatch. Runtime metadata
  exposes project identity and Build digest, not editable source bytes.
- A2A-shaped agent cards: discovered role templates and visible subagents
  advertise local `agent-mail://inbox` delivery with `auto_dispatch:false`.
- Local Agent Mail intake helpers can record messages into Agent Mail, the task
  ledger, and trace rows only. They record `kind:"agent_mail_intake"` and leave
  execution, approvals, memory writes, and workflow continuation owned by the
  Shuheng Orchestrator/TUI.
- Local persistent gateway registration: `agentgateway.registration.v1` at
  `gateway_registration.json` records `shuheng.local` as a local JSONL stdio
  gateway. It exposes `message-send` and `task-status` through
  `shuheng-agent-gateway`, which returns only positive
  purpose/routing/status projections
  and excludes context, permission, approval-payload, trace, and local-path internals.
- OMP host tools: compatibility aliases `shuheng_query` / `shuheng_propose` plus
  typed tools such as `agent_list`, `task_get`, `schedule_list`,
  `memory_context_get`, `runtime_subagent_list`,
  `runtime_subagent_messages`, `memory_candidate_submit`, and
  `schedule_create`.
- OMP native RPC output layer: provider methods expose subagent subscription,
  subagent summaries, subagent transcript reads, and extension UI request events
  from the live OMP RPC process without creating hidden runtime work.
  The read-only query names `runtime_subagent_list` and
  `runtime_subagent_messages` are app-layer projections of those provider
  methods; they are distinct from `agent_list`, which reports Shuheng-managed
  workers from TUI state.
- OMP plugin tools: repo-managed Shuheng plugin
  `integrations/omp-shuheng-plugin` exposes compatibility tools
  `shuheng_context_get` and `shuheng_memory_candidate_submit` by calling the
  local Shuheng bridge CLI.
- MCP resources: `resource://agent-mail/runtime-providers`,
  `resource://agent-mail/schedules`, and
  `resource://agent-mail/schedule-runs`.
- TUI commands: `/runtimes`, `/schedules`, and `/scheduler`, plus the local Agent
  Project workspace and create/fork/build/run actions.
- TUI runtime output view: `/runtime-output` formats the same OMP-native
  runtime subagent query helpers as an operator-readable, read-only snapshot.
- Release readiness: `src/shuheng/release_readiness.py` exposes stable local
  surfaces, experimental local records, known gaps, and verification commands.

## Design Rules

- Do not let backend-specific APIs leak into orchestration code.
- Do not choose a provider by natural-language name similarity. Use explicit provider/capability metadata.
- Do not let scheduled jobs bypass task ledger, artifact, or approval policy.
- Scheduled jobs must reserve an idempotency key before dispatch, record the run result, and then delegate through `agenttask.v2`.
- Scheduler run rows must record the resolved runtime provider. If a schedule
  omits `provider_id`, the injected runtime registry default is used, which is
  `ohmypi`.
- Do not let model choice override policy gates. Model routing is subordinate to TUI governance.
- Do not let OMP permission profiles override policy gates. `full` means normal
  runtime tool availability, not direct long-term memory writes or automatic
  approval for high-risk actions.
- Do not describe A2A/MCP-shaped records as certified protocol implementations
  or reachable endpoints.
- Keep the gateway path on the local JSONL stdio contract owned by the
  Orchestrator.
- Do not let local Agent Mail message intake become a hidden executor. External
  adapter messages are inbox entries and ledger facts until the Orchestrator/TUI
  decides what to run.
- Do not expose broad project context, active specs, memory paths, workflow run
  internals, or full permission matrices to external agents by default. External
  discovery should describe what each agent/role is for and how to message it.
- Do not include local harness paths, process pid/status/log paths, delivery-store
  JSONL paths, or local skill/plugin filesystem paths in adapter-facing
  discovery records.
- Do not create phantom message targets. Agent Mail intake targets must resolve
  to the main orchestrator, a known role template, or a locally discovered subagent.
- Do not list Secret Vault subagents from stateless plaintext metadata. Secret
  subagents require the unlocked TUI state boundary.
- Keep provider selection explicit and reversible; Shuheng defaults to `ohmypi`.
- Keep OMP as the permanent strong main/general Agent. Pi-native may run only an
  explicit bounded worker assignment and must never silently replace the main
  conversation provider.
- Treat Agent Project files as user-owned authoring source, not runtime grants.
  User editability must not imply automatic filesystem, network, Tool, Secret,
  memory, or control-plane authority.
- Freeze all declared Prompt, Skill, and Tool bytes before dispatch. A provider
  must execute the frozen Build and must not reopen mutable project source during
  the run.
- Keep requested, granted, and effective capabilities and Tools distinct. A
  Blueprint request is never a grant, and a grant outside the declared Build is
  invalid.
- Do not implicitly discover global Pi resources, OMP resources, Extensions,
  Hooks, Skills, Prompts, context files, or MCP servers for a Pi-native run.
- Do not make an OMP plugin a new memory owner. Plugin tools may read context and
  submit memory candidates; Shuheng validates, queues approvals, writes durable
  rows, and records provenance.

## Known Gaps And Non-Goals

- The current proof is a local operator-driven create/fork/edit/build/run loop.
  General automatic OMP planning and policy-based routing into arbitrary Agent
  Projects is not yet a complete product surface.
- A source checkout or installed wheel ships the sidecar source and pinned
  `package.json`, not `node_modules`. Until Node >= 22.19 and
  `@earendil-works/pi-coding-agent@0.80.6` are installed beside the sidecar, the
  optional Provider reports `missing_package`; OMP remains available.
- Pi-native runs do not provide transparent provider parity with OMP. OMP and Pi
  Session, Extension, Tool, retry, compaction, and event semantics may differ.
- Pi-native worker sessions are not migrated to or from OMP sessions. Durable
  recovery currently relies on Shuheng task, artifact, trace, and checkpoint
  records rather than cross-provider session restore.
- Busy-worker queue contents remain process-local in this MVP. Approved tasks do
  receive a durable `queued` ledger/checkpoint/trace row, but a host restart does
  not reconstruct the prompt queue; the operator must confirm a new Build run.
- Agent Project workers currently use only the standard governed task lane.
  Secret Vault execution and unledgered direct chat are deliberately blocked.
- A granted project-local Tool is trusted local Node code. The MVP verifies and
  freezes its bytes, binds the executable grant to one Build, strips unrelated
  host credentials from the sidecar environment, and destroys the fresh process
  and temporary source after the run. It does not yet provide an OS-level
  syscall/filesystem/network sandbox inside that run. Capability intersection
  controls whether the Tool is loaded; it is not a syscall policy. Run only
  locally authored Tool source you trust. A hard-killed host may leave a
  best-effort-cleaned temporary directory until normal OS temp cleanup.
- Frozen Build bytes are intentionally transient in this privacy-first MVP.
  Durable rows keep the digest, Run Manifest, causation, and result artifacts,
  but not a replayable source bundle or Git commit. If the authoring files later
  change, an old run remains auditable by identity but cannot be reconstructed
  from Shuheng state alone. Recovery retry therefore requires a new
  `/agent-project run` confirmation. Content-addressed encrypted Build retention
  and true Build replay remain future work.
- The embedded editor deliberately lacks multi-tab editing, completion, LSP,
  debugging, and an embedded terminal.
- Agent Project import/export, template publishing, dependency packaging,
  upgrades, signatures, trust distribution, and a marketplace are not present.
- Full Pi Extension/Hook support and arbitrary third-party MCP auto-discovery are
  not present. Project-local executable Tools remain the only Pi-native
  executable authoring surface in this slice.
- Agent Project execution and A2A/MCP-shaped records remain local to the
  Shuheng control plane.
- Unbounded recursive worker spawning and peer-to-peer Agent swarms are not a
  goal. The strong OMP Orchestrator and Shuheng governance boundary remain
  mandatory.

## Next Providers

Good next adapter candidates:

- Codex CLI: code execution and review tasks, approval-gated write operations.
- Claude Code: clean-context review and long-codebase reading.
- OpenAI Agents SDK: agent-as-tool workers behind an explicit local adapter.
- Agent-card-shaped local adapters: cross-framework workers described through local records before any external transport is designed.

Each new provider should first expose metadata and read-only smoke behavior before
it is allowed to run write or external-send work.
