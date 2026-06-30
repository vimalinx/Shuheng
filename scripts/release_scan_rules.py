"""Shared release leak scan rules for source and distribution artifacts."""
from __future__ import annotations

import re
from re import Pattern


SECRET_PATTERNS: tuple[Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)

LOCAL_PATH_PATTERNS: tuple[Pattern[str], ...] = (
    re.compile(r"/home/[A-Za-z0-9._-]+/"),
    re.compile(r"/Users/[A-Za-z0-9._-]+/"),
)


def has_secret_like_literal(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def has_local_absolute_path(text: str) -> bool:
    return any(pattern.search(text) for pattern in LOCAL_PATH_PATTERNS)


def text_release_leak_errors(text: str, path: str, *, location: str) -> list[str]:
    errors: list[str] = []
    if has_secret_like_literal(text):
        errors.append(f"secret-like literal found in {location}: {path}")
    if has_local_absolute_path(text):
        errors.append(f"local absolute path found in {location}: {path}")
    return errors
