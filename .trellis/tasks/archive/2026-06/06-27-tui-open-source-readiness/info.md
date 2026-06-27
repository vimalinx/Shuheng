# Implementation Plan

## User Scope Decision

The user selected `全量重构` when asked to choose the release-readiness scope. Interpret this as: do real modular extraction and fix patch-like implementation surfaces, but keep changes safe enough to verify in this dirty repo.

## Work Breakdown

1. Release readiness metadata/report
   - Add a small dedicated module for release status, surfaces, known gaps, and verification command metadata.
   - Integrate the report into gateway/baseline surfaces and docs.

2. Baseline evidence hardening
   - Introduce evidence-level semantics: `structural`, `runtime`, `e2e`, and `unknown`.
   - Make baseline items expose these levels so callable/path/schema checks do not look equivalent to end-to-end verification.

3. Eval honesty
   - Extract heuristic eval scoring into a pure helper.
   - Mark scores as heuristic and expose what was inferred from artifact/text presence.

4. Gateway and protocol release posture
   - Make local-only/no-auth posture explicit in service metadata.
   - Ensure A2A/MCP descriptions say compatibility surface unless there is real compliance evidence.
   - Keep remote push gating explicit.

5. Scheduler ownership clarity
   - Make registry/docs clear that scheduler ticks are runtime-owned by TUI/gateway, not an external always-on service unless started.

6. Tests and docs
   - Add policy gate tests for release-readiness report, baseline evidence levels, heuristic eval labels, gateway security posture, protocol wording, and scheduler ownership wording.
   - Update README / README.en where needed so public claims match implementation.

## Constraints

* Do not revert existing unrelated dirty files.
* Preserve all current test behavior.
* Do not move large stateful UI/runtime code unless there is a direct verification path.
* Keep new modules pure and testable when possible.

## Verification

* `python3 -m pytest -q -p no:cacheprovider`
* `python3 scripts/check_policy_gates.py`
* `python3 -m compileall -q src scripts`
* `git diff --check`
