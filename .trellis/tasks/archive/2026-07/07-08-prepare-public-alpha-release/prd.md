# Prepare Shuheng Public Alpha Release

## Goal

Close the remaining public alpha release blockers so Shuheng can be published as an experimental local alpha without leaking local research files, overstating platform support, or leaving fresh-install instructions ambiguous.

## Requirements

* Treat `_knowledge_base/` as private/local research material that must not be tracked, packaged, or shown as an unignored release candidate.
* Add a fresh-machine installation guide covering Linux, WSL, macOS best-effort status, unsupported Windows native status, verification commands, state directories, and the shared agent gateway skill installer.
* Link the installation guide from both READMEs and keep the quick-start path short.
* Update public alpha readiness wording so release owners know the exact platform support claim and release checklist.
* Update the changelog for the current public alpha candidate.
* Extend release hygiene and distribution smoke contracts so the new install guide and private `_knowledge_base/` boundary cannot drift.
* Run the full release gate before finishing.

## Acceptance Criteria

* [x] `git status --short` no longer reports `_knowledge_base/` as an untracked release candidate.
* [x] `docs/install.md` exists and documents fresh install, verification, platform support, state migration, and local gateway skill setup.
* [x] README and README.en link to the install guide and retain concise quick-start commands.
* [x] `scripts/check_release_hygiene.py` requires `docs/install.md` and ignores/prunes `_knowledge_base/` as private local material.
* [x] `scripts/wheel_smoke.py` requires `docs/install.md` in the sdist and rejects `_knowledge_base/` if it appears.
* [x] `CHANGELOG.md` describes the current alpha release hardening work.
* [x] Release hygiene, policy gates, runtime smoke, dogfood stdio gateway, full tests, build, wheel smoke, `shuheng-check`, and `git diff --check` pass.

## Definition of Done

* Release-facing docs and executable release gates agree.
* No new production, remote, Web, HTTP, mobile, macOS, or Windows-native support is claimed.
* Changes are committed, the Trellis task is archived, and the journal records the work.

## Technical Approach

Make this a release-hardening/documentation slice rather than a product-surface expansion. The main changes should be docs and guardrails: `.gitignore`, `MANIFEST.in`, `scripts/check_release_hygiene.py`, `scripts/wheel_smoke.py`, README links, `docs/install.md`, `docs/public-alpha-readiness.md`, and changelog updates.

## Decision (ADR-lite)

**Context**: The repository is already capable of an experimental local alpha, but a fresh public clone still needs clearer platform claims and private-local file boundaries.

**Decision**: Publish the current posture as Linux-first experimental local alpha. Windows native remains unsupported; Windows users should use WSL2. macOS is best-effort/unverified until CI or real terminal smoke coverage exists. `_knowledge_base/` is private local material and is ignored/pruned.

**Consequences**: This avoids overstating support while giving users a reproducible fresh-machine path. Future tasks can add macOS/Windows support only after real CI and terminal behavior verification.

## Out of Scope

* Publishing the repository, creating a GitHub release, or pushing tags.
* Adding macOS or Windows native CI/support.
* Building installers, Homebrew formulae, PyPI release automation, or binary packages.
* Changing runtime architecture, Web/HTTP/mobile/remote surfaces, A2A/MCP certification, or provider behavior.

## Technical Notes

* Current package metadata declares Python `>=3.10` and `Operating System :: POSIX :: Linux`.
* Release posture remains `experimental local alpha`.
* Current release gates are listed in `docs/public-alpha-readiness.md` and `CONTRIBUTING.md`.
* `_knowledge_base/agent-harness-research-2026-07-05.md` is local private research material and must not become a release candidate.
