# Gateway external agent directory and inbox E2E

## Goal

Make Shuheng's local gateway useful to other agents as a narrow agent-discovery and message-delivery surface. External agents should be able to learn which Shuheng agents/roles exist and what they are for, then send a message into Shuheng's inbox. They should not receive broad Shuheng context, full permission matrices, project rules, workflow internals, memory paths, or governance implementation details by default.

## What I already know

* The user wants other agents to know what agents are inside Shuheng and what each agent is used for.
* The user explicitly corrected the previous direction: external agents do not need Shuheng context exposure.
* Existing gateway code exposes A2A agent cards and `/a2a/messages` delivery with `auto_dispatch:false`.
* Existing gateway code also exposes `/gateway/context`, `/gateway/permissions`, and MCP resources for context inspector and permission matrix.
* Internal TUI commands `/context` and `/permissions` are still useful for local operator inspection and should not be removed unless they are external exposure paths.
* Gateway message delivery already writes `kind:"gateway_message"` task rows, Agent Mail rows, and trace rows without auto-dispatch.
* Unknown gateway message targets are rejected rather than creating phantom agents.

## Requirements

* Expose an external agent directory that lists Shuheng-discoverable roles and visible subagents with human-readable purpose, role, status, delivery endpoint, input/output modes, and safety notes.
* Keep A2A agent cards available, but make their purpose clearer as the agent-facing discovery contract.
* Remove `/gateway/context` and `/gateway/permissions` from the external HTTP request/response descriptor and public external-agent path.
* Remove context-inspector and permission-matrix from externally advertised MCP resources.
* Keep context inspector and permission matrix as internal TUI/control-plane projections and durable files where needed for local governance and policy gates.
* Keep `/a2a/messages` as inbox-only delivery: write task ledger, Agent Mail, and trace; do not auto-run subagents, approve actions, execute workflows, call tools/models, or write memory.
* Add E2E/smoke coverage for the external flow: discover agent directory/cards, send message to a discovered agent/role, verify inbox/task/trace/query visibility, and verify unknown target rejection.
* Update specs/docs so future work does not re-expand the external discovery surface back into broad context/permission exposure.

## Acceptance Criteria

* [x] `/gateway` and service descriptors advertise agent discovery and `/a2a/messages`, not `/gateway/context` or `/gateway/permissions`.
* [x] A dedicated external agent directory payload exists and contains role/subagent purpose summaries without project context, memory paths, spec paths, workflow run internals, or full permission matrices.
* [x] `/a2a/agent-cards` still returns cards for role templates and visible subagents.
* [x] `POST /a2a/messages` to a discovered agent/role creates a `gateway_message` task, Agent Mail row, and trace row with `auto_dispatch:false`.
* [x] `POST /a2a/messages` to an unknown target returns a rejection and creates no phantom task.
* [x] `/bus` or equivalent inbox projection makes the received gateway message visible to the local operator.
* [x] Policy gates and runtime smoke cover the narrowed external surface.
* [x] Backend spec and runtime-provider docs describe external agent discovery as purpose/cards/inbox, not broad context or permission inspection.

## Definition of Done

* Targeted compile/Ruff/tests/policy gates pass.
* Full project pytest passes or any skipped/failing command is explicitly explained.
* Release hygiene, runtime smoke, build/wheel smoke, and `shuheng-check` pass where feasible.
* Active backend spec is updated with the narrowed gateway contract.
* Work is committed before task finish-work.

## Technical Approach

* Add a small external-facing agent directory schema such as `shuheng.agent_directory.v1` built from role templates and `gateway_visible_subagents(...)`.
* Keep directory entries intentionally low-context: id, display name, role, purpose, status, delivery endpoint, input/output modes, write-policy category, and safety note.
* Route HTTP discovery through `/gateway/agents` and/or include `agent_directory` in `/gateway`.
* Remove `/gateway/context` and `/gateway/permissions` from `GatewayRequestHandler` external routes or return them only through internal TUI paths, not through external gateway docs/descriptors.
* Remove context/permission MCP resources from `gateway_registry.mcp_resource_registry(...)` external resources.
* Preserve internal `context_inspector_snapshot(...)`, `permission_matrix(...)`, `/context`, `/permissions`, and gateway panel sections unless they cause external exposure.
* Extend `scripts/check_policy_gates.py` and `scripts/runtime_smoke.py` to validate the external-agent E2E path.

## Decision (ADR-lite)

Context: External agents need agent discovery and a delivery endpoint, but broad Shuheng context and full permission matrices expose too much implementation detail and are not necessary for agent-to-agent messaging.

Decision: External gateway discovery is agent-directory/card based. Context inspector and permission matrix remain internal operator/control-plane projections, not external agent discovery endpoints.

Consequences: The gateway is simpler and safer for interop. If future external agents need more detail, they should request scoped agent-card metadata or a specific governed query rather than receiving whole-system context by default.

## Out of Scope

* Production remote gateway auth.
* Full A2A/MCP certification claims.
* Automatic execution of gateway messages.
* Removing internal TUI `/context` or `/permissions` panels.
* Reworking workflow RunState beyond adding E2E coverage for gateway message visibility.
* Cleaning unrelated `_knowledge_base/` research files.

## Technical Notes

* Main implementation file: `src/shuheng/app.py`.
* Gateway helper file: `src/shuheng/gateway_registry.py`.
* Tests/gates: `scripts/check_policy_gates.py`, `scripts/runtime_smoke.py`, `tests/test_baseline_gateway_helpers.py`.
* Specs/docs: `.trellis/spec/backend/agent-control-protocol.md`, `docs/runtime-provider-control-plane.md`.
* Existing untracked `_knowledge_base/agent-harness-research-2026-07-05.md` is unrelated to this task and should stay out of the commit unless explicitly requested.

## Verification

* `python3 -m py_compile src/shuheng/app.py src/shuheng/gateway_registry.py scripts/check_policy_gates.py scripts/runtime_smoke.py tests/test_baseline_gateway_helpers.py`
* `python3 -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py`
* `PYTHONPATH=src pytest -q tests/test_baseline_gateway_helpers.py`
* `python3 scripts/check_policy_gates.py`
* `python3 scripts/runtime_smoke.py`
* `python3 -m compileall -q src scripts`
* `PYTHONPATH=.:src pytest -q`
* `python3 scripts/check_release_hygiene.py`
* `python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist-gateway-agents-*`
* `python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist-gateway-agents-*`
* `shuheng-check`
* `git diff --check`
