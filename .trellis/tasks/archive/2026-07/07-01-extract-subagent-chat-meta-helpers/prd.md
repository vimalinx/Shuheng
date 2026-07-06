# Extract subagent chat meta helpers

## Goal

Continue decomposing `src/shuheng/app.py` by moving pure subagent chat metadata/ref constants and matching logic into `src/shuheng/subagent_store.py`, without moving conversation transcript ownership out of global Shuheng history.

## Requirements

- Extend `src/shuheng/subagent_store.py`.
- Move or re-home pure metadata/ref definitions:
  - `SUBAGENT_CHAT_HISTORY_SCOPE`
  - `SUBAGENT_CHAT_MESSAGES_META_KEY`
  - parameterized subagent chat history metadata matcher
- Keep `src/shuheng/app.py` compatibility constants/wrapper:
  - `SUBAGENT_CHAT_HISTORY_SCOPE`
  - `SUBAGENT_CHAT_MESSAGES_META_KEY`
  - `subagent_chat_history_meta_matches(meta, sub, session_id="")`
- Preserve semantics:
  - Metadata matches only when `conversation_scope == "subagent_chat"`.
  - Metadata matches only for the selected `agent_id`.
  - Optional `session_id` must match `subagent_chat_session_id` when provided.
  - Missing/empty optional session id should not reject otherwise matching metadata.
- Keep `subagent_store.py` free of `State`, `SubAgentRuntime`, `history_store`, Secret Vault storage, runtime providers, Web Console, dashboard, and rendering dependencies.
- Add tests and policy gates for the expanded module boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md`.

## Acceptance Criteria

- [ ] `shuheng.subagent_store` owns the subagent chat history scope constant and pure metadata matcher.
- [ ] `shuheng.app` preserves existing public constant values and wrapper behavior.
- [ ] New helper does not read `MODEL_RESPONSES_DIR`, write transcripts, parse transcript files, or inspect Secret Vault payloads.
- [ ] Unit tests cover matching scope, wrong agent rejection, optional session id behavior, app wrapper parity, and absence of transcript ownership in `subagent_store.py`.
- [ ] Phase exit verification passes.

## Definition of Done

- New helper location, app wrapper, tests, policy gate, and spec update are implemented.
- No behavior change to direct-chat persistence, legacy `sessions/*.json` import, Secret Vault payload storage, runtime dispatch, sidebar rendering, or Web Console actions.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Add constants and `subagent_chat_history_meta_matches(meta, agent_id, session_id="")` to `subagent_store.py`. Replace `app.py` constants with aliases and keep the existing `subagent_chat_history_meta_matches(meta, sub, session_id="")` signature as a wrapper that injects `sub.agent_id`.

## Decision (ADR-lite)

Context: `app.py` still mixes subagent metadata reference matching with high-level chat persistence. The matcher is a pure schema predicate and does not need `State`, runtime agents, storage roots, or transcript parsing.

Decision: Extract only the metadata/ref predicate and constants. Keep all transcript persistence and restoration logic in `app.py` / `history_store.py` for now.

Consequences: `subagent_store.py` becomes the source for subagent metadata ref shape, while global history remains the only plaintext non-secret conversation transcript owner.

## Out of Scope

- Moving `save_subagent_chat_messages_to_history`, `subagent_chat_history_path_for_session`, `subagent_history_chat_session_entries`, `messages_from_history_transcript`, or any transcript parsing/writing.
- Moving Secret Vault subagent chat payload read/write helpers.
- Moving `SubAgentRuntime` file helpers, runtime creation, UI rendering, Web Console payloads, or command handlers.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, `subagent_store.py` boundary.
- Relevant spec scenario: `Direct Subagent Chat Visibility`.
- This slice reinforces the invariant: subagent homes own profile/memory/runtime refs; normal non-secret conversation transcripts live in global history.
