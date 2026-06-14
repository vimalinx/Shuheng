# Internal Current State: OMP + GenericAgent Strengths

## Existing OMP Integration

- `agent_runtime_registry()` registers both `genericagent` and `ohmypi`; `GA_TUI_RUNTIME_PROVIDER` defaults to `ohmypi` on this experiment branch and can be set to `genericagent` for fallback.
- OMP runs through `OhMyPiRuntimeAdapter` and `OhMyPiRpcAgent`, presenting the GenericAgent-shaped `put_task()`/queue interface consumed by existing TUI paths.
- OMP uses an isolated GA-TUI-owned agent directory under `${AGENT_HARNESS_DIR}/runtime/ohmypi/agent` via `PI_CODING_AGENT_DIR`, so system `~/.omp/agent` is not the active embedded runtime directory.
- GA-TUI `/model` entries are projected into isolated OMP `config.yml` and `models.yml`. API keys are passed through child-process env vars instead of being written into generated OMP files.
- OMP receives a bounded `GA/TUI Memory Guidance` append prompt generated from GA-TUI memory sources.
- OMP has two app-injected host tool surfaces: `ga_tui_query` for read-only governance inspection and `ga_tui_propose` for bounded `ga_control` or `memory_candidate` proposals.

## GenericAgent Strengths Worth Preserving

- Strong TUI/GenericAgent control plane: sessions, sidebar, commands, model manager, runtime selection, and settings.
- Governed subagent lifecycle: persistent vs temporary agents, roles, policy gates, task queueing, artifacts, traces, and result bus.
- Explicit `ga-control.v2` and `agenttask.v2` orchestration contract.
- Memory governance: context pack hydration, memory candidate queue, approvals, and no direct long-term writes from workers.
- Query tools: agent/task/approval/artifact/capability/schedule state can be inspected before mutation.
- Scheduler dispatch through `agenttask.v2` instead of bypassing ledgers.
- Architecture baseline: one strong Orchestrator, bounded workers, explicit ledgers, artifact refs, approval gates, and auditable communication.

## Current Gaps / Candidate Work

- OMP sees GA-TUI memory mostly as append-prompt guidance plus generic host tools; it does not yet receive a structured per-turn context pack assembled from the same layers used for GA subagents.
- OMP host tools are currently coarse (`ga_tui_query`/`ga_tui_propose`), not a typed parity surface matching GenericAgent's query tool names.
- OMP runtime sessions are isolated and configured, but TUI does not yet expose rich OMP session history/continue/resume controls.
- Per-subagent runtime/model settings are not fully first-class for OMP-backed subagents.
- Approval UI interactions from OMP are intentionally cancelled or converted into GA-TUI policy flow; host URI schemes and TUI approval mapping remain out of scope until explicitly designed.
- Provider-owned OMP subagents are advertised in metadata, but first-class mapping to GA-TUI's subagent ledger is not designed.

## Feasible Approaches

### Approach A: GA-TUI Control Plane Parity Around OMP (Recommended)

- Keep governance in GA-TUI.
- Add structured OMP context packs, typed host tools, richer provider metadata, and per-agent OMP settings.
- Treat OMP as the execution engine and GA-TUI as the orchestrator/policy/memory owner.
- Best fit for current architecture and lowest risk to system OMP.

### Approach B: Patch OMP Native Runtime More Deeply

- Add GA-like memory, task ledger, and agent governance concepts directly inside OMP's own runtime.
- Could make standalone OMP stronger outside GA-TUI.
- Higher risk: duplicates GA-TUI governance, increases drift, and may require upstream OMP codebase changes.

### Approach C: Bidirectional Sync Layer

- Keep both systems' native strengths and sync sessions, memory candidates, tasks, and artifacts.
- Most flexible long-term if OMP is used standalone and inside TUI.
- Highest complexity: conflict resolution, provenance, idempotency, and security boundaries are harder.

## Recommendation

Start with Approach A as the MVP: make embedded OMP feel like it has GA's useful orchestration, memory, settings, and safety features through GA-TUI-owned structured context and governed tools. Defer native OMP mutation and bidirectional sync until a narrower use case proves they are needed.
