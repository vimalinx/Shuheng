# Expose OMP Native RPC Output Queries

## Goal

Expose the OMP-native RPC output layer added in the previous task through
Shuheng's existing read-only query surfaces. The user-visible result should be:
Shuheng remains the governed shell, but callers can inspect live OMP runtime
subagent output facts through the same host-tool/query path used for
`runtime_registry`, `agent_list`, and `capability_list`.

## What I Already Know

- `OhMyPiRpcAgent` now exposes provider methods:
  `set_subagent_subscription(level)`, `get_runtime_subagents()`, and
  `get_runtime_subagent_messages(...)`.
- `src/shuheng/app.py` already owns the read-only OMP host-tool query surface:
  `shuheng_query`, typed read-only tools, and `ohmypi_tui_query_endpoint(...)`.
- Existing query names such as `agent_list` describe Shuheng-managed persistent
  or temporary subagents, not OMP-native runtime subagents.
- Public gateway discovery must not become an executor and must not expose broad
  project context or internal permission matrices.

## Requirements

- Add read-only query endpoints named `runtime_subagent_list` and
  `runtime_subagent_messages`.
- Expose those endpoints through both:
  - compatibility `shuheng_query` endpoint enum,
  - typed read-only host tools.
- Route the endpoints only to the currently active runtime agent when it
  supports the native OMP methods.
- Do not lazily start OMP, do not synthesize OMP-native data from Shuheng's
  local `State.subagents`, and do not mutate task ledgers, approvals, memory,
  schedules, or gateway inboxes.
- If no active TUI state or no compatible live runtime exists, return a
  structured read-only query error or provider `unsupported` result.
- Keep response payloads JSON-safe and bounded through the existing query
  sanitization path.
- Update spec/docs so future work knows `agent_list` and
  `runtime_subagent_list` are different surfaces.

## Acceptance Criteria

- [ ] `shuheng_query({endpoint:"runtime_subagent_list"})` calls
  `state.agent.get_runtime_subagents()` when available.
- [ ] `runtime_subagent_list` returns structured unsupported/error output
  without starting OMP when no live RPC process exists.
- [ ] `runtime_subagent_messages` forwards `subagent_id`, `session_file`, and
  `from_byte` to `get_runtime_subagent_messages(...)`.
- [ ] Typed host tools include `runtime_subagent_list` and
  `runtime_subagent_messages`.
- [ ] Existing `agent_list` semantics stay unchanged.
- [ ] Policy gates cover query routing, typed tool registration, and the
  no-state/no-method error paths.

## Technical Approach

- Extend `OHMYPI_TUI_QUERY_ENDPOINTS` and `OHMYPI_TYPED_READONLY_TOOL_NAMES`.
- Add app-owned helper functions near existing TUI query helpers:
  `tui_tool_runtime_subagent_list(...)` and
  `tui_tool_runtime_subagent_messages(...)`.
- The helpers call methods on `state.agent` only if present; they do not import
  provider internals or inspect OMP process state directly.
- Existing provider method behavior remains the source of truth for live vs
  unsupported process state.

## Out Of Scope

- No new public HTTP endpoint in this task.
- No automatic execution of gateway/A2A messages.
- No removal of existing provider fallback/recovery behavior.
- No archive/journal bookkeeping commit in this task.

## Technical Notes

- Relevant files:
  - `src/shuheng/app.py`
  - `src/shuheng/ohmypi_provider.py`
  - `scripts/check_policy_gates.py`
  - `.trellis/spec/backend/agent-control-protocol.md`
  - `docs/runtime-provider-control-plane.md`
- The previous work commit is `46d5636 feat: expose omp rpc output layer`.

