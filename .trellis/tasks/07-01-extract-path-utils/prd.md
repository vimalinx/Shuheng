# Extract path utility helpers

## Goal

Continue decomposing `src/ga_tui/app.py` by moving pure filesystem path normalization and containment helpers into a lower-level `src/ga_tui/path_utils.py` module, while preserving app-level compatibility wrappers and Shuheng storage-root behavior.

## Requirements

- Add `src/ga_tui/path_utils.py`.
- Move pure helpers out of `src/ga_tui/app.py`:
  - `normalized_path(path)`
  - `path_is_within(path, root)`
- Add a low-level normal-history predicate that accepts explicit roots:
  - `is_normal_session_log_path(path, *, model_responses_dir, session_trash_dir)`
- Keep `src/ga_tui/app.py` compatibility wrappers for existing callers and tests.
- Preserve current semantics:
  - `normalized_path` expands `~` and returns an absolute path.
  - `path_is_within` resolves real paths and returns `False` instead of raising.
  - normal session logs must be under `MODEL_RESPONSES_DIR`, outside `SESSION_TRASH_DIR`, and have `model_responses*.txt` basename shape.
- Add tests and policy gates for the new module boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the path utility boundary.

## Acceptance Criteria

- [ ] `ga_tui.path_utils` owns the path helper implementations.
- [ ] `ga_tui.app.normalized_path`, `ga_tui.app.path_is_within`, and `ga_tui.app.is_normal_session_log_path` remain behavior-compatible.
- [ ] `path_utils.py` does not import `ga_tui.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, Web Console, dashboard, history store, Secret Vault, runtime dispatch, command handlers, or rendering functions.
- [ ] Existing path-safety tests pass and include direct module coverage plus app wrapper parity.
- [ ] Policy gates assert the ownership and lower-level dependency boundary.
- [ ] Phase exit verification passes.

## Definition of Done

- New module, app wrappers, tests, policy gate, and spec boundary update are implemented.
- No behavior change to storage roots, history ownership, session metadata, subagent homes, Secret Vault, Web Console payloads, or rendering.
- Full phase verification passes.
- Work is committed separately from unrelated untracked files.

## Technical Approach

Extract the exact `normalized_path` and `path_is_within` logic into `path_utils.py`. Add a parameterized normal-history predicate there so the helper can stay low-level and avoid importing app globals. Keep `app.is_normal_session_log_path(...)` as the app-global wrapper that injects `MODEL_RESPONSES_DIR` and `SESSION_TRASH_DIR`.

## Decision (ADR-lite)

Context: History, Secret Vault import validation, Web Console session refs, workspace checks, and policy gates all rely on the same path normalization/containment semantics. Keeping those helpers in `app.py` forces lower-level storage modules or future extractions to either depend on the app facade or duplicate safety logic.

Decision: Create `path_utils.py` as a pure leaf module for path normalization and containment. App-global storage-root selection remains in `app.py`.

Consequences: Future history/Secret/subagent-store extraction can share one path safety implementation without importing `ga_tui.app`; path root ownership remains app-configured and test-retargetable.

## Out of Scope

- Moving Shuheng storage-root constants.
- Moving `configure_frontend_history_storage()`.
- Changing `MODEL_RESPONSES_DIR`, `SESSION_TRASH_DIR`, `SHUHENG_HOME`, legacy bootstrap, or import behavior.
- Moving history metadata, transcript parsing, Secret Vault import validation, workspace storage, Web Console payloads, commands, rendering, or input handlers.

## Technical Notes

- Relevant decomposition plan: `docs/app-py-decomposition-plan.md`, Phase 1/2 dependency direction.
- Relevant spec scenario: `.trellis/spec/backend/agent-control-protocol.md`, Shuheng-owned storage roots and session history scenarios.
- Existing tests for path safety live in `tests/test_path_safety.py`.
