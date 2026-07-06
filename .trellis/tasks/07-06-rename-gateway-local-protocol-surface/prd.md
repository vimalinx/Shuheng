# Rename Gateway Semantics To Local Protocol Surface

## Goal

Remove active `gateway` naming from the current Shuheng runtime, docs, specs, tests, and release wording where it now means local protocol records or Agent Mail intake rather than a Web/HTTP gateway. The user-facing and developer-facing source of truth should be local TUI + OMP runtime, with local protocol registry records and local Agent Mail intake as internal concepts.

## What I Already Know

- The previous task removed active Web Console, HTTP gateway, mobile/remote endpoint, route handlers, and Web Console files.
- Some active code still uses names such as `local_protocol_registry.py`, `local_protocol_service_descriptor`, `local_protocol_baseline_evidence`, `local_protocol_public_registry`, `append_agent_mail_intake_message`, `gateway_message_*`, and constants/stores with `GATEWAY`.
- Because the user explicitly removed Web as an active concept, `gateway` should not remain as the normal active ontology for new work.
- This is a concept lifecycle cleanup. Do not keep `gateway` as a forbidden branch except in one isolated absence/quarantine check that prevents reintroducing Web/HTTP surfaces.
- Preserve local governance behavior: Orchestrator, task/progress ledgers, Agent Mail, local protocol-shaped records, approvals, artifacts, runtime evidence, workflows, plugins, scheduler, OMP runtime output/control.
- Do not touch `_knowledge_base/`.

## Requirements

- Rename active module/function/schema wording where practical from `gateway` to `local_protocol`, `local_protocol_registry`, or `agent_mail_intake`.
- Preserve behavior and stored schema compatibility where changing on-disk schema names would be risky. If a historical schema key must remain, isolate it as compatibility/local record shape and keep docs clear.
- Do not reintroduce Web Console, HTTP server, `/gateway`, `/a2a`, `/mcp`, mobile, remote, SSE, push, or daemon behavior.
- Update tests and policy gates so they assert the new active naming surface and still keep a centralized absence check for removed Web/HTTP runtime symbols.
- Update Trellis spec and active docs to describe the source of truth as local protocol records / Agent Mail intake, not an active gateway.
- Keep changes focused. Do not attempt broad storage migrations or delete historical archived Trellis tasks.

## Acceptance Criteria

- [x] Active docs/specs no longer describe the current local record system as a `gateway` except where referring to historical compatibility names or existing file paths that are intentionally not migrated.
- [x] Runtime code exposes new `local_protocol_*` and/or `agent_mail_intake_*` names for active call sites.
- [x] Old public/active `gateway_*` wrappers are removed or limited to clearly isolated compatibility aliases only when required by tests or stored data.
- [x] Policy gates assert the new local protocol naming and absence of Web/HTTP symbols.
- [x] Behavior remains unchanged for local Agent Mail intake, baseline reports, release readiness, runtime smoke, scheduler/workflow/plugin records, and OMP runtime output/control.
- [x] Quality gates pass: compile/Ruff/targeted tests/policy gates/release hygiene/runtime smoke/full pytest when feasible.
- [x] Final report compares the change against `docs/agent-harness-architecture.md`.

## Out Of Scope

- Reintroducing any Web/HTTP/mobile/remote surface.
- Migrating user data under `~/.shuheng`.
- Removing internal ledgers, approvals, artifacts, workflows, plugins, scheduler, OMP runtime, or local adapter metadata.
- Touching `_knowledge_base/`.

## Likely Files

- `src/shuheng/app.py`
- `src/shuheng/local_protocol_registry.py` or a renamed replacement module
- `src/shuheng/release_readiness.py`
- `src/shuheng/runtime.py`
- `scripts/check_policy_gates.py`
- `scripts/runtime_smoke.py`
- `tests/test_baseline_gateway_helpers.py`
- `README.md`, `README.en.md`, `docs/runtime-provider-control-plane.md`, `docs/app-py-decomposition-plan.md`, `.trellis/spec/backend/agent-control-protocol.md`
