# Extract runtime dispatch helpers

## Goal

Continue decomposing `src/shuheng/app.py` by extracting the next low-risk part of runtime dispatch into `src/shuheng/runtime_dispatch.py`: provider identity helpers, Oh My Pi runtime metadata readers, provider-neutral `RuntimeTaskRequest` construction, and the small compatibility `put_agent_runtime_task(...)` wrapper.

## What I already know

- The user wants to keep splitting `app.py` until the decomposition is complete.
- The prior phase extracted `context_packs.py` and committed `e6c5ffa refactor: extract context pack helpers`.
- `docs/app-py-decomposition-plan.md` Phase 5 names `runtime_dispatch.py` as the next module after context packs.
- The runtime request/event dataclasses already live in `src/shuheng/runtime.py`.
- Existing hot paths call `agent_runtime_provider_id(...)`, `is_ohmypi_runtime_agent(...)`, `ohmypi_native_session_file(...)`, `ohmypi_native_context_usage(...)`, `runtime_task_request_for_agent(...)`, and `put_agent_runtime_task(...)` from `app.py`.
- Runtime stream queue consumption, direct subagent chat/task state transitions, and UI updates remain tightly coupled to `State`, `Message`, `StreamTarget`, and TUI queues; those should not move in this task.
- Extracted modules must not import `shuheng.app`, `curses`, UI renderers, command handlers, `State`, or `SubAgentRuntime`.
- `app.py` must keep compatibility wrappers for existing tests/scripts and must preserve mutable runtime behavior.
- `uv.lock` is unrelated and must stay out of commits.

## Requirements

- Create `src/shuheng/runtime_dispatch.py` as a lower-level helper module.
- Move only helpers that can operate from explicit inputs or generic runtime-agent objects:
  - `agent_runtime_provider_id`.
  - `is_ohmypi_runtime_agent`.
  - `ohmypi_native_session_file`.
  - `ohmypi_native_context_usage`.
  - `runtime_task_request_for_agent`.
  - `put_agent_runtime_task`.
- Keep `app.py` wrappers/re-exports for these names.
- Preserve `RuntimeTaskRequest` fields exactly, including bounded durable record semantics already owned by `runtime.py`.
- Preserve fallback behavior:
  - unknown provider id -> `"unknown"`.
  - failed `get_llm_name(model=True)` -> empty model string.
  - missing `put_runtime_task` -> call `put_task(request.prompt, source=request.source)`.
  - missing/invalid OMP context usage -> `{}`.
- Add policy gates proving the new module boundary and wrapper parity.
- Add targeted unit tests for runtime dispatch helper behavior and fallback paths.
- Do not extract `runtime_context_prompt_for_agent(...)` in this task because it depends on context-pack formatting and OMP full/ref prompt state mutation.
- Do not extract stream queue consumers, subagent state transitions, scheduler dispatch, or Web Console runtime pumping in this task.

## Acceptance Criteria

- [ ] `src/shuheng/runtime_dispatch.py` exists and contains the moved provider-neutral helpers.
- [ ] `runtime_dispatch.py` does not import `shuheng.app`, `.app`, `app`, `curses`, UI renderers, `State`, or `SubAgentRuntime`.
- [ ] `app.py` keeps compatibility wrappers and existing call sites keep working.
- [ ] Policy gates assert module boundary and wrapper parity.
- [ ] Targeted tests cover request construction, provider id fallback, OMP metadata helpers, and `put_agent_runtime_task` fallback.
- [ ] Verification passes: py_compile, Ruff, policy gates, targeted pytest, full pytest, compileall, git diff check.
- [ ] Runtime/release-sensitive verification passes: release hygiene, runtime smoke, build, wheel smoke, and `shuheng-check`.

## Definition of Done

- Tests added/updated.
- Specs updated if this creates a reusable module-boundary contract.
- All required gates pass.
- Work is committed in a narrow `refactor:` commit.
- Remaining runtime-dispatch decomposition work stays explicit for later tasks.

## Technical Approach

Start with the small helper cluster near `build_main_runtime_context_pack(...)` in `app.py`. Move the generic logic into `runtime_dispatch.py`, importing only `typing.Any` and `RuntimeTaskRequest`. Keep all app-facing names as wrappers so existing policy gates and tests remain compatible.

The module should stay below `app.py` and beside `runtime.py`: `runtime.py` owns dataclasses and registry abstractions, while `runtime_dispatch.py` owns lightweight provider-neutral helper functions. State-dependent prompt selection and queue draining remain in `app.py`.

## Decision (ADR-lite)

**Context**: The runtime dispatch area is security- and provenance-sensitive, but not all of it is ready to move. Stream consumption and subagent status mutation still depend on UI state and task-ledger side effects.

**Decision**: Extract only provider-neutral, app-independent helpers first. Leave stateful runtime context prompt selection and queue consumers in `app.py`.

**Consequences**: `app.py` shrinks and dependency direction improves without changing dispatch behavior. A later task can extract stream normalization only after a clear state/event boundary exists.

## Out of Scope

- Stream queue consumption and UI message mutation.
- `runtime_context_prompt_for_agent(...)`.
- Subagent task/chat state transitions.
- Scheduler dispatch behavior.
- Web Console runtime pumping.
- Runtime provider dataclass changes.
- Storage-root or history ownership changes.
- `uv.lock`.

## Technical Notes

- Primary plan source: `docs/app-py-decomposition-plan.md`.
- Runtime boundary docs: `docs/runtime-provider-control-plane.md`.
- Architecture baseline: `docs/agent-harness-architecture.md`.
- Relevant spec: `.trellis/spec/backend/agent-control-protocol.md`.
- Current helper cluster starts near `src/shuheng/app.py` around `agent_runtime_provider_id(...)`.
