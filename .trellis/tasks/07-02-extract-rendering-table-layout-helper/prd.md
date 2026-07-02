# Extract Rendering Table Layout Helper

## Requirement

Continue Goal 7 by extracting the deterministic markdown table layout calculation from `src/ga_tui/app.py` into the lower-level curses-free rendering boundary in `src/ga_tui/rendering.py`.

## Scope

- Add a pure `rendering.table_layout_lines(lines, width)` helper that consumes markdown table source lines and returns neutral table layout records without curses attributes.
- Keep markdown table parsing helpers `split_table_row(...)` and `is_table_separator(...)` in `src/ga_tui/rendering.py`.
- Keep `src/ga_tui/app.py::render_table(...)` as the public compatibility wrapper that converts neutral layout records into `RenderLine` objects with existing `cp(...)` and curses attrs.
- Preserve current rendered table text, separator placement, column-width capping, padding behavior, inline markdown cleanup, and empty-table behavior.
- Expand rendering tests and policy gates so both direct module behavior and `app.py` compatibility behavior are covered.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the helper boundary becomes a durable contract.

## Non-Goals

- Do not move `markdown_blocks(...)`, `plain_blocks(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, `render_assistant_text(...)`, or subagent result card rendering in this slice.
- Do not move `RenderLine` allocation, `cp(...)`, curses attrs, curses drawing, mutable `State`, message cache ownership, command handlers, input handlers, Web Console, dashboard, runtime dispatch, storage roots, ledgers, approvals, artifacts, Secret Vault behavior, or history ownership into `rendering.py`.
- Do not change public rendering behavior or storage/runtime behavior.

## Architecture Notes

This slice moves another deterministic rendering transform toward the lower-level rendering module while preserving `app.py` as the strong Orchestrator and compatibility facade. The extracted helper must not import `ga_tui.app`, curses, mutable TUI `State`, Web Console, dashboard, command/input handlers, runtime providers, storage roots, ledgers, approvals, artifacts, Secret Vault, or history storage.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 gate before commit: full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel/sdist smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.
