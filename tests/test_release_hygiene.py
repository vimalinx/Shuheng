"""Tests for release hygiene guards."""
from __future__ import annotations

from scripts import check_release_hygiene as hygiene


def test_wheel_smoke_release_mode_rejects_no_deps(monkeypatch) -> None:
    command = f"PYTHONDONTWRITEBYTECODE=1 python {hygiene.RELEASE_WHEEL_SMOKE_FRAGMENT}"
    texts = {
        "README.md": command,
        "README.en.md": f"{command} --no-deps",
        ".github/workflows/ci.yml": command,
    }

    monkeypatch.setattr(hygiene, "read_text", lambda path: texts[path])

    errors: list[str] = []
    hygiene.check_wheel_smoke_release_mode(errors)

    assert any("README.en.md release wheel smoke must not use --no-deps" in error for error in errors)
