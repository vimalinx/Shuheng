"""Shared JSONL ledger storage helpers for the Shuheng control plane.

This module owns low-level append/read/cache behavior for task, approval,
artifact, trace, recovery, and scheduler ledgers. UI modules should keep
domain-specific projection logic, but not reimplement JSONL storage mechanics.
"""
from __future__ import annotations

import fcntl
import json
import os
import threading
from typing import Any, Callable


ParseErrorHandler = Callable[[Exception, str], None]

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
