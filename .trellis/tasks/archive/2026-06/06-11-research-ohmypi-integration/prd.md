# Research ohmypi integration

## Goal

Download and compare Oh My Pi and GenericAgent source code, then propose how GenericAgent-TUI could integrate Oh My Pi without immediately changing runtime code.

## Requirements

* Identify the correct upstream Oh My Pi repository and clone a shallow copy for inspection.
* Locate/download GenericAgent source for comparison; prefer the local sibling checkout if it is already the active runtime source, and clone from its remote when available.
* Compare architecture boundaries:
  * process/CLI entrypoints
  * model/provider routing
  * tool execution and edit model
  * subagent/task orchestration
  * session/history/memory persistence
  * protocol surfaces such as ACP/MCP/A2A-like bridges
* Compare those findings against the current GenericAgent-TUI runtime provider architecture.
* Produce a concrete integration recommendation with phased options and risks.

## Acceptance Criteria

* [x] External sources are downloaded or inspected from local/remote checkouts.
* [x] Research notes are persisted under this task's `research/` directory.
* [x] The final answer names the most viable integration path and why.
* [x] The answer distinguishes direct evidence from implementation inference.
* [x] No TUI runtime code is changed in this research task.

## Definition of Done

* Research artifact created.
* Local checkout paths and source URLs recorded.
* Integration options and recommended MVP recorded.
* User receives a concise summary and next implementation step.

## Out of Scope

* Implementing Oh My Pi support in this turn.
* Vendoring third-party source into GenericAgent-TUI.
* Changing model provider configs, subagent behavior, or TUI command UX.

## Technical Notes

* Oh My Pi search result points to `https://github.com/can1357/oh-my-pi`.
* Current TUI repo is `/home/vimalinx/Programs/GenericAgent-TUI`.
* Expected GenericAgent sibling repo is `/home/vimalinx/Programs/GenericAgent`.
