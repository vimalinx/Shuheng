# Extract AgentTask Inferred Policy Action Helper

## Requirement

Continue Goal 7 by moving the deterministic policy-action inference rules for subagent tasks out of `src/shuheng/app.py` and into `src/shuheng/control_protocol.py`, while keeping app-owned runtime state, role objects, approval decisions, queueing, and ledger side effects in `app.py`.

The lower-level protocol helper should preserve the current inference order:

- honor explicit structured AgentTask policy action fields first
- infer from `policy_relevant_subagent_prompt_text(prompt)` after NFKC normalization and lowercasing
- match the existing risky-action keyword groups without changing tokens or precedence
- infer `long_running_privilege_escalation` only for ops-role prompts containing the existing privileged-operation tokens
- return `repo_write` for roles whose write policy is `single_writer`
- return `read_only` otherwise

## Scope

In scope:

- Add a pure helper to `control_protocol.py` that accepts prompt text plus normalized role/write-policy facts.
- Keep `infer_policy_action_for_subagent_task(sub, prompt)` in `app.py` as a compatibility wrapper that extracts facts from `SubAgentRuntime`.
- Preserve every existing call site and public function name.
- Expand `tests/test_control_protocol.py` to cover direct inference behavior and app wrapper parity.
- Expand `scripts/check_policy_gates.py` to enforce protocol ownership for the pure inference helper and to prevent duplicated keyword logic from returning to `app.py`.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the source-of-truth boundary.

Out of scope:

- `policy_gate_for_subagent_task(...)`.
- `evaluate_policy_action(...)`, `queue_policy_approval(...)`, approval metadata, task ledger writes, Secret Vault gating, runtime dispatch, dashboard, rendering, command completion, history, storage roots, or mutable `State`.
- Any behavior rewrite, token rename, risky-action policy change, storage migration, or compatibility migration.

## Acceptance Criteria

- Direct control-protocol tests prove the pure helper returns the same actions for explicit policy action, secret access, spending, deploy, external send, publish, delete file, permission policy, high-risk batch, ops privileged operations, single-writer roles, and read-only fallback.
- `app.infer_policy_action_for_subagent_task(...)` remains callable and delegates to the protocol helper after deriving normalized role/write-policy facts.
- Existing policy gate call sites still use `infer_policy_action_for_subagent_task(...)` with no behavior change.
- Policy gates reject a duplicate app-local policy keyword table and verify the protocol helper boundary.
- Full Goal 7 verification passes before commit when feasible: targeted compile/Ruff/tests, policy gates, full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline

This should move the implementation closer to `docs/agent-harness-architecture.md`: protocol interpretation becomes a restricted, testable helper in `control_protocol.py`, while `app.py` remains the strong Orchestrator facade responsible for runtime state, approval gates, ledgers, artifact provenance, recovery, and side effects.
