"""Security contracts for Shuheng-owned model configuration state."""
from __future__ import annotations

import stat
from pathlib import Path

from shuheng import app as app_module


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def isolate_model_config_paths(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    source_root = tmp_path / "source"
    private_home = tmp_path / "private-home"
    (source_root / "src" / "shuheng").mkdir(parents=True)
    (source_root / "pyproject.toml").write_text("[project]\nname = 'shuheng'\n", encoding="utf-8")
    (source_root / "src" / "shuheng" / "app.py").write_text("# checkout marker\n", encoding="utf-8")
    monkeypatch.setattr(app_module, "ROOT_DIR", str(source_root))
    monkeypatch.setattr(app_module, "APP_ROOT_DIR", str(source_root))
    monkeypatch.setattr(app_module, "SHUHENG_HOME", str(private_home))
    return source_root, private_home


def test_source_root_model_config_migrates_once_into_private_state(monkeypatch, tmp_path: Path) -> None:
    source_root, private_home = isolate_model_config_paths(monkeypatch, tmp_path)
    source = source_root / "mykey.py"
    backup = source_root / "mykey.py.bak-20260710-120000"
    source.write_text(
        "mixin_config = {'llm_nos': ['primary']}\n"
        "native_oai_config = {'name': 'primary', 'apikey': 'secret-value', "
        "'apibase': 'https://example.test/v1', 'model': 'test-model'}\n",
        encoding="utf-8",
    )
    backup.write_text("backup-secret\n", encoding="utf-8")

    ok, error = app_module.migrate_source_mykey_once()

    canonical = private_home / "config" / "mykey.py"
    migrated_backup = private_home / "config" / backup.name
    marker = private_home / "config" / ".source-mykey-migration-v1"
    assert ok is True and error == ""
    assert app_module.mykey_path() == str(canonical)
    assert canonical.exists() and migrated_backup.exists() and marker.exists()
    assert not source.exists() and not backup.exists()
    assert mode(private_home) == 0o700
    assert mode(private_home / "config") == 0o700
    assert mode(canonical) == mode(migrated_backup) == mode(marker) == 0o600

    assignments, load_error = app_module.load_mykey_assignments()
    assert load_error == ""
    assert dict(assignments)["native_oai_config"]["apikey"] == "secret-value"


def test_external_runtime_model_config_is_copied_without_modifying_checkout(monkeypatch, tmp_path: Path) -> None:
    external_root = tmp_path / "external-runtime"
    app_root = tmp_path / "shuheng-source"
    private_home = tmp_path / "private-home"
    external_root.mkdir()
    app_root.mkdir()
    external_config = external_root / "mykey.py"
    external_backup = external_root / "mykey.py.bak-20260710-120000"
    external_config.write_text(
        "mixin_config = {'llm_nos': ['external']}\n"
        "native_oai_config = {'name': 'external', 'apikey': 'external-secret', "
        "'apibase': 'https://example.test/v1', 'model': 'external-model'}\n",
        encoding="utf-8",
    )
    external_backup.write_text("external-backup-secret\n", encoding="utf-8")
    original_config = external_config.read_bytes()
    original_backup = external_backup.read_bytes()
    monkeypatch.setattr(app_module, "ROOT_DIR", str(external_root))
    monkeypatch.setattr(app_module, "APP_ROOT_DIR", str(app_root))
    monkeypatch.setattr(app_module, "SHUHENG_HOME", str(private_home))

    ok, error = app_module.migrate_source_mykey_once()

    canonical = private_home / "config" / "mykey.py"
    migrated_backup = private_home / "config" / external_backup.name
    assert ok is True and error == ""
    assert canonical.read_bytes() == original_config
    assert migrated_backup.read_bytes() == original_backup
    assert mode(canonical) == mode(migrated_backup) == 0o600
    assert external_config.read_bytes() == original_config
    assert external_backup.read_bytes() == original_backup


def test_installed_package_root_is_not_treated_as_a_source_checkout(monkeypatch, tmp_path: Path) -> None:
    installed_root = tmp_path / "venv" / "lib" / "python3.13"
    private_home = tmp_path / "private-home"
    installed_root.mkdir(parents=True)
    unrelated = installed_root / "mykey.py"
    unrelated.write_text("unrelated = True\n", encoding="utf-8")
    monkeypatch.setattr(app_module, "ROOT_DIR", str(installed_root))
    monkeypatch.setattr(app_module, "APP_ROOT_DIR", str(installed_root))
    monkeypatch.setattr(app_module, "SHUHENG_HOME", str(private_home))

    ok, error = app_module.migrate_source_mykey_once()

    assert ok is True and error == ""
    assert unrelated.read_text(encoding="utf-8") == "unrelated = True\n"
    assert not (private_home / "config" / "mykey.py").exists()


def test_saved_model_config_and_backups_are_private(monkeypatch, tmp_path: Path) -> None:
    source_root, private_home = isolate_model_config_paths(monkeypatch, tmp_path)
    entry = app_module.LLMConfigEntry(
        "native_oai_config",
        "native_oai",
        {
            "name": "primary",
            "apikey": "private-api-key",
            "apibase": "https://example.test/v1",
            "model": "test-model",
        },
    )

    first_ok, first_message = app_module.save_llm_config_entries(
        [entry],
        {"llm_nos": ["primary"]},
        [],
    )
    second_ok, second_message = app_module.save_llm_config_entries(
        [entry],
        {"llm_nos": ["primary"]},
        [],
    )

    canonical = private_home / "config" / "mykey.py"
    backups = list((private_home / "config").glob("mykey.py.bak-*"))
    assert first_ok is second_ok is True
    assert first_message == second_message == "模型配置已安全保存。"
    assert canonical.exists() and len(backups) == 1
    assert mode(canonical) == 0o600
    assert all(mode(path) == 0o600 for path in backups)
    assert not (source_root / "mykey.py").exists()
    assert not list(source_root.glob("mykey.py*"))
    assert not list((private_home / "config").glob("*.tmp-*"))


def test_model_config_parse_errors_do_not_disclose_secret_or_paths(monkeypatch, tmp_path: Path) -> None:
    source_root, private_home = isolate_model_config_paths(monkeypatch, tmp_path)
    secret = "TOP-SECRET-SHOULD-NOT-LEAK"
    (source_root / "mykey.py").write_text(
        f"native_oai_config = {{'apikey': '{secret}'\n",
        encoding="utf-8",
    )

    assignments, error = app_module.load_mykey_assignments()

    assert assignments == []
    assert error == "模型配置读取失败: SyntaxError"
    assert secret not in error
    assert str(source_root) not in error
    assert str(private_home) not in error
