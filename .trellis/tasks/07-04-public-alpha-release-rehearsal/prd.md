# Public Alpha Release Rehearsal

## Goal

Run a real local release rehearsal for Shuheng `0.1.0` so the project has a
repeatable public-alpha release candidate path: release notes, artifacts,
checksums, fresh-install smoke evidence, and clear publish boundaries.

## What I Already Know

* `pyproject.toml` currently declares package version `0.1.0`.
* `CHANGELOG.md` already has a `0.1.0 - Experimental Local Alpha` section.
* The previous public-alpha readiness pass already proved the project can pass
  full gates and fresh-user wheel install smoke.
* Current working tree has only unrelated untracked `uv.lock`.
* The current task should not delete Trellis history, publish to PyPI, push
  tags, or claim production readiness.

## Requirements

* Preserve release posture as experimental local alpha.
* Keep `0.1.0` as the package version for this rehearsal unless current code
  evidence proves a version mismatch.
* Update release-facing notes so `CHANGELOG.md` and release docs reflect the
  rehearsed public-alpha candidate.
* Build sdist and wheel artifacts from current HEAD.
* Generate SHA256 checksums for release artifacts.
* Run the full release gate: Ruff, release hygiene, runtime smoke, policy gates,
  full pytest, compileall, build, wheel/sdist smoke, `shuheng-check`, and
  `git diff --check`.
* Run an isolated fresh-user install smoke from the built wheel with clean
  `HOME` and `SHUHENG_HOME`.
* Produce a GitHub Release draft body for the candidate.
* Do not publish externally, create tags, push commits, or upload artifacts.

## Acceptance Criteria

* [x] `CHANGELOG.md` contains a dated public-alpha `0.1.0` entry or equivalent
  release-candidate clarification.
* [x] A release rehearsal document records artifact filenames, SHA256 sums,
  verification commands, fresh-install smoke result, known gaps, and release
  draft text.
* [x] Full release gate passes on current HEAD.
* [x] Wheel/sdist artifact leak scan passes.
* [x] Isolated fresh-user wheel install proves `shuheng --help`,
  `python -m ga_tui --help`, and `shuheng-check`.
* [x] `docs/agent-harness-architecture.md` comparison is recorded because this
  touches release/orchestration posture.
* [x] No unrelated `uv.lock` change is included.

## Definition of Done

* Release-facing docs match the actual local rehearsal.
* All checks pass after docs are updated.
* Artifacts and checksums are generated under `/tmp` or documented as local
  rehearsal output, not committed binaries.
* Changes are committed in coherent work commits.
* Trellis task is archived after work commits.

## Technical Approach

1. Treat `0.1.0` as the candidate version because it is already the package
   version and changelog heading.
2. Add a release rehearsal document rather than committing artifacts.
3. Update changelog wording/date if needed.
4. Build `/tmp/shuheng-dist`, compute checksums, run artifact and fresh-install
   smoke.
5. Record GitHub Release draft text and remaining alpha gaps.

## Decision (ADR-lite)

**Context**: A release rehearsal should prove the publish path without causing
external side effects.

**Decision**: Use `0.1.0` as the local candidate, generate local artifacts and
checksums, document the GitHub Release body, and explicitly avoid tag creation,
PyPI/TestPyPI publishing, or remote upload in this task.

**Consequences**: The repository becomes ready for a manual public-alpha release
step, while external publication remains a separate explicit decision.

## Out of Scope

* PyPI or TestPyPI upload.
* GitHub tag creation or push.
* GitHub Release creation through API.
* Production-readiness or protocol-certification claims.
* More `app.py` decomposition.

## Technical Notes

* Release commands are documented in `docs/public-alpha-readiness.md`,
  `README.md`, `README.en.md`, `.github/PULL_REQUEST_TEMPLATE.md`, and CI.
* Release artifact boundaries and leak scans are implemented in
  `scripts/wheel_smoke.py` and `scripts/check_release_hygiene.py`.
* Rehearsal evidence is recorded in `release-rehearsal.md`; it stays in the
  Trellis task ledger and is not part of Python release artifacts.
