# Extract rendering process group header helper

## Goal

Continue decomposing `src/ga_tui/app.py` by moving deterministic process-group header title/tool aggregation into the curses-free `src/ga_tui/rendering.py` helper layer, while preserving existing process rendering behavior and keeping the Orchestrator facade responsible for process-body parsing.

## Requirements

- Add a pure rendering helper that derives a process group header title and bounded unique tool list from explicit summary strings and tool-name lists.
- Keep `src/ga_tui/app.py` as the compatibility facade and owner of `process_summary_text(...)`, `process_tools(...)`, JSON-ish tool parsing, process turn traversal, `RenderLine` allocation, `cp(...)`, curses attrs, message rendering, and mutable UI state.
- Preserve existing `process_group_header(label, turns, current, expanded)` output for grouped process turns.
- Re-export the new helper through `src/ga_tui/app.py` for compatibility.
- Add direct unit coverage and app wrapper parity coverage.
- Extend policy gates so the helper is owned by `rendering.py`, not duplicated in `app.py`, and the rendering module boundary remains free of app/curses/state/runtime/command/Web/dashboard/input imports.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the durable helper boundary.

## Acceptance Criteria

- [ ] `src/ga_tui/rendering.py` owns a deterministic process-group header aggregation helper.
- [ ] `src/ga_tui/app.py` keeps process summary/tool extraction and only passes explicit summaries/tool lists into the helper.
- [ ] Existing grouped process header strings are unchanged, including summary de-duplication, tool de-duplication, three-tool cap, and fallback `N 条过程` title.
- [ ] `tests/test_rendering.py` covers direct helper behavior and app wrapper parity.
- [ ] `scripts/check_policy_gates.py` covers helper ownership, representative behavior, app wrapper parity, duplicate-definition absence in `app.py`, and rendering boundary rules.
- [ ] Targeted compile, Ruff, rendering tests, policy gates, full tests, release hygiene, runtime smoke, package build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.
- [ ] The change is compared against `docs/agent-harness-architecture.md` before completion.

## Definition of Done

- Tests and policy gates lock the extracted boundary.
- `.trellis/spec/backend/agent-control-protocol.md` documents the new contract.
- Release verification and packaging smoke are green.
- Work is committed as one coherent extraction commit without unrelated dirty files.

## Technical Approach

Add a helper such as `process_group_header_parts(summary_values, tool_groups, turn_count, tool_limit=3)` in `rendering.py`. It should de-duplicate non-empty summaries in order, de-duplicate tool names in order up to the cap, and return `(title, tools)` where title is the compact joined summaries or `"<turn_count> 条过程"` when no summary exists. `app.process_group_header(...)` will continue traversing turns and invoking app-owned `process_summary_text(...)` and `process_tools(...)`, then call the helper before formatting with `process_group_header_text(...)`.

## Decision (ADR-lite)

Context: `process_group_header(...)` still mixes app-owned parsing with pure grouping title/tool aggregation.

Decision: Extract only the pure aggregation over explicit summaries and tool lists into `rendering.py`. Do not move process-body parsing, JSON-ish tool extraction, process grouping traversal, message rendering, or `RenderLine` ownership.

Consequences: The split reduces `app.py` process-rendering coupling without changing the process rendering contract. Later slices can continue separating render-planning from app-owned process parsing once stable neutral boundaries exist.

## Out of Scope

- Moving `process_tools(...)`, `process_summary_text(...)`, `process_title_text(...)`, JSON-ish payload parsing, IRC result parsing, process turn traversal, `render_assistant_text(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, `RenderLine` allocation, `cp(...)`, curses attrs, mutable `State`, Web Console, dashboard, runtime dispatch, command/input handling, storage roots, ledgers, artifacts, Secret Vault behavior, or history ownership.
- Changing grouped process rendering behavior or UI strings.
- Introducing reverse imports from `rendering.py` to `ga_tui.app`.

## Technical Notes

- Current function: `src/ga_tui/app.py::process_group_header(...)`.
- Existing formatter owner: `src/ga_tui/rendering.py::process_group_header_text(...)`.
- Policy gate owner: `scripts/check_policy_gates.py::assert_rendering_module_boundary()`.
- Spec owner: `.trellis/spec/backend/agent-control-protocol.md`.
- Architecture baseline: `docs/agent-harness-architecture.md`, especially strong Orchestrator responsibility and bounded worker/result protocols.
