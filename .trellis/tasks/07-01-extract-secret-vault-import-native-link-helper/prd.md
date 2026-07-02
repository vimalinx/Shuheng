# Extract Secret Vault Import Native Link Helper

## Goal

Move the pure Secret Vault imported-session to native-session link predicate out of `src/ga_tui/app.py` into `src/ga_tui/secret_vault.py`, while preserving current sidebar and restore behavior through `app.py` wrappers.

## Requirements

- Move `secret_import_represented_by_native(import_entry, native_entries)` into `secret_vault.py`.
- Preserve the current matching behavior exactly:
  - A native session represents an imported entry when its normalized `origin_import_path` equals the imported entry path.
  - A native session represents an imported entry when `origin_stable_id` equals the imported entry `stable_id`.
  - A native session represents an imported entry when its `title` equals the imported entry `title`.
  - Entries with empty values must not create accidental matches.
- Keep `app.py` exposing `secret_import_represented_by_native(...)` as a compatibility alias.
- Keep `secret_native_entry_for_import_entry(state, import_entry)` in `app.py`, because it reads current Secret native entries from mutable `State`.
- Do not move sidebar row construction, Secret restore orchestration, encrypted storage, or state mutation in this slice.
- Add tests covering path, stable-id, title, no-match, and app alias parity.
- Extend policy gates and backend spec text for the expanded Secret Vault pure boundary.

## Acceptance Criteria

- [ ] `secret_vault.py` owns the pure import/native link predicate.
- [ ] `app.py` keeps public compatibility and uses the moved helper.
- [ ] Sidebar/import restore behavior remains unchanged.
- [ ] Unit tests and policy gates cover the new helper and no-reverse-import boundary.
- [ ] Targeted and full verification gates from `goal-7/plan.md` pass before commit.

## Definition of Done

- Targeted `py_compile`, Ruff, Secret tests, and policy gates pass.
- Full Ruff, pytest, release hygiene, runtime smoke, compileall, package build, wheel smoke, `git diff --check`, and `shuheng-check` pass.
- Architecture baseline comparison against `docs/agent-harness-architecture.md` is recorded.
- A focused work commit is created for this slice only.

## Technical Approach

Add `secret_import_represented_by_native(import_entry, native_entries)` to `secret_vault.py`, using the same normalized path and field comparisons currently implemented in `app.py`. Replace the app implementation with a direct alias and keep `secret_native_entry_for_import_entry(...)` as the stateful wrapper that loads `secret_native_session_entries(state, include_payload=False)`.

## Out of Scope

- Secret restore, backend reset, provider mutation, encrypted IO, import execution, source deletion/archive, network checks, or proxy env mutation.
- Sidebar row construction and `RenderLine`/curses rendering.
- Web Console/dashboard payloads.
- Global history transcript ownership or subagent home semantics.

## Technical Notes

- Current implementation lives in `src/ga_tui/app.py` near `secret_import_represented_by_native(...)`.
- Existing lower-level Secret helpers and tests live in `src/ga_tui/secret_vault.py` and `tests/test_secret_crypto.py`.
- The architecture baseline remains `docs/agent-harness-architecture.md`: this slice moves pure value matching lower while keeping app orchestration stateful and single-writer.
