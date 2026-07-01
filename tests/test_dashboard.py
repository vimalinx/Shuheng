"""Tests for pure dashboard schema helpers."""
from __future__ import annotations

from ga_tui import app as app_module
from ga_tui import dashboard


class Unserializable:
    def __str__(self) -> str:
        return "unserializable-dashboard"


def test_normalize_dashboard_sections_filters_and_bounds() -> None:
    sections = dashboard.normalize_dashboard_sections(
        [
            "function",
            {"section": "markdown", "label": "Notes", "body": "body"},
            {"type": "unsupported", "title": "drop"},
            {"type": "todos", "title": "T" * 120, "markdown": "M" * 4000},
            123,
        ]
    )

    assert [row["type"] for row in sections] == ["function", "markdown", "todos"]
    assert sections[0] == {"type": "function", "title": "function"}
    assert sections[1] == {"type": "markdown", "title": "Notes", "markdown": "body"}
    assert len(sections[2]["title"]) == 80
    assert len(sections[2]["markdown"]) == 3000


def test_normalize_dashboard_spec_payload_shape_and_bounds() -> None:
    payload = dashboard.normalize_dashboard_spec_payload(
        {
            "task_id": "task_dashboard",
            "artifact_refs": [f"artifact://{idx}" for idx in range(14)] + [""],
            "dashboard": {
                "sections": ["function", {"type": "markdown", "body": "Visible"}],
                "status": "ready",
                "todos": [
                    {"title": "first"},
                    {"task": "second"},
                    "third",
                    {"missing": "ignored"},
                ],
                "markdown": "M" * 6000,
            },
        },
        source="control",
        target="orchestrator.main",
    )

    assert payload["schema_version"] == "dashboard.v1"
    assert payload["updated_at"]
    assert payload["source"] == "control"
    assert payload["target"] == "orchestrator.main"
    assert payload["provenance"]["task_id"] == "task_dashboard"
    assert payload["provenance"]["artifact_refs"] == [f"artifact://{idx}" for idx in range(12)]
    assert payload["sections"] == [
        {"type": "function", "title": "function"},
        {"type": "markdown", "title": "markdown", "markdown": "Visible"},
    ]
    assert payload["status_narrative"] == "ready"
    assert payload["todos"] == ["first", "second", "third"]
    assert len(payload["markdown"]) == 5000


def test_dashboard_cache_signature_is_stable_and_safe() -> None:
    first = dashboard.dashboard_cache_signature({"b": 2, "a": 1})
    second = dashboard.dashboard_cache_signature({"a": 1, "b": 2})

    assert first == second == '{"a":1,"b":2}'
    assert dashboard.dashboard_cache_signature({}) == ""
    assert dashboard.dashboard_cache_signature(Unserializable()) == "unserializable-dashboard"


def test_app_dashboard_wrappers_match_module() -> None:
    assert app_module.SUPPORTED_DASHBOARD_SECTIONS is dashboard.SUPPORTED_DASHBOARD_SECTIONS
    assert app_module.DEFAULT_DASHBOARD_SECTIONS is dashboard.DEFAULT_DASHBOARD_SECTIONS
    assert app_module.DEFAULT_SUBAGENT_DASHBOARD_SECTIONS is dashboard.DEFAULT_SUBAGENT_DASHBOARD_SECTIONS
    assert app_module.bounded_dashboard_text is dashboard.bounded_dashboard_text
    assert app_module.normalize_dashboard_sections is dashboard.normalize_dashboard_sections
    assert app_module.normalize_dashboard_spec_payload is dashboard.normalize_dashboard_spec_payload
    assert app_module.dashboard_cache_signature is dashboard.dashboard_cache_signature
