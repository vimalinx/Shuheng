"""Lightweight public CLI entrypoint for Shuheng."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Shuheng governed local-agent TUI",
        epilog="Run 'shuheng install-agent-gateway-skill' to install the shared local agent gateway skill.",
    )
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


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "install-agent-gateway-skill":
        parsed = build_parser().parse_args(args)
        return _install_agent_gateway_skill(parsed)
    if any(arg in {"-h", "--help"} for arg in args):
        build_parser().parse_args(args)
        return 0
    from .app import main as app_main

    return app_main(args)
