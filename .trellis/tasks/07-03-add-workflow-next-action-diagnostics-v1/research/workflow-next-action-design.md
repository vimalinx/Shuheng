# Workflow Next-Action Diagnostics Design

## Decision

Implement diagnostics as a read-only command-level projection before adding
more automatic execution. The command should tell users which existing command
to run next, not run it for them.

## Rationale

- Shuheng already has explicit state transition commands. Diagnostics should
  not duplicate their logic or become a hidden executor.
- Recovery-oriented UX needs concise next-action hints in addition to detailed
  trace/provenance output.
- The safest MVP is a pure formatter fed by `app.py` ledger reads.

## Classification Rules

- `planned` -> recommend `/workflow continue <run_id>`.
- `waiting_approval` with pending approval -> recommend `/approve <approval_id>`
  or `/reject <approval_id>`, then `/workflow continue <run_id>`.
- `waiting_approval` with approved/rejected approval -> recommend
  `/workflow continue <run_id>`.
- `waiting_task` with non-terminal task -> recommend waiting and using
  `/workflow trace <run_id>` to inspect evidence.
- `waiting_task` with terminal task -> recommend `/workflow continue <run_id>`.
- terminal run -> recommend `/workflow trace <run_id>` or rerun the workflow.
- blocked condition/unsupported step -> recommend trace/cancel/edit, not hidden
  automatic continuation.
