# Extract Rendering Visible Reply Helpers

## Requirement

Move pure visible-reply text cleanup helpers from `src/shuheng/app.py` into the lower-level `src/shuheng/rendering.py` module while preserving executable behavior and public compatibility imports from `shuheng.app`.

## Scope

This slice owns only deterministic, curses-free assistant visible-reply cleanup:

- Move `TOOL_CALL_BLOCK_RE`, `TOOL_RESULT_FENCE_RE`, and `FINAL_RESPONSE_INFO_RE` into `rendering.py`.
- Move `strip_tool_output_blocks(text)`, `strip_standalone_dot_lines(text)`, and `visible_reply_text(body, hide_detail_fences=False)` into `rendering.py`.
- Keep `src/shuheng/app.py` compatibility aliases for every moved regex/helper.
- Preserve default `visible_reply_text(...)` behavior: hide `tool_use`, tool headers, and final-response info, but leave detail/tool-result fences unless `hide_detail_fences=True`.
- Preserve hide-detail behavior: remove tool call blocks, `tool_use` blocks, tool result fences, tool headers, and final-response info.
- Preserve standalone dot-line stripping and triple-newline collapse.
- Add direct rendering tests and app alias parity tests.
- Expand policy gates to assert ownership, behavior, compatibility aliases, and no reverse dependency into app/curses/state/runtime/command/Web/dashboard/input owners.
- Update `.trellis/spec/backend/agent-control-protocol.md` to record the visible-reply cleanup boundary.

## Non-Goals

- Do not move `latest_visible_reply_text(...)`.
- Do not move `render_assistant_text(...)`.
- Do not move `process_tools(...)`, `process_has_tool_noise(...)`, JSON-ish tool parsing, interaction parsing, ask-user handling, process grouping/folding, message block rendering, mutable `State`, curses drawing, Web Console, dashboard, runtime dispatch, storage roots, commands, input handlers, or task ledgers.
- Do not change transcript/history ownership or subagent/session storage semantics.
- Do not rename or remove public `app.py` symbols while downstream tests still import them.

## Architecture Direction

This should move the implementation closer to `docs/agent-harness-architecture.md`: deterministic render-text cleanup becomes a restricted lower-level helper boundary, while `app.py` remains the strong Orchestrator/composition facade for mutable UI state, rendering orchestration, runtime side effects, ledgers, approvals, artifacts, history, and external memory.

## Verification

- Targeted `py_compile` for touched files.
- Targeted Ruff for touched files.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_rendering.py -q -p no:cacheprovider`.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_rendering.py tests/test_cell_utils.py -q -p no:cacheprovider`.
- Full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.
