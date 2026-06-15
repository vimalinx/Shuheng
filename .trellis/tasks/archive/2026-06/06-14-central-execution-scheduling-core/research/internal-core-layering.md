# Internal Core Layering Research

## Question

How should GenericAgent-TUI integrate the useful GenericAgent and Oh My Pi cores while moving toward a maintained central execution and scheduling layer owned by this repo?

## Current GA-TUI Evidence

- `src/ga_tui/runtime.py` already defines provider-neutral `RuntimeTaskRequest`, `RuntimeTaskEvent`, `RuntimeProviderSpec`, `RuntimeAdapter`, and `RuntimeRegistry`.
- `src/ga_tui/scheduler.py` is already partially extracted from `app.py`; it owns schedule registries, schedule run rows, due checks, idempotency keys, and dispatch hooks through `SchedulerRuntime`.
- `src/ga_tui/app.py` still owns too many unrelated responsibilities: TUI state, rendering, model manager, context packs, memory candidates, approvals, governance registry, runtime registry construction, OMP host tool definitions, host tool dispatch, task ledger writes, subagent lifecycle, queue consumption, and scheduler wiring.
- `docs/runtime-provider-control-plane.md` states the intended boundary: GA-TUI owns orchestration/governance/ledgers/approval/memory/scheduler/model routing; runtime providers own narrow execution.
- `docs/agent-harness-architecture.md` states the larger target: strong orchestrator, restricted subagents, shared ledgers, artifact refs, single-writer enforcement, human approval gates, auditable communication, external long-term memory, context hydration, recovery, eval, A2A/MCP compatibility.

## GenericAgent Evidence

- `/home/vimalinx/Programs/GenericAgent/agentmain.py` exposes `GenericAgent` with a task queue, streaming output queue, model switching, abort handling, session log path, and global-memory prompt injection.
- `/home/vimalinx/Programs/GenericAgent/ga.py` contains the old core strengths: tool handler methods, browser/web tools, file tools, working memory checkpointing, plan-mode guardrails, turn-end callbacks, long-term-memory update workflow, and repeated-turn danger prompts.
- GenericAgent's memory flow is direct and mature but too coupled to prompt/tool behavior for unrestricted reuse inside GA-TUI. It should be mined for semantics and candidate extraction patterns, not kept as the governance owner.

## Oh My Pi Evidence

- The installed OMP source entry is `/home/vimalinx/.bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/src/cli.ts`.
- OMP RPC is in `src/modes/rpc/`, especially `rpc-mode.ts`, `rpc-types.ts`, and `host-tools.ts`.
- OMP RPC already supports `prompt`, `steer`, `follow_up`, `abort`, `new_session`, state queries, model switching, thinking level, compaction, bash execution, session export/switch/branch/messages, extension UI, host tools, and host URI schemes.
- OMP `AgentSession` in `src/session/agent-session.ts` is the real local execution/session abstraction. It owns event subscription, session persistence, model/thinking state, compaction, bash execution, session switching, branching, async jobs, tool discovery, LSP, skills/extensions, and provider streaming.
- OMP's `AsyncJobManager` provides useful bounded async job semantics with owner scoping, cancellation, delivery retry, retention, and max-running limits.

## Recommended Ownership Model

GA-TUI should own a new central core layer and treat both runtimes as replaceable execution providers.

- GA-TUI core owns: task execution graph, schedule registry, run ledger, dispatch policy, approval gates, single-writer lock, context-pack construction, artifact refs, trace/eval, memory candidates, runtime registry, provider selection, and TUI-facing state snapshots.
- OMP owns: local model/tool execution, streaming, session persistence, compaction, LSP/tool discovery, extension UI, host tool calls, branch/resume, and low-level runtime process state.
- GenericAgent owns: fallback Python runtime compatibility and serves as a source for memory/working-checkpoint semantics.
- The TUI owns UI rendering only; it should call a service facade instead of directly mutating ledgers/runtime/scheduler state.

## Proposed Layer Split

1. `ga_tui.core.contracts`
   - Pure dataclasses/protocols for task requests, runtime events, execution runs, host tools, approvals, artifacts, memory candidates, schedules, and service results.

2. `ga_tui.core.stores`
   - JSONL/atomic file access wrappers for ledgers, traces, artifacts, approvals, memory candidates, schedules, and runtime registry.

3. `ga_tui.core.context`
   - Context pack and memory hydration generation, including secret/standard separation.

4. `ga_tui.core.governance`
   - Policy gates, risk classification, single-writer lock, approval queue, memory candidate validation, and provenance.

5. `ga_tui.core.executor`
   - Central execution service that accepts a `CoreTaskRequest`, runs gates, reserves run ids, writes ledgers/artifacts/traces, dispatches to provider adapters, and normalizes events/results.

6. `ga_tui.core.scheduler`
   - Move the current scheduler into this layer and make it schedule `CoreTaskRequest` rather than directly calling subagent-specific app functions.

7. `ga_tui.providers`
   - OMP/GenericAgent/Codex/A2A adapters. Providers must not own long-term memory, approvals, task ledger policy, or schedule registry.

8. `ga_tui.tui`
   - Rendering, commands, forms, panels, and state projection. It should not be the primary owner of execution invariants.

## Feasible Approaches

### Approach A: Extract GA-TUI Python core first, keep OMP over RPC

This is the recommended path.

- Add `src/ga_tui/core/` modules in Python.
- Move existing contracts and app-owned service logic behind stable Python APIs.
- Keep OMP as RPC runtime provider with isolated config/session dirs.
- Later optionally vendor or pin OMP source, but do not couple core governance to TypeScript internals.

Pros:
- Lowest risk and fastest path to a maintainable center.
- Preserves current working OMP integration.
- Makes `app.py` smaller without rewriting runtime transport.
- Keeps governance in one Python-owned layer.

Cons:
- OMP internals still live outside this repo unless vendoring/pinning is added later.
- Some capabilities remain limited to OMP RPC shape.

### Approach B: Vendor OMP execution source under GA-TUI and wrap it

- Copy or subtree a minimal OMP package/runtime source into this repo.
- Patch the OMP runtime to expose GA-TUI-specific task/run hooks directly.

Pros:
- Maximum control over OMP internals.
- Easier to modify OMP session/resume/tool behavior deeply.

Cons:
- High maintenance cost.
- Cross-language build and dependency management becomes part of GA-TUI.
- More likely to drift from upstream OMP fixes.
- Riskier before the Python governance boundary is clean.

### Approach C: Build a language-neutral daemon core

- Define a local daemon/API that owns execution/scheduler/governance.
- TUI, OMP, GenericAgent, Codex, A2A, and mobile clients all connect to the daemon.

Pros:
- Strongest long-term product architecture.
- Good for phone control, remote runners, and multi-client operation.

Cons:
- Too big for first refactor.
- Requires auth, lifecycle, persistence, daemon upgrade, and compatibility work.
- Should happen after the Python core contracts stabilize.

## Initial Recommendation Before User Correction

Use Approach A for MVP, but design module boundaries so Approach C remains possible.

Do not start by copying all OMP or GenericAgent code into GA-TUI. First extract the center of gravity from `app.py` into a core Python control plane:

- `CoreExecutionService`
- `CoreSchedulerService`
- `CoreGovernanceService`
- `CoreContextService`
- `CoreStore`
- provider adapters for `ohmypi` and `genericagent`

Then move one lane at a time:

1. OMP host tools and runtime registry.
2. Runtime task request/event dispatch.
3. Subagent task start/queue/ledger path.
4. Scheduler dispatch path.
5. Memory candidate and approval service.
6. Session resume/history projection.

## Risks

- `app.py` is very large; large-bang refactors will break TUI behavior. Migrate lane-by-lane with compatibility wrappers.
- Secret-context paths must remain isolated from normal traces and normal artifacts.
- OMP host tools must remain read-only or proposal-only unless GA-TUI policy explicitly approves.
- Scheduler must keep idempotency and resolved provider provenance.
- Provider selection must stay explicit; do not infer runtime from natural-language names.
- Durable records must not store raw prompts or secrets.

## Suggested MVP Boundary

The first implementation should not change user-facing behavior. It should create the core module shape and move enough behavior to prove the architecture:

- Extract shared runtime contracts and a `CoreExecutionService` facade.
- Extract OMP host tool definitions/handler routing behind a service boundary.
- Extract runtime registry construction behind a service boundary.
- Wire existing `app.py` to call those services.
- Keep all existing tests green and add regression checks that the old public functions still work.

## Superseded User-Corrected Direction

The user rejected the black-box/provider-first framing and wants to modify OMP code directly because OMP is open source and already a better agent runtime foundation. The local installed OMP package metadata reports:

- package: `@oh-my-pi/pi-coding-agent`
- version: `15.10.8`
- license: `MIT`
- repository: `https://github.com/can1357/oh-my-pi`, directory `packages/coding-agent`

The revised recommendation is therefore:

- Do not modify the global Bun-installed OMP package in place.
- Create or attach a project-owned OMP source/runtime path.
- Modify that OMP code directly for GA-TUI integration hooks.
- Route GA-TUI to the project-owned OMP runtime once available.
- Keep GenericAgent as fallback and as a source of memory/working-checkpoint/scheduler semantics to implement in the GA-TUI control plane.

This direction is now superseded by the plugin/control-plane direction below. It remains useful only as fallback evidence that a project-owned OMP fork is legally and technically possible if plugin APIs prove insufficient.

## Second User-Corrected Direction: GA-TUI Control Plane plus OMP Plugin

The user then refined the direction again: instead of making OMP itself the system owner, write an OMP plugin and let GA-TUI centrally maintain project memory, organization, scheduling, and governance. OMP, Pi, Codex, Claude Code, and later agent providers should all be clients of the same GA-TUI-owned center.

This is the better architectural fit:

- GA-TUI remains the source of truth for durable memory, project organization, task ledgers, schedule registries, approvals, artifacts, traces, and provider routing.
- OMP remains a strong execution/session runtime, but it consumes GA-TUI context through plugin/custom-tool/hook surfaces.
- Codex and Claude Code can later consume the same GA-TUI service contracts instead of each runtime inventing its own memory store.
- Forking OMP stays available only if its plugin surface cannot express a required integration.

## OMP Plugin Surface Evidence

Local OMP source exposes enough integration surface for a first bridge:

- `src/commands/plugin.ts` supports `install`, `uninstall`, `list`, `link`, `doctor`, `features`, `config`, `enable`, `disable`, `marketplace`, `discover`, and `upgrade`.
- `src/commands/install.ts` routes local paths to plugin link behavior, so a GA-TUI-managed local plugin can be linked without editing the global OMP install.
- `src/extensibility/plugins/types.ts` supports package manifest fields for `tools`, `hooks`, `extensions`, `commands`, `features`, and plugin settings.
- `src/extensibility/custom-tools/types.ts` supports LLM-callable custom tools with typed parameters, approval metadata, session callbacks, UI rendering, and access to session/model/cwd context.
- `src/extensibility/hooks/types.ts` supports lifecycle and session event handlers with controlled UI/session/model context.
- `src/extensibility/extensions/types.ts` exposes a broader extension surface for lifecycle events, tools, commands, UI widgets, status lines, and model/session interaction.
- `src/memory-backend/types.ts` has memory hooks for developer-instruction injection, pre-start prompt injection, compaction context, stats, diagnostics, enqueue, and clear.

## Revised MVP Strategy

1. Extract the GA-TUI control-plane boundary first.
   - Define a small agent-facing service/contract for memory/context read and governed proposal submission.
   - Keep the first version local and project-owned; do not require a public remote daemon yet.
   - Durable records should use schema-bound objects, previews, refs, and provenance, not raw prompt dumps.

2. Create a project-managed OMP plugin/extension package.
   - Link it into OMP through project/local plugin installation rather than mutating global OMP code.
   - Provide custom tools such as `ga_tui_context_get`, `ga_tui_memory_candidate_submit`, and later `ga_tui_task_propose` / `ga_tui_schedule_propose`.
   - Use hooks/extensions for turn-start context injection and turn-end candidate/progress submission where practical.

3. Keep provider authority bounded.
   - OMP plugin tools can read GA-TUI context and submit proposals.
   - GA-TUI validates proposals, applies approval gates, writes task/memory/schedule ledgers, and records traces.
   - OMP must not directly write long-term memory, approvals, schedules, or ledgers.

4. Preserve future adapters.
   - Codex adapter and Claude Code adapter should consume the same GA-TUI service contracts.
   - Avoid OMP-specific schema names in the central API.
   - Keep provider metadata explicit so the scheduler records resolved provider provenance.

5. Use OMP fork/core edits only as an escape hatch.
   - If plugin hooks cannot inject context at the right time or cannot expose required tool behavior, consider a minimal project-owned OMP fork.
   - Any fork must stay isolated from the user's global OMP and retain a rollback path.
