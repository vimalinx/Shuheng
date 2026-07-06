# Document AgentTask Policy Action Boundary

## Goal

Harden the backend code-spec so future work does not accidentally move AgentTask policy-action parsing or inference back into `app.py`, weaken approval-gate source-of-truth behavior, or treat capability-prohibition text as an approval trigger.

## Requirements

- Update `.trellis/spec/backend/agent-control-protocol.md`.
- Add code-spec depth with concrete signatures, contracts, validation behavior, good/base/bad cases, tests required, and wrong-vs-correct examples.
- Cover the current Task 180-182 boundary:
  - `agenttask_payload_from_prompt(prompt)`.
  - `policy_relevant_subagent_prompt_text(prompt)`.
  - `explicit_policy_action_for_subagent_task(prompt)`.
  - `inferred_policy_action_for_subagent_task(prompt, *, role, write_policy)`.
  - `app.infer_policy_action_for_subagent_task(sub, prompt)` wrapper.
- Preserve the rule that app owns Orchestrator side effects: `SubAgentRuntime`, role template lookup, approval decisions, approval queues, ledgers, runtime dispatch, state mutation, artifacts, storage roots, and Secret Vault paths.

## Acceptance Criteria

- Spec explains exact ownership boundaries and forbidden patterns.
- Spec includes a test checklist that points future changes at `tests/test_control_protocol.py` and `scripts/check_policy_gates.py`.
- No code behavior changes.
- Markdown diff is clean.

## Out Of Scope

- Changing policy tokens or approval behavior.
- Moving `policy_gate_for_subagent_task(...)`.
- Adding new runtime behavior, tests, or migration code in this spec-only task.
