# Extract history response body parser

## Goal

Continue decomposing `src/shuheng/app.py` by moving the pure model response-body text parser into `src/shuheng/history_store.py`, strengthening the history/transcript boundary without changing preview/title policy, session metadata ownership, Web Console behavior, or rendering.

## Requirements

- Extend `src/shuheng/history_store.py`.
- Move pure helper:
  - `assistant_text_from_response_body(response_body)`
- Keep `src/shuheng/app.py` compatibility alias for the moved helper.
- Preserve current parsing behavior:
  - Python literal list response bodies return joined text from `{"type": "text", "text": ...}` dicts and raw string blocks.
  - Python literal dict response bodies return joined `content` text-list items, or `content`, or `text`.
  - Unparseable response bodies fall back to `clean_text(response_body)`.
  - Other literal values fall back to `clean_text(str(value or ""))`.
- Add tests and policy gates for the expanded `history_store.py` boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the response-body parser boundary.

## Acceptance Criteria

- [ ] `shuheng.history_store` owns `assistant_text_from_response_body`.
- [ ] `shuheng.app` exposes `assistant_text_from_response_body` as a direct alias or behavior-identical wrapper.
- [ ] `history_store.py` remains a low-level history/transcript module and does not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, Web Console, dashboard, runtime dispatch, command handlers, or rendering functions.
- [ ] Tests prove list, dict-with-content-list, dict-with-content-string, malformed body fallback, and app alias parity.
- [ ] Existing history-store tests continue to pass.
- [ ] Phase exit verification passes.

## Definition of Done

- New helper, app alias, tests, policy gate, and spec boundary update are implemented.
- No behavior change to session preview, process-summary filtering, history metadata cache invalidation, subagent chat storage, Web Console history payloads, or rendering.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Move the exact parser implementation from `app.py` into `history_store.py` and import `ast` there. In `app.py`, alias `assistant_text_from_response_body = history_store.assistant_text_from_response_body` near existing history-store compatibility wrappers.

## Decision (ADR-lite)

Context: `session_response_preview_text(...)` and Web Console/session restoration need to parse model response blocks, but the parser itself is independent from title policy, process-marker filtering, metadata cache policy, `State`, and rendering.

Decision: Extract only the response-body text parser now. Leave `session_response_preview_text`, `session_summary_titles_from_text`, `is_process_only_session_title`, metadata refresh, and sidebar/Web Console projections in `app.py` until their regex and state dependencies are split.

Consequences: Later history boundary work can reuse the low-level parser without importing `app.py`, while the higher-risk process-summary/title policy remains unchanged.

## Out of Scope

- Moving `session_response_preview_text`, `session_preview_from_pairs`, `session_summary_titles_from_text`, `is_process_only_session_title`, `history_cache_has_process_only_preview`, `message_text_for_metadata_context`, `session_description_from_pairs`, `session_description_from_path`, Web Console history/session payloads, sidebar rows, or history metadata cache refresh.
- Moving process/tool/detail regex constants.
- Changing title selection, process-summary filtering, `session_meta.json` semantics, global history ownership, subagent chat storage, Secret Vault behavior, or storage roots.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, Phase 2.
- Relevant spec scenario: `.trellis/spec/backend/agent-control-protocol.md`, `Session History Titles Ignore Process Summaries`.
- Existing tests for history store live in `tests/test_history_store.py`.
