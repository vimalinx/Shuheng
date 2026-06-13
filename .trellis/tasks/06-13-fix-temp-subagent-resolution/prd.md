# Fix Temp Subagent Resolution After Creation

## Goal

Make `/agent new --temp ...` immediately usable in the same TUI session so a real user can create a temporary subagent and then run `/agent ask <id|name> ...` without getting `找不到子 agent`.

## Requirements

- Temporary subagents created when `active_ui_session_key(state)` is empty must be loaded from the same fallback owner directory used at creation time.
- `/agent ask <created-temp-id> ...` must resolve the newly created temp subagent after command handlers call `load_subagents(state)`.
- Existing persistent subagent loading must remain unchanged.
- Session-scoped temporary subagents must stay isolated to their active owner when an active UI session key exists.
- The fix must not promote temporary subagents to persistent storage or write long-term memory.

## Acceptance Criteria

- [x] A regression test creates a temp subagent with an empty active session key, reloads subagents, and resolves it by id.
- [x] The same regression test verifies temp subagent storage remains under `temp/ga-tui-subagents/current/...` for the empty-key case.
- [x] Existing subagent persistence and policy gate tests keep passing.
- [x] Real TUI smoke can create `TUI-Smoke` and resolve it by id for `/agent ask`.
- [x] Required checks pass: `py_compile`, `scripts/check_policy_gates.py`, `compileall`, `git diff --check`, and `ga-tui-check --root /home/vimalinx/Programs/GenericAgent`.

## Definition of Done

- Bug fix committed with tests.
- No unrelated changes are included.
- Any temporary smoke artifacts outside the repo are left as runtime temp data or cleaned only if safe.

## Technical Approach

Mirror the temp owner fallback in both create and load paths: when `active_ui_session_key(state)` is empty, `load_subagents()` should inspect the `current` temp owner directory just like `create_subagent()` writes to it. Add regression coverage in `scripts/check_policy_gates.py`.

## Decision

Context: Real TUI smoke created `tmp-tui-smoke-806172291529` under `/home/vimalinx/Programs/GenericAgent/temp/ga-tui-subagents/current/...`, then `/agent ask TUI-Smoke ...` and `/agent ask tmp-tui-smoke-806172291529 ...` both failed with `找不到子 agent`.

Decision: Treat `current` as the canonical fallback temp owner whenever the active UI session key is empty.

Consequences: The empty-session startup case remains usable, while explicit session-owner isolation is unchanged for normal keyed sessions.

## Out of Scope

- No redesign of subagent naming or fuzzy matching.
- No persistent subagent migration.
- No changes to OMP runtime behavior.
- No broad TUI UI redesign.

## Technical Notes

- Relevant code: `subagent_home_dirs_for_session()`, `create_subagent()`, `load_subagents()`, `resolve_subagent()` in `src/ga_tui/app.py`.
- Existing creation path already uses `owner = active_ui_session_key(state) or "current"`.
- Existing load path only scans temp subagents when `active_ui_session_key(state)` is truthy, which misses the `current` fallback.

## Verification Log

- `python3 -m py_compile src/ga_tui/app.py scripts/check_policy_gates.py`
- `python3 scripts/check_policy_gates.py`
- `python3 -m compileall -q src scripts`
- `git diff --check`
- `ga-tui-check --root /home/vimalinx/Programs/GenericAgent`
- Real TUI smoke: created `TUI-Smoke2` as `tmp-tui-smoke2-350688346161` under `temp/ga-tui-subagents/current/...`, then `/agent ask tmp-tui-smoke2-350688346161 请只回答：TUI子agent成功` started the subagent and returned `TUI子agent成功`.
