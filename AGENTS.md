# GenericAgent-TUI Agent Harness Instructions

## Architecture Baseline

The long-term architecture baseline for the GenericAgent multi-agent harness is stored in:

- `docs/agent-harness-architecture.md`

For any change that touches the TUI, subagents, task ledger, approvals, memory, artifacts, recovery, eval/trace, A2A, MCP, or orchestration behavior:

1. Before claiming the work is finished, compare the current implementation against `docs/agent-harness-architecture.md`.
2. Report whether the change moves the system closer to or farther from the baseline.
3. Call out any newly discovered gaps, especially around:
   - strong Orchestrator responsibility
   - restricted subagents
   - shared task/progress ledgers
   - artifact references and provenance
   - single-writer enforcement
   - human approval gates
   - auditable agent communication
   - external long-term memory
   - context pack / memory hydration
   - recovery, checkpointing, eval, and trace
   - A2A/MCP gateway compatibility
4. Do not treat "many agents chatting" as success. The target is a governed engineering system: one strong Orchestrator, bounded worker agents, explicit ledgers, artifact refs, approval gates, and auditable protocols.

## Concept Lifecycle And Patchification

When the user corrects a design by saying a concept is removed, fully deprecated, no longer part of the system, or must not be kept for compatibility, classify the operation as a concept lifecycle transition before editing code.

- Treat a purged concept as removed from the active system ontology, not as an active concept with an explicit rejection branch.
- Prefer deletion, positive schema definitions, ontology updates, generic unsupported-field handling, and invariant checks over local guards or special cases.
- Do not add runtime branches, prompt text, active docs, normal tests, user-facing errors, comments, or generated flowcharts that enumerate a purged concept.
- If compatibility or migration is truly required, it must be explicitly requested and isolated in compatibility or migration code with a removal plan.
- Normal tests should cover the current positive schema and generic boundary behavior. If regression protection is needed for a purged vocabulary, use an isolated absence/quarantine check rather than behavior-testing the retired concept.
- Final reports should explain the current source of truth and invariant, not how removed concepts are rejected.

Removed concepts should disappear from the active system. They must not survive as "forbidden branches" inside prompts, tests, docs, or runtime logic.
