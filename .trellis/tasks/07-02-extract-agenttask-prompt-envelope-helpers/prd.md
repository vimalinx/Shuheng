# Extract AgentTask Prompt Envelope Helpers

## Objective

Move deterministic parsing of `[GA TUI AgentTask Envelope v2]` prompt blocks out of `src/ga_tui/app.py` and into `src/ga_tui/control_protocol.py`, preserving current policy-gate inputs while keeping policy decisions and approval side effects in the Orchestrator facade.

## Scope

- Move `agenttask_payload_from_prompt(prompt)` into `control_protocol.py`.
- Move `policy_relevant_subagent_prompt_text(prompt)` into `control_protocol.py`.
- Keep both public names available from `app.py` as compatibility aliases.
- Preserve current behavior:
  - missing envelope markers return `{}` for payload and original prompt for policy text;
  - invalid or non-object JSON returns `{}` for payload and original prompt for policy text;
  - `work_order.objective` wins over top-level `objective`;
  - empty envelope objective falls back to the original prompt.
- Add/extend tests for direct helper behavior and app alias parity.
- Extend policy gates so both helpers have one source of truth in `control_protocol.py`.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the prompt-envelope parser boundary.

## Non-Goals

- Do not move `explicit_policy_action_for_subagent_task(...)`.
- Do not move `infer_policy_action_for_subagent_task(...)`.
- Do not move `policy_gate_for_subagent_task(...)`, `evaluate_policy_action(...)`, approval queueing, role-policy helpers, task schema construction, task ledgers, runtime dispatch, mutable `State`, Web Console, dashboard, rendering, commands, Secret Vault behavior, history, or storage roots.
- Do not change AgentTask envelope format or prompt generation.

## Behavior To Preserve

- Policy gates continue to evaluate the objective inside the generated AgentTask envelope rather than scanning the full envelope JSON when the objective exists.
- Explicit policy action lookup continues to use the parsed payload through the app compatibility alias.
- Invalid envelopes are ignored safely without raising.
- `control_protocol.py` remains lower-level: no `ga_tui.app`, curses, mutable `State`, runtime agent classes, ledgers, approvals, Web Console, dashboard, rendering, commands, or storage-root globals.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/control_protocol.py tests/test_control_protocol.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/control_protocol.py tests/test_control_protocol.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_control_protocol.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- When feasible for the slice, run full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel/sdist smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline

This change should move the system closer to `docs/agent-harness-architecture.md` by putting AgentTask protocol envelope parsing in the restricted protocol module while leaving policy decisions, human approval gates, ledgers, runtime dispatch, artifacts, history, and mutable state in the strong Orchestrator facade.
