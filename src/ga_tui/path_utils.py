"""Pure filesystem path safety helpers."""
from __future__ import annotations

import os


def normalized_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path or ""))


def path_is_within(path: str, root: str) -> bool:
    try:
        real_root = os.path.realpath(normalized_path(root))
        real_path = os.path.realpath(normalized_path(path))
        return os.path.commonpath([real_root, real_path]) == real_root
    except Exception:
        return False


def is_normal_session_log_path(path: str, *, model_responses_dir: str, session_trash_dir: str) -> bool:
    path = normalized_path(path)
    base = os.path.basename(path)
    return (
        path_is_within(path, model_responses_dir)
        and not path_is_within(path, session_trash_dir)
        and base.startswith("model_responses")
        and base.endswith(".txt")
    )
