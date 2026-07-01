"""Tests for low-level history metadata and transcript storage helpers."""
from __future__ import annotations

import json
from pathlib import Path

from ga_tui import app as app_module
from ga_tui import history_store
from ga_tui.ui_types import Message


class TestSessionMetaRegistry:
    def test_round_trip_filters_non_dict_values(self, tmp_path: Path) -> None:
        path = tmp_path / "session_meta.json"
        path.write_text(
            json.dumps({
                "model_responses_a.txt": {"rounds": 1},
                "model_responses_b.txt": ["bad"],
            }),
            encoding="utf-8",
        )

        loaded = history_store.load_session_meta_registry(str(path))

        assert loaded == {"model_responses_a.txt": {"rounds": 1}}

    def test_save_writes_json_atomically(self, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "session_meta.json"

        history_store.save_session_meta_registry(str(path), {"model_responses_a.txt": {"preview": "hello"}})

        assert history_store.load_session_meta_registry(str(path)) == {
            "model_responses_a.txt": {"preview": "hello"}
        }
        assert not path.with_suffix(path.suffix + ".tmp").exists()

    def test_app_wrapper_uses_current_session_meta_path(self, tmp_path: Path) -> None:
        old_path = app_module.SESSION_META_PATH
        try:
            app_module.SESSION_META_PATH = str(tmp_path / "session_meta.json")
            app_module.save_session_meta_registry({"model_responses_a.txt": {"rounds": 2}})
            assert history_store.load_session_meta_registry(app_module.SESSION_META_PATH)["model_responses_a.txt"]["rounds"] == 2
        finally:
            app_module.SESSION_META_PATH = old_path


class TestTranscriptStorage:
    def test_append_model_response_transcript_turn(self, tmp_path: Path) -> None:
        path = tmp_path / "model_responses_a.txt"

        assert history_store.append_model_response_transcript_turn(
            str(path),
            "\x1b[31mhello\x1b[0m",
            "world",
            normal_session_log_path=True,
        )

        content = path.read_text(encoding="utf-8")
        assert "=== Prompt ===" in content
        assert "=== Response ===" in content
        assert "hello" in content
        assert "world" in content
        assert "\x1b[31m" not in content

    def test_append_model_response_rejects_non_normal_path(self, tmp_path: Path) -> None:
        path = tmp_path / "outside.txt"

        assert not history_store.append_model_response_transcript_turn(
            str(path),
            "hello",
            "world",
            normal_session_log_path=False,
        )
        assert not path.exists()

    def test_write_subagent_chat_history_transcript(self, tmp_path: Path) -> None:
        path = tmp_path / "model_responses_subagent.txt"
        messages = [
            Message("assistant", "orphan assistant"),
            Message("user", "first user"),
            Message("assistant", "first reply"),
            Message("user", "second user"),
        ]

        history_store.write_subagent_chat_history_transcript(str(path), messages)

        content = path.read_text(encoding="utf-8")
        assert "orphan assistant" not in content
        assert "first user" in content
        assert "first reply" in content
        assert "second user" in content
        assert content.count("=== Prompt ===") == 2


class TestResponseBodyParser:
    def test_assistant_text_from_response_body_list(self) -> None:
        body = repr([
            {"type": "text", "text": "first"},
            "second",
            {"type": "image", "text": "ignored"},
        ])

        assert history_store.assistant_text_from_response_body(body) == "first\nsecond"

    def test_assistant_text_from_response_body_content_list(self) -> None:
        body = repr({"content": [{"type": "text", "text": "alpha"}, {"type": "text", "text": "beta"}]})

        assert history_store.assistant_text_from_response_body(body) == "alpha\nbeta"

    def test_assistant_text_from_response_body_dict_fallback_fields(self) -> None:
        assert history_store.assistant_text_from_response_body(repr({"content": "direct"})) == "direct"
        assert history_store.assistant_text_from_response_body(repr({"text": "text-field"})) == "text-field"

    def test_assistant_text_from_response_body_malformed_falls_back_to_clean_text(self) -> None:
        assert history_store.assistant_text_from_response_body("\x1b[31mnot python") == "not python"

    def test_app_wrapper_matches_module(self) -> None:
        assert app_module.assistant_text_from_response_body is history_store.assistant_text_from_response_body
