"""Architecture baseline report item helpers."""
from __future__ import annotations

from typing import Any, Optional

try:
    from .release_readiness import (
        baseline_claim_limit,
        evidence_level_summary,
        normalize_evidence_checks,
        strongest_passed_evidence_level,
    )
except Exception:
    from release_readiness import (  # type: ignore
        baseline_claim_limit,
        evidence_level_summary,
        normalize_evidence_checks,
        strongest_passed_evidence_level,
    )


def baseline_status(pass_count: int, required_count: int) -> str:
    if required_count <= 0:
        return "missing"
    if pass_count >= required_count:
        return "complete"
    if pass_count > 0:
        return "partial"
    return "missing"


def baseline_item(
    item_id: str,
    title: str,
    requirement: str,
    checks: list[Any],
    *,
    gaps: Optional[list[str]] = None,
    notes: str = "",
) -> dict[str, Any]:
    normalized_checks = normalize_evidence_checks(checks)
    pass_count = sum(1 for check in normalized_checks if check.get("ok"))
    status = baseline_status(pass_count, len(normalized_checks))
    failed = [str(check.get("description") or "") for check in normalized_checks if not check.get("ok")]
    strongest_level = strongest_passed_evidence_level(normalized_checks)
    return {
        "id": item_id,
        "title": title,
        "requirement": requirement,
        "status": status,
        "pass_count": pass_count,
        "check_count": len(normalized_checks),
        "evidence": [str(check.get("description") or "") for check in normalized_checks if check.get("ok")],
        "evidence_checks": normalized_checks,
        "evidence_levels": evidence_level_summary(normalized_checks),
        "strongest_evidence_level": strongest_level,
        "claim_limit": baseline_claim_limit(strongest_level),
        "missing_evidence": failed,
        "gaps": gaps or failed,
        "notes": notes,
    }


def format_baseline_report(report: dict[str, Any], *, report_path: str, max_items: int = 20) -> str:
    summary = report.get("summary") or {}
    lines = [
        "Architecture Baseline Comparison",
        f"complete={summary.get('complete', 0)} partial={summary.get('partial', 0)} missing={summary.get('missing', 0)} ratio={summary.get('completion_ratio', 0)}",
        "",
        "Items:",
    ]
    for item in (report.get("items") or [])[:max_items]:
        lines.append(
            f"- [{item.get('status', '-')}/{item.get('strongest_evidence_level', 'unknown')}] "
            f"{item.get('id', '')}: {item.get('title', '')}"
        )
        for gap in (item.get("gaps") or [])[:3]:
            lines.append(f"  gap: {gap}")
    gaps = report.get("remaining_gaps") or []
    lines.extend(["", f"Remaining gap groups: {len(gaps)}", f"Report path: {report_path}"])
    return "\n".join(lines)
