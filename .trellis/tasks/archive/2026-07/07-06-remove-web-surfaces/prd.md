# Remove Active Web Surfaces

## Goal

Remove Web Console, HTTP gateway, mobile/remote web routes, and web-facing A2A/MCP exposure from Shuheng's active product surface. The active target becomes local TUI plus OMP runtime output/control. Internal governance concepts such as orchestrator ownership, agent mail, ledgers, approvals, artifacts, scheduler, plugins, workflows, and local runtime provider metadata remain in scope and must not be deleted just because older docs/routes exposed them through HTTP.

## What I Already Know

- The user explicitly said not to care about the web path and that deleting web entirely is acceptable.
- This is a concept lifecycle transition: Web/Web Console/HTTP gateway/mobile/remote exposure is removed from the active Shuheng ontology instead of being kept as a forbidden branch.
- `src/shuheng/app.py` currently exposes `--serve-gateway`, `--gateway-daemon`, `/gui`, `/gateway`, `/a2a`, `/mcp`, SSE, push subscriptions, and a TUI `/gateway` panel.
- `src/shuheng/web_console.py` and `src/shuheng/web_console_static.py` are Web Console helper modules.
- `scripts/runtime_smoke.py`, README, release-readiness docs, and tests currently treat loopback HTTP gateway/Web Console/A2A/MCP compatibility as experimental surfaces.
- `docs/agent-harness-architecture.md` still remains the harness baseline. Removing unauthenticated HTTP/Web exposure should move Shuheng closer to the strong local orchestrator/governed-shell target, as long as internal ledgers and artifact references remain intact.

## Requirements

- Remove active CLI entrypoints that start or manage HTTP/Web gateway services.
- Remove active HTTP request handler/server code and Web Console static/page/action code from runtime.
- Remove user-facing TUI `/gateway` command/panel as a web/protocol exposure surface.
- Update release posture, README, and Trellis specs to state the active surface is local TUI + OMP runtime, with no built-in Web Console/HTTP gateway/mobile/remote endpoint.
- Update tests and policy/release gates so they assert the new positive invariant instead of validating old Web gateway compatibility.
- Preserve internal local governance capabilities: task/progress ledgers, agent mail as local records, approvals, artifacts, runtime evidence, workflows, plugins, scheduler, and OMP runtime provider helpers.
- Do not edit or clean `_knowledge_base/`.
- Do not rewrite archival Trellis history or unrelated historical docs unless they are active release/spec contracts.

## Acceptance Criteria

- [x] `shuheng --help` no longer advertises gateway/Web HTTP serving or daemon flags.
- [x] TUI top-level commands no longer include `/gateway`.
- [x] Runtime no longer imports or exposes Web Console helper modules.
- [x] No active route handler/server remains for `/gui`, `/gateway`, `/a2a`, `/mcp`, mobile, or remote web surfaces.
- [x] Release/readiness docs no longer present Web Console/HTTP gateway/A2A/MCP as active experimental surfaces.
- [x] Tests are updated or removed to match local TUI + OMP-only active surface.
- [x] Quality gates pass: targeted compile/Ruff/tests, policy gates, release hygiene, runtime smoke, full pytest when feasible.
- [x] Final report compares the change against `docs/agent-harness-architecture.md`.

## Out of Scope

- Removing internal ledgers, approvals, artifacts, memory, workflows, plugins, scheduler, or local OMP runtime output/control.
- Building replacement web/mobile/remote clients.
- Cleaning unrelated historical Trellis task directories.
- Touching `_knowledge_base/`.

## Technical Notes

- Likely runtime files: `src/shuheng/app.py`, `src/shuheng/web_console.py`, `src/shuheng/web_console_static.py`, `src/shuheng/gateway_registry.py`, `src/shuheng/release_readiness.py`.
- Likely test/gate files: `tests/test_cli.py`, `tests/test_web_console.py`, `tests/test_web_console_static.py`, `tests/test_baseline_gateway_helpers.py`, `tests/test_release_readiness.py`, `tests/test_release_hygiene.py`, `scripts/runtime_smoke.py`, `scripts/check_release_hygiene.py`, `scripts/wheel_smoke.py`.
- Active docs/specs: `README.md`, `docs/runtime-provider-control-plane.md`, `docs/public-alpha-readiness.md`, `.trellis/spec/backend/agent-control-protocol.md`.
