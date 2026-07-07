# PRD: Dollar Skill As The Only Shuheng Skill Entry

## Problem

Shuheng already maps prompt-level `$skill` invocations to OMP's native `/skill:<name>` command at the runtime boundary. The remaining risk is conceptual leakage: if a user types `/skill:<name> ...` directly in Shuheng, the input could be treated as an ordinary prompt or could be forwarded to OMP without Shuheng owning the command namespace.

In Shuheng, `/` is reserved for Shuheng program commands. Prompt-level skills must be invoked through `$<skill> ...` or `$+<skill> ...` only. OMP's `/skill:<name>` string is an internal runtime protocol detail.

## Goals

- Keep `$<skill> ...` and `$+<skill> ...` working as the user-facing transient skill command surface.
- Prevent direct user input beginning with `/skill:` from reaching OMP as a skill command.
- Return a clear Shuheng system message that points users to `$<skill> ...`.
- Preserve `/agent skill ...` for persistent per-agent skill assignment.
- Keep OMP-native `/skill:<name>` generation only inside the runtime prompt conversion boundary.
- Lock the boundary with unit tests, runtime dispatch tests, policy gates, and backend spec text.

## Non-Goals

- Do not modify OMP source or OMP configuration.
- Do not change persistent per-agent skill management.
- Do not inject Shuheng-side transient skill bodies into prompts.
- Do not expose `/skill:` in user-facing docs or command completion as a Shuheng command.

## Acceptance Criteria

- `/skill:foo do work` produces a Shuheng system guidance message and does not start or forward a user task.
- `$foo do work` still dispatches to an OMP runtime prompt beginning with `/skill:foo ` when the target runtime supports OMP-native skills.
- `$+foo do work` remains supported.
- `/agent skill ...` behavior remains unchanged.
- Context packs keep transient skill refs as metadata only and do not include skill body text.
- `scripts/check_policy_gates.py` asserts the user/runtime boundary.
- Targeted and full quality gates pass.
