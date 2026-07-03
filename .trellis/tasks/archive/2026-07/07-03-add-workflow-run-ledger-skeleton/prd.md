# Add Workflow Run Ledger Skeleton

## Goal

Add the first governed execution boundary for declarative workflows: a durable workflow run ledger and a `/workflow run <ref>` entry point that creates a planned run record without executing any workflow step. This prepares Shuheng for future workflow execution while preserving the strong Orchestrator, approval, ledger, artifact, and single-writer boundaries.

## What I Already Know

- `src/ga_tui/workflows.py` owns pure workflow definition parsing, validation, and bounded formatting.
- `src/ga_tui/plugins.py` owns manifest-declared workflow ref resolution.
- `src/ga_tui/app.py` owns TUI command routing and panel rendering.
- `src/ga_tui/ledger_store.py` owns JSONL append/read/cache mechanics.
- Existing harness ledgers live under `AGENT_HARNESS_DIR` and use `*.jsonl` files plus `ledger_store.append_jsonl(...)`.
- The previous workflow registry task explicitly kept dry-run side-effect-free and forbade subagent dispatch, approvals, tools, plugin code, and workflow run ledgers.

## Requirements

- Add a workflow run ledger path under the harness state root, separate from task/progress ledgers.
- Add pure workflow run record helpers that can create an initial planned run record from a validated workflow definition.
- Add a `/workflow run <plugin-id>/<workflow-id>` command that records a planned run and returns the run id plus planned step count.
- Reject invalid workflow definitions before creating a run record.
- The initial run record must include at least: `schema_version`, `run_id`, timestamp, `status`, `workflow_ref`, plugin/workflow ids, workflow name, source path, input snapshot, permissions metadata, validation issue summary, and step snapshots.
- Step snapshots must include each step id, type, name, dependencies, target agent/ref/prompt metadata, and an initial `pending` status.
- The command must not execute any step, dispatch subagents, create approvals, write artifacts, call tools, mutate task/progress ledgers, alter permissions, or run plugin code.
- Keep Secret Vault isolation unchanged: `/workflow run` remains blocked while the vault is unlocked because `/workflow` is already a normal harness command.
- Update backend spec and policy gates so the run ledger skeleton remains declarative/planned-only.

## Acceptance Criteria

- [ ] Valid workflow definitions can produce a planned workflow run row in a JSONL ledger.
- [ ] Invalid workflow definitions return visible validation issues and do not append a workflow run row.
- [ ] `/workflow run <ref>` returns text containing the run id, status, workflow ref, and a statement that no steps executed.
- [ ] Tests prove `/workflow run` does not create subagents, approvals, artifacts, task ledger rows, progress ledger rows, or dispatch runtime work.
- [ ] Policy gates assert the workflow run helper remains pure from app/runtime/UI/governance owners except the low-level JSONL storage helper if used explicitly.
- [ ] Existing `/workflows`, `/workflow info`, and `/workflow dry-run` behavior remains green.

## Definition of Done

- Tests added/updated for pure run record creation and command behavior.
- `scripts/check_policy_gates.py` covers planned-only run invariants.
- `.trellis/spec/backend/agent-control-protocol.md` documents the run ledger skeleton contract.
- Targeted compile, Ruff, workflow/plugin/command tests, policy gate, and `git diff --check` pass.
- Architecture baseline comparison says the change moves Shuheng closer to the governed harness target.

## Technical Approach

- Extend `src/ga_tui/workflows.py` with pure run record dataclasses/helpers, keeping it independent from `app.py`, curses, runtime dispatch, approval queues, artifacts, and task/progress ledgers.
- Add a harness path constant in `app.py`, e.g. `AGENT_WORKFLOW_RUNS_PATH = os.path.join(AGENT_HARNESS_DIR, "workflow_runs.jsonl")`.
- Add app-level wrappers to append/read workflow run rows through `ledger_store`.
- Extend `handle_workflow_command(...)` with `/workflow run <ref>` after validation succeeds.
- Keep runner behavior explicitly out of scope; this task only persists `status=planned` rows.

## Decision (ADR-lite)

**Context**: Users need workflows to become executable eventually, but directly executing from `/workflow run` would bypass unproven approval, recovery, artifact, and single-writer semantics.

**Decision**: Add a planned-only workflow run ledger first. `/workflow run` creates an auditable run record but does not execute any step.

**Consequences**: Future work can add approval gating and step advancement against a durable run id. Users get visible progress toward workflows without introducing hidden side effects.

## Out of Scope

- Executing workflow steps.
- Advancing step status beyond initial `pending`.
- Dispatching `agent_task` steps.
- Creating approval requests for `approval` steps.
- Writing workflow artifacts.
- Scheduling, retry, resume, cancellation, or recovery.
- A `/workflow runs` panel or run detail viewer.
- A2A/MCP remote workflow services.

## Technical Notes

- Relevant code: `src/ga_tui/workflows.py`, `src/ga_tui/app.py`, `src/ga_tui/ledger_store.py`, `tests/test_workflows.py`, `tests/test_commands.py`, `scripts/check_policy_gates.py`.
- Relevant spec: `.trellis/spec/backend/agent-control-protocol.md`.
- Research note: `research/workflow-run-ledger-design.md`.
