"""Tests for time/format and small pure helpers (shuheng.app).

Covers now_iso, atomic file writes, and helper formatters that don't need
curses or external state.
"""
from __future__ import annotations

from pathlib import Path

from shuheng.app import (
    append_text_file,
    now_iso,
    write_bytes_atomic,
    write_text_atomic,
)


class TestNowIso:
    def test_returns_nonempty(self) -> None:
        assert now_iso() != ""

    def test_format_shape(self) -> None:
        # YYYY-MM-DDTHH:MM:SS<tz>
        ts = now_iso()
        assert len(ts) >= 19
        assert ts[4] == "-"
        assert ts[10] == "T"

    def test_changes_over_time(self) -> None:
        import time

        first = now_iso()
        time.sleep(1.1)
        second = now_iso()
        assert first != second


class TestWriteTextAtomic:
    def test_writes_content(self, tmp_path: Path) -> None:
        path = tmp_path / "out.txt"
        write_text_atomic(str(path), "hello")
        assert path.read_text(encoding="utf-8") == "hello"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "deep" / "out.txt"
        write_text_atomic(str(path), "x")
        assert path.exists()

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        path = tmp_path / "out.txt"
        path.write_text("old", encoding="utf-8")
        write_text_atomic(str(path), "new")
        assert path.read_text(encoding="utf-8") == "new"

    def test_atomic_no_tmp_left(self, tmp_path: Path) -> None:
        path = tmp_path / "out.txt"
        write_text_atomic(str(path), "data")
        assert not (tmp_path / "out.txt.tmp").exists()


class TestWriteBytesAtomic:
    def test_writes_bytes(self, tmp_path: Path) -> None:
        path = tmp_path / "out.bin"
        write_bytes_atomic(str(path), b"\x00\x01\x02")
        assert path.read_bytes() == b"\x00\x01\x02"

    def test_overwrites(self, tmp_path: Path) -> None:
        path = tmp_path / "out.bin"
        path.write_bytes(b"old")
        write_bytes_atomic(str(path), b"new")
        assert path.read_bytes() == b"new"


class TestAppendTextFile:
    def test_appends(self, tmp_path: Path) -> None:
        path = tmp_path / "log.txt"
        append_text_file(str(path), "a\n")
        append_text_file(str(path), "b\n")
        assert path.read_text(encoding="utf-8") == "a\nb\n"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "x" / "y" / "log.txt"
        append_text_file(str(path), "first")
        assert path.exists()
