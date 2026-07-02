# Extract context pack helpers

## Goal

Continue the `src/ga_tui/app.py` decomposition until completion by taking the next low-risk phase: extract context-pack and memory-hydration helper logic into a lower-level `src/ga_tui/context_packs.py` module while preserving existing runtime behavior, public imports, release gates, and Shuheng storage semantics.

## What I already know

- The user wants to keep splitting `app.py` until the decomposition is complete.
- Completed phases already extracted `ui_types.py`, `text_utils.py`, `history_store.py`, `secret_vault.py`, and `governance.py`.
- `docs/app-py-decomposition-plan.md` defines the next phase as `context_packs.py`: memory inventory payloads, context layer assembly, context-pack artifact writing, and runtime prompt context/ref formatting.
- Extracted modules must not import `ga_tui.app`, `curses`, UI renderers, or command handlers.
- `app.py` must keep compatibility wrappers because tests/scripts still import many helpers from `ga_tui.app`.
- Mutable runtime paths are retargeted by policy gates; new helpers must accept paths/config explicitly or remain called through `app.py` wrappers.
- The architecture baseline favors strong Orchestrator control, artifact references, auditable context packs, external memory, and bounded subagents.
- The user invariant remains: global history owns conversations; subagent homes store profile/memory/runtime refs, not full normal transcripts.
- `uv.lock` is an unrelated untracked file and must not be included unless explicitly requested.

## Requirements

- Create `src/ga_tui/context_packs.py` for context-pack/domain helpers that are below `app.py`.
- Move only cohesive, low-level context-pack and memory-hydration helpers that can operate without importing `app.py`, `curses`, UI renderers, or command handlers.
- Keep `app.py` wrappers/re-exports for moved functions, passing current mutable paths and runtime facts explicitly.
- Preserve behavior for subagent task dispatch, OMP memory prompt/context bridge paths, artifact refs, memory candidate governance, and policy gates.
- Add or update tests/policy gates proving module boundary, wrapper compatibility, and at least one context-pack round trip.
- Do not rewrite runtime dispatch, Web Console, dashboard rendering, command handlers, or storage-root semantics in this task.
- Do not migrate normal history ownership or subagent transcript storage.

## Acceptance Criteria

- [ ] `src/ga_tui/context_packs.py` exists and contains extracted context-pack helpers.
- [ ] `context_packs.py` does not contain `ga_tui.app`, `from .app`, `import app`, `import curses`, or `from curses`.
- [ ] `app.py` keeps compatibility wrappers for moved helpers and passes mutable paths/config in explicitly.
- [ ] Policy gates assert the new module boundary and wrapper parity.
- [ ] Targeted tests cover context-pack helper behavior and round-trip artifact/reference behavior.
- [ ] Full phase verification passes: py_compile, Ruff, policy gates, pytest, compileall, git diff check.
- [ ] Storage/release-sensitive verification passes where relevant: release hygiene, runtime smoke, build, wheel smoke, and `shuheng-check`.

## Definition of Done

- Tests added/updated.
- Lint and syntax checks pass.
- Release/runtime smoke gates pass.
- Work is committed in a narrow `refactor:` commit.
- Remaining decomposition phases are left explicit for the next task.

## Technical Approach

Start from current `app.py` helper clusters related to memory hydration and context packs. Extract pure or mostly-pure row/record/formatting helpers first, keeping runtime-specific orchestration in `app.py`. Any helper that needs current storage paths should receive those paths as arguments from `app.py`.

Prefer a conservative extraction over a broad rewrite. The goal is dependency-direction improvement, not behavior changes.

## Decision (ADR-lite)

**Context**: `app.py` is still the orchestration facade and has mutable runtime globals retargeted by tests. Moving too much at once risks changing subagent context hydration and OMP bridge behavior.

**Decision**: Extract lower-level context-pack helpers into `context_packs.py`, while keeping active dispatch and UI commands in `app.py`.

**Consequences**: This reduces monolith coupling and prepares later runtime-dispatch extraction. Some wrappers will remain temporarily duplicated in `app.py` until command/runtime boundaries are split.

## Out of Scope

- Rendering, command parsing, input handling, and Web Console extraction.
- Runtime provider dispatch extraction.
- Storage root migration.
- Changing memory ownership semantics.
- Committing or modifying unrelated `uv.lock`.

## Technical Notes

- Primary plan source: `docs/app-py-decomposition-plan.md`.
- Architecture baseline: `docs/agent-harness-architecture.md`.
- Relevant spec index: `.trellis/spec/backend/index.md`.
- Required boundary style follows prior extracted modules: `history_store.py`, `secret_vault.py`, and `governance.py`.
