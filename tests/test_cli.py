from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from shuheng import cli


def test_cli_help_does_not_import_app(monkeypatch, capsys) -> None:
    sys.modules.pop("shuheng.app", None)

    result = None
    try:
        result = cli.main(["--help"])
    except SystemExit as exc:
        result = exc.code

    output = capsys.readouterr().out

    assert result == 0
    assert "Shuheng governed local-agent TUI" in output
    assert "install-agent-gateway-skill" in output
    assert "--serve-gateway" not in output
    assert "--gateway-daemon" not in output
    assert "shuheng.app" not in sys.modules


def test_python_module_entrypoint_uses_lightweight_cli() -> None:
    main_module = importlib.import_module("shuheng.__main__")

    assert main_module.main is cli.main


def test_app_imports_without_genericagent_discovery() -> None:
    env = dict(os.environ)
    env["SHUHENG_DISABLE_GENERICAGENT"] = "1"
    env["PYTHONPATH"] = "src"
    code = (
        "import json; "
        "from shuheng import app; "
        "print(json.dumps(app.agent_runtime_registry(write_memory_prompt_file=False).to_record(), sort_keys=True))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=os.getcwd(),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["default_provider_id"] == "ohmypi"
    assert payload["provider_ids"] == ["ohmypi"]


def test_install_agent_gateway_skill_writes_shared_skill(tmp_path, monkeypatch, capsys) -> None:
    sys.modules.pop("shuheng.app", None)
    monkeypatch.setenv("SHUHENG_SHARED_SKILL_ROOT", str(tmp_path / "shared-skills"))

    result = cli.main(["install-agent-gateway-skill", "--json"])

    output = json.loads(capsys.readouterr().out)
    skill_dir = tmp_path / "shared-skills" / "shuheng-agent-gateway"
    skill_file = skill_dir / "SKILL.md"
    metadata_file = skill_dir / "agents" / "openai.yaml"

    assert result == 0
    assert output["schema_version"] == "shuheng.skill_install.v1"
    assert output["status"] == "installed"
    assert Path(output["destination"]) == skill_dir
    assert skill_file.is_file()
    assert metadata_file.is_file()
    assert "shuheng.app" not in sys.modules

    skill_text = skill_file.read_text(encoding="utf-8")
    metadata_text = metadata_file.read_text(encoding="utf-8")
    assert "name: shuheng-agent-gateway" in skill_text
    assert "shuheng-agent-gateway agent-directory" in skill_text
    assert "shuheng-agent-gateway serve --stdio" in skill_text
    assert "Do not read Shuheng internal context packs" in skill_text
    assert "$shuheng-agent-gateway" in metadata_text
    assert str(tmp_path) not in skill_text
    assert str(tmp_path) not in metadata_text


def test_install_agent_gateway_skill_is_idempotent(tmp_path) -> None:
    root = tmp_path / "shared-skills"

    first = cli.main(["install-agent-gateway-skill", "--skill-root", str(root)])
    second = cli.main(["install-agent-gateway-skill", "--skill-root", str(root)])

    assert first == 0
    assert second == 0
    skill_dir = root / "shuheng-agent-gateway"
    assert sorted(path.relative_to(skill_dir).as_posix() for path in skill_dir.rglob("*") if path.is_file()) == [
        "SKILL.md",
        "agents/openai.yaml",
    ]
