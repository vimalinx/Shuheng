# Contributing

Shuheng is an experimental local alpha. Contributions should preserve the
control-plane contract: one strong Orchestrator, bounded worker agents, explicit
ledgers, artifact references, approval gates, and auditable protocols.

## Development Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the local application from source:

```bash
PYTHONPATH=src python -m ga_tui
```

## Required Checks

Run these before opening a pull request:

```bash
python -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/runtime_smoke.py scripts/wheel_smoke.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_release_hygiene.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_policy_gates.py
PYTHONDONTWRITEBYTECODE=1 python scripts/runtime_smoke.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
python -m compileall -q src scripts
python -m build --sdist --wheel --outdir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist
git diff --check
```

If you have a sibling GenericAgent checkout, also run:

```bash
PYTHONPATH=src python -m ga_tui.integration doctor --root /path/to/GenericAgent
```

## Pull Request Guidelines

- Keep user-facing product wording as Shuheng or 枢衡.
- Preserve internal compatibility identifiers such as `src/ga_tui`, `GA_TUI_*`,
  `ga_tui_query`, and `ga-tui.*` schemas unless a migration is explicitly scoped.
- Do not commit local runtime state, secrets, model credentials, normal session
  logs, Secret Vault content, or private research notes.
- Changes touching TUI, subagents, approvals, memory, artifacts, recovery,
  eval/trace, A2A/MCP, or orchestration must be checked against
  `docs/agent-harness-architecture.md`.
- Do not describe A2A/MCP as certified implementations without real third-party
  client interoperability tests.

## Release Hygiene

`scripts/check_release_hygiene.py` is the repository-level guardrail for public
alpha releases. If it fails, fix the source issue rather than weakening the
check unless the PR is specifically about release policy.
