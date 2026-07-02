from __future__ import annotations

import ga_tui.app as app_module
from ga_tui import control_protocol


def test_subagent_control_intent_helpers_are_protocol_owned_app_aliases() -> None:
    assert app_module.subagent_control_persistence_intent is control_protocol.subagent_control_persistence_intent
    assert app_module.subagent_control_force_new_intent is control_protocol.subagent_control_force_new_intent
    assert app_module.CONTROL_CONTINUATION_ACTIONS is control_protocol.CONTROL_CONTINUATION_ACTIONS
    assert app_module.STRUCTURED_CONTINUATION_STATES is control_protocol.STRUCTURED_CONTINUATION_STATES
    assert app_module.control_result_continuation_signature is control_protocol.control_result_continuation_signature
    assert app_module.control_continuation_metadata is control_protocol.control_continuation_metadata
    assert app_module.control_explicitly_requests_continuation is control_protocol.control_explicitly_requests_continuation
    assert app_module.control_result_continuation_needed is control_protocol.control_result_continuation_needed
    assert app_module.format_control_result_continuation_prompt is control_protocol.format_control_result_continuation_prompt
    assert app_module.format_agent_control_result is control_protocol.format_agent_control_result
    assert app_module.agenttask_payload_from_prompt is control_protocol.agenttask_payload_from_prompt
    assert app_module.policy_relevant_subagent_prompt_text is control_protocol.policy_relevant_subagent_prompt_text
    assert app_module.explicit_policy_action_for_subagent_task is control_protocol.explicit_policy_action_for_subagent_task
    assert app_module.inferred_policy_action_for_subagent_task is control_protocol.inferred_policy_action_for_subagent_task
    assert control_protocol.subagent_control_persistence_intent.__module__ == "ga_tui.control_protocol"
    assert control_protocol.subagent_control_force_new_intent.__module__ == "ga_tui.control_protocol"
    assert control_protocol.control_result_continuation_signature.__module__ == "ga_tui.control_protocol"
    assert control_protocol.format_control_result_continuation_prompt.__module__ == "ga_tui.control_protocol"
    assert control_protocol.format_agent_control_result.__module__ == "ga_tui.control_protocol"
    assert control_protocol.agenttask_payload_from_prompt.__module__ == "ga_tui.control_protocol"
    assert control_protocol.policy_relevant_subagent_prompt_text.__module__ == "ga_tui.control_protocol"
    assert control_protocol.explicit_policy_action_for_subagent_task.__module__ == "ga_tui.control_protocol"
    assert control_protocol.inferred_policy_action_for_subagent_task.__module__ == "ga_tui.control_protocol"


def test_subagent_control_persistence_intent_explicit_lifecycle_flags() -> None:
    helper = control_protocol.subagent_control_persistence_intent

    assert helper({"persistent": True}, "", "", "", "") == (True, False)
    assert helper({"durable": "yes"}, "", "", "", "") == (True, False)
    assert helper({"long_term": "长期"}, "", "", "", "") == (True, False)
    assert helper({"persistent": False}, "", "", "", "") == (False, True)
    assert helper({"durable": "no"}, "", "", "", "") == (False, True)
    assert helper({"lifecycle": "persistent"}, "", "", "", "") == (True, False)
    assert helper({"lifecycle": "long-term"}, "", "", "", "") == (True, False)
    assert helper({"scope": "永久"}, "", "", "", "") == (True, False)
    assert helper({"scope": "session_only"}, "", "", "", "") == (False, True)
    assert helper({"lifecycle": "临时"}, "", "", "", "") == (False, True)


def test_subagent_control_persistence_intent_defaults_to_temporary_without_inference() -> None:
    helper = control_protocol.subagent_control_persistence_intent

    assert helper({}, "persistent target", "durable value", "长期名称", "permanent profile") == (False, True)
    assert helper({"temporary": True}, "", "", "", "") == (False, True)
    assert helper({"temp": "on"}, "", "", "", "") == (False, True)
    assert helper({"ephemeral": 1}, "", "", "", "") == (False, True)
    assert helper({"session_only": "true"}, "", "", "", "") == (False, True)
    assert helper({"session_scoped": "yes"}, "", "", "", "") == (False, True)
    assert helper({"temporary": False}, "", "", "", "") == (False, True)


def test_subagent_control_force_new_intent_explicit_flags_and_reuse_policy() -> None:
    helper = control_protocol.subagent_control_force_new_intent

    assert helper({"force_new": True}, "", "", "", "")
    assert helper({"create_new": "yes"}, "", "", "", "")
    assert helper({"fresh": 1}, "", "", "", "")
    assert helper({"separate": "on"}, "", "", "", "")
    assert helper({"reuse": False}, "", "", "", "")
    assert helper({"reuse_existing": "no"}, "", "", "", "")
    assert helper({"allow_reuse": 0}, "", "", "", "")
    assert helper({"dedupe": "off"}, "", "", "", "")
    assert helper({"new": "true"}, "", "", "", "")
    assert helper({"new": 1}, "", "", "", "")
    assert helper({"reuse_policy": "force-new"}, "", "", "", "")
    assert helper({"reuse_policy": "never"}, "", "", "", "")
    assert helper({"reuse_policy": "none"}, "", "", "", "")
    assert helper({"reuse_policy": "no_reuse"}, "", "", "", "")


def test_subagent_control_force_new_intent_ignores_display_text_and_default_reuse() -> None:
    helper = control_protocol.subagent_control_force_new_intent

    assert not helper({}, "new target", "force new value", "separate name", "do not reuse", "never reuse this")
    assert not helper({"reuse": True}, "", "", "", "")
    assert not helper({"reuse_existing": "yes"}, "", "", "", "")
    assert not helper({"allow_reuse": 1}, "", "", "", "")
    assert not helper({"dedupe": "true"}, "", "", "", "")
    assert not helper({"new": ["truthy-looking"]}, "", "", "", "")
    assert not helper({"reuse_policy": "reuse"}, "", "", "", "")


def test_control_continuation_metadata_checks_control_and_envelope() -> None:
    helper = control_protocol.control_continuation_metadata
    control = {
        "action": "agent_create",
        "workflow": {"continue_after": True},
        "_ga_control_envelope": {
            "orchestration": {"workflow_state": "in-progress"},
            "continuation": {"next_action": "delegate next"},
        },
    }

    metadata = helper(control)

    assert control in metadata
    assert {"continue_after": True} in metadata
    assert {"workflow_state": "in-progress"} in metadata
    assert {"next_action": "delegate next"} in metadata


def test_control_explicitly_requests_continuation_only_from_structured_fields() -> None:
    helper = control_protocol.control_explicitly_requests_continuation

    assert helper({"action": "agent_create", "continue_after": True})
    assert helper({"action": "agent_create", "next_action_required": "yes"})
    assert helper({"action": "agent_create", "requires_continuation": 1})
    assert helper({"action": "agent_create", "workflow_state": "needs-followup"})
    assert helper({"action": "agent_create", "orchestration": {"state": "partial"}})
    assert helper({"action": "agent_create", "_ga_control_envelope": {"continuation": {"next_action": {"op": "next"}}}})
    assert not helper({"action": "agent_create", "message": "please continue with step 2"})
    assert not helper({"action": "agent_create", "continue_after": False, "next_action": ""})


def test_control_result_continuation_needed_filters_actions_and_metadata() -> None:
    helper = control_protocol.control_result_continuation_needed

    assert not helper("", [])
    assert not helper("continue visibly", [{"action": "agent_create"}])
    assert helper("", [{"action": "agent_create", "continue_after": True}])
    assert helper("", [{"action": "task_update", "workflow_state": "running"}])
    assert not helper("", [{"action": "agent_run", "continue_after": True}])
    assert not helper("", [{"action": "delegate_create", "continue_after": True}])


def test_control_result_signature_and_prompt_formatting_strip_controls() -> None:
    raw_text = "visible before <ga-control>{\"schema_version\":\"ga-control.v2\",\"actions\":[]}</ga-control>"
    results = ["- agent_create Worker: 已创建临时子 agent：Worker"]

    signature = control_protocol.control_result_continuation_signature(raw_text, results)
    assert len(signature) == 16
    assert signature == control_protocol.control_result_continuation_signature(raw_text, results)
    assert signature != control_protocol.control_result_continuation_signature(raw_text, [*results, "- task_update: done"])

    prompt = control_protocol.format_control_result_continuation_prompt(
        reason="control-results",
        control_results=results,
        original_text=raw_text,
    )

    assert prompt.startswith("[GA TUI Control Result Continuation]")
    assert "Reason: control-results" in prompt
    assert results[0] in prompt
    assert "Continue the user-approved workflow yourself" in prompt
    assert "Do not repeat controls that already succeeded." in prompt
    assert "Previous visible text:" in prompt
    assert "visible before" in prompt
    assert "schema_version" not in prompt
    assert prompt.endswith("[/GA TUI Control Result Continuation]")


def test_format_agent_control_result_preserves_labels_and_truncation() -> None:
    helper = control_protocol.format_agent_control_result

    assert helper("agent_create", "Worker", "ok") == "- agent_create Worker: ok"
    assert helper("agent_create", "current", "ok") == "- agent_create: ok"
    assert helper("agent_create", "now", "ok") == "- agent_create: ok"
    assert helper("agent_create", "selected", "ok") == "- agent_create: ok"
    assert helper("", "", "fallback") == "- control: fallback"

    long_result = "x" * 400
    formatted = helper("task_update", "", long_result)
    assert formatted.startswith("- task_update: ")
    assert len(formatted) < len("- task_update: " + long_result)
    assert formatted.endswith("…")


def test_agenttask_prompt_envelope_helpers_parse_payload_and_policy_text() -> None:
    prompt = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "objective": "top-level objective",
            "work_order": {
                "objective": "work order objective",
                "success_criteria": ["done"],
            },
            "output_contract": {"required_sections": ["result"]},
        }
    )

    payload = control_protocol.agenttask_payload_from_prompt(prompt)

    assert payload["schema_version"] == "agenttask.v2"
    assert payload["work_order"]["objective"] == "work order objective"
    assert control_protocol.policy_relevant_subagent_prompt_text(prompt) == "work order objective"


def test_agenttask_prompt_envelope_helpers_fallback_for_missing_invalid_or_empty_objective() -> None:
    plain = "plain prompt"
    assert control_protocol.agenttask_payload_from_prompt(plain) == {}
    assert control_protocol.policy_relevant_subagent_prompt_text(plain) == plain

    invalid = "[GA TUI AgentTask Envelope v2]\nnot json\n[/GA TUI AgentTask Envelope v2]"
    assert control_protocol.agenttask_payload_from_prompt(invalid) == {}
    assert control_protocol.policy_relevant_subagent_prompt_text(invalid) == invalid

    non_object = "[GA TUI AgentTask Envelope v2]\n[]\n[/GA TUI AgentTask Envelope v2]"
    assert control_protocol.agenttask_payload_from_prompt(non_object) == {}
    assert control_protocol.policy_relevant_subagent_prompt_text(non_object) == non_object

    top_level = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "objective": "top-level objective",
            "work_order": {},
        }
    )
    assert control_protocol.policy_relevant_subagent_prompt_text(top_level) == "top-level objective"

    empty_objective = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "objective": "",
            "work_order": {},
        }
    )
    assert control_protocol.policy_relevant_subagent_prompt_text(empty_objective) == empty_objective


def test_explicit_policy_action_for_subagent_task_reads_envelope_fields_in_order() -> None:
    helper = control_protocol.explicit_policy_action_for_subagent_task

    assert helper("plain prompt") == ""
    assert helper("[GA TUI AgentTask Envelope v2]\nnot json\n[/GA TUI AgentTask Envelope v2]") == ""

    top_level = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "policy_action": "Deploy-Service",
            "approval_required_for": "access_secret",
            "approval": {"policy_action": "publish"},
            "capability_contract": {"policy_action": "repo_write"},
        }
    )
    assert helper(top_level) == "deploy_service"

    top_level_list = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "policy_action": ["", "ignored"],
            "approval_required_for": ["Spend-Money", "deploy"],
        }
    )
    assert helper(top_level_list) == "spend_money"

    nested_approval = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "approval": {"policy_action": "External-Send"},
            "capability_contract": {"policy_action": "repo_write"},
        }
    )
    assert helper(nested_approval) == "external_send"

    nested_approval_list = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "approval": {"approval_required_for": ["Delete-File"]},
            "capability_contract": {"policy_action": "repo_write"},
        }
    )
    assert helper(nested_approval_list) == "delete_file"

    capability_contract = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "capability_contract": {"policy_action": "Modify-Permission-Policy"},
        }
    )
    assert helper(capability_contract) == "modify_permission_policy"


def test_inferred_policy_action_for_subagent_task_preserves_current_policy_order() -> None:
    helper = control_protocol.inferred_policy_action_for_subagent_task

    explicit_prompt = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "policy_action": "Publish",
            "work_order": {"objective": "read an api key token"},
        }
    )
    assert helper(explicit_prompt, role="researcher", write_policy="none") == "publish"

    objective_only = control_protocol.format_agenttask_worker_prompt(
        {
            "schema_version": "agenttask.v2",
            "action": "delegate.create",
            "work_order": {"objective": "read docs only"},
            "capability_contract": {"tools_forbidden": ["deploy", "email.send"]},
        }
    )
    assert helper(objective_only, role="researcher", write_policy="none") == "read_only"

    cases = [
        ("read the API key token", "access_secret"),
        ("buy credits and pay the invoice", "spend_money"),
        ("deploy release to production", "deploy"),
        ("send email to the customer", "external_send"),
        ("publish a public post", "publish"),
        ("rm old cache and delete file", "delete_file"),
        ("modify permission policy and role", "modify_permission_policy"),
        ("bulk batch update", "high_risk_batch_change"),
    ]
    for prompt, expected_action in cases:
        assert helper(prompt, role="researcher", write_policy="none") == expected_action

    assert helper("sudo systemctl restart the service", role="ops", write_policy="none") == "long_running_privilege_escalation"
    assert helper("ordinary repo implementation", role="coder", write_policy="single_writer") == "repo_write"
    assert helper("summarize this file", role="researcher", write_policy="none") == "read_only"


def test_app_infer_policy_action_wrapper_delegates_with_role_facts() -> None:
    coder = app_module.SubAgentRuntime(agent_id="coder", name="Coder", home="/tmp/coder", role="coder")
    ops = app_module.SubAgentRuntime(agent_id="ops", name="Ops", home="/tmp/ops", role="ops")
    researcher = app_module.SubAgentRuntime(
        agent_id="researcher",
        name="Researcher",
        home="/tmp/researcher",
        role="researcher",
    )

    assert app_module.infer_policy_action_for_subagent_task(coder, "ordinary repo implementation") == "repo_write"
    assert app_module.infer_policy_action_for_subagent_task(ops, "sudo systemctl restart the service") == "long_running_privilege_escalation"
    assert app_module.infer_policy_action_for_subagent_task(researcher, "read the API key token") == "access_secret"
    assert app_module.infer_policy_action_for_subagent_task(researcher, "summarize this file") == "read_only"
