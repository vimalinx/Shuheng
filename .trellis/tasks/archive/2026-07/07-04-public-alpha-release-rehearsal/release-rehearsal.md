# Shuheng 0.1.0 Public Alpha Release Rehearsal

Date: 2026-07-04

## Scope

This is a local release rehearsal for the Shuheng `0.1.0` public alpha
candidate. It proves the local package build, artifact boundaries, fresh-user
install path, and release-note wording without publishing externally.

No tags were created. No artifacts were uploaded. No PyPI/TestPyPI publication
was attempted.

## Candidate

- Package: `shuheng`
- Version: `0.1.0`
- Release posture: experimental local alpha
- Artifact directory: `/tmp/shuheng-dist`

## Artifacts

```text
06cb9f99de89b098e5e53542795d243cc54d74a47ac3af9e1663c36ab04d6276  /tmp/shuheng-dist/shuheng-0.1.0-py3-none-any.whl
a15096401c5d70c781d745a6890e542e24357ce7f70660e51ad25b516d097875  /tmp/shuheng-dist/shuheng-0.1.0.tar.gz
```

These checksums are for the Python wheel/sdist generated in `/tmp/shuheng-dist`.
They are not checksums for a GitHub source archive.

## Verification Results

All commands below passed during the rehearsal:

```bash
python3 -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_release_hygiene.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/runtime_smoke.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
python3 -m compileall -q src scripts
python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist
shuheng-check
git diff --check
```

Observed results:

- Full pytest: `565 passed`.
- Runtime smoke wrote six evidence rows and reported strongest evidence levels:
  `e2e: 10`, `runtime: 1`, `structural: 2`, `unknown: 0`.
- Wheel smoke passed for both wheel and sdist.
- Wheel smoke found zero forbidden archive members and zero artifact content
  leaks.
- Wheel `RECORD` verification passed with 43 record rows and 42 verified
  non-`RECORD` members.
- Sdist verification passed with 94 archive members and 92 manifest rows.
- `shuheng-check` reported `Status: OK` against
  `/home/vimalinx/Programs/GenericAgent`.

## Fresh-User Install Smoke

The built wheel was installed into a temporary venv with clean `HOME` and
`SHUHENG_HOME`, plus a minimal fake GenericAgent root that satisfied the
documented doctor interface.

Observed result:

```text
help=usage: shuheng [-h] [--serve-gateway]
module_help=usage: python -m ga_tui [-h] [--serve-gateway]
doctor_status=Status: OK
```

This proves the public `--help` path and integration doctor path do not depend
on the maintainer's normal `~/.shuheng` state.

## Architecture Baseline Comparison

This rehearsal moves the system closer to `docs/agent-harness-architecture.md`
because it strengthens release evidence, artifact provenance, and human-visible
approval/release boundaries without adding ungoverned agent autonomy.

Relevant baseline alignment:

- Strong Orchestrator remains unchanged; no runtime orchestration behavior was
  modified.
- No worker/subagent write boundary was loosened.
- Artifacts are referenced by path and SHA256 checksum instead of committed into
  the repository.
- No publish, deploy, tag, or upload side effect was performed automatically.
- Public wording still says A2A/MCP are compatibility surfaces, not certified
  protocol implementations.
- Gateway/Web Console remain documented as no-built-in-auth and loopback-first.

Remaining baseline gaps are unchanged:

- `app.py` is still a large composition module.
- Remote gateway authentication is not built in.
- A2A/MCP conformance still needs third-party client fixtures.
- Heuristic eval still does not prove factual or citation correctness.

## GitHub Release Draft

Title:

```text
Shuheng 0.1.0 - Experimental Local Alpha
```

Tag:

```text
v0.1.0
```

Body:

~~~markdown
## Shuheng 0.1.0 - Experimental Local Alpha

Shuheng is a local-first governed terminal control plane for local agents. This
public alpha focuses on the local curses TUI, sessions, task ledgers, artifacts,
approvals, Secret Vault, runtime provider metadata, plugin/workflow surfaces,
and GenericAgent integration checks.

### Release posture

This is an experimental local alpha. Web Console, HTTP gateway, A2A/MCP
compatibility surfaces, baseline reports, heuristic eval/trace scoring, workflow
automation, and scheduler dispatch are not production-ready remote services and
are not certified protocol implementations.

Gateway/Web Console has no built-in authentication and should stay loopback
unless protected by a trusted external boundary.

### Artifacts

- `shuheng-0.1.0-py3-none-any.whl`
- `shuheng-0.1.0.tar.gz`

SHA256:

```text
06cb9f99de89b098e5e53542795d243cc54d74a47ac3af9e1663c36ab04d6276  shuheng-0.1.0-py3-none-any.whl
a15096401c5d70c781d745a6890e542e24357ce7f70660e51ad25b516d097875  shuheng-0.1.0.tar.gz
```

### Fresh install smoke

```bash
python -m venv .venv
. .venv/bin/activate
pip install shuheng-0.1.0-py3-none-any.whl
shuheng --help
```

Launching the TUI or running `shuheng-check` requires a valid GenericAgent root
through discovery, `GENERICAGENT_ROOT`, or `GA_ROOT`.

### Verified checks

- Ruff
- Release hygiene
- Runtime smoke
- Policy gates
- Full pytest
- Compileall
- Wheel/sdist build
- Wheel/sdist smoke and leak scan
- `shuheng-check`
- `git diff --check`

### Known gaps

- `src/ga_tui/app.py` remains a large composition module.
- Gateway/Web Console has no built-in auth.
- A2A/MCP surfaces are compatibility surfaces, not certified implementations.
- Heuristic eval/trace scoring does not prove factual or citation correctness.
- Scheduler/workflow automation remains runtime-owned, not an installed
  always-on service.
~~~
