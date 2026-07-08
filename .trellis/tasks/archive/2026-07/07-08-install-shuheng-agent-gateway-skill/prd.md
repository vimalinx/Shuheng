# Install Shuheng Agent Gateway Skill

## Goal

Let Shuheng install its own shared agent-facing skill so other local AI agents can discover Shuheng's local stdio gateway, list available Shuheng agents, and send messages through the supported gateway contract.

## Requirements

* Add a classic CLI-discoverable installer surfaced by `shuheng -h`.
* The installer must be run by Shuheng itself, not by manually copying files from outside the package.
* Install/update a shared skill under `~/.agents/skills` by default so non-Codex agents can discover it.
* Support a test override for the shared skill root so tests never write into the user's real home directory.
* Generate a valid skill folder with `SKILL.md` and `agents/openai.yaml`.
* The skill must describe only the supported local stdio gateway contract: discover agents, send messages, and check task status.
* The skill must not expose Shuheng internal context, task ledgers, secrets, permission matrices, filesystem paths, or private runtime state.
* Installation must be offline, deterministic, and idempotent.

## Acceptance Criteria

* [x] `shuheng -h` shows the installer entrypoint.
* [x] The installer writes `SKILL.md` and `agents/openai.yaml` into a configurable shared skill root.
* [x] Re-running the installer updates the same deterministic files without duplicating state.
* [x] Generated skill metadata is valid and does not contain local absolute user paths.
* [x] The generated skill teaches use of `shuheng-agent-gateway` commands and JSONL stdio mode.
* [x] Tests cover CLI help, install output, generated files, and skill content boundaries.
* [x] Policy/release gates cover the new CLI and packaging contract.

## Definition of Done

* Tests added or updated for the CLI installer and generated skill.
* Lint, targeted tests, policy gates, full tests, build, wheel smoke, runtime smoke, and gateway dogfood pass.
* README/spec documentation updated where behavior changes.
* Task changes committed separately from Trellis archive/journal bookkeeping.

## Technical Approach

Add a small installer subcommand to the existing Shuheng CLI. Bundle the skill template inside the Python package and copy it to the shared skill root at runtime. Keep the installer deliberately narrow: no network access, no dynamic secrets, no runtime introspection beyond resolving the destination.

## Decision (ADR-lite)

**Context**: Other agents need a stable, discoverable way to learn how to call Shuheng without being handed internal implementation details.

**Decision**: Shuheng owns and installs a minimal shared skill through its CLI. The skill points external agents at the existing `shuheng-agent-gateway` CLI/stdio contract.

**Consequences**: This keeps Shuheng as the authority for its integration instructions and avoids duplicating gateway docs in each agent. The installer intentionally does not expose richer context-sharing, Web control, or remote operations.

## Out of Scope

* Web, HTTP, mobile, or remote gateway behavior.
* External access to Shuheng contexts, ledgers, approvals, memory, secrets, or filesystem internals.
* Custom per-agent installer UX beyond a shared skill folder.
* Network installation, marketplace publishing, or version negotiation.

## Technical Notes

* Shared multi-agent skill root for this workstation is `~/.agents/skills`.
* Existing local gateway executable is `shuheng-agent-gateway`.
* Project architecture baseline is `docs/agent-harness-architecture.md`.
* Active protocol spec is `.trellis/spec/backend/agent-control-protocol.md`.
