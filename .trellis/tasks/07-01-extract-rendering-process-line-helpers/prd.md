# Extract Rendering Process Line Helpers

## Objective

Continue Goal 7 by extracting deterministic process-line formatting helpers from `src/ga_tui/app.py` into the curses-free `src/ga_tui/rendering.py` module, while preserving existing public compatibility names in `app.py` and avoiding any behavior rewrite.

## Scope

Move or introduce lower-level rendering helpers that format already-known process metadata into strings:

- Process turn labels from marker text.
- Tool suffix formatting from an already-parsed list of tool names.
- Collapsed process line text.
- Process detail line text.
- Process speech header text.
- Process speech summary line text.
- Expanded process header text.
- Process turn number fallback parsing.
- Process group header text from already-known summaries and tool names.
- Collapsed/expanded process child line/header text.

`app.py` should keep the existing public function names as compatibility wrappers. Those wrappers may inject app-owned dependencies such as `process_tools(...)`, `process_summary_text(...)`, `process_title_text(...)`, and `compact_description(...)`.

## Non-Goals

- Do not move `process_tools(...)` into `rendering.py`.
- Do not move JSON-ish tool payload parsing, interaction extraction, ask-user handling, IRC reply extraction, or search-noise detection.
- Do not move `preferred_group_visible_reply(...)`, `append_process_summary_line(...)`, `append_process_turn(...)`, or `render_assistant_text(...)`.
- Do not move message block rendering, markdown/plain block rendering, curses drawing, mutable `State`, command/input handlers, Web Console, dashboard, runtime dispatch, storage roots, ledgers, approvals, artifacts, or history ownership.
- Do not add a reverse import from `rendering.py` to `ga_tui.app`.

## Requirements

1. `src/ga_tui/rendering.py` owns pure helper functions for process-line string formatting.
2. `src/ga_tui/app.py` preserves current public function names and output behavior via compatibility wrappers or aliases.
3. `rendering.py` remains a lower-level dependency with no `ga_tui.app`, curses, mutable TUI `State`, runtime dispatch, command handler, Web Console, dashboard, input handler, storage-root, or ledger dependency.
4. The existing assistant rendering output remains unchanged for process line/header/group formatting.
5. Tests cover direct rendering helper behavior and app wrapper parity.
6. Policy gates assert the new helper ownership, wrapper parity, and no-reverse-dependency boundary.
7. The backend spec documents the new process-line helper boundary and explicitly keeps app-owned process/tool parsing outside `rendering.py`.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_rendering.py -q -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 gate before commit: full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline

This slice should move the implementation closer to `docs/agent-harness-architecture.md` by making process-line rendering a restricted lower-level helper boundary while leaving the strong Orchestrator facade in `app.py` responsible for process parsing, interaction handling, mutable UI state, commands, runtime side effects, ledgers, approvals, artifacts, history, and external-memory boundaries.
