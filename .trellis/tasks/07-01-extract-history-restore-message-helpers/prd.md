# Extract History Restore Message Helpers

## Objective

Move pure history restore message shaping helpers out of `src/shuheng/app.py` into `src/shuheng/history_store.py`, while preserving existing behavior through `app.py` compatibility wrappers.

## Scope

- Move the implementation logic for:
  - `history_round_count(...)`
  - `extract_recent_ui_messages_from_pairs(...)`
  - `history_messages_from_pairs(...)`
- Keep the low-level helpers pure by accepting dependency callables for:
  - prompt/user text extraction
  - prompt-to-tool-result extraction
  - response-segment formatting
- Keep `app.py` wrappers that inject `_user_text`, `_tool_results_from_prompt`, `_format_response_segment`, `RESTORE_DISPLAY_ROUNDS`, and `Message` compatibility.
- Add or expand tests covering:
  - user-round counting with fallback to pair count
  - recent-round selection from the end of parsed transcript pairs
  - assistant segment grouping across promptless process turns
  - `history_messages_from_pairs(...)` loaded/total round counts and `Message` conversion
  - `app.py` wrapper parity with `history_store.py`
- Extend policy gates for the new history-store boundary and no-reverse-import constraints.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the extraction succeeds.

## Out Of Scope

- Do not move `_pairs`, `_user_text`, `_tool_results_from_prompt`, `_format_response_segment`, transcript parsing regexes, `read_history_messages(...)`, `restore_backend_and_recent_messages(...)`, or provider/backend restore orchestration.
- Do not change title/description policy, process-summary filtering policy, storage roots, Secret Vault behavior, subagent homes, Web Console payloads, curses rendering, or runtime dispatch.
- Do not parse or write transcript files from the new lower-level helpers.

## Invariants

- Global Shuheng history remains the owner of normal conversation transcripts.
- `history_store.py` may shape already-parsed transcript pairs into restore-preview UI message records, but it must not own app runtime restore, provider reset/switching, sidebar rendering, or metadata writes.
- Extracted modules must not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, Web Console, dashboard, runtime dispatch, command handlers, or renderer functions.
- Public imports and call behavior from `shuheng.app` remain compatible during decomposition.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/history_store.py tests/test_history_store.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/history_store.py tests/test_history_store.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_history_store.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release-gate verification before commit, matching the goal-7 plan.
