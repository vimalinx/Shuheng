# Extract Rendering Markdown Block Layout Helper

## Objective

Move deterministic markdown block layout from `src/ga_tui/app.py` into the lower-level, curses-free `src/ga_tui/rendering.py` module while preserving existing `app.markdown_blocks(text, width)` behavior through a compatibility wrapper.

## Scope

- Add a neutral markdown layout helper in `src/ga_tui/rendering.py`.
- The helper must parse and layout the same block forms currently handled by `app.markdown_blocks(...)`:
  - fenced code block headers, body lines, and footers
  - markdown tables via the existing `table_layout_lines(...)`
  - blank lines
  - horizontal rules
  - headings
  - block quotes
  - task list items
  - unordered bullets
  - numbered list items
  - normal body lines
- Return neutral layout records, not `RenderLine`.
- Keep `src/ga_tui/app.py` responsible for converting layout records into `RenderLine` instances with the existing `cp(...)` and curses attrs.
- Preserve the public `app.markdown_blocks(text, width)` name and output behavior.
- Add targeted tests for direct rendering helper behavior and app wrapper attr mapping.
- Update policy gates and backend spec to document and enforce the new module boundary.

## Non-Goals

- Do not move `plain_blocks(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, `render_assistant_text(...)`, process folding, subagent result card rendering, or mutable message cache behavior.
- Do not move `RenderLine` allocation or curses color/attr selection into `rendering.py`.
- Do not import `ga_tui.app`, `curses`, mutable `State`, Web Console, dashboard, runtime dispatch, command handlers, input handlers, storage roots, ledgers, approvals, artifacts, Secret Vault behavior, or history ownership into `rendering.py`.
- Do not change markdown rendering semantics beyond the mechanical extraction.

## Acceptance Criteria

- `src/ga_tui/rendering.py` owns `markdown_layout_blocks(text, width)`.
- `markdown_layout_blocks(...)` returns neutral records with stable kind strings that let `app.py` reproduce existing attrs.
- `src/ga_tui/app.py` exposes `markdown_layout_blocks` as a compatibility alias and keeps `markdown_blocks(...)` as a wrapper.
- Existing `markdown_blocks(...)` output text and attrs remain compatible for representative code fences, tables, headings, quotes, task lists, bullets, numbered lists, horizontal rules, blank lines, and body wrapping.
- `tests/test_rendering.py` covers direct helper behavior and app wrapper parity.
- `scripts/check_policy_gates.py` enforces helper ownership, representative behavior, app wrapper parity, absence of a local pure implementation in `app.py`, and the rendering no-reverse-dependency boundary.
- `.trellis/spec/backend/agent-control-protocol.md` documents the markdown layout helper boundary.

## Verification Plan

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release gate after targeted checks pass:
  - full Ruff
  - release hygiene
  - runtime smoke
  - compileall
  - `git diff --check`
  - full pytest
  - package build
  - wheel/sdist smoke
  - `shuheng-check --root /home/vimalinx/Programs/GenericAgent`

## Architecture Baseline Impact

This moves the implementation closer to `docs/agent-harness-architecture.md` by putting deterministic markdown block layout behind a restricted lower-level helper boundary while keeping the app facade as the single Orchestrator/composition owner for mutable UI state, curses drawing, command/input dispatch, runtime side effects, ledgers, approvals, artifacts, history, Secret Vault, Web Console, dashboard, and external-memory behavior.
