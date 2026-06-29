"""Tests for runtime/e2e evidence helper module."""
from __future__ import annotations

from ga_tui import runtime_evidence as re


def test_build_record_normalizes_targets_and_level() -> None:
    row = re.build_runtime_evidence_record(
        evidence_id="rtev_1",
        timestamp="2026-06-29T00:00:00+0800",
        target_items=["a2a_mcp_gateway", "a2a_mcp_gateway", ""],
        targets=None,
        check_id="smoke",
        level="e2e",
        summary="passed",
        evidence_refs=["task://1", ""],
    )

    assert row["schema_version"] == re.RUNTIME_EVIDENCE_SCHEMA
    assert row["target_items"] == ["a2a_mcp_gateway"]
    assert row["targets"] == ["a2a_mcp_gateway"]
    assert row["level"] == "e2e"
    assert row["evidence_refs"] == ["task://1"]


def test_records_filter_by_target_passed_and_min_level() -> None:
    rows = [
        re.build_runtime_evidence_record(
            evidence_id="struct",
            timestamp="t",
            target_items=["item"],
            check_id="struct",
            level="structural",
        ),
        re.build_runtime_evidence_record(
            evidence_id="runtime",
            timestamp="t",
            target_items=["item"],
            check_id="runtime",
            level="runtime",
        ),
        re.build_runtime_evidence_record(
            evidence_id="failed",
            timestamp="t",
            target_items=["item"],
            check_id="failed",
            level="e2e",
            passed=False,
        ),
    ]

    filtered = re.runtime_evidence_records(rows, "item", passed=True, min_level="runtime")

    assert [row["evidence_id"] for row in filtered] == ["runtime"]


def test_checks_and_summary_preserve_strongest_level() -> None:
    rows = [
        re.build_runtime_evidence_record(
            evidence_id="rtev_runtime",
            timestamp="t",
            target_items=["shared_ledgers"],
            check_id="runtime",
            level="runtime",
            summary="runtime smoke",
            source="test",
        ),
        re.build_runtime_evidence_record(
            evidence_id="rtev_e2e",
            timestamp="t",
            target_items=["shared_ledgers"],
            check_id="e2e",
            level="e2e",
            summary="e2e smoke",
            source="test",
        ),
    ]

    checks = re.runtime_evidence_checks_for_records(rows, limit=1)
    summary = re.runtime_evidence_summary("/tmp/runtime_evidence.jsonl", rows)

    assert checks[0]["level"] == "e2e"
    assert "e2e smoke" in checks[0]["description"]
    assert summary["passed"] == 2
    assert summary["targets"]["shared_ledgers"]["strongest_level"] == "e2e"
