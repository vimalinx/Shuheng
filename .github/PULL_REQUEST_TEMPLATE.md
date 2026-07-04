## Summary

Describe the change and why it is needed.

## Release Posture

- [ ] This preserves the experimental local alpha wording.
- [ ] This does not claim production readiness or certified A2A/MCP support.
- [ ] Gateway/Web Console changes preserve loopback-first/no-built-in-auth wording.

## Architecture Baseline

If this touches TUI, subagents, ledgers, approvals, memory, artifacts, recovery,
eval/trace, A2A/MCP, scheduler/workflows, or orchestration:

- [ ] Compared against `docs/agent-harness-architecture.md`.
- [ ] Strong Orchestrator ownership is preserved.
- [ ] Worker/subagent write boundaries and approval gates are preserved.
- [ ] Artifact/provenance/audit behavior is preserved or improved.

## Checks

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

## Notes

Mention any known alpha limitations, skipped checks, or follow-up work.
