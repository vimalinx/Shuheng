# Extract Rendering Visible Reply Policy Helpers

## Objective

Move the remaining pure visible-reply policy helpers out of `src/shuheng/app.py` and into `src/shuheng/rendering.py` while preserving all existing behavior and app-level compatibility names.

## Scope

This slice owns only deterministic, curses-free text policy helpers:

- `visible_reply_is_substantive(text)`
- `visible_reply_is_housekeeping_summary(text)`
- `visible_reply_has_section_shape(text)`

The implementation should keep `src/shuheng/app.py` as a compatibility facade by importing or aliasing the same public names from `src/shuheng/rendering.py`.

## Non-Goals

- Do not move `preferred_group_visible_reply(...)`.
- Do not move `irc_reply_snippets_from_process_body(...)`.
- Do not move `process_tools(...)`, `process_has_tool_noise(...)`, JSON-ish payload parsing, interaction parsing, or ask-user handling.
- Do not move `render_assistant_text(...)`, process grouping/folding, message block rendering, markdown/plain block rendering, or message cache ownership.
- Do not introduce `shuheng.app`, curses, mutable `State`, runtime dispatch, Web Console, dashboard, command/input handlers, storage roots, approvals, artifacts, history ownership, or task-ledger dependencies into `rendering.py`.

## Compatibility

- Existing imports from `shuheng.app` must continue to work.
- Existing callers inside `app.py` should preserve behavior.
- The lower-level helper must depend only on leaf text utilities and local regex logic.

## Tests And Gates

- Add rendering unit coverage for each policy helper and app alias parity.
- Extend policy gates so `rendering.py` owns the helper implementations and `app.py` does not reimplement them.
- Preserve the rendering module no-reverse-dependency boundary.

## Architecture Baseline

This change should move the system closer to `docs/agent-harness-architecture.md` by keeping deterministic rendering text policy in a restricted lower-level helper module while leaving the strong Orchestrator facade responsible for mutable UI state, tool/process parsing, runtime side effects, ledgers, approvals, artifacts, history, and external memory.
