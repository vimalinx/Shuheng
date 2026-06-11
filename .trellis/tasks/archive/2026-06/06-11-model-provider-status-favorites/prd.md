# Color provider statuses and add favorites group

## Goal

Improve the `/model` manager provider rail so users can quickly distinguish configured, unconfigured, and configured-but-currently-failing providers, and expose frequently used models as a first-class category parallel to provider categories.

## Requirements

* Keep the provider selector as a vertical rail.
* Add a `常用` category that appears alongside provider categories when recent/frequent model records exist.
* `常用` must list the configured entries whose display names are present in the recent model list, preserving recent order.
* Provider rail color semantics:
  * Blue for categories with configured models and no known failing health result.
  * Grey for categories with no configured models.
  * Yellow for categories with at least one configured model whose latest in-panel health/test result is failing.
* The active category should remain visually selected while preserving the underlying status color where possible.
* Do not automatically run network health checks merely to color the provider rail; colors reflect current configuration plus health results already produced by `t` or `v`.
* Keep existing navigation and actions unchanged: Tab/left/right switch categories, up/down move through visible model rows, `u` jumps recent models, `t` tests selected model, and `v` batch-validates all models.

## Acceptance Criteria

* [ ] `/model` renders `常用` as a peer category when recent configured models exist.
* [ ] Selecting `常用` shows only recent configured models in recent order.
* [ ] Empty common providers render grey.
* [ ] Configured providers render blue when no failing-only health state is known.
* [ ] Providers with configured models and any known failure render yellow after test/batch validation failure.
* [ ] Existing provider grouping and hidden `/llm`/`/models` alias behavior remains intact.
* [ ] Policy gate regression covers the new category and status colors.
* [ ] Project syntax, compile, policy, integration doctor, `ga-tui-check`, and whitespace checks pass.

## Definition of Done

* Tests added or updated for the provider rail behavior.
* Lint/type/syntax checks pass.
* Command surface spec updated if the visible `/model` contract changes.
* Rollback is simple: revert the UI/helper/test/spec commit.

## Technical Approach

Use existing data sources instead of adding persistence:

* Configured providers already come from `model_entry_categories(entries)` and `model_entry_indices_for_category(...)`.
* Recent/frequent models already come from `load_recent_model_names(entries)` and are passed into `draw_model_manager(...)`.
* Per-model health already lives in the in-memory `health` dictionary keyed by `model_health_key(entry)`.

Add small helper functions for model-manager categories so `常用` can be treated as a virtual category without changing the underlying provider identity logic.

## Decision (ADR-lite)

**Context**: The provider rail currently knows configured count and per-model health is available only after the user runs tests. The user wants status colors and a common/frequent model category.

**Decision**: Keep color semantics local to the model manager and derived from loaded entries, recent names, and current `health` results. Add `常用` as a virtual rail category rather than a provider template.

**Consequences**: No extra persistence or network calls are introduced. Yellow only appears after a failing test/batch validation is known in the current panel session, which keeps the UI fast and avoids surprising network traffic.

## Out of Scope

* Persisting provider health across TUI restarts.
* Automatic background health checking when opening `/model`.
* Changing the model configuration file shape.
* New keybindings or a separate favorites editor.

## Technical Notes

* Primary implementation target: `src/ga_tui/app.py`.
* Regression target: `scripts/check_policy_gates.py`.
* Command contract spec: `.trellis/spec/backend/agent-control-protocol.md`.
* Existing vertical rail requirement is already in `.trellis/spec/backend/agent-control-protocol.md`.
