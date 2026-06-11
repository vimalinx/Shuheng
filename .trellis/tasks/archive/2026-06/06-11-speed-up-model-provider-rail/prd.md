# Speed up model provider rail

## Goal

Fix the `/model` manager lag caused by repeated provider/category scans during drawing and navigation, while preserving the vertical provider rail, `常用` category, and provider status colors.

## Requirements

* Preserve the current `/model` behavior:
  * Provider labels remain a vertical rail.
  * `常用` remains a peer category when recent configured models exist.
  * Configured categories remain blue, empty categories grey, and categories with known failed health yellow.
  * Tab/left/right category switching and up/down model selection remain unchanged.
* Avoid repeated full scans of `entries` during a single draw.
* Avoid recomputing category indices once per visible provider row.
* Precompute a category view/index from `entries`, `recent_names`, and `health`, then make draw/navigation read from that structure.
* Do not add background network probes, persistence changes, or model config shape changes.

## Acceptance Criteria

* [ ] Current local model config count (`84`) no longer makes `/model` key navigation visibly sticky.
* [ ] A local benchmark for 100 draws over the current config improves from the diagnosed baseline of about `12.78s` total / `127.77ms` per draw to low-millisecond-per-draw territory.
* [ ] Stress benchmark for 1000 synthetic entries no longer takes about `1s` per draw.
* [ ] Policy gate tests still assert `常用`, vertical rail rendering, and configured/empty/warning status behavior.
* [ ] Regression tests prevent `draw_model_manager(...)` from recalculating per-entry provider categories when a precomputed category index is supplied.
* [ ] Syntax, compile, policy gates, integration doctor, `ga-tui-check`, and whitespace checks pass.

## Definition of Done

* Code path changed in `src/ga_tui/app.py`.
* Regression updated in `scripts/check_policy_gates.py`.
* Model command surface spec updated if the helper contract changes.
* Performance benchmark results recorded in final summary.

## Technical Approach

Add a lightweight model-manager category index that contains:

* Ordered category labels.
* `category -> entry indices`.
* `selected entry index -> preferred active category`.
* `category -> status` derived from configured count and health.

Use this index in `draw_model_manager(...)` and `open_model_manager(...)` instead of calling `model_manager_entry_indices_for_category(...)` and `model_manager_category_attr(...)` repeatedly inside loops.

## Decision (ADR-lite)

**Context**: The previous feature added `常用` and rail colors, but the implementation recomputed category membership for each category row and status lookup. With 84 configured models this measured at about 128ms per draw locally.

**Decision**: Keep the existing public helper behavior but add a precomputed internal view/index for the hot rendering and navigation path.

**Consequences**: The UI remains behaviorally identical, but the hot path becomes linear per update instead of repeated linear scans per visible row.

## Out of Scope

* Changing model provider detection semantics.
* Persisting category index data.
* Changing recent model storage.
* Background health checking or automatic provider validation.

## Technical Notes

* Main file: `src/ga_tui/app.py`.
* Regression file: `scripts/check_policy_gates.py`.
* Spec file: `.trellis/spec/backend/agent-control-protocol.md`.
* Diagnosis evidence: current config has `84` model entries; 100 current-config draws measured `12.7766s` total before the fix.
