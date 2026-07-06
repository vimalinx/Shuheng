# Extract Rendering Preferred Group Reply Helper

## Summary

Continue Goal 7 by extracting the pure preferred group visible-reply selection logic from `src/shuheng/app.py` into the curses-free `src/shuheng/rendering.py` helper boundary.

## Requirements

- Add `rendering.preferred_group_visible_reply_text(visible_items, irc_replies)` as a deterministic helper over already-cleaned visible replies and already-extracted IRC reply lines.
- Preserve existing selection behavior:
  - choose the latest visible item by default;
  - when the latest item is short or housekeeping-only, prefer a richer earlier substantive answer according to the existing length and section-shape thresholds;
  - append IRC replies under the `### IRC 回复` block, preserving order, skipping duplicates, and skipping replies already present in the chosen text.
- Keep `app.preferred_group_visible_reply(process_turns)` with the same public signature. It must continue to own process-turn traversal, `visible_reply_text(...)` calls, `process_has_tool_noise(...)`, `irc_reply_snippets_from_process_body(...)`, `process_tools(...)`, JSON-ish parsing, and IRC result extraction.
- Expose the new rendering helper through `app.py` as a compatibility alias for tests/import parity.
- Update `tests/test_rendering.py` with direct helper tests and app wrapper parity.
- Update `scripts/check_policy_gates.py` so the rendering boundary includes this helper and continues forbidding reverse dependencies.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document that preferred group reply selection is rendering-owned while process/tool/IRC parsing remains app-owned.
- Compare against `docs/agent-harness-architecture.md` before claiming the slice is complete.

## Non-Goals

- Do not move `irc_reply_snippets_from_process_body(...)`, `process_tools(...)`, JSON-ish object parsing, interaction extraction, ask-user handling, process grouping/folding, `append_process_summary_line(...)`, `append_process_turn(...)`, `render_assistant_text(...)`, message block rendering, curses drawing, Web Console, dashboard, runtime dispatch, storage roots, approvals, artifacts, history ownership, or task ledgers.
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

If behavior changes or the boundary grows a reverse dependency, restore the selection logic inside `app.preferred_group_visible_reply(...)` and remove the new rendering helper/tests/spec entries for this slice only.
