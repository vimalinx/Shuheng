# Extract Subagent Chat Title Helpers

## Objective

Move pure subagent chat title, preview, and description policy out of `src/ga_tui/app.py` into `src/ga_tui/subagent_store.py`, while preserving existing behavior through `app.py` compatibility wrappers.

## Scope

- Move implementation logic for:
  - `subagent_chat_title_for_messages(...)`
  - `subagent_chat_history_preview(...)`
  - `subagent_chat_history_description(...)`
- Keep helpers pure over message lists and explicit fallback strings.
- Use existing lower-level history title policy helpers for compact title/description and suggested-title behavior.
- Keep `app.py` wrappers that inject `SubAgentRuntime` fields, `latest_visible_reply_text(...)`, and current display limits.
- Add or expand tests covering:
  - title selection from a normal non-process assistant summary
  - fallback to first user message when assistant process summaries are not valid titles
  - fallback to existing subagent chat title or agent name
  - description includes first/latest user and final visible assistant text
  - app wrapper parity
- Extend policy gates for ownership and no-reverse-import constraints.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the extraction succeeds.

## Out Of Scope

- Do not move `subagent_chat_session_payload(...)`, `messages_from_subagent_chat_payload(...)`, `save_subagent_chat_messages_to_history(...)`, `messages_from_history_transcript(...)`, `messages_from_subagent_history_meta(...)`, legacy import, Secret Vault payload decoding, chat save/load state mutation, Web Console payloads, rendering, runtime dispatch, storage roots, or transcript writing.
- Do not make subagent homes own normal conversation transcripts.
- Do not import `ga_tui.app` from extracted modules.

## Invariants

- Global history remains the owner of ordinary non-secret subagent chat transcripts.
- `subagent_store.py` may shape message rows into titles, previews, descriptions, counts, and preview rows, but must not parse or write transcript files.
- Process-only assistant summaries such as `OMP 思考` must not become subagent chat titles or descriptions.
- Extracted modules must not import `ga_tui.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, Web Console, dashboard, runtime dispatch, command handlers, renderer functions, Secret Vault storage, or history transcript writers.
- Public imports and call behavior from `ga_tui.app` remain compatible during decomposition.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/subagent_store.py tests/test_subagent_store.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/subagent_store.py tests/test_subagent_store.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_subagent_store.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release-gate verification before commit, matching the goal-7 plan.
