# Extract subagent chat preview helpers

## Goal

Continue decomposing `src/shuheng/app.py` by moving pure subagent chat message normalization and preview/count helpers into `src/shuheng/subagent_store.py`, while keeping transcript persistence, Secret Vault payload decoding, runtime state, and UI rendering in their existing owners.

## Requirements

- Extend `src/shuheng/subagent_store.py`.
- Move pure helpers:
  - `normalize_loaded_subagent_chat_messages(messages)`
  - `subagent_chat_history_preview_messages(messages, limit=20)`
  - `subagent_chat_history_rounds(messages)`
  - `subagent_chat_history_last_user_at(messages, fallback)`
- Keep `src/shuheng/app.py` compatibility aliases for all moved public names.
- Preserve current semantics:
  - Interrupted trailing assistant messages are converted to done assistant messages with the existing interruption suffix.
  - Preview messages include only `user`, `assistant`, and `system` roles.
  - Preview messages are taken from the last `limit` messages and skip blank cleaned content.
  - Round count is the number of non-blank user messages.
  - Last-user timestamp helper preserves current fallback-only behavior.
- Add tests and policy gates for the expanded `subagent_store.py` boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md`.

## Acceptance Criteria

- [ ] `shuheng.subagent_store` owns the selected pure helpers.
- [ ] `shuheng.app` preserves wrapper/alias behavior for existing callers.
- [ ] `subagent_store.py` may depend on `ui_types.Message` and `text_utils.clean_text`, but must not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, `history_store`, `secret_vault`, runtime providers, Web Console, dashboard, or rendering helpers.
- [ ] Unit tests cover interrupted assistant normalization, preview filtering/limit/cleaning, round count, fallback timestamp behavior, and app alias parity.
- [ ] Phase exit verification passes.

## Definition of Done

- New helper location, app aliases, tests, policy gate, and spec update are implemented.
- No behavior change to `messages_from_subagent_chat_payload(...)`, Secret Vault record decoding, normal history transcript persistence, legacy session import, runtime dispatch, sidebar rendering, or Web Console actions.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Move the exact helper bodies into `subagent_store.py`. Replace the app functions with direct aliases. Keep `messages_from_subagent_chat_payload(...)` in `app.py` because it decodes Secret Vault message records through the app/secret-vault boundary.

## Decision (ADR-lite)

Context: `app.py` still owns several pure subagent chat helper functions used to prepare metadata previews and restore interrupted assistant rows. They are independent from storage roots, runtime providers, and UI rendering.

Decision: Extract only the pure message normalization/preview/count helpers. Do not move payload decoding, title/description generation, transcript persistence, or restoration orchestration.

Consequences: `subagent_store.py` becomes a clearer low-level owner for subagent chat metadata shaping while history and Secret Vault remain the only transcript/payload storage owners.

## Out of Scope

- Moving `messages_from_subagent_chat_payload(...)` because it depends on Secret Vault message record decoding.
- Moving `subagent_chat_history_preview(...)` or `subagent_chat_history_description(...)` because they depend on higher-level title/description and visible-reply policies still in `app.py`.
- Moving `save_subagent_chat_messages_to_history`, `subagent_chat_history_path_for_session`, or transcript parsing/writing.
- Moving any `State`, `SubAgentRuntime`, runtime provider, Web Console, command, or rendering behavior.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, `subagent_store.py` boundary.
- Relevant spec scenario: `Direct Subagent Chat Visibility`.
- This slice preserves the invariant that normal non-secret conversations live in global history, not in subagent homes.
