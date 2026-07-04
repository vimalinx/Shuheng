# Public Alpha Readiness

This document records the release-facing decisions that are easy to miss when
looking at the repository from a fresh public clone.

## Release Position

Shuheng is a public alpha for local-first agent control-plane work. The supported
claim is:

> experimental local alpha: stable local TUI/control-plane surfaces with
> experimental gateway, protocol, scheduler, workflow, baseline, and eval
> surfaces.

Do not describe the project as production-ready, remotely secured, or fully
A2A/MCP certified unless the repository later adds the required external
conformance evidence.

## Verified Release Gate

Before cutting a public alpha tag, run the same commands as CI and
`CONTRIBUTING.md`:

```bash
python -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_release_hygiene.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_policy_gates.py
PYTHONDONTWRITEBYTECODE=1 python scripts/runtime_smoke.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
python -m compileall -q src scripts
python -m build --sdist --wheel --outdir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist
git diff --check
```

Also run `shuheng-check` in the target checkout. A GenericAgent checkout is only
needed when validating the optional legacy provider or launcher shim.

## Trellis Repository State

The tracked `.trellis/` tree is project development metadata, not Shuheng
runtime state and not part of the Python source distribution.

The current public-alpha decision is:

- Keep `.trellis/spec/`, `.trellis/workflow.md`, `.trellis/scripts/`, and task
  records in the source repository because they explain the governed development
  process and preserve implementation provenance.
- Keep `.trellis/.runtime/`, `.trellis/.cache/`, `.trellis/.developer`,
  template hashes, backups, and worktrees ignored.
- Keep `.trellis` pruned from sdist/wheel artifacts through `MANIFEST.in`.
- Do not bulk-delete or bulk-archive task directories only to make the GitHub
  tree look smaller. A task directory is a development ledger entry; cleanup
  should be explicit and reviewable.

Some task directories may show `in_progress` while representing older local
workflow state. Treat them as development ledger records, not product features
or release promises.

## Public Alpha Known Gaps

- `src/ga_tui/app.py` remains a large composition module and should continue to
  shrink through small helper extractions with compatibility aliases.
- Gateway/Web Console has no built-in authentication and should bind to loopback
  unless protected by an external trusted boundary.
- A2A/MCP surfaces are compatibility surfaces, not certified protocol
  implementations.
- Heuristic eval and trace scoring do not prove factual or citation correctness.
- Scheduler/workflow automation is runtime-owned, not an installed always-on
  service by default.

## Fresh Clone Expectations

A new contributor should be able to:

1. Create a virtual environment.
2. Install `.[dev]`.
3. Run `shuheng --help` before configuring any optional legacy provider.
4. Run `shuheng-check` or `python -m ga_tui.integration doctor` without a
   GenericAgent checkout.
5. Optionally set `GENERICAGENT_ROOT` or `GA_ROOT` to validate the legacy
   GenericAgent provider / shim path.
6. Run the release hygiene and runtime smoke checks without maintainer-local
   state.

If one of those steps requires local secrets, normal session history, or a
maintainer-specific path, treat that as a release blocker.
