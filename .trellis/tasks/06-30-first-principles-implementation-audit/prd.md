# First-principles implementation audit

## Goal

Review Shuheng's concrete code implementation from first principles and report whether recent patches are principled architecture improvements or patch-by-patch accidental complexity. The user then asked to fix the confirmed findings.

## What I Already Know

- The user asked for a first-principles review of the program's feature implementations and whether recent patches fit those principles.
- The previous task unified non-secret subagent direct chat around global Shuheng history and hardened release-readiness artifact gates.
- The project architecture baseline says success is not "many agents chatting"; it is a governed engineering system with a strong Orchestrator, restricted subagents, shared ledgers/history, artifact refs, approval gates, auditable protocols, external long-term memory, recovery, eval, and trace.
- Current checkout has no active Trellis task before this audit; `uv.lock` is the only pre-existing untracked non-Trellis file.

## First-Principles Review Lens

- Single source of truth: each domain should have one canonical owner for durable facts.
- Boundary clarity: runtime state, user history, Secret storage, release artifacts, protocol metadata, and UI projections should not leak responsibilities into each other.
- Auditability and provenance: durable outputs should carry enough refs, hashes, metadata, or evidence to reconstruct what happened.
- Recovery and reload: persistent state should survive process restart without hidden process-only assumptions.
- Hard gates over model discretion: security, approval, release, and publish boundaries should be enforced by executable code, not wording.
- Simplicity under pressure: patches should reduce branching and duplicated logic, not only add local guards.

## Requirements

- Review the concrete implementation of the main patched surfaces:
  - subagent chat history ownership and metadata refs,
  - Secret Vault isolation,
  - shared user profile and memory candidate flow,
  - task ledger/artifact/approval governance,
  - Web Console subagent conversation projection,
  - release-readiness and wheel/sdist artifact gates,
  - runtime-provider/control-plane boundaries.
- Prioritize executable code paths over comments or docs.
- Report findings with file/line evidence and severity.
- Distinguish first-principles violations from acceptable pragmatic tradeoffs.
- Fix the confirmed first-principles findings:
  - Make non-secret subagent chat restore from the canonical history transcript instead of full message copies in `session_meta.json`.
  - Make single-writer lock acquisition/release atomic across processes.
  - Move duplicated release secret/local-path scan rules into a shared source of truth.

## Acceptance Criteria

- [ ] Findings are ordered by severity and include concrete file/line evidence.
- [ ] The report identifies where patches improved the system's first-principles alignment.
- [ ] The report identifies where patches still look like local guards, duplication, or boundary leakage.
- [ ] The report calls out residual risk and suggested next fix order.
- [ ] Business-code changes are covered by policy gates and focused tests.

## Out of Scope

- Publishing the repository.
- Re-running the full release-quality suite unless a finding depends on fresh runtime evidence.
- External web research unless a claim needs current third-party documentation.

## Technical Notes

- Architecture baseline: `docs/agent-harness-architecture.md`.
- Primary executable contract: `.trellis/spec/backend/agent-control-protocol.md`.
- Important code areas discovered by symbol scan: `src/ga_tui/app.py`, `src/ga_tui/release_readiness.py`, `scripts/wheel_smoke.py`, `scripts/check_policy_gates.py`, `scripts/check_release_hygiene.py`, and related tests.
