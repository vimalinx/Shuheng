"""Lightweight public CLI entrypoint for Shuheng."""
from __future__ import annotations

import argparse
import sys
from typing import Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shuheng governed local-agent TUI")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(arg in {"-h", "--help"} for arg in args):
        build_parser().parse_args(args)
        return 0
    from .app import main as app_main

    return app_main(args)
