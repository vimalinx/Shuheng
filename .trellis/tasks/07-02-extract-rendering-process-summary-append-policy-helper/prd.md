# Extract Rendering Process Summary Append Policy Helper

## Goal

Continue Goal 7 by moving one more deterministic process-rendering decision out of `src/shuheng/app.py` and into `src/shuheng/rendering.py`, without changing transcript rendering behavior.

## What I Already Know

- `src/shuheng/rendering.py` already owns pure process text helpers such as `process_summary_text(...)`, `process_title_text_from_parts(...)`, process-line string formatters, process-noise predicates, process-group header aggregation, and `process_turn_lines(...)`.
- `src/shuheng/app.py` still owns `append_process_summary_line(rendered, marker, body)`, which parses the raw process body, formats the final summary row, and mutates the caller-provided `rendered` list.
- The only pure policy inside `append_process_summary_line(...)` is whether a precomputed summary line should be appended: append when `summary` is non-empty and not equal to `执行中`.
- `app.py` must remain the owner of raw body parsing, `process_tools(...)`, JSON-ish tool extraction, process-turn traversal, list mutation, `RenderLine` conversion, curses attrs, mutable `State`, Web Console, dashboard, runtime dispatch, ledgers, history, and Secret Vault behavior.
- `docs/agent-harness-architecture.md` requires the decomposition to preserve a strong Orchestrator facade and move deterministic lower-level transforms behind auditable boundaries.

## Requirements

- Add a pure helper in `src/shuheng/rendering.py` that receives explicit summary and preformatted summary line values and returns the lines that should be appended for that process summary policy.
- Keep `src/shuheng/app.py` exposing the new helper as a compatibility alias.
- Keep `append_process_summary_line(rendered, marker, body)` in `app.py` as the compatibility wrapper that:
  - computes `summary = process_summary_text(body)`,
  - computes the formatted row with `process_speech_summary_line(marker, body, summary)`,
  - mutates the supplied `rendered` list,
  - returns the same boolean result as before.
- Preserve existing behavior:
  - non-empty summary other than `执行中` appends one formatted summary line and returns `True`,
  - empty summary appends nothing and returns `False`,
  - summary exactly equal to `执行中` appends nothing and returns `False`.
- Update unit tests, policy gates, and `.trellis/spec/backend/agent-control-protocol.md` to document and enforce the new boundary.

## Acceptance Criteria

- `rendering.py` owns the new helper and the helper has no dependency on `shuheng.app`, curses, mutable `State`, runtime dispatch, Web Console, dashboard, command/input handlers, ledgers, artifacts, history stores, Secret Vault storage, or JSON-ish tool parsing.
- `app.py` contains no local implementation of the new helper beyond a compatibility alias.
- Existing visible assistant/process rendering remains unchanged.
- Tests cover direct helper behavior and `app.append_process_summary_line(...)` wrapper parity.
- Policy gates cover helper ownership, representative behavior, alias parity, duplicate-definition absence in `app.py`, and the existing rendering no-reverse-dependency boundary.
- Targeted and full verification gates pass before commit.

## Out Of Scope

- Moving `process_tools(...)`, JSON-ish parsing, `extract_interaction_request(...)`, `irc_reply_snippets_from_process_body(...)`, `append_process_turn(...)`, `render_assistant_text(...)`, `message_block_lines(...)`, `message_lines_from_cache(...)`, `RenderLine` allocation, curses attrs, or mutable UI state into `rendering.py`.
- Changing process folding/grouping behavior, user-visible process strings, history/session title policy, runtime provider behavior, token accounting, Web Console behavior, dashboard behavior, Secret Vault behavior, or storage roots.

## Verification Plan

- `python3 -m py_compile src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full project Ruff, pytest, release hygiene, runtime smoke, compileall, `git diff --check`, package build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.
- Compare against `docs/agent-harness-architecture.md` before declaring the slice complete.

## Rollback Plan

- Revert this extraction commit if helper ownership causes a regression.
- Since this slice is a pure helper extraction with an app wrapper, rollback does not require runtime-state, history, Secret Vault, or storage migration.
