# Expose OMP Runtime Output In TUI

## Goal

Add a Shuheng TUI read-only command that lets the operator inspect live
OMP-native runtime subagent output facts through the query layer added in the
previous task. The result should make Shuheng visibly act as the OMP output
governance layer without inventing OMP state from local Shuheng worker records.

## What I Already Know

- `OhMyPiRpcAgent` exposes native output methods:
  `get_runtime_subagents(...)` and `get_runtime_subagent_messages(...)`.
- `shuheng_query` and typed host tools already expose
  `runtime_subagent_list` and `runtime_subagent_messages`.
- Existing `/runtimes` shows provider registry metadata only.
- Existing `/agent(s)` commands list Shuheng-managed persistent or temporary
  workers and must stay separate from OMP-native runtime subagents.
- The implementation should follow existing command-output patterns such as
  `/runtimes`, `/tasks`, `/gateway`, and `/artifacts`: write a bounded system
  message via `add_system(...)`, not a new background service.

## Requirements

- Add a TUI command named `/runtime-output`.
- Add `/runtime-output` to command completion/help text.
- The command must call the existing app-layer runtime query helpers against
  the current active runtime agent.
- The command output must include:
  - runtime provider id,
  - provider query status,
  - OMP-native subagent id/name/status/session file when available,
  - a bounded preview of recent messages for each listed runtime subagent.
- The command must work when the provider returns `unsupported` or when the
  active runtime does not expose native methods, returning an explicit readable
  status instead of raising.
- The command must not lazily start OMP, send prompts, dispatch agents, mutate
  task/progress ledgers, write memory, touch approvals, create schedules, or
  process gateway inboxes.
- Existing `/runtimes` and `agent_list` semantics must stay unchanged.

## Acceptance Criteria

- [ ] `/runtime-output` appears in `COMMANDS` and command completion.
- [ ] `/runtime-output` formats OMP-native runtime subagent list output from
  `get_runtime_subagents(...)`.
- [ ] `/runtime-output` formats bounded runtime subagent message previews from
  `get_runtime_subagent_messages(...)`.
- [ ] Unsupported/no-method/no-state cases produce readable output and do not
  crash the TUI.
- [ ] The command does not call `tui_tool_agent_list(...)` or read
  `State.subagents` as a fallback for OMP-native runtime facts.
- [ ] Policy gates cover command registration, formatting, and no-fallback
  behavior.

## Definition Of Done

- Targeted compile/Ruff checks pass.
- `scripts/check_policy_gates.py` passes.
- Full test suite passes unless a clear external blocker is found.
- Relevant spec/docs are updated if this creates a durable command contract.
- Work is committed before finish-work.

## Technical Approach

- Add a formatter such as `format_runtime_output_snapshot(state)` near
  `format_runtime_registry(...)`.
- Reuse `ohmypi_tui_runtime_subagent_list(...)` and
  `ohmypi_tui_runtime_subagent_messages(...)`; do not parse provider internals.
- Add a `/runtime-output` branch near `/runtimes` in the command handler.
- Add policy-gate coverage with a fake active runtime agent that records method
  calls and proves `agent_list` is not used as fallback.

## Decision (ADR-lite)

**Context**: We need an operator-visible proof that Shuheng can read live
OMP-native runtime output without pretending local Shuheng workers are OMP
runtime subagents.

**Decision**: Implement a small read-only command first (`/runtime-output`)
instead of a new persistent panel or background refresh loop.

**Consequences**: The MVP is easy to verify and low-risk. A richer panel,
rightbar badge, or Web Console projection can be added later using the same
query/formatting boundary.

## Out Of Scope

- No new HTTP/gateway endpoint.
- No rightbar or dashboard auto-refresh.
- No live polling loop.
- No OMP process startup for inspection.
- No changes to OMP execution, host-tool proposal behavior, approvals, memory,
  schedules, or gateway execution.

## Technical Notes

- Relevant code:
  - `src/shuheng/app.py`
  - `scripts/check_policy_gates.py`
  - `.trellis/spec/backend/agent-control-protocol.md`
  - `docs/runtime-provider-control-plane.md`
- Related completed commits:
  - `46d5636 feat: expose omp rpc output layer`
  - `df66940 feat: expose omp runtime output queries`
