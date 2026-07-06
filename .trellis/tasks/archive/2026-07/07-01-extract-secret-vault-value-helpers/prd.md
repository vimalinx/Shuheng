# Extract Secret Vault Value Helpers

## Objective

Move pure Secret Vault value/payload helper logic out of `src/shuheng/app.py` into `src/shuheng/secret_vault.py`, while preserving existing behavior through `app.py` compatibility aliases or thin wrappers.

## Scope

- Move pure helper ownership for:
  - `secret_session_title_for_messages(...)`
  - `parse_secret_import_args(...)`
  - `parse_secret_proxy_chain(...)`
  - `normalize_secret_proxy_endpoint(...)`
- Keep `secret_session_state_payload(...)` behavior compatible while moving title normalization into the Secret Vault module where practical.
- Preserve Secret import disposition aliases, `skill://`-free unrelated behavior, proxy chain parsing, Tor endpoint normalization, and Secret title fallback behavior.
- Add or expand tests covering module behavior and `app.py` compatibility.
- Extend policy gates for ownership and no-reverse-import constraints.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the extraction succeeds.

## Out Of Scope

- Do not move Secret Vault unlock/setup state machine, password-entry UI, Secret prompt/hint rendering, import validation, policy gates, one-way import execution, ordinary-source deletion/archive, Secret file IO, encrypted read/write, network health checks, proxy environment mutation, native/imported restore orchestration, backend reset, history parsing, Web Console payloads, curses rendering, commands, or transcript storage.
- Do not make `secret_vault.py` import `shuheng.app`, curses, mutable TUI `State`, runtime providers, Web Console, dashboard, command handlers, or rendering owners.
- Do not change Secret Vault storage format, file paths, approval requirements, encryption behavior, or local runtime side effects.

## Invariants

- `secret_vault.py` may own Secret-specific value shaping, message payload shaping, import-argument parsing, and proxy endpoint string normalization.
- `app.py` remains the owner of mutable `State`, approval/command wiring, UI hints, import/delete/archive orchestration, proxy env mutation, and runtime/backend restore.
- Public imports and call behavior from `shuheng.app` remain compatible during decomposition.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/secret_vault.py tests/test_secret_crypto.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/secret_vault.py tests/test_secret_crypto.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_secret_crypto.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release-gate verification before commit, matching the goal-7 plan.
