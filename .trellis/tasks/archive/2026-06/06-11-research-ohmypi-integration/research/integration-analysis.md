# Oh My Pi Integration Analysis

## Scope

This is a research-only comparison of Oh My Pi, GenericAgent, and the current
GenericAgent-TUI runtime-provider surface. No runtime code was changed.

## Source Checkouts

| Project | Source | Checkout | Commit |
| --- | --- | --- | --- |
| Oh My Pi | `https://github.com/can1357/oh-my-pi` | `/home/vimalinx/.cache/ga-tui-research/ohmypi-integration-20260611-140813/oh-my-pi` | `e6ee124d7cb59afa261cece022895b1a3f150b3a` |
| GenericAgent upstream | `https://github.com/lsdefine/GenericAgent.git` | `/home/vimalinx/.cache/ga-tui-research/ohmypi-integration-20260611-140813/GenericAgent-upstream` | `260027c946be2234e7bc4d15fe0c969f82167a52` |
| GenericAgent-TUI | local repo | `/home/vimalinx/Programs/GenericAgent-TUI` | `6e8cf48d06b9d6fa95d7ccce7f23330883c728f7` |

Local installed runtime check:

- `omp --version`: `omp/15.10.8`
- `bun --version`: `1.3.14`
- The cloned Oh My Pi package declares `@oh-my-pi/pi-coding-agent` version
  `15.11.0`, so implementation should smoke-test the installed binary before
  assuming cloned HEAD behavior.
- Minimal installed RPC smoke passed:
  `printf "" | omp --mode rpc --no-session --no-tools --no-lsp --no-skills --no-rules --cwd /home/vimalinx/Programs/GenericAgent-TUI`
  emitted `{"type":"ready"}` and exited with code `0`.

## Direct Evidence

Oh My Pi:

- `packages/coding-agent/package.json` exposes the `omp` binary and depends on
  the `pi-coding-agent`, `pi-agent-core`, `pi-ai`, `pi-tui`, and
  `@agentclientprotocol/sdk` packages.
- `packages/coding-agent/src/cli/args.ts` defines output modes
  `text`, `json`, `rpc`, `acp`, and `rpc-ui`.
- `docs/rpc.md` documents `omp --mode rpc` as a newline-delimited JSON protocol
  over stdio with ready frames, command responses, session events, extension UI
  requests, host tool calls, host URI calls, model commands, session commands,
  and subagent subscription commands.
- `packages/coding-agent/src/modes/rpc/rpc-types.ts` defines command types such
  as `prompt`, `abort`, `get_state`, `get_available_models`, `set_model`,
  `set_host_tools`, `set_host_uri_schemes`, `get_subagents`, and
  `get_subagent_messages`.
- `docs/sdk.md` says the SDK is the in-process Bun/Node integration surface and
  recommends RPC mode when cross-language or process isolation is needed.
- `docs/session.md` records file-backed JSONL sessions under `~/.omp/agent`.
- `docs/tools/task.md` shows Oh My Pi has its own background subagent system,
  async jobs, `agent://` and `history://` artifact URLs, isolation modes, and
  lifecycle handling.
- `docs/provider-streaming-internals.md` shows provider streams are normalized
  to `message_update` events and final agent/session events.
- `docs/models.md` shows Oh My Pi has a separate `~/.omp/agent/models.yml`
  provider/model registry with built-in and custom providers.
- `packages/coding-agent/src/commands/acp.ts` and `src/modes/acp/acp-mode.ts`
  show ACP stdio support also exists.

GenericAgent:

- `agentmain.py` provides an in-process Python API:
  `GenericAgent()`, a daemon thread running `agent.run()`, and
  `put_task(prompt, source)` returning a `queue.Queue` of `next` and `done`
  dictionaries.
- `agentmain.py` exposes `abort()`, `load_llm_sessions()`, `next_llm()`,
  `list_llms()`, and `get_llm_name()`.
- `llmcore.py` owns the OpenAI/Anthropic-compatible model session wrappers and
  loads model config from `mykey.py` or `mykey.json`.
- `frontends/model_cmd.py` mutates the active GenericAgent backend model in
  memory.
- `frontends/genericagent_acp_bridge.py` adapts GenericAgent into a basic ACP
  JSON-RPC stdio server.

GenericAgent-TUI:

- `docs/runtime-provider-control-plane.md` defines the intended architecture:
  the TUI is the orchestrator/control plane, while concrete agent systems plug
  in as runtime providers.
- `src/ga_tui/runtime.py` defines `RuntimeProviderSpec`,
  `RuntimeAdapter`, and `RuntimeRegistry`.
- `src/ga_tui/genericagent_provider.py` implements
  `GenericAgentRuntimeAdapter` and keeps GenericAgent-specific prompt/tool
  installation out of the provider-neutral runtime module.
- `src/ga_tui/app.py` registers only `genericagent` today in
  `agent_runtime_registry()`.
- `src/ga_tui/app.py` still has GenericAgent-shape assumptions in hot paths:
  `put_task`, `abort`, `is_running`, `task_queue.unfinished_tasks`,
  `get_llm_name`, `llmclient.backend`, `load_llm_sessions`, and
  `next_llm`.
- `.trellis/spec/backend/agent-control-protocol.md` requires provider labels,
  runtime metadata, and governed `agenttask.v2` delegation to stay under the
  TUI control plane.
- `docs/agent-harness-architecture.md` says the target is a strong
  orchestrator, restricted workers, shared ledgers, artifact refs, single-writer
  behavior, approval gates, and auditable protocols.

## Architecture Comparison

| Area | GenericAgent | Oh My Pi | Integration impact |
| --- | --- | --- | --- |
| Runtime language | Python in-process object plus thread | Bun/TypeScript CLI with optional native pieces | Use process isolation for Oh My Pi. Do not embed its SDK in Python. |
| Primary TUI integration shape | `put_task()` returns queue events | `omp --mode rpc` emits JSONL events | Build a Python adapter that translates RPC JSONL into the existing queue shape first. |
| Model registry | `mykey.py` / `mykey.json`, `llmcore` sessions | `~/.omp/agent/models.yml`, `ModelRegistry`, RPC model commands | Keep registries separate initially. Later map TUI `/model` to RPC `get_available_models` and `set_model`. |
| Streaming | Queue items with `next` and `done` text | `message_update` text deltas and `agent_end` | Direct mapping is straightforward. |
| Tools | GenericAgent tool schema injection and TUI query tools | Built-in file/bash/edit/LSP/debug/browser/task/tools plus host tools and host URI schemes | Start without host tools/URIs. Add host tool bridge only after policy gates are mapped. |
| Subagents | TUI owns subagent ledger and delegation | Oh My Pi owns internal `task` subagents and `agent://` artifacts | Do not merge ledgers in MVP. Treat Oh My Pi's subagents as internal details of one runtime job. |
| Session storage | GenericAgent model response logs and TUI session store | JSONL sessions and blobs under `~/.omp/agent` | Store Oh My Pi session paths as artifact/provenance refs in TUI, not as copied chat logs. |
| Protocols | Basic ACP bridge exists upstream | RPC, ACP, SDK, host tools, host URI | Prefer RPC for TUI because it exposes Oh My Pi-specific state and models. ACP remains useful for editor interoperability. |
| Approval/governance | TUI policy gates wrap GenericAgent control actions | Oh My Pi has its own approval modes and tools | TUI must remain policy owner. Disable or tightly configure unsafe Oh My Pi write/approval paths until mapped. |

## Recommendation

Add Oh My Pi as a second runtime provider, not as a replacement for
GenericAgent and not as a vendored dependency.

Recommended MVP:

1. Add `src/ga_tui/ohmypi_provider.py` with an `OhMyPiRuntimeAdapter`.
2. The adapter creates an `OhMyPiRpcAgent` Python wrapper that starts
   `omp --mode rpc --cwd <workspace>` as a child process.
3. `OhMyPiRpcAgent.put_task(prompt, source)` sends an RPC `prompt` command and
   returns a `queue.Queue` of GenericAgent-style display events.
4. Map `message_update.assistantMessageEvent.text_delta` to queue `next`
   events.
5. Map `agent_end` or an equivalent terminal event to queue `done`.
6. Implement `abort()` by sending RPC `abort`, then terminating the process on
   timeout.
7. Implement `get_llm_name(model=True/False)` from cached `get_state` or
   `get_available_models`.
8. Maintain `is_running` and a `task_queue`-like object so current TUI busy
   checks keep working.
9. Register the provider alongside `genericagent` in `agent_runtime_registry()`
   and allow opt-in via `GA_TUI_RUNTIME_PROVIDER=ohmypi`.
10. Keep GenericAgent as the default provider until smoke tests prove parity.

Why RPC instead of SDK:

- The TUI is Python and curses-based; the SDK is Bun/Node in-process.
- Oh My Pi explicitly recommends RPC for cross-language/process isolation.
- RPC exposes the exact surfaces the TUI needs: prompt, abort, state, models,
  sessions, messages, host tools, host URIs, and subagent frames.

Why RPC instead of ACP as the first implementation:

- ACP is the generic editor-facing protocol.
- Oh My Pi RPC is richer for TUI control-plane integration because it exposes
  Oh My Pi's internal state, model commands, host tools, host URIs, and
  subagent snapshots.
- GenericAgent's upstream ACP bridge is basic and shows ACP is workable, but
  the TUI needs provider-specific runtime telemetry for a good control surface.

## Phased Plan

Phase 0 - discovery only:

- Add a provider spec for `ohmypi` with status `available` or `missing`
  depending on whether `omp --version` works.
- Add a no-execution smoke command/path that records the detected binary,
  version, and RPC capability.
- No model or tool execution yet.

Phase 1 - single-session runtime:

- Add `OhMyPiRpcAgent` and `OhMyPiRuntimeAdapter`.
- Start `omp --mode rpc` as a child process with stdout reserved for JSONL and
  stderr routed into diagnostics.
- Translate prompt streaming into the current TUI queue contract.
- Support abort and process cleanup.
- Gate activation behind `GA_TUI_RUNTIME_PROVIDER=ohmypi`.

Phase 2 - model/status integration:

- Use `get_state` and `get_available_models` for status-panel display.
- Add a provider-specific model switch path that calls RPC `set_model`.
- Do not reuse GenericAgent `llmclient` mutation paths for Oh My Pi.

Phase 3 - artifact and provenance integration:

- Record Oh My Pi `sessionFile`, `agent://`, `history://`, export paths, and
  artifact paths as TUI artifact refs.
- Keep raw Oh My Pi session JSONL in its own store unless the user explicitly
  requests import.

Phase 4 - governed host tools:

- Expose selected TUI capabilities to Oh My Pi through RPC `set_host_tools` and
  `set_host_uri_schemes`.
- Route every write, external-send, deploy, delete, and memory-write operation
  through existing TUI approval gates before returning host tool success.

Phase 5 - subagent ledger mapping:

- If useful, subscribe to Oh My Pi subagent frames and display them as nested
  runtime children under one Oh My Pi session.
- Do not let Oh My Pi internal subagents become independent TUI subagents until
  they can carry the same `agenttask.v2` routing, work order, capability,
  context, output, approval, and provenance fields.

## Main Risks

1. GenericAgent coupling remains in TUI hot paths.
   The current `RuntimeAdapter` abstraction exists, but model switching, token
   panels, title generation, and session metadata still often reach into
   `state.agent.llmclient.backend`. The MVP should either provide safe
   compatibility methods or skip those features for `ohmypi` until the TUI
   surface is fully provider-neutral.

2. Approval ownership can split.
   Oh My Pi has its own approval modes and many tools. For GenericAgent-TUI, the
   TUI must remain the policy owner. Start with conservative tool exposure and
   avoid `--auto-approve`/`--yolo` unless the TUI explicitly approved that
   runtime job.

3. Duplicate subagent systems can confuse the user.
   GenericAgent-TUI has a governed subagent ledger; Oh My Pi has an internal
   `task` tool and agent lifecycle. The first integration should present Oh My
   Pi as one runtime provider. Nested Oh My Pi agents can be displayed later as
   provider-owned children, not first-class TUI workers.

4. Session persistence semantics differ.
   Oh My Pi JSONL sessions and blobs should be referenced by path/provenance.
   Importing them directly into the TUI session model would require a separate
   migration design.

5. Bun/runtime availability is external.
   The provider must degrade cleanly if `omp` or a compatible Bun/compiled
   binary is missing.

## Alignment With Architecture Baseline

This recommendation moves the system closer to the baseline:

- Strong orchestrator: the TUI remains the owner of provider selection,
  dispatch, policy gates, artifacts, and user-facing session state.
- Restricted subagents: Oh My Pi starts as a bounded runtime worker, not an
  autonomous peer that can bypass the TUI ledger.
- Shared ledgers and artifacts: Oh My Pi session files and artifacts are
  attached as refs/provenance instead of copied into chat.
- Single-writer: write/tool exposure is delayed until host tools can enforce
  TUI approval and single-writer constraints.
- Auditable protocols: JSONL RPC frames are recordable and replayable enough for
  trace/debug work.
- A2A/MCP compatibility: ACP remains available for editor compatibility, while
  RPC host tools/URIs can later be mapped to the TUI gateway.

The biggest remaining gap is that `app.py` still assumes a GenericAgent-shaped
runtime in several places. A clean long-term implementation should move those
operations behind provider-neutral methods instead of adding more local
`if provider == "ohmypi"` checks.

## Next Implementation Task

Implement Phase 0 and Phase 1 behind an opt-in environment flag:

- `ohmypi_provider_spec(...)`
- `OhMyPiRpcAgent`
- `OhMyPiRuntimeAdapter`
- registry registration next to `GenericAgentRuntimeAdapter`
- tests that provider metadata exists, missing binary is safe, and a fake RPC
  subprocess stream maps to `next` and `done` queue events
