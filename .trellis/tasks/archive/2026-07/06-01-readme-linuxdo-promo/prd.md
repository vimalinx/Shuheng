# Write README with linux.do promotion

## Goal

Rewrite the repository README so it clearly explains what Shuheng is, how to install and run it, how it integrates with the external GenericAgent core, what user-facing TUI capabilities exist, and includes a lightweight promotional mention of https://linux.do/.

## What I Already Know

* The user wants the README improved for this self-written TUI.
* The user explicitly asked to include promotion for https://linux.do/.
* The existing README is Chinese, so the new README should keep the same language style.
* `pyproject.toml` exposes `shuheng`, `shuheng-check`, `shuheng-install-core-shim`, and `shuheng-integration`.
* `src/shuheng/app.py` is a stable curses TUI that avoids Textual any-motion mouse behavior.
* The TUI integrates with an external GenericAgent checkout via `GENERICAGENT_ROOT` or auto-discovery.
* The TUI includes session management, model management, persistent subagents, task ledger views, approvals, artifacts, recovery/eval views, gateway/baseline views, memory inspection, and local encrypted Secret Vault commands.
* `docs/agent-harness-architecture.md` is the architecture baseline for harness-related work.

## Assumptions

* This task is documentation-only and should not change runtime behavior.
* The Linux.do promotion should be visible but not spammy.
* The README should avoid over-claiming features not present in the repo.

## Requirements

* Replace the minimal README with a complete, polished Chinese README.
* Preserve accurate install and launch instructions.
* Document the optional shim flow for launching from the GenericAgent core.
* Include practical command examples for common TUI operations.
* Include the https://linux.do/ link in a promotional/community section.
* Mention that the TUI is an external launcher around the GenericAgent core.
* Keep the documentation grounded in inspected source files.

## Acceptance Criteria

* [x] README explains project purpose in the first screen.
* [x] README includes install, run, doctor, and shim commands.
* [x] README includes a feature overview based on current source code.
* [x] README includes a visible Linux.do promotion link.
* [x] README keeps the current upstream-update guidance.
* [x] Markdown renders cleanly with consistent headings and code fences.
* [x] No code behavior changes are made.

## Definition of Done

* README updated.
* Markdown sanity checked.
* Git diff reviewed to ensure only intended documentation/task files changed.
* Architecture baseline impact considered: this documentation should clarify the governed orchestrator/subagent direction without changing implementation.

## Out of Scope

* Runtime code changes.
* Packaging changes.
* Screenshots or generated images.
* Publishing to a remote package registry.

## Technical Notes

* Inspected `README.md`, `pyproject.toml`, `src/shuheng/app.py`, `src/shuheng/integration.py`, and `docs/agent-harness-architecture.md`.
* The existing README already had uncommitted changes before this task; preserve useful content and expand it rather than reverting it.
