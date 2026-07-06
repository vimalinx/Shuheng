# Extract AgentTask Explicit Policy Action Helper

## Requirement

Move deterministic explicit policy-action extraction for `[Shuheng AgentTask Envelope v2]` prompts from `src/shuheng/app.py` into `src/shuheng/control_protocol.py`.

The moved helper must preserve existing behavior for:

- top-level `policy_action`
- top-level `approval_required_for`
- nested `approval.policy_action`
- nested `approval.approval_required_for`
- nested `capability_contract.policy_action`
- string normalization via strip, lowercase, and hyphen-to-underscore conversion
- list handling by using the first non-empty item
- empty, invalid, missing, or non-envelope prompts returning `""`

## Scope

In scope:

- Add `explicit_policy_action_for_subagent_task(prompt)` to `control_protocol.py`.
- Re-export the helper from `app.py` as a compatibility alias.
- Remove the duplicate local function body from `app.py`.
- Expand `tests/test_control_protocol.py` for direct behavior and app alias parity.
- Expand `scripts/check_policy_gates.py` to enforce helper ownership and absence of duplicate app-local definition.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable boundary.

Out of scope:

- `infer_policy_action_for_subagent_task(...)`.
- `policy_gate_for_subagent_task(...)`.
- role policy, approval queueing, task ledger writes, runtime dispatch, artifacts, history, Secret Vault, Web Console, dashboard, rendering, commands, storage roots, or mutable `State`.
- Any behavior rewrite or storage migration.

## Acceptance Criteria

- `control_protocol.explicit_policy_action_for_subagent_task.__module__ == "shuheng.control_protocol"`.
- `app.explicit_policy_action_for_subagent_task is control_protocol.explicit_policy_action_for_subagent_task`.
- Existing call sites continue to use the same public name without behavior changes.
- Targeted control-protocol tests pass.
- Policy gates pass.
- Full release gates pass when feasible for the slice.

## Architecture Baseline

This moves the implementation closer to `docs/agent-harness-architecture.md` by keeping protocol interpretation in a restricted lower-level parser module while preserving `app.py` as the strong Orchestrator facade for policy decisions, approval gates, ledgers, artifacts, history, Secret Vault, Web Console, dashboard, runtime side effects, mutable state, and storage roots.
