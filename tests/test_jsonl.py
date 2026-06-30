"""Tests for JSONL read/append helpers.

The shared ledger store holds a process-internal lock per path plus an advisory
fcntl.flock for cross-process safety. These tests cover correctness, caching,
app compatibility wrappers, and JSON object read-modify-write concurrency.
"""
from __future__ import annotations

import json
import multiprocessing
from pathlib import Path


from ga_tui.app import append_jsonl, read_jsonl
from ga_tui.ledger_store import (
    clear_jsonl_caches,
    jsonl_file_signature,
    latest_records_by_id,
    rows_matching,
    update_json_dict_file,
)


def increment_json_counter(path: str, iterations: int) -> None:
    for _ in range(iterations):
        def update(data: dict[str, object]) -> tuple[dict[str, object], None]:
            data["count"] = int(data.get("count") or 0) + 1
            return data, None

        update_json_dict_file(path, update)


class TestAppendJsonl:
    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "deep" / "tasks.jsonl"
        append_jsonl(str(path), {"task_id": "t1"})
        assert path.exists()

    def test_appends_records(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        append_jsonl(str(path), {"task_id": "t1"})
        append_jsonl(str(path), {"task_id": "t2"})
        rows = read_jsonl(str(path))
        assert [r["task_id"] for r in rows] == ["t1", "t2"]

    def test_unicode_payload(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        append_jsonl(str(path), {"name": "枢衡", "emoji": "\N{ROCKET}"})
        rows = read_jsonl(str(path))
        assert rows[0]["name"] == "枢衡"

    def test_writes_valid_json_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        append_jsonl(str(path), {"a": 1})
        append_jsonl(str(path), {"b": 2})
        with open(path, encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        assert len(lines) == 2
        for line in lines:
            assert json.loads(line)  # no exception

    def test_overwrites_partial_not_possible(self, tmp_path: Path) -> None:
        # Append mode never truncates; an existing file keeps prior content.
        path = tmp_path / "tasks.jsonl"
        path.write_text('{"existing": true}\n', encoding="utf-8")
        append_jsonl(str(path), {"new": True})
        rows = read_jsonl(str(path))
        assert len(rows) == 2


class TestReadJsonl:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert read_jsonl(str(tmp_path / "nope.jsonl")) == []

    def test_skips_blank_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        path.write_text('{"a": 1}\n\n  \n{"b": 2}\n', encoding="utf-8")
        assert len(read_jsonl(str(path))) == 2

    def test_skips_corrupt_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        path.write_text('{"a": 1}\nBROKEN\n{"b": 2}\n', encoding="utf-8")
        rows = read_jsonl(str(path))
        assert len(rows) == 2
        assert rows[0]["a"] == 1

    def test_limit_returns_tail(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        for i in range(10):
            append_jsonl(str(path), {"i": i})
        rows = read_jsonl(str(path), limit=3)
        assert [r["i"] for r in rows] == [7, 8, 9]

    def test_limit_zero_means_all(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        for i in range(5):
            append_jsonl(str(path), {"i": i})
        assert len(read_jsonl(str(path), limit=0)) == 5

    def test_skips_non_dict_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        path.write_text('[1,2,3]\n"string"\n42\n{"ok": true}\n', encoding="utf-8")
        rows = read_jsonl(str(path))
        assert len(rows) == 1
        assert rows[0]["ok"] is True


class TestLedgerStore:
    def test_latest_records_cache_returns_copies_and_invalidates_on_append(self, tmp_path: Path) -> None:
        clear_jsonl_caches()
        path = tmp_path / "tasks.jsonl"
        append_jsonl(str(path), {"task_id": "t1", "status": "queued"})
        append_jsonl(str(path), {"task_id": "t2", "status": "working"})

        first = latest_records_by_id(str(path), "task_id")
        first["t1"]["status"] = "mutated"
        assert latest_records_by_id(str(path), "task_id")["t1"]["status"] == "queued"

        append_jsonl(str(path), {"task_id": "t1", "status": "completed"})
        latest = latest_records_by_id(str(path), "task_id")
        assert latest["t1"]["status"] == "completed"
        assert latest["t2"]["status"] == "working"

    def test_rows_matching_reads_exact_field_history(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        append_jsonl(str(path), {"task_id": "t1", "status": "queued"})
        append_jsonl(str(path), {"task_id": "t2", "status": "working"})
        append_jsonl(str(path), {"task_id": "t1", "status": "completed"})

        rows = rows_matching(str(path), "task_id", "t1")
        assert [row["status"] for row in rows] == ["queued", "completed"]

    def test_file_signature_changes_on_append(self, tmp_path: Path) -> None:
        path = tmp_path / "tasks.jsonl"
        assert jsonl_file_signature(str(path)) == (0, 0)
        append_jsonl(str(path), {"task_id": "t1"})
        first = jsonl_file_signature(str(path))
        append_jsonl(str(path), {"task_id": "t2"})
        assert jsonl_file_signature(str(path))[1] > first[1]

    def test_update_json_dict_file_returns_result_and_preserves_existing(self, tmp_path: Path) -> None:
        path = tmp_path / "locks.json"
        path.write_text('{"single_writer": {"task_id": "old"}}\n', encoding="utf-8")

        def update(data: dict[str, object]) -> tuple[dict[str, object], str]:
            assert data["single_writer"] == {"task_id": "old"}
            data["single_writer"] = {"task_id": "new"}
            return data, "updated"

        assert update_json_dict_file(str(path), update) == "updated"
        assert json.loads(path.read_text(encoding="utf-8")) == {"single_writer": {"task_id": "new"}}

    def test_update_json_dict_file_serializes_cross_process_updates(self, tmp_path: Path) -> None:
        path = tmp_path / "locks.json"
        process_count = 4
        iterations = 25
        processes = [
            multiprocessing.Process(target=increment_json_counter, args=(str(path), iterations))
            for _ in range(process_count)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=10)
            if process.exitcode is None:
                process.terminate()
                process.join()
            assert process.exitcode == 0

        assert json.loads(path.read_text(encoding="utf-8"))["count"] == process_count * iterations
