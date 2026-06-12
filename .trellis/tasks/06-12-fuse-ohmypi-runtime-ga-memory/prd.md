# Fuse Oh My Pi Runtime With GA Memory

## Goal

Create an experimental branch that makes Oh My Pi the primary execution runtime inside GenericAgent-TUI while preserving the useful GenericAgent/GenericAgent-TUI memory and governance mechanisms. The first implementation should prove the seam quickly: OMP runs the agent work, and GA/TUI supplies a bounded memory/context append block plus keeps memory writes as governed candidates.

## What I Already Know

- User direction: directly fuse the systems, open a branch, try replacing the runtime, and move the GA memory mechanism into OMP.
- Current branch is `experiment/ohmypi-runtime-memory`; base branch is `main`.
- Existing runtime registry already includes both `genericagent` and `ohmypi`.
- Current OMP provider uses `omp --mode rpc` and translates JSONL streaming into GenericAgent-style queue events.
- OMP is currently opt-in with `GA_TUI_RUNTIME_PROVIDER=ohmypi`; GenericAgent remains default on `main`.
- OMP supports `--append-system-prompt <text-or-file>`, which can append extra system prompt content while preserving OMP's defaults.
- GenericAgent injects memory through `get_global_memory()`, sourced from `memory/global_mem_insight.txt` and fixed memory structure text.
- GenericAgent-TUI already has context packs and approval-gated memory candidates.

## Assumptions

- This task is an experiment branch spike, not a mainline hard migration.
- We should default to `ohmypi` only on this branch while keeping a clear escape hatch to `genericagent`.
- The first version should inject GA/TUI memory into OMP through OMP's supported prompt customization surface, not by patching OMP internals.
- Memory writes should stay governed by GA/TUI memory candidates and approval gates.
- OMP host tools, host URI schemes, and internal subagents should remain provider-owned until a later governance-mapping task.

## Research References

- [`research/runtime-memory-architecture.md`](research/runtime-memory-architecture.md) - wrapper-level OMP default plus GA/TUI memory append prompt is the fastest low-risk fusion seam.
- `.trellis/tasks/archive/2026-06/06-11-research-ohmypi-integration/research/integration-analysis.md` - prior source comparison and RPC recommendation.
- `docs/runtime-provider-control-plane.md` - TUI as control plane, providers as bounded execution.
- `.trellis/spec/backend/agent-control-protocol.md` - Oh My Pi provider boundary and governance constraints.

## Requirements

- On this experiment branch, the default runtime provider should be `ohmypi` unless explicitly overridden.
- A user/developer must still be able to force `genericagent` with an environment variable or equivalent explicit setting.
- `OhMyPiRuntimeAdapter` should pass a generated GA/TUI memory append prompt file into OMP startup.
- The generated memory append prompt should be bounded, readable, and safe to inject into OMP's system prompt.
- The memory append prompt should include the strongest useful GA/TUI memory layers available without copying raw logs or secrets.
- The memory append prompt should reference source paths/artifact refs when possible.
- After an OMP prompt finishes, the TUI should create a governed memory-candidate signal from durable-looking output instead of directly writing long-term memory.
- OMP memory candidates must reuse the existing TUI candidate/approval path or an equivalent JSONL record shape, not bypass policy gates.
- OMP prompt execution should continue to stream through the existing TUI display queue.
- Missing `omp` should still degrade into a queue error instead of crashing the TUI.
- Tests/checks should prove default runtime selection, command construction, memory file generation, post-run candidate signaling, and existing OMP queue mapping.

## Acceptance Criteria

- [x] `agent_runtime_registry().to_record()["default_provider_id"]` is `ohmypi` on this experiment branch when no runtime override is set.
- [x] Setting `GA_TUI_RUNTIME_PROVIDER=genericagent` selects GenericAgent.
- [x] OMP command construction includes `--append-system-prompt <generated-memory-file>` by default in this branch.
- [x] The generated memory file includes a clear `GA/TUI Memory Guidance` block with bounded content and source refs.
- [x] The generated memory file excludes raw logs, secrets, direct credential-looking values, and unrelated session dumps.
- [x] A completed OMP prompt can enqueue or record a governed memory candidate signal with an evidence/source reference.
- [x] Memory candidate signaling is skipped for empty, secret-looking, or too-short outputs.
- [x] Existing fake RPC queue mapping tests still pass.
- [x] `python3 -m py_compile src/ga_tui/app.py src/ga_tui/ohmypi_provider.py src/ga_tui/runtime.py scripts/check_policy_gates.py` passes.
- [x] `python3 scripts/check_policy_gates.py` passes.
- [x] `git diff --check` passes.
- [x] Architecture baseline comparison shows the experiment keeps TUI as Orchestrator and OMP as bounded execution runtime.

## Definition Of Done

- Branch metadata is recorded on the Trellis task.
- PRD is updated with the chosen MVP scope.
- Relevant Trellis spec context is loaded before implementation.
- Implementation is covered by policy-gate checks.
- Runtime behavior is smoke-tested without requiring real model calls.
- Changes are committed on `experiment/ohmypi-runtime-memory`.

## Out Of Scope

- Vendoring or editing Oh My Pi source.
- Writing directly into Oh My Pi's native memory backend.
- Enabling OMP host tools or host URI schemes.
- Mapping OMP internal subagents into first-class TUI subagents.
- Replacing the entire TUI runtime API with a provider-neutral work-order API in this task.
- Changing production/main default runtime before this branch is validated.

## Technical Notes

- Likely files: `src/ga_tui/runtime.py`, `src/ga_tui/ohmypi_provider.py`, `src/ga_tui/app.py`, `scripts/check_policy_gates.py`, `.trellis/spec/backend/agent-control-protocol.md`.
- Useful existing memory functions: `ga.get_global_memory()`, `memory_hydration_pack()`, `build_context_pack()`, `build_memory_candidate()`, `queue_curated_memory_candidate()`.
- OMP prompt customization docs recommend `APPEND_SYSTEM.md` or `--append-system-prompt` for adding instructions without replacing defaults.
- The current OMP provider deliberately avoids importing `app.py`; memory prompt generation should respect that boundary by passing plain data/path configuration into the provider instead of importing mutable TUI state.

## Decisions

- Scope decision: implement startup GA/TUI memory injection plus post-run governed memory candidate signaling in this experiment branch.

## Verification Notes

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/ohmypi_provider.py src/ga_tui/runtime.py src/ga_tui/scheduler.py scripts/check_policy_gates.py` passed.
- `python3 scripts/check_policy_gates.py` passed.
- `python3 -m compileall -q src scripts` passed.
- `git diff --check` passed.
- `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` passed.

## Architecture Baseline Comparison

- This experiment moves closer to `docs/agent-harness-architecture.md`: GenericAgent-TUI stays the strong Orchestrator and still owns provider selection, task/schedule registries, approval gates, artifact refs, and long-term memory governance.
- Oh My Pi is used as a bounded execution runtime through the provider adapter and RPC process boundary, not as an unchecked replacement for the TUI control plane.
- Memory integration follows the baseline rule that workers do not write long-term memory directly: OMP receives bounded GA/TUI memory guidance at startup and only emits memory candidate signals for TUI-side approval.
- Remaining gaps are intentionally out of scope: OMP host tools are not mapped through TUI approval gates yet, OMP internal subagents are not first-class TUI ledger rows, and the runtime API still carries GenericAgent-shaped compatibility surfaces.
