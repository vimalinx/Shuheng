# Extract Subagent Result Context Update Helpers

## Goal

Continue Goal 7 by moving deterministic subagent-result context-update text helpers out of `src/ga_tui/app.py` into the lower-level curses-free rendering helper boundary, while preserving app-owned ledger/session injection and existing behavior.

## What I Already Know

- `src/ga_tui/app.py` currently owns `subagent_result_reply_excerpt(...)`, `format_subagent_result_context_update(...)`, `subagent_result_context_update_from_notice(...)`, and `subagent_context_updates_from_messages(...)`.
- Recent slices already moved subagent result notice parsing, metadata splitting, metadata summary/detail strings, notice-body shaping, and final notice assembly into `src/ga_tui/rendering.py`.
- `format_subagent_result_context_update(...)` still mixes deterministic text assembly with app-owned task-ledger lookups via `latest_task_records()`.
- `subagent_context_updates_from_messages(...)` still mixes deterministic de-duplication/budget selection with app-owned `Message` objects and `session_key(path)` injection.
- `docs/agent-harness-architecture.md` requires a strong Orchestrator: ledgers, approvals, artifacts, history, and side effects must remain app-owned or in governed service modules.

## Assumptions

- This slice should keep `app.py` as the compatibility facade for all existing public helper names.
- `rendering.py` may own deterministic text transforms over explicit inputs, but it must not read task ledgers, parse session paths, inspect `State`, allocate `RenderLine`, call curses, or perform storage/runtime side effects.
- `subagent_result_context_update_from_notice(...)` can remain an app wrapper because it combines notice parsing with app-owned defaults and public compatibility.

## Requirements

- Add a pure helper in `src/ga_tui/rendering.py` that builds a reply excerpt and metadata line tuple from an already-rendered subagent result body and an explicit limit.
- Add a pure helper in `src/ga_tui/rendering.py` that extracts the first `Confidence` metadata value from already-parsed metadata lines, preserving inline-markdown cleanup and truncation behavior.
- Add a pure helper in `src/ga_tui/rendering.py` that formats the final context-update text from explicit `session_key_value`, subagent identity, task/artifact ids, parent/plan ids, role, confidence, and reply excerpt.
- Add a pure helper in `src/ga_tui/rendering.py` that selects bounded context-update strings from an explicit list using the existing newest-first, de-duplicate, count limit, and total-character budget behavior.
- Keep `src/ga_tui/app.py` as the compatibility facade:
  - `subagent_result_reply_excerpt(...)` keeps injecting `render_subagent_result_body(...)` and the default `SUBAGENT_CONTEXT_REPLY_LIMIT`.
  - `format_subagent_result_context_update(...)` keeps injecting `latest_task_records()` task/parent/plan/role fields.
  - `subagent_result_context_update_from_notice(...)` keeps parsing notices and passing app-owned session defaults.
  - `subagent_context_updates_from_messages(...)` keeps iterating app `Message` objects and injecting `session_key(path)`.
- Preserve existing behavior for empty result fallback, long excerpt truncation suffix, `Confidence` markdown cleanup and 80-cell truncation, missing task/artifact/role/parent/plan fields, duplicate context updates, newest-first selection, and total budget enforcement.
- Do not move `render_subagent_result_body(...)`, `render_assistant_text(...)`, `latest_task_records(...)`, `session_key(...)`, `Message`, history ownership, task-ledger lookups, artifact IO, caches, mutable `State`, `RenderLine`, curses attrs, Web Console, dashboard, runtime dispatch, commands, Secret Vault behavior, or storage roots into `rendering.py`.
- Add unit tests for direct rendering helper behavior and app wrapper/alias parity.
- Extend policy gates so the moved helpers are owned by `rendering.py`, app wrapper behavior matches, local duplicate definitions are absent from `app.py` where applicable, and `rendering.py` retains the no-reverse-dependency boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable context-update helper boundary.

## Acceptance Criteria

- [ ] `src/ga_tui/rendering.py` owns pure helpers for subagent result reply excerpt shaping, context-update confidence extraction, final context-update text assembly, and bounded update selection.
- [ ] `src/ga_tui/app.py` exposes compatibility aliases or wrappers for the public helper names and has no local duplicate implementation for newly moved pure helpers.
- [ ] App-owned wrappers continue to inject rendered subagent bodies, task-ledger fields, session keys, and `Message` traversal.
- [ ] `rendering.py` does not import `ga_tui.app`, curses, mutable `State`, runtime dispatch, command handlers, Web Console, dashboard, input handlers, draw functions, storage-root owners, task ledgers, or artifact IO.
- [ ] Tests cover direct helper output, app wrapper dependency injection/parity, long excerpt truncation, confidence cleanup, duplicate/update-budget selection, and existing notice-to-context behavior.
- [ ] Policy gates cover helper ownership, representative behavior, wrapper parity, duplicate-definition absence, and the rendering no-reverse-dependency boundary.
- [ ] Targeted tests, policy gates, full tests, release hygiene, package build, wheel smoke, `git diff --check`, and `shuheng-check` pass.

## Definition of Done

- Tests added or updated for helper behavior and compatibility wrappers.
- Policy gate updated for ownership and module-boundary regression checks.
- Backend spec updated for the durable context-update helper boundary.
- Full Goal 7 verification chain passes.
- One focused work commit is created without staging unrelated untracked Trellis task directories, goal records, or `uv.lock`.

## Technical Approach

- Keep the extraction in `src/ga_tui/rendering.py` because these helpers are deterministic text transforms tied to the existing notice/metadata helper group.
- Use explicit inputs for every app-owned dependency:
  - already-rendered body text for excerpt shaping;
  - metadata lines for confidence extraction;
  - already-resolved parent/plan/role values for final text assembly;
  - already-built update strings for budget selection.
- Keep `app.py` wrappers thin and compatibility-preserving.

## Decision (ADR-lite)

Context: Task 151 and Task 152 moved deterministic subagent result notice helpers into `rendering.py`. Context-update formatting is the next adjacent pure-text slice, but it currently touches task ledgers and session keys.

Decision: Move only the deterministic text assembly and selection logic into `rendering.py`; keep ledger/session/message traversal in `app.py`.

Consequences: `app.py` loses another pure formatting slice without weakening the strong Orchestrator boundary. Later slices can target card/message rendering only after `RenderLine`, curses attrs, message cache, and process rendering dependencies have cleaner boundaries.

## Out of Scope

- No changes to subagent result context-update copy or visual design.
- No extraction of `subagent_result_card_blocks(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, `render_assistant_text(...)`, or message cache ownership.
- No movement of `latest_task_records(...)`, `session_key(...)`, `Message`, task ledgers, artifact IO, runtime dispatch, approvals, Secret Vault, Web Console, dashboard, command, storage-root, or history ownership.
- No storage migration or transcript ownership change.

## Technical Notes

- `docs/app-py-decomposition-plan.md` defines `rendering.py` as the owner of curses-agnostic rendering transforms first.
- `docs/agent-harness-architecture.md` requires the app facade to remain the strong Orchestrator for mutation, ledgers, approvals, artifacts, history, and side effects.
- `.trellis/spec/backend/agent-control-protocol.md` already records the notice/metadata and notice-format helper boundaries; this task should extend that boundary only for deterministic context-update text helpers.
