# Implement Open-Source Release Readiness

## Goal

Make the Shuheng repository credible for an open-source alpha release by fixing the concrete gaps found in the release-readiness audit: governance files, CI, package metadata, release hygiene, private-file guardrails, brand consistency, plugin docs, gateway/security wording, and reproducible verification.

## What I Already Know

* The user asked to implement all findings from the open-source readiness review.
* Current automated behavior is healthy enough for alpha: pytest, policy gate, `git diff --check`, wheel build, isolated wheel install, and `shuheng-check` were verified in the review turn.
* Root-level open-source governance files are missing: `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and CI.
* `pyproject.toml` has minimal package metadata but lacks license, authors, classifiers, project URLs, keywords, and release-oriented optional dependencies.
* The repository has untracked private/local files: `config/mcporter.json`, `references/taste-ledger.md`, and two unrelated homework-market research docs under `docs/`.
* The main README already labels Shuheng as `experimental local alpha`, and `release_readiness.py` exposes known gaps for gateway auth, protocol certification, heuristic eval, scheduler ownership, and monolith risk.
* The OMP plugin still presents itself as GA-TUI with old local path examples, while the public product name is now Shuheng.
* `src/ga_tui/app.py` remains very large; full decomposition is high risk and should be incremental, but a release task can still move safe pure release/hygiene checks out of ad-hoc process.

## Requirements

* Add standard open-source project governance files for license, security reporting, contributing workflow, code of conduct, and changelog/release notes.
* Add GitHub Actions CI that runs the same meaningful release checks contributors can reproduce locally: tests, policy gates, compile check, release hygiene, and package build.
* Add a release hygiene script that catches missing governance files, accidental private paths/files, secret-like literals, package metadata gaps, and inconsistent public alpha claims.
* Protect known local/private paths from accidental commits without deleting user files.
* Improve `pyproject.toml` metadata and package inclusion so the sdist/wheel match the intended public surface.
* Update README/README.en and release readiness docs to explain release verification, security posture, and alpha boundaries clearly.
* Rename or clarify user-facing OMP plugin docs/package wording from GA-TUI to Shuheng while preserving internal `ga_tui_*` compatibility tool names.
* Keep protocol-level compatibility identifiers such as `ga_tui_query`, `GA_TUI_*`, and `src/ga_tui` unless a dedicated migration is designed.
* Establish a configured Python quality baseline. Ruff may be introduced with pragmatic legacy ignores rather than blocking the release on unrelated historical style debt.
* Ensure all changes move the system closer to the architecture baseline: strong Orchestrator, bounded workers, explicit ledgers, artifact refs, approval gates, auditable communication, and clear compatibility claims.

## Acceptance Criteria

* [x] Root includes `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `CHANGELOG.md`.
* [x] `.github/workflows/ci.yml` runs pytest, `scripts/check_policy_gates.py`, `scripts/check_release_hygiene.py`, compileall, and package build.
* [x] `scripts/check_release_hygiene.py` passes locally and is documented.
* [x] `.gitignore` prevents accidental commit of known private local files without deleting them.
* [x] `pyproject.toml` has license/authors/classifiers/keywords/project URLs and package build support.
* [x] sdist includes intended public docs/integrations and excludes ignored private/local files.
* [x] OMP plugin public docs/package wording use Shuheng as product name while compatibility tool identifiers remain unchanged.
* [x] README and README.en include release checklist and security/alpha posture.
* [x] Ruff is configured and `ruff check` passes for the selected baseline.
* [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passes.
* [x] `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py` passes.
* [x] `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_release_hygiene.py` passes.
* [x] `python3 -m compileall -q src scripts` passes.
* [x] `python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist` passes.
* [x] Isolated wheel install can run `shuheng-check`.
* [x] `git diff --check` passes.

## Definition Of Done

* Release-blocking repository hygiene gaps are fixed or guarded.
* Existing runtime behavior remains stable.
* Documentation matches defensible alpha claims.
* Verification commands above pass.
* No unrelated user/private files are deleted.
* Architecture baseline impact is reported.

## Technical Approach

1. Add governance docs and release metadata.
2. Add release hygiene automation and CI.
3. Update packaging configuration and package inclusion.
4. Clean public docs and plugin wording while preserving compatibility identifiers.
5. Configure a pragmatic lint baseline and run format/checks.
6. Verify through tests, policy gate, release hygiene, compile, build, isolated install, and integration doctor.

## Decision (ADR-lite)

**Context**: The codebase is functional but not ready for public alpha because repo-level governance, package metadata, CI, hygiene guardrails, and public-facing naming are incomplete.

**Decision**: Treat this as a release-hardening task, not a feature rewrite. Implement concrete release gates and docs now; leave full `app.py` decomposition and certified A2A/MCP conformance as explicit future work unless they can be safely covered by compatibility wording and hygiene checks.

**Consequences**: The repository becomes publishable as an experimental alpha with honest limitations. Some technical debt remains visible, but future contributors get clear CI and guardrails instead of implicit local conventions.

## Out Of Scope

* Full decomposition of the 28k-line curses/runtime composition module.
* Renaming internal compatibility identifiers (`src/ga_tui`, `GA_TUI_*`, `ga_tui_query`, `ga-tui.*` schemas).
* Complete A2A or MCP protocol certification with third-party clients.
* Adding production-grade remote gateway authentication beyond clear local-only/no-auth posture and remote-bind guardrails.
* Publishing to GitHub/PyPI or changing the remote URL.
* Deleting user-private research/config files from disk.

## Technical Notes

* Architecture baseline: `docs/agent-harness-architecture.md`.
* Runtime provider contract: `docs/runtime-provider-control-plane.md`.
* Brand entrypoint contract: `.trellis/spec/backend/agent-control-protocol.md`.
* Release-readiness helpers: `src/ga_tui/release_readiness.py`.
* Current public docs: `README.md`, `README.en.md`.
* Plugin surface: `integrations/omp-ga-tui-plugin`.

## Completion Notes

Implemented on 2026-06-28:

* Added MIT license, security policy, contribution guide, code of conduct, changelog, MANIFEST, and GitHub Actions CI.
* Added `scripts/check_release_hygiene.py` and wired release hygiene expectations into `scripts/check_policy_gates.py`.
* Updated `pyproject.toml` with release metadata, development dependencies, Ruff baseline, and package URLs.
* Updated `.gitignore` to protect local/private config, references, and unrelated research docs without deleting those files.
* Updated README/README.en with release checks and open-source/security boundaries.
* Updated release-readiness metadata so repository hygiene gaps are conditional and verification commands include Ruff, release hygiene, and package build.
* Updated OMP plugin public wording to Shuheng while preserving `ga_tui_*` compatibility tool names and legacy env compatibility.
* Added `.trellis/spec/backend/agent-control-protocol.md` release-hygiene contract.

Verification passed:

* `python3 -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py`
* `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_release_hygiene.py`
* `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
* `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` with 171 tests
* `python3 -m compileall -q src scripts`
* `python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist`
* isolated wheel install plus `shuheng-check --root /home/vimalinx/Programs/GenericAgent`
* `PYTHONPATH=src python3 -m ga_tui.integration doctor --root /home/vimalinx/Programs/GenericAgent`
* `git diff --check`

Architecture baseline impact: the change moves Shuheng closer to the baseline by making public release claims auditable, preserving a strong local Orchestrator/control-plane boundary, preventing private local state from entering artifacts, and keeping A2A/MCP/eval/gateway surfaces clearly labeled as compatibility/experimental surfaces until stronger evidence exists.
