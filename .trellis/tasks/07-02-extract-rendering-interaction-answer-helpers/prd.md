# Extract Rendering Interaction Answer Helpers

## Goal

Continue reducing `src/ga_tui/app.py` by moving deterministic interaction answer
and prompt text helpers into `src/ga_tui/rendering.py`, while preserving the
current `app.py` compatibility surface and Orchestrator-owned interaction
state/approval behavior.

## Requirements

- Move only pure interaction answer/prompt text helpers that do not mutate
  runtime state, write ledgers, call approvals, or depend on curses.
- Preserve public compatibility names from `ga_tui.app` for existing tests and
  downstream imports.
- Keep interaction request extraction, payload normalization, current question
  traversal, selection mutation, `State.pending_interaction`, approval decisions,
  answer submission, `mark_dirty(...)`, and input/key handling in `app.py`.
- Preserve existing behavior for candidate number selection, free-text answers,
  empty-text fallback to selected candidates, multi-question answer formatting,
  approval prompt labels, question prompt labels, and default prompt labels.
- Add direct rendering tests, app parity tests, and policy-gate checks for the
  new boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable
  boundary so future agents do not move stateful approval/input behavior into
  `rendering.py`.

## Acceptance Criteria

- [ ] `src/ga_tui/rendering.py` owns deterministic helpers for interaction
      answer resolution, multi-question answer formatting, and prompt text.
- [ ] `src/ga_tui/app.py` exposes compatibility aliases or thin wrappers and
      keeps all state mutation and approval handling.
- [ ] `tests/test_rendering.py` covers the direct helpers and app parity.
- [ ] `scripts/check_policy_gates.py` verifies helper ownership, representative
      behavior, app compatibility, duplicate-definition absence in `app.py`, and
      the rendering no-reverse-dependency boundary.
- [ ] Relevant backend spec text documents the interaction answer helper
      boundary.
- [ ] Targeted and full verification pass, including policy gates, pytest,
      release hygiene, runtime smoke, package build, wheel smoke, and
      `shuheng-check`.

## Definition of Done

- Code is implemented in a small behavior-preserving slice.
- The release gates used by recent decomposition slices pass.
- The work is committed separately from unrelated untracked Trellis directories
  and `uv.lock`.
- `goal-7/tasks.md` records the completed slice and architecture-baseline
  comparison.

## Out of Scope

- Changing interaction UX strings beyond the exact behavior-preserving boundary.
- Moving `accept_interaction_input(...)`, `accept_approval_interaction_input(...)`,
  `accept_subagent_interaction_input(...)`, `move_interaction_selection(...)`, or
  `interaction_hint_lines(...)`.
- Moving JSON-ish tool parsing, `extract_interaction_request(...)`,
  `request_payload_from_args(...)`, approval ledger logic, runtime dispatch,
  message traversal, curses attrs, or command/key handlers.
- Storage-root, history, Secret Vault, dashboard, Web Console, or runtime
  behavior changes.

## Technical Approach

Add rendering helpers that operate on already-normalized payload/candidate data
and injected current-question/selection values where needed. Keep `app.py` as the
facade that reads/mutates `State.pending_interaction`, computes the current
question/candidates/selection from runtime payloads, and delegates pure string
or answer-shaping decisions to `rendering.py`.

## Technical Notes

- Current candidates:
  - `interaction_answer_from_input(...)`
  - `compose_request_user_input_answer(...)`
  - `interaction_input_prompt(...)`
- Existing nearby pure rendering helpers:
  - `rendering.sanitize_interaction_candidates(...)`
  - `rendering.render_interaction_card(...)`
- Architecture baseline remains
  `docs/agent-harness-architecture.md`: this slice should move deterministic
  rendering/input-text shaping closer to lower-level helpers while keeping the
  strong Orchestrator facade responsible for human approval gates, ledgers,
  state mutation, auditable communication, history, memory, and runtime effects.
