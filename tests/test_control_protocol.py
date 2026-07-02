from __future__ import annotations

import ga_tui.app as app_module
from ga_tui import control_protocol


def test_subagent_control_intent_helpers_are_protocol_owned_app_aliases() -> None:
    assert app_module.subagent_control_persistence_intent is control_protocol.subagent_control_persistence_intent
    assert app_module.subagent_control_force_new_intent is control_protocol.subagent_control_force_new_intent
    assert control_protocol.subagent_control_persistence_intent.__module__ == "ga_tui.control_protocol"
    assert control_protocol.subagent_control_force_new_intent.__module__ == "ga_tui.control_protocol"


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
