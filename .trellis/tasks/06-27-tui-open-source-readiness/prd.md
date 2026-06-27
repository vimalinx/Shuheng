# Harden TUI for Open-Source Release Readiness

## Goal

Prepare the Shuheng TUI for a credible open-source alpha by converting the current maturity review into executable hardening and architectural cleanup work. The user explicitly selected the broader refactor path: improve the release posture and begin dismantling patch-like monolith boundaries instead of only documenting the gaps.

## What I Already Know

* The current TUI is runnable and tested: `python3 -m pytest -q -p no:cacheprovider` passed with 168 tests, `python3 scripts/check_policy_gates.py` passed, and `git diff --check` passed during the review.
* The worktree was already dirty before this task: `src/ga_tui/app.py` had uncommitted changes and there were unrelated/untracked directories and research docs.
* `src/ga_tui/app.py` is a very large composition module and owns many release-critical concerns: curses UI, Web Console, policy, artifact store, gateway, A2A/MCP registries, memory candidates, recovery, eval, scheduler loop, runtime configuration, and dispatch.
* Some useful extractions already exist: `src/ga_tui/runtime.py`, `src/ga_tui/scheduler.py`, `src/ga_tui/control_protocol.py`, `src/ga_tui/genericagent_provider.py`, `src/ga_tui/ohmypi_provider.py`, `src/ga_tui/integration.py`, and `src/ga_tui/agent_bridge.py`.
* The architecture baseline in `docs/agent-harness-architecture.md` requires a strong Orchestrator, restricted workers, shared ledgers, artifact refs, single-writer enforcement, approval gates, auditable communication, external memory, recovery/eval/trace, and A2A/MCP compatibility.
* README currently markets broad governance capabilities, including task ledger, approvals, artifacts, recovery, eval, trace, A2A/MCP gateway, and baseline comparison.

## Requirements

* Create an open-source readiness hardening layer that makes release status explicit: experimental alpha, supported local surfaces, experimental surfaces, and known gaps.
* Extract release-readiness/baseline/eval logic out of ad-hoc inline code where feasible, prioritizing pure helpers that are easy to test and safe to move.
* Make architecture baseline reporting less patch-like by distinguishing structural evidence, runtime evidence, and true end-to-end verification instead of treating function/path/schema existence as enough.
* Make task eval reporting less misleading by marking heuristic scores as heuristic and exposing evidence quality/gaps clearly.
* Harden Web Console and Gateway release boundaries by making local-only/no-auth defaults explicit, preventing accidental unsafe remote exposure where feasible, and documenting the security model.
* Tighten A2A/MCP language and metadata so it is presented as a compatibility surface unless tested with real clients.
* Improve scheduler release messaging so users know scheduler execution is tied to the TUI/gateway runtime unless a real daemon is active.
* Preserve existing passing behavior and tests while adding focused checks for the new release-readiness contracts.
* Avoid destabilizing unrelated behavior, but do perform real modular extraction for the reviewed release-readiness concerns instead of only changing labels.
* Update docs so README promises match what the code can defensibly prove.
* Keep unrelated existing dirty files out of this task's change set unless they are directly required.

## Acceptance Criteria

* [x] README clearly labels Shuheng as experimental alpha and distinguishes stable local TUI features from experimental gateway/A2A/MCP/eval/baseline features.
* [x] A release readiness document or generated report lists blockers, public-alpha gaps, experimental surfaces, and verification commands.
* [x] Architecture baseline comparison exposes evidence levels and does not imply that callable/path/schema existence is equivalent to full completion.
* [x] Release-readiness or baseline/eval helpers live in separate module(s) rather than adding more large inline logic to `app.py`.
* [x] Eval output/schema or display text makes heuristic scoring explicit and does not overstate factual/citation accuracy from artifact presence alone.
* [x] Gateway/Web Console docs and code make local-only/no-auth posture explicit and safer for accidental remote binding.
* [x] A2A/MCP registry/service descriptions use compatibility-surface wording unless there is real protocol compliance evidence.
* [x] Scheduler docs/UI text disclose runtime/tick ownership and do not imply an always-on scheduler unless the gateway daemon or TUI loop is active.
* [x] Tests cover the release-readiness wording/contracts and continue covering existing policy gates.
* [x] `python3 -m pytest -q -p no:cacheprovider` passes.
* [x] `python3 scripts/check_policy_gates.py` passes.
* [x] `python3 -m compileall -q src scripts` passes.
* [x] `git diff --check` passes.

## Definition Of Done

* The task is implemented with narrowly scoped code/docs changes.
* Quality checks above pass.
* No unrelated user/WIP changes are reverted.
* Architecture baseline impact is explicitly reported.
* Any remaining release gaps are documented as known limitations, not hidden behind optimistic labels.

## Technical Approach

Use a staged refactor that extracts the reviewed maturity risks while keeping the live TUI stable:

1. Add explicit release status metadata and docs that classify capabilities as stable, experimental, or known-gap.
2. Extract pure release-readiness/evidence/eval-scoring helpers into new module(s) so `app.py` delegates those concerns.
3. Adjust baseline/eval/gateway/scheduler descriptions so generated surfaces are honest about evidence level and runtime ownership.
4. Add tests to `scripts/check_policy_gates.py` or focused pytest files that assert the new release-readiness contract and the extraction boundaries.
5. Leave high-risk UI/runtime rewrites for follow-up tasks only when they require moving large stateful code; document remaining monolith gaps explicitly.

## Decision (ADR-lite)

**Context**: The audit found a runnable and tested TUI, but release maturity is weakened by overbroad public claims, a huge `app.py`, optimistic self-checks, heuristic eval, gateway security ambiguity, and protocol surfaces that look more complete than they are.

**Decision**: Treat this task as a full release-readiness refactor within safe boundaries: extract pure governance/readiness logic and fix overclaiming, but do not rewrite the live curses event loop or runtime providers unless directly required.

**Consequences**: This reduces open-source risk while making real progress away from patch-like monolith logic. Some large stateful areas will remain in `app.py`, but the remaining gaps must be explicitly visible in the release-readiness report.

## Out Of Scope

* Full decomposition of the curses drawing/event loop.
* Complete A2A or MCP protocol certification against third-party clients.
* Replacing the scheduler with a standalone system service.
* Replacing heuristic eval with a full evaluator framework.
* Changing OMP runtime architecture beyond release-boundary clarification and tests.
* Cleaning unrelated dirty/untracked files that existed before this task.

## Technical Notes

* Baseline reference: `docs/agent-harness-architecture.md`.
* Runtime provider contract: `docs/runtime-provider-control-plane.md`.
* Main TUI composition: `src/ga_tui/app.py`.
* Provider abstraction: `src/ga_tui/runtime.py`.
* Scheduler module: `src/ga_tui/scheduler.py`.
* Release-facing docs: `README.md`, `README.en.md`, `pyproject.toml`.
* Current broad policy regression suite: `scripts/check_policy_gates.py`.

## Research References

* [`research/current-tui-maturity-audit.md`](research/current-tui-maturity-audit.md) - local evidence from the maturity review that seeded this task.

## Completion Notes

Implemented `src/ga_tui/release_readiness.py` as the pure release-readiness contract layer for release posture, baseline evidence levels, gateway bind safety, protocol compatibility wording, scheduler ownership, and heuristic eval metadata. `app.py`, scheduler registry, docs, and policy gates now delegate to those contracts.

Verification on 2026-06-27:

* `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py` passed.
* `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passed with 171 tests.
* `python3 -m compileall -q src scripts` passed.
* `git diff --check` passed.
* `PYTHONPATH=src python3 -m ga_tui.integration doctor --root /home/vimalinx/Programs/GenericAgent` passed with `Status: OK`.

Architecture baseline impact: this moves the TUI closer to the baseline by making the Orchestrator/control-plane release claims auditable, making evidence quality explicit, preserving single-writer/runtime ownership language, and narrowing gateway/A2A/MCP claims to compatibility surfaces until end-to-end proof exists. Remaining baseline gaps are now explicit: `app.py` is still a large composition module, A2A/MCP need real client conformance tests, eval remains heuristic, gateway has no built-in auth, and scheduler is not an installed always-on service.
