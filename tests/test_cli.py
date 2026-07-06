from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys

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
