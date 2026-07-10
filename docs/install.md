# Fresh Machine Setup

This guide is the public alpha installation contract for Shuheng.

## Support Matrix

| Platform | Status | Notes |
| --- | --- | --- |
| Linux | Supported alpha target | The package metadata declares POSIX Linux and the main UI is Python `curses`. |
| Windows via WSL2 | Recommended Windows path | Install an Ubuntu WSL2 environment and follow the Linux steps inside WSL. |
| macOS | Best effort, unverified | It may work in a compatible terminal, but there is no macOS CI or release gate yet. |
| Windows native | Unsupported | Native Windows terminals do not provide the same `curses`/POSIX behavior expected by the current TUI. |

Do not describe this release as production-ready, network-service hardened, or fully
cross-platform. The supported claim is experimental local alpha.

## Requirements

- Python 3.10 or newer.
- A POSIX shell environment.
- A terminal that supports Python `curses`.
- [Bun](https://bun.sh/) 1.3.14 or newer for the permanent OMP main runtime.
- Network access for the Python package and the pinned
  `@oh-my-pi/pi-coding-agent@16.1.7` runtime unless already cached.
- Optional Pi-native workers require Node.js 22.19 or newer plus npm.

## Recommended Alpha Install

The public alpha installer creates an isolated virtual environment under
`$HOME/.local/share/shuheng`, installs launchers into `$HOME/.local/bin`,
installs or verifies the pinned OMP runtime, installs the shared local agent
gateway skill, then runs `shuheng-check`. If Bun or OMP setup is unavailable,
the installer stops with an actionable non-zero result; it never reports a
usable main Agent while OMP is missing.

```bash
curl -fsSL https://raw.githubusercontent.com/vimalinx/Shuheng/main/scripts/install.sh | sh
```

If you prefer to inspect the script before running it:

```bash
curl -fsSL -o /tmp/shuheng-install.sh https://raw.githubusercontent.com/vimalinx/Shuheng/main/scripts/install.sh
sh /tmp/shuheng-install.sh
```

Useful options:

```bash
sh /tmp/shuheng-install.sh --help
sh /tmp/shuheng-install.sh --dry-run
sh /tmp/shuheng-install.sh --prefix "$HOME/.local/share/shuheng" --bin-dir "$HOME/.local/bin"
sh /tmp/shuheng-install.sh --skip-agent-gateway-skill
```

The installer supports Linux, Windows via WSL2, and best-effort macOS. It rejects
native Windows shells and points users to WSL2.

Verify the installed release and runtime:

```bash
shuheng --version
shuheng runtime check
shuheng-check
```

`shuheng-check --package-only` exists only for isolated artifact debugging. It
does not prove that an installation can run its main Agent.

## Install From Source

```bash
git clone <shuheng-repository-url>
cd Shuheng

python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
shuheng runtime setup-omp
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

The same installer can install a local checkout for development smoke tests:

```bash
sh scripts/install.sh --source . --editable --skip-agent-gateway-skill
```

## Runtime Setup

OMP is required and remains Shuheng's permanent main Agent:

```bash
shuheng runtime setup-omp
shuheng runtime check
```

The setup command installs the pinned OMP package through Bun when OMP is
missing, then verifies the pinned versions and a real RPC ready/state round
trip. It does not silently replace an existing unsupported OMP version.
After reviewing the impact on other local OMP workflows, replacement must be
explicit:

```bash
shuheng runtime setup-omp --replace
```

Pi-native Agent Projects are optional. Install their locked SDK beside the
packaged sidecar with:

```bash
shuheng runtime setup-pi
shuheng runtime check --require-pi
```

This runs `npm ci` against the shipped lockfile and verifies a live sidecar
health response. It does not make project-local executable Tools an OS sandbox.

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

Model configuration is stored at `~/.shuheng/config/mykey.py`. Shuheng enforces
mode `0700` on its private configuration directory and `0600` on the config,
temporary files, and backups. A pre-release source-root `mykey.py` is migrated
once and is never retained as an active lookup path.

OMP starts with the governed `standard` permission profile and `write` approval
mode. Broad host access is an expert opt-in:

```bash
export SHUHENG_OMP_PERMISSION_PROFILE=full
export SHUHENG_OMP_APPROVAL_MODE=yolo
```

Both variables are required for prompt-free broad authority. `yolo` without
`full` is downgraded to `write`; `full + write/always-ask` retains Shuheng's
program-level high-risk action gate. In prompted full mode only bounded local
edit/write Tools may be auto-admitted; shell, browser, eval, task, and unknown
Tools fail closed.

OMP inherits a narrow environment by default. If it needs an enterprise CA,
proxy, or another named value, opt in to the exact variable names:

```bash
export SHUHENG_OMP_INHERIT_ENV=HTTPS_PROXY,NODE_EXTRA_CA_CERTS
```

Any explicitly inherited value becomes visible to the OMP process and its
Tools, so do not add unrelated cloud, SSH, or application credentials.

For a clean fresh install, do not copy these directories. To migrate a trusted
existing machine, copy them only after `shuheng-check` passes on the new
machine. Treat Secret Vault material and machine-specific paths as local
operator state.

## Upgrade

Re-run the inspected installer to upgrade. The `0.2.0a1` package version is
newer than the original public package's `0.1.0`, so ordinary pip upgrade
semantics apply without `--force-reinstall`:

```bash
sh /tmp/shuheng-install.sh --version v0.2.0-alpha.1
shuheng --version
shuheng-check
```

Back up trusted `~/.shuheng` state before changing pre-release versions.

## Uninstall

The default installer is user-local. Remove its launchers and venv with:

```bash
rm -f "$HOME/.local/bin/shuheng" \
      "$HOME/.local/bin/shuheng-agent-bridge" \
      "$HOME/.local/bin/shuheng-agent-gateway" \
      "$HOME/.local/bin/shuheng-check" \
      "$HOME/.local/bin/shuheng-install-core-shim" \
      "$HOME/.local/bin/shuheng-integration"
rm -rf "$HOME/.local/share/shuheng"
```

OMP is a separately installed shared runtime. Do not remove it unless no other
workflow needs it. Runtime state and the shared gateway skill are also preserved
by default; after reviewing/backing them up, they may be removed separately:

```bash
rm -rf "$HOME/.shuheng"
rm -rf "$HOME/.agents/skills/shuheng-agent-gateway"
```

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
npm ci --ignore-scripts --prefix integrations/pi-native-sidecar
node --check integrations/pi-native-sidecar/sidecar.mjs
python -m build --sdist --wheel --outdir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist --upgrade-from-alpha1
shuheng-check
git diff --check
```

The working tree should not show untracked local knowledge bases, runtime
state, secrets, or generated build artifacts before a public release.
