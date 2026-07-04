# Extract History Preview Helpers

## Objective

Move the pure history restore preview compaction helper out of `src/shuheng/app.py` into `src/shuheng/history_store.py`, while preserving existing behavior through an `app.py` compatibility wrapper.

## Scope

- Move `compact_ui_preview_messages_from_pairs(...)` logic into `history_store.py`.
- Keep the low-level helper pure by accepting dependency callables for:
  - prompt/user text extraction
  - assistant response preview text shaping
- Keep `app.py` as the compatibility wrapper that injects existing app-level behavior and constants.
- Add or expand unit tests that verify:
  - recent restore preview rounds are selected from the end of the transcript pairs
  - blank user prompts are skipped
  - assistant `"执行中"` previews are not included
  - wrapper parity between `app.py` and `history_store.py`
- Extend policy gates so the history-store boundary proves the helper lives below `app.py` and does not import UI/runtime orchestration.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable boundary if the extraction succeeds.

## Out Of Scope

- Do not move `_pairs`, `_user_text`, transcript parsing regexes, `load_history`, sidebar/home rendering, or active session restore orchestration.
- Do not move title/description policy such as `suggested_session_title`, `session_preview_from_pairs`, `session_description_from_pairs`, or process-only title detection in this slice.
- Do not change history storage roots, `session_meta.json` ownership, Secret Vault behavior, subagent homes, Web Console payloads, curses rendering, or runtime dispatch.
- Do not parse/write transcript files from the new helper.

## Invariants

- Global Shuheng history remains the owner of normal conversation transcripts.
- Subagent homes remain profile/memory/runtime refs only, not normal transcript stores.
- Extracted lower-level modules must not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, gateway handlers, rendering functions, or runtime mutation helpers.
- Public imports from `shuheng.app` must remain compatible during decomposition.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/history_store.py tests/test_history_store.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/history_store.py tests/test_history_store.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_history_store.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release-gate verification before commit, matching the goal-7 plan.
