# Extract recent history selection helper

## Goal

Continue decomposing `src/shuheng/app.py` by moving the pure recent-history row selection helper into `src/shuheng/history_store.py`, using the existing `path_utils` boundary for path normalization and preserving sidebar/home history behavior.

## Requirements

- Extend `src/shuheng/history_store.py`.
- Move pure helper:
  - `recent_history_items(history_entries, used_paths, limit)`
- Keep `src/shuheng/app.py` compatibility wrapper with the existing default `RECENT_SESSION_LIMIT`.
- Preserve current semantics:
  - Only rows with positive activity timestamps are eligible.
  - Rows whose normalized path is already in `used_paths` are excluded.
  - Rows are sorted by activity timestamp descending.
  - The result preserves `(idx, item)` shape and applies the caller-provided limit.
- Add tests and policy gates for the expanded history-store boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the recent-history helper boundary.

## Acceptance Criteria

- [ ] `shuheng.history_store` owns `recent_history_items`.
- [ ] `shuheng.app.recent_history_items` remains behavior-compatible and preserves the old default limit.
- [ ] `history_store.py` may depend on `path_utils.py` but still does not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, Web Console, dashboard, runtime dispatch, command handlers, or renderer functions.
- [ ] Unit tests cover sorting, zero-timestamp exclusion, used-path de-duplication, limit behavior, and app wrapper parity.
- [ ] Existing policy gates around recent history and history-store boundaries continue to pass.
- [ ] Phase exit verification passes.

## Definition of Done

- New helper location, app wrapper, tests, policy gate, and spec update are implemented.
- No behavior change to `load_history`, sidebar grouping, home session rows, session metadata writes, process-summary filtering, storage roots, Web Console payloads, or rendering.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Move the body of `app.recent_history_items(...)` into `history_store.py` and replace its `normalized_path(...)` call with `path_utils.normalized_path(...)`. Keep an app wrapper that injects `RECENT_SESSION_LIMIT` when `limit` is omitted so existing callers and tests remain compatible.

## Decision (ADR-lite)

Context: Recent history selection is a history-domain data projection, not TUI rendering. It is already consumed by sidebar grouping and dashboard/home rows, but the helper itself only filters, de-duplicates, and sorts tuples.

Decision: Move only the pure selector into `history_store.py`. Keep sidebar row formatting, labels, `State`, and render types in `app.py`.

Consequences: The history boundary grows in a safe direction and can now reuse the lower-level `path_utils` module without creating a reverse dependency into `app.py`.

## Out of Scope

- Moving `load_history`, `cached_session_rows`, sidebar row rendering, home row rendering, `RECENT_SESSION_LIMIT`, session categories, title/description generation, process-summary filtering, or metadata writes.
- Changing how pinned/recent/category groups are displayed.
- Changing history storage roots or legacy bootstrap behavior.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, Phase 2.
- Relevant spec scenarios: `Session History Titles Ignore Process Summaries`, `Path Utility Module Boundary`, and Shuheng-owned storage.
- Existing policy gate scenario for recent history lives in `scripts/check_policy_gates.py` around `recent_history_items(...)`.
