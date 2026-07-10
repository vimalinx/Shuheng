from __future__ import annotations

import json
from pathlib import Path

import pytest

from shuheng import agent_projects


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_project(root: Path, *, reverse_creation: bool = False) -> Path:
    root.mkdir(parents=True)
    project = {
        "schema_version": "shuheng.agent_project.v1",
        "id": "research-agent",
        "name": "Research Agent",
        "description": "A deterministic test project.",
        "entry_blueprint": "agent.json",
        "default_runtime": "pi-native",
        "runtime_version": "0.80.6",
        "tests": [{"id": "smoke", "path": "tests/smoke.json"}],
    }
    blueprint = {
        "schema_version": "shuheng.agent_blueprint.v1",
        "id": "main",
        "name": "Research Worker",
        "prompt": {"path": "prompts/system.md"},
        "skills": [
            {"id": "source-review", "path": "skills/source-review/SKILL.md"},
            {"id": "writing", "path": "skills/writing/SKILL.md"},
        ],
        "tools": [
            {
                "id": "local-search",
                "path": "tools/local-search.ts",
                "requested_capabilities": ["repo.read"],
            }
        ],
        "requested_capabilities": ["repo.read", "repo.write"],
        "delegation": {"max_subagents": 0},
        "budget": {"max_turns": 8},
        "output_contract": {"format": "structured_markdown"},
    }
    source_files = [
        (root / "prompts/system.md", "Do careful research.\n"),
        (root / "skills/source-review/SKILL.md", "# Review sources\n"),
        (root / "skills/writing/SKILL.md", "# Write clearly\n"),
        (root / "tools/local-search.ts", "export const localSearch = true;\n"),
        (root / "tests/smoke.json", '{"prompt":"hello"}\n'),
    ]
    for path, content in reversed(source_files) if reverse_creation else source_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    write_json(root / "agent-project.json", project)
    write_json(root / "agent.json", blueprint)
    return root


def diagnostic_codes(result: agent_projects.AgentProjectResult) -> set[str]:
    return {item.code for item in result.diagnostics}


def test_compile_valid_project_is_deterministic_frozen_and_json_safe(tmp_path: Path) -> None:
    first_root = make_project(tmp_path / "first")
    second_root = make_project(tmp_path / "second", reverse_creation=True)

    first = agent_projects.compile_agent_project(first_root)
    again = agent_projects.compile_agent_project(first_root)
    second = agent_projects.compile_agent_project(second_root)

    assert first.ok and first.build is not None
    assert again.ok and again.build is not None
    assert second.ok and second.build is not None
    assert first.build.digest == again.build.digest == second.build.digest
    assert [item.path for item in first.build.files] == sorted(item.path for item in first.build.files)
    assert first.build.runtime == "pi-native"
    assert first.build.runtime_version == "0.80.6"
    prompt = first.build.file("prompts/system.md")
    assert prompt is not None
    assert prompt.content_bytes() == b"Do careful research.\n"
    assert prompt.sha256
    json.dumps(first.to_record(), ensure_ascii=False)

    # The Build owns source bytes; later source edits do not mutate it.
    (first_root / "prompts/system.md").write_text("changed after build\n", encoding="utf-8")
    assert prompt.content_bytes() == b"Do careful research.\n"


@pytest.mark.parametrize(
    "relative_path,replacement",
    [
        ("prompts/system.md", "Changed prompt.\n"),
        ("skills/source-review/SKILL.md", "# Changed skill\n"),
        ("tools/local-search.ts", "export const localSearch = false;\n"),
        ("tests/smoke.json", '{"prompt":"changed"}\n'),
    ],
)
def test_referenced_source_changes_change_build_digest(
    tmp_path: Path, relative_path: str, replacement: str
) -> None:
    root = make_project(tmp_path / "project")
    before = agent_projects.compile_agent_project(root)
    assert before.ok and before.build is not None

    (root / relative_path).write_text(replacement, encoding="utf-8")
    after = agent_projects.compile_agent_project(root)

    assert after.ok and after.build is not None
    assert after.build.digest != before.build.digest


def test_manifest_byte_change_changes_build_digest(tmp_path: Path) -> None:
    root = make_project(tmp_path / "project")
    before = agent_projects.compile_agent_project(root)
    assert before.ok and before.build is not None

    manifest = json.loads((root / "agent-project.json").read_text(encoding="utf-8"))
    manifest["description"] = "Changed manifest source."
    write_json(root / "agent-project.json", manifest)
    after = agent_projects.compile_agent_project(root)

    assert after.ok and after.build is not None
    assert after.build.digest != before.build.digest


def test_malformed_and_duplicate_json_return_diagnostics(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed"
    malformed.mkdir()
    (malformed / "agent-project.json").write_text('{"schema_version":', encoding="utf-8")

    malformed_result = agent_projects.compile_agent_project(malformed)

    assert not malformed_result.ok
    assert "malformed_json" in diagnostic_codes(malformed_result)
    diagnostic = malformed_result.diagnostics[0]
    assert diagnostic.line > 0 and diagnostic.column > 0

    duplicate = tmp_path / "duplicate"
    duplicate.mkdir()
    (duplicate / "agent-project.json").write_text(
        '{"schema_version":"shuheng.agent_project.v1","id":"one","id":"two"}',
        encoding="utf-8",
    )

    duplicate_result = agent_projects.compile_agent_project(duplicate)

    assert not duplicate_result.ok
    assert "invalid_json" in diagnostic_codes(duplicate_result)
    assert "duplicate JSON key" in duplicate_result.diagnostics[0].message


def test_duplicate_ids_paths_capabilities_and_unknown_fields_are_rejected(tmp_path: Path) -> None:
    root = make_project(tmp_path / "project")
    blueprint_path = root / "agent.json"
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    blueprint["unknown"] = True
    blueprint["requested_capabilities"] = ["repo.read", "repo.read"]
    blueprint["skills"] = [
        {"id": "same", "path": "skills/source-review/SKILL.md"},
        {"id": "same", "path": "skills/writing/SKILL.md"},
        {"id": "third", "path": "skills/writing/SKILL.md"},
    ]
    write_json(blueprint_path, blueprint)

    result = agent_projects.compile_agent_project(root)

    assert not result.ok
    codes = diagnostic_codes(result)
    assert "unknown_field" in codes
    assert "duplicate_value" in codes
    assert "duplicate_resource_id" in codes
    assert "duplicate_resource_path" in codes


@pytest.mark.parametrize("unsafe", ["../outside.md", "/tmp/outside.md", "~/outside.md", "a/./b.md", "C:/outside.md"])
def test_declared_paths_cannot_escape_or_use_nonlocal_forms(tmp_path: Path, unsafe: str) -> None:
    root = make_project(tmp_path / "project")
    blueprint_path = root / "agent.json"
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    blueprint["prompt"] = {"path": unsafe}
    write_json(blueprint_path, blueprint)

    result = agent_projects.compile_agent_project(root)

    assert not result.ok
    assert "unsafe_path" in diagnostic_codes(result)


def test_symlink_escape_and_alias_are_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    escaping = make_project(tmp_path / "escaping")
    (escaping / "prompts/system.md").unlink()
    (escaping / "prompts/system.md").symlink_to(outside)

    escape_result = agent_projects.compile_agent_project(escaping)

    assert not escape_result.ok
    assert "path_escape" in diagnostic_codes(escape_result)

    aliasing = make_project(tmp_path / "aliasing")
    alias = aliasing / "skills/alias.md"
    alias.symlink_to(aliasing / "skills/source-review/SKILL.md")
    blueprint_path = aliasing / "agent.json"
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    blueprint["skills"][1]["path"] = "skills/alias.md"
    write_json(blueprint_path, blueprint)

    alias_result = agent_projects.compile_agent_project(aliasing)

    assert not alias_result.ok
    assert "duplicate_resolved_source" in diagnostic_codes(alias_result)


def test_tool_capability_must_be_declared_by_blueprint(tmp_path: Path) -> None:
    root = make_project(tmp_path / "project")
    blueprint_path = root / "agent.json"
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    blueprint["tools"][0]["requested_capabilities"] = ["network.read"]
    write_json(blueprint_path, blueprint)

    result = agent_projects.compile_agent_project(root)

    assert not result.ok
    assert "tool_capability_not_requested" in diagnostic_codes(result)


def test_run_manifest_intersects_requests_with_grants_and_requires_tool_grant(tmp_path: Path) -> None:
    compiled = agent_projects.compile_agent_project(make_project(tmp_path / "project"))
    assert compiled.ok and compiled.build is not None

    run = agent_projects.create_agent_run_manifest(
        compiled.build,
        assignment_id="task-001",
        granted_capabilities=["repo.read", "network.read"],
        granted_tool_ids=["local-search"],
        workspace=tmp_path / "workspace",
        provider_revision="pi-0.80.6",
        causation_refs=["task://root"],
    )

    assert run.ok and run.value is not None
    assert run.value.requested_capabilities == ("repo.read", "repo.write")
    assert run.value.granted_capabilities == ("network.read", "repo.read")
    assert run.value.effective_capabilities == ("repo.read",)
    assert run.value.effective_tool_ids == ("local-search",)
    record = run.value.to_record()
    assert record["capabilities"]["effective"] == ["repo.read"]
    assert record["tools"]["effective"] == ["local-search"]
    json.dumps(record)

    no_grants = agent_projects.create_agent_run_manifest(
        compiled.build,
        assignment_id="task-002",
        workspace=str(tmp_path / "workspace"),
        provider_revision="pi-0.80.6",
    )
    assert no_grants.ok and no_grants.value is not None
    assert no_grants.value.effective_capabilities == ()
    assert no_grants.value.effective_tool_ids == ()


def test_run_manifest_rejects_tool_without_required_effective_capability(tmp_path: Path) -> None:
    compiled = agent_projects.compile_agent_project(make_project(tmp_path / "project"))
    assert compiled.ok and compiled.build is not None

    result = agent_projects.create_agent_run_manifest(
        compiled.build,
        assignment_id="task-001",
        granted_tool_ids=["local-search"],
        workspace=str(tmp_path / "workspace"),
        provider_revision="pi-0.80.6",
    )

    assert not result.ok
    assert "tool_capability_denied" in diagnostic_codes(result)


def test_create_and_fork_publish_complete_valid_projects(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    created = agent_projects.create_agent_project(
        projects,
        project_id="writer",
        name="Writer",
        runtime_version="0.80.6",
    )

    assert created.ok and created.value is not None
    assert created.value.source_root == str((projects / "writer").resolve())
    assert agent_projects.compile_agent_project(projects / "writer").ok
    assert not list(projects.glob(".writer.tmp-*"))

    forked = agent_projects.fork_agent_project(
        projects / "writer",
        projects,
        project_id="writer-fork",
        name="Writer Fork",
    )

    assert forked.ok and forked.value is not None
    assert forked.value.project_id == "writer-fork"
    assert forked.value.name == "Writer Fork"
    assert agent_projects.compile_agent_project(projects / "writer-fork").ok
    original = json.loads((projects / "writer" / "agent-project.json").read_text(encoding="utf-8"))
    assert original["id"] == "writer"
    assert not list(projects.glob(".writer-fork.tmp-*"))


def test_create_and_fork_do_not_replace_existing_targets(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    first = agent_projects.create_agent_project(projects, project_id="existing", name="Existing")
    assert first.ok
    marker = projects / "existing" / "marker.txt"
    marker.write_text("keep", encoding="utf-8")

    second = agent_projects.create_agent_project(projects, project_id="existing", name="Replacement")
    fork = agent_projects.fork_agent_project(
        projects / "existing", projects, project_id="existing", name="Fork Replacement"
    )

    assert not second.ok and "project_exists" in diagnostic_codes(second)
    assert not fork.ok and "project_exists" in diagnostic_codes(fork)
    assert marker.read_text(encoding="utf-8") == "keep"


def test_bad_user_inputs_return_diagnostics_instead_of_exceptions(tmp_path: Path) -> None:
    missing = agent_projects.compile_agent_project(tmp_path / "missing")
    unsafe_create = agent_projects.create_agent_project(tmp_path, project_id="../bad")

    assert not missing.ok and "invalid_project_root" in diagnostic_codes(missing)
    assert not unsafe_create.ok and "unsafe_id" in diagnostic_codes(unsafe_create)
    assert agent_projects.safe_agent_id("valid.agent-1") == "valid.agent-1"
    assert agent_projects.safe_agent_id("bad/id") == ""
