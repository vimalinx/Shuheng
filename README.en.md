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

`Shuheng` is a terminal control plane for local multi-agent work. It does not reimplement agent runtimes; it separates the daily user-facing execution, orchestration, approval, memory, and session workspace into a dedicated repository.

Current release posture is **experimental local alpha**. The local curses TUI, sessions, task ledgers, artifacts, approvals, Secret Vault, and OMP runtime output/control are the primary stable surfaces. External AI clients use the local JSONL stdio `shuheng-agent-gateway`. A2A/MCP-shaped data is represented as local records in Agent Mail and resource registries.

Think of it as:

```text
Session Manager + Multi-Agent Console + Task Board + Memory/Approval Governance + Automation Control Plane
```

Shuheng first makes the OMP runtime easier to govern in long-running terminal workflows, while keeping one control-plane contract for future Codex, Claude Code, and other Provider adapters. OMP remains the default core runtime, while Shuheng owns session history, harness ledgers, subagents, Secret Vault state, and isolated runtime files under `~/.shuheng`.

> Runtimes execute. Shuheng governs the control surface.

## Why This Exists

| Problem | What Shuheng does |
| --- | --- |
| TUI patches conflict with upstream core updates | Keep the TUI external and launch it with `shuheng` |
| Long conversations become hard to manage | Restore, pin, categorize, filter, archive, and trash sessions |
| Multi-agent work can drift | Keep one orchestrator responsible for planning, dispatch, synthesis, and validation |
| Subagent identities need continuity | Support temporary and persistent subagents with profile, role, model, and memory candidates |
| Task progress needs visibility | Expose task ledger, step plans, agent mail, artifacts, heuristic evals, and traces |
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
| Governance views | Task ledger, approvals, artifacts, recovery, heuristic evals, traces | `Check whether that background task has returned` |

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

For full fresh-machine setup, platform support, and state migration notes, see
[`docs/install.md`](docs/install.md).

```bash
curl -fsSL https://raw.githubusercontent.com/vimalinx/Shuheng/main/scripts/install.sh | sh
```

The installer creates an isolated user-local venv, installs `shuheng` /
`shuheng-check` launchers, installs or verifies the pinned OMP runtime, installs
the shared `shuheng-agent-gateway` skill by default, and runs `shuheng-check`.
OMP requires Bun 1.3.14+; a missing main runtime produces an actionable failure,
not a false success. The installer supports Linux, Windows via WSL2, and
best-effort macOS; native Windows users should use WSL2.

Developer source install:

```bash
python -m pip install -e .
```

Run directly from source without installation:

```bash
PYTHONPATH=src python -m shuheng
```

`shuheng` remains the Python module name for compatibility. The official command is `shuheng`.

First confirm the public command entrypoint is available:

```bash
shuheng --help
shuheng --version
```

`shuheng --help`, TUI launch, local protocol records, and `shuheng-check` use Shuheng's own local control plane. The default runtime core is OhMyPi / OMP.

### 2. Validate Integration

```bash
shuheng-check
```

Healthy output includes:

```text
Core runtime: OhMyPi / OMP
OMP runtime check: OK
Status: OK
Launch without legacy patches: shuheng
```

### 3. Launch

```bash
shuheng
```

The recommended update flow is to re-run the inspected installer:

```bash
sh /tmp/shuheng-install.sh --version v0.2.0-alpha.1
shuheng --version
shuheng-check
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

Model configuration lives at `~/.shuheng/config/mykey.py`; its directory is
mode `0700` and config/backups are mode `0600`. OMP defaults to
`standard + write`. Full host authority requires the explicit combination
`SHUHENG_OMP_PERMISSION_PROFILE=full` and `SHUHENG_OMP_APPROVAL_MODE=yolo`.
`yolo` without `full` is downgraded to `write`; `full + write/always-ask`
continues to fail closed at the program-level high-risk gate.
Additional inherited environment variables must be named in
`SHUHENG_OMP_INHERIT_ENV`.

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

### Agent Projects (Pi-native workers)

```text
/agent-projects                               Open the embedded single-file Agent Project workspace
/agent-project list                           List local projects
/agent-project create <id> [name]             Create a project
/agent-project fork <source-id> <new-id>      Fork a project
/agent-project build <id>                     Validate and create a content-addressed Build
/agent-project run <id> <objective>           Run a Build with no custom authority requests
/agent-project run <id> --grant-declared ...  Grant this frozen Build's declared capabilities and local Tools
```

OMP remains the main Agent and default Provider. Pi-native only runs task workers
through ledger, policy, and single-writer admission. An authorized project Tool is
trusted local Node code; this MVP has no OS syscall sandbox, so the writer lock
cannot prevent direct host side effects. Run only source you trust. Pi workers do
not support Secret Vault execution or unledgered direct chat. Frozen Build bytes
are not retained, so an old Build is digest-auditable but not replayable from
Shuheng state after its source changes. Every Project assignment must confirm the
current Build through `/agent-project run`; `/agent ask`, scheduler, and recovery
retry never start mutable Project source silently.

Pi-native is an optional experimental Provider. First use requires Node.js 22.19+
and npm; the installed command uses the shipped lockfile to install the pinned
SDK. Otherwise `/runtimes` reports `missing_package` while OMP remains usable:

```bash
shuheng runtime setup-pi
shuheng runtime check --require-pi
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
/evals               View heuristic eval and trace records
/baseline            View architecture baseline report and evidence levels
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
├── README.md / README.en.md          Chinese / English readme
├── THIRD_PARTY_NOTICES.md            External runtime and dependency license boundaries
├── pyproject.toml                    Package metadata, deps, entry points, ruff config
├── docs/
│   ├── agent-harness-architecture.md     Long-term agent harness architecture baseline (north star)
│   ├── development/                      Public contributor engineering contracts
│   ├── app-py-decomposition-plan.md      Incremental `app.py` split plan (Phase 0–7)
│   ├── runtime-provider-control-plane.md Runtime provider control-plane design
│   ├── public-alpha-readiness.md         Release posture, known gaps, fresh-clone expectations
│   └── install.md                        Cross-platform install and platform-support notes
├── scripts/
│   ├── check_policy_gates.py         Function-level smoke for harness policy gates (CI gate)
│   ├── check_release_hygiene.py      Release hygiene checks (secrets / private paths / posture)
│   ├── runtime_smoke.py              Runtime provider runtime smoke
│   ├── dogfood_stdio_gateway.py      Local stdio agent gateway end-to-end dogfood
│   ├── wheel_smoke.py                wheel/sdist integrity and public/private boundary checks
│   ├── release_scan_rules.py         Release content scan rules
│   └── install.sh                    `curl|sh` cross-platform installer (Linux / WSL2 / macOS)
├── src/shuheng/
│   # ── Entry & wiring ──
│   ├── __main__.py                   `python -m shuheng`
│   ├── __init__.py                   Package definition, `__version__`
│   ├── cli.py                        Lightweight public CLI (`--help` avoids heavy runtime)
│   ├── app.py                        curses TUI main wiring + process loop (composition module, still shrinking)
│   # ── Pure leaves: types / text / paths ──
│   ├── ui_types.py                   UI state and shared dataclasses
│   ├── text_utils.py                 Terminal cell / text pure helpers
│   ├── path_utils.py                 Filesystem path-safety pure helpers
│   ├── agent_projects.py             Pure Agent Project/Blueprint/Build/Run Manifest contracts
│   ├── agent_editor.py               Single-file edit state, atomic save, and conflict checks
│   # ── Storage adapters ──
│   ├── ledger_store.py               JSONL append/read/cache (fcntl + thread locks)
│   ├── history_store.py              Normal session history and transcript I/O
│   ├── subagent_store.py             Subagent identity / profile / memory / sidebar keys
│   ├── secret_vault.py               Secret Vault crypto (xchacha20poly1305) and encrypted storage
│   ├── compat_legacy.py              Legacy session/memory parsing (quarantined)
│   # ── Governance layer ──
│   ├── governance.py                 task / approval / artifact / trace / eval record semantics + single-writer lock
│   ├── control_protocol.py           Agent task control protocol (v2) parsing
│   ├── local_protocol_registry.py    Local protocol record shapes (A2A/MCP-shaped metadata)
│   ├── context_packs.py              Context layering and memory hydration
│   ├── release_readiness.py          Release posture, baseline evidence levels, heuristic eval
│   # ── Runtime ──
│   ├── runtime.py                    Runtime provider abstractions and registry
│   ├── runtime_dispatch.py           Provider-neutral dispatch and stream normalization
│   ├── runtime_evidence.py           Runtime / e2e evidence collection
│   ├── runtime_setup.py              OMP/Pi installation, RPC readiness, version, and health checks
│   ├── ohmypi_provider.py            OhMyPi/OMP provider (subprocess + JSONL stdio RPC)
│   ├── pi_native_provider.py         Pi-native frozen-Build worker provider
│   ├── subagent_task_dispatch.py     Injected governed subagent task dispatch
│   ├── agent_project_workspace.py    Agent Project TUI/command composition layer
│   ├── integration.py                `shuheng-check` doctor and local integration utilities
│   ├── frontend_history_compat.py    Legacy frontend history/name fallback
│   # ── Automation & extensions ──
│   ├── scheduler.py                  Scheduled-task registry and triggering (cron / interval / at)
│   ├── workflows.py                  Declarative workflow definitions
│   ├── plugins.py                    Declarative plugin registry
│   ├── skill_installer.py            Install shared skills (e.g. shuheng-agent-gateway)
│   # ── Protocol bridge ──
│   ├── agent_bridge.py               Local agent bridge / stdio gateway API (discover agents, send tasks, submit proposals)
│   # ── UI rendering & input ──
│   ├── rendering.py                  curses-free rendering transforms and message-block parsing
│   ├── dashboard.py                  Dashboard schema and normalization
│   ├── input_controller.py           Terminal input / cursor / mouse / paste
│   ├── commands.py                   Command completion and command handling
│   # ── Helpers ──
│   ├── baseline.py                   Architecture baseline report items
│   └── history_titles.py             Session title/description (process-summary safe)
└── tests/                            pytest suite: pure functions, crypto, parsers, stores, rendering, governance, install, and release
```

Dependency direction (bottom-up, from [`docs/app-py-decomposition-plan.md`](docs/app-py-decomposition-plan.md)):

```text
path / type constants → pure text & cell helpers → storage adapters & stores → governance services
  → renderers / command handlers / local protocol records → app.py orchestration facade & process loop
```

> `src/shuheng/app.py` is still a ~28k-line composition module and the top maintainability risk; it is being shrunk phase by phase per the plan above. Newly extracted modules must not import `shuheng.app` back.

> A small number of internal legacy-glue modules carrying retired branding (local compatibility only, not a public control surface) are intentionally not named in this public map per the retirement policy; see the source tree.

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
| Protocol records | A2A/MCP-shaped objects are local registry/record shapes in Agent Mail and resource registries |
| Local gateway | `shuheng-agent-gateway serve --stdio` provides a persistent local JSONL stdin/stdout channel |

Changes touching TUI behavior, subagents, approvals, memory, artifacts, recovery, eval/trace, A2A/MCP, or orchestration should be checked against the architecture baseline before completion.

### Release Readiness

Shuheng's release-readiness metadata lives in `src/shuheng/release_readiness.py`. Current default posture:

- Stable local surfaces: curses TUI, session workspace, task ledgers, artifacts, approvals, Secret Vault, OMP runtime output/control.
- Experimental surfaces: Pi-native Agent Projects, baseline report, runtime/evidence smoke, heuristic eval, scheduler runtime dispatch, local protocol-shaped registry records, stdio agent gateway.
- Known gaps: `app.py` remains a large composition module; eval does not prove factual/citation correctness; A2A/MCP-shaped records are not reachable protocol endpoints; Pi-native custom Tools are trusted local code rather than an OS sandbox.

### Local Agent Gateway

```bash
shuheng install-agent-gateway-skill
shuheng-agent-gateway register
shuheng-agent-gateway agent-directory
shuheng-agent-gateway serve --stdio
shuheng-agent-gateway message-send --target <agent-id> --message "task for this agent"
shuheng-agent-gateway task-status --task-id <task-id>
```

`shuheng install-agent-gateway-skill` installs or updates Shuheng's bundled `shuheng-agent-gateway` skill into the shared skill root, defaulting to `~/.agents/skills`. Other local agents can then use `$shuheng-agent-gateway` to learn the local stdio gateway contract. The skill only documents agent discovery, governed message dispatch, and task-status reads; it does not expose Shuheng internal context, ledgers, secrets, or permission matrices.

`serve --stdio` is the long-lived local process intended for an external AI or supervisor to hold. It speaks JSONL over stdin/stdout and exposes exactly `agent_directory`, `message_send`, `task_status`, and `gateway_status`; internal metadata, filesystem paths, and other bridge actions do not cross that process boundary. `message-send` dispatches through the Shuheng Orchestrator's governed subagent task path and approval gates.

Public clients should launch only `shuheng-agent-gateway`. `shuheng-agent-bridge` and `python -m shuheng.agent_bridge` are trusted internal integration surfaces for local Providers/plugins, not aliases for the public gateway, and must not be handed to untrusted clients.

Local end-to-end verification:

```bash
python scripts/dogfood_stdio_gateway.py
```

The script launches a real `serve --stdio` subprocess under an isolated `SHUHENG_HOME` and verifies `agent_directory`, `message_send`, `task_status`, the task ledger, approval ledger, and trace ledger.

## Development

Run from source:

```bash
PYTHONPATH=src python -m shuheng
```

Validate integration:

```bash
shuheng-check
```

Recommended checks before committing:

```bash
python -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/dogfood_stdio_gateway.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_release_hygiene.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_policy_gates.py
PYTHONDONTWRITEBYTECODE=1 python scripts/dogfood_stdio_gateway.py
PYTHONDONTWRITEBYTECODE=1 python scripts/runtime_smoke.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
python -m compileall -q src scripts
npm ci --ignore-scripts --prefix integrations/pi-native-sidecar
node --check integrations/pi-native-sidecar/sidecar.mjs
python -m build --sdist --wheel --outdir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist
git diff --check
```

`scripts/wheel_smoke.py --dist-dir` installs both the latest wheel and sdist, checks the wheel metadata/private file boundary, verifies wheel RECORD hash/size integrity, checks the sdist archive public/private file boundary, sdist metadata/entry points, and SOURCES manifest consistency, scans both artifact contents for secret-like literals and local absolute paths, and runs public entrypoint checks. `--no-deps` and `--wheel-only` are local debugging options, not release gates.

Before publishing, verify that no local absolute paths, secrets, model credentials, normal session logs, or Secret Vault content are added. `scripts/check_release_hygiene.py` checks governance files, package metadata, private paths, realistic secret patterns, and public alpha wording.

### Open-Source Release Boundaries

- License: MIT, see `LICENSE`.
- Security reporting and boundaries: see `SECURITY.md`. The local agent gateway uses JSONL stdio. External sending, deployment, deletion, Secret access, and long-term memory writes still go through local approval gates.
- Contribution flow: see `CONTRIBUTING.md`; code of conduct: `CODE_OF_CONDUCT.md`.
- Release notes: see `CHANGELOG.md`.
- Third-party dependency boundary: see `THIRD_PARTY_NOTICES.md`.
- Contributor engineering contracts: see `docs/development/`.
- CI: `.github/workflows/ci.yml` runs release hygiene, policy gates, runtime smoke, pytest, compile, package build, wheel smoke, and `git diff --check`.
- Public alpha readiness: see `docs/public-alpha-readiness.md` for the release posture, source boundary, known gaps, and fresh-clone expectations.

## Community

This project is promoted in the [LINUX DO](https://linux.do/) open-source community. Thanks to the community for discussion, feedback, and suggestions.
