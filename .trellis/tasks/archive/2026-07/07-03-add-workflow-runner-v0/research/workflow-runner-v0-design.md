# Workflow Runner V0 Design Note

## Question

How should Shuheng add automatic workflow execution without violating the governed agent harness baseline?

## Local Evidence

- `docs/agent-harness-architecture.md` prioritizes a strong Orchestrator, ledgers, artifact refs, single-writer behavior, human approval gates, auditable protocols, checkpointing, and bounded subagents.
- `.trellis/spec/backend/agent-control-protocol.md` already defines workflows as manifest-backed declarative data and currently limits `/workflow run` to planned ledger creation.
- `src/ga_tui/workflows.py` is already the pure parser/formatter owner and must not import runtime, app, governance, ledger, approval, provider, UI, Secret Vault, or subprocess owners.
- `src/ga_tui/app.py` already owns concrete harness paths and JSONL append operations.

## Design Conclusion

The safest runner v0 is append-only ledger progression, not real execution. It can prove workflow state-machine behavior and user-visible automation while keeping all high-risk operations gated for later tasks.

## Step-Type Policy

- `prompt`: safe to mark completed as a recorded prompt step; no model call is made in v0.
- `notify`: safe to mark completed as a ledger-only notification snapshot; no external send occurs.
- `pause`: safe to mark completed as an intentional no-op checkpoint in v0.
- `artifact_summary`: safe to mark completed only as a summary placeholder; no artifact row is written.
- `approval`: stop at `waiting_approval`; do not create a real approval row in v0.
- `agent_task`: stop at `blocked`; do not dispatch a subagent or write task/progress rows in v0.
- `condition`: stop at `blocked`; evaluating expressions or inspecting runtime state needs a later explicit contract.

## Ledger Shape

Use two rows per successful `/workflow run` call:

1. Initial `planned` row produced by `build_workflow_run_record(...)`.
2. Advanced row with the same `run_id`, updated step statuses, runner metadata, status, and stop reason.

This keeps history append-only and makes `latest_records_by_id(..., "run_id")` return the current run state without mutating old rows.

## Guardrails

- No task/progress/approval/artifact ledger writes.
- No subagent creation.
- No tool, shell, plugin code, provider, Secret Vault, memory, A2A, or MCP calls.
- No hidden condition evaluation.
- All non-safe steps stop the runner with a visible reason.
