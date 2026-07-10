"""Pure single-file editor state for Agent Project authoring files.

This module deliberately knows nothing about curses, the Shuheng application
state, or runtime providers.  It owns only deterministic text transitions and
the filesystem consistency rules needed by an editor view.

Cursor coordinates are zero-based.  Diagnostic line/column coordinates are
one-based, matching common parser and compiler output.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat as stat_module
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


ALLOWED_AUTHORING_SUFFIXES = frozenset(
    {
        ".cjs",
        ".js",
        ".json",
        ".jsonc",
        ".jsx",
        ".markdown",
        ".md",
        ".mjs",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }
)

_NEWLINE_RE = re.compile(r"\r\n|\r|\n")
_DEFAULT_UNDO_LIMIT = 200


class AgentEditorError(Exception):
    """Base error for the pure Agent Project editor model."""


class EditorPathError(AgentEditorError, ValueError):
    """Raised when an editor path is outside the project or is not authorable."""


class UnsupportedAuthoringFileError(EditorPathError):
    """Raised when a file type or file content is not supported by the editor."""


class ExternalFileConflictError(AgentEditorError):
    """Raised when saving would overwrite a file changed outside the editor."""


@dataclass(frozen=True)
class Cursor:
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class Viewport:
    top: int = 0
    left: int = 0


@dataclass(frozen=True)
class FileStatSnapshot:
    """Stable stat fields used to notice same-content external replacements."""

    device: int
    inode: int
    mode: int
    size: int
    mtime_ns: int
    ctime_ns: int

    @classmethod
    def from_stat_result(cls, value: os.stat_result) -> "FileStatSnapshot":
        return cls(
            device=int(value.st_dev),
            inode=int(value.st_ino),
            mode=int(value.st_mode),
            size=int(value.st_size),
            mtime_ns=int(value.st_mtime_ns),
            ctime_ns=int(value.st_ctime_ns),
        )


@dataclass(frozen=True)
class EditorDiagnostic:
    message: str
    path: str = ""
    line: int = 1
    column: int = 1
    severity: str = "error"
    code: str = ""


Validator = Callable[[Path, str], Iterable[EditorDiagnostic | Mapping[str, Any]] | None]


@dataclass(frozen=True)
class SaveResult:
    path: Path
    digest: str
    stat: FileStatSnapshot
    diagnostics: tuple[EditorDiagnostic, ...] = ()


@dataclass(frozen=True)
class _DiskSnapshot:
    data: bytes
    digest: str
    stat: FileStatSnapshot


@dataclass(frozen=True)
class _UndoSnapshot:
    lines: tuple[str, ...]
    cursor: Cursor
    viewport: Viewport
    preferred_column: int | None


def content_digest(value: str | bytes) -> str:
    """Return a stable SHA-256 digest for authoring content."""

    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def is_allowed_authoring_path(path: str | os.PathLike[str]) -> bool:
    """Whether *path* has an allowlisted text authoring suffix."""

    return Path(path).suffix.casefold() in ALLOWED_AUTHORING_SUFFIXES


def resolve_project_file(
    project_root: str | os.PathLike[str],
    path: str | os.PathLike[str],
) -> tuple[Path, Path]:
    """Resolve one authoring file and prove that it remains in the project.

    Existing symlinks are resolved, so a symlink inside the project cannot be
    used to open or save a target outside the project root.
    """

    root = Path(project_root).expanduser().resolve(strict=False)
    if not root.is_dir():
        raise EditorPathError(f"Agent Project root is not a directory: {root}")

    raw = Path(path).expanduser()
    candidate = raw if raw.is_absolute() else root / raw
    resolved = candidate.resolve(strict=False)
    try:
        contained = os.path.commonpath((str(root), str(resolved))) == str(root)
    except ValueError:
        contained = False
    if not contained or resolved == root:
        raise EditorPathError(f"Authoring file must stay inside the Agent Project root: {path}")
    if not is_allowed_authoring_path(candidate) or not is_allowed_authoring_path(resolved):
        allowed = ", ".join(sorted(ALLOWED_AUTHORING_SUFFIXES))
        raise UnsupportedAuthoringFileError(
            f"Unsupported Agent Project authoring file type: {candidate.name}. Allowed: {allowed}"
        )
    return root, resolved


def _preferred_newline(text: str) -> str:
    match = _NEWLINE_RE.search(text)
    return match.group(0) if match else "\n"


def _split_lines(text: str, newline: str | None = None) -> tuple[list[str], str]:
    selected = newline or _preferred_newline(text)
    # Authoring files are represented without embedded newline characters.
    # Empty final items preserve a trailing newline exactly.
    return _NEWLINE_RE.split(text), selected


def _decode_authoring_bytes(data: bytes, path: Path) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedAuthoringFileError(f"Authoring file must be UTF-8 text: {path}") from exc
    if "\x00" in text:
        raise UnsupportedAuthoringFileError(f"Authoring file contains a NUL byte: {path}")
    return text


def _read_disk_snapshot(path: Path, *, attempts: int = 3) -> _DiskSnapshot:
    """Read bytes and stat from one stable pathname snapshot."""

    last_error: Exception | None = None
    for _attempt in range(max(1, attempts)):
        try:
            with path.open("rb") as handle:
                opened_stat = FileStatSnapshot.from_stat_result(os.fstat(handle.fileno()))
                if not stat_module.S_ISREG(opened_stat.mode):
                    raise UnsupportedAuthoringFileError(f"Authoring path is not a regular file: {path}")
                data = handle.read()
            path_stat = FileStatSnapshot.from_stat_result(path.stat())
        except (FileNotFoundError, OSError) as exc:
            last_error = exc
            continue
        if opened_stat == path_stat:
            return _DiskSnapshot(data=data, digest=content_digest(data), stat=path_stat)
        last_error = ExternalFileConflictError(f"Authoring file changed while it was being read: {path}")
    if isinstance(last_error, FileNotFoundError):
        raise last_error
    if last_error is not None:
        raise ExternalFileConflictError(f"Could not read a stable authoring file snapshot: {path}") from last_error
    raise ExternalFileConflictError(f"Could not read a stable authoring file snapshot: {path}")


def _normalize_diagnostic(
    value: EditorDiagnostic | Mapping[str, Any],
    *,
    default_path: Path,
) -> EditorDiagnostic:
    if isinstance(value, EditorDiagnostic):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("validator diagnostics must be EditorDiagnostic or mapping values")
    return EditorDiagnostic(
        message=str(value.get("message") or value.get("detail") or "Validation failed"),
        path=str(value.get("path") or value.get("file") or default_path),
        line=max(1, int(value.get("line") or 1)),
        column=max(1, int(value.get("column") or value.get("col") or 1)),
        severity=str(value.get("severity") or "error"),
        code=str(value.get("code") or ""),
    )


def movement_target(
    lines: Sequence[str],
    cursor: Cursor,
    movement: str,
    *,
    page_rows: int = 1,
    preferred_column: int | None = None,
) -> Cursor:
    """Return a clamped cursor target for a deterministic movement command."""

    safe_lines = list(lines) or [""]
    line = min(max(0, int(cursor.line)), len(safe_lines) - 1)
    column = min(max(0, int(cursor.column)), len(safe_lines[line]))
    command = str(movement or "").strip().lower().replace("-", "_")

    if command == "left":
        if column > 0:
            return Cursor(line, column - 1)
        if line > 0:
            return Cursor(line - 1, len(safe_lines[line - 1]))
        return Cursor(line, column)
    if command == "right":
        if column < len(safe_lines[line]):
            return Cursor(line, column + 1)
        if line + 1 < len(safe_lines):
            return Cursor(line + 1, 0)
        return Cursor(line, column)
    if command == "home":
        return Cursor(line, 0)
    if command == "end":
        return Cursor(line, len(safe_lines[line]))
    if command in {"up", "down", "page_up", "page_down"}:
        delta = 1
        if command.startswith("page_"):
            delta = max(1, int(page_rows))
        if command in {"up", "page_up"}:
            target_line = max(0, line - delta)
        else:
            target_line = min(len(safe_lines) - 1, line + delta)
        goal = column if preferred_column is None else max(0, int(preferred_column))
        return Cursor(target_line, min(goal, len(safe_lines[target_line])))
    raise ValueError(f"Unknown editor movement: {movement}")


@dataclass
class AgentEditor:
    """Narrowly stateful, single-file Agent Project editor model."""

    project_root: Path
    path: Path
    lines: list[str]
    cursor: Cursor = field(default_factory=Cursor)
    viewport: Viewport = field(default_factory=Viewport)
    dirty: bool = False
    original_digest: str = ""
    original_stat: FileStatSnapshot | None = None
    diagnostics: list[EditorDiagnostic] = field(default_factory=list)
    external_conflict: bool = False
    newline: str = "\n"
    validator: Validator | None = field(default=None, repr=False, compare=False)
    undo_limit: int = field(default=_DEFAULT_UNDO_LIMIT, repr=False)
    _original_text: str = field(default="", repr=False, compare=False)
    _undo_stack: list[_UndoSnapshot] = field(default_factory=list, repr=False, compare=False)
    _preferred_column: int | None = field(default=None, repr=False, compare=False)

    @classmethod
    def open(
        cls,
        project_root: str | os.PathLike[str],
        path: str | os.PathLike[str],
        *,
        create: bool = False,
        validator: Validator | None = None,
        undo_limit: int = _DEFAULT_UNDO_LIMIT,
    ) -> "AgentEditor":
        root, resolved = resolve_project_file(project_root, path)
        if resolved.exists():
            snapshot = _read_disk_snapshot(resolved)
            text = _decode_authoring_bytes(snapshot.data, resolved)
            lines, newline = _split_lines(text)
            baseline_text = newline.join(lines)
            editor = cls(
                project_root=root,
                path=resolved,
                lines=lines or [""],
                original_digest=snapshot.digest,
                original_stat=snapshot.stat,
                newline=newline,
                validator=validator,
                undo_limit=max(1, int(undo_limit)),
                _original_text=baseline_text,
            )
        else:
            if not create:
                raise FileNotFoundError(resolved)
            if not resolved.parent.is_dir():
                raise EditorPathError(f"Authoring file parent directory does not exist: {resolved.parent}")
            editor = cls(
                project_root=root,
                path=resolved,
                lines=[""],
                original_digest=content_digest(b""),
                original_stat=None,
                validator=validator,
                undo_limit=max(1, int(undo_limit)),
                _original_text="",
            )
        editor._clamp_state()
        editor.validate()
        return editor

    @property
    def text(self) -> str:
        return self.newline.join(self.lines)

    @property
    def cursor_line(self) -> int:
        return self.cursor.line

    @property
    def cursor_column(self) -> int:
        return self.cursor.column

    @property
    def viewport_top(self) -> int:
        return self.viewport.top

    @property
    def viewport_left(self) -> int:
        return self.viewport.left

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def _clamp_state(self) -> None:
        if not self.lines:
            self.lines = [""]
        line = min(max(0, int(self.cursor.line)), len(self.lines) - 1)
        column = min(max(0, int(self.cursor.column)), len(self.lines[line]))
        self.cursor = Cursor(line, column)
        self.viewport = Viewport(max(0, self.viewport.top), max(0, self.viewport.left))

    def _snapshot_for_undo(self) -> _UndoSnapshot:
        return _UndoSnapshot(
            lines=tuple(self.lines),
            cursor=self.cursor,
            viewport=self.viewport,
            preferred_column=self._preferred_column,
        )

    def _begin_edit(self) -> None:
        self._undo_stack.append(self._snapshot_for_undo())
        if len(self._undo_stack) > self.undo_limit:
            del self._undo_stack[: len(self._undo_stack) - self.undo_limit]

    def _finish_edit(self) -> None:
        self._clamp_state()
        self.dirty = self.text != self._original_text
        self.validate()

    def set_cursor(self, line: int, column: int) -> Cursor:
        self.cursor = Cursor(int(line), int(column))
        self._preferred_column = None
        self._clamp_state()
        return self.cursor

    def set_viewport(self, top: int, left: int = 0) -> Viewport:
        self.viewport = Viewport(max(0, int(top)), max(0, int(left)))
        return self.viewport

    def ensure_cursor_visible(self, height: int, width: int = 0) -> Viewport:
        rows = max(1, int(height))
        top = self.viewport.top
        if self.cursor.line < top:
            top = self.cursor.line
        elif self.cursor.line >= top + rows:
            top = self.cursor.line - rows + 1
        left = self.viewport.left
        if width > 0:
            columns = max(1, int(width))
            if self.cursor.column < left:
                left = self.cursor.column
            elif self.cursor.column >= left + columns:
                left = self.cursor.column - columns + 1
        self.viewport = Viewport(max(0, top), max(0, left))
        return self.viewport

    def move(self, movement: str, *, page_rows: int = 1) -> Cursor:
        command = str(movement or "").strip().lower().replace("-", "_")
        vertical = command in {"up", "down", "page_up", "page_down"}
        if vertical and self._preferred_column is None:
            self._preferred_column = self.cursor.column
        target = movement_target(
            self.lines,
            self.cursor,
            command,
            page_rows=page_rows,
            preferred_column=self._preferred_column if vertical else None,
        )
        self.cursor = target
        if not vertical:
            self._preferred_column = None
        if command == "page_up":
            self.viewport = Viewport(max(0, self.viewport.top - max(1, int(page_rows))), self.viewport.left)
        elif command == "page_down":
            maximum = max(0, len(self.lines) - 1)
            self.viewport = Viewport(
                min(maximum, self.viewport.top + max(1, int(page_rows))),
                self.viewport.left,
            )
        return self.cursor

    def move_left(self) -> Cursor:
        return self.move("left")

    def move_right(self) -> Cursor:
        return self.move("right")

    def move_up(self) -> Cursor:
        return self.move("up")

    def move_down(self) -> Cursor:
        return self.move("down")

    def move_home(self) -> Cursor:
        return self.move("home")

    def move_end(self) -> Cursor:
        return self.move("end")

    def page_up(self, page_rows: int) -> Cursor:
        return self.move("page_up", page_rows=page_rows)

    def page_down(self, page_rows: int) -> Cursor:
        return self.move("page_down", page_rows=page_rows)

    def insert_text(self, value: str) -> bool:
        text = str(value)
        if not text:
            return False
        if "\x00" in text:
            raise UnsupportedAuthoringFileError("NUL characters are not allowed in authoring text")
        self._begin_edit()
        line_index = self.cursor.line
        column = self.cursor.column
        current = self.lines[line_index]
        before, after = current[:column], current[column:]
        parts = _NEWLINE_RE.split(text)
        if len(parts) == 1:
            self.lines[line_index] = before + parts[0] + after
            self.cursor = Cursor(line_index, column + len(parts[0]))
        else:
            replacement = [before + parts[0], *parts[1:-1], parts[-1] + after]
            self.lines[line_index : line_index + 1] = replacement
            self.cursor = Cursor(line_index + len(replacement) - 1, len(parts[-1]))
        self._preferred_column = None
        self._finish_edit()
        return True

    def paste(self, value: str) -> bool:
        """Insert a possibly multiline bracketed-paste payload as one undo step."""

        return self.insert_text(value)

    def newline_at_cursor(self) -> bool:
        return self.insert_text("\n")

    def backspace(self) -> bool:
        line = self.cursor.line
        column = self.cursor.column
        if line == 0 and column == 0:
            return False
        self._begin_edit()
        if column > 0:
            current = self.lines[line]
            self.lines[line] = current[: column - 1] + current[column:]
            self.cursor = Cursor(line, column - 1)
        else:
            previous = self.lines[line - 1]
            self.lines[line - 1 : line + 1] = [previous + self.lines[line]]
            self.cursor = Cursor(line - 1, len(previous))
        self._preferred_column = None
        self._finish_edit()
        return True

    def delete_forward(self) -> bool:
        line = self.cursor.line
        column = self.cursor.column
        current = self.lines[line]
        if line == len(self.lines) - 1 and column == len(current):
            return False
        self._begin_edit()
        if column < len(current):
            self.lines[line] = current[:column] + current[column + 1 :]
        else:
            self.lines[line : line + 2] = [current + self.lines[line + 1]]
        self._preferred_column = None
        self._finish_edit()
        return True

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        snapshot = self._undo_stack.pop()
        self.lines = list(snapshot.lines) or [""]
        self.cursor = snapshot.cursor
        self.viewport = snapshot.viewport
        self._preferred_column = snapshot.preferred_column
        self._finish_edit()
        return True

    def validate(self) -> tuple[EditorDiagnostic, ...]:
        if self.validator is None:
            self.diagnostics = []
            return ()
        try:
            raw = self.validator(self.path, self.text)
            values = [] if raw is None else list(raw)
            self.diagnostics = [_normalize_diagnostic(item, default_path=self.path) for item in values]
        except Exception as exc:
            self.diagnostics = [
                EditorDiagnostic(
                    message=f"Validator failed: {type(exc).__name__}: {exc}",
                    path=str(self.path),
                    line=1,
                    column=1,
                    severity="error",
                    code="validator_error",
                )
            ]
        return tuple(self.diagnostics)

    def goto_diagnostic(self, diagnostic: int | EditorDiagnostic = 0) -> Cursor:
        item = self.diagnostics[diagnostic] if isinstance(diagnostic, int) else diagnostic
        return self.set_cursor(max(0, item.line - 1), max(0, item.column - 1))

    def _matches_original(self, snapshot: _DiskSnapshot | None) -> bool:
        if self.original_stat is None:
            return snapshot is None
        return (
            snapshot is not None
            and snapshot.digest == self.original_digest
            and snapshot.stat == self.original_stat
        )

    def _current_disk_snapshot(self) -> _DiskSnapshot | None:
        try:
            return _read_disk_snapshot(self.path)
        except FileNotFoundError:
            return None

    def check_external_conflict(self) -> bool:
        _root, resolved = resolve_project_file(self.project_root, self.path)
        if resolved != self.path:
            self.external_conflict = True
            return True
        try:
            snapshot = self._current_disk_snapshot()
        except ExternalFileConflictError:
            self.external_conflict = True
            return True
        self.external_conflict = not self._matches_original(snapshot)
        return self.external_conflict

    def _assert_no_external_conflict(self) -> None:
        if self.check_external_conflict():
            raise ExternalFileConflictError(
                f"Authoring file changed outside the editor; reload or cancel before saving: {self.path}"
            )

    def save(self) -> SaveResult:
        """Atomically save unless the opened disk baseline changed externally."""

        _root, resolved = resolve_project_file(self.project_root, self.path)
        if resolved != self.path:
            self.external_conflict = True
            raise ExternalFileConflictError(f"Authoring file path changed outside the project: {self.path}")
        self._assert_no_external_conflict()
        data = self.text.encode("utf-8")
        parent = self.path.parent
        fd, temporary_name = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=parent)
        temporary = Path(temporary_name)
        try:
            if self.original_stat is not None:
                os.fchmod(fd, stat_module.S_IMODE(self.original_stat.mode))
            with os.fdopen(fd, "wb", closefd=True) as handle:
                fd = -1
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            # A second comparison narrows the window in which an external editor
            # could change the file while our temporary file is being written.
            self._assert_no_external_conflict()
            os.replace(temporary, self.path)
            try:
                directory_fd = os.open(parent, os.O_RDONLY)
            except OSError:
                directory_fd = -1
            if directory_fd >= 0:
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            if fd >= 0:
                os.close(fd)
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

        snapshot = _read_disk_snapshot(self.path)
        saved_text = _decode_authoring_bytes(snapshot.data, self.path)
        self.original_digest = snapshot.digest
        self.original_stat = snapshot.stat
        self._original_text = saved_text
        self.dirty = self.text != self._original_text
        self.external_conflict = False
        self._undo_stack.clear()
        diagnostics = self.validate()
        return SaveResult(path=self.path, digest=snapshot.digest, stat=snapshot.stat, diagnostics=diagnostics)

    def reload(self) -> tuple[EditorDiagnostic, ...]:
        """Discard the buffer and adopt the latest external file as baseline."""

        _root, resolved = resolve_project_file(self.project_root, self.path)
        if resolved != self.path:
            raise EditorPathError(f"Authoring file path no longer resolves to the opened file: {self.path}")
        snapshot = _read_disk_snapshot(self.path)
        text = _decode_authoring_bytes(snapshot.data, self.path)
        self.lines, self.newline = _split_lines(text)
        self.original_digest = snapshot.digest
        self.original_stat = snapshot.stat
        self._original_text = self.newline.join(self.lines)
        self.cursor = Cursor()
        self.viewport = Viewport()
        self.dirty = False
        self.external_conflict = False
        self._undo_stack.clear()
        self._preferred_column = None
        self._clamp_state()
        return self.validate()

    def cancel(self) -> bool:
        """Cancel a pending save/close decision without changing buffer or disk.

        This intentionally leaves an external-conflict flag latched.  A later
        save must still fail until the caller explicitly reloads the file.
        """

        return False


# A concise alias for callers that prefer a state-oriented name.
AgentEditorState = AgentEditor


__all__ = [
    "ALLOWED_AUTHORING_SUFFIXES",
    "AgentEditor",
    "AgentEditorError",
    "AgentEditorState",
    "Cursor",
    "EditorDiagnostic",
    "EditorPathError",
    "ExternalFileConflictError",
    "FileStatSnapshot",
    "SaveResult",
    "UnsupportedAuthoringFileError",
    "Validator",
    "Viewport",
    "content_digest",
    "is_allowed_authoring_path",
    "movement_target",
    "resolve_project_file",
]
