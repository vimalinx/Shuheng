# Fix Subagent Message No Reply

## Goal

When a user sends a direct chat message to a persistent subagent, Shuheng must either dispatch the message and render the assistant reply, or show an explicit actionable state such as pending approval, queued behind active work, missing runtime, or runtime failure. The current user-visible problem is that direct subagent messages appear to get no reply.

## What I Already Know

* User reported: "现在我给子代理发消息他不回我".
* Shuheng is running locally as `/home/vimalinx/.local/bin/shuheng` with an OhMyPi RPC runtime process.
* Today's trace ledger has main-agent runtime activity through `2026-06-29T07:12:48+0800`, but today's task/message/approval ledgers do not show matching subagent-chat rows from the latest complaint.
* Historical approval/message rows show that approval-gated work can sit in `approval_inbox` as `pending`, so silent approval waits are a realistic no-reply failure mode.
* The active protocol spec says persistent-agent home plain text should switch to subagent chat and send the input, and that agent communication, approvals, task ledgers, artifacts, and traces must remain auditable.

## Requirements

* Direct subagent chat entry points must provide immediate user-visible feedback when a message is sent.
* If the chat is blocked by approval, runtime startup, a busy subagent, missing agent metadata, missing runtime, or an exception, the UI must show a clear status instead of appearing idle.
* A successfully dispatched direct chat must preserve the existing governed path: context pack, agent mail/task provenance where applicable, runtime provider provenance, queue draining, token persistence, and memory-candidate handling.
* The fix must not bypass approval gates, single-writer boundaries, or subagent permissions.
* The Web-console `agent.chat` path must stay consistent with the TUI path if it shares the same dispatcher.

## Acceptance Criteria

* [ ] Sending plain text while a persistent subagent chat/home is selected starts or queues direct subagent chat and leaves a visible pending assistant row or explicit status message.
* [ ] Approval-required or policy-blocked direct chat is surfaced with the approval id/status and does not look like a silent non-response.
* [ ] Runtime startup and terminal failures mark the subagent chat done/failed and release the subagent for later messages.
* [ ] Existing completed subagent chat replies still save to the subagent chat session, event log, token usage, and memory-candidate path.
* [ ] Policy gate tests cover the discovered no-reply failure.
* [ ] `ruff`, policy gates, targeted pytest, compileall, `git diff --check`, and `shuheng-check` pass or any external-environment blocker is documented.

## Technical Approach

1. Inspect the direct chat entry points in `src/ga_tui/app.py`, especially `start_subagent_chat`, `maybe_start_next_subagent_chat`, subagent home/chat plain-text routing, `consume_stream_queue_to_ui`, approval handling, and Web `/gui/action` chat dispatch.
2. Reproduce the silent path with existing tests or a new policy-gate scenario using fake subagents/runtimes.
3. Patch the smallest shared dispatcher/status path so every accepted input produces a visible state transition and every blocked path returns a structured, user-visible result.
4. Add regression coverage for the root cause.

## Decision

Context: A no-reply bug can mean the message was not routed, was queued, was approval-gated, or the runtime replied but the UI did not consume the stream.

Decision: Diagnose from runtime ledgers first, then patch the shared dispatch/status path rather than adding a local special-case message.

Consequences: The fix should move Shuheng closer to the governed Orchestrator baseline because it improves auditable communication and user-visible approval/runtime states without relaxing policy.

## Out of Scope

* Redesigning the whole subagent scheduler or runtime provider abstraction.
* Changing approval policy semantics.
* Migrating historical task/message ledgers.
* Fixing unrelated old pending approvals or deleted subagent metadata.

## Technical Notes

* Relevant spec: `.trellis/spec/backend/agent-control-protocol.md`.
* Relevant architecture baseline: `docs/agent-harness-architecture.md`.
* Relevant runtime provider doc: `docs/runtime-provider-control-plane.md`.
* Likely code: `src/ga_tui/app.py`, `scripts/check_policy_gates.py`, and focused tests under `tests/`.
* Runtime evidence checked: `~/.shuheng/memory/agent_harness/{approvals,tasks,messages,traces}.jsonl`, `~/.shuheng/memory/subagents/*/meta.json`, and current Shuheng/OhMyPi processes.
