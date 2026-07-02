# Extract latest user message helper

## Goal

Continue decomposing `src/ga_tui/app.py` by moving the pure transcript-bridge message selector into `src/ga_tui/history_store.py`, while keeping provider/runtime gating and transcript persistence orchestration in `app.py`.

## Requirements

- Extend `src/ga_tui/history_store.py`.
- Move pure helper:
  - `latest_user_message_text(messages)`
- Keep `src/ga_tui/app.py` compatibility alias for the moved helper.
- Preserve current semantics:
  - Scan messages from newest to oldest.
  - Return the stripped content of the newest user message whose content is non-empty after stripping.
  - Return an empty string when there is no such user message.
  - Ignore assistant/system messages and blank user messages.
- Add tests and policy gates for the expanded history-store boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the transcript helper boundary.

## Acceptance Criteria

- [ ] `ga_tui.history_store` owns `latest_user_message_text`.
- [ ] `ga_tui.app.latest_user_message_text` remains a direct alias or behavior-identical wrapper.
- [ ] `persist_transcript_bridge_turn(...)` keeps using the same helper behavior but remains in `app.py` because it depends on runtime provider state, app storage roots, and agent log-path checks.
- [ ] `history_store.py` still does not import `ga_tui.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, Web Console, dashboard, runtime dispatch, command handlers, or renderer functions.
- [ ] Unit tests cover newest-user selection, blank-user skipping, no-user fallback, and app alias parity.
- [ ] Phase exit verification passes.

## Definition of Done

- New helper location, app alias, tests, policy gate, and spec update are implemented.
- No behavior change to transcript bridge gating, normal session log path checks, provider/runtime state checks, storage roots, session metadata, Web Console payloads, or rendering.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Move the exact helper body from `app.py` into `history_store.py`. Replace the app function with `latest_user_message_text = history_store.latest_user_message_text` near existing history-store compatibility wrappers. Keep `persist_transcript_bridge_turn(...)` untouched except that it resolves the alias.

## Decision (ADR-lite)

Context: `persist_transcript_bridge_turn(...)` needs the last meaningful user prompt before appending a bridge transcript turn. The selection itself is independent from runtime provider checks, `State`, storage roots, and rendering.

Decision: Extract only the pure message selector now. Do not move transcript bridge orchestration yet.

Consequences: The transcript storage boundary grows incrementally while the high-level app facade still owns runtime/provider gating and normal-session path validation.

## Out of Scope

- Moving `persist_transcript_bridge_turn`, `agent_requires_transcript_bridge`, `agent_log_path`, `agent_log_path_is_devnull`, `append_model_response_transcript_turn`, runtime provider checks, storage-root checks, or any rendering/sidebar behavior.
- Changing transcript format or bridge persistence policy.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, Phase 2.
- Relevant spec scenario: `Session History Titles Ignore Process Summaries` and history-store boundary contracts.
- Existing transcript storage tests live in `tests/test_history_store.py`.
