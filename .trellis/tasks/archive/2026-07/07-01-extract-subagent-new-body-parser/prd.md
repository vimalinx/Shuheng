# Extract Subagent New-Body Parser

## Goal

Move the deterministic `/agent new ...` body parser out of `src/shuheng/app.py`
and into the lower-level `src/shuheng/subagent_store.py` boundary, while keeping
`app.py` responsible for role-template policy, command handling, runtime state,
metadata writes, and subagent creation side effects.

## Requirements

- `subagent_store.py` must own a pure helper that parses the `/agent new` body into name, profile, role, persistence flag, and role note.
- The lower-level helper must not import or reference `shuheng.app`, `ROLE_TEMPLATES`, curses, `State`, `SubAgentRuntime`, runtime providers, Web Console, rendering, Secret Vault, or history transcript owners.
- Role recognition must be injected from `app.py` as a supported-role collection and role-normalization callable, so `ROLE_TEMPLATES` remains app-owned.
- `src/shuheng/app.py` must keep the public `parse_subagent_new_body(body)` compatibility function with the same signature and behavior.
- Existing behavior must be preserved for:
  - `--persistent`, `--persist`, `--long-term`, `--long_term`, `--permanent`, `--durable`
  - `--temp`, `--temporary`, `--ephemeral`
  - `persistent:`, `persist:`, `permanent:`, `durable:`, `long_term:`, `long-term:`, `长期:`, `持久:`, `永久:`
  - `temp:`, `temporary:`, `ephemeral:`, `临时:`, `暂时:`
  - `|` profile splitting
  - ASCII and full-width role separator forms `:` and `：`
  - `main_orchestrator` normalization through the app-owned role normalizer
- Tests and policy gates must cover direct helper behavior, app wrapper parity,
  app-owned role injection, and subagent-store boundary purity.

## Acceptance Criteria

- [ ] `src/shuheng/subagent_store.py` exposes the pure parser helper.
- [ ] `src/shuheng/app.py` no longer contains the parser implementation body and delegates through a compatibility wrapper.
- [ ] `tests/test_subagent_store.py` covers flags, prefixes, profile splitting, role recognition, unsupported role fallback, app wrapper parity, and `main_orchestrator` role-note preservation.
- [ ] `scripts/check_policy_gates.py` asserts the helper is owned by `subagent_store.py`, app wrapper parity holds, and `subagent_store.py` still has no forbidden dependencies.
- [ ] `.trellis/spec/backend/agent-control-protocol.md` records the parser boundary and the role-template injection invariant.
- [ ] Targeted tests, policy gates, full release gates, package build, wheel/sdist smoke, and `shuheng-check` pass.
- [ ] The change is compared against `docs/agent-harness-architecture.md` before completion.

## Definition of Done

- Tests added or updated for the new parser boundary.
- Lint, compile, policy gates, full pytest, release hygiene, runtime smoke, build,
  wheel smoke, and integration smoke pass.
- The app facade remains compatible for existing callers and tests.
- No storage root, transcript ownership, Secret Vault, role-template policy, or
  command side-effect behavior changes are bundled into this slice.

## Technical Approach

Add a pure parser helper in `subagent_store.py` with an explicit dependency
injection shape such as:

```python
parse_subagent_new_body(
    body,
    supported_roles=...,
    normalize_role=...,
)
```

The helper may call `clean_subagent_id(...)` because identity normalization is
already owned by `subagent_store.py`. It must treat role support and role-note
generation as injected policy. `app.parse_subagent_new_body(body)` will pass
`ROLE_TEMPLATES` keys and `subagent_role_request(...)`, preserving current
behavior without moving role-template policy into the store module.

## Decision (ADR-lite)

Context: The `/agent new` command parser is deterministic and currently lives in
the app monolith, but it consults app-owned role templates. Moving it directly
with `ROLE_TEMPLATES` would violate the lower-level store boundary.

Decision: Extract only the parsing algorithm and inject the supported role set
and role normalizer from `app.py`.

Consequences: The lower-level module gains a testable parser while app remains
the policy owner for role templates and reserved-role notes. This keeps the
decomposition aligned with the strong-Orchestrator architecture and avoids
turning `subagent_store.py` into a command or policy module.

## Out of Scope

- Moving `ROLE_TEMPLATES`, `normalized_role(...)`, `subagent_role_request(...)`,
  permission profiles, or role policy helpers out of `app.py`.
- Moving `handle_subagent_command(...)`, `create_subagent(...)`,
  `find_reusable_subagent(...)`, metadata writes, Secret subagent handling,
  direct-chat persistence, Web Console actions, rendering, command routing, or
  runtime dispatch.
- Changing the subagent/session/history invariant: normal non-secret
  conversations remain history-owned; subagent homes store profile, memory,
  runtime refs, and metadata refs.

## Technical Notes

- Current parser location: `src/shuheng/app.py::parse_subagent_new_body`.
- Target module: `src/shuheng/subagent_store.py`.
- Existing subagent-store boundary is documented in
  `.trellis/spec/backend/agent-control-protocol.md`.
- Architecture baseline: `docs/agent-harness-architecture.md`.
- Decomposition plan: `docs/app-py-decomposition-plan.md`.
