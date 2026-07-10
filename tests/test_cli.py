from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from shuheng import cli
from shuheng import runtime_setup


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


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
    assert "runtime" in output
    assert "install or verify Shuheng's external runtimes" in output
    assert "shuheng.app" not in sys.modules


def test_cli_version_uses_canonical_package_version(capsys) -> None:
    result = None
    try:
        cli.main(["--version"])
    except SystemExit as exc:
        result = exc.code

    assert result == 0
    assert capsys.readouterr().out.strip().endswith(f" {cli.package_version()}")


def test_cli_setup_omp_is_lightweight_and_machine_readable(monkeypatch, capsys) -> None:
    sys.modules.pop("shuheng.app", None)
    probe = runtime_setup.RuntimeProbe(
        runtime="omp",
        ok=True,
        status="available",
        package=runtime_setup.OMP_PACKAGE,
        required_version=runtime_setup.OMP_VERSION,
        binary="/tmp/omp",
        detected_version=runtime_setup.OMP_VERSION,
    )
    monkeypatch.setattr(runtime_setup, "setup_omp_runtime", lambda *, replace=False: probe)

    result = cli.main(["runtime", "setup-omp", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert payload["schema_version"] == "shuheng.runtime_setup.v1"
    assert payload["results"][0]["package"] == runtime_setup.OMP_PACKAGE
    assert "shuheng.app" not in sys.modules


def test_cli_runtime_check_requires_only_omp_by_default(monkeypatch, capsys) -> None:
    omp = runtime_setup.RuntimeProbe(
        runtime="omp",
        ok=True,
        status="available",
        package=runtime_setup.OMP_PACKAGE,
        required_version=runtime_setup.OMP_VERSION,
    )
    pi = runtime_setup.RuntimeProbe(
        runtime="pi-native",
        ok=False,
        status="missing_package",
        package=runtime_setup.PI_NATIVE_SDK_PACKAGE,
        required_version=runtime_setup.PI_NATIVE_SDK_VERSION,
    )
    monkeypatch.setattr(runtime_setup, "check_omp_runtime", lambda: omp)
    monkeypatch.setattr(runtime_setup, "check_pi_native_runtime", lambda: pi)

    assert cli.main(["runtime", "check", "--json"]) == 0
    optional = json.loads(capsys.readouterr().out)
    assert optional["ok"] is True

    assert cli.main(["runtime", "check", "--require-pi", "--json"]) == 1
    required = json.loads(capsys.readouterr().out)
    assert required["ok"] is False


def test_python_module_entrypoint_uses_lightweight_cli() -> None:
    main_module = importlib.import_module("shuheng.__main__")

    assert main_module.main is cli.main


def test_app_imports_without_genericagent_discovery() -> None:
    env = dict(os.environ)
    env["SHUHENG_DISABLE_GENERICAGENT"] = "1"
    env["PYTHONPATH"] = str(SRC)
    code = (
        "import json; "
        "from shuheng import app; "
        "print(json.dumps(app.agent_runtime_registry(write_memory_prompt_file=False).to_record(), sort_keys=True))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["default_provider_id"] == "ohmypi"
    assert payload["provider_ids"] == ["ohmypi", "pi-native"]


def test_pi_native_cannot_replace_permanent_omp_main_provider() -> None:
    env = dict(os.environ)
    env.update({
        "SHUHENG_DISABLE_GENERICAGENT": "1",
        "SHUHENG_RUNTIME_PROVIDER": "pi-native",
        "PYTHONPATH": str(SRC),
    })
    code = (
        "import json; "
        "from shuheng import app; "
        "print(json.dumps(app.agent_runtime_registry(write_memory_prompt_file=False).to_record(), sort_keys=True))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["default_provider_id"] == "ohmypi"
    assert payload["provider_ids"] == ["ohmypi", "pi-native"]


def test_legacy_runtime_env_cannot_replace_permanent_omp_main_provider() -> None:
    env = dict(os.environ)
    env.update({
        "SHUHENG_DISABLE_GENERICAGENT": "1",
        "SHUHENG_RUNTIME_PROVIDER": "genericagent",
        "PYTHONPATH": str(SRC),
    })
    code = (
        "import json; "
        "from shuheng import app; "
        "print(json.dumps(app.agent_runtime_registry(write_memory_prompt_file=False).to_record(), sort_keys=True))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["default_provider_id"] == "ohmypi"
    assert payload["provider_ids"] == ["ohmypi", "pi-native"]


def test_fresh_process_state_stays_out_of_simulated_real_home(tmp_path: Path) -> None:
    simulated_real_home = tmp_path / "simulated-real-home"
    isolated_root = tmp_path / "isolated-shuheng"
    env = dict(os.environ)
    env.update({
        "HOME": str(simulated_real_home),
        "SHUHENG_HOME": str(isolated_root),
        "SHUHENG_HARNESS_DIR": str(isolated_root / "memory" / "agent_harness"),
        "SHUHENG_SECRET_VAULT_DIR": str(isolated_root / "memory" / "secret_vault"),
        "SHUHENG_DISABLE_GENERICAGENT": "1",
        "PYTHONPATH": str(SRC),
    })
    code = "\n".join([
        "import json",
        "from shuheng.frontend_history_compat import fallback_continue_cmd_module, fallback_session_names",
        "fallback_continue = fallback_continue_cmd_module()",
        "fallback_names = fallback_session_names()",
        "fallback_names.set_name('/tmp/model_responses_fallback.txt', 'Fallback title')",
        "from shuheng import app",
        "app.save_session_meta_registry({'model_responses_test.txt': {'rounds': 1}})",
        "app.ensure_shuheng_layered_memory_files()",
        "workspace = app.workspace_context_payload()",
        "runtime = app.runtime_registry_record()",
        "print(json.dumps({",
        "    'home': app.SHUHENG_HOME,",
        "    'harness': app.AGENT_HARNESS_DIR,",
        "    'secret': app.SECRET_VAULT_DIR,",
        "    'session_meta': app.SESSION_META_PATH,",
        "    'workspace_ref': (workspace.get('refs') or [''])[0],",
        "    'runtime_path': app.AGENT_RUNTIME_REGISTRY_PATH,",
        "    'runtime_schema': runtime.get('schema_version', ''),",
        "    'fallback_cache': fallback_continue._ROUNDS_CACHE_PATH,",
        "    'fallback_names': fallback_names._REG_PATH,",
        "}, sort_keys=True))",
    ])

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert Path(payload["home"]) == isolated_root
    assert Path(payload["harness"]).is_relative_to(isolated_root)
    assert Path(payload["secret"]).is_relative_to(isolated_root)
    assert Path(payload["session_meta"]).is_relative_to(isolated_root)
    assert Path(payload["workspace_ref"]).is_relative_to(isolated_root)
    assert Path(payload["runtime_path"]).is_relative_to(isolated_root)
    assert Path(payload["fallback_cache"]).is_relative_to(isolated_root)
    assert Path(payload["fallback_names"]).is_relative_to(isolated_root)
    assert json.loads(Path(payload["fallback_names"]).read_text(encoding="utf-8")) == {
        "model_responses_fallback.txt": "Fallback title"
    }
    assert payload["runtime_schema"] == "agentruntime.registry.v1"
    assert not (simulated_real_home / ".shuheng").exists()


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
