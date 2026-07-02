"""Pure declarative plugin registry helpers for Shuheng."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

try:
    from .path_utils import normalized_path, path_is_within
except Exception:  # pragma: no cover - script-mode compatibility
    from path_utils import normalized_path, path_is_within  # type: ignore

PLUGIN_SCHEMA_VERSION = "shuheng.plugin.v1"
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
_PLUGIN_SKILL_REF_RE = re.compile(
    r"^plugin://(?P<plugin>[A-Za-z0-9][A-Za-z0-9_.-]{0,79})/skills/(?P<skill>[A-Za-z0-9][A-Za-z0-9_.-]{0,79})$"
)
_PLUGIN_AGENT_TEMPLATE_REF_RE = re.compile(
    r"^plugin://(?P<plugin>[A-Za-z0-9][A-Za-z0-9_.-]{0,79})/agents/(?P<template>[A-Za-z0-9][A-Za-z0-9_.-]{0,79})$"
)
_PLUGIN_WORKFLOW_REF_RE = re.compile(
    r"^plugin://(?P<plugin>[A-Za-z0-9][A-Za-z0-9_.-]{0,79})/workflows/(?P<workflow>[A-Za-z0-9][A-Za-z0-9_.-]{0,79})$"
)


@dataclass(frozen=True)
class PluginIssue:
    plugin_id: str
    manifest_path: str
    message: str


@dataclass(frozen=True)
class PluginSkill:
    plugin_id: str
    skill_id: str
    ref: str
    name: str
    description: str
    path: str
    exists: bool


@dataclass(frozen=True)
class PluginAgentTemplate:
    plugin_id: str
    template_id: str
    ref: str
    name: str
    description: str
    role: str
    profile: str
    persistent: bool
    skill_refs: tuple[str, ...]
    default_model: str


@dataclass(frozen=True)
class PluginWorkflow:
    plugin_id: str
    workflow_id: str
    ref: str
    name: str
    description: str
    path: str
    exists: bool


@dataclass(frozen=True)
class PluginRecord:
    plugin_id: str
    name: str
    version: str
    description: str
    root: str
    manifest_path: str
    skills: tuple[PluginSkill, ...] = ()
    agent_templates: tuple[PluginAgentTemplate, ...] = ()
    workflows: tuple[PluginWorkflow, ...] = ()
    permissions: dict[str, Any] | None = None


@dataclass(frozen=True)
class PluginRegistry:
    plugins: dict[str, PluginRecord]
    issues: tuple[PluginIssue, ...] = ()


def safe_plugin_id(value: Any) -> str:
    text = str(value or "").strip()
    return text if _SAFE_ID_RE.fullmatch(text) else ""


def plugin_skill_ref(plugin_id: str, skill_id: str) -> str:
    plugin = safe_plugin_id(plugin_id)
    skill = safe_plugin_id(skill_id)
    return f"plugin://{plugin}/skills/{skill}" if plugin and skill else ""


def plugin_agent_template_ref(plugin_id: str, template_id: str) -> str:
    plugin = safe_plugin_id(plugin_id)
    template = safe_plugin_id(template_id)
    return f"plugin://{plugin}/agents/{template}" if plugin and template else ""


def plugin_workflow_ref(plugin_id: str, workflow_id: str) -> str:
    plugin = safe_plugin_id(plugin_id)
    workflow = safe_plugin_id(workflow_id)
    return f"plugin://{plugin}/workflows/{workflow}" if plugin and workflow else ""


def parse_plugin_skill_ref(ref: Any) -> tuple[str, str]:
    text = str(ref or "").strip().removeprefix("skill://").strip()
    match = _PLUGIN_SKILL_REF_RE.fullmatch(text)
    if not match:
        return "", ""
    return match.group("plugin"), match.group("skill")


def parse_plugin_agent_template_ref(ref: Any) -> tuple[str, str]:
    text = str(ref or "").strip()
    match = _PLUGIN_AGENT_TEMPLATE_REF_RE.fullmatch(text)
    if match:
        return match.group("plugin"), match.group("template")
    parts = text.split("/")
    if len(parts) == 2 and safe_plugin_id(parts[0]) and safe_plugin_id(parts[1]):
        return parts[0], parts[1]
    if len(parts) == 3 and parts[1] == "agents" and safe_plugin_id(parts[0]) and safe_plugin_id(parts[2]):
        return parts[0], parts[2]
    return "", ""


def parse_plugin_workflow_ref(ref: Any) -> tuple[str, str]:
    text = str(ref or "").strip()
    match = _PLUGIN_WORKFLOW_REF_RE.fullmatch(text)
    if match:
        return match.group("plugin"), match.group("workflow")
    parts = text.split("/")
    if len(parts) == 2 and safe_plugin_id(parts[0]) and safe_plugin_id(parts[1]):
        return parts[0], parts[1]
    if len(parts) == 3 and parts[1] == "workflows" and safe_plugin_id(parts[0]) and safe_plugin_id(parts[2]):
        return parts[0], parts[2]
    return "", ""


def is_plugin_skill_ref(ref: Any) -> bool:
    return parse_plugin_skill_ref(ref) != ("", "")


def plugin_skill_ref_from_token(token: Any) -> str:
    text = str(token or "").strip().removeprefix("skill://").strip()
    if is_plugin_skill_ref(text):
        return text
    parts = text.split("/")
    if len(parts) == 2:
        return plugin_skill_ref(parts[0], parts[1])
    if len(parts) == 3 and parts[1] == "skills":
        return plugin_skill_ref(parts[0], parts[2])
    return ""


def plugin_roots(*roots: str) -> list[str]:
    raw_roots = list(roots)
    if not raw_roots:
        shuheng_home = os.path.abspath(
            os.path.expanduser(os.environ.get("SHUHENG_HOME") or os.environ.get("GA_TUI_HOME") or "~/.shuheng")
        )
        raw_roots = [os.path.join(shuheng_home, "plugins")]
    normalized: list[str] = []
    seen: set[str] = set()
    for root in raw_roots:
        path = normalized_path(root)
        if not path or path in seen:
            continue
        seen.add(path)
        normalized.append(path)
    return normalized


def _manifest_paths(roots: list[str]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for root in plugin_roots(*roots):
        root_manifest = os.path.join(root, "plugin.json")
        if os.path.isfile(root_manifest):
            manifest = normalized_path(root_manifest)
            if manifest not in seen:
                seen.add(manifest)
                paths.append(manifest)
        if not os.path.isdir(root):
            continue
        try:
            child_names = sorted(os.listdir(root))
        except OSError:
            continue
        for child_name in child_names:
            manifest = normalized_path(os.path.join(root, child_name, "plugin.json"))
            if manifest in seen or not os.path.isfile(manifest):
                continue
            if not path_is_within(manifest, root):
                continue
            seen.add(manifest)
            paths.append(manifest)
    return paths


def plugin_registry_fingerprint(roots: list[str]) -> tuple[tuple[str, str, int, int], ...]:
    rows: list[tuple[str, str, int, int]] = []
    for root in plugin_roots(*roots):
        try:
            stat = os.stat(root)
            rows.append(("root", normalized_path(root), int(stat.st_mtime_ns), int(stat.st_size)))
        except OSError:
            rows.append(("missing", normalized_path(root), 0, 0))
    for manifest in _manifest_paths(roots):
        try:
            stat = os.stat(manifest)
            rows.append(("manifest", normalized_path(manifest), int(stat.st_mtime_ns), int(stat.st_size)))
        except OSError:
            rows.append(("missing-manifest", normalized_path(manifest), 0, 0))
    return tuple(rows)


def _issue(plugin_id: str, manifest_path: str, message: str) -> PluginIssue:
    return PluginIssue(plugin_id=plugin_id or "(unknown)", manifest_path=manifest_path, message=message)


def _string_items(value: Any) -> list[str]:
    if isinstance(value, str):
        if "," in value or "\n" in value:
            return [part.strip() for part in re.split(r"[,\n]+", value) if part.strip()]
        return [part.strip() for part in value.split() if part.strip()]
    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        for item in value:
            if isinstance(item, dict):
                result.append(str(item.get("ref") or item.get("id") or item.get("name") or ""))
            else:
                result.append(str(item or ""))
        return [item.strip() for item in result if item.strip()]
    if isinstance(value, dict):
        return [str(key) for key, enabled in value.items() if enabled]
    return []


def _resolve_declared_file(plugin_root: str, raw_path: Any) -> str:
    rel_path = str(raw_path or "").strip()
    if not rel_path or rel_path.startswith("~") or os.path.isabs(os.path.expanduser(rel_path)):
        return ""
    path = normalized_path(os.path.join(plugin_root, rel_path))
    if not path_is_within(path, plugin_root):
        return ""
    return path


def _template_skill_refs(raw_value: Any, plugin_id: str, local_skill_ids: set[str]) -> tuple[str, ...]:
    refs: list[str] = []
    seen: set[str] = set()
    for raw in _string_items(raw_value):
        ref = re.sub(r"\s+", " ", raw.strip().removeprefix("skill://").strip())
        if not ref:
            continue
        if ref in local_skill_ids:
            ref = plugin_skill_ref(plugin_id, ref)
        key = ref.casefold()
        if key in seen:
            continue
        seen.add(key)
        refs.append(ref)
    return tuple(refs)


def _parse_skill_entries(
    plugin_id: str,
    plugin_root: str,
    manifest_path: str,
    entries: Any,
) -> tuple[tuple[PluginSkill, ...], tuple[PluginIssue, ...]]:
    if entries in (None, ""):
        return (), ()
    if not isinstance(entries, list):
        return (), (_issue(plugin_id, manifest_path, "contributes.skills must be a list"),)
    skills: list[PluginSkill] = []
    issues: list[PluginIssue] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            issues.append(_issue(plugin_id, manifest_path, f"skills[{index}] must be an object"))
            continue
        skill_id = safe_plugin_id(entry.get("id"))
        if not skill_id:
            issues.append(_issue(plugin_id, manifest_path, f"skills[{index}] has an invalid id"))
            continue
        if skill_id.casefold() in seen:
            issues.append(_issue(plugin_id, manifest_path, f"skills[{index}] duplicates id {skill_id}"))
            continue
        seen.add(skill_id.casefold())
        path = _resolve_declared_file(plugin_root, entry.get("path") or f"skills/{skill_id}/SKILL.md")
        if not path:
            issues.append(_issue(plugin_id, manifest_path, f"skills[{index}] path must stay inside the plugin root"))
            continue
        exists = os.path.isfile(path)
        if not exists:
            issues.append(_issue(plugin_id, manifest_path, f"skills[{index}] path does not exist: {entry.get('path') or path}"))
        skills.append(
            PluginSkill(
                plugin_id=plugin_id,
                skill_id=skill_id,
                ref=plugin_skill_ref(plugin_id, skill_id),
                name=str(entry.get("name") or skill_id).strip() or skill_id,
                description=str(entry.get("description") or "").strip(),
                path=path,
                exists=exists,
            )
        )
    return tuple(skills), tuple(issues)


def _parse_agent_templates(
    plugin_id: str,
    manifest_path: str,
    entries: Any,
    local_skill_ids: set[str],
) -> tuple[tuple[PluginAgentTemplate, ...], tuple[PluginIssue, ...]]:
    if entries in (None, ""):
        return (), ()
    if not isinstance(entries, list):
        return (), (_issue(plugin_id, manifest_path, "contributes.agent_templates must be a list"),)
    templates: list[PluginAgentTemplate] = []
    issues: list[PluginIssue] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            issues.append(_issue(plugin_id, manifest_path, f"agent_templates[{index}] must be an object"))
            continue
        template_id = safe_plugin_id(entry.get("id"))
        if not template_id:
            issues.append(_issue(plugin_id, manifest_path, f"agent_templates[{index}] has an invalid id"))
            continue
        if template_id.casefold() in seen:
            issues.append(_issue(plugin_id, manifest_path, f"agent_templates[{index}] duplicates id {template_id}"))
            continue
        seen.add(template_id.casefold())
        lifecycle = str(entry.get("lifecycle") or "").strip().lower()
        persistent = bool(entry.get("persistent", lifecycle not in {"temp", "temporary", "ephemeral"}))
        templates.append(
            PluginAgentTemplate(
                plugin_id=plugin_id,
                template_id=template_id,
                ref=plugin_agent_template_ref(plugin_id, template_id),
                name=str(entry.get("name") or template_id).strip() or template_id,
                description=str(entry.get("description") or "").strip(),
                role=str(entry.get("role") or "specialist").strip() or "specialist",
                profile=str(entry.get("profile") or entry.get("description") or "").strip(),
                persistent=persistent,
                skill_refs=_template_skill_refs(entry.get("skill_refs", entry.get("skills", entry.get("skill", []))), plugin_id, local_skill_ids),
                default_model=str(entry.get("default_model") or entry.get("model") or "").strip(),
            )
        )
    return tuple(templates), tuple(issues)


def _parse_workflows(
    plugin_id: str,
    plugin_root: str,
    manifest_path: str,
    entries: Any,
) -> tuple[tuple[PluginWorkflow, ...], tuple[PluginIssue, ...]]:
    if entries in (None, ""):
        return (), ()
    if not isinstance(entries, list):
        return (), (_issue(plugin_id, manifest_path, "contributes.workflows must be a list"),)
    workflows: list[PluginWorkflow] = []
    issues: list[PluginIssue] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            issues.append(_issue(plugin_id, manifest_path, f"workflows[{index}] must be an object"))
            continue
        workflow_id = safe_plugin_id(entry.get("id"))
        if not workflow_id:
            issues.append(_issue(plugin_id, manifest_path, f"workflows[{index}] has an invalid id"))
            continue
        if workflow_id.casefold() in seen:
            issues.append(_issue(plugin_id, manifest_path, f"workflows[{index}] duplicates id {workflow_id}"))
            continue
        seen.add(workflow_id.casefold())
        path = _resolve_declared_file(plugin_root, entry.get("path") or f"workflows/{workflow_id}.md")
        if not path:
            issues.append(_issue(plugin_id, manifest_path, f"workflows[{index}] path must stay inside the plugin root"))
            continue
        exists = os.path.isfile(path)
        if not exists:
            issues.append(_issue(plugin_id, manifest_path, f"workflows[{index}] path does not exist: {entry.get('path') or path}"))
        workflows.append(
            PluginWorkflow(
                plugin_id=plugin_id,
                workflow_id=workflow_id,
                ref=plugin_workflow_ref(plugin_id, workflow_id),
                name=str(entry.get("name") or workflow_id).strip() or workflow_id,
                description=str(entry.get("description") or "").strip(),
                path=path,
                exists=exists,
            )
        )
    return tuple(workflows), tuple(issues)


def load_plugin_manifest(manifest_path: str) -> tuple[PluginRecord | None, tuple[PluginIssue, ...]]:
    path = normalized_path(manifest_path)
    plugin_root = os.path.dirname(path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as exc:
        return None, (_issue("", path, f"plugin.json is not valid JSON: {exc}"),)
    if not isinstance(payload, dict):
        return None, (_issue("", path, "plugin.json must contain a JSON object"),)
    plugin_id = safe_plugin_id(payload.get("id"))
    if payload.get("schema_version") != PLUGIN_SCHEMA_VERSION:
        return None, (_issue(plugin_id, path, f"schema_version must be {PLUGIN_SCHEMA_VERSION}"),)
    if not plugin_id:
        return None, (_issue("", path, "plugin id is required and must be filesystem-safe"),)
    contributes = payload.get("contributes") if isinstance(payload.get("contributes"), dict) else {}
    issues: list[PluginIssue] = []
    skills, skill_issues = _parse_skill_entries(plugin_id, plugin_root, path, contributes.get("skills"))
    issues.extend(skill_issues)
    local_skill_ids = {skill.skill_id for skill in skills}
    templates, template_issues = _parse_agent_templates(plugin_id, path, contributes.get("agent_templates"), local_skill_ids)
    issues.extend(template_issues)
    workflows, workflow_issues = _parse_workflows(plugin_id, plugin_root, path, contributes.get("workflows"))
    issues.extend(workflow_issues)
    permissions = payload.get("permissions") if isinstance(payload.get("permissions"), dict) else {}
    record = PluginRecord(
        plugin_id=plugin_id,
        name=str(payload.get("name") or plugin_id).strip() or plugin_id,
        version=str(payload.get("version") or "").strip(),
        description=str(payload.get("description") or "").strip(),
        root=plugin_root,
        manifest_path=path,
        skills=skills,
        agent_templates=templates,
        workflows=workflows,
        permissions=dict(permissions),
    )
    return record, tuple(issues)


def discover_plugins(roots: list[str]) -> PluginRegistry:
    plugins: dict[str, PluginRecord] = {}
    issues: list[PluginIssue] = []
    for manifest_path in _manifest_paths(roots):
        record, record_issues = load_plugin_manifest(manifest_path)
        issues.extend(record_issues)
        if record is None:
            continue
        if record.plugin_id in plugins:
            issues.append(_issue(record.plugin_id, manifest_path, f"duplicate plugin id ignored: {record.plugin_id}"))
            continue
        plugins[record.plugin_id] = record
    return PluginRegistry(plugins=plugins, issues=tuple(issues))


def plugin_skill_for_ref(ref: Any, registry: PluginRegistry) -> PluginSkill | None:
    plugin_id, skill_id = parse_plugin_skill_ref(ref)
    if not plugin_id or not skill_id:
        return None
    plugin = registry.plugins.get(plugin_id)
    if plugin is None:
        return None
    for skill in plugin.skills:
        if skill.skill_id == skill_id:
            return skill
    return None


def plugin_skill_file_for_ref(ref: Any, registry: PluginRegistry) -> str:
    skill = plugin_skill_for_ref(ref, registry)
    if skill is None or not os.path.isfile(skill.path):
        return ""
    plugin = registry.plugins.get(skill.plugin_id)
    if plugin is None or not path_is_within(skill.path, plugin.root):
        return ""
    return normalized_path(skill.path)


def plugin_skill_display_name(ref: Any, registry: PluginRegistry) -> str:
    skill = plugin_skill_for_ref(ref, registry)
    if skill is None:
        plugin_id, skill_id = parse_plugin_skill_ref(ref)
        return f"{plugin_id}/{skill_id}" if plugin_id and skill_id else ""
    plugin = registry.plugins.get(skill.plugin_id)
    plugin_name = plugin.name if plugin else skill.plugin_id
    return f"{plugin_name}/{skill.name or skill.skill_id}"


def plugin_agent_template_for_ref(ref: Any, registry: PluginRegistry) -> PluginAgentTemplate | None:
    plugin_id, template_id = parse_plugin_agent_template_ref(ref)
    if not plugin_id or not template_id:
        return None
    plugin = registry.plugins.get(plugin_id)
    if plugin is None:
        return None
    for template in plugin.agent_templates:
        if template.template_id == template_id:
            return template
    return None


def plugin_workflow_for_ref(ref: Any, registry: PluginRegistry) -> PluginWorkflow | None:
    plugin_id, workflow_id = parse_plugin_workflow_ref(ref)
    if not plugin_id or not workflow_id:
        return None
    plugin = registry.plugins.get(plugin_id)
    if plugin is None:
        return None
    for workflow in plugin.workflows:
        if workflow.workflow_id == workflow_id:
            return workflow
    return None


def plugin_workflow_file_for_ref(ref: Any, registry: PluginRegistry) -> str:
    workflow = plugin_workflow_for_ref(ref, registry)
    if workflow is None or not os.path.isfile(workflow.path):
        return ""
    plugin = registry.plugins.get(workflow.plugin_id)
    if plugin is None or not path_is_within(workflow.path, plugin.root):
        return ""
    return normalized_path(workflow.path)


def format_plugin_list(registry: PluginRegistry) -> str:
    lines: list[str] = []
    if registry.plugins:
        lines.append("Plugins:")
        for plugin_id in sorted(registry.plugins):
            plugin = registry.plugins[plugin_id]
            version = f" v{plugin.version}" if plugin.version else ""
            summary = f"skills:{len(plugin.skills)} templates:{len(plugin.agent_templates)} workflows:{len(plugin.workflows)}"
            lines.append(f"- {plugin.plugin_id} · {plugin.name}{version} · {summary}")
            if plugin.description:
                lines.append(f"  {plugin.description}")
    else:
        lines.append("No plugins found.")
    if registry.issues:
        lines.append("Validation issues:")
        for issue in registry.issues[:20]:
            lines.append(f"- {issue.plugin_id}: {issue.message}")
    return "\n".join(lines)


def format_plugin_info(plugin_id: str, registry: PluginRegistry) -> str:
    plugin = registry.plugins.get(str(plugin_id or "").strip())
    if plugin is None:
        return f"Plugin not found: {plugin_id}"
    lines = [
        f"id: {plugin.plugin_id}",
        f"name: {plugin.name}",
        f"version: {plugin.version or '(none)'}",
        f"description: {plugin.description or '(none)'}",
        f"root: {plugin.root}",
    ]
    lines.append("skills:")
    if plugin.skills:
        for skill in plugin.skills:
            status = "ok" if skill.exists else "missing"
            lines.append(f"- {skill.ref} · {skill.name} · {status}")
            if skill.description:
                lines.append(f"  {skill.description}")
    else:
        lines.append("- (none)")
    lines.append("agent_templates:")
    if plugin.agent_templates:
        for template in plugin.agent_templates:
            lifecycle = "persistent" if template.persistent else "temporary"
            skills = ", ".join(template.skill_refs) if template.skill_refs else "(none)"
            lines.append(f"- {template.ref} · {template.name} · role:{template.role} · {lifecycle} · skills:{skills}")
    else:
        lines.append("- (none)")
    lines.append("workflows:")
    if plugin.workflows:
        for workflow in plugin.workflows:
            status = "ok" if workflow.exists else "missing"
            lines.append(f"- {workflow.ref} · {workflow.name} · {status}")
    else:
        lines.append("- (none)")
    matching_issues = [issue for issue in registry.issues if issue.plugin_id == plugin.plugin_id]
    if matching_issues:
        lines.append("validation_issues:")
        for issue in matching_issues[:20]:
            lines.append(f"- {issue.message}")
    return "\n".join(lines)
