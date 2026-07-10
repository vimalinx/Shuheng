"""Governed Shuheng subagent task dispatch extracted from the TUI monolith."""
from __future__ import annotations

from pathlib import Path
import threading
import time
from typing import Any, Optional

try:
    from .ui_types import Message, PolicyDecision, State, SubAgentRuntime
except ImportError:  # pragma: no cover - direct source-tree compatibility
    from ui_types import Message, PolicyDecision, State, SubAgentRuntime  # type: ignore

_HOST_NAMES = (
    "acquire_single_writer_lock",
    "active_ui_session_key",
    "agent_has_unfinished_task",
    "agent_project_diagnostic_lines",
    "agent_project_helpers",
    "agent_project_root_for_id",
    "agent_runtime_provider_id",
    "append_agent_mail",
    "append_orchestrator_plan",
    "append_subagent_event",
    "append_task_checkpoint",
    "append_task_ledger",
    "append_trace",
    "apply_subagent_default_model",
    "approval_metadata",
    "build_context_pack",
    "consume_subagent_queue",
    "context_policy_for_task",
    "default_task_budget",
    "display_prompt_for_subagent_task",
    "ensure_subagent_agent",
    "infer_policy_action_for_subagent_task",
    "mark_dirty",
    "mark_subagent_messages_changed",
    "normalized_subagent_role",
    "permissions_for_role",
    "policy_decision_to_dict",
    "policy_gate_for_subagent_task",
    "policy_gate_text",
    "policy_relevant_subagent_prompt_text",
    "prepare_agent_project_runtime_envelope",
    "put_agent_runtime_task",
    "queue_subagent_task",
    "record_shared_user_profile_interaction",
    "release_single_writer_lock",
    "risks_for_action",
    "role_output_contract",
    "runtime_context_prompt_for_agent",
    "runtime_prompt_with_transient_skill_command",
    "runtime_task_request_for_agent",
    "save_subagent_chat_session",
    "save_subagent_meta",
    "short_uid",
    "split_transient_skill_prompt",
    "start_secret_subagent_task",
    "subagent_task_schema_kwargs",
    "task_contract_for_role",
    "truncate_cells",
    "update_plan_step_from_child",
)


_HOST: Any = None


class _HostBinding:
    """Late-bound facade that preserves app monkeypatch compatibility."""

    def __init__(self, name: str) -> None:
        self.name = name

    def _target(self) -> Any:
        if _HOST is None:
            raise RuntimeError("Subagent task dispatch host is not configured")
        return getattr(_HOST, self.name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._target()(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target(), name)


(
    acquire_single_writer_lock,
    active_ui_session_key,
    agent_has_unfinished_task,
    agent_project_diagnostic_lines,
    agent_project_helpers,
    agent_project_root_for_id,
    agent_runtime_provider_id,
    append_agent_mail,
    append_orchestrator_plan,
    append_subagent_event,
    append_task_checkpoint,
    append_task_ledger,
    append_trace,
    apply_subagent_default_model,
    approval_metadata,
    build_context_pack,
    consume_subagent_queue,
    context_policy_for_task,
    default_task_budget,
    display_prompt_for_subagent_task,
    ensure_subagent_agent,
    infer_policy_action_for_subagent_task,
    mark_dirty,
    mark_subagent_messages_changed,
    normalized_subagent_role,
    permissions_for_role,
    policy_decision_to_dict,
    policy_gate_for_subagent_task,
    policy_gate_text,
    policy_relevant_subagent_prompt_text,
    prepare_agent_project_runtime_envelope,
    put_agent_runtime_task,
    queue_subagent_task,
    record_shared_user_profile_interaction,
    release_single_writer_lock,
    risks_for_action,
    role_output_contract,
    runtime_context_prompt_for_agent,
    runtime_prompt_with_transient_skill_command,
    runtime_task_request_for_agent,
    save_subagent_chat_session,
    save_subagent_meta,
    short_uid,
    split_transient_skill_prompt,
    start_secret_subagent_task,
    subagent_task_schema_kwargs,
    task_contract_for_role,
    truncate_cells,
    update_plan_step_from_child,
) = tuple(_HostBinding(name) for name in _HOST_NAMES)


def configure_subagent_task_dispatch(host: Any) -> None:
    """Inject app-owned control-plane bindings without a reverse import."""

    global _HOST
    _HOST = host


def start_subagent_task(
    state: State,
    sub: SubAgentRuntime,
    prompt: str,
    source: str = "user",
    policy_approved: bool = False,
    parent_task_id: str = "",
    task_title: str = "",
    expected_build_digest: str = "",
    agent_project_grant_declared: bool = False,
    approved_policy: Optional[dict[str, Any]] = None,
) -> str:
    if _HOST is None:
        raise RuntimeError("Subagent task dispatch host is not configured")
    raw_prompt = (prompt or "").strip()
    approved_policy = dict(approved_policy or {})
    prompt, transient_skill_refs = split_transient_skill_prompt(raw_prompt)
    if not prompt:
        return "子 agent 输入为空。"
    role = normalized_subagent_role(sub.role)
    task_objective = policy_relevant_subagent_prompt_text(prompt)
    is_agent_project = bool(sub.agent_project_id or sub.runtime_provider_id == "pi-native")
    governed_task_title = task_title or (
        f"Agent Project: {sub.agent_project_id}" if is_agent_project else f"子 agent 执行: {sub.name}"
    )
    if is_agent_project and sub.security_context != "standard":
        return "Pi-native Agent Project 仅支持 standard 受管任务通道；Secret 通道未开放。"
    if agent_project_grant_declared and (not is_agent_project or not source.startswith("user:agent_project")):
        return "Agent Project executable grant 缺少受管用户确认来源，已阻止运行。"
    if is_agent_project and not str(expected_build_digest or "").strip() and not approved_policy:
        return (
            "Agent Project 运行缺少已确认 Build digest，已阻止运行。"
            "请使用 /agent-project run <id> <objective> 重新查看并确认当前 Build。"
        )
    policy_action = "repo_write" if agent_project_grant_declared else infer_policy_action_for_subagent_task(sub, prompt)
    if sub.security_context == "secret":
        return start_secret_subagent_task(
            state,
            sub,
            prompt,
            source=source,
            policy_approved=policy_approved,
            parent_task_id=parent_task_id,
            task_title=task_title,
            transient_skill_refs=transient_skill_refs,
        )
    record_shared_user_profile_interaction(prompt, source=source, state=state)
    if sub.status in {"running", "aborting"} or (sub.agent is not None and agent_has_unfinished_task(sub.agent)):
        queued_result = queue_subagent_task(
            state,
            sub,
            raw_prompt,
            source=source,
            policy_approved=policy_approved,
            parent_task_id=parent_task_id,
            task_title=task_title,
            expected_build_digest=expected_build_digest,
            agent_project_grant_declared=agent_project_grant_declared,
            approved_policy=approved_policy,
        )
        if approved_policy:
            queued_task_id = str(approved_policy.get("original_task_id") or "").strip() or short_uid("task")
            required_for = str(approved_policy.get("approval_required_for") or "").strip()
            queued_approval = approval_metadata(
                status="approved",
                approval_required_for=[required_for] if required_for else [],
                approval_id=str(approved_policy.get("approval_id") or ""),
            )
            queued_approval["policy_decision_id"] = str(approved_policy.get("policy_decision_id") or "")
            queued_approval["policy_action"] = str(approved_policy.get("policy_action") or policy_action)
            schema = subagent_task_schema_kwargs(sub, task_objective)
            schema["approval"] = dict(queued_approval)
            append_orchestrator_plan(
                sub,
                task_objective,
                queued_task_id,
                status="queued",
                source=source,
                approval=dict(queued_approval),
                action_override=policy_action,
            )
            append_task_ledger(
                queued_task_id,
                status="queued",
                assigned_agent=sub.agent_id,
                title=governed_task_title,
                kind="subagent_task",
                objective=truncate_cells(task_objective, 240),
                parent_task_id=parent_task_id,
                session_key=active_ui_session_key(state),
                summary=queued_result,
                **schema,
            )
            update_plan_step_from_child(parent_task_id)
            approval_audit = {
                key: value
                for key, value in {
                    "approval_id": str(queued_approval.get("approval_id") or ""),
                    "policy_decision_id": str(queued_approval.get("policy_decision_id") or ""),
                    "policy_action": str(queued_approval.get("policy_action") or ""),
                }.items()
                if value
            }
            checkpoint = append_task_checkpoint(
                queued_task_id,
                status="queued",
                reason="approved_subagent_task_queued",
                state=state,
                agent_id=sub.agent_id,
                summary=queued_result,
                extra=approval_audit,
            )
            append_trace(
                queued_task_id,
                "approved_subagent_task_queued",
                agent_id=sub.agent_id,
                status="queued",
                payload={"checkpoint_id": checkpoint.get("checkpoint_id", ""), **approval_audit},
            )
        return queued_result
    bus_task_id = str(approved_policy.get("original_task_id") or "").strip() or short_uid("task")
    decision: Optional[PolicyDecision] = None
    if not policy_approved:
        decision = policy_gate_for_subagent_task(
            sub,
            prompt,
            source=source,
            bus_task_id=bus_task_id,
            parent_task_id=parent_task_id,
            task_title=task_title,
            deferred_prompt=raw_prompt,
            transient_skill_refs=transient_skill_refs,
            expected_build_digest=expected_build_digest,
            agent_project_grant_declared=agent_project_grant_declared,
            action_override=policy_action,
        )
        if decision.approval_required:
            append_orchestrator_plan(
                sub,
                task_objective,
                bus_task_id,
                status="approval_required",
                source=source,
                decision=decision,
            )
            append_task_ledger(
                bus_task_id,
                status="approval_required",
                assigned_agent=sub.agent_id,
                title=governed_task_title,
                kind="subagent_task",
                objective=truncate_cells(task_objective, 240),
                parent_task_id=parent_task_id,
                session_key=active_ui_session_key(state),
                summary=policy_gate_text(decision),
                **subagent_task_schema_kwargs(sub, task_objective, decision=decision),
            )
            update_plan_step_from_child(parent_task_id)
            checkpoint = append_task_checkpoint(
                bus_task_id,
                status="approval_required",
                reason="subagent_policy_gate_waiting_approval",
                state=state,
                agent_id=sub.agent_id,
                summary=policy_gate_text(decision),
            )
            payload = policy_decision_to_dict(decision)
            payload["checkpoint_id"] = checkpoint.get("checkpoint_id", "")
            append_trace(bus_task_id, "policy_gate_waiting_approval", agent_id=sub.agent_id, status="approval_required", payload=payload)
            return policy_gate_text(decision)
        if not decision.allowed:
            append_orchestrator_plan(
                sub,
                task_objective,
                bus_task_id,
                status="rejected",
                source=source,
                decision=decision,
                error=policy_gate_text(decision),
            )
            append_task_ledger(
                bus_task_id,
                status="rejected",
                assigned_agent=sub.agent_id,
                title=governed_task_title,
                kind="subagent_task",
                objective=truncate_cells(task_objective, 240),
                parent_task_id=parent_task_id,
                session_key=active_ui_session_key(state),
                error=policy_gate_text(decision),
                **subagent_task_schema_kwargs(sub, task_objective, decision=decision),
            )
            update_plan_step_from_child(parent_task_id)
            checkpoint = append_task_checkpoint(
                bus_task_id,
                status="rejected",
                reason="subagent_policy_gate_denied",
                state=state,
                agent_id=sub.agent_id,
                summary=policy_gate_text(decision),
            )
            payload = policy_decision_to_dict(decision)
            payload["checkpoint_id"] = checkpoint.get("checkpoint_id", "")
            append_trace(bus_task_id, "policy_gate_denied", agent_id=sub.agent_id, status="rejected", payload=payload)
            return policy_gate_text(decision)
    if decision is not None:
        effective_approval = approval_metadata(decision=decision)
    elif approved_policy:
        required_for = str(approved_policy.get("approval_required_for") or "").strip()
        effective_approval = approval_metadata(
            status="approved",
            approval_required_for=[required_for] if required_for else [],
            approval_id=str(approved_policy.get("approval_id") or ""),
        )
        effective_approval["policy_decision_id"] = str(approved_policy.get("policy_decision_id") or "")
        effective_approval["policy_action"] = str(approved_policy.get("policy_action") or policy_action)
    else:
        effective_approval = approval_metadata()

    def governed_task_schema_kwargs() -> dict[str, Any]:
        payload = subagent_task_schema_kwargs(sub, task_objective, decision=decision)
        payload["approval"] = dict(effective_approval)
        return payload

    approval_audit = {
        "approval_id": str(effective_approval.get("approval_id") or ""),
        "policy_decision_id": str(effective_approval.get("policy_decision_id") or ""),
        "policy_action": str(effective_approval.get("policy_action") or ""),
    }
    approval_audit = {key: value for key, value in approval_audit.items() if value}
    causation_refs = [f"approval:{approval_audit['approval_id']}"] if approval_audit.get("approval_id") else []
    if approval_audit.get("policy_decision_id"):
        causation_refs.append(f"policy:{approval_audit['policy_decision_id']}")
    agent_project_runtime_payload: dict[str, Any] = {}
    agent_project_run_ref = ""
    agent_project_metadata: dict[str, Any] = dict(approval_audit)

    def durable_preflight_message(message: str) -> str:
        if not is_agent_project:
            return message
        roots = {str(sub.agent_project_root or "")}
        canonical = agent_project_root_for_id(sub.agent_project_id)
        if canonical:
            roots.add(canonical)
        for root in sorted((item for item in roots if item), key=len, reverse=True):
            message = message.replace(root, "<agent-project-source>")
            try:
                resolved = str(Path(root).resolve(strict=False))
            except (OSError, RuntimeError):
                resolved = ""
            if resolved:
                message = message.replace(resolved, "<agent-project-source>")
        return message

    def fail_governed_preflight(message: str, reason: str, *, status: str = "failed") -> str:
        if not approved_policy and not is_agent_project:
            return message
        durable_message = durable_preflight_message(message)
        artifact_refs = [agent_project_run_ref] if agent_project_run_ref else []
        append_orchestrator_plan(
            sub,
            task_objective,
            bus_task_id,
            status=status,
            source=source,
            decision=decision,
            approval=dict(effective_approval),
            action_override=policy_action,
            error=durable_message,
        )
        append_task_ledger(
            bus_task_id,
            status=status,
            assigned_agent=sub.agent_id,
            title=governed_task_title,
            kind="subagent_task",
            objective=truncate_cells(task_objective, 240),
            parent_task_id=parent_task_id,
            session_key=active_ui_session_key(state),
            error=durable_message,
            artifact_refs=artifact_refs,
            **governed_task_schema_kwargs(),
        )
        update_plan_step_from_child(parent_task_id)
        checkpoint = append_task_checkpoint(
            bus_task_id,
            status=status,
            reason=reason,
            state=state,
            agent_id=sub.agent_id,
            summary=truncate_cells(durable_message, 240),
            extra={**agent_project_metadata, **approval_audit},
        )
        append_trace(
            bus_task_id,
            reason,
            agent_id=sub.agent_id,
            status=status,
            payload={
                "error": durable_message,
                "checkpoint_id": checkpoint.get("checkpoint_id", ""),
                **agent_project_metadata,
                **approval_audit,
            },
        )
        return message

    if is_agent_project and not str(expected_build_digest or "").strip():
        return fail_governed_preflight(
            "Agent Project 运行缺少已确认 Build digest，已阻止运行。"
            "请使用 /agent-project run <id> <objective> 重新查看并确认当前 Build。",
            "agent_project_build_confirmation_missing",
            status="rejected",
        )
    if sub.agent_project_root or sub.agent_project_id:
        canonical_root = agent_project_root_for_id(sub.agent_project_id)
        try:
            configured_root = str(Path(sub.agent_project_root).resolve(strict=True))
        except (OSError, RuntimeError):
            configured_root = ""
        if not canonical_root or configured_root != canonical_root:
            return fail_governed_preflight(
                f"{sub.name} 的 Agent Project 来源不再位于受管项目目录，已阻止运行。",
                "agent_project_root_invalid",
                status="rejected",
            )
        compiled = agent_project_helpers.compile_agent_project(canonical_root)
        if not compiled.ok or compiled.build is None:
            return fail_governed_preflight(
                f"{sub.name} 的 Agent Project 构建失败：\n" + "\n".join(agent_project_diagnostic_lines(compiled)),
                "agent_project_build_invalid",
                status="rejected",
            )
        build = compiled.build
        if build.runtime != "pi-native" or sub.runtime_provider_id != "pi-native":
            return fail_governed_preflight(
                f"{sub.name} 的 Agent Project runtime/provider 不匹配："
                f"build={build.runtime!r}, worker={sub.runtime_provider_id!r}。",
                "agent_project_runtime_mismatch",
                status="rejected",
            )
        if build.project.project_id != sub.agent_project_id:
            return fail_governed_preflight(
                f"{sub.name} 的 Agent Project ID 与冻结 Build 不一致，已阻止运行。",
                "agent_project_identity_mismatch",
                status="rejected",
            )
        expected_build_digest = str(expected_build_digest or "").strip().lower()
        if not expected_build_digest or build.digest != expected_build_digest:
            return fail_governed_preflight(
                f"{sub.name} 的 Agent Project 在确认后发生变化，已阻止运行。"
                "请重新查看权限并确认新的冻结 Build。",
                "agent_project_build_digest_changed",
                status="rejected",
            )
        try:
            agent_project_runtime_payload, agent_project_run_ref, agent_project_metadata = (
                prepare_agent_project_runtime_envelope(
                    build,
                    assignment_id=bus_task_id,
                    grant_declared=agent_project_grant_declared,
                    causation_refs=causation_refs,
                )
            )
        except Exception as exc:
            return fail_governed_preflight(
                f"{sub.name} 的 Agent Run Manifest 创建失败：{type(exc).__name__}: {exc}",
                "agent_project_run_manifest_failed",
            )
        agent_project_metadata.update(approval_audit)
        sub.agent_build_digest = build.digest
        save_subagent_meta(sub)
    try:
        agent = ensure_subagent_agent(state, sub)
    except Exception as exc:
        return fail_governed_preflight(
            f"{sub.name} runtime 准备失败：{type(exc).__name__}: {exc}",
            "subagent_runtime_prepare_failed",
        )
    ok_model, model_msg = apply_subagent_default_model(state, sub)
    if not ok_model:
        return fail_governed_preflight(
            f"{sub.name} 默认模型未应用，已阻止启动：{model_msg}",
            "subagent_model_apply_failed",
        )
    sub.task_id += 1
    task_id = sub.task_id
    locked, lock_error = acquire_single_writer_lock(sub, bus_task_id, task_objective)
    if not locked:
        append_orchestrator_plan(
            sub,
            task_objective,
            bus_task_id,
            status="rejected",
            source=source,
            decision=decision,
            approval=dict(effective_approval),
            action_override=policy_action,
            error=lock_error,
        )
        append_task_ledger(
            bus_task_id,
            status="rejected",
            assigned_agent=sub.agent_id,
            title=governed_task_title,
            kind="subagent_task",
            objective=truncate_cells(task_objective, 240),
            parent_task_id=parent_task_id,
            session_key=active_ui_session_key(state),
            error=lock_error,
            artifact_refs=[agent_project_run_ref] if agent_project_run_ref else [],
            **governed_task_schema_kwargs(),
        )
        update_plan_step_from_child(parent_task_id)
        checkpoint = append_task_checkpoint(
            bus_task_id,
            status="rejected",
            reason="single_writer_denied",
            state=state,
            agent_id=sub.agent_id,
            summary=lock_error,
            extra=dict(agent_project_metadata),
        )
        append_trace(
            bus_task_id,
            "single_writer_denied",
            agent_id=sub.agent_id,
            status="rejected",
            payload={
                "error": lock_error,
                "checkpoint_id": checkpoint.get("checkpoint_id", ""),
                **agent_project_metadata,
            },
        )
        return lock_error
    context_pack, context_ref = build_context_pack(
        state,
        sub,
        task_objective,
        bus_task_id,
        parent_task_id=parent_task_id,
        transient_skill_refs=transient_skill_refs,
    )
    append_orchestrator_plan(
        sub,
        task_objective,
        bus_task_id,
        status="working",
        source=source,
        decision=decision,
        approval=dict(effective_approval),
        action_override=policy_action,
        context_ref=context_ref,
    )
    sub.active_task_id = task_id
    sub.active_bus_task_id = bus_task_id
    sub.status = "running"
    sub.updated_at = time.time()
    sub.pending_interaction = None
    visible_prompt = display_prompt_for_subagent_task(prompt)
    sub.messages.append(Message("user", visible_prompt))
    sub.messages.append(Message("assistant", "", done=False))
    save_subagent_meta(sub)
    save_subagent_chat_session(state, sub, source=source)
    mark_subagent_messages_changed(state, sub)
    append_subagent_event(sub, source, visible_prompt)
    append_task_ledger(
        bus_task_id,
        status="working",
        assigned_agent=sub.agent_id,
        title=governed_task_title,
        kind="subagent_task",
        objective=truncate_cells(task_objective, 240),
        parent_task_id=parent_task_id,
        session_key=active_ui_session_key(state),
        artifact_refs=[context_ref] + ([agent_project_run_ref] if agent_project_run_ref else []),
        **governed_task_schema_kwargs(),
    )
    update_plan_step_from_child(parent_task_id)
    runtime_provider_id = agent_runtime_provider_id(agent)
    append_agent_mail(
        from_agent="orchestrator.main",
        to_type="agent",
        target=sub.agent_id,
        intent="delegate",
        task_id=bus_task_id,
        status="working",
        payload={
            "objective": task_objective,
            "context_pack_ref": context_ref,
            "role": role,
            "runtime_provider_id": runtime_provider_id,
            **agent_project_metadata,
            "output_contract": {"required_sections": role_output_contract(role)},
            "permissions": permissions_for_role(role, security_context=sub.security_context),
            "transient_skill_refs": transient_skill_refs,
        },
        artifact_refs=[context_ref] + ([agent_project_run_ref] if agent_project_run_ref else []),
        budget=default_task_budget(role),
        permissions=permissions_for_role(role, security_context=sub.security_context),
        context_policy=context_policy_for_task(task_objective, security_context=sub.security_context),
        task=task_contract_for_role(role, task_objective),
        risks=risks_for_action(
            decision.action if decision is not None else policy_action,
            role,
            task_objective,
        ),
        approval=dict(effective_approval),
    )
    checkpoint = append_task_checkpoint(
        bus_task_id,
        status="working",
        reason="subagent_delegated",
        state=state,
        agent_id=sub.agent_id,
        summary=truncate_cells(task_objective, 240),
        extra={
            "context_pack_ref": context_ref,
            "transient_skill_refs": transient_skill_refs,
            **agent_project_metadata,
        },
    )
    append_trace(
        bus_task_id,
        "delegated",
        agent_id=sub.agent_id,
        status="working",
        payload={
            "context_pack": context_ref,
            "role": role,
            "checkpoint_id": checkpoint.get("checkpoint_id", ""),
            "runtime_provider_id": runtime_provider_id,
            "transient_skill_refs": transient_skill_refs,
            **agent_project_metadata,
        },
    )
    agent_prompt = f"{runtime_context_prompt_for_agent(agent, context_pack, context_ref)}\n\n[Task]\n{prompt}\n[/Task]"
    agent_prompt = runtime_prompt_with_transient_skill_command(agent, agent_prompt, transient_skill_refs)
    try:
        runtime_source = f"subagent:{sub.agent_id}"
        request = runtime_task_request_for_agent(
            agent=agent,
            task_id=bus_task_id,
            parent_task_id=parent_task_id,
            prompt=agent_prompt,
            source=runtime_source,
            agent_id=sub.agent_id,
            role=role,
            objective=task_objective,
            context_pack_ref=context_ref,
            permissions=permissions_for_role(role, security_context=sub.security_context),
            approval_policy=dict(effective_approval),
            output_contract=task_contract_for_role(role, task_objective).get("output_contract") or {},
            artifact_refs=[context_ref] + ([agent_project_run_ref] if agent_project_run_ref else []),
            metadata={
                "runtime_lane": "subagent",
                "source": source,
                "security_context": sub.security_context,
                "transient_skill_refs": transient_skill_refs,
                **agent_project_metadata,
            },
            runtime_payload=agent_project_runtime_payload,
        )
        dq = put_agent_runtime_task(agent, request)
    except Exception as exc:
        sub.status = "error"
        sub.active_task_id = None
        sub.active_bus_task_id = ""
        sub.messages[-1] = Message("assistant", f"[ERROR] put_task: {type(exc).__name__}: {exc}")
        save_subagent_meta(sub)
        save_subagent_chat_session(state, sub, source=f"{source}:error")
        mark_subagent_messages_changed(state, sub)
        release_single_writer_lock(bus_task_id)
        append_orchestrator_plan(
            sub,
            task_objective,
            bus_task_id,
            status="failed",
            source=source,
            decision=decision,
            approval=dict(effective_approval),
            action_override=policy_action,
            context_ref=context_ref,
            error=f"{type(exc).__name__}: {exc}",
        )
        append_task_ledger(
            bus_task_id,
            status="failed",
            assigned_agent=sub.agent_id,
            title=governed_task_title,
            kind="subagent_task",
            objective=truncate_cells(task_objective, 240),
            parent_task_id=parent_task_id,
            session_key=active_ui_session_key(state),
            error=f"{type(exc).__name__}: {exc}",
            artifact_refs=[context_ref] + ([agent_project_run_ref] if agent_project_run_ref else []),
            **governed_task_schema_kwargs(),
        )
        update_plan_step_from_child(parent_task_id)
        checkpoint = append_task_checkpoint(
            bus_task_id,
            status="failed",
            reason="subagent_put_task_failed",
            state=state,
            agent_id=sub.agent_id,
            summary=f"{type(exc).__name__}: {exc}",
            extra={"context_pack_ref": context_ref, **agent_project_metadata},
        )
        append_trace(
            bus_task_id,
            "put_task_failed",
            agent_id=sub.agent_id,
            status="failed",
            payload={
                "error": f"{type(exc).__name__}: {exc}",
                "checkpoint_id": checkpoint.get("checkpoint_id", ""),
                **agent_project_metadata,
            },
        )
        return f"{sub.name} 启动失败: {type(exc).__name__}: {exc}"
    threading.Thread(target=consume_subagent_queue, args=(state, sub.agent_id, task_id, dq), daemon=True, name=f"subagent-{sub.agent_id}-stream").start()
    mark_dirty(state)
    return f"已启动子 agent：{sub.name}"




__all__ = ["configure_subagent_task_dispatch", "start_subagent_task"]
