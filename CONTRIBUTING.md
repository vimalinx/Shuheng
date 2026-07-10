# Contributing

Shuheng is an experimental local alpha. Contributions should preserve the
control-plane contract: one strong Orchestrator, bounded worker agents, explicit
ledgers, artifact references, approval gates, and auditable protocols.

## Development Setup

Read [`docs/development/`](docs/development/index.md) before changing runtime,
storage, orchestration, packaging, or release behavior.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the local application from source:

```bash
PYTHONPATH=src python -m shuheng
```

## Branch Workflow

- `main` is the release-ready OMP core line and the repository default. Do not
  use it for day-to-day feature development.
- `dev` is the integration line for Pi ecosystem, custom Agent, Skill/Plugin,
  scheduler, and other forward development. The full CI matrix runs on every
  push to `dev`.
- Start normal work from `dev`, preferably on a short-lived `feature/*` branch,
  and merge it back into `dev` after CI.
- Promote a release candidate with a `dev -> main` pull request. `main` requires
  the Python 3.10 and 3.13 checks, an up-to-date branch, and linear history.
- Start urgent fixes from `main` on `hotfix/*`, merge them into `main` through a
  pull request, then bring the resulting `main` commit back into `dev`.
- Pi remains optional and explicit on the release line. Its presence in the
  source tree does not make `runtime setup-pi` part of the default install.

## Required Checks

Run these before opening a pull request:

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

## Pull Request Guidelines

- Keep user-facing product wording as Shuheng or 枢衡.
- Preserve internal compatibility identifiers such as `src/shuheng`, `SHUHENG_*`,
  `shuheng_query`, and `shuheng.*` schemas unless a migration is explicitly scoped.
- Do not commit local runtime state, secrets, model credentials, normal session
  logs, Secret Vault content, or private research notes.
- Changes touching TUI, subagents, approvals, memory, artifacts, recovery,
  eval/trace, A2A/MCP, or orchestration must be checked against
  `docs/agent-harness-architecture.md`.
- Do not describe A2A/MCP as certified implementations without real third-party
  client interoperability tests.

## Contribution License

Unless explicitly stated otherwise, contributions submitted to this repository
are licensed under the repository's MIT License. By submitting a contribution,
you confirm that you have the right to provide it under those terms.

## Release Hygiene

`scripts/check_release_hygiene.py` is the repository-level guardrail for public
alpha releases. If it fails, fix the source issue rather than weakening the
check unless the PR is specifically about release policy.
