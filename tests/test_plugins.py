from __future__ import annotations

import json
from pathlib import Path

from ga_tui import plugins


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_discover_plugins_resolves_manifest_declared_skills_and_templates(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugins" / "research-pack"
    skill_path = plugin_root / "skills" / "source-review" / "SKILL.md"
    workflow_path = plugin_root / "workflows" / "compare-sources.md"
    skill_path.parent.mkdir(parents=True)
    workflow_path.parent.mkdir(parents=True)
    skill_path.write_text("# Source Review\n", encoding="utf-8")
    workflow_path.write_text("# Compare Sources\n", encoding="utf-8")
    write_json(
        plugin_root / "plugin.json",
        {
            "schema_version": "shuheng.plugin.v1",
            "id": "research-pack",
            "name": "Research Pack",
            "version": "0.1.0",
            "description": "Reusable research agents and SOPs.",
            "contributes": {
                "skills": [
                    {
                        "id": "source-review",
                        "name": "Source Review",
                        "description": "Review source quality.",
                        "path": "skills/source-review/SKILL.md",
                    }
                ],
                "agent_templates": [
                    {
                        "id": "evidence-researcher",
                        "name": "Evidence Researcher",
                        "role": "researcher",
                        "profile": "Collect evidence.",
                        "skills": ["source-review"],
                    }
                ],
                "workflows": [{"id": "compare-sources", "path": "workflows/compare-sources.md"}],
            },
            "permissions": {"requested_tools": ["read"], "write_policy": "none"},
        },
    )

    registry = plugins.discover_plugins([str(tmp_path / "plugins")])

    assert not registry.issues
    plugin = registry.plugins["research-pack"]
    assert plugin.name == "Research Pack"
    assert plugin.skills[0].ref == "plugin://research-pack/skills/source-review"
    assert plugins.plugin_skill_file_for_ref("plugin://research-pack/skills/source-review", registry) == str(skill_path)
    assert plugins.plugin_skill_display_name("plugin://research-pack/skills/source-review", registry) == (
        "Research Pack/Source Review"
    )
    template = plugins.plugin_agent_template_for_ref("research-pack/evidence-researcher", registry)
    assert template is not None
    assert template.ref == "plugin://research-pack/agents/evidence-researcher"
    assert template.skill_refs == ("plugin://research-pack/skills/source-review",)
    assert "Research Pack" in plugins.format_plugin_list(registry)
    assert "plugin://research-pack/agents/evidence-researcher" in plugins.format_plugin_info("research-pack", registry)


def test_discover_plugins_reports_invalid_paths_without_resolving_outside_files(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugins" / "bad-pack"
    plugin_root.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("outside marker", encoding="utf-8")
    write_json(
        plugin_root / "plugin.json",
        {
            "schema_version": "shuheng.plugin.v1",
            "id": "bad-pack",
            "name": "Bad Pack",
            "contributes": {
                "skills": [
                    {"id": "outside", "path": "../outside.md"},
                    {"id": "missing", "path": "skills/missing/SKILL.md"},
                ]
            },
        },
    )

    registry = plugins.discover_plugins([str(tmp_path / "plugins")])

    assert "bad-pack" in registry.plugins
    assert plugins.plugin_skill_file_for_ref("plugin://bad-pack/skills/outside", registry) == ""
    assert plugins.plugin_skill_file_for_ref("plugin://bad-pack/skills/missing", registry) == ""
    assert any("inside the plugin root" in issue.message for issue in registry.issues)
    assert any("does not exist" in issue.message for issue in registry.issues)


def test_plugin_ref_parsing_and_roots_are_stable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SHUHENG_HOME", str(tmp_path / "home"))

    assert plugins.plugin_roots() == [str(tmp_path / "home" / "plugins")]
    assert plugins.plugin_roots(str(tmp_path), str(tmp_path)) == [str(tmp_path)]
    assert plugins.plugin_skill_ref("research-pack", "source-review") == "plugin://research-pack/skills/source-review"
    assert plugins.plugin_skill_ref("bad/id", "source-review") == ""
    assert plugins.plugin_skill_ref_from_token("research-pack/source-review") == "plugin://research-pack/skills/source-review"
    assert plugins.plugin_skill_ref_from_token("research-pack/skills/source-review") == (
        "plugin://research-pack/skills/source-review"
    )
    assert plugins.plugin_workflow_ref("research-pack", "compare-sources") == (
        "plugin://research-pack/workflows/compare-sources"
    )
    assert plugins.parse_plugin_workflow_ref("plugin://research-pack/workflows/compare-sources") == (
        "research-pack",
        "compare-sources",
    )
    assert plugins.parse_plugin_workflow_ref("research-pack/compare-sources") == (
        "research-pack",
        "compare-sources",
    )
    assert plugins.parse_plugin_workflow_ref("research-pack/workflows/compare-sources") == (
        "research-pack",
        "compare-sources",
    )
    assert plugins.parse_plugin_skill_ref("skill://plugin://research-pack/skills/source-review") == (
        "research-pack",
        "source-review",
    )
    assert plugins.parse_plugin_agent_template_ref("plugin://research-pack/agents/evidence-researcher") == (
        "research-pack",
        "evidence-researcher",
    )
    assert plugins.parse_plugin_agent_template_ref("research-pack/evidence-researcher") == (
        "research-pack",
        "evidence-researcher",
    )
