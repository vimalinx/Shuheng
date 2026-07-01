"""Tests for low-level history metadata and transcript storage helpers."""
from __future__ import annotations

import json
from pathlib import Path

from ga_tui import app as app_module
from ga_tui import history_store
from ga_tui import path_utils
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


class TestRecentHistoryItems:
    def test_sorts_by_activity_desc_and_applies_limit(self, tmp_path: Path) -> None:
        older = str(tmp_path / "model_responses_old.txt")
        newer = str(tmp_path / "model_responses_new.txt")
        zero = str(tmp_path / "model_responses_zero.txt")
        entries = [
            (1, (older, 10.0, "old", 1)),
            (2, (zero, 0.0, "zero", 1)),
            (3, (newer, 30.0, "new", 1)),
        ]

        result = history_store.recent_history_items(entries, set(), 1)

        assert result == [(3, (newer, 30.0, "new", 1))]

    def test_excludes_used_normalized_paths(self, tmp_path: Path) -> None:
        used = str(tmp_path / "model_responses_used.txt")
        other = str(tmp_path / "model_responses_other.txt")
        entries = [
            (1, (used, 40.0, "used", 1)),
            (2, (other, 20.0, "other", 1)),
        ]

        result = history_store.recent_history_items(
            entries,
            {path_utils.normalized_path(used)},
            5,
        )

        assert result == [(2, (other, 20.0, "other", 1))]

    def test_app_wrapper_preserves_default_recent_limit(self, tmp_path: Path) -> None:
        entries = [
            (idx, (str(tmp_path / f"model_responses_{idx}.txt"), float(idx), f"item {idx}", idx))
            for idx in range(1, app_module.RECENT_SESSION_LIMIT + 3)
        ]

        result = app_module.recent_history_items(entries, set())

        assert len(result) == app_module.RECENT_SESSION_LIMIT
        assert result[0][0] == app_module.RECENT_SESSION_LIMIT + 2
        assert result == history_store.recent_history_items(entries, set(), app_module.RECENT_SESSION_LIMIT)


class TestRestorePreviewCompaction:
    @staticmethod
    def _user_text(prompt: str) -> str:
        return prompt.strip()

    @staticmethod
    def _response_preview(response: str) -> str:
        return response.strip()

    def test_compact_ui_preview_messages_from_pairs_selects_recent_rounds(self) -> None:
        pairs = [
            ("first", "first reply"),
            ("   ", "blank user reply"),
            ("second", "执行中"),
            ("third", "third reply"),
        ]

        messages, loaded, total, count = history_store.compact_ui_preview_messages_from_pairs(
            pairs,
            2,
            default_rounds=3,
            user_text_from_prompt=self._user_text,
            response_preview_text=self._response_preview,
        )

        assert loaded == 2
        assert total == 3
        assert count == 3
        assert messages == [
            {"role": "user", "content": "second"},
            {"role": "user", "content": "third"},
            {"role": "assistant", "content": "（预览）third reply"},
        ]

    def test_compact_ui_preview_messages_from_pairs_falls_back_to_pair_count(self) -> None:
        messages, loaded, total, count = history_store.compact_ui_preview_messages_from_pairs(
            [(" ", "one"), ("", "two")],
            5,
            default_rounds=3,
            user_text_from_prompt=self._user_text,
            response_preview_text=self._response_preview,
        )

        assert loaded == 2
        assert total == 2
        assert count == 2
        assert messages == [
            {"role": "assistant", "content": "（预览）one"},
            {"role": "assistant", "content": "（预览）two"},
        ]

    def test_app_compact_ui_preview_wrapper_preserves_behavior(self) -> None:
        response = repr([{"type": "text", "text": "visible reply"}])
        direct = history_store.compact_ui_preview_messages_from_pairs(
            [("  user asks  ", response)],
            app_module.RESTORE_DISPLAY_ROUNDS,
            default_rounds=app_module.RESTORE_DISPLAY_ROUNDS,
            user_text_from_prompt=app_module._user_text,
            response_preview_text=app_module.session_response_preview_text,
        )

        assert app_module.compact_ui_preview_messages_from_pairs([("  user asks  ", response)]) == direct


class TestTranscriptStorage:
    def test_latest_user_message_text_selects_newest_non_blank_user(self) -> None:
        messages = [
            Message("user", "first"),
            Message("assistant", "reply"),
            Message("user", "  "),
            Message("system", "ignored"),
            Message("user", "  newest  "),
        ]

        assert history_store.latest_user_message_text(messages) == "newest"

    def test_latest_user_message_text_returns_empty_without_user(self) -> None:
        messages = [
            Message("assistant", "reply"),
            Message("system", "notice"),
            Message("user", "  "),
        ]

        assert history_store.latest_user_message_text(messages) == ""

    def test_app_latest_user_message_text_alias_matches_module(self) -> None:
        assert app_module.latest_user_message_text is history_store.latest_user_message_text

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
