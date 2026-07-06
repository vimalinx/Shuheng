# Extract Rendering Process Display Summary Helper

## Objective

Continue Goal 7 by moving one more deterministic process-rendering decision out of `src/shuheng/app.py` and into `src/shuheng/rendering.py`, while preserving all visible behavior and keeping `app.py` as the compatibility facade.

## Scope

- Add a pure helper in `src/shuheng/rendering.py` that chooses whether a process summary/preview value is displayable.
- The helper must accept explicit summary and preview strings only.
- Preserve the existing behavior used in `render_assistant_text(...)`: prefer a non-empty summary, fall back to preview, and suppress empty values and the in-progress sentinel `执行中`.
- Add an `app.py` compatibility alias for the helper.
- Replace the duplicated local `summary = process_summary_text(body) or process_preview(body)` plus `summary != "执行中"` branches in `render_assistant_text(...)` with the new helper.
- Add tests and policy gates for direct helper behavior, app alias parity, and app wrapper behavior.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the durable boundary.

## Out Of Scope

- Do not move `render_assistant_text(...)`.
- Do not move `append_process_turn(...)`.
- Do not move `process_tools(...)`, JSON-ish parsing, tool-result parsing, process-turn traversal, interaction extraction, message cache rendering, `RenderLine` allocation, curses attrs, mutable `State`, Web Console, dashboard, runtime dispatch, history, Secret Vault, ledgers, approvals, or artifact behavior.
- Do not change storage semantics, public console scripts, or release posture.

## Compatibility Requirements

- `app.process_display_summary_text` must be the same callable as `rendering.process_display_summary_text`.
- Existing `render_assistant_text(...)` visible output must remain stable for no-final-text process turns with explicit summaries, preview fallbacks, and `执行中` suppression.
- The new rendering helper must not import `shuheng.app`, curses, runtime classes, mutable state, Web Console, dashboard, input handlers, or command handlers.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full project quality gate from Goal 7 before commit.

## Architecture Baseline

The change should move the implementation closer to `docs/agent-harness-architecture.md` by narrowing `app.py` to orchestration and compatibility injection while keeping deterministic rendering policy inside the policy-gated rendering module. The strong Orchestrator facade must still own mutation, ledgers, approvals, artifacts, history, Secret Vault, Web Console, dashboard, runtime side effects, mutable UI state, and curses rendering.
