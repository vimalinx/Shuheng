# Current TUI Maturity Audit

## Summary

The TUI is usable and has meaningful automated checks, but its public release posture is not mature enough for broad claims. The safest release stance is an experimental local alpha with explicit stable/experimental/known-gap classification.

## Verification Snapshot

* `python3 -m pytest -q -p no:cacheprovider` passed with 168 tests.
* `python3 scripts/check_policy_gates.py` passed.
* `git diff --check` passed.
* Worktree was dirty before this task: `src/ga_tui/app.py` modified; `.trellis/tasks/06-20-shuheng-genericagent-memory-mode/`, `config/`, two research docs, and `references/` untracked.

## Evidence

* `src/ga_tui/app.py` is about 30k lines and includes UI, gateway, policy, artifact, memory, eval, scheduler loop, baseline report, secret vault, and provider composition concerns.
* `docs/agent-harness-architecture.md` requires a governed system, not just many agents chatting.
* `README.md` promises task ledgers, agent mail, artifacts, eval, trace, approvals, A2A/MCP gateway, and architecture baseline checks.
* `src/ga_tui/runtime.py` provides useful provider-neutral request/event/spec abstractions.
* `src/ga_tui/scheduler.py` is already a good extraction and receives app dependencies by injection.
* `architecture_baseline_report()` currently relies heavily on function existence, configured paths, schema presence, and registry presence.
* `append_task_eval()` currently derives factual/citation/source quality mostly from artifact presence and non-empty text.
* Gateway/Web Console expose local HTTP surfaces with no visible auth layer. Push subscriptions record `auth: {"type": "none"}` and remote push is gated by env.
* A2A/MCP surfaces exist as registry and HTTP endpoints, but there is no evidence of third-party protocol compliance testing in the maturity review.
* Scheduler tick currently runs from the TUI loop and manual/web-console paths; this is valid but should be documented as runtime-owned rather than always-on.

## Release Risks To Address

1. Overclaiming public maturity in README and generated registries.
2. Self-checks that treat "exists" as "complete".
3. Heuristic eval scores that look authoritative.
4. No-auth gateway/Web Console ambiguity.
5. A2A/MCP compatibility wording that may imply complete protocol support.
6. Scheduler runtime ownership ambiguity.
7. Missing open-source hygiene files/CI/license are known gaps. This task may document them, but full repository governance can be separate if it would distract from TUI hardening.

## Recommended Scope For This Task

Implement high-leverage release-readiness safeguards:

* Add release status metadata/reporting.
* Downgrade overconfident labels.
* Add evidence-level fields to baseline report.
* Label eval scores as heuristic.
* Document/guard gateway local-only/no-auth behavior.
* Add policy-gate tests for the new contracts.
