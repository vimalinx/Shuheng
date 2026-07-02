# Extract Rendering Latest Visible Reply Helper

## Goal

Move the pure latest-visible-reply selection logic out of `src/ga_tui/app.py` and into `src/ga_tui/rendering.py`, while preserving existing behavior through an `app.py` compatibility wrapper.

## Scope

- Add `rendering.latest_visible_reply_text(text, has_tool_noise=None)`.
- Keep the existing public `app.latest_visible_reply_text(text)` name and behavior.
- Let `app.latest_visible_reply_text(...)` inject `process_has_tool_noise(...)` into the lower-level helper.
- Preserve turn-aware selection over `split_top_level_turn_markers(...)`.
- Preserve fallback behavior that hides detail fences only when the injected tool-noise predicate says the full text has tool noise.
- Add direct rendering tests and app-wrapper parity tests.
- Add policy-gate checks that lock helper ownership, wrapper parity, and behavior.
- Update `.trellis/spec/backend/agent-control-protocol.md` if this boundary needs durable documentation.

## Out Of Scope

- Do not move `render_assistant_text(...)`.
- Do not move `process_tools(...)`, `process_has_tool_noise(...)`, `process_has_tool_call_noise(...)`, or `process_has_tool_result_noise(...)`.
- Do not move JSON-ish tool payload parsing, interaction parsing, ask-user handling, process grouping/folding, message block rendering, markdown/plain block rendering, or curses drawing.
- Do not change mutable `State`, Web Console, dashboard, runtime dispatch, storage roots, ledgers, approvals, artifacts, or history ownership.
- Do not change visible reply semantics except where tests prove exact parity.

## Acceptance Criteria

- `src/ga_tui/rendering.py` owns the lower-level latest visible reply helper.
- `src/ga_tui/app.py` keeps a same-name compatibility wrapper.
- `rendering.py` remains free of `ga_tui.app`, curses, mutable `State`, runtime dispatch, Web Console/dashboard handlers, storage roots, and ledger writes.
- Unit tests prove:
  - latest turn body wins when it has visible content;
  - empty latest process turns fall back to earlier visible turns;
  - non-turn text uses the injected tool-noise predicate to decide whether to hide detail fences;
  - app wrapper behavior matches direct helper behavior with the app-owned predicate.
- Policy gates pass and cover the new boundary.
- Full Goal 7 release verification passes before commit.
