# Extract Rendering Inline Markdown Helper

## Goal

Move the deterministic inline markdown cleanup helper into the lower-level `src/ga_tui/rendering.py` module as a public helper, while keeping `src/ga_tui/app.py` as the compatibility facade and owner of table rendering, markdown block rendering, `RenderLine` allocation, curses attrs, process/tool parsing, mutable UI state, command/input handling, and runtime side effects.

## Requirements

- `src/ga_tui/rendering.py` must expose `strip_inline_markdown(text: str) -> str`.
- Existing rendering-internal callers must use the public `strip_inline_markdown(...)` helper instead of the private `_strip_inline_markdown(...)`.
- `src/ga_tui/app.py` must re-export `strip_inline_markdown = rendering_helpers.strip_inline_markdown` for compatibility.
- The local `def strip_inline_markdown(...)` implementation must be removed from `src/ga_tui/app.py`.
- Existing app-owned callers in table rendering, markdown block rendering, and metadata parsing may continue to call `strip_inline_markdown(...)` through the compatibility alias.
- Tests must cover direct helper behavior and app alias parity.
- Policy gates must assert helper ownership in `rendering.py`, app alias compatibility, representative behavior, absence of the local `app.py` implementation, and the existing rendering no-reverse-dependency boundary.
- The backend spec must document the helper boundary and exclusions.

## Acceptance Criteria

- [ ] `rendering.strip_inline_markdown("![alt](url)") == "[alt]"`.
- [ ] `rendering.strip_inline_markdown("[text](url)") == "text (url)"`.
- [ ] Inline code backticks are removed without changing the content.
- [ ] Bold, italic, and underscore emphasis markers are removed without changing the content.
- [ ] `app.strip_inline_markdown is rendering.strip_inline_markdown`.
- [ ] `src/ga_tui/app.py` no longer defines a local `strip_inline_markdown(...)` function.
- [ ] `rendering.py` remains curses-free and must not import `ga_tui.app`, mutable `State`, runtime agent classes, command/input handlers, Web Console, dashboard, storage roots, approvals, artifacts, history ownership, or gateway handlers.
- [ ] Targeted compile, Ruff, rendering tests, policy gates, full release gates, package build, wheel smoke, and `shuheng-check` pass.

## Definition of Done

- Tests added or updated for direct helper behavior and compatibility alias parity.
- `scripts/check_policy_gates.py` updated to lock the ownership boundary.
- `.trellis/spec/backend/agent-control-protocol.md` updated with the durable rendering helper contract.
- `docs/agent-harness-architecture.md` checked for architecture direction before completion.
- Changes committed as one coherent work commit.

## Technical Approach

Rename the private `_strip_inline_markdown(...)` implementation in `rendering.py` to public `strip_inline_markdown(...)`, update the three visible-reply policy call sites in `rendering.py`, add the app compatibility alias in the rendering alias block, and delete the duplicate app-local implementation. This keeps all existing app call sites source-compatible while removing duplicated logic from the app facade.

## Decision (ADR-lite)

Context: both `app.py` and `rendering.py` currently carry equivalent inline markdown cleanup logic, which makes future rendering cleanup drift-prone.

Decision: make the lower-level rendering helper the single owner of inline markdown cleanup and keep `app.py` as a re-exporting compatibility facade.

Consequences: text cleanup behavior becomes policy-gated in one place. Table rendering, markdown block rendering, metadata parsing, `RenderLine` allocation, curses attrs, process/tool parsing, mutable state, and runtime side effects remain app-owned until later explicit slices.

## Out of Scope

- Moving `split_table_row(...)`, `render_table(...)`, `markdown_blocks(...)`, `plain_blocks(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, or `render_assistant_text(...)`.
- Moving `RenderLine` allocation, curses attrs, curses drawing, message cache mutation, or redraw behavior.
- Moving process/tool/IRC parsing, subagent result metadata parsing, runtime dispatch, Web Console, dashboard, storage roots, ledgers, approvals, artifacts, external memory, or history ownership.
- Changing user-visible markdown rendering behavior.

## Technical Notes

- Current duplicate implementations:
  - `src/ga_tui/rendering.py` has private `_strip_inline_markdown(...)` used by visible-reply policy helpers.
  - `src/ga_tui/app.py` has public `strip_inline_markdown(...)` used by table/markdown block and metadata parsing helpers.
- Existing rendering alias block in `src/ga_tui/app.py` already re-exports other pure rendering helpers such as `boxed_user_lines`.
- Relevant verification surfaces: `tests/test_rendering.py`, `scripts/check_policy_gates.py`, `.trellis/spec/backend/agent-control-protocol.md`, and `docs/agent-harness-architecture.md`.
