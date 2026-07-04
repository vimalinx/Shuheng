# Fix Stalled Shuheng Model Communication Turn

## Goal

Fix the Shuheng stable TUI hang where a main-runtime request that asks the model to communicate with other models starts tool discovery (`todo`, `agent_list`, `irc`) but then stops visibly after "Started. Let me discover who's available — Shuheng agents and IRC peers."

## What I Already Know

* User reproduced the hang in the stable Shuheng TUI.
* Visible transcript shows a folded process group `G3` with tools `todo`, `agent_list`, and `irc`.
* The final visible assistant text stops at: `Started. Let me discover who's available — Shuheng agents and IRC peers.`
* The running `shuheng` process is alive at PID `393058`.
* The embedded `omp --mode rpc` child process is alive at PID `424556`.
* The active OMP command uses model `shuheng-opencode-go-deepseek-v4-flas-6094d65d/deepseek-v4-flash` and append prompt `/home/vimalinx/.shuheng/memory/agent_harness/runtime/ohmypi-shuheng-memory.md`.
* The stalled communication-turn transcript is `/home/vimalinx/.shuheng/model_responses/model_responses_102106070390001.txt`.
* The matching OMP session JSONL is `/home/vimalinx/.shuheng/memory/agent_harness/runtime/ohmypi/agent/sessions/-Programs-Shuheng/2026-06-23T10-41-47-438Z_019ef412-67ae-7000-963f-fd8edcc7854d.jsonl`.
* Recent commits already include `d0dc323 fix: finish stalled ohmypi host tool turns`, so this is likely a related but not fully covered stall path.
* Current repo state has one unrelated untracked Trellis task: `.trellis/tasks/06-20-shuheng-genericagent-memory-mode/`.

## Assumptions

* The hang is in the Shuheng/OMP runtime integration path, not in curses rendering alone.
* The fix should make this class of tool-driven "communicate with other models" turn either finish with a user-visible final reply or show a clear failure/timeout instead of staying silent.
* The current live process should be used as evidence, but the code fix should be made in repo source and covered by regression tests.

## Open Questions

* None blocking yet. The immediate next step is log/code diagnosis.

## Requirements

* Diagnose from live Shuheng logs and current code paths, not from UI text alone.
* Preserve running user state where possible; do not kill the user's TUI unless recovery requires it and is reported.
* Fix the OMP/host-tool turn path so tool discovery/IRC requests cannot leave the UI stuck without a final visible outcome.
* Add or update regression coverage in `scripts/check_policy_gates.py` or the pytest suite for the specific stall class.
* Preserve existing behavior for successful tool-rich OMP turns, including folded process groups and bounded IRC snippets.
* Do not include unrelated `.trellis/tasks/06-20-shuheng-genericagent-memory-mode/` changes.

## Acceptance Criteria

* [x] The root cause of the current stalled turn is identified from logs/code.
* [x] A code path is fixed so the relevant OMP RPC/tool turn reaches a terminal UI state.
* [x] Regression coverage proves the stalled tool path now produces a final visible reply, explicit failure, or bounded timeout.
* [x] `python3 scripts/check_policy_gates.py` passes.
* [x] `python3 -m pytest -q` passes or any skipped subset is explicitly justified.
* [x] The final report states whether the currently running TUI needs restart to pick up the fix.

## Definition Of Done

* Code and tests updated.
* Relevant Trellis/backend spec updated if a runtime contract changes.
* Architecture baseline checked before claiming completion.
* Changes committed, excluding unrelated task directories.

## Out Of Scope

* Completing the layered-memory task.
* Redesigning all IRC/model communication UX.
* Updating Trellis itself.
* Killing or restarting the live Shuheng process unless necessary for recovery verification.

## Technical Notes

* Likely code paths: `src/shuheng/ohmypi_provider.py`, `src/shuheng/app.py`, and tests around OMP host tools/final text fallback.
* Live process evidence should be gathered from `~/.shuheng/model_responses/`, `~/.shuheng/memory/agent_harness/*.jsonl`, and the live `shuheng`/`omp` process tree.
* Prior memory indicates OMP is the preferred runtime-provider direction and previous fixes touched stalled host-tool turns and final reply enforcement.

## Completion Notes

* Root cause: after a host tool result, the provider's fixed follow-up watchdog could finish the active prompt from pre-tool visible progress text while OMP was still processing later frames. That made the underlying OMP session continue while Shuheng UI no longer received those frames.
* Fix: `OhMyPiRpcAgent` now records the buffer boundary at each host tool result, refreshes follow-up activity on later OMP frames, waits for a full idle window before fallback, and only lets post-tool visible text suppress the provider fallback.
* Safety fix: provider-owned host-tool watchdog fallback mixed with pre-tool progress text is filtered from Oh My Pi memory-candidate extraction.
* Regression coverage: `scripts/check_policy_gates.py` now covers stalled host-tool fallback, post-tool activity deferring completion until final answer, pre-tool progress not suppressing fallback, and mixed fallback not becoming a memory candidate.
* Verification passed: `python3 -m py_compile src/shuheng/ohmypi_provider.py scripts/check_policy_gates.py`; `python3 -m compileall -q src scripts`; `python3 scripts/check_policy_gates.py`; `python3 -m pytest -q`; `git diff --check`.
* Architecture baseline: the change keeps OMP as a bounded runtime provider, preserves Shuheng as the Orchestrator/ledger/memory owner, and moves the system closer to the governed-agent baseline by preventing provider progress/fallback from bypassing traceability or memory-candidate governance.
* Runtime note: the currently running `shuheng` PID `393058` with OMP child `424556` is still using the old imported code. The pipx launcher imports this checkout's `src/shuheng`, so no reinstall is needed; exit and relaunch `shuheng` to pick up the source fix.
