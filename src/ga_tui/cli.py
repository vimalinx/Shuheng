"""Lightweight public CLI entrypoint for Shuheng."""
from __future__ import annotations

import argparse
import sys
from typing import Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shuheng governed local-agent TUI")
    parser.add_argument("--serve-gateway", action="store_true", help="serve the A2A/MCP gateway over HTTP instead of starting curses")
    parser.add_argument("--gateway-daemon", choices=["start", "stop", "restart", "status"], help="manage the A2A/MCP gateway as a background service")
    parser.add_argument("--gateway-host", default="127.0.0.1", help="gateway bind host")
    parser.add_argument("--gateway-port", type=int, default=8765, help="gateway bind port")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(arg in {"-h", "--help"} for arg in args):
        build_parser().parse_args(args)
        return 0
    from .app import main as app_main

    return app_main(args)
