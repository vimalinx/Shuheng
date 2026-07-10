"""Lightweight public CLI entrypoint for Shuheng."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from . import __version__


def package_version() -> str:
    """Return the package version enforced against pyproject metadata by release hygiene."""

    return __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Shuheng governed local-agent TUI",
        epilog="Run 'shuheng install-agent-gateway-skill' to install the shared local agent gateway skill.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {package_version()}")
    subcommands = parser.add_subparsers(dest="command")
    install_skill = subcommands.add_parser(
        "install-agent-gateway-skill",
        help="install Shuheng's shared local agent gateway skill",
        description="Install or update Shuheng's shared local agent gateway skill.",
    )
    install_skill.add_argument(
        "--skill-root",
        default="",
        help="shared skill root; defaults to $SHUHENG_SHARED_SKILL_ROOT or ~/.agents/skills",
    )
    install_skill.add_argument("--json", action="store_true", help="print machine-readable install result")
    runtime = subcommands.add_parser(
        "runtime",
        help="install or verify Shuheng's external runtimes",
        description="Install or verify the permanent OMP runtime and optional Pi-native worker SDK.",
    )
    runtime_commands = runtime.add_subparsers(dest="runtime_command", required=True)
    setup_omp = runtime_commands.add_parser(
        "setup-omp",
        help="idempotently install the pinned permanent OMP runtime",
    )
    setup_omp.add_argument(
        "--replace",
        action="store_true",
        help="explicitly replace an existing unsupported OMP version with Shuheng's pinned version",
    )
    setup_omp.add_argument("--json", action="store_true", help="print a machine-readable result")
    setup_pi = runtime_commands.add_parser(
        "setup-pi",
        help="idempotently install the pinned optional Pi-native worker SDK",
    )
    setup_pi.add_argument("--json", action="store_true", help="print a machine-readable result")
    check = runtime_commands.add_parser("check", help="verify external runtime availability")
    check.add_argument("--require-pi", action="store_true", help="also require the optional Pi-native worker SDK")
    check.add_argument("--json", action="store_true", help="print machine-readable results")
    return parser


def _install_agent_gateway_skill(args: argparse.Namespace) -> int:
    from .skill_installer import install_agent_gateway_skill

    result = install_agent_gateway_skill(getattr(args, "skill_root", "") or None)
    record = result.to_record()
    if getattr(args, "json", False):
        print(json.dumps(record, ensure_ascii=False, sort_keys=True))
        return 0
    print(f"Installed {record['name']} skill")
    print(f"Destination: {record['destination']}")
    print("Use: $shuheng-agent-gateway")
    print("Gateway: shuheng-agent-gateway serve --stdio")
    return 0


def _print_runtime_probe(probe: object) -> None:
    record = probe.to_record()  # type: ignore[attr-defined]
    label = "OMP" if record["runtime"] == "omp" else "Pi-native"
    print(f"{label}: {'OK' if record['ok'] else 'FAIL'} ({record['status']})")
    print(f"Package: {record['package']}@{record['required_version']}")
    if record.get("binary"):
        print(f"Binary: {record['binary']}")
    if record.get("detected_version"):
        print(f"Detected version: {record['detected_version']}")
    if record.get("detail"):
        print(str(record["detail"]))
    if record.get("action"):
        print(str(record["action"]))


def _runtime_command(args: argparse.Namespace) -> int:
    from .runtime_setup import (
        check_omp_runtime,
        check_pi_native_runtime,
        setup_omp_runtime,
        setup_pi_native_runtime,
    )

    if args.runtime_command == "setup-omp":
        probes = [setup_omp_runtime(replace=bool(getattr(args, "replace", False)))]
    elif args.runtime_command == "setup-pi":
        probes = [setup_pi_native_runtime()]
    else:
        probes = [check_omp_runtime(), check_pi_native_runtime()]
    ok = bool(probes[0].ok) and (not getattr(args, "require_pi", False) or all(probe.ok for probe in probes))
    if getattr(args, "json", False):
        payload = {
            "schema_version": "shuheng.runtime_setup.v1",
            "ok": ok,
            "results": [probe.to_record() for probe in probes],
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        for index, probe in enumerate(probes):
            if index:
                print()
            _print_runtime_probe(probe)
        if args.runtime_command == "check" and not getattr(args, "require_pi", False) and not probes[1].ok:
            print("\nPi-native is optional; its unavailable status does not fail this check.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"install-agent-gateway-skill", "runtime"}:
        parsed = build_parser().parse_args(args)
        if parsed.command == "install-agent-gateway-skill":
            return _install_agent_gateway_skill(parsed)
        return _runtime_command(parsed)
    if any(arg in {"-h", "--help", "--version"} for arg in args):
        build_parser().parse_args(args)
        return 0
    from .app import main as app_main

    return app_main(args)
