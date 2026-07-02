# Workflow Design Research Notes

## Question

How should Shuheng introduce user/plugin workflows without weakening the current governed agent harness model?

## Comparable Patterns

- LangGraph-style graph workflows are useful as a long-term reference for explicit state, step transitions, human interrupts, and checkpointed execution.
- Temporal-style workflow/activity separation is the right reliability model for long-running execution: deterministic orchestration and side-effecting activities must be separated.
- OpenAI Agents SDK handoffs/guardrails are useful as a reference for explicit control transfer and validation boundaries, but guardrails do not replace programmatic approval gates.
- Airflow/Dagster/n8n are useful UI and vocabulary references for workflows, runs, nodes, schedules, and credentials, but their automation model should not be copied directly into Shuheng's agent governance layer.
- A2A/MCP compatibility should remain a future-facing constraint: workflow runs should eventually map cleanly to task/status/artifact concepts and tool/resource/prompt boundaries.

## Constraints From This Repo

- `src/ga_tui/plugins.py` already parses plugin-contributed workflow metadata as `PluginWorkflow` records with refs shaped like `plugin://<plugin-id>/workflows/<workflow-id>`.
- Current plugin contracts explicitly forbid executable plugin code, plugin-native tools, permission overrides, and global body-text injection.
- `src/ga_tui/app.py` already has harness panels for tasks, approvals, artifacts, recovery, evals, gateway, baseline, and plugins. A workflow panel should reuse the same `PanelItem` + `open_harness_panel(...)` pattern.
- Commands are centralized in `COMMANDS`, non-interactive command handling goes through `submit(...)`, and Secret Vault isolation uses `SECRET_BLOCKED_NORMAL_COMMANDS`.
- `scripts/check_policy_gates.py` is the executable boundary for app-level policy regressions.

## Recommended Approach

Start with declarative discovery and dry-run only.

- Add a pure workflow definition parser that reads manifest-declared local workflow files only.
- Keep workflow definitions data-only: JSON object or fenced/whole-file JSON is acceptable for MVP; no Python, shell, JavaScript, or template execution.
- Validate schema, ids, input names, step ids, step references, and known safe step types.
- Add `/workflows`, `/workflow info <ref>`, and `/workflow dry-run <ref>`.
- Add a read-only `/workflows` harness panel.
- Do not start subagents, create approvals, write ledgers, or dispatch tools from workflow dry-run.

## Deferred

- Actual workflow runner.
- Persistent workflow run ledger.
- Approval-resume semantics.
- Parallel/conditional graph execution.
- External A2A/MCP workflow publication.
- Remote marketplace or workflow install UI.
