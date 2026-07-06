# Extract compact title text helpers

## Goal

Continue decomposing `src/shuheng/app.py` by moving pure compact title/category text helpers into `src/shuheng/text_utils.py`, preparing for later history/sidebar extraction without changing session, metadata, rendering, or storage behavior.

## Requirements

- Extend `src/shuheng/text_utils.py`.
- Move pure helper functions:
  - `compact_title(text, max_width=24)`
  - `compact_category(text)`
- Keep `src/shuheng/app.py` compatibility aliases for the moved names.
- Preserve current text cleaning behavior:
  - ANSI cleanup via `clean_text`.
  - fenced-code/html/markdown marker stripping.
  - whitespace collapse.
  - leading user/summary/completion phrase cleanup.
  - terminal-cell truncation via `truncate_cells`.
  - category sentinel handling for `-`, `clear`, `none`, `null`, and `未分类`.
- Add tests and policy gates for the expanded `text_utils.py` boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the compact title helper boundary.

## Acceptance Criteria

- [ ] `shuheng.text_utils` owns `compact_title` and `compact_category`.
- [ ] `shuheng.app` exposes `compact_title` and `compact_category` as direct aliases or behavior-identical wrappers.
- [ ] `text_utils.py` remains a pure leaf module and does not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, runtime providers, history storage, ledgers, Web Console, dashboard, or command handlers.
- [ ] Tests prove title cleanup strips code/html/markdown markers, trims user/task boilerplate, keeps CJK width truncation behavior, and filters category sentinel values.
- [ ] Existing cell/text utility tests continue to pass.
- [ ] Phase exit verification passes.

## Definition of Done

- New helpers, app aliases, tests, policy gate, and spec boundary update are implemented.
- No behavior change to session titles, category labels, sidebar rendering, history metadata, or runtime state.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Move the exact existing implementations from `app.py` into `text_utils.py`, using the already extracted `clean_text` and `truncate_cells` helpers. Import the helpers into `app.py` alongside the other text utility aliases.

## Decision (ADR-lite)

Context: The history boundary still depends on title/description cleaning, but `compact_description` currently depends on control/procedure regexes that are not yet lower-level. `compact_title` and `compact_category` are already pure leaf helpers.

Decision: Extract only `compact_title` and `compact_category` now. Leave `compact_description`, process-summary logic, history metadata, sidebar projection, and transcript parsing in `app.py` or `history_store.py` until their dependencies are cleanly separated.

Consequences: Later history/sidebar extraction can reuse a lower-level title/category contract without pulling in `app.py`.

## Out of Scope

- Moving `compact_description`, `session_description_from_pairs`, `session_response_preview_text`, `session_summary_titles_from_text`, `is_process_only_session_title`, history metadata refresh, sidebar row rendering, Web Console history payloads, transcript parsing, or any storage root.
- Moving regex constants for process/tool/detail fences.
- Changing visible title/category copy, session naming behavior, category registry behavior, history ownership, subagent session storage, Secret Vault behavior, or release posture.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, Phase 1 and Phase 2.
- Existing `text_utils.py` already owns `ANSI_RE`, `cell_width`, `truncate_cells`, `pad_cells`, `clean_text`, and `wrap_cells`.
- Existing `tests/test_cell_utils.py` covers app re-export parity for text utilities.
