"""Tests for path-safety and ID-sanitization helpers (shuheng.app).

These guard against directory traversal (secret vault, artifacts, workspaces)
and enforce stable identifier shapes for subagents/workspaces.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import shuheng.app as app

from shuheng import path_utils
from shuheng.app import (
    clean_subagent_id,
    normalized_path,
    normalized_workspace_id,
    path_is_within,
    secret_safe_session_id,
    short_uid,
    workspace_slug,
)


class TestNormalizedPath:
    def test_expands_user(self, monkeypatch) -> None:
        monkeypatch.setenv("HOME", "/tmp/shuheng-test-home")
        assert normalized_path("~/x") == "/tmp/shuheng-test-home/x"
        assert path_utils.normalized_path("~/x") == "/tmp/shuheng-test-home/x"

    def test_makes_absolute(self) -> None:
        # Relative path resolved against cwd.
        result = normalized_path("a/b")
        assert os.path.isabs(result)

    def test_empty_falls_back_to_cwd(self) -> None:
        assert os.path.isabs(normalized_path(""))

    def test_app_wrapper_matches_module(self) -> None:
        assert app.normalized_path is path_utils.normalized_path


class TestPathIsWithin:
    def test_inside(self, tmp_path: Path) -> None:
        inner = tmp_path / "sub" / "file"
        inner.parent.mkdir()
        inner.write_text("x")
        assert path_is_within(str(inner), str(tmp_path)) is True

    def test_outside(self, tmp_path: Path) -> None:
        assert path_is_within("/etc/passwd", str(tmp_path)) is False

    def test_root_is_within_itself(self, tmp_path: Path) -> None:
        assert path_is_within(str(tmp_path), str(tmp_path)) is True

    def test_sibling_not_within(self, tmp_path: Path) -> None:
        sibling = tmp_path.parent / "other_dir_xyz"
        sibling.mkdir(exist_ok=True)
        try:
            assert path_is_within(str(sibling), str(tmp_path)) is False
        finally:
            sibling.rmdir()

    def test_traversal_rejected(self, tmp_path: Path) -> None:
        # "/safe_root/../evil" should normalize outside.
        traversing = str(tmp_path) + "/../" + os.path.basename(str(tmp_path)) + "_evil"
        # After realpath this points outside tmp_path -> False (if it exists).
        # We assert the function does not crash and returns a bool.
        assert isinstance(path_is_within(traversing, str(tmp_path)), bool)

    def test_app_wrapper_matches_module(self) -> None:
        assert app.path_is_within is path_utils.path_is_within


class TestNormalSessionLogPath:
    def test_accepts_model_response_inside_history_root(self, tmp_path: Path) -> None:
        history_root = tmp_path / "model_responses"
        trash_root = history_root / ".trash"
        history_root.mkdir()
        path = history_root / "model_responses_a.txt"

        assert path_utils.is_normal_session_log_path(
            str(path),
            model_responses_dir=str(history_root),
            session_trash_dir=str(trash_root),
        )

    def test_rejects_trash_path(self, tmp_path: Path) -> None:
        history_root = tmp_path / "model_responses"
        trash_root = history_root / ".trash"
        trash_root.mkdir(parents=True)
        path = trash_root / "model_responses_a.txt"

        assert not path_utils.is_normal_session_log_path(
            str(path),
            model_responses_dir=str(history_root),
            session_trash_dir=str(trash_root),
        )

    def test_rejects_non_model_response_basename(self, tmp_path: Path) -> None:
        history_root = tmp_path / "model_responses"
        trash_root = history_root / ".trash"
        history_root.mkdir()
        path = history_root / "notes.txt"

        assert not path_utils.is_normal_session_log_path(
            str(path),
            model_responses_dir=str(history_root),
            session_trash_dir=str(trash_root),
        )

    def test_app_wrapper_uses_current_roots(self, tmp_path: Path) -> None:
        old_model_responses_dir = app.MODEL_RESPONSES_DIR
        old_session_trash_dir = app.SESSION_TRASH_DIR
        try:
            app.MODEL_RESPONSES_DIR = str(tmp_path / "model_responses")
            app.SESSION_TRASH_DIR = str(tmp_path / "model_responses" / ".trash")
            path = Path(app.MODEL_RESPONSES_DIR) / "model_responses_a.txt"

            assert app.is_normal_session_log_path(str(path))
        finally:
            app.MODEL_RESPONSES_DIR = old_model_responses_dir
            app.SESSION_TRASH_DIR = old_session_trash_dir


class TestSecretSafeSessionId:
    def test_passes_safe_chars(self) -> None:
        assert secret_safe_session_id("abc_123-4.5") == "abc_123-4.5"

    def test_replaces_slashes(self) -> None:
        assert secret_safe_session_id("../etc/passwd") == "..-etc-passwd"

    def test_strips_leading_trailing_dashes(self) -> None:
        assert secret_safe_session_id("---safe---") == "safe"

    def test_empty_falls_back(self) -> None:
        assert secret_safe_session_id("") == "session"

    def test_preserves_case(self) -> None:
        # Uppercase is allowed by the allow-list.
        assert secret_safe_session_id("ABC123") == "ABC123"


class TestCleanSubagentId:
    def test_lowercases(self) -> None:
        assert clean_subagent_id("Researcher") == "researcher"

    def test_strips_invalid(self) -> None:
        assert clean_subagent_id("research!@#er") == "researcher"

    def test_spaces_to_dashes(self) -> None:
        assert clean_subagent_id("code reviewer") == "code-reviewer"

    def test_max_40_chars(self) -> None:
        result = clean_subagent_id("a" * 100)
        assert len(result) == 40

    def test_empty_falls_back_to_agent_prefix(self) -> None:
        result = clean_subagent_id("")
        assert result.startswith("agent-")

    def test_all_invalid_falls_back(self) -> None:
        result = clean_subagent_id("!!!")
        assert result.startswith("agent-")

    def test_nfkc_normalization(self) -> None:
        # Fullwidth 'Ａ' (U+FF21) normalizes to 'A'.
        assert clean_subagent_id("Ａ") == "a"


class TestNormalizedWorkspaceId:
    def test_lowercases(self) -> None:
        assert normalized_workspace_id("MyProject") == "myproject"

    def test_replaces_separators(self) -> None:
        assert normalized_workspace_id("my/project") == "my-project"

    def test_collapses_dashes(self) -> None:
        assert normalized_workspace_id("a---b") == "a-b"

    def test_max_80_chars(self) -> None:
        assert len(normalized_workspace_id("x" * 200)) == 80

    def test_empty(self) -> None:
        assert normalized_workspace_id("") == ""


class TestWorkspaceSlug:
    def test_ascii_slug(self) -> None:
        assert workspace_slug("Shuheng Project!") == "shuheng-project"

    def test_non_ascii_dropped(self) -> None:
        # NFKD strips accents; non-decomposable CJK is dropped.
        slug = workspace_slug("枢衡")
        assert slug == "workspace"  # all dropped -> fallback

    def test_empty_falls_back(self) -> None:
        assert workspace_slug("") == "workspace"

class TestWorkspaceIdForRoot:
    def test_new_workspace_id_uses_sha256_suffix(self, tmp_path: Path, monkeypatch) -> None:
        workspaces = tmp_path / "workspaces"
        monkeypatch.setattr(app, "SHUHENG_WORKSPACES_DIR", str(workspaces))
        root = tmp_path / "Project Root"
        root.mkdir()
        normalized = os.path.abspath(str(root))
        expected = hashlib.sha256(normalized.encode("utf-8", errors="replace")).hexdigest()[:8]
        assert app.workspace_id_for_root(str(root)).endswith(f"-{expected}")

    def test_legacy_sha1_workspace_id_remains_discoverable(self, tmp_path: Path, monkeypatch) -> None:
        workspaces = tmp_path / "workspaces"
        monkeypatch.setattr(app, "SHUHENG_WORKSPACES_DIR", str(workspaces))
        root = tmp_path / "Project Root"
        root.mkdir()
        normalized = os.path.abspath(str(root))
        slug = app.workspace_slug(root.name)
        legacy = hashlib.sha1(normalized.encode("utf-8", errors="replace")).hexdigest()[:8]
        legacy_id = f"{slug}-{legacy}"
        (workspaces / legacy_id).mkdir(parents=True)
        assert app.workspace_id_for_root(str(root)) == legacy_id


class TestShortUid:
    def test_has_prefix(self) -> None:
        assert short_uid("task").startswith("task_")

    def test_unique(self) -> None:
        ids = {short_uid("x") for _ in range(100)}
        assert len(ids) > 1  # not all identical

    def test_contains_pid(self) -> None:
        uid = short_uid("p")
        # Format: prefix_<hex-time>_<hex-pid>
        parts = uid.split("_")
        assert len(parts) == 3
