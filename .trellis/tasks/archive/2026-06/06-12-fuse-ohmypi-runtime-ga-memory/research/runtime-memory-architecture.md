# Runtime And Memory Fusion Research

## Question

How should GenericAgent-TUI fuse Oh My Pi as the main execution runtime while preserving the useful GenericAgent memory and orchestration mechanisms?

## Current Evidence

- `docs/runtime-provider-control-plane.md` defines the intended split: GenericAgent-TUI owns orchestration, ledgers, approvals, artifacts, model routing, and scheduled work; runtime providers accept bounded work, run it, stream events, and expose status/artifact refs.
- `src/ga_tui/runtime.py` still has a small `RuntimeAdapter` interface centered on `create_agent()`, `prepare_agent()`, `start_agent()`, `abort_agent()`, `put_task()`, and `current_model()`.
- `src/ga_tui/ohmypi_provider.py` currently adapts `omp --mode rpc` into the existing GenericAgent-shaped queue contract, including compatibility attributes such as `llmclient.backend`, `task_queue.unfinished_tasks`, and `get_llm_name()`.
- `.trellis/spec/backend/agent-control-protocol.md` requires the Oh My Pi provider to stay provider-local, not import curses/app state, and not enable host tools or auto-approval until TUI policy gates can audit them.
- The prior Oh My Pi integration research concluded that RPC is the correct first integration surface because it exposes prompt, abort, state, models, sessions, host tools, host URIs, and subagent frames across the Python/Bun boundary.

## Memory Evidence

- GenericAgent injects global memory through `ga.get_global_memory()`: it reads `memory/global_mem_insight.txt`, adds a fixed structure prompt, and tells the agent that memory lives under `../memory`.
- GenericAgent's memory SOP defines an L1/L2/L3/L4 stack: `global_mem_insight.txt`, `global_mem.txt`, task-specific `memory/` files, and raw session history under `memory/L4_raw_sessions`.
- GenericAgent-TUI already has a governed memory path: context packs, `memory_hydration_pack()`, `build_context_pack()`, `build_memory_candidate()`, approval-gated `queue_curated_memory_candidate()`, artifacts, traces, and memory candidate JSONL records.
- Oh My Pi already has an autonomous memory backend of its own. Its docs describe project-scoped `MEMORY.md`, `memory_summary.md`, generated `skills/`, memory injection into the system prompt, and `memory://` read URLs.
- Oh My Pi supports `--append-system-prompt <text-or-file>` and project/user `APPEND_SYSTEM.md`; docs say this appends a block while preserving the default prompt and dynamic project/environment footer.

## Integration Options

### Option A: Fast wrapper-level fusion

Make Oh My Pi the experiment branch's default runtime provider and inject a generated GA/TUI memory block through `--append-system-prompt <file>` when the OMP RPC process starts.

Pros:

- Minimal cross-language work.
- Preserves Oh My Pi defaults and tools.
- Keeps GA/TUI governance outside OMP.
- Testable with fake process command assertions.

Cons:

- Memory is injected at process start, not dynamically updated mid-session.
- Does not yet use Oh My Pi's native memory store.
- Still leaves some GenericAgent-shaped compatibility in the TUI.

### Option B: Native OMP memory backend bridge

Write or configure Oh My Pi's local memory backend to import GA/TUI memory summaries as OMP memory artifacts.

Pros:

- Makes memory visible through OMP's `memory://` mechanisms.
- Aligns with OMP's native memory UX.

Cons:

- Requires TypeScript/Bun-side changes or deeper OMP config knowledge.
- Higher risk of fighting OMP's own consolidation pipeline.
- Slower path to prove runtime replacement value.

### Option C: Full runtime-neutral TUI refactor first

Replace GenericAgent-shaped hot paths with provider-neutral work-order APIs before changing defaults.

Pros:

- Architecturally clean.
- Reduces future compatibility shims.

Cons:

- Too large for an experimental branch spike.
- Delays validating whether OMP is materially better as the runtime.

## Recommendation

Implement Option A first on `experiment/ohmypi-runtime-memory`:

- Default the runtime provider to `ohmypi` on this experiment branch.
- Preserve an escape hatch to run `genericagent`.
- Generate a bounded GA/TUI memory append prompt file under the harness/runtime area.
- Pass that file to OMP through `--append-system-prompt`.
- Keep memory writes governed by GenericAgent-TUI memory candidates and approval gates, not by direct OMP writes.

Then validate whether OMP works better as the execution runtime before investing in Option B or C.

## Suggested MVP Boundaries

- No vendoring or patching Oh My Pi source.
- No direct writes into OMP's native memory SQLite/summary store.
- No host tool bridge yet.
- No OMP internal subagent ledger merge yet.
- No automatic approval or yolo mode.

