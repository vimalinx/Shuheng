# Workflow Inputs and Condition V1 Design Note

## Design Question

How can Shuheng make workflows branch on user-provided context without adding an unsafe expression engine or hidden workflow executor?

## Current Repo Constraints

- `workflows.py` is a pure helper module. It may parse, validate, copy, and transform workflow data, but must not import app/runtime/UI/governance owners or write ledgers.
- `app.py` is the strong Orchestrator owner for command parsing, run ids, timestamps, registry refresh, and ledger appends.
- `Workflow Runner V0` currently completes only safe ledger-only steps and blocks on `condition`.
- Existing workflow inputs are parsed and displayed, but command paths pass `{}`.

## Options

### Option A: Free-form expression strings

- Example: `"expression": "inputs.ready == true"`.
- Pros: familiar, compact, easy for models to generate.
- Cons: quickly becomes a language runtime; invites unsafe eval, subtle parsing bugs, and future pressure to read artifacts/files/secrets.
- Decision: reject as executable v1. Preserve as a blocked placeholder only.

### Option B: Declarative JSON predicates (recommended)

- Example: `{"condition": {"ref": "inputs.ready", "equals": true}}`.
- Pros: deterministic, easy to validate, no code execution, compatible with pure helper ownership, extensible with finite operators.
- Cons: less expressive than a full expression language.
- Decision: use this for condition v1.

### Option C: Conditions remain blocked until a full workflow engine exists

- Pros: lowest risk.
- Cons: generated workflows cannot make even simple safe branches, which blocks the next useful automation step.
- Decision: too conservative for the current goal.

## MVP Contract

- Inputs resolve before run rows are appended.
- Required/default validation happens before ledger writes.
- Unknown input keys are rejected.
- Predicate reads only `inputs.<id>`.
- True predicate completes the condition step.
- False predicate marks the step `skipped` and stops progress.
- Unsupported predicate blocks with a visible reason.

## Why This Matches The Architecture Baseline

The condition evaluator remains deterministic and local to pure run-state transformation. It does not call tools, models, plugin code, files, Secret Vault, task ledgers, or approval queues. App remains the only writer, and generated workflows still execute through manifest-backed definitions plus append-only workflow rows.
