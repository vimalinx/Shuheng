"""Tests for context-pack shaping helpers."""
from __future__ import annotations

from shuheng import app as app_module
from shuheng import context_packs


def _sample_pack() -> dict:
    return {
        "task_id": "task_context_test",
        "for_agent": {"id": "agent-test", "name": "Test Agent", "role": "researcher"},
        "objective": "Verify context pack prompt formatting",
        "permission_profile": "",
        "budget": {"max_tokens": 1000, "max_tool_calls": 5, "max_wall_clock_seconds": 60},
        "permissions": {
            "permission_profile": "",
            "write_policy": "none",
            "tools_allowed": ["repo.read", "web.search"],
            "tools_forbidden": ["filesystem.write"],
        },
        "output_contract": ["summary", "artifact_refs"],
        "task": {
            "boundaries": ["Use artifact refs"],
            "success_criteria": ["Prompt contains memory and artifact refs"],
            "stop_condition": "Return summary",
        },
        "source_policy": {
            "allowed_sources": ["task_brief", "artifact_index.refs"],
            "forbidden_sources": ["secrets"],
            "artifact_policy": "Use refs.",
        },
        "layered_memory": {"prompt": "Layered memory text", "refs": ["memory://layered"]},
        "shared_user_profile": {"text": "Shared profile text", "refs": ["memory://profile"]},
        "memory_pack": {
            "memory_pack_id": "mempack_test",
            "included": [
                {"scope": "user.shared-profile", "items": ["Shared profile"]},
                {"scope": "shuheng.layered-memory", "items": ["Layered item"]},
            ],
            "excluded": [{"scope": "secrets", "reason": "approval required"}],
        },
        "workspace_context": {
            "included": True,
            "workspace": {"name": "Workspace", "workspace_id": "workspace-123"},
            "items": ["Workspace memory"],
        },
        "layers": {
            "L7_artifacts": {
                "items": [
                    {
                        "uri": "artifact://context_packs/agent-test/task_context_test.json",
                        "hash": "sha256:test",
                        "source_task_id": "task_context_test",
                    }
                ]
            }
        },
        "skill_pack": {
            "included": [
                {
                    "name": "local-skill",
                    "ref": "local-skill",
                    "resolved": True,
                    "summary": "Local only",
                    "body": "Follow this local skill.",
                }
            ]
        },
        "profile_excerpt": "Profile excerpt",
        "memory_excerpt": "Memory excerpt",
    }


def test_compact_nonempty_lines_skips_headings_and_truncates() -> None:
    lines = context_packs.compact_nonempty_lines(
        "# heading\n\nfirst useful line\nsecond useful line is deliberately long",
        limit=2,
        width=20,
    )

    assert lines[0] == "first useful line"
    assert len(lines) == 2
    assert lines[1].startswith("second")
    assert lines[1] != "second useful line is deliberately long"


def test_memory_hydration_pack_scopes_and_refs() -> None:
    pack = context_packs.memory_hydration_pack(
        task_id="task_memory",
        profile="profile line",
        memory="memory line",
        recent_mail=[
            {"message_id": "msg1", "intent": "delegate", "status": "done", "task_id": "task1"},
            {"message_id": "msg2", "intent": "result", "status": "done", "task_id": "task2"},
        ],
        shared_profile={
            "profile_description": "Shared profile",
            "interaction_count": 3,
            "focus": ["context"],
            "projects": ["Shuheng"],
            "refs": ["memory://profile"],
        },
        layered_memory={"items": ["Layered item"], "refs": ["memory://layered"]},
        workspace_context={
            "included": True,
            "workspace": {"name": "Workspace", "workspace_id": "workspace-123"},
            "items": ["Workspace memory"],
            "refs": ["workspace://memory"],
            "l4": {"refs_count": 2},
        },
        agent_profile_ref="agent://profile",
        agent_memory_ref="agent://memory",
        memory_pack_id="mempack_memory",
    )

    scopes = {row["scope"] for row in pack["included"]}
    assert {
        "user.shared-profile",
        "shuheng.layered-memory",
        "project.agent-harness",
        "subagent.profile",
        "subagent.memory",
        "workspace.project-provenance",
        "agent_mail.refs",
    } <= scopes
    assert pack["memory_pack_id"] == "mempack_memory"
    assert pack["for_task_id"] == "task_memory"


def test_context_layers_shape_progress_and_trace_refs() -> None:
    memory_pack = {"memory_pack_id": "mempack_layers"}
    layers = context_packs.context_layers_for_task(
        role="researcher",
        security_context="standard",
        objective="Build context layers",
        profile="Profile line",
        memory="Memory line",
        task_contract={"success_criteria": ["L0-L8"]},
        memory_pack=memory_pack,
        source_policy={"allowed_sources": ["task_brief"]},
        shared_profile={"profile_description": "Shared", "refs": ["memory://profile"]},
        layered_memory={"items": ["Layered"], "refs": ["memory://layered"]},
        workspace_context={"included": False, "reason": "No workspace"},
        recent_tasks=[{"task_id": "task1", "status": "working", "objective": "Read code"}],
        recent_progress=[{"task_id": "task1", "status": "completed", "summary": "Read code done"}],
        recent_traces=[{"trace_id": "trace1", "payload": {"raw": "hidden"}}],
        recent_artifacts=[
            {
                "artifact_id": "artifact1",
                "type": "context_pack",
                "uri": "artifact://context_packs/agent-test/task1.json",
                "hash": "sha256:abc",
                "source_task_id": "task1",
            }
        ],
        active_session="main",
        subagent_status="idle",
    )

    assert set(layers) == {
        "L0_system_constitution",
        "L1_user_profile",
        "L2_project_memory",
        "L3_task_brief",
        "L4_plan_ledger",
        "L5_progress_ledger",
        "L6_working_notes",
        "L7_artifacts",
        "L8_raw_trace",
    }
    assert layers["L5_progress_ledger"]["items"] == ["task1: completed Read code done"]
    assert layers["L8_raw_trace"]["included"] is False
    assert layers["L8_raw_trace"]["trace_refs"] == ["trace1"]
    assert "payload" not in layers["L8_raw_trace"]


def test_prompt_and_ref_formatting_round_trip() -> None:
    pack = _sample_pack()
    prompt = context_packs.format_context_pack_for_prompt(pack, default_permission_profile="standard")
    ref = "artifact://context_packs/agent-test/task_context_test.json"
    ref_prompt = context_packs.format_context_ref_for_prompt(pack, ref, default_permission_profile="standard")

    assert "[Shuheng Context Pack]" in prompt
    assert "Memory hydration pack:" in prompt
    assert "Recent artifact refs:" in prompt
    assert "Dedicated skills for this agent only:" in prompt
    assert "deictic_reference_rule:" in prompt
    assert "context_pack_ref: artifact://context_packs/agent-test/task_context_test.json" in ref_prompt
    assert "deictic_reference_rule:" in ref_prompt


def test_app_formatting_wrappers_match_context_pack_module() -> None:
    pack = _sample_pack()
    ref = "artifact://context_packs/agent-test/task_context_test.json"

    assert app_module.indent_text("a\n\nb", "  ") == context_packs.indent_text("a\n\nb", "  ")
    assert app_module.format_context_pack_for_prompt(pack) == context_packs.format_context_pack_for_prompt(
        pack,
        default_permission_profile=app_module.PERMISSION_PROFILE_STANDARD,
    )
    assert app_module.format_context_ref_for_prompt(pack, ref) == context_packs.format_context_ref_for_prompt(
        pack,
        ref,
        default_permission_profile=app_module.PERMISSION_PROFILE_STANDARD,
    )
