# Extract Secret Vault Native Import Match Helper

## Objective

Move the pure "find the native Secret session represented by an imported Secret entry" logic out of `src/ga_tui/app.py` into `src/ga_tui/secret_vault.py`, while keeping `app.py` as the compatibility wrapper that loads native entries from `State`.

## Scope

- Add a pure helper in `secret_vault.py` that accepts an `import_entry` plus already-loaded native entries and returns the first non-error native entry represented by that import.
- Keep `app.secret_native_entry_for_import_entry(state, import_entry)` available with the same public signature.
- Preserve current matching semantics by delegating to `secret_import_represented_by_native(...)`.
- Exclude error native entries from matching.
- Add unit tests for direct helper behavior, no-match behavior, error-entry filtering, and app wrapper delegation.
- Update policy gates and backend spec for the expanded Secret Vault boundary.

## Non-Goals

- Do not move native-entry loading, sidebar row construction, Secret restore behavior, encrypted file IO, mutable `State`, approval/UI/command wiring, proxy env mutation, Web Console payloads, or rendering.
- Do not change `secret_import_represented_by_native(...)` semantics.
- Do not change restore selection behavior beyond delegating the existing loop through the lower-level helper.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/secret_vault.py tests/test_secret_crypto.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/secret_vault.py tests/test_secret_crypto.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_secret_crypto.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release gate from `goal-7/plan.md` before commit.

## Architecture Baseline

This should move the system closer to `docs/agent-harness-architecture.md`: imported/native Secret matching becomes a lower-level pure boundary, while the app Orchestrator still owns state loading, restore side effects, approvals/UI, encrypted storage wiring, Web Console payloads, commands, and rendering.
