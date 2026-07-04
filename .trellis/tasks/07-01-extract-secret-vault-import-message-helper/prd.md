# Extract Secret Vault Import Message Helper

## Objective

Move Secret imported-session message shaping out of `src/shuheng/app.py` into the lower-level `src/shuheng/secret_vault.py` boundary without changing restore behavior.

## Scope

- Add a pure Secret Vault helper that converts an imported session payload's `raw_log` text into restore messages and round/message counts.
- Keep the existing `messages_from_secret_import_payload(payload)` public function available from `shuheng.app` as a compatibility wrapper.
- Keep app-owned transcript parsing and display policy injected from `app.py`: `_pairs`, `history_messages_from_pairs`, and `RESTORE_DISPLAY_ROUNDS`.
- Preserve existing fallback behavior:
  - parsed raw-log pairs use `history_messages_from_pairs(..., RESTORE_DISPLAY_ROUNDS)`;
  - non-empty unparseable raw log becomes a single assistant message with `loaded_rounds=1`, `total_rounds=1`, `message_count=1`;
  - empty payload becomes the current system empty-session message with zero rounds and one message.
- Add unit tests that cover parsed logs, unparseable raw logs, empty payloads, direct `secret_vault.py` helper behavior, and `app.py` compatibility wrapper parity.
- Keep policy gates and backend spec updated for the expanded Secret Vault boundary.

## Non-Goals

- Do not move `_pairs`, `_parse_native_history`, `history_messages_from_pairs`, restore orchestration, backend reset/restore, mutable `State`, UI commands, sidebar rendering, proxy env mutation, or encrypted Secret storage in this slice.
- Do not change `restore_secret_imported_session(...)` behavior except for delegating message shaping through the compatibility wrapper.
- Do not migrate storage roots or normal history transcript ownership.
- Do not introduce `shuheng.app` imports, curses imports, `State`, `SubAgentRuntime`, rendering types, gateway handlers, or runtime mutation helpers into `secret_vault.py`.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/secret_vault.py tests/test_secret_crypto.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/secret_vault.py tests/test_secret_crypto.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_secret_crypto.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release gate from `goal-7/plan.md` before commit.

## Architecture Baseline

This should move the system closer to `docs/agent-harness-architecture.md`: Secret imported-session value shaping becomes a policy-gated lower-level boundary, while the strong app Orchestrator still owns mutable state, restore side effects, approvals/UI, history parser injection, Web Console payloads, commands, and rendering.
