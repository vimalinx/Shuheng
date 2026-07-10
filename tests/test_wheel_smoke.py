"""Unit tests for the distribution smoke helper."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import tarfile
import zipfile

from scripts import wheel_smoke


def console_scripts_text(missing_script: str = "") -> str:
    scripts = [
        script
        for script in wheel_smoke.PUBLIC_CONSOLE_SCRIPTS
        if script != missing_script
    ]
    return "\n".join(["[console_scripts]", *[f"{script} = shuheng.__main__:main" for script in scripts], ""])


def sdist_fixture_content(member: str, *, missing_script: str = "", sources_members: list[str] | None = None) -> bytes:
    if member in {"PKG-INFO", "src/shuheng.egg-info/PKG-INFO"}:
        return b"Metadata-Version: 2.4\nName: shuheng\nVersion: 0.1.0\n"
    if member == "src/shuheng.egg-info/entry_points.txt":
        return console_scripts_text(missing_script).encode()
    if member == "src/shuheng.egg-info/top_level.txt":
        return b"shuheng\n"
    if member == wheel_smoke.SDIST_SOURCES_MEMBER:
        rows = sources_members or []
        return ("\n".join(rows) + "\n").encode()
    return b"fixture\n"


def write_sdist_fixture(
    path: Path,
    members: list[str],
    *,
    missing_script: str = "",
    sources_members: list[str] | None = None,
) -> None:
    if sources_members is None:
        generated = set(wheel_smoke.SDIST_GENERATED_MEMBERS_NOT_IN_SOURCES)
        sources_members = [member for member in members if member not in generated]
    with tarfile.open(path, "w:gz") as archive:
        for member in members:
            data = sdist_fixture_content(member, missing_script=missing_script, sources_members=sources_members)
            info = tarfile.TarInfo(f"shuheng-0.1.0/{member}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def wheel_entry_points_text(missing_script: str = "") -> str:
    return console_scripts_text(missing_script)


def wheel_fixture_content(member: str, *, missing_script: str = "") -> bytes:
    if member.endswith("/METADATA"):
        return b"Name: shuheng\nVersion: 0.1.0\n"
    if member.endswith("/entry_points.txt"):
        return wheel_entry_points_text(missing_script).encode()
    return b"fixture\n"


def write_wheel_fixture(
    path: Path,
    members: list[str],
    *,
    missing_script: str = "",
    missing_record_member: str = "",
    corrupt_record_member: str = "",
    corrupt_size_member: str = "",
) -> None:
    content_by_member = {
        member: wheel_fixture_content(member, missing_script=missing_script)
        for member in members
        if not member.endswith("/RECORD")
    }
    record_member = next((member for member in members if member.endswith("/RECORD")), "")
    if record_member:
        rows = []
        for member, data in content_by_member.items():
            if member == missing_record_member:
                continue
            hash_field = "sha256=invalid" if member == corrupt_record_member else wheel_smoke.wheel_record_hash(data)
            size_field = str(len(data) + 1) if member == corrupt_size_member else str(len(data))
            rows.append(f"{member},{hash_field},{size_field}")
        if record_member != missing_record_member:
            rows.append(f"{record_member},,")
        content_by_member[record_member] = ("\n".join(rows) + "\n").encode()

    with zipfile.ZipFile(path, "w") as archive:
        for member in members:
            archive.writestr(member, content_by_member.get(member, b"fixture\n"))


def expected_wheel_members() -> list[str]:
    dist_info_dir = "shuheng-0.1.0.dist-info"
    return [
        *wheel_smoke.WHEEL_REQUIRED_PACKAGE_MEMBERS,
        *wheel_smoke.wheel_required_data_members(dist_info_dir),
        *[f"{dist_info_dir}/{member}" for member in wheel_smoke.WHEEL_REQUIRED_DIST_INFO_MEMBERS],
    ]


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


def test_sdist_archive_contract_accepts_expected_public_members(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    write_sdist_fixture(sdist, list(wheel_smoke.SDIST_REQUIRED_MEMBERS))

    check = wheel_smoke.sdist_archive_contract_check(sdist)

    assert check["command"] == "sdist archive public/private member contract"
    assert check["returncode"] == 0


def test_sdist_archive_contract_rejects_missing_public_member(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    members = [member for member in wheel_smoke.SDIST_REQUIRED_MEMBERS if member != "SECURITY.md"]
    write_sdist_fixture(sdist, members)

    try:
        wheel_smoke.sdist_archive_contract_check(sdist)
    except ValueError as exc:
        assert "missing required members: SECURITY.md" in str(exc)
    else:
        raise AssertionError("missing sdist member should fail")


def test_sdist_archive_contract_rejects_private_member(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    members = [*wheel_smoke.SDIST_REQUIRED_MEMBERS, "config/mcporter.json"]
    write_sdist_fixture(sdist, members)

    try:
        wheel_smoke.sdist_archive_contract_check(sdist)
    except ValueError as exc:
        assert "forbidden members present: config/mcporter.json" in str(exc)
    else:
        raise AssertionError("private sdist member should fail")


def test_sdist_archive_contract_rejects_agent_metadata_and_credential_shims(tmp_path: Path) -> None:
    private_members = (
        ".agents/skills/local/SKILL.md",
        ".claude/settings.local.json",
        "mykey.py",
        "mykey.py.bak-20260710T120000",
        "mykey.py.tmp.123",
        ".mykey.py.123.tmp",
    )
    for index, private_member in enumerate(private_members):
        sdist = tmp_path / f"shuheng-private-{index}.tar.gz"
        write_sdist_fixture(sdist, [*wheel_smoke.SDIST_REQUIRED_MEMBERS, private_member])

        try:
            wheel_smoke.sdist_archive_contract_check(sdist)
        except ValueError as exc:
            assert f"forbidden members present: {private_member}" in str(exc)
        else:
            raise AssertionError(f"private sdist member should fail: {private_member}")


def test_sdist_archive_contract_rejects_pi_sidecar_node_modules(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    dependency_member = "integrations/pi-native-sidecar/node_modules/dependency/package.json"
    members = [*wheel_smoke.SDIST_REQUIRED_MEMBERS, dependency_member]
    write_sdist_fixture(sdist, members)

    try:
        wheel_smoke.sdist_archive_contract_check(sdist)
    except ValueError as exc:
        assert f"forbidden members present: {dependency_member}" in str(exc)
    else:
        raise AssertionError("sidecar node_modules should not ship in the sdist")


def test_sdist_metadata_contract_accepts_package_metadata(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    write_sdist_fixture(sdist, list(wheel_smoke.SDIST_REQUIRED_MEMBERS))

    check = wheel_smoke.sdist_metadata_contract_check(sdist)

    assert check["command"] == "sdist metadata/entry points contract"
    assert check["returncode"] == 0
    assert check["console_scripts"] == len(wheel_smoke.PUBLIC_CONSOLE_SCRIPTS)


def test_sdist_metadata_contract_rejects_missing_pkg_info(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    members = [member for member in wheel_smoke.SDIST_REQUIRED_MEMBERS if member != "PKG-INFO"]
    write_sdist_fixture(sdist, members)

    try:
        wheel_smoke.sdist_metadata_contract_check(sdist)
    except ValueError as exc:
        assert "missing required members: PKG-INFO" in str(exc)
    else:
        raise AssertionError("missing sdist PKG-INFO should fail")


def test_sdist_metadata_contract_rejects_missing_console_script_metadata(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    write_sdist_fixture(sdist, list(wheel_smoke.SDIST_REQUIRED_MEMBERS), missing_script="shuheng-check")

    try:
        wheel_smoke.sdist_metadata_contract_check(sdist)
    except ValueError as exc:
        assert "entry_points.txt missing console scripts: shuheng-check" in str(exc)
    else:
        raise AssertionError("missing sdist console script metadata should fail")


def test_sdist_sources_integrity_accepts_manifest(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    write_sdist_fixture(sdist, list(wheel_smoke.SDIST_REQUIRED_MEMBERS))

    check = wheel_smoke.sdist_sources_integrity_check(sdist)

    assert check["command"] == "sdist SOURCES manifest integrity"
    assert check["returncode"] == 0
    assert "PKG-INFO" in check["generated_members_not_required"]


def test_sdist_sources_integrity_rejects_missing_sources_member(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    members = [member for member in wheel_smoke.SDIST_REQUIRED_MEMBERS if member != wheel_smoke.SDIST_SOURCES_MEMBER]
    write_sdist_fixture(sdist, members)

    try:
        wheel_smoke.sdist_sources_integrity_check(sdist)
    except ValueError as exc:
        assert f"missing {wheel_smoke.SDIST_SOURCES_MEMBER}" in str(exc)
    else:
        raise AssertionError("missing sdist SOURCES.txt should fail")


def test_sdist_sources_integrity_rejects_missing_archive_member_row(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    members = list(wheel_smoke.SDIST_REQUIRED_MEMBERS)
    generated = set(wheel_smoke.SDIST_GENERATED_MEMBERS_NOT_IN_SOURCES)
    sources_members = [member for member in members if member not in generated and member != "README.md"]
    write_sdist_fixture(sdist, members, sources_members=sources_members)

    try:
        wheel_smoke.sdist_sources_integrity_check(sdist)
    except ValueError as exc:
        assert "SOURCES missing rows for archive members: README.md" in str(exc)
    else:
        raise AssertionError("sdist SOURCES missing member row should fail")


def test_sdist_sources_integrity_rejects_missing_archive_member_from_sources(tmp_path: Path) -> None:
    sdist = tmp_path / "shuheng-0.1.0.tar.gz"
    members = list(wheel_smoke.SDIST_REQUIRED_MEMBERS)
    generated = set(wheel_smoke.SDIST_GENERATED_MEMBERS_NOT_IN_SOURCES)
    sources_members = [member for member in members if member not in generated]
    sources_members.append("docs/not-packaged.md")
    write_sdist_fixture(sdist, members, sources_members=sources_members)

    try:
        wheel_smoke.sdist_sources_integrity_check(sdist)
    except ValueError as exc:
        assert "SOURCES rows for missing archive members: docs/not-packaged.md" in str(exc)
    else:
        raise AssertionError("sdist SOURCES extra member row should fail")


def test_artifact_content_leak_scan_rejects_secret_like_literal() -> None:
    secret_like = "sk-" + "artifactleak12345678901234567890"

    try:
        wheel_smoke.check_archive_text_has_no_release_leaks(
            [("tests/test_leaky_fixture.py", f'TOKEN = "{secret_like}"\n'.encode())],
            artifact_kind="sdist",
        )
    except ValueError as exc:
        assert "secret-like literal found in artifact member: tests/test_leaky_fixture.py" in str(exc)
    else:
        raise AssertionError("secret-like artifact content should fail")


def test_artifact_content_leak_scan_rejects_local_absolute_path() -> None:
    local_path = "/home/" + "tester/shuheng"
    try:
        wheel_smoke.check_archive_text_has_no_release_leaks(
            [("shuheng/generated.py", f'HOME = "{local_path}"\n'.encode())],
            artifact_kind="wheel",
        )
    except ValueError as exc:
        assert "local absolute path found in artifact member: shuheng/generated.py" in str(exc)
    else:
        raise AssertionError("local absolute artifact content should fail")


def test_artifact_retired_naming_scan_rejects_old_console_name() -> None:
    retired_console = "ga" + "-tui"
    try:
        wheel_smoke.check_archive_text_has_no_retired_naming(
            [("shuheng-0.1.0.dist-info/entry_points.txt", f"{retired_console} = shuheng.__main__:main\n".encode())],
            artifact_kind="wheel",
        )
    except ValueError as exc:
        assert "retired pre-Shuheng naming found in artifact member" in str(exc)
    else:
        raise AssertionError("retired artifact naming should fail")


def test_artifact_retired_naming_scan_rejects_old_package_name() -> None:
    retired_package = "ga" + "_tui"
    try:
        wheel_smoke.check_archive_text_has_no_retired_naming(
            [("PKG-INFO", f"Requires-Dist: {retired_package}\n".encode())],
            artifact_kind="sdist",
        )
    except ValueError as exc:
        assert "retired pre-Shuheng naming found in artifact member" in str(exc)
    else:
        raise AssertionError("retired artifact package naming should fail")


def test_wheel_archive_contract_accepts_metadata_and_public_members(tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.1.0-py3-none-any.whl"
    write_wheel_fixture(wheel, expected_wheel_members())

    check = wheel_smoke.wheel_archive_contract_check(wheel)

    assert check["command"] == "wheel archive metadata/private member contract"
    assert check["returncode"] == 0
    assert check["console_scripts"] == len(wheel_smoke.PUBLIC_CONSOLE_SCRIPTS)


def test_wheel_archive_contract_rejects_missing_metadata_member(tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.1.0-py3-none-any.whl"
    members = [member for member in expected_wheel_members() if not member.endswith("/METADATA")]
    write_wheel_fixture(wheel, members)

    try:
        wheel_smoke.wheel_archive_contract_check(wheel)
    except ValueError as exc:
        assert "missing required members: shuheng-0.1.0.dist-info/METADATA" in str(exc)
    else:
        raise AssertionError("missing wheel metadata should fail")


def test_wheel_archive_contract_rejects_private_member(tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.1.0-py3-none-any.whl"
    write_wheel_fixture(wheel, [*expected_wheel_members(), "memory/secret_vault/session.secret"])

    try:
        wheel_smoke.wheel_archive_contract_check(wheel)
    except ValueError as exc:
        assert "forbidden members present: memory/secret_vault/session.secret" in str(exc)
    else:
        raise AssertionError("private wheel member should fail")


def test_wheel_archive_contract_rejects_root_credential_shim(tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.1.0-py3-none-any.whl"
    write_wheel_fixture(wheel, [*expected_wheel_members(), "mykey.py.bak-20260710"])

    try:
        wheel_smoke.wheel_archive_contract_check(wheel)
    except ValueError as exc:
        assert "forbidden members present: mykey.py.bak-20260710" in str(exc)
    else:
        raise AssertionError("root credential shim should not ship in a wheel")


def test_wheel_archive_contract_rejects_missing_console_script_metadata(tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.1.0-py3-none-any.whl"
    write_wheel_fixture(wheel, expected_wheel_members(), missing_script="shuheng-check")

    try:
        wheel_smoke.wheel_archive_contract_check(wheel)
    except ValueError as exc:
        assert "entry_points.txt missing console scripts: shuheng-check" in str(exc)
    else:
        raise AssertionError("missing wheel console script metadata should fail")


def test_wheel_record_integrity_accepts_hashes_and_sizes(tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.1.0-py3-none-any.whl"
    write_wheel_fixture(wheel, expected_wheel_members())

    check = wheel_smoke.wheel_record_integrity_check(wheel)

    assert check["command"] == "wheel RECORD hash/size integrity"
    assert check["returncode"] == 0
    assert check["verified_members"] == len(expected_wheel_members()) - 1


def test_wheel_record_integrity_rejects_hash_mismatch(tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.1.0-py3-none-any.whl"
    write_wheel_fixture(wheel, expected_wheel_members(), corrupt_record_member="shuheng/app.py")

    try:
        wheel_smoke.wheel_record_integrity_check(wheel)
    except ValueError as exc:
        assert "RECORD hash mismatch: shuheng/app.py" in str(exc)
    else:
        raise AssertionError("wheel RECORD hash mismatch should fail")


def test_wheel_record_integrity_rejects_missing_member_row(tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.1.0-py3-none-any.whl"
    write_wheel_fixture(wheel, expected_wheel_members(), missing_record_member="shuheng/app.py")

    try:
        wheel_smoke.wheel_record_integrity_check(wheel)
    except ValueError as exc:
        assert "RECORD missing rows: shuheng/app.py" in str(exc)
    else:
        raise AssertionError("wheel RECORD missing row should fail")


def test_isolated_venv_uses_symlinks_on_posix(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    class FakeEnvBuilder:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

        def create(self, path: Path) -> None:
            captured["path"] = path

    monkeypatch.setattr(wheel_smoke.venv, "EnvBuilder", FakeEnvBuilder)

    wheel_smoke.create_isolated_venv(tmp_path / "venv")

    assert captured["with_pip"] is True
    assert captured["clear"] is True
    assert captured["symlinks"] is (wheel_smoke.os.name != "nt")
    assert captured["path"] == tmp_path / "venv"


def test_wheel_smoke_main_returns_nonzero_for_false_report(monkeypatch, tmp_path: Path, capsys) -> None:
    wheel = tmp_path / "shuheng-0.2.0a1-py3-none-any.whl"
    wheel.write_bytes(b"fixture")
    monkeypatch.setattr(
        wheel_smoke,
        "run_distribution_smoke",
        lambda *_args, **_kwargs: {"schema_version": "shuheng.wheel_smoke.v1", "ok": False, "checks": []},
    )

    assert wheel_smoke.main(["--wheel", str(wheel), "--wheel-only"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_upgrade_smoke_uses_normal_pip_upgrade_and_imports_agent_projects(monkeypatch, tmp_path: Path) -> None:
    wheel = tmp_path / "shuheng-0.2.0a1-py3-none-any.whl"
    wheel.write_bytes(b"fixture")
    commands: list[list[str]] = []

    class FakeEnvBuilder:
        def __init__(self, **_kwargs) -> None:
            pass

        def create(self, path: Path) -> None:
            python = path / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.write_text("fixture\n", encoding="utf-8")

    def fake_run(command: list[str], **_kwargs):
        commands.append(command)
        return None

    monkeypatch.setattr(wheel_smoke.venv, "EnvBuilder", FakeEnvBuilder)
    monkeypatch.setattr(wheel_smoke, "wheel_metadata_version", lambda _wheel: "0.2.0a1")
    monkeypatch.setattr(wheel_smoke, "run", fake_run)

    report = wheel_smoke.run_upgrade_smoke(wheel, previous_artifact="/tmp/shuheng-0.1.0.whl")

    pip_commands = [command for command in commands if command[1:4] == ["-m", "pip", "install"]]
    assert len(pip_commands) == 2
    assert pip_commands[0][-1] == "/tmp/shuheng-0.1.0.whl"
    assert pip_commands[1][-1] == str(wheel)
    assert all("--force-reinstall" not in command for command in pip_commands)
    assert any("import shuheng.agent_projects" in " ".join(command) for command in commands)
    assert report["previous_version"] == "0.1.0"
    assert report["current_version"] == "0.2.0a1"
