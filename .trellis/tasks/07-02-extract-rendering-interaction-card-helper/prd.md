# Extract rendering interaction card helper

## Goal

Continue decomposing `src/ga_tui/app.py` by moving the deterministic ask-user/request-user-input card text renderer into the curses-free `src/ga_tui/rendering.py` helper layer, while preserving interactive tool visibility and keeping `app.py` responsible for payload extraction, pending interaction state, approvals, input handling, and curses hint rows.

## Requirements

- Add a pure rendering helper that formats an interaction request payload into the existing plain text card shown inside assistant/process output.
- Keep `src/ga_tui/app.py` as the compatibility facade and owner of `extract_interaction_request(...)`, `request_payload_from_args(...)`, JSON-ish parsing, tool-name extraction, `State.pending_interaction`, approval interaction payloads, candidate selection, answer submission, `interaction_hint_lines(...)`, curses attrs, and input/key handling.
- Preserve existing `render_interaction_card(payload)` output for plain candidate prompts, approval candidate prompts, multi-question `request_user_input` prompts, and the default interactive fallback.
- Re-export the new helper through `src/ga_tui/app.py` for compatibility.
- Add direct unit coverage and app alias/wrapper parity coverage.
- Extend policy gates so the helper is owned by `rendering.py`, not duplicated in `app.py`, and the rendering module boundary remains free of app/curses/state/runtime/command/Web/dashboard/input imports.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the durable helper boundary.

## Acceptance Criteria

- [ ] `src/ga_tui/rendering.py` owns a deterministic interaction card formatting helper.
- [ ] `src/ga_tui/app.py` keeps interaction request extraction and stateful interaction handling, and only delegates card text formatting.
- [ ] Existing visible card strings are unchanged for normal candidates, approval candidates, multi-question request-user-input payloads, and empty fallback.
- [ ] `tests/test_rendering.py` covers direct helper behavior and app wrapper/alias parity.
- [ ] `scripts/check_policy_gates.py` covers helper ownership, representative behavior, app wrapper parity, duplicate-definition absence in `app.py`, and rendering boundary rules.
- [ ] Targeted compile, Ruff, rendering tests, policy gates, full tests, release hygiene, runtime smoke, package build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.
- [ ] The change is compared against `docs/agent-harness-architecture.md` before completion.

## Definition of Done

- Tests and policy gates lock the extracted boundary.
- `.trellis/spec/backend/agent-control-protocol.md` documents the new contract.
- Release verification and packaging smoke are green.
- Work is committed as one coherent extraction commit without unrelated dirty files.

## Technical Approach

Move the existing `render_interaction_card(payload)` string construction into `rendering.py` as the rendering-owned implementation. The helper should accept an explicit payload dictionary, normalize only the values needed for display, call or reuse a rendering-owned candidate-sanitizing helper if needed, and return the same multi-line card text. `app.py` will expose `render_interaction_card = rendering_helpers.render_interaction_card` for compatibility. App-owned `visible_ask_user_text(...)` will continue to parse process bodies with `extract_interaction_request(...)`, then pass the explicit payload into the helper.

## Decision (ADR-lite)

Context: ask-user and request-user-input cards are currently formatted inside `app.py`, but the string renderer is deterministic over an explicit payload and does not need mutable UI state.

Decision: Extract only the plain card text renderer into `rendering.py`. Do not move request extraction, JSON-ish payload parsing, tool detection, pending interaction state, approvals, candidate selection, answer composition, hint rows, key handling, or curses attrs.

Consequences: The split reduces `app.py` rendering coupling without changing interactive tool behavior. Later slices can consider lower-level interaction payload normalization only after the parsing/state boundaries are independently locked.

## Out of Scope

- Moving `extract_interaction_request(...)`, `request_payload_from_args(...)`, `loose_interaction_args(...)`, `jsonish_objects(...)`, `process_tools(...)`, approval interaction payloads, `normalize_interaction_payload(...)`, `interaction_footer(...)`, `interaction_hint_lines(...)`, `interaction_current_candidates(...)`, `interaction_selection(...)`, answer submission, `State.pending_interaction`, subagent pending interaction handling, command/input handlers, `RenderLine` allocation, `cp(...)`, curses attrs, Web Console, dashboard, runtime dispatch, storage roots, ledgers, artifacts, Secret Vault behavior, or history ownership.
- Changing visible interaction card copy or user-input behavior.
- Introducing reverse imports from `rendering.py` to `ga_tui.app`.

## Technical Notes

- Current function: `src/ga_tui/app.py::render_interaction_card(...)`.
- Current call site: `src/ga_tui/app.py::visible_ask_user_text(...)`.
- Existing policy coverage: `scripts/check_policy_gates.py::assert_ask_user_tool_use_input_payload_visible(...)`, `assert_ask_user_multiline_tool_args_payload_visible(...)`, and approval interaction checks.
- Policy gate owner: `scripts/check_policy_gates.py::assert_rendering_module_boundary()`.
- Spec owner: `.trellis/spec/backend/agent-control-protocol.md`.
- Architecture baseline: `docs/agent-harness-architecture.md`, especially strong Orchestrator responsibility, human approval gates, auditable communication, and bounded worker protocols.
