# Make OhMyPi the default runtime core

## Goal

Make Shuheng treat OhMyPi / OMP as the normal core runtime and GenericAgent as an optional legacy compatibility provider. Normal Shuheng import, help, startup, release checks, and OMP use must not require a GenericAgent checkout.

## What I Already Know

* The user explicitly corrected the architecture: OhMyPi is the core runtime; GenericAgent is not the root of Shuheng.
* `src/shuheng/app.py` must stay importable without an optional GenericAgent legacy-provider checkout.
* `src/shuheng/integration.py` must treat OhMyPi / OMP and Shuheng package health as core checks, with GenericAgent checks isolated to optional legacy-provider diagnostics.
* `RuntimeRegistry` defaults to `ohmypi`; provider selection must not depend on optional legacy-provider import success.
* Active docs, release hygiene, doctor output, and task guidance must describe Shuheng as the owned control plane, not as an external layer over GenericAgent.

## Requirements

* Shuheng imports and CLI help must work without a GenericAgent checkout.
* The default runtime provider must be `ohmypi`.
* The OMP provider must register independently of GenericAgent.
* The GenericAgent provider must be optional: available only when a valid GenericAgent legacy-provider checkout and imports are present, or explicitly used for legacy compatibility.
* `shuheng-check` and `python3 -m shuheng.integration doctor` must distinguish Shuheng core / OhMyPi provider checks from optional GenericAgent legacy-provider checks.
* Missing GenericAgent must not be a global failure for normal Shuheng operation.
* GenericAgent launcher shim installation may still require a valid GenericAgent legacy-provider checkout.
* Documentation, executable policy gates, and Trellis spec must state the new source of truth.

## Acceptance Criteria

* [x] `python3 -c "import shuheng.app"` succeeds when GenericAgent auto-discovery is disabled or absent.
* [x] `python3 -m shuheng --help` succeeds without requiring GenericAgent.
* [x] `shuheng --help` succeeds without requiring GenericAgent.
* [x] Runtime registry reports `ohmypi` as the default provider.
* [x] Missing GenericAgent is reported as an unavailable optional legacy provider, not as a failed Shuheng core.
* [x] GenericAgent provider still works when a valid legacy-provider checkout is configured.
* [x] Policy gates prevent reintroducing module-import hard dependency on GenericAgent.
* [x] README / docs / spec no longer describe GenericAgent as Shuheng's root runtime.

## Definition of Done

* Tests and policy gates updated for OMP-first runtime ownership.
* Lint, compile, targeted tests, release hygiene, runtime smoke, policy gates, full pytest, build, wheel smoke, and `shuheng-check` pass where available.
* `docs/agent-harness-architecture.md` is compared before final report because this touches orchestration and runtime provider behavior.
* The existing untracked `uv.lock` remains untouched.

## Technical Approach

Remove GenericAgent from Shuheng's import-time critical path. Keep GenericAgent-specific code in the provider and shim boundary, but make discovery/import optional and lazy enough that OMP-first Shuheng can boot alone. Where app code needs GenericAgent history helpers, provide Shuheng-owned fallback implementations and use GenericAgent's `continue_cmd` helpers only when available.

## Decision (ADR-lite)

Context: GenericAgent was historical bootstrap infrastructure, but OhMyPi is the product runtime core. Treating GenericAgent as root makes startup slow, fragile, and conceptually wrong.

Decision: Shuheng owns the control plane and defaults to OMP. GenericAgent remains an optional legacy compatibility provider and shim target.

Consequences: Legacy compatibility code may remain only inside isolated provider, shim, migration, or quarantine boundaries, but active docs, checks, and provider metadata must not imply that GenericAgent is required for normal Shuheng.

## Out of Scope

* Removing the GenericAgent provider entirely.
* Rewriting the full memory architecture or every legacy string that accurately refers to GenericAgent compatibility behavior.
* Changing OMP RPC protocol behavior beyond startup/provider ownership.
* Adding auth, network gateway exposure, or production A2A/MCP certification claims.

## Technical Notes

* Key files: `src/shuheng/app.py`, `src/shuheng/integration.py`, `src/shuheng/runtime.py`, `src/shuheng/genericagent_provider.py`, `src/shuheng/ohmypi_provider.py`.
* Regression gates: `scripts/check_policy_gates.py`, release hygiene tests, CLI/import tests, runtime dispatch tests.
* Docs/spec candidates: `README.md`, `README.en.md`, `docs/public-alpha-readiness.md`, `docs/runtime-provider-control-plane.md`, `.trellis/spec/backend/agent-control-protocol.md`.

## Completion Notes

* Shuheng now registers OMP as the independent default runtime core and registers the GenericAgent provider only when the optional legacy checkout/imports are available.
* Missing GenericAgent is a healthy OMP-core state: `shuheng-check` and `python3 -m shuheng.integration doctor` report the legacy provider as optional rather than failing Shuheng core checks.
* `app.py` uses Shuheng-owned history/session-name fallback helpers when GenericAgent frontends are unavailable.
* Active user-facing docs, prompts, doctor output, release readiness text, and policy gates now state that GenericAgent is an optional legacy provider/shim target, not Shuheng's root runtime.
* Architecture baseline comparison: this moves closer to `docs/agent-harness-architecture.md` by strengthening a single Shuheng Orchestrator/control plane, making runtime providers bounded adapters, and preserving policy/ledger/memory ownership in Shuheng.
* Remaining gaps: `app.py` is still a large composition module, retired naming is limited to quarantined historical cleanup and executable absence gates, and A2A/MCP remain compatibility surfaces rather than certified external conformance.
