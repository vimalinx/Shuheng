"""Release-readiness contracts for the Shuheng control plane.

This module is intentionally pure: it owns public release posture, baseline
evidence semantics, gateway safety wording, and heuristic eval scoring without
importing the large curses application module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


EVIDENCE_LEVELS = ("structural", "runtime", "e2e", "unknown")
EVIDENCE_LEVEL_DESCRIPTIONS = {
    "structural": "Code, schema, path, or registry shape exists.",
    "runtime": "The path is exercised by local runtime data or smoke checks.",
    "e2e": "An end-to-end behavior is verified through a client or task flow.",
    "unknown": "No reliable evidence level is available.",
}


def bounded_score(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 2)))


def evidence_check(ok: bool, description: str, level: str = "structural") -> dict[str, Any]:
    level = level if level in EVIDENCE_LEVELS else "unknown"
    return {"ok": bool(ok), "description": str(description), "level": level}


def normalize_evidence_checks(checks: Iterable[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for check in checks:
        if isinstance(check, dict):
            normalized.append(evidence_check(
                bool(check.get("ok")),
                str(check.get("description") or check.get("desc") or ""),
                str(check.get("level") or "structural"),
            ))
            continue
        if isinstance(check, (tuple, list)) and len(check) >= 2:
            level = str(check[2]) if len(check) >= 3 else "structural"
            normalized.append(evidence_check(bool(check[0]), str(check[1]), level))
            continue
        normalized.append(evidence_check(False, str(check), "unknown"))
    return normalized


def evidence_level_summary(checks: Iterable[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        level: {"passed": 0, "total": 0}
        for level in EVIDENCE_LEVELS
    }
    for check in checks:
        level = str(check.get("level") or "unknown")
        if level not in summary:
            level = "unknown"
        summary[level]["total"] += 1
        if check.get("ok"):
            summary[level]["passed"] += 1
    return summary


def strongest_passed_evidence_level(checks: Iterable[dict[str, Any]]) -> str:
    passed = {str(check.get("level") or "unknown") for check in checks if check.get("ok")}
    for level in ("e2e", "runtime", "structural"):
        if level in passed:
            return level
    return "unknown"


def baseline_claim_limit(strongest_level: str) -> str:
    if strongest_level == "e2e":
        return "End-to-end evidence exists for at least one completed check, but the item may still have uncovered edge cases."
    if strongest_level == "runtime":
        return "Runtime evidence exists, but this is not full protocol or product certification."
    if strongest_level == "structural":
        return "Structural evidence only: implementation shape exists, but behavior still needs runtime or end-to-end proof."
    return "No passing evidence is available."


@dataclass(frozen=True)
class HeuristicEvalInput:
    has_text: bool
    role: str
    max_tools: int
    tool_calls: int
    approval_count: int
    artifact_count: int
    artifact_recorded: bool


def heuristic_eval_assessment(data: HeuristicEvalInput) -> dict[str, Any]:
    max_tools = max(1, int(data.max_tools or 1))
    artifact_count = max(0, int(data.artifact_count or 0))
    tool_calls = max(0, int(data.tool_calls or 0))
    approval_count = max(0, int(data.approval_count or 0))
    has_artifact = artifact_count > 0
    has_text = bool(data.has_text)
    role = str(data.role or "")
    human_takeover_cost = bounded_score(min(1.0, approval_count / 3.0))
    policy_compliance = bounded_score(0.85 if approval_count and role in {"coder", "ops"} else 1.0)
    scores = {
        "completion": 1.0 if has_text else 0.0,
        "factual_accuracy": bounded_score(0.78 if has_artifact else (0.55 if has_text else 0.0)),
        "citation_accuracy": bounded_score(0.85 if has_artifact else 0.25),
        "source_quality": bounded_score(0.85 if has_artifact else 0.4),
        "tool_efficiency": bounded_score(1.0 - min(tool_calls / max_tools, 1.0) * 0.25),
        "policy_compliance": policy_compliance,
        "human_takeover_cost": human_takeover_cost,
        "evidence_quality": 0.85 if has_artifact else 0.45,
        "artifact_recorded": 1.0 if data.artifact_recorded else 0.0,
        "needs_review": 1.0 if approval_count or role in {"coder", "ops"} else 0.0,
    }
    return {
        "schema_version": "shuheng.heuristic_eval.v1",
        "method": "heuristic",
        "scores": scores,
        "policy_compliance": policy_compliance,
        "human_takeover_cost": human_takeover_cost,
        "basis": {
            "has_text": has_text,
            "artifact_count": artifact_count,
            "tool_calls": tool_calls,
            "max_tools": max_tools,
            "approval_count": approval_count,
            "role": role,
        },
        "limitations": [
            "Scores are inferred from task text, artifact refs, tool counts, and approval refs.",
            "Factual and citation accuracy are not independently verified by this heuristic.",
            "Use verifier/reviewer tasks or end-to-end tests for authoritative quality claims.",
        ],
    }


def is_loopback_host(host: str) -> bool:
    host = str(host or "").strip().lower()
    return host in {"", "127.0.0.1", "localhost", "::1"}


def gateway_bind_safety(host: str, *, allow_remote: bool = False) -> dict[str, Any]:
    host = str(host or "127.0.0.1").strip() or "127.0.0.1"
    local_only = is_loopback_host(host)
    allowed = local_only or bool(allow_remote)
    return {
        "schema_version": "shuheng.gateway_bind_safety.v1",
        "host": host,
        "local_only": local_only,
        "auth": "none",
        "allowed": allowed,
        "reason": "loopback_default" if local_only else ("remote_allowed_by_env" if allow_remote else "remote_bind_requires_GA_TUI_GATEWAY_ALLOW_REMOTE_BIND"),
        "operator_note": "Gateway/Web Console has no built-in authentication; bind to loopback unless protected by a trusted external boundary.",
    }


def protocol_compatibility_metadata(kind: str) -> dict[str, Any]:
    kind = str(kind or "gateway")
    return {
        "posture": "compatibility_surface",
        "certification": "not_protocol_certified",
        "evidence_required_for_certified": [
            "real third-party client interoperability test",
            "request/response conformance fixture",
            "streaming/push behavior fixture",
        ],
        "wording": f"{kind} exposes Shuheng-compatible registry and HTTP surfaces; do not treat it as certified full protocol compliance.",
    }


def scheduler_runtime_ownership() -> dict[str, Any]:
    return {
        "owner": "ga-tui.control_plane",
        "tick_owner": "tui_loop_or_gateway_manual_action",
        "always_on": False,
        "daemon_note": "Recurring jobs are evaluated while the TUI loop runs or when a gateway/manual scheduler action invokes a tick; no external system service is installed by default.",
    }


def distribution_smoke_contract() -> dict[str, Any]:
    return {
        "schema_version": "shuheng.distribution_smoke.v1",
        "command": "python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist",
        "artifacts": ["wheel", "sdist"],
        "install_mode": "with_dependencies",
        "public_console_scripts": [
            "shuheng",
            "shuheng-agent-bridge",
            "shuheng-check",
            "shuheng-install-core-shim",
            "shuheng-integration",
        ],
        "checks": [
            "sdist archive public/private member contract",
            "public console scripts exist",
            "shuheng --help",
            "helper --help entrypoints",
            "python -m ga_tui.integration doctor",
            "shuheng-check against isolated GenericAgent stub",
        ],
        "debug_options_not_release_gates": ["--no-deps", "--wheel-only"],
    }


def release_readiness_report(
    *,
    app_py_lines: int = 0,
    has_license: bool = False,
    has_ci: bool = False,
    has_security_policy: bool = False,
) -> dict[str, Any]:
    known_gaps = [
        "app.py remains a large composition module and is not fully decomposed",
        "A2A/MCP surfaces need real third-party client conformance tests before certification language",
        "heuristic eval does not prove factual or citation correctness",
        "gateway has no built-in authentication and should stay loopback by default",
        "scheduler is runtime-owned rather than an installed always-on service",
    ]
    missing_hygiene = []
    if not has_license:
        missing_hygiene.append("LICENSE")
    if not has_ci:
        missing_hygiene.append("CI")
    if not has_security_policy:
        missing_hygiene.append("SECURITY.md")
    if missing_hygiene:
        known_gaps.append("repository-level open-source hygiene still missing: " + ", ".join(missing_hygiene))
    return {
        "schema_version": "shuheng.release_readiness.v1",
        "status": "experimental_alpha",
        "public_position": "local-first governed agent TUI with experimental gateway/protocol surfaces",
        "support_level": {
            "stable_local_surfaces": [
                "curses TUI session workspace",
                "local task ledger and agent mail inspection",
                "local artifact/index inspection",
                "Secret Vault local encryption flow",
                "runtime provider registry metadata",
            ],
            "experimental_surfaces": [
                "Web Console and HTTP gateway",
                "A2A compatibility surface",
                "MCP compatibility surface",
                "architecture baseline comparison",
                "heuristic eval and trace quality scoring",
                "scheduler runtime dispatch",
            ],
            "known_gaps": known_gaps,
        },
        "monolith_risk": {
            "app_py_lines": int(app_py_lines or 0),
            "status": "known_gap" if int(app_py_lines or 0) > 5000 else "bounded",
            "note": "Large stateful UI/runtime code should be extracted incrementally with tests.",
        },
        "repository_hygiene": {
            "license": bool(has_license),
            "ci": bool(has_ci),
            "security_policy": bool(has_security_policy),
        },
        "distribution_smoke": distribution_smoke_contract(),
        "verification_commands": [
            "python3 -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/runtime_smoke.py scripts/wheel_smoke.py",
            "python3 scripts/check_release_hygiene.py",
            "python3 -m pytest -q -p no:cacheprovider",
            "python3 scripts/check_policy_gates.py",
            "python3 scripts/runtime_smoke.py",
            "python3 -m compileall -q src scripts",
            "python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist",
            "python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist",
            "shuheng-check",
            "git diff --check",
        ],
    }
