## Summary

Describe the change and why it is needed.

## Release Posture

- [ ] This preserves the experimental local alpha wording.
- [ ] This does not claim production readiness or certified A2A/MCP support.
- [ ] This does not introduce a built-in network service; the supported gateway
      remains local JSONL stdio.

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
npm ci --ignore-scripts --prefix integrations/pi-native-sidecar
node --check integrations/pi-native-sidecar/sidecar.mjs
python -m build --sdist --wheel --outdir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist
git diff --check
```

## Notes

Mention any known alpha limitations, skipped checks, or follow-up work.
