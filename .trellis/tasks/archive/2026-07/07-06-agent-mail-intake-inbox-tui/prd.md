# Agent Mail Intake Inbox TUI

## Goal

Add a local TUI inbox for Agent Mail intake messages so the Orchestrator/user can inspect incoming local-adapter messages and decide what to do next. This makes Agent Mail intake visible as a governed control-plane queue instead of a hidden ledger-only record.

## What I Already Know

- Shuheng no longer has active Web/HTTP/mobile/remote surfaces.
- `append_agent_mail_intake_message(...)` already writes local Agent Mail, task ledger, and trace rows with `auto_dispatch:false`.
- Agent Mail intake must not dispatch runtimes, approve policy actions, write memory, execute workflows, or synthesize OMP-native state.
- The current architecture baseline wants a strong Orchestrator, explicit ledgers, human approval gates, artifact refs, and auditable communication.
- The local protocol naming task was completed in commit `21b24d2` and archived before this task.
- `_knowledge_base/` is unrelated and must not be touched.

## Requirements

- Add a TUI-visible Agent Mail intake inbox panel or command reachable from the local app.
- The inbox must show recent `agent_mail_intake` messages/tasks with enough metadata to decide: source, target, status, task id, message summary, timestamp, and delivery `auto_dispatch:false`.
- Provide an Orchestrator-owned local action for a selected intake item, at minimum one safe action that marks it reviewed/ignored or creates an explicit follow-up/delegation path through existing governed flows.
- Preserve the boundary: viewing/handling inbox items must not auto-dispatch runtime work, bypass approvals, mutate Secret Vault state, write long-term memory, or call OMP/provider APIs.
- Add tests/policy gates so Agent Mail intake visibility and no-auto-dispatch behavior are executable contracts.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the TUI inbox adds a new command, panel, or record status convention.

## Acceptance Criteria

- [x] User can open/inspect Agent Mail intake entries from the TUI command surface.
- [x] The inbox reads from existing local ledgers and renders entries without exposing hidden context, permission matrix internals, Secret plaintext, or local filesystem-only implementation details.
- [x] Handling an inbox item is explicit and Orchestrator-owned; it records auditable task/mail/trace/progress state as appropriate.
- [x] Unknown/invalid intake ids are handled cleanly without creating phantom tasks.
- [x] No Web/HTTP/SSE/push/mobile/remote surface is reintroduced.
- [x] Policy gates or tests cover the positive inbox path and the no-auto-dispatch boundary.
- [x] Quality gates pass: compile/Ruff/targeted tests/policy gates/runtime smoke/release hygiene/full pytest when feasible.
- [x] Final report compares the change against `docs/agent-harness-architecture.md`.

## Out Of Scope

- Web UI, HTTP endpoints, mobile/remote operations, SSE, push, or daemon behavior.
- Automatic execution of intake messages.
- OMP-native subagent state synthesis from Shuheng ledgers.
- Storage migration of historical local registry files.
- Touching `_knowledge_base/`.

## Technical Notes

- Likely files: `src/shuheng/app.py`, `scripts/check_policy_gates.py`, `tests/*`, `.trellis/spec/backend/agent-control-protocol.md`.
- Existing related helpers: `append_agent_mail_intake_message(...)`, `agent_mail_intake_message_text(...)`, `agent_mail_intake_message_target(...)`, `append_agent_mail(...)`, `append_task_ledger(...)`, `append_trace(...)`.
- Existing TUI panel patterns should be reused rather than adding a parallel UI system.
