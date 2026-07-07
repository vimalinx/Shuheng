"""Context-pack shaping helpers for the Shuheng control plane."""
from __future__ import annotations

from typing import Any, Optional

try:
    from .text_utils import clean_text, truncate_cells
except Exception:
    from text_utils import clean_text, truncate_cells  # type: ignore


def compact_nonempty_lines(text: str, *, limit: int = 12, width: int = 220) -> list[str]:
    lines: list[str] = []
    for line in (text or "").splitlines():
        line = clean_text(line).strip()
        if not line or line.startswith("#"):
            continue
        lines.append(truncate_cells(line, width))
        if len(lines) >= limit:
            break
    return lines


def memory_hydration_pack(
    *,
    task_id: str,
    profile: str,
    memory: str,
    recent_mail: list[dict[str, Any]],
    shared_profile: dict[str, Any],
    layered_memory: dict[str, Any],
    workspace_context: Optional[dict[str, Any]] = None,
    agent_profile_ref: str = "",
    agent_memory_ref: str = "",
    agent_persistent: bool = True,
    memory_pack_id: str = "",
) -> dict[str, Any]:
    profile_items = compact_nonempty_lines(profile, limit=8)
    memory_items = compact_nonempty_lines(memory, limit=12)
    workspace_context = workspace_context or {}
    included: list[dict[str, Any]] = [
        {
            "scope": "user.shared-profile",
            "reason": "Shared user profile/current state that every Shuheng agent should know.",
            "items": [
                str(shared_profile.get("profile_description") or ""),
                f"interactions={shared_profile.get('interaction_count', 0)}",
                "focus=" + ", ".join(str(item) for item in (shared_profile.get("focus") or [])[:6]),
                "projects=" + ", ".join(str(item) for item in (shared_profile.get("projects") or [])[:4]),
            ],
            "refs": [str(ref) for ref in (shared_profile.get("refs") or []) if ref],
        },
        {
            "scope": "shuheng.layered-memory",
            "reason": "Primary Shuheng-owned L0-L4 layered memory context.",
            "items": [str(item) for item in (layered_memory.get("items") or [])[:8]],
            "refs": [str(ref) for ref in (layered_memory.get("refs") or []) if ref],
        },
        {
            "scope": "project.agent-harness",
            "reason": "Defines the governed multi-agent baseline and approval/single-writer constraints.",
            "items": [
                "Strong Orchestrator, bounded workers, ledgers, artifact refs, human approval gates.",
                "Read tasks may be parallel; write tasks stay single-writer or approval-gated.",
            ],
            "refs": ["docs/agent-harness-architecture.md", "AGENTS.md"],
        },
        {
            "scope": "subagent.profile",
            "reason": "Defines this worker's role, boundaries, and persistent behavior.",
            "items": profile_items or ["(empty profile)"],
            "refs": [agent_profile_ref] if agent_profile_ref else [],
        },
        {
            "scope": "subagent.memory",
            "reason": "Hydrates only this worker's own approved long-term memory.",
            "items": memory_items or (["(disabled for ephemeral session agent)"] if not agent_persistent else ["(empty memory)"]),
            "refs": [agent_memory_ref] if agent_persistent and agent_memory_ref else [],
        },
    ]
    if workspace_context.get("included"):
        workspace = workspace_context.get("workspace") or {}
        workspace_name = str(workspace.get("name") or workspace.get("workspace_id") or "selected workspace")
        l4 = workspace_context.get("l4") or {}
        workspace_items = [f"Workspace provenance: {workspace_name}"]
        workspace_items.extend(str(item) for item in (workspace_context.get("items") or [])[:6])
        workspace_items.append(f"Workspace L4 refs indexed: {int(l4.get('refs_count') or 0)}")
        included.append({
            "scope": "workspace.project-provenance",
            "reason": "Automatic workspace inference is secondary provenance, not the primary memory mode.",
            "items": workspace_items,
            "refs": [str(ref) for ref in (workspace_context.get("refs") or []) if ref],
        })
    mail_items = [
        f"{row.get('message_id', '')}: {row.get('intent', '')} {row.get('status', '')} task={row.get('task_id', '')}"
        for row in recent_mail[-5:]
    ]
    if mail_items:
        included.append({
            "scope": "agent_mail.refs",
            "reason": "Recent bus references can reveal pending approvals, delegated work, and result artifacts.",
            "items": mail_items,
            "refs": [str(row.get("message_id") or "") for row in recent_mail[-5:] if row.get("message_id")],
        })
    result = {
        "memory_pack_id": memory_pack_id,
        "for_task_id": task_id,
        "included": included,
        "excluded": [
            {"scope": "raw_logs", "reason": "context_policy.include_raw_logs=false; use refs and previews instead."},
            {"scope": "unrelated_project_memory", "reason": "Avoid context pollution across unrelated projects."},
            {
                "scope": "workspace.project-provenance",
                "reason": str(workspace_context.get("reason") or "Workspace memory is included after automatic inference."),
            } if not workspace_context.get("included") else {},
            {"scope": "secrets", "reason": "No secret access without an explicit approval gate."},
        ],
    }
    result["excluded"] = [row for row in result["excluded"] if row]
    return result


def context_layers_for_task(
    *,
    role: str,
    security_context: str,
    objective: str,
    profile: str,
    memory: str,
    task_contract: dict[str, Any],
    memory_pack: dict[str, Any],
    source_policy: dict[str, Any],
    shared_profile: dict[str, Any],
    layered_memory: dict[str, Any],
    workspace_context: Optional[dict[str, Any]] = None,
    recent_tasks: Optional[list[dict[str, Any]]] = None,
    recent_progress: Optional[list[dict[str, Any]]] = None,
    recent_traces: Optional[list[dict[str, Any]]] = None,
    recent_artifacts: Optional[list[dict[str, Any]]] = None,
    active_session: str = "",
    subagent_status: str = "",
) -> dict[str, Any]:
    workspace_context = workspace_context or {}
    recent_tasks = recent_tasks or []
    recent_progress = recent_progress or []
    recent_traces = recent_traces or []
    recent_artifacts = recent_artifacts or []
    progress_source = recent_progress or recent_tasks
    progress_items = [
        f"{row.get('task_id', '')}: {row.get('status', '')} {truncate_cells(str(row.get('summary') or row.get('error') or row.get('objective') or ''), 160)}"
        for row in progress_source[-6:]
    ]
    project_items = [
        "Shuheng agent harness implementation follows docs/agent-harness-architecture.md.",
        "Program-level approval, task/mail schemas, artifact index, and single-writer are active implementation layers.",
        "Primary memory mode is Shuheng-owned L0-L4 layered memory.",
    ]
    project_refs = ["docs/agent-harness-architecture.md", "goal-2/tasks.md"]
    project_refs.extend(str(ref) for ref in (layered_memory.get("refs") or []) if ref)
    if workspace_context.get("included"):
        workspace = workspace_context.get("workspace") or {}
        project_items.append(f"Shuheng workspace provenance: {workspace.get('name') or workspace.get('workspace_id')}")
        project_items.extend(str(item) for item in (workspace_context.get("items") or [])[:6])
        l4 = workspace_context.get("l4") or {}
        project_items.append(f"Workspace L4 refs indexed: {int(l4.get('refs_count') or 0)}")
        project_refs.extend(str(ref) for ref in (workspace_context.get("refs") or []) if ref)
    return {
        "L0_system_constitution": {
            "included": True,
            "items": [
                "Strong Orchestrator remains responsible for final integration.",
                "Bounded subagents execute only delegated objectives.",
                "Risky operations require program-level approval gates.",
                "Write operations respect single-writer policy.",
                "Return artifact refs, evidence refs, risks, and uncertainty.",
            ],
        },
        "L1_user_profile": {
            "included": True,
            "reason": "Shared user profile/current work-state context for all Shuheng agents.",
            "profile": shared_profile,
            "items": [
                str(shared_profile.get("profile_description") or ""),
                f"interactions={shared_profile.get('interaction_count', 0)}",
                "focus=" + ", ".join(str(item) for item in (shared_profile.get("focus") or [])[:8]),
                "projects=" + ", ".join(str(item) for item in (shared_profile.get("projects") or [])[:6]),
            ],
            "refs": list(shared_profile.get("refs") or []),
        },
        "L2_project_memory": {
            "included": True,
            "workspace": workspace_context or {
                "included": False,
                "reason": "No Shuheng workspace context was provided.",
            },
            "shuheng_layered_memory": layered_memory,
            "items": project_items,
            "refs": project_refs,
        },
        "L3_task_brief": {
            "included": True,
            "objective": objective,
            "task": task_contract,
            "source_policy": source_policy,
        },
        "L4_plan_ledger": {
            "included": True,
            "items": [
                f"{row.get('task_id', '')}: {row.get('status', '')} -> {truncate_cells(str(row.get('objective') or ''), 160)}"
                for row in recent_tasks[-6:]
            ],
        },
        "L5_progress_ledger": {
            "included": True,
            "items": progress_items,
        },
        "L6_working_notes": {
            "included": True,
            "profile_excerpt": profile[:1200],
            "memory_excerpt": memory[:1200],
            "memory_pack_ref": memory_pack.get("memory_pack_id", ""),
            "subagent_status": subagent_status,
            "active_session": active_session,
        },
        "L7_artifacts": {
            "included": True,
            "items": [
                {
                    "artifact_id": row.get("artifact_id", ""),
                    "type": row.get("type", ""),
                    "uri": row.get("uri", ""),
                    "hash": row.get("hash", ""),
                    "source_task_id": row.get("source_task_id", ""),
                }
                for row in recent_artifacts
            ],
        },
        "L8_raw_trace": {
            "included": False,
            "include_raw_logs": False,
            "trace_refs": [row.get("trace_id", "") for row in recent_traces if row.get("trace_id")],
            "reason": "Raw trace content is excluded by default; refs are available for targeted inspection.",
        },
    }


def indent_text(text: str, prefix: str) -> str:
    return "\n".join(prefix + line if line else prefix.rstrip() for line in str(text or "").splitlines())


def skill_pack_prompt_items(skill_pack: dict[str, Any]) -> list[str]:
    skill_items: list[str] = []
    for item in (skill_pack.get("included") or []):
        name = str(item.get("name") or item.get("ref") or "").strip()
        ref = str(item.get("ref") or "").strip()
        path = str(item.get("path") or "").strip()
        status = "resolved" if item.get("resolved") else "unresolved"
        summary = str(item.get("summary") or "").strip()
        body = str(item.get("body") or item.get("body_excerpt") or "").strip()
        header = f"- {name or ref} ({status})"
        if ref and ref != name:
            header += f" ref={ref}"
        if path:
            header += f" path={path}"
        if summary:
            header += f"\n  summary: {summary}"
        if body:
            header += f"\n  instructions:\n{indent_text(body, '    ')}"
        skill_items.append(header)
    return skill_items


def format_context_pack_for_prompt(
    pack: dict[str, Any],
    *,
    default_permission_profile: str = "standard",
) -> str:
    budget = pack.get("budget") or {}
    task = pack.get("task") or {}
    permissions = pack.get("permissions") or {}
    source_policy = pack.get("source_policy") or {}
    memory_pack = pack.get("memory_pack") or {}
    layered_memory = pack.get("layered_memory") or {}
    shared_profile = pack.get("shared_user_profile") or ((pack.get("layers") or {}).get("L1_user_profile") or {}).get("profile") or {}
    skill_pack = pack.get("skill_pack") or {}
    transient_skill_pack = pack.get("transient_skill_pack") or {}
    layers = pack.get("layers") or {}
    boundaries = "\n".join(f"- {item}" for item in (task.get("boundaries") or []))
    success = "\n".join(f"- {item}" for item in (task.get("success_criteria") or []))
    memory_items: list[str] = []
    for entry in memory_pack.get("included", []) or []:
        scope = entry.get("scope", "")
        items = entry.get("items", []) or []
        memory_items.append(f"- {scope}: " + "; ".join(str(item) for item in items[:3]))
    memory_excluded: list[str] = []
    for entry in memory_pack.get("excluded", []) or []:
        scope = entry.get("scope", "")
        reason = entry.get("reason", "")
        memory_excluded.append(f"- {scope}: {reason}")
    workspace_context = pack.get("workspace_context") or {}
    workspace = workspace_context.get("workspace") or {}
    if workspace_context.get("included"):
        workspace_line = f"{workspace.get('name') or workspace.get('workspace_id')} ({workspace.get('workspace_id')})"
    else:
        workspace_line = f"none - {workspace_context.get('reason') or 'No Shuheng workspace is selected.'}"
    layered_memory_prompt = str(layered_memory.get("prompt") or "").strip()
    shared_profile_text = str(shared_profile.get("text") or "").strip()
    artifact_items = []
    for item in ((layers.get("L7_artifacts") or {}).get("items") or [])[-5:]:
        artifact_items.append(f"- {item.get('uri', '')} {item.get('hash', '')} task={item.get('source_task_id', '')}")
    skill_items = skill_pack_prompt_items(skill_pack)
    transient_skill_items = skill_pack_prompt_items(transient_skill_pack)
    return f"""
[Shuheng Context Pack]
task_id: {pack.get("task_id", "")}
agent: {(pack.get("for_agent") or {}).get("name", "")} ({(pack.get("for_agent") or {}).get("id", "")})
role: {(pack.get("for_agent") or {}).get("role", "specialist")}
objective: {pack.get("objective", "")}
permission_profile: {pack.get("permission_profile") or permissions.get("permission_profile", default_permission_profile)}
budget: tokens={budget.get("max_tokens", 0)} tool_calls={budget.get("max_tool_calls", 0)} wall_clock={budget.get("max_wall_clock_seconds", 0)}s
write_policy: {permissions.get("write_policy", "none")}
tools_allowed: {", ".join(permissions.get("tools_allowed", []))}
tools_forbidden: {", ".join(permissions.get("tools_forbidden", []))}
output_contract: {", ".join(pack.get("output_contract") or [])}
stop_condition: {task.get("stop_condition", "")}
subagent_identity_rule: To claim you talked to a persistent Shuheng subagent, route the message to that existing agent_id through Shuheng subagent task/direct-chat controls. A copied profile, OMP native task spawn, or IRC demo participant is only a clone/persona simulation and must be reported as such.
final_reply_rule: After tool use, runtime task execution, or memory-candidate submission attempts, always finish with a normal user-facing final reply in the user's language. Tool results, "Result:" status lines, and memory-candidate submitted/deferred notices are not a substitute for that reply.
deictic_reference_rule: Treat this Shuheng Context Pack as internal execution metadata, not as a user-visible conversation object. User phrases such as "这个", "这个东西", "它", "this", or "that" refer to the most recent visible user-facing topic or message unless the user explicitly says "context pack" or "上下文包".
persistent_agent_request_rule: If the user explicitly asks to create/build a persistent/long-term agent, first emit or execute agent.create with lifecycle:"persistent" or persistent:true for a dedicated matching agent, or reuse an existing matching persistent agent by id. Do not satisfy that request with only scripts, schedules, memory candidates, or a suggestion to create the agent later.

Boundaries:
{boundaries or "- (empty)"}

Success criteria:
{success or "- (empty)"}

Source policy:
- allowed: {", ".join(source_policy.get("allowed_sources", []))}
- forbidden: {", ".join(source_policy.get("forbidden_sources", []))}
- artifact_policy: {source_policy.get("artifact_policy", "")}

Layered Shuheng memory:
{layered_memory_prompt or "- (empty)"}

Shared user profile:
{shared_profile_text or "- (empty)"}

Memory hydration pack:
{chr(10).join(memory_items) or "- (empty)"}

Memory excluded:
{chr(10).join(memory_excluded) or "- (empty)"}

Workspace context:
- provenance: {workspace_line}

Recent artifact refs:
{chr(10).join(artifact_items) or "- (empty)"}

Dedicated skills for this agent only:
{chr(10).join(skill_items) or "- (none)"}

Transient skills requested for this prompt only:
{chr(10).join(transient_skill_items) or "- (none)"}

Profile excerpt:
{pack.get("profile_excerpt") or "(empty)"}

Memory excerpt:
{pack.get("memory_excerpt") or "(empty)"}
[/Shuheng Context Pack]
""".strip()


def format_context_ref_for_prompt(
    pack: dict[str, Any],
    context_ref: str,
    *,
    default_permission_profile: str = "standard",
) -> str:
    permissions = pack.get("permissions") or {}
    return f"""
[Shuheng Context Ref]
task_id: {pack.get("task_id", "")}
context_pack_ref: {context_ref or "(none)"}
role: {(pack.get("for_agent") or {}).get("role", "main_orchestrator")}
objective: {pack.get("objective", "")}
permission_profile: {pack.get("permission_profile") or permissions.get("permission_profile", default_permission_profile)}
policy: This is a refreshed Shuheng context-pack artifact for the current turn.
Do not treat older full context-pack blocks in OMP history as current if this ref is newer.
Read the referenced artifact or call memory_context_get only when the task needs deeper context.
final_reply_rule: Always finish with a normal user-facing final reply in the user's language; do not stop at tool results, "Result:" status lines, or memory-candidate notices.
deictic_reference_rule: This Shuheng Context Ref is internal execution metadata. If the user says "这个", "它", "this", or "that", resolve it to the recent visible conversation/task topic, not to this context ref, unless the user explicitly names the context pack/ref.
persistent_agent_request_rule: Explicit user requests to create a persistent/long-term agent require agent.create lifecycle:"persistent" or persistent:true before reporting success; scripts/schedules alone are not enough.
[/Shuheng Context Ref]
""".strip()
