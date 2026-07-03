# Workflow Approval Bridge Design Note

## Question

How should workflow approval steps connect to Shuheng's existing approval ledger?

## Evidence

- Shuheng already has `agentapproval.v1` rows, `/approvals`, `/approve`, `/reject`, approval inbox mail, and policy approval paths.
- Workflow runner v0 currently records approval intent only inside `workflow_runs.jsonl`, so the user cannot approve it through the governed approval surface.
- The architecture baseline requires hard human approval gates and auditable communication before risky or delegated work proceeds.

## Decision

Use the existing approval system as the source of truth. A workflow approval step creates one `workflow_step_approval` row and records its id in the workflow run row. `/workflow continue` consults that approval row.

## Guardrails

- Do not create a second approval mechanism.
- Do not make `/approve` run workflow continuation as a hidden side effect.
- Do not dispatch subagents or run tools after approval in this slice; only runner-v0 safe steps continue.
- Use append-only workflow rows and append-only approval decision rows for auditability.
