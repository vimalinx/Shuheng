# Agent dashboard home pages

## Goal

Add a first usable version of dashboard home pages for the main Shuheng Orchestrator and persistent, long-running Shuheng subagents. The page should make the main agent and every long-term role agent feel like a real workspace, while preserving the existing governed architecture: scheduler state stays in the TUI control plane, work is dispatched through `agenttask.v2`, and displayed data comes from shared ledgers, schedule runs, traces, approvals, and artifact references.

## What I Already Know

- The user agreed that normal scheduled work should not create a separate hidden session per agent.
- The user wants true long-running role agents to be able to have a dedicated program panel for relevant content.
- The user clarified that every persistent agent should have a main page.
- The user clarified that the main agent / Orchestrator also needs this kind of page.
- The user wants the agent itself to decide page layout and which relevant content to show, including capability/function description, recent scheduled work, current status narrative, and todos.
- The user wants startup to trigger the default display.
- During an active TUI process, the default displayed view should be the last opened interface.
- The last-opened interface does not need to persist across program restarts.
- The desired boundary is declaration over execution: a persistent agent may describe what its dashboard should show, but the TUI owns rendering, data access, permissions, and audit behavior.
- The architecture baseline requires a strong Orchestrator, shared task/progress ledgers, artifact references, single-writer enforcement, human approval gates, auditable communication, and external memory.
- Existing scheduler code stores definitions and run audit rows centrally in `src/ga_tui/scheduler.py`; scheduled agent work maps into `agenttask.v2`.
- Existing TUI panel infrastructure uses `PanelItem` plus `open_harness_panel(...)` in `src/ga_tui/app.py` for tasks, approvals, artifacts, recovery, eval/trace, gateway, and baseline panels.
- Existing subagent metadata includes `persistent`, `owner_session`, `role`, `status`, `chat_session_id`, `chat_title`, profile, memory, and per-agent session files.
- Existing read-only host/query tools already expose agent, task, approval, artifact, capability, and schedule snapshots, so the dashboard should reuse the same governed facts rather than introduce a parallel state store.

## Assumptions

- MVP should work without new external dependencies.
- MVP should not require the model to generate executable UI code.
- MVP should support a useful default panel for persistent agents even before an agent provides a custom dashboard spec.
- MVP should support a useful default main-agent home page even before any custom main dashboard spec exists.
- If an agent-provided spec is malformed or references unsupported widgets, the TUI should ignore unsupported parts and render a safe fallback.
- The "agent decides layout" requirement means the agent can declare section order, labels, emphasis, and bounded content sources, but cannot run arbitrary UI code.
- Startup default display means: when no prior view is available for the current runtime, open the main Orchestrator home page rather than a blank or arbitrary chat-only view.
- Last opened interface means: after the user opens a home page, chat view, history/session, or harness panel during the same app lifetime, returning to the default display should restore that last view.
- Last-opened UI state is in-memory only for MVP. Each fresh program launch should default back to the main Orchestrator home page.

## Requirements

- The main Orchestrator gets a dedicated home page.
- Every persistent subagent gets a dedicated main page.
- The persistent-agent main page should be the primary landing view when a persistent agent is selected, not only a separate optional admin panel.
- Selecting a persistent agent should default to the agent main page. Existing chat remains available through a clear switch/command/key path.
- On startup, Shuheng should show the default home display. Proposed default: main Orchestrator home page.
- During use, Shuheng should remember the last opened interface in memory and use that as the default display target until the user switches again.
- Do not persist last-opened UI navigation state across restarts in the MVP.
- Add a declaration format, tentatively `dashboard.v1`, stored with the agent metadata/home or derived from profile/content artifacts, that lets the agent choose layout and content sections.
- Use a hybrid page contract for MVP: the top status card is fixed by Shuheng for consistency, and the lower content area is agent-controlled through safe declarative sections and/or bounded Markdown.
- Allow persistent agents to update their own main-page declaration through a governed update path. The TUI validates and stores `dashboard.v1`/status/todos content, records provenance, and rejects unsupported executable or private-state fields.
- Supported dashboard sections should cover function/capability description, recent scheduled work and run outcomes, current status narrative, todo items, recent tasks, artifacts, approvals, and memory/profile summary.
- Render dashboards through the existing `PanelItem`/popup panel browser, not a separate UI framework.
- Display only data available through shared Shuheng registries and ledgers: subagent metadata, task ledger, schedule registry/runs, approvals, traces/evals, artifacts, profile/memory summaries, and generated artifact previews.
- Keep scheduler ownership centralized. The dashboard may show schedules targeting the agent, but must not store or run its own scheduler.
- Keep artifacts as references/previews. The dashboard should not inline unbounded artifact bodies.
- Add a command surface to open dashboards directly. Proposed MVP: `/home` for the current/default home page and `/agent-dashboard <agent>` for a target agent, plus automatic opening from persistent-agent selection if practical.
- Add tests or policy checks covering persistent-only visibility, malformed spec fallback, and no private scheduler/session state.
- Update docs/spec notes if the control contract changes.

## Acceptance Criteria

- [ ] The main Orchestrator has a home page.
- [ ] Every persistent subagent has a main page available from its selected agent view.
- [ ] Startup opens the default home display when no saved/active view should be restored.
- [ ] During the running TUI session, the default display restores the last opened interface.
- [ ] After a fresh restart, Shuheng defaults back to the main Orchestrator home page instead of restoring the previous process's last-opened UI state.
- [ ] Selecting a persistent agent opens the home page by default.
- [ ] The previous persistent-agent chat view remains reachable without losing current chat/session behavior.
- [ ] A persistent subagent can also be opened by id/name in a dedicated dashboard panel command.
- [ ] A temporary subagent either does not get a persistent dashboard or shows an explicit fallback explaining that dashboards are for persistent roles.
- [ ] The page shows at least agent identity/status, function/capability description, current status narrative, todo items, recent assigned tasks, schedule records targeting the agent, recent artifacts or artifact refs, and pending approvals relevant to the agent.
- [ ] The top status card has a stable Shuheng-owned layout for identity, lifecycle, status, queues, active task, model/security context, and last update.
- [ ] If a valid `dashboard.v1` spec exists, the page follows its declared section order/layout using only supported section types.
- [ ] The lower content area can render agent-declared safe sections and/or bounded Markdown.
- [ ] A persistent agent can submit a governed dashboard update containing layout, status narrative, and todo content.
- [ ] Dashboard updates are validated, stored with provenance, and degrade to the prior/default dashboard if invalid.
- [ ] Temporary agents cannot persist dashboard updates.
- [ ] If the spec is missing or invalid, the panel renders a safe default dashboard.
- [ ] Schedule data is read from the existing TUI scheduler registry/run audit path; no per-agent cron/session store is introduced.
- [ ] The implementation keeps existing task, approval, artifact, recovery, eval, gateway, and baseline panels working.
- [ ] Architecture baseline comparison says the change moves closer to the governed Orchestrator/dashboard target.

## Definition of Done

- Tests added or updated for the new dashboard behavior.
- `python3 -m compileall -q src scripts` passes.
- `python3 scripts/check_policy_gates.py` passes, or any failure is explained if unrelated to this task.
- `git diff --check` passes.
- `shuheng-check --root /home/vimalinx/Programs/GenericAgent` passes, or any failure is explained if environment-related.
- `docs/agent-harness-architecture.md` is compared before final claim.

## Technical Approach

Use existing TUI rendering primitives as much as possible. Add a small dashboard aggregation layer that turns one persistent `SubAgentRuntime` plus shared ledger data into a main-page model. Use a hybrid layout contract: Shuheng owns a fixed top status card, while the agent controls lower-page composition through `dashboard.v1` sections and/or bounded Markdown. Treat `dashboard.v1` as a bounded declaration: section ids, section order, titles, display density, and allowed data-source references only, not executable code. The renderer validates the spec, ignores unsupported sections, and falls back to a default persistent-agent dashboard.

Main Orchestrator home page:

- Show Shuheng runtime identity, current session/status, active main task if any, runtime provider state, pending approvals, recent tasks, recent artifacts, schedules overview, and high-level todos.
- It uses the same hybrid contract as persistent subagent pages, but its source identity is `orchestrator.main`.
- It should not masquerade as a subagent or create a fake persistent subagent record.

Persistent-agent UX:

- Default selected-agent view: agent home page.
- Chat/session history remains available through an explicit toggle, command, or keybinding.
- Temporary/session-only subagents keep the current chat-first behavior.

Default display UX:

- Startup default: main Orchestrator home page.
- Runtime default: remember the last opened interface such as main home, persistent-agent home, agent chat, history/session, or harness panel.
- The last-opened interface is UI navigation state, not a new task, schedule, memory, or agent session.
- Runtime default state is not persisted across process restarts in the MVP.

Proposed initial section types:

- `overview`: agent id, name, role, lifecycle, status, queues, active task, model/security context.
- `function`: the agent's self-description, capabilities, boundaries, and role promise.
- `status_narrative`: a bounded human-readable current status statement, ideally sourced from the latest agent-authored dashboard spec/status artifact.
- `todos`: pending work items declared by the agent or inferred from open assigned tasks.
- `schedules`: schedules whose target/routing points to this agent, with due state and latest run status.
- `tasks`: recent task ledger rows assigned to this agent.
- `artifacts`: recent artifact refs associated with this agent's tasks.
- `approvals`: pending or recent approvals targeting this agent or its tasks.
- `memory`: bounded profile/memory summary, with Secret Vault isolation respected.

Proposed governed update path:

- Add a `dashboard.update` style control/proposal path for persistent subagents, or reuse the existing proposal bridge with a current-schema action if that is more consistent with existing control parsing.
- Store the latest accepted dashboard declaration in the subagent's persisted state with provenance fields such as `updated_at`, `source`, `task_id`, and `artifact_refs`.
- Reject or ignore unsupported fields generically; do not add special branches for removed or private scheduler/session concepts.

Proposed data flow:

`Main Orchestrator or Persistent SubAgentRuntime -> governed dashboard.update or default spec -> shared ledgers/registries -> home-page model -> TUI default display / selected-agent view / optional panel command`

## Decision (ADR-lite)

Context: The main Orchestrator and long-running agents need role-specific workspaces, but hidden per-agent scheduled sessions would fragment state and violate the shared-ledger architecture.

Decision: Implement hybrid home pages for the main Orchestrator and persistent agents, rendered by the TUI from shared registries. Shuheng owns the top status card; agents control lower-page layout through governed `dashboard.v1` updates, safe declarations, and bounded Markdown. Each fresh startup defaults to the main home display, and runtime navigation remembers the last opened interface in memory only. Do not let agents create private scheduler state or executable UI code.

Consequences: The first version gives the main agent and each persistent agent a recognizable role page while preserving consistent operational status, auditability, recovery, approval gates, and future compatibility with A2A/MCP-style artifact references.

## Expansion Sweep

Future evolution:

- A later version can let persistent agents submit dashboard spec updates as governed proposals or artifacts.
- A later version can support richer widgets once the section contract stabilizes.
- A later version can add a marketplace/library of dashboard section templates for common roles such as monitor, researcher, curator, maintainer, or ops agent.

Related scenarios:

- `/schedules`, `/tasks`, `/artifacts`, and `/approvals` should remain the source panels; the agent dashboard is a filtered role workspace, not a duplicate source of truth.
- Secret subagents need the same dashboard concept but must respect Secret Vault isolation and encrypted storage boundaries.

Failure and edge cases:

- Missing target, ambiguous target, temporary agent, deleted agent, malformed spec, unsupported section, empty ledgers, and locked Secret Vault must all degrade gracefully.
- The dashboard must not create tasks, approve actions, run schedules, write memory, or mutate artifacts.

## Out of Scope

- Agent-generated executable UI code.
- Per-agent private scheduler/session stores.
- Persistent dashboards for temporary/session-only agents.
- Rich graphical chart widgets beyond the existing curses panel browser.
- Direct memory writes or approval decisions from the dashboard.
- Full A2A remote dashboard compatibility in the first pass.
- Ungoverned agent writes to dashboard state.

## Technical Notes

- Existing panel primitive: `PanelItem` dataclass and `open_harness_panel(...)` in `src/ga_tui/app.py`.
- Existing subagent state: `SubAgentRuntime`, `save_subagent_meta(...)`, `load_subagents(...)`, `subagent_chat_session_entries(...)`.
- Existing scheduler source of truth: `src/ga_tui/scheduler.py`, including `scheduled_task_registry(...)`, `latest_schedule_records(...)`, and schedule run audit helpers.
- Existing shared task source: `latest_task_records(...)` and `task_panel_items(...)`.
- Existing artifact source: `artifact_inventory(...)` and `artifact_preview(...)`.
- Existing read-only query tools: `tui_tool_agent_list`, `tui_tool_agent_get`, `tui_tool_task_list`, `tui_tool_schedule_list`, and related host tool definitions.
- Existing command handling includes panel commands for `/tasks`, `/approvals`, `/artifacts`, `/recover`, `/evals`, `/gateway`, and `/baseline`; `/schedules` currently reports status text and can inform the new command surface.
