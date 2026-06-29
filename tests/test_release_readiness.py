"""Tests for release-readiness helper metadata."""
from __future__ import annotations

from ga_tui.release_readiness import release_readiness_report


def test_release_readiness_exposes_distribution_smoke_contract() -> None:
    report = release_readiness_report(has_license=True, has_ci=True, has_security_policy=True)

    distribution_smoke = report["distribution_smoke"]

    assert distribution_smoke["schema_version"] == "shuheng.distribution_smoke.v1"
    assert distribution_smoke["artifacts"] == ["wheel", "sdist"]
    assert distribution_smoke["install_mode"] == "with_dependencies"
    assert distribution_smoke["command"] == "python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist"
    assert "shuheng-check" in distribution_smoke["public_console_scripts"]
    assert "shuheng-check against isolated GenericAgent stub" in distribution_smoke["checks"]
    assert {"--no-deps", "--wheel-only"} <= set(distribution_smoke["debug_options_not_release_gates"])
    assert "git diff --check" in report["verification_commands"]
