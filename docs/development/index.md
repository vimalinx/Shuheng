# Development Contracts

These documents are the contributor-facing engineering contracts for Shuheng.
They are ordinary project documentation and do not require a particular local
agent workflow framework.

- [`runtime-governance.md`](runtime-governance.md) — runtime authority,
  permissions, credentials, ledgers, artifacts, and worker boundaries.
- [`test-isolation.md`](test-isolation.md) — filesystem isolation and shared
  state transaction rules for tests.
- [`release-engineering.md`](release-engineering.md) — clean-room build,
  packaging, install, upgrade, security, and release gates.
- [`../agent-harness-architecture.md`](../agent-harness-architecture.md) — the
  long-term strong-Orchestrator architecture baseline.

When code and documentation disagree, treat the mismatch as a defect. Update
the implementation, tests, and the owning contract together.
