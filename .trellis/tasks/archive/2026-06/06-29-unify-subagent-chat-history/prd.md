# Unify subagent chat history ownership

## Goal

Make Shuheng `history` the canonical storage for all visible conversations, including direct subagent chats, while keeping `agent sessions` limited to agent-local runtime/navigation metadata and references. This removes the current split where main conversations live under `model_responses/` but subagent conversations are duplicated as per-agent session JSON payloads.

## What I Already Know

* User confirmed the intended model: `history` should contain every conversation, including `agent sessions`; `agent sessions` should not own conversation transcripts.
* Current main history is stored under `MODEL_RESPONSES_DIR` with `model_responses*.txt`, `session_meta.json`, `session_names.json`, token usage, sidebar rows, and Web `session.open` projection.
* Current subagent direct chat persists full message arrays in `subagent.chat_session.v1` payloads under per-agent `sessions/*.json` or encrypted Secret Vault `subagent-chat` payloads.
* `chat_session_id` and `chat_title` in subagent metadata should remain as navigation/current-history refs, not authoritative transcript storage.
* Direct chat must remain direct chat, not a task-ledger `subagent_task`; task ledgers, events, artifacts, approvals, and memory candidates remain governance records around the conversation.
* This touches TUI, subagents, history, memory candidates, Web console, and orchestration behavior, so it must be checked against `docs/agent-harness-architecture.md` before finish.

## Requirements

* Store newly persisted direct subagent chat conversations in the global Shuheng history store under `MODEL_RESPONSES_DIR`, not in per-agent `sessions/*.json` transcript files.
* Mark subagent-owned history rows with metadata sufficient for filtering and restoration, including `conversation_scope` or equivalent, `agent_id`, `agent_name`, `subagent_chat_session_id`, security context, title, preview, message count, source, and timestamps.
* Keep subagent `meta.json` / encrypted meta limited to runtime and navigation state: current chat session id/ref, title, queue counts, dashboard, model, permissions/security, and status. It must not be the authoritative conversation transcript.
* `subagent_chat_session_entries(...)`, sidebar rows, home session sections, `/chat`, and `switch_to_subagent_chat_session(...)` must read subagent conversations from global history metadata.
* `load_subagent_chat_session(...)` must restore `sub.messages` from the selected global history transcript so existing chat panes continue to render.
* Existing legacy per-agent `sessions/*.json` and encrypted Secret Vault `subagent-chat` payloads must remain recoverable through migration or compatibility import so older conversations are not lost.
* Memory-candidate evidence refs for direct chat should point at the canonical history ref after this change.
* Web console agent conversation and Web `agent.chat` behavior must continue to use the same dispatcher and read from the canonical history-backed conversation state.
* Temporary subagents may keep process-local message state, but any persistent conversation that is saved must go through global history. Temporary behavior must not create long-lived private transcript stores.
* Secret subagent conversations must remain protected: do not leak Secret Vault plaintext into normal unencrypted history when the vault is unlocked. If they cannot share normal history safely, they must use an encrypted history-compatible store/ref and keep the same single-source principle inside Secret storage.

## Acceptance Criteria

* [ ] A new persistent non-secret subagent direct chat creates a `model_responses*.txt` history row with subagent metadata and no new authoritative transcript JSON under the agent's `sessions/` directory.
* [ ] `load_history()` can include subagent chat rows when appropriate metadata filters allow it, and subagent-specific UI can filter by `agent_id`.
* [ ] Reloading the app restores the current subagent chat from the canonical history row, including interrupted pending assistant rows being normalized as done.
* [ ] Switching between subagent chat sessions works from history-backed rows.
* [ ] `new_subagent_chat_session(...)` creates a new history-backed empty/current conversation ref without losing the previous conversation.
* [ ] Existing legacy per-agent `sessions/*.json` payloads are imported or read through a compatibility path and then represented as history-backed entries.
* [ ] Direct chat blocked-model/error paths persist the attempted user message and visible assistant error into canonical history.
* [ ] Queue notices and memory-candidate notices remain visible and persist in the selected conversation.
* [ ] Memory candidate evidence refs use canonical history refs for non-secret direct chat.
* [ ] Secret subagent direct chat remains encrypted and is not copied into normal history plaintext.
* [ ] Policy-gate tests assert that subagent sessions no longer own conversation message arrays as the authoritative non-secret storage.

## Technical Approach

Add a history-backed adapter for subagent chat rather than teaching every UI caller a new storage format. New helper functions should create/locate a canonical history path for a subagent chat session, serialize current `Message` objects using the existing model-response transcript format, and attach subagent metadata in `session_meta.json`.

`subagent_chat_session_entries(...)` should become a projection over history metadata plus a bounded legacy import/compatibility path. `save_subagent_chat_session(...)` should persist non-secret persistent subagent chats into global history and return the history path/ref. `load_subagent_chat_session(...)` should load messages from that history path. The old per-agent JSON payload format should be treated as legacy input only.

Secret subagent chat must not be written to normal plaintext history. It can keep encrypted Secret Vault records as the encrypted canonical store for Secret context, but the conceptual boundary remains the same: Secret agent session metadata stores refs, while encrypted Secret history/chat records store transcripts.

## Decision (ADR-lite)

**Context**: The old split makes `history` incomplete and causes agent sessions to become a second transcript store. That conflicts with the desired model and with the architecture baseline's preference for governed shared records and auditable communication.

**Decision**: Use global Shuheng history as the canonical transcript store for non-secret subagent direct chat; keep agent session metadata as refs/runtime state; preserve Secret Vault plaintext boundaries with encrypted canonical records.

**Consequences**: Sidebar/history and subagent UI can share one conversation source. Migration/compatibility logic is required for old per-agent session files. Some helper names may remain for UI compatibility but their implementation should project from history rather than owning files under `memory/subagents/.../sessions/`.

## Out of Scope

* Converting direct chat into task-ledger `subagent_task` records.
* Changing approval policy, role permissions, or single-writer task behavior.
* Reworking OMP native JSONL session storage beyond adding/providing refs in history metadata.
* Renaming all user-facing labels from `AGENT SESSIONS` in this task unless needed for correctness.
* Deleting legacy session files destructively.

## Technical Notes

* Relevant implementation entry points: `subagent_chat_session_payload`, `save_subagent_chat_session`, `subagent_chat_session_entries`, `load_subagent_chat_session`, `new_subagent_chat_session`, `switch_to_subagent_chat_session`, `subagent_sidebar_rows`, `subagent_recent_session_rows`, `web_console_agent_conversation`, `start_subagent_chat`, `process_ui_queue`.
* Main history helpers: `new_session_log_path`, `append_model_response_transcript_turn`, `load_session_meta_registry`, `save_session_meta_registry`, `set_session_meta_fields`, `cached_session_rows`, `load_history`.
* Tests to update: `assert_selected_subagent_chat_is_direct_session`, Secret Vault direct-chat assertions, Web console/session-open policy gates, and history ownership gates in `scripts/check_policy_gates.py`.
* Spec/docs likely need updates in `.trellis/spec/backend/agent-control-protocol.md` and `docs/runtime-provider-control-plane.md`.
* Architecture baseline comparison must report whether the implementation moves closer to strong Orchestrator, shared ledgers/history, artifact refs, auditable communication, external memory, and recovery/checkpoint expectations.
