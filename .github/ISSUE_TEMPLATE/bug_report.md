---
name: Bug report
about: Report a reproducible Shuheng problem
title: "[bug] "
labels: bug
assignees: ""
---

## Summary

Describe the visible problem and what you expected instead.

## Environment

- Shuheng version or commit:
- OMP version (`omp --version`), if runtime-related:
- Python version:
- OS and terminal:
- Install mode: source editable / wheel / sdist / other
- Extra runtime checkout configured: yes / no / not relevant

## Reproduction

```text
1.
2.
3.
```

## Evidence

Paste relevant command output, screenshots, or logs. Redact secrets, local model
credentials, normal session logs, and Secret Vault content.

## Checks Already Run

```bash
shuheng-check
PYTHONDONTWRITEBYTECODE=1 python scripts/runtime_smoke.py
```

## Security Or Data Exposure

Did this involve secrets, local files, network access, deletion, executable
Tools, permission escalation, or other external side effects? For sensitive
details, use private vulnerability reporting instead of this public issue.
