# Extract Rendering Table Parser Helpers

## Requirement

Continue Goal 7 by extracting the next small curses-free rendering helper boundary from `src/ga_tui/app.py` into `src/ga_tui/rendering.py`.

This slice moves only the pure markdown table parsing helpers:

- `is_table_separator(cells)`
- `split_table_row(line)`

`src/ga_tui/app.py` must keep compatibility aliases so existing imports, tests, and call sites continue to work.

## Scope

- Add the helper implementations to `src/ga_tui/rendering.py`.
- Re-export the helpers from `src/ga_tui/app.py` as direct compatibility aliases.
- Keep `render_table(...)`, `markdown_blocks(...)`, `plain_blocks(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, and `render_assistant_text(...)` in `app.py`.
- Add focused tests to `tests/test_rendering.py` for separator detection, row splitting, inline markdown cleanup, whitespace/edge trimming, and app alias parity.
- Update `scripts/check_policy_gates.py` to assert helper ownership, alias parity, representative behavior, absence of app-local definitions, and the rendering module no-reverse-dependency boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the durable rendering boundary wording needs to include table parser helpers.

## Non-Goals

- Do not move `render_table(...)` yet because it allocates `RenderLine` with curses attrs.
- Do not move markdown block parsing or message block rendering.
- Do not change table rendering behavior.
- Do not change `RenderLine`, curses color, message-cache, process folding, Web Console, dashboard, runtime dispatch, storage roots, ledgers, approvals, artifacts, history ownership, or external-memory behavior.
- Do not stage or commit historical untracked Trellis task directories, `goal-7/*`, or `uv.lock`.

## Acceptance Criteria

- `src/ga_tui/rendering.py` owns `is_table_separator(...)` and `split_table_row(...)`.
- `src/ga_tui/app.py` exposes `is_table_separator` and `split_table_row` as compatibility aliases.
- App-owned `render_table(...)` still calls the same public names and preserves current behavior.
- Targeted rendering tests and policy gates pass.
- Full release gate pattern passes before commit.
- The change is committed as one coherent work commit.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py tests/test_cell_utils.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- `python3 -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_release_hygiene.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/runtime_smoke.py`
- `python3 -m compileall -q src scripts`
- `git diff --check`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`
- `python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist`
- `shuheng-check --root /home/vimalinx/Programs/GenericAgent`

## Architecture Baseline Check

Before claiming completion, compare this slice against `docs/agent-harness-architecture.md`.

Expected direction: closer to the governed harness baseline because deterministic markdown table parsing becomes a lower-level policy-gated rendering helper, while the strong Orchestrator facade still owns `RenderLine` allocation, curses attrs, mutable UI state, cache storage, redraw decisions, command/input dispatch, runtime side effects, ledgers, approvals, artifacts, history, and external-memory boundaries.
