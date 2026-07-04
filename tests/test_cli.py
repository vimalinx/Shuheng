from __future__ import annotations

import importlib
import sys

from ga_tui import cli


def test_cli_help_does_not_import_app(monkeypatch, capsys) -> None:
    sys.modules.pop("ga_tui.app", None)

    result = None
    try:
        result = cli.main(["--help"])
    except SystemExit as exc:
        result = exc.code

    output = capsys.readouterr().out

    assert result == 0
    assert "Shuheng governed local-agent TUI" in output
    assert "--serve-gateway" in output
    assert "ga_tui.app" not in sys.modules


def test_python_module_entrypoint_uses_lightweight_cli() -> None:
    main_module = importlib.import_module("ga_tui.__main__")

    assert main_module.main is cli.main
