# Extract Subagent Result Notice Format Helpers

## Goal

Continue Goal 7 by moving the remaining deterministic subagent-result notice formatting helpers out of `src/shuheng/app.py` into the lower-level curses-free rendering helper boundary, while preserving existing app compatibility wrappers and behavior.

## Requirements

- Move only pure subagent result notice formatting behavior into `src/shuheng/rendering.py`.
- Add a rendering helper that shapes the notice body from explicit `raw`, `rendered`, `final_reply`, `has_tool_noise`, and `limit` inputs.
- Add a rendering helper that formats the final subagent result notice text from explicit `name`, `agent_id`, `bus_task_id`, `artifact_ref`, and already-shaped `body`.
- Add a rendering helper that returns wrapped metadata detail strings for an already-parsed notice and metadata lines.
- Keep `src/shuheng/app.py` as the compatibility facade:
  - `subagent_result_notice_body(...)` keeps injecting `clean_text(...)`, `render_assistant_text(...)`, `latest_visible_reply_text(...)`, and `process_has_tool_noise(...)`.
  - `format_subagent_result_notice(...)` keeps injecting `SubAgentRuntime` fields.
  - `format_subagent_result_notice_parts(...)` keeps the public signature and delegates final string assembly.
  - `subagent_result_metadata_detail_blocks(...)` keeps allocating `RenderLine(..., cp(9))`.
- Preserve current behavior for folded process/tool notice text, final-reply fallback, long-result truncation suffixes, empty-result fallback, notice header/body assembly, task/artifact lines, and expanded metadata detail display.
- Keep app-owned subagent result card rendering, context update formatting, task ledger lookups, artifact IO, message block rendering, mutable state, caches, and curses attrs outside `rendering.py`.
- Add unit tests for direct rendering helper behavior and app wrapper/alias parity.
- Extend policy gates so the moved helpers are owned by `rendering.py`, app wrapper behavior matches, local duplicate definitions are absent from `app.py` where applicable, and `rendering.py` retains the no-reverse-dependency boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable helper boundary.

## Acceptance Criteria

- [ ] `src/shuheng/rendering.py` owns pure helpers for subagent result notice body shaping, final notice string assembly, and metadata detail line wrapping.
- [ ] `src/shuheng/app.py` exposes compatibility aliases or wrappers for the public helper names and has no local duplicate implementation for newly moved pure helpers.
- [ ] `render_subagent_result_body(...)`, `subagent_result_reply_excerpt(...)`, `format_subagent_result_context_update(...)`, `subagent_result_context_update_from_notice(...)`, `subagent_context_updates_from_messages(...)`, `subagent_result_card_blocks(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, `RenderLine` allocation, curses attrs, mutable `State`, message cache ownership, Web Console, dashboard, runtime dispatch, commands, storage roots, approvals, artifacts, Secret Vault behavior, and history ownership remain outside `rendering.py`.
- [ ] Tests cover direct rendering helper output, app wrapper dependency injection/parity, metadata detail wrapped strings, and `RenderLine` attr conversion remains app-owned.
- [ ] Policy gates cover helper ownership, representative behavior, app wrapper parity, duplicate-definition absence, and the rendering no-reverse-dependency boundary.
- [ ] Targeted tests, policy gates, full tests, release hygiene, package build, wheel smoke, `git diff --check`, and `shuheng-check` pass.

## Definition of Done

- Tests added or updated for helper behavior and compatibility wrappers.
- Policy gate updated for ownership and module-boundary regression checks.
- Backend spec updated for the durable notice-format helper boundary.
- Full Goal 7 verification chain passes.
- One focused work commit is created without staging unrelated untracked Trellis task directories, goal records, or `uv.lock`.

## Technical Approach

Use the same extraction pattern as the recent rendering layout and subagent-result notice helper slices:

- Move deterministic text transforms into `src/shuheng/rendering.py`.
- Keep app wrappers responsible for app-only dependencies and existing public signatures.
- Keep `RenderLine`, `cp(...)`, curses attrs, stateful caches, artifact/ledger IO, and context-update behavior in `src/shuheng/app.py`.
- Prefer explicit inputs over importing app-level helpers into `rendering.py`.

## Decision (ADR-lite)

Context: Task 151 moved notice parsing and metadata summary helpers to `rendering.py`, but notice body shaping and final notice assembly still sit in `app.py`. These helpers are deterministic once app-owned dependencies have produced rendered/final-reply strings and tool-noise flags.

Decision: Move the remaining pure notice formatting and metadata detail string wrapping into `rendering.py`, while leaving wrappers in `app.py` to inject rendering, visible-reply cleanup, process-noise detection, `SubAgentRuntime` fields, and `RenderLine` allocation.

Consequences: `app.py` loses another pure formatting slice without weakening the strong Orchestrator boundary. A later task can decide whether to introduce neutral card layout records, but this slice does not move card rendering or message block rendering.

## Out of Scope

- No changes to subagent result visual design.
- No extraction of `subagent_result_card_blocks(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, full assistant rendering, or message cache ownership.
- No movement of `render_assistant_text(...)`, `latest_visible_reply_text(...)`, `process_has_tool_noise(...)`, or `process_tools(...)` into `rendering.py`.
- No storage-root, history ownership, Secret Vault, Web Console, dashboard, command, runtime dispatch, approval, artifact, or ledger behavior changes.

## Technical Notes

- `docs/app-py-decomposition-plan.md` defines `rendering.py` as the owner of curses-agnostic rendering transforms first.
- `docs/agent-harness-architecture.md` requires the app facade to remain the strong Orchestrator for mutation, ledgers, approvals, artifacts, history, and side effects.
- `.trellis/spec/backend/agent-control-protocol.md` already records the Task 151 notice/metadata helper boundary and must be expanded for notice formatting helpers.
