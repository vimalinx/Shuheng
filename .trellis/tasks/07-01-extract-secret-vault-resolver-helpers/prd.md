# Extract Secret Vault Resolver Helpers

## Goal

Move pure Secret Vault session resolver logic out of `src/ga_tui/app.py` into `src/ga_tui/secret_vault.py`, while preserving current `ga_tui.app` compatibility wrappers and all restore/import behavior.

## Requirements

- Add lower-level resolver helpers in `secret_vault.py` that accept already-loaded `entries` plus a user `target`.
- Preserve the current matching behavior for imported Secret sessions:
  - empty target returns the current usage message.
  - numeric target matches 1-based list index.
  - text target matches the current candidate set: raw path, normalized path, filename, filename without `.secret`, `stable_id`, or source `basename`.
  - missing entries and unmatched targets return the same Chinese error text as today.
- Preserve the current matching behavior for native Secret sessions:
  - empty target returns the current usage message.
  - numeric target matches 1-based list index.
  - text target matches `session_id`, title, or sidebar-key form after normal sidebar-key normalization.
  - missing entries and unmatched targets return the same Chinese error text as today.
- Keep `app.py` wrappers named `resolve_secret_imported_session(state, target)` and `resolve_secret_native_session(state, target)` so existing callers and tests remain compatible.
- Add unit coverage for the new lower-level helpers and `app.py` wrapper parity where practical.
- Extend policy gates so `secret_vault.py` remains a lower-level Secret module without reverse imports into `ga_tui.app`, curses, mutable TUI state, runtime providers, rendering, Web Console, or command handlers.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the resolver boundary is established.

## Acceptance Criteria

- [ ] `secret_vault.py` owns pure resolver helpers over `entries + target`.
- [ ] `app.py` only loads entries from `State` and delegates resolver matching.
- [ ] Existing Secret restore and import orchestration behavior is unchanged.
- [ ] Tests cover imported/native resolver success, index matching, missing entries, and unmatched target errors.
- [ ] Policy gates pass and include the expanded Secret Vault module boundary.
- [ ] Targeted and full verification gates from `goal-7/plan.md` pass before commit.

## Definition of Done

- Targeted `py_compile`, Ruff, Secret tests, and policy gates pass.
- Full Ruff, pytest, release hygiene, runtime smoke, compileall, package build, wheel smoke, `git diff --check`, and `shuheng-check` pass.
- Architecture baseline comparison against `docs/agent-harness-architecture.md` is recorded.
- A focused work commit is created for this slice only.

## Technical Approach

Add `resolve_secret_imported_session_entry(entries, target)` and `resolve_secret_native_session_entry(entries, target)` to `secret_vault.py`. These helpers should filter out error entries internally or receive already-filtered entries consistently with existing behavior, normalize target strings in the same way as `app.py`, and return `(entry | None, error_text)`.

Keep the stateful `app.py` wrappers responsible for calling `secret_imported_session_entries(...)` and `secret_native_session_entries(...)` with the correct `State` and payload flags. Do not move restore orchestration or encrypted storage in this slice.

## Out of Scope

- Secret Vault unlock/setup state, password-entry UI, prompt/hint rendering, approval gates, commands, or curses rendering.
- Import validation/execution, source deletion/archive, encrypted file IO, metadata writes, storage paths, or data migrations.
- Backend restore orchestration, provider reset, runtime state mutation, network checks, or proxy environment mutation.
- Web Console payloads, dashboard payloads, global history transcript ownership, or subagent home semantics.

## Technical Notes

- Current wrappers live in `src/ga_tui/app.py` near `resolve_secret_imported_session(...)` and `resolve_secret_native_session(...)`.
- Existing Secret lower-level helpers live in `src/ga_tui/secret_vault.py`.
- Existing Secret tests live in `tests/test_secret_crypto.py`.
- The architecture baseline remains `docs/agent-harness-architecture.md`: this slice should move pure value matching lower, while keeping the app facade as the orchestrator for mutable state and restore side effects.
