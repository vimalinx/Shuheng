# Complete Public Alpha Release Readiness Pass

## Goal

Move Shuheng from "locally works for the maintainer" toward a credible public alpha by executing the pasted release-readiness plan end to end: prove the full release gate, clean public repository presentation where safe, continue reducing the `app.py` monolith, and verify a fresh-user install path with documentation fixes.

## Requirements

* Keep the release positioning as public alpha / experimental local alpha. Do not claim production readiness, full protocol certification, or stable remote service semantics.
* Preserve security boundaries: Gateway/Web Console remain loopback-first without built-in auth; secrets, session logs, local paths, and model credentials must not enter source or artifacts.
* Run the full release gate from `release_readiness_report()` and preserve command evidence.
* Improve public repository presentation without deleting project-critical history. Trellis cleanup must be non-destructive, reviewable, and must not erase active task evidence blindly.
* Continue `app.py` decomposition with one low-risk helper slice that preserves the strong Orchestrator boundary and compatibility facade.
* Run a fresh-user install smoke from built artifacts or isolated source install, with no dependence on the maintainer's current `~/.shuheng` state.
* Patch README/onboarding docs for any gap discovered by the fresh-user smoke.

## Acceptance Criteria

* [x] Full release gate passes: Ruff, release hygiene, runtime smoke, policy gates, full pytest, compileall, build, wheel/sdist smoke, `shuheng-check`, and `git diff --check`.
* [x] Public repository presentation has an explicit decision for tracked Trellis task clutter, with either safe cleanup or documented rationale.
* [x] One additional `app.py` helper extraction is completed with tests and policy gates where appropriate.
* [x] Fresh-user install smoke proves a new environment can install/run documented entrypoints without relying on maintainer runtime state.
* [x] README/onboarding docs are updated if smoke reveals missing setup, state-root, cleanup, or troubleshooting guidance.
* [x] Final verification compares the implementation against `docs/agent-harness-architecture.md` and reports whether the work moved closer to the baseline.

## Definition of Done

* Relevant tests and policy gates pass after changes.
* Release artifacts pass leak and wheel/sdist smoke checks.
* Documentation reflects the actual public alpha behavior.
* No unrelated user changes are included.
* The task is committed in coherent work commits after verification.

## Technical Approach

1. Treat the pasted text as the source of requirements.
2. Use current repo state as authoritative evidence.
3. Prefer non-destructive cleanup over deleting Trellis state.
4. Choose one pure helper extraction from `app.py` rather than a broad refactor.
5. Re-run targeted checks after edits, then run release gates needed to prove public alpha readiness.

## Decision (ADR-lite)

**Context**: The pasted plan is broad and includes both verification and implementation work. Trying to finish every long-term gap, such as full A2A/MCP certification or complete `app.py` decomposition, would redefine public alpha into production readiness.

**Decision**: Scope this task to the public-alpha pass: green release gate, non-destructive repo presentation cleanup, one safe decomposition slice, fresh-user smoke, and docs updates.

**Consequences**: The project may still have known alpha gaps after this task, but those gaps must be honestly documented and must not block a public alpha release if the release gate and onboarding proof pass.

## Out of Scope

* Production readiness claims.
* Full A2A/MCP certification.
* Built-in Gateway/Web Console authentication.
* Complete `app.py` decomposition.
* Deleting or rewriting large Trellis history without an explicit preservation path.

## Technical Notes

* Full release gate completed on 2026-07-04:
  * `python3 -m ruff check ...` passed.
  * `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_release_hygiene.py` passed.
  * `PYTHONDONTWRITEBYTECODE=1 python3 scripts/runtime_smoke.py` passed.
  * `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py` passed.
  * `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passed with 561 tests.
  * `python3 -m compileall -q src scripts` passed.
  * `python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist` built `shuheng-0.1.0.tar.gz` and `shuheng-0.1.0-py3-none-any.whl`.
  * `PYTHONDONTWRITEBYTECODE=1 python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist` passed for wheel and sdist.
  * `shuheng-check` passed.
  * `git diff --check` passed.
* Current dirty state before implementation: only untracked `uv.lock` plus this task's new Trellis files.
* Current `app.py` size observed before this task: about 27,629 lines.
* Current Trellis presentation issue: no current task initially, but 99 active task directories were reported by Trellis context.
* Public repository presentation decision: keep tracked `.trellis` task/spec/workflow metadata as development provenance, document that it is not runtime state, keep runtime/cache/worktree/private state ignored, and keep `.trellis` excluded from sdist/wheel artifacts.
* Helper extraction completed: moved pure display helpers `rel_age(...)` and `human_tokens(...)` from `src/ga_tui/app.py` into `src/ga_tui/text_utils.py`; `app.py` keeps compatibility aliases and remains responsible for orchestration/state.
* Fresh-user smoke completed from built wheel in an isolated venv with clean `HOME`/`SHUHENG_HOME` and a fake GenericAgent root:
  * `shuheng --help` passed without importing the heavy TUI/root-dependent app path.
  * `python -m ga_tui --help` passed through the lightweight CLI.
  * `shuheng-check` reported `Status: OK` after the fake root satisfied the documented core interface.
* README/onboarding docs now tell fresh users to run `shuheng --help` first and clarify that TUI launch, Gateway, and `shuheng-check` require a valid GenericAgent root.
* Final release gate re-run on 2026-07-04 after edits:
  * `python3 -m ruff check ...` passed.
  * `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_release_hygiene.py` passed.
  * `PYTHONDONTWRITEBYTECODE=1 python3 scripts/runtime_smoke.py` passed.
  * `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py` passed.
  * `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passed with 565 tests.
  * `python3 -m compileall -q src scripts` passed.
  * `python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist` built `shuheng-0.1.0.tar.gz` and `shuheng-0.1.0-py3-none-any.whl`.
  * `PYTHONDONTWRITEBYTECODE=1 python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist` passed for wheel and sdist.
  * `shuheng-check` passed against `/home/vimalinx/Programs/GenericAgent`.
  * `git diff --check` passed.
* Architecture baseline comparison: this work moves Shuheng closer to `docs/agent-harness-architecture.md` because public alpha docs and PR templates require explicit release posture, approval/gateway wording, provenance/audit awareness, and architecture-baseline comparison; the helper extraction reduces `app.py` without weakening the strong Orchestrator boundary; the lightweight CLI improves onboarding without adding side effects. It does not solve remaining alpha gaps such as full `app.py` decomposition, built-in remote auth, external A2A/MCP conformance, or stronger eval/citation correctness.
