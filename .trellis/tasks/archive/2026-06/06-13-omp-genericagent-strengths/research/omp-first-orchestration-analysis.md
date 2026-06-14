# OMP-first Orchestration Analysis

## Corrected Product Direction

The intended target is not a bidirectional GenericAgent/OMP sync layer. The target is:

- GA-TUI should embed and productize OMP as the primary runtime.
- GenericAgent's useful strengths should become GA-TUI control-plane services around OMP.
- GenericAgent's Python runtime should be treated as legacy/fallback or eventually removed from the primary product path.

## Current Code Findings

### Runtime Layer

- `src/ga_tui/runtime.py` already defines provider metadata and adapter boundaries.
- The current registry registers both `genericagent` and `ohmypi`; OMP is default through `GA_TUI_RUNTIME_PROVIDER`.
- `OhMyPiRpcAgent` intentionally presents a GenericAgent-shaped `put_task()` queue interface, which keeps old hot paths working but also hides the opportunity to make OMP a first-class task runtime.

### OMP Provider

- `src/ga_tui/ohmypi_provider.py` owns JSONL stdio RPC, isolated config generation, model projection, host tool registration, stream mapping, and memory-candidate signal extraction.
- Embedded OMP already uses a GA-TUI-owned `PI_CODING_AGENT_DIR`, so the correct product boundary is already isolated from system `~/.omp/agent`.
- OMP provider currently has coarse host tools: `ga_tui_query` and `ga_tui_propose`.
- OMP provider metadata says `human_approval:false`, but approval still exists in the GA-TUI control plane. The better model is provider approval capability via TUI gateway, not native OMP approval ownership.

### GenericAgent Provider

- `src/ga_tui/genericagent_provider.py` mostly contains GenericAgent-specific glue: tool schema injection, `GenericAgentHandler` patching, control prompt injection, and thread startup.
- Its useful concepts are the query tool schemas, schedule tool schemas, control hint, and handler dispatch pattern. These should be moved into provider-neutral control-plane modules rather than kept tied to GenericAgent.

### App Control Plane

- `src/ga_tui/app.py` is the real owner of the valuable GenericAgent strengths:
  - session metadata and durable UI system messages
  - subagent registry, profile, memory, chat sessions, and lifecycle
  - task ledger, agent mail, approvals, artifacts, checkpoints, traces, evals
  - role templates, permissions, single-writer policy, risk policy
  - scheduler runtime and schedule-run audit
  - context pack hydration for delegated subagent tasks
  - memory candidate extraction and approval flow
- Many of these services are currently entangled in a single large app module but are not inherently GenericAgent-specific.

### Scheduler

- `src/ga_tui/scheduler.py` is already provider-neutral enough: it owns schedule registry/run audit and dispatches through injected app callbacks.
- Its default provider id is already `ohmypi`.
- This can become an OMP-first scheduler by routing scheduled work into OMP-backed task execution while preserving `agenttask.v2`, idempotency, approval, and audit.

## Proposed Better Architecture

### 1. Product Shape

Rename the internal mental model from "GenericAgent-TUI with OMP provider" to:

```text
OMP Workbench / GA-TUI Control Plane

TUI Product Shell
  - sessions
  - model/settings
  - agents/workers
  - approvals
  - memory
  - scheduler
  - artifacts/traces

Control Plane Services
  - Orchestrator service
  - Task ledger service
  - Memory service
  - Scheduler service
  - Artifact/trace service
  - Policy/approval service
  - Context-pack service

Runtime
  - OMP primary runtime through JSONL RPC
  - optional legacy GenericAgent runtime for fallback only
```

### 2. OMP-first Runtime Contract

Introduce a provider-neutral task runtime contract above the old GenericAgent-shaped queue:

```python
RuntimeTaskRequest:
  task_id
  parent_task_id
  agent_id
  role
  objective
  context_pack_ref
  prompt
  model
  permissions
  approval_policy
  output_contract

RuntimeTaskEvent:
  task_id
  provider_id
  event_type
  delta
  artifact_refs
  tool_call_refs
  status
  error
```

`OhMyPiRpcAgent.put_task()` can remain as a compatibility shim, but new orchestration should prefer structured `RuntimeTaskRequest` and event normalization.

### 3. Memory System

Make memory a GA-TUI control-plane service, not a GenericAgent feature:

- `MemoryHydrator`: builds OMP context packs from project memory, subagent memory, current session, task ledger, artifacts, and approved user/project memory.
- `MemoryCandidateSink`: accepts OMP text signals, `ga_tui_propose` memory candidates, and subagent memory blocks.
- `MemoryCurator`: dedupes, scores, maps scope, attaches evidence refs, and creates approval records.
- `MemoryPublisher`: after approval, writes to GA-TUI memory stores and regenerates OMP memory prompt/context pack.

OMP should never write long-term memory directly. It receives memory through context packs and submits candidates through tools/events.

### 4. Scheduler System

Keep the scheduler as a control-plane service:

- Schedules are registered in GA-TUI.
- Runs are audited as `scheduledtask.run.v1`.
- Due jobs create `agenttask.v2` work orders.
- Dispatch target defaults to OMP runtime.
- Risky scheduled work queues approvals before runtime dispatch.
- OMP only executes approved/allowed work and streams events/artifacts back.

### 5. Worker/Subagent System

Keep GA-TUI's worker registry but change implementation semantics:

- Subagent records are "managed workers" with role/profile/memory/policy.
- OMP is the execution substrate for those workers.
- A worker's prompt/context is built by GA-TUI, then executed by OMP.
- OMP-native subagents can exist later, but they should be imported as worker capabilities only through an explicit mapping contract.

### 6. Tool Surface

Replace coarse OMP tools with typed control-plane tools:

- Read-only: `agent_list`, `agent_get`, `agent_match`, `task_list`, `task_get`, `approval_list`, `artifact_list`, `capability_list`, `schedule_list`, `memory_context_get`.
- Governed mutations: `proposal_submit`, `memory_candidate_submit`, `schedule_create`, `task_delegate`, `artifact_create_ref`.
- All mutations return proposal/audit ids and run through policy.

The old `ga_tui_query` and `ga_tui_propose` can remain aliases for compatibility.

### 7. Module Decomposition

Recommended extraction from `app.py`:

- `control_plane/session_store.py`
- `control_plane/memory_service.py`
- `control_plane/task_ledger.py`
- `control_plane/artifact_store.py`
- `control_plane/policy_service.py`
- `control_plane/context_pack.py`
- `control_plane/worker_registry.py`
- `control_plane/tool_gateway.py`
- `runtime/ohmypi_runtime.py`

This turns "GenericAgent-TUI" into an OMP-first workbench while keeping the proven governance code.

## Migration Plan

### Phase 1: OMP-first Facade

- Make OMP the only visible runtime in product language.
- Keep GenericAgent fallback hidden behind env/dev mode.
- Update `/runtimes`, docs, and provider metadata to express OMP-primary.
- Add OMP-first runtime task records and event tracing while preserving old queue paths.

### Phase 2: Memory Service

- Extract memory hydration/candidate/approval logic into a provider-neutral service.
- Generate per-task OMP context packs instead of relying mostly on append prompt.
- Add typed `memory_context_get` and `memory_candidate_submit` host tools.

### Phase 3: Scheduler Service

- Make scheduler dispatch explicitly OMP-backed by default.
- Add UI/status surfaces that show scheduled OMP tasks, run provenance, approval state, and artifacts.
- Preserve `agenttask.v2` and idempotency.

### Phase 4: Worker Runtime

- Rework subagent execution so workers are GA-TUI-managed identities executed by OMP.
- Add per-worker OMP model/settings/context profiles.
- Normalize OMP result streams into artifacts, task ledger rows, traces, and memory candidate extraction.

### Phase 5: Remove or Quarantine GenericAgent Runtime

- Keep GenericAgent as dev fallback until OMP-first paths pass parity checks.
- Remove GenericAgent-specific prompt/tool injection from product path.
- Retain only compatibility shims if needed.

## MVP Recommendation

The first implementation should not be model/settings sync. It should be:

**OMP-first Memory + Scheduling Foundation**

Concrete MVP:

1. Add a provider-neutral `RuntimeTaskRequest`/`RuntimeTaskEvent` data shape.
2. Add an OMP context-pack artifact per main task/subagent task, referenced by task ledger.
3. Add typed OMP host tools for read-only state and memory candidate submission.
4. Route scheduler due agent tasks into OMP with explicit provider provenance.
5. Record OMP runtime events into traces/artifacts.

This directly gives OMP the GenericAgent advantages the user cares about: memory, scheduling, orchestration, approvals, and auditability.
