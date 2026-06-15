# Central Agent Control Plane and OMP Plugin Bridge

## Goal

Create a GA-TUI-owned central control plane for project memory, organization, scheduling, approvals, traces, artifacts, and provider routing, then expose that control plane to multiple agent clients. OMP should be the first high-quality client through a plugin/extension bridge, not the owner of memory or governance. Codex, Claude Code, Pi/OMP, and future agents should eventually consume the same GA-TUI-managed context and governed tools.

## What I Already Know

- The user wants GA-TUI to be the self-owned center for memory, project organization, execution scheduling, and governance rather than letting OMP or GenericAgent define the system's architecture.
- The previous OMP-first work made OMP the default runtime on `experiment/ohmypi-runtime-memory`, with GenericAgent kept as fallback through `GA_TUI_RUNTIME_PROVIDER=genericagent`.
- GA-TUI already has provider-neutral runtime contracts in `src/ga_tui/runtime.py`.
- GA-TUI already has a partially extracted scheduler in `src/ga_tui/scheduler.py`.
- `src/ga_tui/app.py` is still the main monolith and owns too much business logic beyond rendering.
- OMP's real local strength is `AgentSession` plus RPC: execution, streaming, sessions, compaction, model/tool state, host tools, host URI, LSP/tool discovery, extension UI, and async jobs.
- GenericAgent's real local strength is memory/working checkpoint semantics, tool-loop heuristics, plan-mode guardrails, and turn-end memory/update prompts.
- System OMP under `~/.omp/agent` must not be mutated; GA-TUI should continue using isolated runtime files under a GA-TUI-owned runtime directory.
- The installed OMP package is `@oh-my-pi/pi-coding-agent@15.10.8`; local `package.json` reports `license: MIT`, so a modified fork/bundle is legally feasible as a fallback if plugin APIs are insufficient.
- OMP has a real plugin/extension surface: `omp plugin`, `omp install`, project/user plugin scopes, extension entry points, hooks, custom tools, custom commands, and memory backend hooks.
- The user now prefers an OMP plugin/extension bridge because GA-TUI should centrally maintain memory and project organization for OMP, Codex, Claude Code, Pi, and other agents.

## Assumptions

- GA-TUI should be the product/control plane and the source of truth for cross-agent project memory, organization, scheduling, approvals, ledgers, artifacts, and traces.
- OMP should stay the best local execution/session runtime, but it should consume GA-TUI context through a plugin/extension bridge rather than owning GA-TUI memory and governance.
- GenericAgent should be mined for memory, working-checkpoint, long-task, and scheduler ideas, then those semantics should be implemented in GA-TUI core services and exposed to all providers.
- Forking or modifying OMP core remains a fallback only if the plugin/extension surface cannot support a required integration point.

## Requirements

- Define a GA-TUI central control plane maintained by this project, not by any one runtime provider.
- Separate GA-TUI UI rendering from core governance, memory, scheduling, stores, and provider-adapter contracts.
- Keep OMP as the default execution runtime for now, but integrate it through a project-managed plugin/extension bridge rather than mutating the user's global OMP.
- Keep GenericAgent as a fallback provider.
- Move the architecture closer to the baseline in `docs/agent-harness-architecture.md`.
- Preserve approval gates, single-writer policy, task ledgers, artifacts, traces, memory candidates, scheduler idempotency, and provider provenance.
- Avoid a big-bang rewrite; migrate one execution lane at a time with compatibility wrappers.
- Do not introduce direct writes from OMP, Codex, Claude Code, or other providers into long-term memory, approvals, schedules, or ledgers.
- Expose GA-TUI memory/context to agent clients through explicit read/proposal APIs rather than raw file scraping.
- Let agent clients submit memory candidates, task proposals, and schedule proposals through GA-TUI-governed schemas.
- Build OMP plugin support as the first client integration, using OMP custom tools/hooks/extensions where possible.
- Design the bridge so Codex and Claude Code adapters can later use the same GA-TUI service contracts.

## Acceptance Criteria

- [x] A GA-TUI central control-plane strategy exists and is documented.
- [x] A first agent-facing service/contract exists for memory/context read and governed proposal submission.
- [x] An OMP plugin/extension packaging strategy exists that does not mutate system OMP in place.
- [x] The first implementation wires at least one non-trivial OMP plugin capability to GA-TUI-owned context or proposals.
- [x] Existing OMP runtime behavior remains compatible with current tests.
- [x] Existing scheduler behavior keeps idempotency keys and resolved provider provenance.
- [x] Existing memory candidate and approval boundaries are preserved.
- [x] Secret-context runtime events and raw prompts remain excluded from normal durable trace records.
- [x] `python3 -m compileall -q src scripts` passes.
- [x] `python3 scripts/check_policy_gates.py` passes.
- [x] `git diff --check` passes.
- [x] Architecture baseline comparison says the change moves closer to the target.

## Definition of Done

- Tests added or updated for the extracted core boundary.
- Lint/type/compile checks pass for changed Python modules.
- Runtime/provider docs or Trellis backend spec updated when contracts move.
- Migration preserves current user-facing behavior.
- Rollback is straightforward because compatibility wrappers remain in `app.py`.

## Out of Scope

- Editing the user's global Bun OMP install in place.
- Making OMP, Codex, Claude Code, or any provider the source of truth for long-term memory or governance.
- Rewriting the TUI renderer.
- Replacing the OMP RPC protocol.
- Removing GenericAgent fallback.
- Remote A2A/MCP worker implementation.
- Multi-client daemon mode.
- Direct long-term memory writes by runtime providers.
- Forking OMP core unless plugin/extension APIs prove insufficient.

## Technical Approach

Selected MVP direction: build a GA-TUI central control plane and connect OMP through a project-managed plugin/extension bridge, while keeping the globally installed OMP untouched.

Target ownership:

- GA-TUI central control plane: project memory, project organization, context packs, scheduler, task/run ledgers, approval gates, artifacts, traces, provider registry, model routing, and single-writer enforcement.
- Agent bridge API: read-only context/memory retrieval, governed proposal submission, runtime metadata, task status, artifact refs, and health checks.
- OMP plugin/extension bridge: context injection, GA-TUI custom tools, memory candidate submission, task/schedule proposal tools, and status display inside OMP where useful.
- GA-TUI Python shell: TUI rendering, user commands, visible settings, approval UI, task/trace/artifact panels, and compatibility orchestration while the control plane is extracted.
- Shared contracts: runtime task/event envelopes, host-tool schemas, memory candidate schema, schedule/run schema, artifact refs, approval proposal schema, and agent-client service schemas.
- GenericAgent fallback: compatibility runtime plus source for memory/working-checkpoint/long-task semantics to implement in the GA-TUI control plane.

## Feasible Approaches

### Approach A: GA-TUI control plane plus OMP plugin bridge

Selected and recommended. Extract the GA-TUI-owned control plane first, expose a local agent-facing service/contract, and build an OMP plugin/extension as the first client. OMP remains the best execution runtime, but memory/governance/scheduling stay provider-neutral.

### Approach B: Vendor or fork OMP execution source

Fallback only. Maintain a project-owned OMP fork/bundle and modify OMP directly if plugin/extension hooks cannot provide required integration. This gives maximum control, but creates higher sync, build, and maintenance cost.

### Approach C: Build a language-neutral daemon core

Long-term target. Turn the GA-TUI control plane into a daemon/API used by the TUI, OMP plugin, Codex adapter, Claude Code adapter, phone clients, remote runners, A2A, and MCP. Too large for the first refactor, but the MVP contracts should not block it.

## Open Questions

- What should the MVP expose first: project memory/context reads, governed task/schedule proposals, or both?

## Decision (ADR-lite)

**Context**: The repo needs a self-owned memory, organization, scheduling, and governance center. OMP is a stronger execution runtime than GenericAgent and already exposes plugin/extension/custom-tool/hook surfaces. The user wants GA-TUI to maintain shared project memory and organization for multiple agents, with OMP as one client rather than the policy owner.

**Decision**: Use Approach A for the MVP: extract the GA-TUI central control plane and build an OMP plugin/extension bridge that consumes GA-TUI memory/context and submits governed proposals. Do not fork or modify OMP core unless the plugin API blocks a required capability.

**Consequences**: This preserves the strongest architectural boundary: GA-TUI owns durable memory and governance; providers are replaceable clients. It lowers OMP maintenance burden and makes Codex/Claude Code integration more natural. It may require a small local service/API and careful plugin packaging; if OMP's plugin surface is insufficient, a focused fork remains the escape hatch.

## Research References

- [`research/internal-core-layering.md`](research/internal-core-layering.md) - local code evidence and recommended layering.

## Technical Notes

- Relevant GA-TUI files: `src/ga_tui/app.py`, `src/ga_tui/runtime.py`, `src/ga_tui/scheduler.py`, `src/ga_tui/ohmypi_provider.py`, `src/ga_tui/genericagent_provider.py`, `src/ga_tui/control_protocol.py`.
- Relevant docs/specs: `docs/agent-harness-architecture.md`, `docs/runtime-provider-control-plane.md`, `.trellis/spec/backend/agent-control-protocol.md`.
- Relevant GenericAgent files: `/home/vimalinx/Programs/GenericAgent/agentmain.py`, `/home/vimalinx/Programs/GenericAgent/ga.py`.
- Relevant OMP files: `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/modes/rpc/rpc-mode.ts`, `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/modes/rpc/rpc-types.ts`, `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/session/agent-session.ts`, `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/async/job-manager.ts`.
- Relevant OMP plugin/extension files: `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/commands/plugin.ts`, `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/commands/install.ts`, `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/extensibility/plugins/types.ts`, `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/extensibility/extensions/types.ts`, `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/extensibility/custom-tools/types.ts`, `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/extensibility/hooks/types.ts`, `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/memory-backend/types.ts`.

## Implementation Notes

- Added `ga_tui.agent_bridge` as the first local agent-facing bridge API and CLI.
- Added repo-managed OMP plugin package under `integrations/omp-ga-tui-plugin`.
- Added plugin tools `ga_tui_context_get` and `ga_tui_memory_candidate_submit`.
- Kept memory writes candidate-only by routing through existing GA-TUI proposal and approval paths.
- Verified OMP plugin manifest with a temporary-HOME `omp plugin link --dry-run --json`, so the user's system OMP config was not modified.
