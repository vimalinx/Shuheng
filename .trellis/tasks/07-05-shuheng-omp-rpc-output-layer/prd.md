# PRD: Shuheng OMP RPC Output Layer

## Problem

Shuheng currently launches OMP as the default runtime provider, but parts of the
adapter still behave like a compensating agent shell: it interprets completion,
adds fallback recovery, handles host-tool watchdogs, and only partially exposes
OMP native RPC surfaces. That makes it easy for Shuheng to look complete from
local UI state while the real execution kernel has not produced the authoritative
result.

The desired direction is not to replace OMP. OMP remains the execution kernel:
agent loop, tool loop, session lifecycle, subagent lifecycle, retry, compaction,
plugin execution, and native RPC state. Shuheng is the governed output/control
layer: TUI, ledgers, approval gates, artifact references, memory candidates,
runtime events, and external gateway discovery.

## Goals

- Make the OMP RPC process the normal source of truth for runtime state and
  subagent output-layer facts that OMP already exposes.
- Add explicit provider methods for OMP native subagent subscription and query
  surfaces so app/gateway layers do not need to guess from Shuheng-only state.
- Preserve existing Shuheng governance: OMP may execute, stream, and report; it
  does not own Shuheng ledgers, approvals, long-term memory, schedules, or TUI
  state mutation.
- Treat current terminal fallback behavior as compatibility recovery only, not
  as the preferred completion authority.
- Capture unknown OMP extension UI requests as output-layer events instead of
  silently dropping them.

## Non-Goals

- Do not delete terminal grace fallback, incomplete-reply continuation, or host
  tool watchdog behavior in this task.
- Do not reimplement OMP's agent loop, retry policy, compaction, plugin runtime,
  session lifecycle, or subagent lifecycle inside Shuheng.
- Do not make gateway or A2A messages directly execute runtime work.
- Do not expose project context, memory paths, or internal permission matrices
  through public gateway discovery.
- Do not rename or reintroduce removed legacy concepts.

## Source Of Truth

- OMP owns execution progress, native RPC state, native subagent registry, native
  subagent transcripts, extension UI requests, and final `agent_end` semantics.
- Shuheng owns governance and persistence: task/progress ledgers, approval gates,
  artifact references, runtime event normalization, memory candidates, gateway
  inbox rows, UI rendering, and policy decisions.
- Compatibility fallback is allowed only when OMP omits or withholds a terminal
  surface required to keep the UI recoverable. Fallback output must remain visibly
  marked as provider recovery when it is not model-authored final text.

## Acceptance Criteria

- `OhMyPiRpcAgent` exposes bounded JSON-safe methods for:
  - setting native OMP subagent subscription level,
  - reading native OMP subagent summaries,
  - reading native OMP subagent messages.
- The methods pass through OMP RPC commands when a live RPC process exists and
  return structured unsupported/error payloads when it does not, without raising
  into the TUI.
- Unknown or non-approval OMP `extension_ui_request` frames are emitted as
  provider output-layer events so they can be inspected and tested; approval
  handling remains unchanged.
- Provider metadata/spec documents Shuheng as an OMP RPC output/control layer,
  not an alternate execution kernel.
- Policy gates cover native RPC pass-through methods and unknown extension UI
  request preservation.
- Existing OMP completion, host-tool bridge, model switching, and runtime event
  tests continue to pass.

## Validation

- `python3 -m py_compile src/shuheng/ohmypi_provider.py scripts/check_policy_gates.py`
- `python3 scripts/check_policy_gates.py`
- `python3 -m compileall -q src scripts`
- `git diff --check`

