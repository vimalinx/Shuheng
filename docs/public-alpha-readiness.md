# Public Alpha Readiness

This document records the release-facing decisions that are easy to miss when
looking at the repository from a fresh public clone.

## Release Position

Shuheng is a public alpha for local-first agent control-plane work. The supported
claim is:

> experimental local alpha: stable local TUI/control-plane surfaces with
> stable OMP runtime output/control, a local JSONL stdio gateway, and
> experimental local scheduler, workflow, baseline, eval, and protocol-shaped
> registry records.

Do not describe the project as production-ready, network-service hardened, or fully
A2A/MCP certified. Current A2A/MCP-shaped data is local metadata only, not a
reachable protocol service.

## Verified Release Gate

Before cutting a public alpha tag, run the same commands as CI and
`CONTRIBUTING.md`:

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
git diff --check
```

Also run `shuheng --version`, `shuheng runtime check`, and `shuheng-check` in
the target checkout. `--package-only` is an artifact/debug escape hatch and is
not runtime-readiness evidence.

The fresh-machine install and platform support contract lives in
[`docs/install.md`](install.md). The release support claim is Linux-first
experimental local alpha; Windows users should use WSL2, macOS is best-effort
until covered by CI or real terminal smoke verification, and native Windows is
not supported by the curses TUI.

## Maintainer Workflow State

Maintainer agent-framework state is not part of Shuheng's public source or
runtime contract. `.trellis/`, generated `.agents/`, `.claude/`, and `.codex/`
remain local and ignored. They must not enter Git, wheel, or sdist artifacts.

Contributor-facing Shuheng contracts live under [`docs/development/`](development/)
and the architecture baseline remains
[`docs/agent-harness-architecture.md`](agent-harness-architecture.md). This keeps
the public MIT boundary independent from whichever local workflow framework a
maintainer chooses to use.

## Public Alpha Known Gaps

- `src/shuheng/app.py` remains a large composition module and should continue to
  shrink through small helper extractions with compatibility aliases.
- A2A/MCP-shaped records are local metadata only, not certified protocol
  implementations or reachable endpoints.
- Heuristic eval and trace scoring do not prove factual or citation correctness.
- Scheduler/workflow automation is runtime-owned, not an installed always-on
  service by default.
- Pi-native custom Tools are trusted local code and are not an OS sandbox.
- OMP full/yolo host access is an explicit operator opt-in, not the public
  default safety posture.

## Fresh Clone Expectations

A new contributor should be able to:

1. Create a virtual environment.
2. Install `.[dev]`.
3. Follow `docs/install.md` for supported platform expectations.
4. Run `shuheng --help` and `shuheng --version` before configuring models.
5. Run `shuheng-check` or `python -m shuheng.integration doctor`; the command
   must verify OMP or return an actionable non-zero missing-runtime result.
6. Run the release hygiene and runtime smoke checks without maintainer-local
   state.

If one of those steps requires local secrets, normal session history, or a
maintainer-specific path, treat that as a release blocker.
