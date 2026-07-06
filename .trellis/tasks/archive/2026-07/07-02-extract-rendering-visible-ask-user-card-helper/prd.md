# Extract Rendering Visible Ask-User Card Helper

## Goal

Continue reducing `src/shuheng/app.py` by moving the deterministic visible
ask-user/default-card text selection into `src/shuheng/rendering.py`, while
preserving `app.py` as the owner of interaction extraction and process/runtime
control flow.

## Requirements

- Add a pure `rendering.visible_ask_user_card_text(...)` helper that accepts an
  already-extracted interaction payload or `None`.
- When a payload is present, the helper must render the same card text as
  `rendering.render_interaction_card(payload)`.
- When no payload is present, the helper must render the same default
  interactive waiting card currently produced by `app.visible_ask_user_text(...)`.
- Preserve `app.visible_ask_user_text(body)` as a compatibility wrapper that
  calls `extract_interaction_request(body)` and delegates only the extracted or
  missing payload to the rendering helper.
- Keep `extract_interaction_request(...)`, `has_ask_user_tool(...)`,
  `process_tools(...)`, JSON-ish parsing, tool payload regexes, process folding,
  `State.pending_interaction`, approval gates, input handling, curses attrs, and
  `RenderLine` allocation outside `rendering.py`.
- Update direct rendering tests, app wrapper parity tests, policy gates, and the
  backend spec boundary.

## Acceptance Criteria

- [ ] `src/shuheng/rendering.py` owns `visible_ask_user_card_text(...)`.
- [ ] `src/shuheng/app.py` exposes `visible_ask_user_card_text` as a
      compatibility alias and keeps `visible_ask_user_text(...)` as an
      app-owned parser wrapper.
- [ ] Existing visible ask-user card text is preserved for extracted payloads
      and fallback/no-payload bodies.
- [ ] `tests/test_rendering.py` covers direct helper behavior and app wrapper
      parity.
- [ ] `scripts/check_policy_gates.py` verifies helper ownership,
      representative behavior, app compatibility, duplicate-definition absence
      in `app.py`, and the rendering no-reverse-dependency boundary.
- [ ] `.trellis/spec/backend/agent-control-protocol.md` documents this
      rendering/app ownership split.
- [ ] Targeted and full verification pass, including policy gates, pytest,
      release hygiene, runtime smoke, package build, wheel smoke, and
      `shuheng-check`.

## Definition of Done

- Code is implemented in one behavior-preserving slice.
- The full release verification chain used by recent decomposition slices
  passes.
- The work commit excludes unrelated untracked Trellis directories, goal
  records, and `uv.lock`.
- `goal-7/tasks.md` records the completed slice and architecture-baseline
  comparison.

## Technical Approach

Add a rendering helper that takes `payload: dict[str, Any] | None` and returns
`render_interaction_card(payload)` or the existing default interactive card. The
app wrapper continues to parse raw assistant/process text with
`extract_interaction_request(...)` before delegating.

This keeps `rendering.py` deterministic and free of parser/runtime state while
removing one more interaction display decision from `app.py`.

## Decision (ADR-lite)

Context: The next candidate after footer extraction should remain lower risk
than moving `interaction_hint_lines(...)`, which owns curses attrs and selected
candidate layout.

Decision: Extract only the visible ask-user card text fallback helper into
`rendering.py`; keep extraction/parsing in `app.py`.

Consequences: The slice is small but preserves the first-principles ownership
line: rendering owns pure text, the Orchestrator facade owns parsing, state,
approval, input, process folding, and side effects.

## Out of Scope

- Moving `extract_interaction_request(...)`, `request_payload_from_args(...)`,
  `looks_like_interaction_payload(...)`, loose JSON parsing, or tool-name
  parsing.
- Moving `has_ask_user_tool(...)`, `render_assistant_text(...)`,
  `append_process_turn(...)`, process grouping, or process-noise detection.
- Moving `interaction_hint_lines(...)`, `RenderLine`/curses attr logic,
  selection mutation, input submission, approval decisions, or pending
  interaction state.
- Changing visible card wording or interaction behavior.

## Technical Notes

- Current source wrapper: `app.visible_ask_user_text(body)`.
- Existing rendering-owned interaction helpers:
  - `sanitize_interaction_candidates(...)`
  - `render_interaction_card(...)`
  - `interaction_answer_from_text(...)`
  - `compose_request_user_input_answer(...)`
  - `interaction_input_prompt_text(...)`
  - `interaction_footer_text(...)`
- Architecture baseline remains `docs/agent-harness-architecture.md`: this
  slice moves static display text into the lower-level rendering boundary while
  the strong Orchestrator facade keeps human approval gates, pending interaction
  state, ledgers, selection mutation, input handling, and runtime side effects.
