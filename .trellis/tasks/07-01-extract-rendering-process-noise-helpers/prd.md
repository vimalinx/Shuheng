# Extract Rendering Process Noise Helpers

## Summary

Continue Goal 7 by extracting the pure process-noise and search-noise predicates from `src/shuheng/app.py` into the curses-free `src/shuheng/rendering.py` helper boundary.

## Requirements

- Move deterministic process-noise predicate behavior into `rendering.py`:
  - `process_has_tool_call_noise_text(body, tools)`
  - `process_has_tool_result_noise_text(body)`
  - `process_has_tool_noise_text(body, tools)`
  - `process_has_search_noise_text(body, tools)`
- Keep `app.py` compatibility wrappers with the existing public names and signatures:
  - `process_has_tool_call_noise(body)`
  - `process_has_tool_result_noise(body)`
  - `process_has_tool_noise(body)`
  - `process_has_search_noise(body)`
- `app.py` wrappers must inject `process_tools(body)` into rendering helpers so `rendering.py` does not parse JSON-ish tool payloads or import `shuheng.app`.
- Preserve existing behavior for tool-call detection, result fence/final-response detection, combined tool-noise detection, and search/browser marker detection.
- Update `tests/test_rendering.py` with direct helper tests and app wrapper parity.
- Update `scripts/check_policy_gates.py` so the rendering boundary includes these helpers and continues forbidding reverse dependencies.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document that process noise/search noise is now a rendering-helper boundary with app-injected tool names.
- Compare against `docs/agent-harness-architecture.md` before claiming the slice is complete.

## Non-Goals

- Do not move `process_tools(...)`, JSON-ish object parsing, interaction extraction, ask-user handling, IRC snippet parsing, `preferred_group_visible_reply(...)`, `append_process_summary_line(...)`, `append_process_turn(...)`, `render_assistant_text(...)`, message block rendering, curses drawing, Web Console, dashboard, runtime dispatch, storage roots, approvals, artifacts, history ownership, or task ledgers.
- Do not change public console scripts, storage semantics, history ownership, subagent home responsibilities, or Secret Vault behavior.
- Do not stage or commit `goal-7/*`, `uv.lock`, or unrelated historical `.trellis/tasks/*` directories.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_rendering.py -q -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_rendering.py tests/test_cell_utils.py -q -p no:cacheprovider`
- Full release gate from Goal 7 when the targeted gates are green:
  - full Ruff over `src`, `tests`, and release scripts
  - release hygiene
  - runtime smoke
  - compileall
  - `git diff --check`
  - full pytest
  - wheel/sdist build
  - wheel smoke
  - `shuheng-check --root /home/vimalinx/Programs/GenericAgent`

## Rollback

If behavior changes or the boundary grows a reverse dependency, restore the `app.py` predicate bodies and remove the new `rendering.py` helpers/tests/spec entries for this slice only.
