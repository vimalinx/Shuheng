"""Unit tests for the distribution smoke helper."""
from __future__ import annotations

import os
from pathlib import Path

from scripts import wheel_smoke


def test_latest_sdist_selects_newest_artifact(tmp_path: Path) -> None:
    old = tmp_path / "shuheng-0.1.0.tar.gz"
    new = tmp_path / "shuheng-0.2.0.tar.gz"
    old.write_text("old", encoding="utf-8")
    new.write_text("new", encoding="utf-8")
    os.utime(old, (1000, 1000))
    os.utime(new, (2000, 2000))

    assert wheel_smoke.latest_sdist(tmp_path) == new


def test_distribution_smoke_combines_wheel_and_sdist(monkeypatch, tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.1.0-py3-none-any.whl"
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    wheel.write_text("wheel", encoding="utf-8")
    sdist.write_text("sdist", encoding="utf-8")

    def fake_wheel_smoke(path: Path, *, no_deps: bool = False) -> dict[str, object]:
        return {
            "ok": True,
            "artifact": path.name,
            "artifact_kind": "wheel",
            "install_mode": "no_deps" if no_deps else "with_dependencies",
            "checks": [{"command": "wheel check", "returncode": 0}],
        }

    def fake_sdist_smoke(path: Path, *, no_deps: bool = False) -> dict[str, object]:
        return {
            "ok": True,
            "artifact": path.name,
            "artifact_kind": "sdist",
            "install_mode": "no_deps" if no_deps else "with_dependencies",
            "checks": [{"command": "sdist check", "returncode": 0}],
        }

    monkeypatch.setattr(wheel_smoke, "run_wheel_smoke", fake_wheel_smoke)
    monkeypatch.setattr(wheel_smoke, "run_sdist_smoke", fake_sdist_smoke)

    report = wheel_smoke.run_distribution_smoke(wheel, sdist)

    assert report["ok"] is True
    assert report["install_mode"] == "with_dependencies"
    assert [artifact["artifact_kind"] for artifact in report["artifacts"]] == ["wheel", "sdist"]
    assert [check["artifact_kind"] for check in report["checks"]] == ["wheel", "sdist"]
