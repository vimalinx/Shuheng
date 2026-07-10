"""App-facing Agent Project commands and the minimal curses authoring workspace.

Pure source contracts live in :mod:`shuheng.agent_projects` and pure editor
state lives in :mod:`shuheng.agent_editor`.  This module is the intentionally
thin UI/control-plane adapter.  It resolves the large ``app`` host lazily so
those two lower layers remain importable without curses or runtime providers.
"""
from __future__ import annotations

import curses
import json
import os
from pathlib import Path
import re
import shlex
import time
from typing import Any, Optional

try:
    from . import agent_projects as agent_project_helpers
    from .agent_editor import (
        AgentEditor,
        AgentEditorError,
        EditorDiagnostic,
        ExternalFileConflictError,
        is_allowed_authoring_path,
    )
    from .pi_native_provider import PI_NATIVE_SDK_VERSION
except ImportError:  # pragma: no cover - direct source-tree compatibility
    import agent_projects as agent_project_helpers  # type: ignore
    from agent_editor import (  # type: ignore
        AgentEditor,
        AgentEditorError,
        EditorDiagnostic,
        ExternalFileConflictError,
        is_allowed_authoring_path,
    )
    from pi_native_provider import PI_NATIVE_SDK_VERSION  # type: ignore


_HOST: Any = None


def configure_agent_project_workspace(host: Any) -> None:
    """Inject the app-owned composition facade without reversing imports."""

    global _HOST
    _HOST = host


def _host() -> Any:
    if _HOST is None:
        raise RuntimeError("Agent Project workspace host is not configured")
    return _HOST


def agent_project_root_for_id(project_id: str) -> str:
    """Resolve one local Agent Project without accepting path-like selectors."""

    host = _host()
    safe_id = agent_project_helpers.safe_agent_id(project_id)
    if not safe_id:
        return ""
    projects_root = Path(host.SHUHENG_AGENT_PROJECTS_DIR).expanduser().resolve(strict=False)
    candidate = projects_root / safe_id
    if candidate.is_symlink() or not candidate.is_dir():
        return ""
    try:
        resolved = candidate.resolve(strict=True)
        if os.path.commonpath((str(projects_root), str(resolved))) != str(projects_root):
            return ""
    except (OSError, RuntimeError, ValueError):
        return ""
    return str(resolved)


def local_agent_project_roots() -> list[str]:
    root = Path(_host().SHUHENG_AGENT_PROJECTS_DIR).expanduser()
    if not root.is_dir():
        return []
    projects: list[str] = []
    try:
        entries = sorted(root.iterdir(), key=lambda item: item.name.casefold())
    except OSError:
        return []
    for entry in entries:
        if entry.name.startswith(".") or entry.is_symlink() or not entry.is_dir():
            continue
        if not agent_project_helpers.safe_agent_id(entry.name):
            continue
        if (entry / agent_project_helpers.PROJECT_MANIFEST_NAME).is_file():
            projects.append(str(entry.resolve()))
    return projects


def agent_project_authoring_files(project_root: str) -> list[str]:
    try:
        root = Path(project_root).resolve(strict=True)
    except (OSError, RuntimeError):
        return []
    files: list[str] = []
    try:
        candidates = sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold())
    except OSError:
        return []
    for candidate in candidates:
        if any(part.startswith(".") for part in candidate.relative_to(root).parts):
            continue
        if candidate.is_symlink() or not candidate.is_file() or not is_allowed_authoring_path(candidate):
            continue
        try:
            resolved = candidate.resolve(strict=True)
            if os.path.commonpath((str(root), str(resolved))) != str(root):
                continue
        except (OSError, RuntimeError, ValueError):
            continue
        files.append(candidate.relative_to(root).as_posix())
    return files


def agent_project_diagnostic_lines(result: Any, *, limit: int = 8) -> list[str]:
    diagnostics = list(getattr(result, "diagnostics", ()) or ())
    lines: list[str] = []
    for item in diagnostics[: max(1, limit)]:
        location = str(getattr(item, "path", "") or "")
        line = int(getattr(item, "line", 0) or 0)
        column = int(getattr(item, "column", 0) or 0)
        if line:
            location += f":{line}"
            if column:
                location += f":{column}"
        code = str(getattr(item, "code", "") or "validation")
        message = str(getattr(item, "message", "") or "Invalid Agent Project")
        lines.append(f"{location + ' · ' if location else ''}{code}: {message}")
    if len(diagnostics) > len(lines):
        lines.append(f"… 另有 {len(diagnostics) - len(lines)} 条诊断")
    return lines


def agent_project_inventory_text() -> str:
    roots = local_agent_project_roots()
    if not roots:
        return (
            "还没有本地 Agent Project。\n"
            "使用 /agent-project create <id> [name]，或在 TUI 输入 /agent-projects 打开工作台。"
        )
    lines = [f"Agent Projects: {len(roots)}"]
    for root in roots:
        result = agent_project_helpers.compile_agent_project(root)
        if result.ok and result.build is not None:
            build = result.build
            lines.append(
                f"- {build.project.project_id} · {build.project.name} · {build.runtime} · "
                f"build {build.digest[:12]} · {len(build.blueprint.skills)} skill · {len(build.blueprint.tools)} tool"
            )
        else:
            lines.append(f"- {Path(root).name} · invalid · {agent_project_diagnostic_lines(result, limit=1)[0]}")
    return "\n".join(lines)


def agent_project_editor_validator(path: Path, text: str) -> list[EditorDiagnostic]:
    if path.suffix.casefold() != ".json":
        return []
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        return [
            EditorDiagnostic(
                message=exc.msg,
                path=str(path),
                line=exc.lineno,
                column=exc.colno,
                severity="error",
                code="malformed_json",
            )
        ]
    return []


def create_local_agent_project(project_id: str, name: str = "") -> str:
    result = agent_project_helpers.create_agent_project(
        _host().SHUHENG_AGENT_PROJECTS_DIR,
        project_id=project_id,
        name=name,
    )
    if not result.ok or result.value is None:
        return "Agent Project 创建失败：\n" + "\n".join(agent_project_diagnostic_lines(result))
    return f"已创建 Agent Project：{result.value.project_id} · {result.value.source_root}"


def fork_local_agent_project(source_id: str, project_id: str, name: str = "") -> str:
    source_root = agent_project_root_for_id(source_id)
    if not source_root:
        return f"找不到 Agent Project：{source_id}"
    result = agent_project_helpers.fork_agent_project(
        source_root,
        _host().SHUHENG_AGENT_PROJECTS_DIR,
        project_id=project_id,
        name=name,
    )
    if not result.ok or result.value is None:
        return "Agent Project Fork 失败：\n" + "\n".join(agent_project_diagnostic_lines(result))
    return f"已 Fork Agent Project：{source_id} → {result.value.project_id}"


def build_local_agent_project(project_id: str) -> tuple[Any, str]:
    root = agent_project_root_for_id(project_id)
    if not root:
        return None, f"找不到 Agent Project：{project_id}"
    result = agent_project_helpers.compile_agent_project(root)
    if not result.ok or result.build is None:
        return None, "Agent Project 构建失败：\n" + "\n".join(agent_project_diagnostic_lines(result))
    build = result.build
    if build.runtime != "pi-native":
        return None, f"MVP 仅运行 pi-native worker；当前 Build 声明为 {build.runtime!r}。"
    if build.runtime_version and build.runtime_version != PI_NATIVE_SDK_VERSION:
        return None, (
            f"MVP 固定使用 Pi SDK {PI_NATIVE_SDK_VERSION}；"
            f"当前 Build 声明为 {build.runtime_version!r}。"
        )
    return build, (
        f"Build 成功：{build.project.project_id} · {build.digest}\n"
        f"Prompt 1 · Skill {len(build.blueprint.skills)} · Tool {len(build.blueprint.tools)} · "
        f"requested={list(build.blueprint.requested_capabilities)}"
    )


def agent_project_subagent(state: Any, build: Any) -> Any:
    host = _host()
    if bool(getattr(getattr(state, "secret_vault", None), "unlocked", False)):
        raise RuntimeError("Agent Project MVP 仅支持 standard 受管任务通道；请先锁定 Secret Vault。")
    project_id = str(build.project.project_id)
    source_root = str(build.project.source_root)
    for sub in state.subagents.values():
        if sub.agent_project_id != project_id:
            continue
        if sub.status in {"running", "aborting"} and sub.runtime_provider_id != "pi-native":
            raise RuntimeError(f"{sub.name} 正在运行，不能切换为 pi-native。")
        sub.runtime_provider_id = "pi-native"
        sub.agent_project_root = source_root
        # Project-local executable Tools are trusted host code in this MVP, so
        # every Agent Project worker uses the single-writer role conservatively.
        sub.role = "coder"
        # A queued confirmation carries its own digest. Do not make the next
        # Build look active while the current task is still running.
        if sub.status not in {"running", "aborting"}:
            sub.agent_build_digest = build.digest
        sub.updated_at = time.time()
        host.save_subagent_meta(sub)
        return sub
    return host.create_subagent(
        state,
        f"Pi · {build.project.name}",
        profile=(
            f"# {build.project.name}\n\n"
            "- 这是由 Shuheng 强主控调度的 Pi-native 任务型 worker。\n"
            f"- Agent Project：{project_id}。\n"
            "- Prompt、Skill 和项目内 Tool 只来自当前已冻结 Build。\n"
            "- 不拥有调度权、权限授予权、长期记忆直写权或控制面状态所有权。\n"
        ),
        role="coder",
        persistent=True,
        runtime_provider_id="pi-native",
        agent_project_id=project_id,
        agent_project_root=source_root,
        agent_build_digest=build.digest,
    )


def run_local_agent_project(
    state: Any,
    project_id: str,
    objective: str,
    *,
    grant_declared: bool = False,
    expected_build_digest: str = "",
) -> str:
    host = _host()
    objective = (objective or "").strip()
    if not objective:
        return "Agent Project 运行目标不能为空。"
    build, message = build_local_agent_project(project_id)
    if build is None:
        return message
    expected_build_digest = str(expected_build_digest or "").strip().lower()
    if expected_build_digest and build.digest != expected_build_digest:
        return (
            "Agent Project 源码在确认后发生了变化，已阻止运行。\n"
            f"已确认 Build：{expected_build_digest}\n"
            f"当前 Build：{build.digest}\n"
            "请重新查看权限并确认新的冻结 Build。"
        )
    has_authority_requests = bool(build.blueprint.requested_capabilities or build.blueprint.tools)
    if has_authority_requests and not grant_declared:
        return (
            "该 Build 声明了 capability 或项目内 Tool，尚未获得运行授权。\n"
            "请在 /agent-projects 工作台按 Ctrl+R 查看并确认，或显式使用：\n"
            f"/agent-project run {project_id} --grant-declared <objective>"
        )
    try:
        sub = host.agent_project_subagent(state, build)
    except Exception as exc:
        return f"Agent Project worker 准备失败：{type(exc).__name__}: {exc}"
    source = "user:agent_project:approved" if grant_declared else "user:agent_project"
    result = host.start_subagent_task(
        state,
        sub,
        objective,
        source=source,
        # The explicit capability/Tool grant is not a blanket approval for the
        # task itself. Keep the normal Shuheng policy gate in the dispatch path.
        policy_approved=False,
        task_title=f"Agent Project: {project_id}",
        expected_build_digest=build.digest,
        agent_project_grant_declared=grant_declared,
    )
    return f"{message}\n{result}"


def pi_native_model_runtime_payload() -> dict[str, Any]:
    """Translate the Shuheng default model into a transient Pi SDK model record."""

    host = _host()
    entries, _mixin, _preserved, error = host.load_llm_config_entries()
    entry = host.configured_global_default_entry()
    if error or entry is None:
        provider = os.environ.get("SHUHENG_PI_NATIVE_MODEL_PROVIDER", "").strip()
        model_id = os.environ.get("SHUHENG_PI_NATIVE_MODEL", "").strip()
        if not provider or not model_id:
            return {}
        return {
            "provider": provider,
            "id": model_id,
            "api_key": os.environ.get("SHUHENG_PI_NATIVE_API_KEY", "").strip(),
            "base_url": os.environ.get("SHUHENG_PI_NATIVE_BASE_URL", "").strip(),
            "api": os.environ.get("SHUHENG_PI_NATIVE_API", "openai-completions").strip(),
            "thinking_level": os.environ.get("SHUHENG_PI_NATIVE_THINKING", "off").strip() or "off",
        }
    index = next((idx for idx, item in enumerate(entries) if item.var_name == entry.var_name), 0)
    cfg = entry.cfg
    model_id = str(cfg.get("model") or "").strip()
    if not model_id:
        return {}
    headers = cfg.get("headers") if isinstance(cfg.get("headers"), dict) else {}
    return {
        "provider": host.ohmypi_provider_id_for_entry(entry, index),
        "id": model_id,
        "name": host.config_display_name(entry),
        "api": host.ohmypi_model_api_for_entry(entry),
        "api_key": str(cfg.get("apikey") or "").strip(),
        "base_url": str(cfg.get("apibase") or "").strip(),
        "headers": {str(key): str(value) for key, value in headers.items()},
        "auth_header": bool(cfg.get("auth_header", True)),
        "reasoning": bool(cfg.get("reasoning", False)),
        "context_window": host.positive_int_config_value(cfg.get("context_window")) or 128000,
        "max_tokens": host.positive_int_config_value(cfg.get("max_tokens")) or 16384,
        "thinking_level": str(cfg.get("thinking_level") or "off").strip() or "off",
    }


def prepare_agent_project_runtime_envelope(
    build: Any,
    *,
    assignment_id: str,
    grant_declared: bool,
    causation_refs: list[str] | None = None,
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Create a safe durable manifest plus a transient frozen Build payload."""

    host = _host()
    granted_capabilities = list(build.blueprint.requested_capabilities) if grant_declared else []
    granted_tool_ids = [item.tool_id for item in build.blueprint.tools] if grant_declared else []
    result = agent_project_helpers.create_agent_run_manifest(
        build,
        assignment_id=assignment_id,
        granted_capabilities=granted_capabilities,
        granted_tool_ids=granted_tool_ids,
        workspace=host.current_workspace_root(),
        provider_revision=PI_NATIVE_SDK_VERSION,
        causation_refs=causation_refs or [],
    )
    if not result.ok or result.value is None:
        raise RuntimeError("; ".join(agent_project_diagnostic_lines(result)))
    manifest_record = result.value.to_record()
    manifest_ref = host.write_harness_artifact(
        "agent_project_runs",
        f"{assignment_id}.json",
        json.dumps(manifest_record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        source_task_id=assignment_id,
        provenance={
            "generated_by": "orchestrator.main",
            "project_id": build.project.project_id,
            "build_digest": build.digest,
            "provider_id": "pi-native",
        },
        content_type="application/json",
    )
    runtime_payload = {
        "agent_build": build.to_record(),
        "agent_run_manifest": manifest_record,
    }
    model_payload = host.pi_native_model_runtime_payload()
    if model_payload:
        runtime_payload["model"] = model_payload
    durable_metadata = {
        "agent_project_id": build.project.project_id,
        "agent_build_digest": build.digest,
        "agent_run_manifest_ref": manifest_ref,
    }
    return runtime_payload, manifest_ref, durable_metadata


def handle_agent_project_command(state: Any, text: str) -> bool:
    host = _host()
    match = re.match(r"^/agent-project(?:\s+(.*))?\s*$", text, re.I | re.S)
    if not match:
        return False
    body = (match.group(1) or "").strip()
    if not body or body.lower() in {"list", "ls", "status"}:
        host.add_system(state, agent_project_inventory_text())
        return True
    try:
        args = shlex.split(body)
    except ValueError as exc:
        host.add_system(state, f"Agent Project 命令解析失败：{exc}")
        return True
    verb = args[0].lower() if args else ""
    if verb == "create" and len(args) >= 2:
        host.add_system(state, create_local_agent_project(args[1], " ".join(args[2:])))
        return True
    if verb == "fork" and len(args) >= 3:
        host.add_system(state, fork_local_agent_project(args[1], args[2], " ".join(args[3:])))
        return True
    if verb == "build" and len(args) == 2:
        _build, message = build_local_agent_project(args[1])
        host.add_system(state, message)
        return True
    if verb == "run" and len(args) >= 3:
        project_id = args[1]
        tail = args[2:]
        grant_declared = "--grant-declared" in tail
        tail = [item for item in tail if item != "--grant-declared"]
        host.add_system(
            state,
            run_local_agent_project(state, project_id, " ".join(tail), grant_declared=grant_declared),
        )
        return True
    host.add_system(
        state,
        "Agent Project 用法：\n"
        "/agent-project list\n"
        "/agent-project create <id> [name]\n"
        "/agent-project fork <source-id> <new-id> [name]\n"
        "/agent-project build <id>\n"
        "/agent-project run <id> [--grant-declared] <objective>\n"
        "/agent-projects  # 打开内嵌单文件工作台",
    )
    return True


def draw_agent_project_input_modal(
    stdscr: Any,
    state: Any,
    *,
    title: str,
    prompt: str,
    text: str,
    cursor: int,
    detail: list[str] | None = None,
    message: str = "",
) -> None:
    host = _host()
    host.redraw(stdscr, state)
    height, width = stdscr.getmaxyx()
    y0, x0, h, w = host.popup_geometry(height, width, min_h=12, min_w=76)
    host.draw_popup(stdscr, y0, x0, h, w, title)
    inner_w = w - 4
    y = y0 + 2
    for raw in detail or []:
        for line in host.wrap_cells(raw, inner_w):
            if y >= y0 + h - 6:
                break
            host.safe_add(stdscr, y, x0 + 2, line, inner_w, host.cp(2))
            y += 1
    field_y = y0 + h - 4
    field = f"{prompt}> "
    host.safe_add(stdscr, field_y, x0 + 2, " " * inner_w, inner_w, host.cp(11))
    host.safe_add(
        stdscr,
        field_y,
        x0 + 2,
        host.truncate_cells(field + text, inner_w),
        inner_w,
        host.cp(11),
    )
    if message:
        host.safe_add(
            stdscr,
            y0 + h - 3,
            x0 + 2,
            host.truncate_cells(message, inner_w),
            inner_w,
            host.cp(5),
        )
    host.safe_add(stdscr, y0 + h - 2, x0 + 2, "Enter 确认  Esc 取消  ←/→ 移动", inner_w, host.cp(1))
    try:
        cursor_x = x0 + 2 + min(inner_w - 1, host.cell_width(field + text[:cursor]))
        stdscr.move(field_y, cursor_x)
    except curses.error:
        pass
    stdscr.refresh()


def open_agent_project_text_prompt(
    stdscr: Any,
    state: Any,
    *,
    title: str,
    prompt: str,
    detail: list[str] | None = None,
    initial: str = "",
) -> Optional[str]:
    host = _host()
    text = initial
    cursor = len(text)
    paste_mode = False
    paste_buffer = ""
    old_timeout = host.TUI_POLL_TIMEOUT_MS
    try:
        host.drain_pending_keys(stdscr)
        stdscr.timeout(-1)
        while True:
            cursor = max(0, min(cursor, len(text)))
            draw_agent_project_input_modal(
                stdscr,
                state,
                title=title,
                prompt=prompt,
                text=text,
                cursor=cursor,
                detail=detail,
            )
            try:
                key = host.modal_read_key(stdscr)
            except (KeyboardInterrupt, curses.error):
                return None
            if key == host.PASTE_START:
                paste_mode = True
                paste_buffer = ""
                continue
            if key == host.PASTE_END and paste_mode:
                paste_mode = False
                inserted = host.normalize_pasted_text(paste_buffer)
                text = text[:cursor] + inserted + text[cursor:]
                cursor += len(inserted)
                paste_buffer = ""
                continue
            if paste_mode:
                if isinstance(key, str):
                    paste_buffer += key
                continue
            if key in ("\x1b", 27, "\x03"):
                return None
            if key in ("\n", "\r", curses.KEY_ENTER):
                return text.strip()
            if key == curses.KEY_LEFT:
                cursor -= 1
            elif key == curses.KEY_RIGHT:
                cursor += 1
            elif key == curses.KEY_HOME:
                cursor = 0
            elif key == curses.KEY_END:
                cursor = len(text)
            elif key in (curses.KEY_BACKSPACE, 127, "\b") and cursor > 0:
                text = text[: cursor - 1] + text[cursor:]
                cursor -= 1
            elif key == curses.KEY_DC and cursor < len(text):
                text = text[:cursor] + text[cursor + 1 :]
            elif isinstance(key, str) and key.isprintable():
                text = text[:cursor] + key + text[cursor:]
                cursor += len(key)
    finally:
        stdscr.timeout(old_timeout)
        host.mark_dirty(state)


def confirm_agent_project_action(
    stdscr: Any,
    state: Any,
    *,
    title: str,
    lines: list[str],
    confirm_label: str = "确认",
) -> bool:
    host = _host()
    host.draw_modal_notice(
        stdscr,
        state,
        title,
        lines,
        footer=f"Enter {confirm_label}  Esc 取消",
    )
    while True:
        try:
            key = host.modal_read_key(stdscr)
        except (KeyboardInterrupt, curses.error):
            return False
        if key in ("\n", "\r", curses.KEY_ENTER):
            return True
        if key in ("\x1b", 27, "\x03"):
            return False


def agent_project_list_window(items: list[str], selected: int, rows: int) -> tuple[int, list[str]]:
    rows = max(1, rows)
    selected = max(0, min(selected, max(0, len(items) - 1)))
    start = max(0, selected - rows // 2)
    start = min(start, max(0, len(items) - rows))
    return start, items[start : start + rows]


def agent_project_source_style(path: Path, line: str) -> int:
    host = _host()
    stripped = line.lstrip()
    suffix = path.suffix.casefold()
    if suffix in {".md", ".markdown"}:
        if stripped.startswith("#"):
            return host.cp(3) | curses.A_BOLD
        if stripped.startswith(("- ", "* ", "> ", "```")):
            return host.cp(7)
    if suffix in {".json", ".jsonc"}:
        if stripped.startswith("//"):
            return host.cp(1)
        if re.match(r'^\s*"[^"\\]+"\s*:', line):
            return host.cp(3)
    if suffix in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}:
        if stripped.startswith(("//", "/*", "*")):
            return host.cp(1)
        if re.match(r"^(export\s+)?(const|let|function|class|import)\b", stripped):
            return host.cp(3)
    return host.cp(2)


def draw_agent_project_workspace(
    stdscr: Any,
    state: Any,
    *,
    project_roots: list[str],
    project_index: int,
    files: list[str],
    file_index: int,
    focus: str,
    editor: Optional[AgentEditor],
    message: str,
    build_digest: str,
) -> None:
    host = _host()
    host.redraw(stdscr, state)
    height, width = stdscr.getmaxyx()
    h = max(3, min(max(18, int(height * 0.92)), max(3, height - 2)))
    w = max(10, min(max(82, int(width * 0.94)), max(10, width - 2)))
    y0 = max(0, (height - h) // 2)
    x0 = max(0, (width - w) // 2)
    host.draw_popup(stdscr, y0, x0, h, w, "Agent Projects · OMP 主控 / Pi-native Worker")
    inner_w = w - 4
    body_top = y0 + 3
    body_bottom = y0 + h - 4
    body_rows = max(1, body_bottom - body_top)
    rail_w = min(34, max(24, w // 4))
    editor_x = x0 + 3 + rail_w
    editor_w = max(20, x0 + w - 2 - editor_x)
    project_name = Path(project_roots[project_index]).name if project_roots else "(none)"
    state_bits = [f"project {project_name}", "source editable", "runtime governed"]
    if build_digest:
        state_bits.append(f"build {build_digest[:12]}")
    if editor is not None and editor.dirty:
        state_bits.append("● unsaved")
    if editor is not None and editor.external_conflict:
        state_bits.append("! external change")
    host.safe_add(stdscr, y0 + 2, x0 + 2, " · ".join(state_bits), inner_w, host.cp(7))
    for row in range(body_rows):
        host.safe_add(stdscr, body_top + row, x0 + 2, " " * rail_w, rail_w, host.cp(8))
    try:
        for row in range(body_rows):
            stdscr.addch(body_top + row, editor_x - 1, curses.ACS_VLINE, host.cp(1))
    except curses.error:
        pass

    project_rows = min(6, max(3, body_rows // 3))
    host.safe_add(
        stdscr,
        body_top,
        x0 + 3,
        "PROJECTS" + ("  ◀" if focus == "projects" else ""),
        rail_w - 2,
        host.cp(3) | curses.A_BOLD,
    )
    labels = [Path(item).name for item in project_roots]
    start, shown = agent_project_list_window(labels, project_index, project_rows - 1)
    for offset, label in enumerate(shown):
        actual = start + offset
        style = host.cp(11) if actual == project_index else host.cp(8)
        marker = "› " if actual == project_index else "  "
        host.safe_add(stdscr, body_top + 1 + offset, x0 + 3, marker + label, rail_w - 2, style)

    files_top = body_top + project_rows + 1
    host.safe_add(
        stdscr,
        files_top,
        x0 + 3,
        "FILES" + ("  ◀" if focus == "files" else ""),
        rail_w - 2,
        host.cp(3) | curses.A_BOLD,
    )
    available_file_rows = max(1, body_bottom - files_top - 1)
    start, shown_files = agent_project_list_window(files, file_index, available_file_rows)
    for offset, path in enumerate(shown_files):
        actual = start + offset
        style = host.cp(11) if actual == file_index else host.cp(8)
        marker = "› " if actual == file_index else "  "
        host.safe_add(stdscr, files_top + 1 + offset, x0 + 3, marker + path, rail_w - 2, style)

    if editor is None:
        empty_lines = [
            "选择一个文件并按 Enter 开始编辑。",
            "",
            "N  新建工程    F  Fork",
            "A  新建文件    Ctrl+B 构建",
            "Ctrl+R 运行     Tab 切换区域",
        ]
        for offset, line in enumerate(empty_lines[:body_rows]):
            host.safe_add(stdscr, body_top + offset, editor_x + 1, line, editor_w - 2, host.cp(2))
    else:
        relative = editor.path.relative_to(editor.project_root).as_posix()
        title_style = host.cp(3) | curses.A_BOLD if focus == "editor" else host.cp(7)
        host.safe_add(stdscr, body_top, editor_x + 1, relative, editor_w - 2, title_style)
        edit_top = body_top + 2
        edit_rows = max(1, body_bottom - edit_top)
        line_number_w = max(3, len(str(len(editor.lines))))
        text_w = max(1, editor_w - line_number_w - 4)
        editor.ensure_cursor_visible(edit_rows, text_w)
        for screen_row in range(edit_rows):
            line_index = editor.viewport.top + screen_row
            if line_index >= len(editor.lines):
                break
            raw_line = editor.lines[line_index]
            number_style = host.cp(3) if line_index == editor.cursor.line else host.cp(1)
            host.safe_add(
                stdscr,
                edit_top + screen_row,
                editor_x + 1,
                str(line_index + 1).rjust(line_number_w),
                line_number_w,
                number_style,
            )
            host.safe_add(
                stdscr,
                edit_top + screen_row,
                editor_x + line_number_w + 3,
                raw_line[editor.viewport.left :],
                text_w,
                agent_project_source_style(editor.path, raw_line),
            )
        if focus == "editor":
            try:
                cursor_line = edit_top + editor.cursor.line - editor.viewport.top
                prefix = editor.lines[editor.cursor.line][editor.viewport.left : editor.cursor.column]
                cursor_x = editor_x + line_number_w + 3 + min(text_w - 1, host.cell_width(prefix))
                stdscr.move(cursor_line, cursor_x)
            except curses.error:
                pass
    if message:
        is_error = any(token in message.lower() for token in ("失败", "错误", "invalid", "conflict"))
        host.safe_add(
            stdscr,
            y0 + h - 3,
            x0 + 2,
            host.truncate_cells(message, inner_w),
            inner_w,
            host.cp(5) if is_error else host.cp(7),
        )
    footer = "Tab 区域  Enter 打开/换行  Ctrl+S 保存  Ctrl+L 重载  Ctrl+Z 撤销  Ctrl+B 构建  Ctrl+R 运行  Esc 返回"
    host.safe_add(stdscr, y0 + h - 2, x0 + 2, footer, inner_w, host.cp(1))
    stdscr.refresh()


def new_agent_project_authoring_editor(project_root: str, relative_path: str) -> AgentEditor:
    relative_path = (relative_path or "").strip().replace("\\", "/")
    parts = tuple(part for part in relative_path.split("/") if part)
    if (
        not relative_path
        or relative_path.startswith(("/", "~"))
        or not parts
        or any(part in {".", ".."} or part.startswith(".") for part in parts)
        or not is_allowed_authoring_path(relative_path)
    ):
        raise AgentEditorError("请输入项目内相对文本路径，例如 tools/local-tool.mjs 或 skills/review/SKILL.md。")
    root = Path(project_root).resolve(strict=True)
    candidate = root.joinpath(*parts)
    parent = candidate.parent.resolve(strict=False)
    if os.path.commonpath((str(root), str(parent))) != str(root):
        raise AgentEditorError("新文件必须位于 Agent Project 内。")
    if candidate.exists() or candidate.is_symlink():
        raise AgentEditorError(f"文件已经存在：{relative_path}")
    parent.mkdir(parents=True, exist_ok=True)
    editor = AgentEditor.open(root, relative_path, create=True, validator=agent_project_editor_validator)
    suffix = candidate.suffix.casefold()
    if suffix == ".json":
        editor.paste("{}\n")
    elif suffix in {".md", ".markdown"}:
        editor.paste("# New Agent Resource\n")
    elif suffix in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}:
        editor.paste("// Project-local Pi tool source. Declare this path in agent.json before build.\n")
    return editor


def open_agent_project_workspace(stdscr: Any, state: Any) -> None:
    host = _host()
    os.makedirs(host.SHUHENG_AGENT_PROJECTS_DIR, exist_ok=True)
    project_index = 0
    file_index = 0
    focus = "projects"
    editor: Optional[AgentEditor] = None
    editor_ref = ""
    message = "N 新建工程；选择文件后 Enter 编辑。OMP 仍是主 Agent。"
    build_digest = ""
    paste_mode = False
    paste_buffer = ""
    old_timeout = host.TUI_POLL_TIMEOUT_MS

    def discard_or_keep() -> bool:
        if editor is None or not editor.dirty:
            return True
        return confirm_agent_project_action(
            stdscr,
            state,
            title="未保存修改",
            lines=[f"{editor.path.name} 还有未保存修改。", "继续会丢弃当前缓冲区，但不会改动磁盘文件。"],
            confirm_label="丢弃",
        )

    try:
        host.drain_pending_keys(stdscr)
        stdscr.timeout(-1)
        while True:
            project_roots = local_agent_project_roots()
            project_index = max(0, min(project_index, max(0, len(project_roots) - 1)))
            project_root = project_roots[project_index] if project_roots else ""
            files = agent_project_authoring_files(project_root) if project_root else []
            file_index = max(0, min(file_index, max(0, len(files) - 1)))
            if editor is not None:
                try:
                    editor.check_external_conflict()
                except AgentEditorError:
                    editor.external_conflict = True
            draw_agent_project_workspace(
                stdscr,
                state,
                project_roots=project_roots,
                project_index=project_index,
                files=files,
                file_index=file_index,
                focus=focus,
                editor=editor,
                message=message,
                build_digest=build_digest,
            )
            message = ""
            try:
                key = host.modal_read_key(stdscr)
            except KeyboardInterrupt:
                if discard_or_keep():
                    return
                continue
            except curses.error:
                continue
            if key == host.PASTE_START and focus == "editor" and editor is not None:
                paste_mode = True
                paste_buffer = ""
                continue
            if key == host.PASTE_END and paste_mode:
                paste_mode = False
                if editor is not None:
                    editor.paste(paste_buffer)
                paste_buffer = ""
                continue
            if paste_mode:
                if isinstance(key, str):
                    paste_buffer += key
                continue
            if key in ("\x1b", 27, "\x03"):
                if focus == "editor":
                    focus = "files"
                    message = "已返回文件列表；编辑缓冲区仍保留。"
                    continue
                if discard_or_keep():
                    return
                focus = "editor"
                continue
            if key == "\t":
                order = ["projects", "files", "editor"] if editor is not None else ["projects", "files"]
                focus = order[(order.index(focus) + 1) % len(order)] if focus in order else order[0]
                continue
            if key in ("n", "N") and focus != "editor":
                project_id = open_agent_project_text_prompt(
                    stdscr,
                    state,
                    title="New Agent Project",
                    prompt="id",
                    detail=["创建本地 Pi-native worker 工程。ID 只能使用 ASCII 字母、数字、点、横线和下划线。"],
                )
                if project_id is not None:
                    message = create_local_agent_project(project_id)
                    roots = local_agent_project_roots()
                    project_index = next(
                        (i for i, item in enumerate(roots) if Path(item).name == project_id),
                        project_index,
                    )
                    editor = None
                    editor_ref = ""
                continue
            if key in ("f", "F") and focus != "editor" and project_root:
                new_id = open_agent_project_text_prompt(
                    stdscr,
                    state,
                    title="Fork Agent Project",
                    prompt="new id",
                    detail=[f"来源：{Path(project_root).name}", "Fork 会复制可编辑源码，但之后拥有独立 Build digest。"],
                )
                if new_id is not None:
                    message = fork_local_agent_project(Path(project_root).name, new_id)
                continue
            if key in ("a", "A") and focus == "files" and project_root:
                relative = open_agent_project_text_prompt(
                    stdscr,
                    state,
                    title="New Agent Project File",
                    prompt="path",
                    detail=["示例：skills/review/SKILL.md 或 tools/local-tool.mjs", "新文件仍需在 agent.json 中显式声明才会进入 Build。"],
                )
                if relative:
                    if not discard_or_keep():
                        continue
                    try:
                        editor = new_agent_project_authoring_editor(project_root, relative)
                        editor_ref = relative
                        focus = "editor"
                        message = "新文件尚未落盘；Ctrl+S 原子保存。"
                    except (AgentEditorError, OSError, ValueError) as exc:
                        message = f"新建文件失败：{exc}"
                continue
            if key == "\x02":  # Ctrl+B
                if not project_root:
                    message = "请先创建或选择 Agent Project。"
                elif editor is not None and editor.dirty:
                    message = "构建前请先 Ctrl+S 保存当前文件。"
                else:
                    build, message = build_local_agent_project(Path(project_root).name)
                    build_digest = build.digest if build is not None else ""
                continue
            if key == "\x12":  # Ctrl+R
                if not project_root:
                    message = "请先创建或选择 Agent Project。"
                    continue
                if editor is not None and editor.dirty:
                    message = "运行前请先 Ctrl+S 保存并构建当前源码。"
                    continue
                build, build_message = build_local_agent_project(Path(project_root).name)
                if build is None:
                    message = build_message
                    continue
                objective = open_agent_project_text_prompt(
                    stdscr,
                    state,
                    title="Run Pi-native Worker",
                    prompt="objective",
                    detail=[
                        f"Project：{build.project.project_id}",
                        f"Build：{build.digest[:16]}",
                        "任务结果会回到 Shuheng task ledger 并进入 OMP 上下文，供主控后续综合。",
                    ],
                )
                if not objective:
                    message = "运行已取消。"
                    continue
                requested = list(build.blueprint.requested_capabilities)
                tool_ids = [item.tool_id for item in build.blueprint.tools]
                grant = True
                if requested or tool_ids:
                    grant = confirm_agent_project_action(
                        stdscr,
                        state,
                        title="Grant Agent Project Authority",
                        lines=[
                            f"Project：{build.project.project_id}",
                            f"Build：{build.digest}",
                            f"requested capabilities：{requested or '(none)'}",
                            f"project-local tools：{tool_ids or '(none)'}",
                            "Enter 只授权这次冻结 Build；源码后续变化不会进入本次运行。",
                            "项目内 Tool 是本机代码。MVP 尚未提供 OS 级进程沙箱，只运行你信任的源码。",
                        ],
                        confirm_label="授权并运行",
                    )
                if grant:
                    message = run_local_agent_project(
                        state,
                        build.project.project_id,
                        objective,
                        grant_declared=bool(requested or tool_ids),
                        expected_build_digest=build.digest,
                    )
                    build_digest = build.digest
                else:
                    message = "未授予 capability / Tool，运行已取消。"
                continue
            if editor is not None and key == "\x13":  # Ctrl+S
                try:
                    editor.save()
                    editor_ref = editor.path.relative_to(editor.project_root).as_posix()
                    compiled, build_message = build_local_agent_project(Path(project_root).name)
                    if compiled is None:
                        message = f"已保存 {editor_ref}；{build_message.replace(chr(10), ' · ')}"
                        build_digest = ""
                    else:
                        build_digest = compiled.digest
                        message = f"已保存 {editor_ref} · Build {compiled.digest[:12]}"
                except ExternalFileConflictError:
                    message = "保存被阻止：文件已被外部编辑器修改。Ctrl+L 重载，或先在外部处理差异。"
                except (AgentEditorError, OSError) as exc:
                    message = f"保存失败：{type(exc).__name__}: {exc}"
                continue
            if editor is not None and key == "\x0c":  # Ctrl+L
                if editor.dirty and not confirm_agent_project_action(
                    stdscr,
                    state,
                    title="Reload External File",
                    lines=["重载会丢弃当前未保存缓冲区，并采用磁盘上的最新版本。"],
                    confirm_label="重载",
                ):
                    message = "重载已取消。"
                    continue
                try:
                    editor.reload()
                    message = "已重载磁盘文件；外部冲突已清除。"
                except (AgentEditorError, OSError) as exc:
                    message = f"重载失败：{type(exc).__name__}: {exc}"
                continue
            if editor is not None and key == "\x1a":  # Ctrl+Z
                message = "已撤销一步。" if editor.undo() else "没有可撤销的编辑。"
                continue
            if focus == "projects":
                if key == curses.KEY_UP and project_roots:
                    if editor is not None and editor.dirty:
                        message = "切换工程前请保存当前文件，或 Esc 退出时确认丢弃。"
                    else:
                        project_index = (project_index - 1) % len(project_roots)
                        file_index = 0
                        editor = None
                        editor_ref = ""
                        build_digest = ""
                elif key == curses.KEY_DOWN and project_roots:
                    if editor is not None and editor.dirty:
                        message = "切换工程前请保存当前文件，或 Esc 退出时确认丢弃。"
                    else:
                        project_index = (project_index + 1) % len(project_roots)
                        file_index = 0
                        editor = None
                        editor_ref = ""
                        build_digest = ""
                elif key in (curses.KEY_RIGHT, "\n", "\r", curses.KEY_ENTER):
                    focus = "files"
                continue
            if focus == "files":
                if key == curses.KEY_UP and files:
                    file_index = (file_index - 1) % len(files)
                elif key == curses.KEY_DOWN and files:
                    file_index = (file_index + 1) % len(files)
                elif key == curses.KEY_LEFT:
                    focus = "projects"
                elif key in (curses.KEY_RIGHT, "\n", "\r", curses.KEY_ENTER) and files:
                    selected_ref = files[file_index]
                    opened_in_project = bool(
                        editor is not None and editor.project_root == Path(project_root).resolve(strict=False)
                    )
                    if not opened_in_project or editor_ref != selected_ref:
                        if not discard_or_keep():
                            continue
                        try:
                            editor = AgentEditor.open(
                                project_root,
                                selected_ref,
                                validator=agent_project_editor_validator,
                            )
                            editor_ref = selected_ref
                        except (AgentEditorError, OSError) as exc:
                            message = f"打开文件失败：{type(exc).__name__}: {exc}"
                            continue
                    focus = "editor"
                continue
            if focus == "editor" and editor is not None:
                edit_rows = max(3, stdscr.getmaxyx()[0] - 10)
                if key == curses.KEY_LEFT:
                    editor.move_left()
                elif key == curses.KEY_RIGHT:
                    editor.move_right()
                elif key == curses.KEY_UP:
                    editor.move_up()
                elif key == curses.KEY_DOWN:
                    editor.move_down()
                elif key == curses.KEY_HOME:
                    editor.move_home()
                elif key == curses.KEY_END:
                    editor.move_end()
                elif key == curses.KEY_PPAGE:
                    editor.page_up(edit_rows)
                elif key == curses.KEY_NPAGE:
                    editor.page_down(edit_rows)
                elif key in (curses.KEY_BACKSPACE, 127, "\b"):
                    editor.backspace()
                elif key == curses.KEY_DC:
                    editor.delete_forward()
                elif key in ("\n", "\r", curses.KEY_ENTER):
                    editor.newline_at_cursor()
                elif key == getattr(curses, "KEY_F8", -1) and editor.diagnostics:
                    editor.goto_diagnostic(0)
                elif isinstance(key, str) and key.isprintable():
                    editor.insert_text(key)
    finally:
        stdscr.timeout(old_timeout)
        host.mark_dirty(state)


__all__ = [
    "agent_project_authoring_files",
    "agent_project_diagnostic_lines",
    "agent_project_editor_validator",
    "agent_project_inventory_text",
    "agent_project_list_window",
    "agent_project_root_for_id",
    "agent_project_source_style",
    "agent_project_subagent",
    "build_local_agent_project",
    "confirm_agent_project_action",
    "configure_agent_project_workspace",
    "create_local_agent_project",
    "draw_agent_project_input_modal",
    "draw_agent_project_workspace",
    "fork_local_agent_project",
    "handle_agent_project_command",
    "local_agent_project_roots",
    "new_agent_project_authoring_editor",
    "open_agent_project_text_prompt",
    "open_agent_project_workspace",
    "pi_native_model_runtime_payload",
    "prepare_agent_project_runtime_envelope",
    "run_local_agent_project",
]
