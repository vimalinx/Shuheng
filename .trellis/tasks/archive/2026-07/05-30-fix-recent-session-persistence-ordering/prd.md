# Fix Recent Session Persistence And Ordering

## Goal

Make the ordinary left-sidebar `Recent` section behave as a recency-by-activity view so users can find newly created or recently used sessions after restarting the TUI.

## What I Already Know

* The current ordinary `Recent` section is generated from `session_meta.json` entries that have `last_opened_at`.
* `last_opened_at` is written only by `restore_history()` via `mark_session_opened()`.
* New ordinary sessions created by `/new` or `Ctrl+N` are assigned a new log path but are not marked as opened.
* The user expects `Recent` to reflect the last time a message was sent, not the last time the session was clicked/opened.
* The user reports that previously created sessions are hard to find after restarting because they do not appear in `Recent`.

## Assumptions

* This task applies to ordinary non-Secret sessions only.
* Pinned sessions should still stay in `Pinned` and should not duplicate in `Recent`, matching the current sidebar grouping behavior.
* Archived and deleted sessions should continue to obey the current filters.
* Sessions with no persisted log content cannot be recovered after process restart unless the app creates a durable empty log or metadata-only row. The MVP focuses on sessions that have activity and a normal log file.

## Requirements

* `Recent` must be based on session activity time, preferably the cached `last_user_at` derived from the session log.
* Opening a historical session must not reorder `Recent` by click time.
* Newly created sessions that later receive user messages must appear in `Recent` after restart.
* The visible time in `Recent` should match the activity sort key rather than the open timestamp.
* Keep the existing `Pinned` de-duplication and archive/delete behavior.

## Acceptance Criteria

* [ ] A session with a newer user-message timestamp appears above an older session in `Recent`, even if the older session was opened more recently.
* [ ] A session with user-message activity but no `last_opened_at` metadata can appear in `Recent`.
* [ ] Opening a historical session does not change its `Recent` sort position.
* [ ] Existing pinned sessions are not duplicated in `Recent`.
* [ ] Quality checks cover the changed sidebar grouping behavior where practical.

## Definition Of Done

* Tests or focused validation cover the changed `Recent` behavior.
* Lint/type-check or syntax validation passes for touched Python code.
* The change is compared against `docs/agent-harness-architecture.md` before final reporting.
* Rollback is simple: restore the previous `Recent` candidate sort key and metadata behavior.

## Out Of Scope

* Secret Vault session recency behavior.
* Subagent chat session recency behavior.
* A full redesign of session categories.
* Recovering completely empty sessions with no log file after restart.

## Technical Notes

* Main file: `src/shuheng/app.py`.
* `load_history()` loads `session_meta.json` and cached session rows.
* `cached_session_rows()` computes and caches `last_user_at`.
* `draw_sidebar()` currently builds `Recent` from `last_opened_at`.
