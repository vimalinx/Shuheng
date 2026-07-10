"""Shared JSONL ledger storage helpers for the Shuheng control plane.

This module owns low-level append/read/cache behavior for task, approval,
artifact, trace, recovery, and scheduler ledgers. UI modules should keep
domain-specific projection logic, but not reimplement JSONL storage mechanics.
"""
from __future__ import annotations

import copy
import fcntl
import json
import os
import threading
from typing import Any, Callable, TypeVar


ParseErrorHandler = Callable[[Exception, str], None]
T = TypeVar("T")

LATEST_RECORDS_CACHE_LIMIT = 64

_JSONL_APPEND_LOCKS_GUARD = threading.Lock()
_JSONL_APPEND_LOCKS: dict[str, threading.Lock] = {}
_LATEST_RECORDS_CACHE_LOCK = threading.Lock()
_LATEST_RECORDS_CACHE: dict[tuple[str, str], tuple[tuple[int, int], dict[str, dict[str, Any]]]] = {}


def _jsonl_append_lock(path: str) -> threading.Lock:
    """Return a process-internal lock keyed by normalized path."""

    key = os.path.normpath(path)
    lock = _JSONL_APPEND_LOCKS.get(key)
    if lock is not None:
        return lock
    with _JSONL_APPEND_LOCKS_GUARD:
        lock = _JSONL_APPEND_LOCKS.setdefault(key, threading.Lock())
    return lock


def invalidate_jsonl_cache(path: str) -> None:
    """Drop latest-record cache entries for one JSONL ledger path."""

    normalized = os.path.normpath(path)
    with _LATEST_RECORDS_CACHE_LOCK:
        stale_keys = [key for key in _LATEST_RECORDS_CACHE if key[0] == normalized]
        for cache_key in stale_keys:
            _LATEST_RECORDS_CACHE.pop(cache_key, None)


def clear_jsonl_caches() -> None:
    """Clear process-local JSONL caches. Primarily useful for tests."""

    with _LATEST_RECORDS_CACHE_LOCK:
        _LATEST_RECORDS_CACHE.clear()


def append_jsonl(path: str, payload: dict[str, Any]) -> None:
    """Append one JSONL record under process-internal and cross-process locks."""

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
    with _jsonl_append_lock(path):
        with open(path, "a", encoding="utf-8") as fh:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            except (OSError, ValueError):
                # Some platforms or file descriptors may not support flock; the
                # process-local lock still protects co-located writer threads.
                pass
            try:
                fh.write(line)
                fh.flush()
            finally:
                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                except (OSError, ValueError):
                    pass
    invalidate_jsonl_cache(path)


def update_json_dict_file(
    path: str,
    updater: Callable[[dict[str, Any]], tuple[dict[str, Any], T]],
    *,
    write_when_unchanged: bool = True,
    on_failure: Callable[[], None] | None = None,
) -> T:
    """Atomically update a JSON object file under process and flock locks.

    Callers that perform read-mostly transactions may skip the replace when
    their updater returns data equal to the current JSON object.
    """

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    lock_path = f"{path}.lock"
    lock_parent = os.path.dirname(lock_path)
    if lock_parent:
        os.makedirs(lock_parent, exist_ok=True)

    temp_path = ""
    with _jsonl_append_lock(lock_path):
        with open(lock_path, "a+", encoding="utf-8") as lock_fh:
            try:
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
            except (OSError, ValueError):
                pass
            try:
                try:
                    with open(path, encoding="utf-8") as fh:
                        raw = json.load(fh)
                except Exception:
                    raw = {}
                current = dict(raw) if isinstance(raw, dict) else {}
                comparison_snapshot = copy.deepcopy(current) if not write_when_unchanged else None
                next_data, result = updater(current)
                if not isinstance(next_data, dict):
                    raise TypeError("JSON dict updater must return a dict payload")
                if not write_when_unchanged and next_data == comparison_snapshot:
                    return result
                temp_path = f"{path}.tmp.{os.getpid()}.{threading.get_ident()}"
                with open(temp_path, "w", encoding="utf-8") as out:
                    json.dump(next_data, out, ensure_ascii=False, indent=2, sort_keys=True)
                    out.write("\n")
                    out.flush()
                    try:
                        os.fsync(out.fileno())
                    except OSError:
                        pass
                os.replace(temp_path, path)
                temp_path = ""
                return result
            except BaseException as exc:
                if on_failure is not None:
                    try:
                        on_failure()
                    except BaseException as rollback_exc:
                        detail = f"rollback failed: {type(rollback_exc).__name__}: {rollback_exc}"
                        add_note = getattr(exc, "add_note", None)
                        if callable(add_note):
                            add_note(detail)
                        else:
                            try:
                                setattr(exc, "_shuheng_rollback_error", detail)
                            except Exception:
                                pass
                raise
            finally:
                if temp_path:
                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass
                try:
                    fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
                except (OSError, ValueError):
                    pass


def read_jsonl(path: str, limit: int = 0, *, on_parse_error: ParseErrorHandler | None = None) -> list[dict[str, Any]]:
    """Read dict rows from a JSONL file, skipping corrupt or non-dict lines."""

    rows: list[dict[str, Any]] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except (json.JSONDecodeError, ValueError) as exc:
                    if on_parse_error is not None:
                        on_parse_error(exc, f"{path}:{lineno}")
                    continue
                if isinstance(item, dict):
                    rows.append(item)
    except OSError:
        return []
    if limit and len(rows) > limit:
        return rows[-limit:]
    return rows


def jsonl_file_signature(path: str) -> tuple[int, int]:
    """Return an mtime/size signature for JSONL cache invalidation."""

    try:
        stat = os.stat(path)
    except OSError:
        return (0, 0)
    return (int(stat.st_mtime_ns), int(stat.st_size))


def latest_records_by_id(path: str, key: str) -> dict[str, dict[str, Any]]:
    """Return the latest row for each non-empty id field in a JSONL ledger."""

    normalized = os.path.normpath(path)
    cache_key = (normalized, key)
    signature = jsonl_file_signature(normalized)
    with _LATEST_RECORDS_CACHE_LOCK:
        cached = _LATEST_RECORDS_CACHE.get(cache_key)
        if cached is not None and cached[0] == signature:
            return {row_id: dict(row) for row_id, row in cached[1].items()}

    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(normalized):
        row_id = str(row.get(key) or "")
        if row_id:
            latest[row_id] = row

    with _LATEST_RECORDS_CACHE_LOCK:
        _LATEST_RECORDS_CACHE[cache_key] = (signature, {row_id: dict(row) for row_id, row in latest.items()})
        while len(_LATEST_RECORDS_CACHE) > LATEST_RECORDS_CACHE_LIMIT:
            _LATEST_RECORDS_CACHE.pop(next(iter(_LATEST_RECORDS_CACHE)))
    return {row_id: dict(row) for row_id, row in latest.items()}


def rows_matching(path: str, key: str, value: str) -> list[dict[str, Any]]:
    """Return rows whose stringified field exactly matches value."""

    expected = str(value or "")
    return [row for row in read_jsonl(path) if str(row.get(key) or "") == expected]
