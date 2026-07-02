# Extract Rendering Boxed User Lines Helper

## Goal

Continue Goal 7 by extracting the pure boxed user-message text layout helper from `src/ga_tui/app.py` into the curses-free `src/ga_tui/rendering.py` helper boundary.

## Requirements

- Move `boxed_user_lines(text, width)` into `src/ga_tui/rendering.py`.
- Preserve existing behavior:
  - compute `inner_limit = max(8, width - 4)`;
  - wrap the body with terminal cell-aware wrapping;
  - render an empty body as one empty line inside the box;
  - compute the inner box width from wrapped body cell widths, bounded by `inner_limit`;
  - return top border, padded body rows, and bottom border as plain strings.
- Keep `src/ga_tui/app.py` exposing `boxed_user_lines` as a compatibility alias.
- Keep `message_block_lines(...)`, `RenderLine(...)` allocation, markdown/plain rendering, color attrs, curses drawing, process folding, input handling, Web Console, dashboard, runtime dispatch, storage roots, ledgers, approvals, artifacts, and history ownership outside `rendering.py`.
- Update `tests/test_rendering.py` with direct helper behavior and app alias parity.
- Update `scripts/check_policy_gates.py` so the rendering boundary includes this helper and continues forbidding reverse dependencies.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document that boxed user-message text layout is rendering-owned while `RenderLine` allocation and message-block rendering remain app-owned.
- Compare against `docs/agent-harness-architecture.md` before claiming the slice is complete.

## Acceptance Criteria

- `rendering.boxed_user_lines(...)` owns the implementation.
- `app.boxed_user_lines is rendering.boxed_user_lines`.
- Existing call sites keep rendering user messages through the `app.py` compatibility alias.
- Unit tests cover simple text, empty text, width clamping, wrapped rows, CJK/wide text padding, and alias parity.
- Policy gates assert ownership, app alias parity, representative output shape, absence of a local `def boxed_user_lines` in `app.py`, and no reverse dependency from `rendering.py` into app/curses/state/runtime/command/Web/dashboard/input owners.

## Out of Scope

- Do not move `message_block_lines(...)`, `message_lines_from_cache(...)`, `markdown_blocks(...)`, `plain_blocks(...)`, `render_assistant_text(...)`, `RenderLine` allocation, color selection, curses drawing, process grouping/folding, command handlers, input handlers, Web Console, dashboard, runtime dispatch, storage roots, approvals, artifacts, history ownership, or task ledgers.
- Do not change public console scripts, storage semantics, history ownership, subagent home responsibilities, Secret Vault behavior, or release packaging.
- Do not stage or commit `goal-7/*`, `uv.lock`, or unrelated historical `.trellis/tasks/*` directories.

## Technical Notes

- This is a narrow rendering leaf extraction. `boxed_user_lines(...)` already depends only on `wrap_cells`, `cell_width`, and `pad_cells`, which are lower-level text helpers already imported by `rendering.py`.
- The app facade remains the owner of `message_block_lines(...)`, where boxed user lines become `RenderLine(line, cp(2))`.
- The architecture direction stays aligned with the governed harness baseline: pure text layout moves into a restricted lower-level helper, while app keeps Orchestrator responsibilities and mutable UI/rendering side effects.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_rendering.py -q -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_rendering.py tests/test_cell_utils.py -q -p no:cacheprovider`
- Full release gate from Goal 7 when targeted gates are green:
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

If behavior changes or the boundary grows a reverse dependency, restore `boxed_user_lines(...)` inside `app.py` and remove this slice's rendering helper/tests/spec entries only.
