# Trellis Development Ledger

This directory stores Shuheng's project-local Trellis workflow metadata.

Public alpha readers should interpret it as development provenance, not runtime
state:

- `.trellis/spec/` contains executable engineering contracts for AI-assisted
  development.
- `.trellis/tasks/` contains task ledgers and may include historical local
  workflow state.
- `.trellis/workflow.md` and `.trellis/scripts/` define the local development
  process used by maintainers.
- `.trellis/.runtime/`, `.trellis/.cache/`, `.trellis/.developer`, backups,
  template hashes, and worktrees are ignored local state.

The Python release artifacts intentionally exclude `.trellis/` via
`MANIFEST.in`. Do not infer public product status from the count of task
directories; product readiness is tracked through release gates, tests,
documentation, and `src/ga_tui/release_readiness.py`.
