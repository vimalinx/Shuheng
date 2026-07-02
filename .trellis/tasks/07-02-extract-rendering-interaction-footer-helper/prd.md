# Extract Rendering Interaction Footer Helper

## Goal

Continue reducing `src/ga_tui/app.py` by moving deterministic interaction footer
text selection into `src/ga_tui/rendering.py`, while preserving the app facade as
the owner of pending interaction state, approval gates, selection mutation,
curses hint rows, and input submission.

## Requirements

- Add a pure `rendering.interaction_footer_text(...)` helper that chooses the
  existing footer strings from explicit boolean facts.
- Preserve `app.interaction_footer(payload)` as a compatibility wrapper that
  injects current-candidate, approval, and question-state facts.
- Keep `interaction_current_candidates(...)`, `interaction_questions(...)`,
  `is_approval_interaction(...)`, `interaction_selection(...)`,
  `interaction_hint_lines(...)`, `State.pending_interaction`, approval decisions,
  `mark_dirty(...)`, curses attrs, and key/input handling in `app.py`.
- Preserve the exact footer text for approval candidate prompts, normal
  candidate prompts, multi-question `request_user_input` prompts, default
  interactive prompts, and no-payload fallback.
- Add direct rendering tests, app wrapper parity tests, and policy-gate checks.
- Update `.trellis/spec/backend/agent-control-protocol.md` so future
  decomposition keeps footer text in the rendering helper while leaving stateful
  interaction behavior in `app.py`.

## Acceptance Criteria

- [ ] `src/ga_tui/rendering.py` owns `interaction_footer_text(...)`.
- [ ] `src/ga_tui/app.py` exposes `interaction_footer_text` as a compatibility
      alias and keeps `interaction_footer(...)` as an app-owned wrapper.
- [ ] `tests/test_rendering.py` covers direct helper behavior and wrapper
      parity for all footer branches.
- [ ] `scripts/check_policy_gates.py` verifies helper ownership,
      representative behavior, app compatibility, duplicate-definition absence
      in `app.py`, and the rendering no-reverse-dependency boundary.
- [ ] Relevant backend spec text documents the interaction footer helper
      boundary.
- [ ] Targeted and full verification pass, including policy gates, pytest,
      release hygiene, runtime smoke, package build, wheel smoke, and
      `shuheng-check`.

## Definition of Done

- Code is implemented in one behavior-preserving slice.
- The full release verification chain used by recent decomposition slices passes.
- The work commit excludes unrelated untracked Trellis directories, goal records,
  and `uv.lock`.
- `goal-7/tasks.md` records the completed slice and architecture-baseline
  comparison.

## Out of Scope

- Moving `interaction_hint_lines(...)` or any `RenderLine`/curses attr logic.
- Moving `interaction_current_candidates(...)`, `interaction_questions(...)`,
  `interaction_selection(...)`, `move_interaction_selection(...)`, answer
  submission, approval decisions, or pending-interaction mutation.
- Changing footer wording or interaction behavior.
- Storage-root, history, Secret Vault, dashboard, Web Console, runtime dispatch,
  command, or key-handler changes.

## Technical Approach

Add a rendering helper that accepts `has_payload`, `has_candidates`,
`is_approval`, and `has_questions`. The app wrapper computes those booleans from
the current payload using app-owned traversal/approval logic, then delegates to
the rendering helper. This keeps `rendering.py` deterministic and app-free while
removing one more interaction text decision from `app.py`.

## Technical Notes

- Current source helper: `app.interaction_footer(payload)`.
- Existing rendering-owned interaction helpers:
  - `sanitize_interaction_candidates(...)`
  - `render_interaction_card(...)`
  - `interaction_answer_from_text(...)`
  - `compose_request_user_input_answer(...)`
  - `interaction_input_prompt_text(...)`
- Architecture baseline remains
  `docs/agent-harness-architecture.md`: this slice moves static display text
  into the lower-level rendering boundary while the Orchestrator facade keeps
  human approval gates, pending interaction state, ledgers, selection mutation,
  input handling, and runtime side effects.
