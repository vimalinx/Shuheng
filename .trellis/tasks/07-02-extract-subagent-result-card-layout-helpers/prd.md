# Extract subagent result card layout helpers

## Goal

Continue the `src/shuheng/app.py` decomposition by moving the deterministic subagent result card layout decisions into the curses-free `src/shuheng/rendering.py` helper layer, while preserving the existing TUI behavior and keeping the Orchestrator facade responsible for message traversal, rendering dependency injection, and curses `RenderLine` assembly.

## Requirements

- Add a pure rendering helper for subagent result card string/layout decisions in `src/shuheng/rendering.py`.
- Keep `src/shuheng/app.py` as the compatibility facade and owner of `RenderLine` allocation, `cp(...)`, curses attributes, `render_subagent_result_body(...)`, `markdown_blocks(...)`, `plain_blocks(...)`, and `subagent_result_metadata_detail_blocks(...)`.
- Preserve current card output for valid subagent result notices, including title, metadata summary row, metadata expanded/collapsed state, reply header, reply body prefixing, and footer.
- Keep invalid/non-subagent messages returning no card blocks.
- Re-export the new helper through `src/shuheng/app.py` for compatibility.
- Add tests for direct helper behavior and app wrapper parity.
- Extend policy gates so the helper is owned by `rendering.py`, not duplicated in `app.py`, and the rendering module remains a lower-level dependency with no reverse import.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the durable card-layout boundary.

## Acceptance Criteria

- [ ] `src/shuheng/rendering.py` owns a pure helper for subagent result card layout records or text decisions.
- [ ] `src/shuheng/app.py` keeps all `RenderLine`, `cp(...)`, curses, markdown/plain conversion, metadata detail block, and rendered-body injection responsibilities.
- [ ] Existing subagent result card text output is preserved.
- [ ] `tests/test_rendering.py` covers direct helper behavior for collapsed metadata, expanded metadata, no-metadata cards, and app wrapper parity.
- [ ] `scripts/check_policy_gates.py` covers ownership, no duplicate app implementation, representative behavior, and rendering boundary rules.
- [ ] Targeted compile, Ruff, rendering tests, policy gates, full tests, release hygiene, runtime smoke, package build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` pass.
- [ ] The change is compared against `docs/agent-harness-architecture.md` before completion.

## Definition of Done

- Tests added/updated for the new helper boundary.
- Lint, tests, policy gates, release gates, and packaging smoke are green.
- Spec notes are updated if the boundary changes.
- Work is committed as one coherent extraction commit without unrelated dirty files.

## Technical Approach

Use a neutral layout helper in `rendering.py` that accepts explicit notice metadata, expanded state, and body width and returns deterministic string decisions. `app.py` will parse the notice, render and split the body, call the helper, then convert the neutral strings into the existing `RenderLine` rows using the current attrs and block renderers.

## Decision (ADR-lite)

Context: `subagent_result_card_blocks(...)` still mixes pure layout decisions with curses-specific row creation and injected app dependencies.

Decision: Extract only the pure card layout/string decisions into `rendering.py`. Do not move any dependency that requires `RenderLine`, curses attrs, body rendering, message traversal, ledgers, artifacts, history, or mutable state.

Consequences: This reduces `app.py` coupling and locks another rendering boundary while keeping behavior stable. A later slice can revisit deeper message-card assembly only after shared UI types and rendering ownership are broader and safer.

## Out of Scope

- Moving `RenderLine`, `cp(...)`, curses attrs, `markdown_blocks(...)`, `plain_blocks(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, `render_assistant_text(...)`, or `render_subagent_result_body(...)`.
- Changing subagent result notice parsing or metadata semantics.
- Changing task ledgers, artifacts, approvals, Secret Vault, Web Console, dashboard, runtime dispatch, command/input handling, storage roots, or history ownership.
- Introducing reverse imports from `rendering.py` to `shuheng.app`.

## Technical Notes

- Current function: `src/shuheng/app.py::subagent_result_card_blocks(...)`.
- Existing helper owner: `src/shuheng/rendering.py`.
- Policy gate owner: `scripts/check_policy_gates.py::assert_rendering_module_boundary()`.
- Spec owner: `.trellis/spec/backend/agent-control-protocol.md`.
- Architecture baseline: `docs/agent-harness-architecture.md`, especially strong Orchestrator responsibility and bounded worker/result protocols.
