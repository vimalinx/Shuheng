"""Runtime and E2E evidence helpers for the Shuheng harness."""
from __future__ import annotations

from typing import Any, Optional


RUNTIME_EVIDENCE_SCHEMA = "agentruntime.evidence.v1"
RUNTIME_EVIDENCE_SUMMARY_SCHEMA = "agentruntime.evidence_summary.v1"
RUNTIME_EVIDENCE_LEVEL_RANK = {"unknown": 0, "structural": 1, "runtime": 2, "e2e": 3}
RUNTIME_EVIDENCE_LEVELS = frozenset(RUNTIME_EVIDENCE_LEVEL_RANK)


def runtime_evidence_level(level: str) -> str:
    level = str(level or "runtime")
    return level if level in RUNTIME_EVIDENCE_LEVELS else "unknown"


def runtime_evidence_targets(value: Any) -> list[str]:
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = []
    targets: list[str] = []
    for item in raw_items:
        text = str(item or "").strip()
        if text and text not in targets:
            targets.append(text)
    return targets


def build_runtime_evidence_record(
    *,
    evidence_id: str,
    timestamp: str,
    target_items: Any,
    check_id: str,
    level: str = "runtime",
    passed: bool = True,
    summary: str = "",
    source: str = "",
    command: str = "",
    evidence_refs: Optional[list[str]] = None,
    targets: Any = None,
    details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    item_targets = runtime_evidence_targets(target_items)
    check_targets = runtime_evidence_targets(targets) or list(item_targets)
    return {
        "schema_version": RUNTIME_EVIDENCE_SCHEMA,
        "evidence_id": str(evidence_id or ""),
        "timestamp": str(timestamp or ""),
        "target_items": item_targets,
        "targets": check_targets,
        "check_id": str(check_id or ""),
        "level": runtime_evidence_level(level),
        "passed": bool(passed),
        "summary": str(summary or ""),
        "source": str(source or ""),
        "command": str(command or ""),
        "evidence_refs": [str(ref) for ref in (evidence_refs or []) if str(ref)],
        "details": details or {},
    }


def runtime_evidence_records(
    rows: list[dict[str, Any]],
    target: str = "",
    *,
    passed: Optional[bool] = True,
    min_level: str = "runtime",
) -> list[dict[str, Any]]:
    min_rank = RUNTIME_EVIDENCE_LEVEL_RANK.get(runtime_evidence_level(min_level), 0)
    target = str(target or "").strip()
    records: list[dict[str, Any]] = []
    for row in rows:
        if row.get("schema_version") != RUNTIME_EVIDENCE_SCHEMA:
            continue
        if passed is not None and bool(row.get("passed")) is not bool(passed):
            continue
        level = runtime_evidence_level(str(row.get("level") or ""))
        if RUNTIME_EVIDENCE_LEVEL_RANK.get(level, 0) < min_rank:
            continue
        row_targets = set(runtime_evidence_targets(row.get("target_items")))
        row_targets.update(runtime_evidence_targets(row.get("targets")))
        if target and target not in row_targets:
            continue
        records.append(row)
    return records


def runtime_evidence_checks_for_records(rows: list[dict[str, Any]], *, limit: int = 3) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    slice_limit = max(0, int(limit))
    for row in (rows[-slice_limit:] if slice_limit else []):
        level = runtime_evidence_level(str(row.get("level") or ""))
        summary = str(row.get("summary") or row.get("check_id") or "runtime smoke passed")
        evidence_id = str(row.get("evidence_id") or "")
        source = str(row.get("source") or row.get("command") or "")
        suffix = f" ({evidence_id})" if evidence_id else ""
        if source:
            suffix = f"{suffix} via {source}"
        checks.append({
            "ok": True,
            "description": f"{level} evidence: {summary}{suffix}",
            "level": level,
        })
    return checks


def runtime_evidence_summary(path: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "schema_version": RUNTIME_EVIDENCE_SUMMARY_SCHEMA,
        "path": path,
        "total": 0,
        "passed": 0,
        "failed": 0,
        "levels": {level: 0 for level in ("structural", "runtime", "e2e", "unknown")},
        "targets": {},
    }
    for row in rows:
        if row.get("schema_version") != RUNTIME_EVIDENCE_SCHEMA:
            continue
        summary["total"] += 1
        if row.get("passed"):
            summary["passed"] += 1
        else:
            summary["failed"] += 1
        level = runtime_evidence_level(str(row.get("level") or ""))
        summary["levels"][level] += 1
        for target in runtime_evidence_targets(row.get("target_items")):
            target_summary = summary["targets"].setdefault(
                target,
                {"passed": 0, "failed": 0, "strongest_level": "unknown"},
            )
            if row.get("passed"):
                target_summary["passed"] += 1
                if RUNTIME_EVIDENCE_LEVEL_RANK[level] > RUNTIME_EVIDENCE_LEVEL_RANK[target_summary["strongest_level"]]:
                    target_summary["strongest_level"] = level
            else:
                target_summary["failed"] += 1
    return summary
