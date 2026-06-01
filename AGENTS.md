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
