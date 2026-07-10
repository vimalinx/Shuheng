from __future__ import annotations

import os
from pathlib import Path

import pytest

from shuheng.agent_editor import (
    AgentEditor,
    Cursor,
    EditorDiagnostic,
    EditorPathError,
    ExternalFileConflictError,
    UnsupportedAuthoringFileError,
    content_digest,
    is_allowed_authoring_path,
    movement_target,
    resolve_project_file,
)


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_open_tracks_file_baseline_lines_cursor_and_viewport(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompts" / "main.md"
    write_bytes(source, "你好\r\nAgent\r\n".encode())

    editor = AgentEditor.open(project, "prompts/main.md")

    assert editor.project_root == project.resolve()
    assert editor.path == source.resolve()
    assert editor.lines == ["你好", "Agent", ""]
    assert editor.text == "你好\r\nAgent\r\n"
    assert editor.newline == "\r\n"
    assert editor.cursor == Cursor(0, 0)
    assert editor.viewport_top == 0
    assert editor.viewport_left == 0
    assert editor.original_digest == content_digest(source.read_bytes())
    assert editor.original_stat is not None
    assert editor.dirty is False
    assert editor.external_conflict is False


@pytest.mark.parametrize(
    "name",
    [
        "agent.yaml",
        "agent.yml",
        "prompt.md",
        "notes.txt",
        "tool.ts",
        "tool.js",
        "config.json",
        "settings.toml",
    ],
)
def test_authoring_file_allowlist_accepts_project_source_types(name: str) -> None:
    assert is_allowed_authoring_path(name) is True


@pytest.mark.parametrize("name", ["tool.sh", "image.png", "archive.zip", "README"])
def test_authoring_file_allowlist_rejects_non_source_types(name: str) -> None:
    assert is_allowed_authoring_path(name) is False


def test_open_rejects_path_escape_absolute_outside_and_unsupported_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(EditorPathError):
        AgentEditor.open(project, "../outside.md")
    with pytest.raises(EditorPathError):
        AgentEditor.open(project, outside)
    with pytest.raises(UnsupportedAuthoringFileError):
        AgentEditor.open(project, "payload.bin", create=True)


def test_open_rejects_symlink_escape(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "prompt.md").write_text("outside", encoding="utf-8")
    (project / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(EditorPathError):
        resolve_project_file(project, "linked/prompt.md")


def test_open_rejects_non_utf8_and_nul_text(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    invalid = project / "invalid.md"
    invalid.write_bytes(b"\xff\xfe")
    with pytest.raises(UnsupportedAuthoringFileError):
        AgentEditor.open(project, invalid)

    invalid.write_bytes(b"hello\x00world")
    with pytest.raises(UnsupportedAuthoringFileError):
        AgentEditor.open(project, invalid)


def test_insert_newline_backspace_and_delete_forward_are_deterministic(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, "abc\ndef".encode())
    editor = AgentEditor.open(project, source)

    editor.set_cursor(0, 1)
    assert editor.insert_text("你") is True
    assert editor.lines == ["a你bc", "def"]
    assert editor.cursor == Cursor(0, 2)

    assert editor.newline_at_cursor() is True
    assert editor.lines == ["a你", "bc", "def"]
    assert editor.cursor == Cursor(1, 0)

    assert editor.backspace() is True
    assert editor.lines == ["a你bc", "def"]
    assert editor.cursor == Cursor(0, 2)

    editor.move_end()
    assert editor.delete_forward() is True
    assert editor.lines == ["a你bcdef"]
    assert editor.cursor == Cursor(0, 4)
    assert editor.dirty is True


def test_edit_boundaries_are_noops_without_creating_undo_entries(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, b"")
    editor = AgentEditor.open(project, source)

    assert editor.backspace() is False
    assert editor.delete_forward() is False
    assert editor.insert_text("") is False
    assert editor.can_undo is False
    assert editor.dirty is False


def test_multiline_paste_normalizes_input_newlines_as_one_undo_step(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, "start:end".encode())
    editor = AgentEditor.open(project, source)
    editor.set_cursor(0, 6)

    assert editor.paste("甲\r\n乙\r丙\n") is True
    assert editor.lines == ["start:甲", "乙", "丙", "end"]
    assert editor.cursor == Cursor(3, 0)
    assert editor.dirty is True

    assert editor.undo() is True
    assert editor.text == "start:end"
    assert editor.cursor == Cursor(0, 6)
    assert editor.dirty is False
    assert editor.undo() is False


def test_undo_restores_cursor_viewport_and_dirty_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, b"one\ntwo\nthree")
    editor = AgentEditor.open(project, source)
    editor.set_cursor(1, 2)
    editor.set_viewport(1, 3)

    editor.insert_text("X")
    editor.set_viewport(2, 8)
    assert editor.undo() is True

    assert editor.lines == ["one", "two", "three"]
    assert editor.cursor == Cursor(1, 2)
    assert editor.viewport.top == 1
    assert editor.viewport.left == 3
    assert editor.dirty is False


def test_movement_targets_cross_lines_and_preserve_vertical_goal_column(tmp_path: Path) -> None:
    lines = ["abcd", "x", "uvwxyz"]
    assert movement_target(lines, Cursor(0, 0), "left") == Cursor(0, 0)
    assert movement_target(lines, Cursor(0, 4), "right") == Cursor(1, 0)
    assert movement_target(lines, Cursor(1, 0), "left") == Cursor(0, 4)
    assert movement_target(lines, Cursor(1, 1), "home") == Cursor(1, 0)
    assert movement_target(lines, Cursor(1, 0), "end") == Cursor(1, 1)
    assert movement_target(lines, Cursor(0, 3), "down") == Cursor(1, 1)
    assert movement_target(lines, Cursor(1, 1), "down", preferred_column=3) == Cursor(2, 3)

    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, b"abcd\nx\nuvwxyz")
    editor = AgentEditor.open(project, source)
    editor.set_cursor(0, 3)
    assert editor.move_down() == Cursor(1, 1)
    assert editor.move_down() == Cursor(2, 3)
    assert editor.move_up() == Cursor(1, 1)


def test_page_movement_updates_cursor_and_viewport(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, "\n".join(f"line-{index}" for index in range(20)).encode())
    editor = AgentEditor.open(project, source)
    editor.set_cursor(2, 4)
    editor.set_viewport(1, 0)

    assert editor.page_down(6) == Cursor(8, 4)
    assert editor.viewport.top == 7
    assert editor.page_up(6) == Cursor(2, 4)
    assert editor.viewport.top == 1
    editor.set_cursor(19, 7)
    assert editor.ensure_cursor_visible(5).top == 15


def test_atomic_save_preserves_newline_style_updates_baseline_and_clears_undo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, b"one\r\ntwo\r\n")
    before_mode = source.stat().st_mode
    editor = AgentEditor.open(project, source)
    editor.set_cursor(1, 3)
    editor.insert_text("-edited")

    result = editor.save()

    assert source.read_bytes() == b"one\r\ntwo-edited\r\n"
    assert result.path == source.resolve()
    assert result.digest == content_digest(source.read_bytes())
    assert editor.original_digest == result.digest
    assert editor.original_stat == result.stat
    assert editor.dirty is False
    assert editor.external_conflict is False
    assert editor.can_undo is False
    assert source.stat().st_mode & 0o777 == before_mode & 0o777
    assert not list(source.parent.glob(f".{source.name}.*.tmp"))

    # Saving again uses the refreshed baseline and does not report our own
    # atomic replace as an external change.
    assert editor.save().digest == result.digest


def test_new_empty_file_can_be_created_and_saved_atomically(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    source = project / "agent.yaml"
    editor = AgentEditor.open(project, source, create=True)

    assert editor.original_stat is None
    editor.paste("name: 示例\n")
    result = editor.save()

    assert source.read_text(encoding="utf-8") == "name: 示例\n"
    assert result.stat == editor.original_stat
    assert editor.dirty is False


def test_external_content_change_blocks_save_without_overwriting(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, b"original")
    editor = AgentEditor.open(project, source)
    editor.move_end()
    editor.insert_text(" buffer")
    source.write_text("external", encoding="utf-8")

    with pytest.raises(ExternalFileConflictError, match="reload or cancel"):
        editor.save()

    assert source.read_text(encoding="utf-8") == "external"
    assert editor.text == "original buffer"
    assert editor.dirty is True
    assert editor.external_conflict is True
    assert editor.cancel() is False
    assert editor.text == "original buffer"
    assert source.read_text(encoding="utf-8") == "external"


def test_external_stat_only_change_blocks_save(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, b"same")
    editor = AgentEditor.open(project, source)
    editor.move_end()
    editor.insert_text(" buffer")
    original_ns = source.stat().st_mtime_ns
    os.utime(source, ns=(original_ns + 2_000_000_000, original_ns + 2_000_000_000))
    assert source.read_bytes() == b"same"

    with pytest.raises(ExternalFileConflictError):
        editor.save()

    assert source.read_bytes() == b"same"
    assert editor.external_conflict is True


def test_new_file_appearing_externally_is_a_conflict(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    source = project / "agent.yaml"
    editor = AgentEditor.open(project, source, create=True)
    editor.insert_text("ours: true")
    source.write_text("theirs: true", encoding="utf-8")

    with pytest.raises(ExternalFileConflictError):
        editor.save()
    assert source.read_text(encoding="utf-8") == "theirs: true"


def test_deleted_open_file_is_an_external_conflict(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, b"original")
    editor = AgentEditor.open(project, source)
    editor.insert_text("buffer")
    source.unlink()

    with pytest.raises(ExternalFileConflictError):
        editor.save()
    assert source.exists() is False


def test_reload_discards_buffer_and_adopts_external_baseline(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, b"old")
    editor = AgentEditor.open(project, source)
    editor.move_end()
    editor.insert_text(" buffer")
    source.write_text("外部\n内容", encoding="utf-8")
    assert editor.check_external_conflict() is True

    editor.reload()

    assert editor.lines == ["外部", "内容"]
    assert editor.cursor == Cursor(0, 0)
    assert editor.dirty is False
    assert editor.external_conflict is False
    assert editor.can_undo is False
    editor.move_end()
    editor.insert_text("!")
    editor.save()
    assert source.read_text(encoding="utf-8") == "外部!\n内容"


def test_validation_callback_supports_file_line_diagnostics_and_navigation(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "agent.yaml"
    write_bytes(source, b"name: demo\ninvalid: true")
    calls: list[tuple[Path, str]] = []

    def validator(path: Path, text: str):
        calls.append((path, text))
        if "invalid" in text:
            return [
                EditorDiagnostic(
                    message="unsupported field",
                    path=str(path),
                    line=2,
                    column=1,
                    code="unknown_field",
                )
            ]
        return []

    editor = AgentEditor.open(project, source, validator=validator)
    assert editor.diagnostics[0].message == "unsupported field"
    assert editor.diagnostics[0].line == 2
    assert editor.goto_diagnostic() == Cursor(1, 0)

    editor.move_end()
    editor.backspace()
    editor.save()
    assert calls
    assert editor.diagnostics[0].path == str(source.resolve())


def test_validation_callback_accepts_mapping_and_converts_failure_to_diagnostic(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "agent.json"
    write_bytes(source, b"{}")

    editor = AgentEditor.open(
        project,
        source,
        validator=lambda path, text: [{"message": "bad value", "file": str(path), "line": 7, "col": 3}],
    )
    assert editor.diagnostics == [
        EditorDiagnostic(message="bad value", path=str(source.resolve()), line=7, column=3)
    ]

    def broken_validator(path: Path, text: str):
        raise RuntimeError("boom")

    editor.validator = broken_validator
    diagnostics = editor.validate()
    assert diagnostics[0].code == "validator_error"
    assert "RuntimeError: boom" in diagnostics[0].message


def test_inserting_nul_is_rejected_without_mutating_buffer(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "prompt.md"
    write_bytes(source, b"safe")
    editor = AgentEditor.open(project, source)

    with pytest.raises(UnsupportedAuthoringFileError):
        editor.insert_text("bad\x00text")
    assert editor.text == "safe"
    assert editor.dirty is False
    assert editor.can_undo is False
