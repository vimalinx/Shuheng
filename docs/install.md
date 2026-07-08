# Fresh Machine Setup

This guide is the public alpha installation contract for Shuheng.

## Support Matrix

| Platform | Status | Notes |
| --- | --- | --- |
| Linux | Supported alpha target | The package metadata declares POSIX Linux and the main UI is Python `curses`. |
| Windows via WSL2 | Recommended Windows path | Install an Ubuntu WSL2 environment and follow the Linux steps inside WSL. |
| macOS | Best effort, unverified | It may work in a compatible terminal, but there is no macOS CI or release gate yet. |
| Windows native | Unsupported | Native Windows terminals do not provide the same `curses`/POSIX behavior expected by the current TUI. |

Do not describe this release as production-ready, remotely secured, or fully
cross-platform. The supported claim is experimental local alpha.

## Requirements

- Python 3.10 or newer.
- A POSIX shell environment.
- A terminal that supports Python `curses`.
- Network access only for installing Python dependencies unless dependencies
  are already cached.

## Install From Source

```bash
git clone <shuheng-repository-url>
cd Shuheng

python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Verify the public entry points:

```bash
shuheng --help
shuheng-check
```

Launch the local TUI:

```bash
shuheng
```

You can also run from a source checkout without installing entry points:

```bash
PYTHONPATH=src python -m shuheng
```

## Install The Shared Agent Gateway Skill

If other local agents should learn how to discover and message Shuheng agents,
install Shuheng's bundled shared skill:

```bash
shuheng install-agent-gateway-skill
```

By default this writes:

```text
~/.agents/skills/shuheng-agent-gateway/
```

The installed skill teaches only local stdio gateway usage. It does not expose
Shuheng contexts, ledgers, secrets, permission matrices, or private filesystem
paths.

Useful gateway checks:

```bash
shuheng-agent-gateway register
shuheng-agent-gateway agent-directory
shuheng-agent-gateway serve --stdio
```

## Local State

Shuheng keeps runtime state outside the source checkout:

```text
~/.shuheng/
~/.agents/skills/
```

For a clean fresh install, do not copy these directories. To migrate a trusted
existing machine, copy them only after `shuheng-check` passes on the new
machine. Treat Secret Vault material and machine-specific paths as local
operator state.

## Release Verification

Before cutting an alpha tag from a checkout, run:

```bash
python -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/dogfood_stdio_gateway.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_release_hygiene.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_policy_gates.py
PYTHONDONTWRITEBYTECODE=1 python scripts/dogfood_stdio_gateway.py
PYTHONDONTWRITEBYTECODE=1 python scripts/runtime_smoke.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
python -m compileall -q src scripts
python -m build --sdist --wheel --outdir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist
shuheng-check
git diff --check
```

The working tree should not show untracked local knowledge bases, runtime
state, secrets, or generated build artifacts before a public release.
