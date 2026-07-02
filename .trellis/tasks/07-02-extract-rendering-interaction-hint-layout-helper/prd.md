# Extract Rendering Interaction Hint Layout Helper

## Objective

Continue Goal 7 by moving deterministic interaction hint text layout out of
`src/ga_tui/app.py` and into the lower-level, curses-free
`src/ga_tui/rendering.py` module, while preserving the legacy app wrapper and
runtime behavior.

## Scope

- Add a pure helper in `src/ga_tui/rendering.py` that returns neutral
  interaction hint layout records over explicit inputs:
  - payload-present flag
  - tool name
  - title source
  - optional current question text
  - optional approval preview lines
  - sanitized candidates
  - selected candidate index
  - footer text
  - terminal width
- Keep `app.interaction_hint_lines(payload, width)` as the compatibility wrapper
  that inspects payloads, computes current question/candidate/selection facts,
  calls approval detection, and converts neutral layout records into existing
  `(text, attr)` tuples with `cp(...)` and `curses.A_BOLD`.
- Preserve visible hint strings for:
  - no payload
  - normal candidate prompts
  - approval prompts with preview body lines
  - multi-question `request_user_input` prompts
  - long candidate lists and selected candidate windows
  - footer lines
- Add unit tests and policy gates for direct helper behavior, app wrapper parity,
  helper ownership, duplicate-definition absence, and the rendering module
  boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable
  boundary if implementation changes the contract.

## Out Of Scope

- Do not move `interaction_hint_lines(...)` itself.
- Do not move `current_interaction_payload(...)`, `normalize_interaction_payload(...)`,
  `interaction_questions(...)`, `interaction_current_index(...)`,
  `interaction_current_candidates(...)`, `interaction_selection(...)`,
  `move_interaction_selection(...)`, `accept_interaction_input(...)`,
  `accept_approval_interaction_input(...)`, `interaction_answer_from_input(...)`,
  or input/key handling.
- Do not move approval payload construction, `decide_approval(...)`, approval
  ledger reads/writes, `State.pending_interaction`, subagent pending interaction,
  Web Console, dashboard, runtime dispatch, history, Secret Vault, ledgers,
  artifacts, draw functions, or storage roots.
- Do not import `ga_tui.app`, curses, mutable TUI `State`, runtime dispatch,
  command handlers, Web Console, dashboard, input handlers, or draw functions
  from `rendering.py`.

## Compatibility Requirements

- Existing callers of `app.interaction_hint_lines(payload, width)` must receive
  identical text and attr tuples.
- The new rendering helper must return only neutral text-kind records, not
  `RenderLine` objects or curses attrs.
- `app.py` must remain the owner of bold/normal/selection/footer attr mapping.
- The helper must be deterministic over explicit values and must not mutate the
  input payload or candidate list.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 release-quality gate before commit.

## Architecture Baseline

This should move the system closer to `docs/agent-harness-architecture.md` by
keeping deterministic UI hint text shaping in a restricted lower-level rendering
module while the strong Orchestrator facade retains human approval gates,
pending interaction state, selection mutation, input handling, ledgers,
artifacts, history, Secret Vault, Web Console, dashboard, runtime side effects,
mutable UI state, and curses rendering.
