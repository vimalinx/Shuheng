# Extract Rendering Process Summary Helpers

## Problem

`src/ga_tui/app.py` still owns process-block preview and summary text helpers even though they are deterministic, curses-free rendering transforms. Keeping these helpers in `app.py` makes later extraction of process folding and message rendering harder because low-level text summarization stays mixed with Orchestrator-owned state, curses drawing, command routing, and runtime side effects.

## Goal

Move the smallest safe process-summary helper boundary into `src/ga_tui/rendering.py` while preserving existing behavior and public compatibility from `src/ga_tui/app.py`.

## In Scope

- Move `strip_meta_blocks(text)` into `src/ga_tui/rendering.py`.
- Move `process_preview(text)` into `src/ga_tui/rendering.py`.
- Move `process_summary_text(text)` into `src/ga_tui/rendering.py`.
- Keep `src/ga_tui/app.py` compatibility aliases with the same public names.
- Reuse existing regex semantics from `history_titles.py` where practical.
- Add unit tests covering summary preference, fallback preview cleanup, thinking fallback for process-only summaries, empty fallback, and app alias parity.
- Expand `scripts/check_policy_gates.py` so the rendering module boundary covers these helpers and still forbids reverse dependencies.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the module boundary has new durable guidance.

## Out of Scope

- Do not move `process_tools(...)`; it depends on JSON-ish parsing and interaction/tool payload recognition.
- Do not move `process_title_text(...)`; it still calls `process_has_search_noise(...)` in `app.py`.
- Do not move `collapsed_process_line(...)`, `process_detail_line(...)`, `process_speech_header(...)`, `process_speech_summary_line(...)`, `process_group_header(...)`, or any process grouping/folding logic.
- Do not move `message_block_lines(...)`, `message_lines_from_cache(...)`, `markdown_blocks(...)`, or `plain_blocks(...)`.
- Do not introduce curses imports, mutable `State`, `RenderLine` allocation changes, runtime dispatch, Web Console, dashboard, command, input-handler, storage-root, ledger, or history-ownership behavior into `rendering.py`.
- Do not change subagent/session/history ownership invariants.

## Acceptance Criteria

- `src/ga_tui/rendering.py` owns the three selected helper implementations.
- `src/ga_tui/app.py` keeps the three public names as compatibility aliases.
- Existing call sites continue to work without behavior changes.
- `rendering.py` remains a lower-level curses-free helper boundary with no `ga_tui.app` import and no mutable TUI state dependency.
- Targeted rendering tests pass.
- Policy gates pass.
- Full release gate passes before the work is committed.

## Verification Plan

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_rendering.py tests/test_cell_utils.py -q -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_release_hygiene.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/runtime_smoke.py`
- `python3 -m compileall -q src scripts`
- `git diff --check`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`
- `rm -rf /tmp/shuheng-dist && python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist`
- `shuheng-check --root /home/vimalinx/Programs/GenericAgent`

## Rollback Plan

Revert the extraction commit or restore the helper implementations in `src/ga_tui/app.py` while keeping the existing tests as behavior references.
