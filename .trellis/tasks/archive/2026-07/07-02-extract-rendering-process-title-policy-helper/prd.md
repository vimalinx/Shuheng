# Extract Rendering Process Title Policy Helper

## Goal

Continue reducing `src/shuheng/app.py` by moving the deterministic process-title
choice policy into `src/shuheng/rendering.py`, while preserving `app.py` as the
owner of process body parsing, tool-name extraction, search-noise detection,
process grouping, and runtime/curses behavior.

## Requirements

- Add a pure `rendering.process_title_text_from_parts(summary, has_search_noise,
  preview)` helper.
- Preserve the existing title priority:
  1. non-empty summary wins;
  2. search/browser noise with no summary returns `搜索/浏览输出已折叠`;
  3. otherwise use the provided preview.
- Preserve `app.process_title_text(body)` as the compatibility wrapper that
  injects `process_summary_text(body)`, `process_has_search_noise(body)`, and
  `process_preview(body)`.
- Keep `process_tools(...)`, JSON-ish parsing, search-noise body inspection,
  process turn traversal, message rendering, `RenderLine`, curses attrs, mutable
  `State`, runtime dispatch, Web Console, dashboard, history, and Secret Vault
  behavior outside `rendering.py`.
- Add direct rendering tests, app wrapper parity tests, policy-gate checks, and
  backend spec coverage.

## Acceptance Criteria

- [ ] `src/shuheng/rendering.py` owns `process_title_text_from_parts(...)`.
- [ ] `src/shuheng/app.py` exposes `process_title_text_from_parts` as a
      compatibility alias and keeps `process_title_text(...)` as an app-owned
      parser wrapper.
- [ ] Summary-first, search-noise fallback, and preview fallback behavior are
      unchanged.
- [ ] `tests/test_rendering.py` covers direct helper behavior and app wrapper
      parity.
- [ ] `scripts/check_policy_gates.py` verifies helper ownership,
      representative behavior, app compatibility, duplicate-definition absence
      in `app.py`, and the rendering no-reverse-dependency boundary.
- [ ] `.trellis/spec/backend/agent-control-protocol.md` documents the title
      policy helper boundary.
- [ ] Targeted and full verification pass, including policy gates, pytest,
      release hygiene, runtime smoke, package build, wheel smoke, and
      `shuheng-check`.

## Definition of Done

- Code is implemented in one behavior-preserving slice.
- The full release verification chain used by recent decomposition slices
  passes.
- The work commit excludes unrelated untracked Trellis directories, goal
  records, and `uv.lock`.
- `goal-7/tasks.md` records the completed slice and architecture-baseline
  comparison.

## Technical Approach

Add a rendering helper that chooses between explicit `summary`,
`has_search_noise`, and `preview` inputs. `app.process_title_text(...)` computes
those facts from the raw process body and delegates to the new helper.

This keeps `rendering.py` deterministic and parser-free while shaving another
process display decision out of `app.py`.

## Decision (ADR-lite)

Context: `process_title_text(...)` currently mixes a pure title-priority policy
with app-owned body parsing. Moving the full function would violate the current
spec because search-noise detection injects `process_tools(...)` and JSON-ish
tool parsing.

Decision: Extract only the title choice policy over explicit facts.

Consequences: The slice is small but keeps the lower-level rendering direction
consistent: pure text policy moves down, parser/runtime responsibilities stay in
the Orchestrator facade.

## Out of Scope

- Moving `process_title_text(...)` itself into `rendering.py`.
- Moving `process_tools(...)`, `process_has_search_noise(...)`, JSON-ish parsing,
  tool payload regexes, or process body traversal.
- Moving `append_process_turn(...)`, `process_group_header(...)`,
  `render_assistant_text(...)`, message cache handling, `RenderLine` allocation,
  curses attrs, mutable `State`, runtime dispatch, Web Console, dashboard,
  history, or Secret Vault behavior.
- Changing process title wording or process folding behavior.

## Technical Notes

- Current source wrapper: `app.process_title_text(body)`.
- Existing rendering-owned process helpers include `process_preview(...)`,
  `process_summary_text(...)`, process-line formatters, process-noise predicate
  helpers, `process_group_header_parts(...)`, and `process_turn_lines(...)`.
- Architecture baseline remains `docs/agent-harness-architecture.md`: this
  slice moves pure display policy into the lower-level rendering module while
  the strong Orchestrator facade keeps parsing, ledgers, approvals, artifacts,
  state, runtime side effects, and curses rendering.
