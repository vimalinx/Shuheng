# Extract Rendering Turn Marker Split Helpers

## Problem

`src/ga_tui/app.py` still owns the top-level process-turn splitter used by process rendering and latest-visible-reply extraction. The splitter is deterministic text parsing over already-loaded assistant output, but it currently sits beside Orchestrator-owned rendering, interaction, queue, and runtime side-effect code. Keeping this parser in `app.py` makes later process rendering extraction harder because lower-level rendering helpers cannot own their own turn segmentation boundary.

## Goal

Move the smallest safe turn-marker splitting boundary into `src/ga_tui/rendering.py` while preserving existing behavior and public compatibility from `src/ga_tui/app.py`.

## Requirements

- Move `next_nonblank_line(lines, start)` into `src/ga_tui/rendering.py`.
- Move `line_numbered_file_line(line)` into `src/ga_tui/rendering.py`.
- Move `stray_line_numbered_fence_close(line, previous_nonblank, next_nonblank)` into `src/ga_tui/rendering.py`.
- Move `split_top_level_turn_markers(text)` into `src/ga_tui/rendering.py`.
- Keep `src/ga_tui/app.py` compatibility aliases with the same public names.
- Preserve the existing protection that line-numbered file output inside fences is not misinterpreted as a top-level process turn split.
- Reuse shared process marker semantics from `history_titles.TURN_MARKER_RE`.
- Add tests for normal top-level turn splitting, fenced content opacity, stray line-numbered fence-close behavior, empty text behavior, and app alias parity.
- Expand `scripts/check_policy_gates.py` so the rendering module boundary covers these helpers and still forbids reverse dependencies.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable rendering splitter boundary.

## Out of Scope

- Do not move `render_assistant_text(...)`.
- Do not move `latest_visible_reply_text(...)`.
- Do not move `process_tools(...)`, JSON-ish tool payload parsing, interaction parsing, or ask-user handling.
- Do not move `append_process_turn(...)`, process grouping/folding, `message_block_lines(...)`, `message_lines_from_cache(...)`, markdown/plain block rendering, or `RenderLine` allocation.
- Do not introduce curses imports, mutable `State`, `SubAgentRuntime`, Web Console, dashboard, command, input-handler, storage-root, ledger, approval, artifact, or runtime-dispatch behavior into `rendering.py`.
- Do not change subagent/session/history ownership invariants.

## Acceptance Criteria

- `src/ga_tui/rendering.py` owns the selected helper implementations.
- `src/ga_tui/app.py` keeps the public names as compatibility aliases.
- Existing call sites continue to work without behavior changes.
- `rendering.py` remains a lower-level curses-free helper boundary with no `ga_tui.app` import and no mutable TUI state dependency.
- Targeted rendering tests pass.
- Policy gates pass.
- Full release gate passes before the work is committed.

## Technical Notes

- Current callers include `render_assistant_text(...)`, `latest_visible_reply_text(...)`, and history/context-preview code that needs the existing split behavior.
- `LINE_NUMBERED_FILE_RE` and `FENCE_BOUNDARY_RE` can move with the helper because they are only used by the splitter boundary in `app.py`.
- `TURN_MARKER_RE` remains sourced from `history_titles.py` so title policy and rendering segmentation share the same process marker grammar.

## Verification Plan

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_rendering.py tests/test_cell_utils.py -q -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- `python3 -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_release_hygiene.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/runtime_smoke.py`
- `python3 -m compileall -q src scripts`
- `git diff --check`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`
- `rm -rf /tmp/shuheng-dist && python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist`
- `shuheng-check --root /home/vimalinx/Programs/GenericAgent`

## Rollback Plan

Revert the extraction commit or restore the helper implementations in `src/ga_tui/app.py` while keeping the tests as behavior references.
