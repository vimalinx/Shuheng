# Extract Agent Control Result Format Helper

## Objective

Move the deterministic agent-control result line formatter out of `src/shuheng/app.py` and into `src/shuheng/control_protocol.py`, preserving current visible result strings and keeping `app.py` as the Orchestrator owner for control execution and mutable state.

## Scope

- Move `format_agent_control_result(action, target, result)` into `control_protocol.py`.
- Keep the same public name available from `app.py` as a compatibility alias.
- Preserve current output:
  - default action label is `control`;
  - non-empty targets other than `current`, `now`, and `selected` are appended to the action label;
  - result text is truncated with `truncate_cells(..., 260)`;
  - returned lines keep the `- <label>: <result>` shape.
- Add/extend tests for direct helper behavior and app alias parity.
- Extend policy gates so the helper has one source of truth in `control_protocol.py`.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the formatter boundary.

## Non-Goals

- Do not move `apply_tui_controls_from_text(...)`.
- Do not move `record_control_result(...)` or its nested state mutation.
- Do not move `apply_dashboard_control(...)`, `apply_schedule_control(...)`, `apply_task_control(...)`, `apply_subagent_control(...)`, or session operation execution.
- Do not change control parsing, shuheng-control schema handling, continuation behavior, system-message persistence, `State.last_error`, dirty marking, ledgers, approvals, artifacts, history, Secret Vault, Web Console, dashboard, rendering, commands, or storage roots.

## Behavior To Preserve

- `format_agent_control_result("agent_create", "Worker", "ok")` returns a line containing `agent_create Worker`.
- Targets `current`, `now`, and `selected` are not appended to the action label.
- Blank actions fall back to `control`.
- Long result text is cell-truncated to the existing 260-cell limit before formatting.
- `apply_tui_controls_from_text(...)` still records the same visible `Agent 控制结果：` lines through the app compatibility alias.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/control_protocol.py tests/test_control_protocol.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/control_protocol.py tests/test_control_protocol.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_control_protocol.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- When feasible for the slice, run full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel/sdist smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline

This change should move the system closer to `docs/agent-harness-architecture.md` by placing protocol result-string interpretation in the restricted protocol module while keeping the strong Orchestrator facade responsible for state mutation, task/progress ledgers, human approval gates, artifacts, history, runtime dispatch, and storage roots.
