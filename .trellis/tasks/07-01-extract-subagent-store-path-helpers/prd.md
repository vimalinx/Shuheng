# Extract subagent store path helpers

## Goal

Continue decomposing `src/shuheng/app.py` by introducing `src/shuheng/subagent_store.py` for pure subagent identity, home-path, and sidebar-key helpers, while preserving the invariant that normal non-secret subagent conversations are stored in global Shuheng history, not in per-agent session files.

## Requirements

- Add `src/shuheng/subagent_store.py`.
- Move or re-home pure helpers that do not require `State`, `SubAgentRuntime`, runtime providers, Secret Vault payload IO, history transcript parsing, or rendering:
  - `subagent_home_session_key(agent_id)`
  - `home_subagent_id_from_key(key)`
  - `is_main_home_session_key(key)`
  - `is_scheduled_reports_session_key(key)`
  - `is_home_session_key(key)`
  - `subagent_home(agent_id)` as an app compatibility wrapper over a parameterized lower-level helper.
  - `secret_subagent_home(agent_id)`
  - `subagent_meta_path(agent_id)` as an app compatibility wrapper.
  - `subagent_profile_path(agent_id)` as an app compatibility wrapper.
  - `subagent_memory_path(agent_id)` as an app compatibility wrapper.
  - `subagent_events_path(agent_id)` as an app compatibility wrapper.
  - `subagent_new_chat_session_id()`
  - `subagent_session_sidebar_key(agent_id, session_id)`
  - `subagent_session_from_sidebar_key(key)`
- Keep `src/shuheng/app.py` compatibility aliases or wrappers for all moved public names.
- Keep the existing `SUBAGENT_SESSION_PREFIX` value stable.
- Keep parameterized store helpers free of app storage-root globals where the root must remain app-owned.
- Add tests and policy gates for the new module boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the `subagent_store.py` boundary.

## Acceptance Criteria

- [ ] `shuheng.subagent_store` owns pure subagent path/key/session-id helpers.
- [ ] `shuheng.app` preserves existing public helper behavior through aliases or wrappers.
- [ ] Store helpers sanitize agent/session identifiers exactly as current `app.py` behavior does.
- [ ] Lower-level path helpers accept `SUBAGENTS_DIR` as an explicit parameter instead of importing `app.py` or reading app-owned storage roots.
- [ ] `subagent_store.py` does not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, runtime provider classes, Web Console, dashboard, history persistence, or rendering helpers.
- [ ] Unit tests cover sanitization, app wrapper parity, home-session keys, normal subagent file paths, secret virtual homes, chat session id shape, and sidebar-key round trips.
- [ ] Phase exit verification passes.

## Definition of Done

- New module, app wrappers/aliases, tests, policy gate, and spec update are implemented.
- No behavior change to normal history transcript persistence, Secret Vault payload storage, runtime dispatch, subagent metadata writes, profile/memory contents, Web Console payloads, or rendering.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Create a low-level module with a shared identifier sanitizer, home-session key helpers, explicit-root path helpers, secret virtual home refs, session-id generation, and sidebar-key encoding/decoding. Replace `app.py` function bodies with direct aliases where no app global is needed, and wrappers where `SUBAGENTS_DIR` must be injected by the app facade.

## Decision (ADR-lite)

Context: `app.py` currently owns both subagent home path helpers and the higher-level behavior that persists non-secret direct chat into global Shuheng history. Keeping all of that in one file obscures the user's corrected responsibility split: subagent homes store profile/memory/runtime refs, while conversation transcripts belong in global history or Secret Vault.

Decision: Extract only pure path/key helpers now. Do not move chat-history persistence, legacy `sessions/*.json` import, Secret Vault reads/writes, runtime creation, or metadata mutation in this slice.

Consequences: The subagent storage boundary becomes explicit without creating a second conversation owner or changing any runtime persistence behavior.

## Out of Scope

- Moving `subagent_file_path`, `subagent_meta_file`, `subagent_profile_file`, `subagent_memory_file`, `subagent_events_file`, `subagent_sessions_dir`, or `subagent_chat_session_file` because they take `SubAgentRuntime` or still participate in higher-level runtime wiring.
- Moving `save_subagent_chat_messages_to_history`, `subagent_chat_history_path_for_session`, `subagent_history_chat_session_entries`, `import_legacy_subagent_chat_sessions`, or any normal history transcript logic.
- Moving Secret Vault subagent storage helpers or encrypted payload handlers.
- Changing subagent profile/memory file contents, runtime provider state, sidebar rendering, or Web Console payloads.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, `subagent_store.py` boundary.
- Relevant spec scenarios: persistent subagent direct chat, state root migration, dashboard home keys, and external memory/approval boundaries in `.trellis/spec/backend/agent-control-protocol.md`.
- Existing policy-gate assertions around subagent memory and history ownership must keep passing unchanged.
