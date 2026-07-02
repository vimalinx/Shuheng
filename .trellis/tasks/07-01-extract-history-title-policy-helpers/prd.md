# Extract History Title Policy Helpers

## Objective

Move process-summary-safe session title, preview, description, and metadata-text policy out of `src/ga_tui/app.py` into a lower-level helper module, while preserving current behavior through `app.py` compatibility wrappers.

## Scope

- Add a pure policy module for history title/description helpers.
- Move or wrap the implementation logic for:
  - `short_session_title(...)`
  - `compact_description(...)`
  - `text_has_process_markers(...)`
  - `session_summary_titles_from_text(...)`
  - `session_response_preview_text(...)`
  - `session_preview_from_pairs(...)`
  - `is_process_only_session_title(...)`
  - `history_cache_has_process_only_preview(...)`
  - `message_text_for_metadata_context(...)`
  - `session_description_from_pairs(...)`
  - `suggested_session_title(...)`
- Keep `app.py` compatibility wrappers that inject app-owned prompt parsing and rendering-derived visible-reply extraction where needed.
- Keep process marker regexes as a single imported source of truth if they are moved with the policy module.
- Add or expand tests covering:
  - process-marked summaries are not title candidates
  - cached process-only preview/description markers are detected
  - response preview falls back to final visible prose when summaries are process-only
  - session preview/description prefers user prompt and usable assistant summary
  - metadata context strips hidden process/tool/control text
  - app wrapper parity with the new module
- Extend policy gates for module ownership, no reverse imports, and no curses/TUI/runtime dependency.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the extraction succeeds.

## Out Of Scope

- Do not move transcript file parsing/writing, `_pairs(...)`, `_user_text(...)`, `read_history_messages(...)`, `load_history(...)`, `restore_backend_and_recent_messages(...)`, Web Console payloads, provider/backend restore orchestration, runtime dispatch, command handlers, or rendering functions.
- Do not change session storage roots, Secret Vault behavior, subagent homes, global history ownership, or metadata write policy.
- Do not make metadata refresh author persisted titles; main-runtime `session.rename` remains the title-write authority.
- Do not import `ga_tui.app` from extracted modules.

## Invariants

- Global Shuheng history remains the owner of normal conversation transcripts.
- Process-only summaries such as `OMP 思考`, `执行中`, tool-call labels, hidden thinking, and tool-control blocks must not become session titles, previews, descriptions, or AI metadata context.
- A normal non-process assistant `<summary>` can still be used as a title/preview candidate.
- Extracted modules must not import `ga_tui.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, Web Console, dashboard, runtime dispatch, command handlers, or renderer functions.
- Public imports and call behavior from `ga_tui.app` remain compatible during decomposition.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/history_titles.py tests/test_history_titles.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/history_titles.py tests/test_history_titles.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_history_titles.py tests/test_history_store.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release-gate verification before commit, matching the goal-7 plan.
