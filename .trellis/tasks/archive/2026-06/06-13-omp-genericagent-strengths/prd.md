# OMP-first GenericAgent-TUI Orchestration

## Goal

Transform GA-TUI into an OMP-first agent workbench: OMP is the primary runtime inside the TUI, while GenericAgent's useful strengths become provider-neutral control-plane services around OMP, especially memory, scheduling, task ledgers, approvals, artifacts, traces, and governed worker orchestration.

## Corrected Direction

The user clarified that the goal is not GA/OMP bidirectional sync. The intended product is:

- GA-TUI should "put OMP inside" as the primary runtime.
- OMP should be enhanced with GenericAgent's memory and scheduling systems.
- A more complete orchestration system should be designed after analyzing the codebase.
- GenericAgent should not remain the conceptual center of the product.

## What I Already Know

- OMP is already the default runtime provider on this experiment branch.
- Embedded OMP already runs in a GA-TUI-owned isolated `PI_CODING_AGENT_DIR`, not system `~/.omp/agent`.
- GA-TUI already projects `/model` entries into isolated OMP `config.yml` and `models.yml`.
- OMP already communicates through JSONL stdio RPC and exposes a GenericAgent-shaped queue compatibility wrapper.
- OMP already has bounded host-tool bridges: `ga_tui_query` for read-only state and `ga_tui_propose` for governed control or memory-candidate proposals.
- GenericAgent's most valuable behavior is now mostly in GA-TUI's control plane, not in the GenericAgent runtime adapter itself.
- Existing control-plane assets include subagents/workers, memory candidates, approvals, scheduler, task ledger, agent mail, artifacts, checkpoints, traces, evals, role permissions, and single-writer policy.

## Requirements

- Make OMP the primary product/runtime path in GA-TUI.
- Keep embedded OMP isolated from system `~/.omp/agent`.
- Preserve GenericAgent's useful memory system as a GA-TUI/OMP control-plane service.
- Preserve GenericAgent's useful scheduler system as a GA-TUI/OMP control-plane service.
- Preserve approvals, artifacts, task ledgers, traces, checkpoints, and single-writer policy.
- Reframe subagents as GA-TUI-managed workers executed by OMP.
- Avoid giving OMP direct write authority over long-term memory, secrets, approvals, or ledgers.
- Maintain a temporary GenericAgent fallback only as an escape hatch during migration.

## Proposed Architecture

```text
OMP Workbench / GA-TUI Control Plane

TUI Product Shell
  - sessions
  - /model and runtime settings
  - workers/subagents
  - approvals
  - memory
  - schedules
  - artifacts/traces/evals

Control Plane Services
  - Orchestrator service
  - Worker registry
  - Memory service
  - Scheduler service
  - Task ledger and agent mail
  - Artifact/trace/checkpoint/eval store
  - Policy and approval service
  - Context-pack builder
  - Typed host-tool gateway

Runtime Layer
  - OMP primary runtime through JSONL RPC
  - GenericAgent fallback quarantined behind env/dev mode
```

## Technical Approach

### Runtime Contract

Introduce a provider-neutral runtime task contract above the current GenericAgent-shaped queue compatibility layer:

- `RuntimeTaskRequest`: task id, parent task id, worker id, role, objective, context pack ref, prompt, model, permissions, approval policy, output contract.
- `RuntimeTaskEvent`: task id, provider id, event type, stream delta, tool refs, artifact refs, status, error.

`OhMyPiRpcAgent.put_task()` can remain as a compatibility shim while new orchestration paths use structured task requests/events.

### Memory System

Extract memory behavior into a provider-neutral OMP-first memory service:

- `MemoryHydrator`: builds per-task/per-worker OMP context packs from approved memory, worker profile/memory, current session, task ledger, and artifact refs.
- `MemoryCandidateSink`: accepts OMP memory-candidate signals, typed host-tool submissions, and worker output markers.
- `MemoryCurator`: dedupes, scopes, scores, and attaches evidence refs.
- `MemoryPublisher`: writes approved memory and regenerates OMP context inputs.

OMP receives memory through generated context packs and submits memory candidates; it never writes long-term memory directly.

### Scheduler System

Keep scheduler ownership in GA-TUI, but make OMP the default executor:

- Schedule rows stay `scheduledtask.v1`.
- Run rows stay `scheduledtask.run.v1`.
- Due jobs create `agenttask.v2` work orders.
- Risky scheduled work queues approval before OMP execution.
- OMP runs approved work and streams events/artifacts back into GA-TUI.

### Worker/Subagent System

Reframe subagents as OMP-backed workers:

- GA-TUI owns worker identity, role, permissions, memory, profile, and lifecycle.
- OMP executes worker tasks using generated context packs.
- Results are normalized into artifacts, task ledger rows, traces, evals, and memory candidates.
- OMP-native subagents can be mapped later only through an explicit capability/provenance contract.

### Host Tool Gateway

Replace or augment coarse OMP tools with typed tools:

- Read-only tools: `agent_list`, `agent_get`, `agent_match`, `task_list`, `task_get`, `approval_list`, `artifact_list`, `capability_list`, `schedule_list`, `memory_context_get`.
- Governed tools: `proposal_submit`, `memory_candidate_submit`, `schedule_create`, `task_delegate`, `artifact_create_ref`.
- Keep `ga_tui_query` and `ga_tui_propose` as compatibility aliases during migration.

## Migration Plan

### Phase 1: OMP-first Facade

- Make OMP the only visible runtime in product language.
- Keep GenericAgent fallback hidden behind env/dev mode.
- Update `/runtimes`, provider metadata, and docs to express OMP-primary.
- Start recording OMP runtime events with provider/task provenance.

### Phase 2: Memory Service

- Extract memory hydration/candidate/approval logic from `app.py`.
- Generate per-task OMP context-pack artifacts.
- Add typed OMP host tools for memory context and memory candidates.

### Phase 3: Scheduler Service

- Make scheduled agent work explicitly dispatch to OMP by default.
- Show OMP run provenance, approval state, and artifact refs in scheduler views.
- Preserve idempotency and `agenttask.v2`.

### Phase 4: Worker Runtime

- Execute GA-TUI-managed workers through OMP structured runtime requests.
- Add per-worker OMP model/settings/context profiles.
- Normalize OMP streams into worker chat, artifacts, task ledger, traces, and memory candidates.

### Phase 5: GenericAgent Quarantine

- Keep GenericAgent runtime only as a fallback until OMP-first parity passes.
- Remove GenericAgent-specific prompt/tool injection from the normal product path.
- Keep compatibility shims only where required by old tests or migration.

## MVP Scope

First implementation should be **OMP-first Memory + Scheduling Foundation**, not model/settings sync.

### In Scope

- Define provider-neutral `RuntimeTaskRequest` / `RuntimeTaskEvent` data shapes.
- Generate OMP context-pack artifacts for main tasks and worker/subagent tasks.
- Add typed OMP host tools for read-only control-plane state and memory candidate submission.
- Route scheduler due agent tasks into OMP with explicit provider provenance.
- Record OMP runtime events into traces/artifacts.
- Preserve current user-visible behavior while shifting internals toward OMP-first services.

### Out of Scope

- Mutating system `~/.omp/agent`.
- Direct long-term memory writes from OMP.
- Removing GenericAgent fallback in the first MVP.
- Importing unknown OMP-native agents or providers as trusted GA-TUI workers.
- Rewriting the entire `app.py` monolith in one task.
- Syncing every session/task/memory/artifact surface at once.

## Acceptance Criteria

- [ ] OMP remains the default runtime path.
- [ ] Embedded OMP still uses only GA-TUI-owned runtime files for active config.
- [ ] GenericAgent runtime remains available as fallback during migration.
- [ ] OMP task execution can be represented as structured runtime request/event records.
- [ ] OMP receives memory through generated context-pack artifacts.
- [ ] OMP memory candidates are routed through GA-TUI approval flow.
- [ ] Scheduler agent-task dispatch defaults to OMP and records provider provenance.
- [ ] OMP task results create artifact refs, task ledger rows, and traces.
- [ ] No OMP path bypasses approvals, single-writer locks, or long-term memory governance.
- [ ] Specs are updated for the OMP-first orchestration contracts.

## Definition of Done

- Tests added or updated for runtime request/event contracts, OMP memory candidate flow, scheduler dispatch provenance, and artifact/trace output.
- `python3 scripts/check_policy_gates.py`, compile checks, `git diff --check`, and `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` pass.
- Real TUI + OMP smoke verifies a scheduled or delegated OMP task goes through memory/context, task ledger, artifact, and trace paths.
- Docs/specs updated if behavior changes.
- Rollback remains possible through `GA_TUI_RUNTIME_PROVIDER=genericagent` until fallback is intentionally deprecated.

## Technical Notes

- Relevant files: `src/ga_tui/app.py`, `src/ga_tui/ohmypi_provider.py`, `src/ga_tui/genericagent_provider.py`, `src/ga_tui/runtime.py`, `src/ga_tui/scheduler.py`, `src/ga_tui/control_protocol.py`.
- Relevant docs/specs: `docs/runtime-provider-control-plane.md`, `docs/agent-harness-architecture.md`, `.trellis/spec/backend/agent-control-protocol.md`.
- Detailed analysis: `research/omp-first-orchestration-analysis.md`.
