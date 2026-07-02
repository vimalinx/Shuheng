# Extract Subagent Result Notice Helpers

## Goal

Continue Goal 7 by moving deterministic subagent-result notice parsing and metadata summary helpers out of `src/ga_tui/app.py` into the lower-level curses-free rendering helper boundary, while preserving existing app compatibility names and behavior.

## Requirements

- Move pure subagent result notice parsing and metadata text helpers into `src/ga_tui/rendering.py`.
- Keep `src/ga_tui/app.py` as the compatibility facade by re-exporting moved helper names.
- Preserve current behavior for Chinese subagent result notices, optional task/artifact headers, body extraction, metadata footer detection, metadata label/value extraction, metadata entry grouping, metadata label lists, list-like count summaries, metadata summary text, and deterministic meta labels.
- Keep app-owned subagent result card rendering in `app.py`.
- Keep app-owned context update formatting, history/session key behavior, task ledger lookups, artifact IO, message block rendering, mutable state, caches, and curses attrs outside `rendering.py`.
- Add unit tests for direct rendering helper behavior and app alias parity.
- Extend policy gates so the moved helpers are owned by `rendering.py`, app compatibility aliases match, local duplicate definitions are absent from `app.py`, and `rendering.py` retains the no-reverse-dependency boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable helper boundary.

## Acceptance Criteria

- [ ] `src/ga_tui/rendering.py` owns `SUBAGENT_RESULT_HEADER_RE`, `SUBAGENT_RESULT_META_LABEL_RE`, `parse_subagent_result_notice(...)`, `subagent_result_metadata_separator(...)`, `subagent_result_metadata_label(...)`, `subagent_result_metadata_value(...)`, `split_subagent_result_reply_and_metadata(...)`, `subagent_result_metadata_labels(...)`, `count_list_like_metadata_value(...)`, `subagent_result_metadata_entries(...)`, `subagent_result_metadata_summary(...)`, and `subagent_meta_label(...)`.
- [ ] `src/ga_tui/app.py` exposes the same public names as direct compatibility aliases and has no local definitions for those moved helpers.
- [ ] `subagent_result_card_blocks(...)`, `subagent_result_metadata_detail_blocks(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, `RenderLine` allocation, curses attrs, mutable `State`, message cache ownership, Web Console, dashboard, runtime dispatch, commands, storage roots, approvals, artifacts, Secret Vault behavior, and history ownership remain outside `rendering.py`.
- [ ] Targeted tests, policy gates, full tests, release hygiene, package build, wheel smoke, `git diff --check`, and `shuheng-check` pass.

## Definition of Done

- Tests added or updated for helper behavior and compatibility aliases.
- Policy gate updated for ownership and module-boundary regression checks.
- Backend spec updated if the helper boundary is durable.
- Full Goal 7 verification chain passes.
- One focused work commit is created without staging unrelated untracked Trellis task directories, goal records, or `uv.lock`.

## Technical Approach

Use the same pattern as the recent rendering layout extractions:

- Move only deterministic text transforms into `src/ga_tui/rendering.py`.
- Keep `app.py` aliases for existing tests/callers.
- Keep higher-level functions that allocate `RenderLine` or use `cp(...)` in `app.py`.
- Reuse `rendering.strip_inline_markdown(...)`, `text_utils.clean_text(...)`, and `text_utils.truncate_cells(...)` from the lower-level module.

## Decision (ADR-lite)

Context: Subagent result cards still live in `app.py`, but their notice parsing and metadata summary helpers are pure text processing. Leaving these helpers in `app.py` keeps the monolith larger and makes future message rendering extraction harder.

Decision: Move the pure notice/metadata helper group to `rendering.py` first, and leave `RenderLine` card assembly in `app.py` until a later explicit render-line boundary exists.

Consequences: This reduces `app.py` without changing UI behavior. The next later slice can decide whether to extract neutral subagent-result card layout records or keep card assembly in the app facade longer.

## Out of Scope

- No changes to subagent result card visual design.
- No extraction of `subagent_result_card_blocks(...)` or `subagent_result_metadata_detail_blocks(...)`.
- No extraction of `message_block_lines(...)`, `message_lines_from_cache(...)`, full assistant rendering, or message cache ownership.
- No storage-root, history ownership, Secret Vault, Web Console, dashboard, command, runtime dispatch, or approval behavior changes.

## Technical Notes

- `docs/app-py-decomposition-plan.md` defines `rendering.py` as the owner of curses-agnostic rendering transforms first.
- `docs/agent-harness-architecture.md` requires the app facade to remain the strong Orchestrator for mutation, ledgers, approvals, artifacts, history, and side effects.
- Existing helper cluster currently lives near `src/ga_tui/app.py` message rendering.
- Prior plain/markdown/table layout slices already established the compatibility-alias and policy-gate pattern.
