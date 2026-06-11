# Implement Oh My Pi runtime provider

## Goal

Add an opt-in Oh My Pi runtime provider to GenericAgent-TUI using Oh My Pi's
`omp --mode rpc` JSONL stdio protocol, while keeping GenericAgent as the
default backend.

## Requirements

- Add provider metadata for `ohmypi` to the runtime registry.
- Add a Python runtime adapter that can create an Oh My Pi-backed agent object.
- Start Oh My Pi as an external child process through `omp --mode rpc`.
- Translate Oh My Pi RPC streaming events into the current TUI display queue
  contract:
  - text deltas become `{"next": ...}`
  - terminal completion becomes `{"done": ...}`
  - command/startup failures become `{"done": "...error..."}`
- Support abort through RPC `abort`, with process termination as a cleanup
  fallback.
- Preserve existing GenericAgent default behavior unless the user opts in with
  `GA_TUI_RUNTIME_PROVIDER=ohmypi`.
- Degrade safely when `omp` is not installed.
- Add non-network/non-model tests by using a fake RPC process or injected process
  factory.
- Update policy-gate/runtime checks so the new provider is visible without
  breaking existing `genericagent` expectations.

## Non-Goals

- Do not make Oh My Pi the default runtime.
- Do not vendor Oh My Pi source into this repository.
- Do not expose Oh My Pi host tools or host URI schemes in this iteration.
- Do not merge Oh My Pi internal subagents into the TUI subagent ledger yet.
- Do not rewrite the existing `/model` manager for Oh My Pi in this iteration.
- Do not run a real model prompt as part of automated tests.

## Acceptance Criteria

- [x] `agent_runtime_registry().to_record()` includes `genericagent` and `ohmypi`.
- [x] Default provider remains `genericagent` when no environment variable is set.
- [x] `GA_TUI_RUNTIME_PROVIDER=ohmypi` selects the Oh My Pi adapter.
- [x] If the `omp` binary exists, the provider spec reports an available/active
  status with RPC entrypoints.
- [x] If the `omp` binary is missing, the provider spec records a missing status and
  adapter startup returns a user-visible queue error rather than crashing the
  TUI.
- [x] A fake RPC stream test proves ready, prompt ack, text delta, and completion
  map into the TUI queue contract.
- [x] Abort is covered at adapter level.
- [x] `python3 -m py_compile` passes for changed Python files.
- [x] `python3 scripts/check_policy_gates.py` passes.
- [x] `git diff --check` passes.

## Design Constraints

- Keep provider-specific code outside `app.py` where practical.
- The Oh My Pi provider module must not import curses or mutable TUI `State`.
- The TUI remains the orchestrator and policy owner.
- Backend-specific RPC details must not leak into scheduler or control protocol
  semantics.
- Treat Oh My Pi session files/artifacts as provider-owned refs for now.

## Research Input

- `.trellis/tasks/06-11-research-ohmypi-integration/research/integration-analysis.md`
