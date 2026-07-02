# Extract Rendering Running Indicator Helpers

## Goal

Create the first low-risk `src/ga_tui/rendering.py` boundary by moving pure running-indicator helper behavior out of `src/ga_tui/app.py` while preserving existing TUI animation behavior and app-level compatibility imports.

## Requirements

- Move `RUN_FRAMES`, `running_indicator(frame)`, `running_indicator_cell_width()`, and `render_running_indicator_line(line, frame)` into `src/ga_tui/rendering.py`.
- Keep `src/ga_tui/app.py` as a compatibility facade that exposes the same public names.
- Keep `record_running_indicator_rect(...)`, `draw_running_indicator_frame(...)`, `message_block_lines(...)`, `draw_main(...)`, event-loop frame advancement, and all mutable `State` behavior in `app.py`.
- The new rendering helper module may depend on lower-level `text_utils.cell_width` and `ui_types.RenderLine`.
- Add unit tests for helper output, frame modulo behavior, width calculation, non-indicator line passthrough, indicator line prefixing, and app alias parity.
- Add a policy gate that locks the `rendering.py` boundary and prevents reverse dependency into `app.py`, curses drawing, mutable `State`, runtime dispatch, command handlers, Web Console, dashboard, and input handlers.
- Update backend spec text to document the rendering helper ownership and exclusions.

## Acceptance Criteria

- [ ] `src/ga_tui/rendering.py` exists and owns the selected helper implementations.
- [ ] `src/ga_tui/app.py` re-exports the selected names as compatibility aliases without behavior changes.
- [ ] Existing running-indicator lightweight redraw behavior remains app-owned and still passes policy gates.
- [ ] New tests cover direct helper behavior and app alias parity.
- [ ] Targeted compile, targeted Ruff, targeted tests, policy gates, full tests, release hygiene, runtime smoke, build, wheel smoke, `git diff --check`, and `shuheng-check` pass.

## Definition of Done

- The extraction is committed as one coherent work commit.
- `goal-7/tasks.md` records the plan, implementation, verification, architecture-baseline comparison, and commit hash.
- The active Trellis task is finished with `python3 ./.trellis/scripts/task.py finish`.

## Technical Approach

Add `src/ga_tui/rendering.py` as a curses-free helper module. Move only pure string/line helper logic first. Import that module from `app.py` and assign compatibility aliases near the existing lower-level helper imports. Leave actual screen drawing, rectangle tracking, dirty-state decisions, cache behavior, and main loop animation in `app.py`.

## Decision (ADR-lite)

Context: Phase 7 of `docs/app-py-decomposition-plan.md` says rendering should be split late and first through curses-agnostic transforms.

Decision: Start `rendering.py` with running-indicator helper functions only, because they are small, deterministic, and already separated from the stateful lightweight row refresh path.

Consequences: This creates a policy-gated rendering boundary without moving high-risk `State`, curses drawing, process folding, selection, or cache code. Future rendering slices can move selection geometry, message block transforms, and draw helpers once their boundaries are similarly explicit.

## Out of Scope

- Moving `State`, `RenderLine` dataclass definitions, curses drawing functions, or `draw_main(...)`.
- Moving `message_block_lines(...)`, process folding, markdown/table rendering, sidebar/rightbar rendering, or selection mutation.
- Changing frame timing, cache keys, dirty-state behavior, terminal resize behavior, or runtime/provider streaming.
- Changing history, Secret Vault, dashboard, Web Console, commands, input handlers, storage roots, or task ledgers.

## Technical Notes

- Relevant code: `src/ga_tui/app.py` around `RUN_FRAMES`, `running_indicator(...)`, `message_block_lines(...)`, `record_running_indicator_rect(...)`, and `draw_running_indicator_frame(...)`.
- Relevant spec: `.trellis/spec/backend/agent-control-protocol.md` running-indicator animation contract and app decomposition boundaries.
- Relevant tests/gates: `scripts/check_policy_gates.py`, a new `tests/test_rendering.py`, existing full pytest and release gates.
