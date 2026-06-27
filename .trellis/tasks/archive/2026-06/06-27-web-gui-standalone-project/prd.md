# Extract Web GUI Into Standalone Project

## Goal

Move the existing web GUI into its own project so it is clearly separated from the current Shuheng/GenericAgent TUI codebase while preserving the ability to run and develop it independently.

## What I already know

* User request: "把网页端 gui 单独拿出来弄个项目，和现在的项目区分开。"
* The target is the existing web-side GUI, not a new UI redesign.
* The separation should make the web GUI distinguishable from the current project.
* The current web GUI is not a separate frontend package. It is embedded in `src/ga_tui/app.py` as `web_console_html()`.
* The GUI talks to the current gateway through `GET /gui/snapshot` and `POST /gui/action`.
* The gateway also exposes `/gui`, `/dashboard`, and `/console`, currently all served from the embedded `web_console_html()`.
* `src/ga_tui/app.py` already had uncommitted Web Console changes before this task. These changes are treated as the current source to extract, not as code to discard.

## Assumptions (temporary)

* Create the standalone GUI as a sibling project at `/home/vimalinx/Programs/Shuheng-Web-GUI`, so it is visibly separate from `/home/vimalinx/Programs/Shuheng`.
* Keep the Shuheng backend/gateway in the current project. The standalone GUI remains a client of that gateway.
* Use a dependency-light static GUI project with a small Python dev server/proxy instead of introducing a Node/Vite stack unless the existing GUI requires it.
* Preserve the current working-tree version of the GUI during extraction.

## Open Questions

* None for the MVP. The sibling-project location can be renamed later if needed.

## Requirements (evolving)

* Identify the current web GUI entry points, assets, and build/dev dependencies.
* Create a standalone web GUI project separated from the current TUI/backend project at `/home/vimalinx/Programs/Shuheng-Web-GUI`.
* Preserve the existing web GUI behavior as much as possible during extraction.
* Make the standalone GUI run locally without needing to start the curses/TUI UI.
* Allow the standalone GUI dev server to proxy `/gui/snapshot` and `/gui/action` to an existing Shuheng gateway.
* Remove the large embedded GUI HTML/JS/CSS from the Shuheng backend path or replace it with a loader so the GUI source of truth lives in the standalone project.
* Keep unrelated dirty files out of this task's code changes.

## Acceptance Criteria (evolving)

* [x] `/home/vimalinx/Programs/Shuheng-Web-GUI` has its own README, project metadata, runnable dev server, and static GUI source.
* [x] The standalone GUI serves the extracted current Web Console UI.
* [x] The standalone GUI can proxy existing `/gui/snapshot` and `/gui/action` calls to a configurable Shuheng gateway API base.
* [x] The Shuheng gateway no longer owns the full embedded web GUI source; it serves the external GUI if available or a clear fallback if not.
* [x] Static validation and a local HTTP smoke test pass for the standalone GUI.
* [x] Existing Shuheng Python tests still pass or any failures are explained.
* [x] The architecture baseline impact is reviewed against `docs/agent-harness-architecture.md`.

## Definition of Done (team quality bar)

* Tests added/updated where appropriate.
* Lint / typecheck / build smoke green where available.
* Docs/notes updated if behavior or project layout changes.
* Rollback considered if the extraction creates integration risk.

## Out of Scope (explicit)

* Redesigning the web GUI visual language.
* Rewriting backend/TUI orchestration behavior unless needed to keep the extracted GUI runnable.

## Technical Notes

* Task directory: `.trellis/tasks/06-27-web-gui-standalone-project`.
* Current project metadata: `pyproject.toml` declares Python package `shuheng` and console script `shuheng = ga_tui.app:main`.
* Current gateway entry points: `python -m ga_tui.app --serve-gateway`, `--gateway-daemon`, `--gateway-host`, `--gateway-port`.
* Current embedded UI source: `src/ga_tui/app.py` around `web_console_html()`.
* Backend API helpers such as `web_console_snapshot()` and `web_console_apply_action()` stay in Shuheng because the standalone GUI still depends on them.

## Technical Approach

Extract the current `web_console_html()` output into a new sibling project. The new project will serve static `public/index.html` and provide a stdlib-only Python dev server that proxies `/gui/*` requests to `SHUHENG_API_BASE` (default `http://127.0.0.1:8765`). Then replace Shuheng's embedded GUI function with an external-file loader that prefers `SHUHENG_WEB_GUI_INDEX`, then the sibling project path, then a small fallback page.

## Decision (ADR-lite)

**Context**: The current GUI is a large embedded HTML/CSS/JS string inside the backend/TUI file, which makes it hard to evolve independently.

**Decision**: Make `/home/vimalinx/Programs/Shuheng-Web-GUI` the GUI source of truth and keep Shuheng responsible for runtime state, governance actions, and gateway APIs.

**Consequences**: The GUI and backend become easier to work on separately. Local gateway `/gui` depends on either the sibling GUI project or an explicit `SHUHENG_WEB_GUI_INDEX`; if neither exists, it returns a fallback page instead of embedding the old full UI.

## Verification

* `PYTHONPATH=src python3 -m unittest discover -s tests` in `/home/vimalinx/Programs/Shuheng-Web-GUI`: passed.
* `python3 -m compileall -q src scripts` in `/home/vimalinx/Programs/Shuheng-Web-GUI`: passed.
* `python3 -m compileall -q src scripts` in `/home/vimalinx/Programs/Shuheng`: passed.
* `pytest -q` in `/home/vimalinx/Programs/Shuheng`: `171 passed`.
* `python3 scripts/check_policy_gates.py` in `/home/vimalinx/Programs/Shuheng`: passed.
* `git diff --check` in `/home/vimalinx/Programs/Shuheng`: passed after the spec update.
* HTTP smoke started an in-process Shuheng gateway and standalone GUI proxy, then verified `/`, `/gui/snapshot`, and invalid `/gui/action` schema handling.

## Architecture Baseline Impact

This moves the system closer to `docs/agent-harness-architecture.md`: the browser UI is now a separate client surface while Shuheng remains the strong Orchestrator/gateway owner for task ledgers, approvals, artifacts, schedules, A2A/MCP, and governed `/gui/action` mutations. No new browser-owned mutation path, scheduler, memory writer, approval bypass, or multi-writer channel was introduced.

Remaining gaps are unchanged from the baseline: the Web GUI still depends on the current gateway API shape and does not add independent recovery/checkpointing, trace visualization, or long-term memory hydration beyond what the Shuheng backend already exposes.
