"""Tests for low-level history metadata and transcript storage helpers."""
from __future__ import annotations

import json
import multiprocessing
import time
from pathlib import Path

import pytest

from shuheng import app as app_module
from shuheng import history_store
from shuheng import path_utils
from shuheng.ui_types import Message


def _session_meta_increment_worker(path: str, worker_id: int, iterations: int, start_event) -> None:
    start_event.wait(timeout=10)
    for _ in range(iterations):
        def mutate(registry):
            shared = dict(registry.get("model_responses_shared.txt", {}))
            shared["rounds"] = int(shared.get("rounds") or 0) + 1
            registry["model_responses_shared.txt"] = shared
            registry[f"model_responses_worker_{worker_id}.txt"] = {"worker_id": worker_id}
            time.sleep(0.005)
            return shared["rounds"]

        committed, result = history_store.transact_session_meta_registry(path, mutate)
        assert result >= 1
        assert f"model_responses_worker_{worker_id}.txt" in committed


def _history_text_write_worker(path: str, text: str, start_event) -> None:
    start_event.wait(timeout=10)
    history_store.write_text_atomic(path, text)


def _legacy_history_copy_worker(source_dir: str, destination_dir: str, start_event) -> None:
    start_event.wait(timeout=10)
    app_module.copy_legacy_history_to_shuheng(source_dir, destination_dir)


def _start_and_join_processes(processes, start_event) -> None:
    for process in processes:
        process.start()
    start_event.set()
    try:
        for process in processes:
            process.join(timeout=20)
        assert [process.exitcode for process in processes] == [0] * len(processes)
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)


class TestSessionMetaRegistry:
    def test_name_rollback_does_not_overwrite_a_later_writer(self) -> None:
        names = {"session.txt": "original"}

        class Registry:
            def name_for(self, path: str) -> str:
                return names.get(Path(path).name, "")

            def set_name(self, path: str, name: str) -> None:
                names[Path(path).name] = name

        rollback = history_store.RollbackStack()
        rollback.set_session_name(Registry(), "/history/session.txt", "failed writer")
        names["session.txt"] = "later successful writer"

        rollback()

        assert names["session.txt"] == "later successful writer"

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

    def test_transaction_serializes_processes_without_lost_updates(self, tmp_path: Path) -> None:
        path = tmp_path / "session_meta.json"
        worker_count = 4
        iterations = 6
        ctx = multiprocessing.get_context("spawn")
        start_event = ctx.Event()
        processes = [
            ctx.Process(
                target=_session_meta_increment_worker,
                args=(str(path), worker_id, iterations, start_event),
            )
            for worker_id in range(worker_count)
        ]

        _start_and_join_processes(processes, start_event)

        registry = history_store.load_session_meta_registry(str(path))
        assert registry["model_responses_shared.txt"]["rounds"] == worker_count * iterations
        assert {
            registry[f"model_responses_worker_{worker_id}.txt"]["worker_id"]
            for worker_id in range(worker_count)
        } == set(range(worker_count))

    def test_transaction_supports_delete_and_rolls_back_exceptions(self, tmp_path: Path) -> None:
        path = tmp_path / "session_meta.json"
        original = {
            "model_responses_keep.txt": {"rounds": 1},
            "model_responses_delete.txt": {"rounds": 2},
        }
        history_store.save_session_meta_registry(str(path), original)

        committed, removed = history_store.transact_session_meta_registry(
            str(path),
            lambda registry: registry.pop("model_responses_delete.txt", None),
        )

        assert removed == {"rounds": 2}
        assert committed == {"model_responses_keep.txt": {"rounds": 1}}

        def fail_after_mutation(registry):
            registry["model_responses_keep.txt"]["rounds"] = 99
            raise RuntimeError("stop before commit")

        with pytest.raises(RuntimeError, match="stop before commit"):
            history_store.transact_session_meta_registry(str(path), fail_after_mutation)

        assert history_store.load_session_meta_registry(str(path)) == committed
        assert not list(tmp_path.glob("session_meta.json.tmp.*"))

    def test_noop_transaction_does_not_replace_registry_file(self, tmp_path: Path) -> None:
        path = tmp_path / "session_meta.json"
        history_store.save_session_meta_registry(str(path), {"model_responses_a.txt": {"rounds": 1}})
        inode_before = path.stat().st_ino

        committed, result = history_store.transact_session_meta_registry(str(path), lambda _registry: "unchanged")

        assert result == "unchanged"
        assert committed == {"model_responses_a.txt": {"rounds": 1}}
        assert path.stat().st_ino == inode_before

    def test_transaction_persists_in_place_nested_dict_and_list_mutations(self, tmp_path: Path) -> None:
        path = tmp_path / "session_meta.json"
        key = "model_responses_nested.txt"
        history_store.save_session_meta_registry(
            str(path),
            {
                key: {
                    "activity": {"counts": {"messages": 1}},
                    "durable_messages": [{"content": "first"}],
                }
            },
        )
        retained_registry = {}

        def mutate(registry):
            retained_registry["value"] = registry
            registry[key]["activity"]["counts"]["messages"] += 1
            registry[key]["durable_messages"].append({"content": "second"})
            return "nested-updated"

        committed, result = history_store.transact_session_meta_registry(str(path), mutate)

        expected = {
            key: {
                "activity": {"counts": {"messages": 2}},
                "durable_messages": [{"content": "first"}, {"content": "second"}],
            }
        }
        assert result == "nested-updated"
        assert committed == expected
        assert history_store.load_session_meta_registry(str(path)) == expected

        retained_registry["value"][key]["activity"]["counts"]["messages"] = 99
        retained_registry["value"][key]["durable_messages"].append({"content": "after-commit"})
        assert committed == expected
        assert history_store.load_session_meta_registry(str(path)) == expected

    def test_legacy_merge_adds_missing_entries_and_preserves_current_values(self, tmp_path: Path) -> None:
        path = tmp_path / "session_meta.json"
        history_store.save_session_meta_registry(
            str(path),
            {"model_responses_shared.txt": {"title": "current"}},
        )

        committed, changed = history_store.merge_session_meta_registry(
            str(path),
            {
                "model_responses_legacy.txt": {"title": "legacy"},
                "model_responses_shared.txt": {"title": "stale"},
            },
        )

        assert changed is True
        assert committed == {
            "model_responses_legacy.txt": {"title": "legacy"},
            "model_responses_shared.txt": {"title": "current"},
        }

    def test_concurrent_legacy_name_imports_preserve_existing_and_independent_titles(self, tmp_path: Path) -> None:
        destination = tmp_path / "destination"
        destination.mkdir()
        names_path = destination / "session_names.json"
        names_path.write_text(json.dumps({"shared.txt": "current"}), encoding="utf-8")
        sources: list[Path] = []
        for worker_id in range(4):
            source = tmp_path / f"source-{worker_id}"
            source.mkdir()
            (source / "session_names.json").write_text(
                json.dumps({"shared.txt": "stale", f"worker-{worker_id}.txt": f"title-{worker_id}"}),
                encoding="utf-8",
            )
            sources.append(source)

        ctx = multiprocessing.get_context("spawn")
        start_event = ctx.Event()
        processes = [
            ctx.Process(target=_legacy_history_copy_worker, args=(str(source), str(destination), start_event))
            for source in sources
        ]

        _start_and_join_processes(processes, start_event)

        names = json.loads(names_path.read_text(encoding="utf-8"))
        assert names["shared.txt"] == "current"
        assert {names[f"worker-{worker_id}.txt"] for worker_id in range(4)} == {
            f"title-{worker_id}" for worker_id in range(4)
        }
        assert not list(destination.glob("session_names.json.tmp*"))


class TestAtomicHistoryTextWrites:
    def test_transcript_rollback_does_not_overwrite_a_later_writer(self, tmp_path: Path) -> None:
        path = tmp_path / "transcript.txt"
        path.write_bytes(b"original")
        rollback = history_store.RollbackStack()
        rollback.write_subagent_transcript(
            str(path),
            [Message("user", "failed writer"), Message("assistant", "failed response")],
        )
        path.write_bytes(b"later successful writer")

        rollback()

        assert path.read_bytes() == b"later successful writer"

    def test_concurrent_processes_use_collision_safe_temporary_files(self, tmp_path: Path) -> None:
        path = tmp_path / "transcript.txt"
        payloads = [f"writer-{idx}\n" * 2000 for idx in range(4)]
        ctx = multiprocessing.get_context("spawn")
        start_event = ctx.Event()
        processes = [
            ctx.Process(target=_history_text_write_worker, args=(str(path), payload, start_event))
            for payload in payloads
        ]

        _start_and_join_processes(processes, start_event)

        assert path.read_text(encoding="utf-8") in payloads
        assert not list(tmp_path.glob("transcript.txt.tmp.*"))

    def test_replace_failure_cleans_unique_temporary_file(self, tmp_path: Path, monkeypatch) -> None:
        path = tmp_path / "transcript.txt"

        def fail_replace(_source, _target):
            raise OSError("replace failed")

        monkeypatch.setattr(history_store.os, "replace", fail_replace)

        with pytest.raises(OSError, match="replace failed"):
            history_store.write_text_atomic(str(path), "new transcript")

        assert not path.exists()
        assert not list(tmp_path.glob("transcript.txt.tmp.*"))


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


class TestRestoreMessageHelpers:
    @staticmethod
    def _user_text(prompt: str) -> str:
        return prompt.strip()

    @staticmethod
    def _tool_results(prompt: str) -> dict[str, str]:
        return {"tool": f"tool-for:{prompt.strip()}"} if prompt.strip().startswith("tool:") else {}

    @staticmethod
    def _format_segment(response: str, tool_results: dict[str, str]) -> str:
        suffix = f" [{tool_results['tool']}]" if tool_results else ""
        return response.strip() + suffix

    def test_history_round_count_uses_non_blank_users_then_pair_count(self) -> None:
        pairs = [(" first ", "one"), (" ", "two"), (" third ", "three")]

        assert history_store.history_round_count(pairs, user_text_from_prompt=self._user_text) == 2
        assert history_store.history_round_count([(" ", "one"), ("", "two")], user_text_from_prompt=self._user_text) == 2

    def test_extract_recent_ui_messages_from_pairs_groups_promptless_turns(self) -> None:
        pairs = [
            ("first", "first reply"),
            ("second", "second reply"),
            ("", "second tool follow-up"),
            ("tool:third", "third reply"),
        ]

        messages = history_store.extract_recent_ui_messages_from_pairs(
            pairs,
            2,
            user_text_from_prompt=self._user_text,
            tool_results_from_prompt=self._tool_results,
            format_response_segment=self._format_segment,
        )

        assert messages == [
            {"role": "user", "content": "second"},
            {
                "role": "assistant",
                "content": (
                    "\n\n**LLM Running (Turn 1) ...**\n\nsecond reply"
                    "\n\n**LLM Running (Turn 2) ...**\n\nsecond tool follow-up [tool-for:tool:third]"
                ),
            },
            {"role": "user", "content": "tool:third"},
            {"role": "assistant", "content": "\n\n**LLM Running (Turn 1) ...**\n\nthird reply"},
        ]

    def test_history_messages_from_pairs_returns_message_rows_and_counts(self) -> None:
        pairs = [("first", "first reply"), ("second", "second reply")]

        messages, loaded, total = history_store.history_messages_from_pairs(
            pairs,
            1,
            default_rounds=3,
            user_text_from_prompt=self._user_text,
            ui_messages_from_pairs=lambda source_pairs, rounds: history_store.extract_recent_ui_messages_from_pairs(
                source_pairs,
                rounds,
                user_text_from_prompt=self._user_text,
                tool_results_from_prompt=self._tool_results,
                format_response_segment=self._format_segment,
            ),
        )

        assert loaded == 1
        assert total == 2
        assert [(message.role, message.content) for message in messages] == [
            ("user", "second"),
            ("assistant", "\n\n**LLM Running (Turn 1) ...**\n\nsecond reply"),
        ]

    def test_app_restore_message_wrappers_preserve_behavior(self) -> None:
        pairs = [("first", repr([{"type": "text", "text": "first reply"}])), ("second", "['second reply']")]

        assert app_module.history_round_count(pairs) == history_store.history_round_count(
            pairs,
            user_text_from_prompt=app_module._user_text,
        )
        assert app_module.extract_recent_ui_messages_from_pairs(pairs, 1) == history_store.extract_recent_ui_messages_from_pairs(
            pairs,
            1,
            user_text_from_prompt=app_module._user_text,
            tool_results_from_prompt=app_module._tool_results_from_prompt,
            format_response_segment=app_module._format_response_segment,
        )
        assert app_module.history_messages_from_pairs(pairs, 1) == history_store.history_messages_from_pairs(
            pairs,
            1,
            default_rounds=app_module.RESTORE_DISPLAY_ROUNDS,
            user_text_from_prompt=app_module._user_text,
            ui_messages_from_pairs=app_module.extract_recent_ui_messages_from_pairs,
        )


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
