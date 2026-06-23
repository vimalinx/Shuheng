<div align="center">

<h1>Shuheng</h1>

<p><strong>A central execution, orchestration, memory, and approval layer for local agents.</strong></p>

<p>
Bring session management, multi-agent orchestration, task planning, memory governance, and automation control into a stable curses-based TUI built for long-running local agent work.
</p>

<p>
  <a href="README.md">简体中文</a>
  ·
  <a href="README.en.md"><strong>English</strong></a>
</p>

<p>
  <a href="https://www.python.org/"><img alt="Python >= 3.10" src="https://img.shields.io/badge/Python-%3E%3D3.10-111827?style=for-the-badge&logo=python&logoColor=white"></a>
  <a href="#positioning"><img alt="Curses TUI" src="https://img.shields.io/badge/Interface-curses-0f172a?style=for-the-badge"></a>
  <a href="#architecture-direction"><img alt="Agent Harness" src="https://img.shields.io/badge/Agent_Harness-governed-1f2937?style=for-the-badge"></a>
  <a href="https://linux.do/"><img alt="LINUX DO" src="https://img.shields.io/badge/Community-LINUX%20DO-111827?style=for-the-badge"></a>
</p>

<p>
  <a href="#quick-start">Quick Start</a>
  ·
  <a href="#capability-overview">Capabilities</a>
  ·
  <a href="#command-surface">Commands</a>
  ·
  <a href="#architecture-direction">Architecture</a>
  ·
  <a href="#community">Community</a>
</p>

</div>

---

## Positioning

`Shuheng` is a terminal control plane for local multi-agent work. It evolved from the earlier `GenericAgent TUI`: it does not reimplement agent runtimes, but separates the daily user-facing execution, orchestration, approval, memory, and session workspace into a dedicated repository.

Think of it as:

```text
Session Manager + Multi-Agent Console + Task Board + Memory/Approval Governance + Automation Control Plane
```

Shuheng makes OMP, GenericAgent, Codex, Claude Code, and other local agent runtimes easier to govern in long-running terminal workflows. The current compatibility layer still reuses the main `GenericAgent` project for history restoration and related core capabilities.

> Runtimes execute. Shuheng governs the control surface.

## Why This Exists

| Problem | What Shuheng does |
| --- | --- |
| TUI patches conflict with upstream core updates | Keep the TUI external and launch it with `shuheng` |
| Long conversations become hard to manage | Restore, pin, categorize, filter, archive, and trash sessions |
| Multi-agent work can drift | Keep one orchestrator responsible for planning, dispatch, synthesis, and validation |
| Subagent identities need continuity | Support temporary and persistent subagents with profile, role, model, and memory candidates |
| Task progress needs visibility | Expose task ledger, step plans, agent mail, artifacts, evals, and traces |
| Sensitive sessions should not leak into normal history | Use local encrypted Secret Vault and clear plaintext state on lock |

The implementation uses Python `curses` for a small, controlled, low-dependency terminal surface. This avoids common input issues that can appear in heavier UI stacks under some terminal, Wayland, and mouse-mode combinations.

## Capability Overview

### In One Sentence

`Shuheng` combines conversational control, session organization, task planning, multi-agent collaboration, memory governance, and automation execution in one terminal control plane.

### Core Capability Matrix

| Layer | What it controls | Example intent |
| --- | --- | --- |
| Session management | Pin, categorize, filter, collapse, archive, rename, delete | `Put this session under "Project Development"` |
| Task planning | Create multi-step plans and track completion | `Create a five-step plan and work through it step by step` |
| Subagent orchestration | Create, reuse, stop, and remove temporary or persistent subagents | `Start a temporary researcher to check best practices for this library` |
| Main orchestration | Let the main agent plan, delegate, wait, and synthesize | `Wait for the subagents before summarizing` |
| Automation entrypoint | File, code, browser, log, memory, and system operations | `Ask the reviewer to inspect the code I just wrote` |
| Governance views | Task ledger, approvals, artifacts, recovery, evals, traces | `Check whether that background task has returned` |

### Session Workspace

| Capability | Purpose |
| --- | --- |
| Pin / unpin | Keep important sessions at the top |
| Category | Organize sessions by labels such as development, research, daily, pending |
| Filter | Show only a selected group of sessions |
| Collapse / expand | Control sidebar density |
| Archive / unarchive | Hide inactive but still valuable sessions |
| Rename | Give important tasks readable titles |
| Delete to trash | Clean up useless sessions |

### Task Board

Complex work can be split into steps and advanced gradually. Subagents can attach to specific steps while the main orchestrator keeps final responsibility.

```text
Task: Build a crawler system

1. Analyze target website
2. Design data structure
3. Implement crawler
4. Test anti-bot behavior
5. Write docs and run instructions
```

Supported workflow:

- Create a multi-step plan.
- Mark steps completed.
- Track the active step.
- Attach subagents to specific steps.
- Keep the main orchestrator responsible for final synthesis.

### Subagent Console

| Role | Typical work |
| --- | --- |
| Researcher | Collect references, compare options, produce findings |
| Coder | Write code, fix bugs, implement features |
| Reviewer | Inspect code, surface risks, run quality checks |
| Verifier | Re-check results, run tests, validate facts |
| Memory curator | Prepare long-term memory candidates |
| Ops agent | Handle deployment, environment, logs, and command execution |

### Temporary And Persistent Subagents

| Type | Best for | Behavior |
| --- | --- | --- |
| Temporary subagent | One-off research, short tasks, experiments | No long-term identity; disposable |
| Persistent subagent | Long-running projects, fixed roles, dedicated assistants | Stable identity with profile, responsibility, memory candidates, and default model |

Examples:

```text
Start a temporary researcher to check best practices for this library.
Create a long-term code reviewer for my Python projects.
Ask the previous researcher to continue the analysis.
Ask the reviewer to inspect the code I just wrote.
```

### Natural Language Control

You do not need to memorize every command. Describe the goal:

```text
Pin the current session.
Move this session to "Project Development".
Hide archived sessions.
Rename this session to "FastAPI Backend Refactor".
```

```text
Create a five-step plan for this project and proceed step by step.
Assign step one to the researcher and step two to the coder.
Wait for the subagents before summarizing.
```

```text
Help me manage this session.
Create a subagent for me.
Break this task into a plan.
Let several agents work on it together.
Organize my historical sessions.
```

## Quick Start

### 1. Install

```bash
python -m pip install -e .
```

Run directly from source without installation:

```bash
PYTHONPATH=src python -m ga_tui
```

`ga_tui` remains the Python module name for compatibility. The official command is `shuheng`.

### 2. Point To GenericAgent Core

The TUI tries to discover the `GenericAgent` checkout automatically. If discovery fails:

```bash
export GENERICAGENT_ROOT=/path/to/GenericAgent
```

Legacy variable is also supported:

```bash
export GA_ROOT=/path/to/GenericAgent
```

### 3. Validate Integration

```bash
shuheng-check
```

Healthy output includes:

```text
Status: OK
Core imports: agentmain, continue_cmd
Launch without core patches: shuheng
```

### 4. Launch

```bash
shuheng
```

Recommended update flow:

```bash
cd /path/to/GenericAgent
git pull

cd /path/to/Shuheng
shuheng
```

This lets the core `GenericAgent` project update normally while the TUI evolves as a separate interface layer.

## Optional Core Shim

If you want the `GenericAgent` checkout's core launcher to launch this external TUI, install a small launcher shim.

Replace `frontends/tuiapp.py`:

```bash
shuheng-install-core-shim --target tuiapp --overwrite
```

The first replacement keeps a backup:

```text
frontends/tuiapp.py.genericagent-tui.bak
```

Install a sidecar without replacing `frontends/tuiapp.py`:

```bash
shuheng-install-core-shim
python /path/to/GenericAgent/frontends/tuiapp_curses.py
```

Call integration utilities explicitly:

```bash
shuheng-integration doctor --root /path/to/GenericAgent
shuheng-integration install-core-shim --root /path/to/GenericAgent --target tuiapp-curses
```

## Command Surface

Type `/help` inside the TUI for the full command list.

### Sessions

```text
/continue [n]        List or restore historical sessions
/sessions            List historical sessions
/new                 Create a new empty session
/temp                Create a temporary session without history logs, session memory, or memory candidates
/clear               Clear the current screen
/status              Show current status
/stop                Stop the current task
/resume              Ask the agent to summarize recent activity
/fold                Toggle automatic process folding
/md                  Toggle lightweight Markdown rendering
/rename <name>       Rename current session
/pin [n]             Pin current or numbered session
/unpin [n]           Unpin current or numbered session
/category [n] <name> Set session category
/filter [category]   Filter by category
/archive [n]         Archive current or numbered session
/delete [n]          Move current or numbered session to trash
```

### Models

```text
/model               Manage model configs, switch current dialogue model, extract models, health check, set defaults
```

### Subagents

```text
/agents                         List persistent subagents
/agent list                     List subagents
/agent new [role:]<name>        Create a subagent
/agent ask <agent> <prompt>     Delegate work to a subagent
/agent role <agent> <role>      Set subagent role
/agent model <agent> [model]    Set persistent subagent default model
/agent settings <agent>         Open persistent subagent settings
/agent memory <agent>           Inspect subagent memory
/agent remember <agent> <text>  Append subagent memory
/agent stop <agent>             Stop a subagent
/agent delete <agent>           Remove a subagent
```

### Governance And Observability

```text
/tasks               View shared task ledger
/bus                 View agent mail
/approvals           View pending approvals
/approve <id>        Approve an item
/reject <id>         Reject an item
/artifacts           Open artifact store
/recover             View or handle recoverable tasks
/evals               View eval and trace records
/gateway             View A2A/MCP gateway scaffold
/baseline            View architecture baseline report
/memory              Inspect memory system
/mem                 Alias for /memory
```

### Secret Vault

```text
/Secret                         Enter local encrypted Secret Vault
/Secret status                  Show Secret Vault status
/Secret sessions                List Secret sessions
/Secret open-session <n>        Open a Secret session
/lock                           Lock Secret Vault and clear plaintext state
/toSecret [delete|archive] [n]  One-way migrate normal session to Secret
```

## Project Layout

```text
.
├── README.md
├── README.en.md
├── pyproject.toml
├── docs/
│   └── agent-harness-architecture.md
├── scripts/
│   └── check_policy_gates.py
├── src/
│   └── ga_tui/
│       ├── __main__.py
│       ├── __init__.py
│       ├── app.py
│       ├── integration.py
│       ├── runtime.py
│       ├── scheduler.py
│       ├── control_protocol.py
│       ├── agent_bridge.py
│       ├── ohmypi_provider.py
│       ├── genericagent_provider.py
│       └── compat_legacy.py
└── tests/
    ├── conftest.py
    ├── test_cell_utils.py
    ├── test_jsonl.py
    ├── test_path_safety.py
    ├── test_scheduler_parsing.py
    ├── test_secret_crypto.py
    └── test_time_path_helpers.py
```

| File | Purpose |
| --- | --- |
| `src/ga_tui/app.py` | Main curses TUI: sessions, memory, approvals, Secret Vault core logic |
| `src/ga_tui/integration.py` | GenericAgent core discovery, doctor checks, launcher shim |
| `src/ga_tui/runtime.py` | Runtime provider abstractions and registry |
| `src/ga_tui/scheduler.py` | Scheduled-task registry and due-time evaluation (cron / interval / at) |
| `src/ga_tui/control_protocol.py` | Agent task control protocol (v2) parsing |
| `src/ga_tui/agent_bridge.py` | Local agent bridge API for OMP and other clients to read/write Shuheng state |
| `src/ga_tui/ohmypi_provider.py` | OMP runtime adapter (process, host tools, usage sync) |
| `src/ga_tui/genericagent_provider.py` | GenericAgent runtime adapter |
| `src/ga_tui/compat_legacy.py` | Legacy session/memory compatibility parsing |
| `tests/` | pytest suite covering pure functions, crypto, and parsers |
| `scripts/check_policy_gates.py` | Function-level smoke checks for harness policy gates |
| `docs/agent-harness-architecture.md` | Long-term agent harness architecture baseline |
| `pyproject.toml` | Python package metadata, dependencies, and command entry points |

## Relationship With GenericAgent

This repository is the external TUI layer for `GenericAgent`.

It currently reuses core modules from the main project:

- `agentmain.py` for the main agent runtime.
- `frontends/continue_cmd.py` for history restoration and transcript parsing.
- `frontends/session_names.py` for optional session naming.

This boundary lets the core project follow upstream updates while the TUI can be tested, released, and evolved independently. Future adapter work can make the external boundary even cleaner.

## Architecture Direction

`Shuheng` is evolving from a chat entrypoint into a governed local agent harness.

Architecture baseline:

```text
docs/agent-harness-architecture.md
```

| Principle | Direction |
| --- | --- |
| Strong orchestrator | One main controller remains accountable for final outcomes |
| Restricted subagents | Subagents run under role, permission, budget, and stop-condition boundaries |
| Single-writer discipline | Read work can be parallel; writes stay controlled |
| Auditability | task ledger, progress ledger, mail, artifacts, approvals, evals, and traces remain inspectable |
| Human approval gates | Long-term memory, Secret operations, deletion, deployment, and external side effects require approval |
| Protocol compatibility | A2A/MCP gateway surfaces prepare for cross-agent and cross-tool workflows |

Changes touching TUI behavior, subagents, approvals, memory, artifacts, recovery, eval/trace, A2A/MCP, or orchestration should be checked against the architecture baseline before completion.

## Development

Run from source:

```bash
PYTHONPATH=src python -m ga_tui
```

Validate integration:

```bash
shuheng-check
```

Recommended checks before committing:

```bash
git diff --check
python -m py_compile src/ga_tui/*.py
PYTHONPATH=src python -m ga_tui.integration doctor
python -m pytest tests/ -q
```

Before publishing, verify that no local absolute paths, secrets, model credentials, normal session logs, or Secret Vault content are added.

## Community

This project is promoted in the [LINUX DO](https://linux.do/) open-source community. Thanks to the community for discussion, feedback, and suggestions.
