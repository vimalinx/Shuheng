# Extract Control Continuation Helpers

## Objective

Move deterministic control-result continuation helpers out of `src/ga_tui/app.py` and into `src/ga_tui/control_protocol.py`, preserving current behavior and keeping `app.py` as the Orchestrator owner for mutable state and runtime side effects.

## Scope

- Move pure continuation action/state constants into `control_protocol.py`.
- Move pure continuation result signature calculation into `control_protocol.py`.
- Move pure continuation metadata discovery into `control_protocol.py`.
- Move pure explicit-continuation predicate into `control_protocol.py`.
- Move pure continuation-needed predicate into `control_protocol.py`.
- Move pure control-continuation prompt formatting into `control_protocol.py`.
- Keep compatibility aliases in `app.py` for the moved public names.

## Non-Goals

- Do not move `maybe_queue_orchestrator_control_continuation(...)`.
- Do not move `maybe_queue_orchestrator_plan_continuation(...)`.
- Do not move `apply_tui_controls_from_text(...)` or `apply_subagent_control(...)`.
- Do not move `State`, `add_system(...)`, `start_main_agent_task(...)`, auto-continuation counters, task ledgers, approvals, artifacts, history, Secret Vault behavior, Web Console, dashboard, rendering, commands, or storage roots.
- Do not change `ga-control.v2` parsing semantics, action mapping, or subagent lifecycle/reuse behavior.

## Behavior To Preserve

- Continuation is only considered when structured continuation metadata is present on the executed control or its original envelope.
- Accepted structured metadata includes truthy `continue_after`, `next_action_required`, `requires_continuation`, workflow/orchestrator state values in the existing continuation state set, and non-empty `next_action`.
- Visible prose must never trigger continuation.
- `subagent_ask`, `subagent_run`, `subagent_input`, `agent_ask`, and `agent_run` controls must not trigger the fallback continuation path.
- Continuation only applies to the current continuation action set.
- The prompt block text must keep the current `[GA TUI Control Result Continuation]` wrapper, control results, optional visible text, and instruction not to repeat successful controls.

## Verification

- Add or extend `tests/test_control_protocol.py` to cover direct helper behavior and `app.py` compatibility aliases.
- Extend `scripts/check_policy_gates.py` to assert ownership, behavior, and no duplicate app-local definitions.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the extracted continuation helper boundary.
- Run targeted compile, targeted Ruff, targeted tests, policy gates, full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel/sdist smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline

This change should move the system closer to `docs/agent-harness-architecture.md` by keeping protocol interpretation in a restricted protocol module while preserving the strong Orchestrator facade for state mutation, ledgers, approvals, artifacts, history, runtime dispatch, and human approval gates.
