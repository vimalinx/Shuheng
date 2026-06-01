"""Integration helpers for keeping GenericAgent-TUI outside GenericAgent core.

The external TUI should normally be launched as ``ga-tui``.  For users who want
the upstream ``ga tui`` command to land in this external TUI, this module can
install a tiny re-runnable shim into a GenericAgent checkout instead of carrying
large local patches in upstream TUI files.
"""
from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
import sys
from textwrap import dedent
from typing import Iterable


REQUIRED_ROOT_FILES = ("agentmain.py", "ga.py")
REQUIRED_FRONTEND_FILES = ("continue_cmd.py",)
REQUIRED_CONTINUE_FUNCS = (
    "_format_response_segment",
    "_pairs",
    "_parse_native_history",
    "_preview_text",
    "_tool_results_from_prompt",
    "_user_text",
    "reset_conversation",
    "restore",
)


def tui_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_genericagent_root(start: str | os.PathLike[str] | None = None) -> Path:
    """Find a GenericAgent checkout without importing its runtime modules."""

    here = Path(__file__).resolve()
    env_root = os.environ.get("GENERICAGENT_ROOT") or os.environ.get("GA_ROOT")
    candidates: list[Path | str | None] = [
        env_root,
        start or os.getcwd(),
        here.parents[3] / "GenericAgent",
        here.parents[4] / "GenericAgent" if len(here.parents) > 4 else None,
        Path.home() / "Programs" / "GenericAgent",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        root = Path(candidate).expanduser().resolve()
        if is_genericagent_root(root):
            return root
    raise RuntimeError("GenericAgent root not found; set GENERICAGENT_ROOT=/path/to/GenericAgent")


def is_genericagent_root(root: Path) -> bool:
    return all((root / name).is_file() for name in REQUIRED_ROOT_FILES) and (root / "frontends").is_dir()


def _prepend_once(path: Path) -> None:
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)


def ensure_core_import_path(root: Path) -> None:
    _prepend_once(root)
    _prepend_once(root / "frontends")


def validate_core(root: Path) -> list[str]:
    """Return human-readable validation failures for a GenericAgent checkout."""

    failures: list[str] = []
    if not is_genericagent_root(root):
        failures.append(f"{root} does not look like a GenericAgent root")
        return failures
    for name in REQUIRED_FRONTEND_FILES:
        if not (root / "frontends" / name).is_file():
            failures.append(f"missing frontends/{name}")
    ensure_core_import_path(root)
    try:
        importlib.import_module("agentmain")
    except Exception as exc:
        failures.append(f"cannot import agentmain: {type(exc).__name__}: {exc}")
    try:
        continue_cmd = importlib.import_module("continue_cmd")
    except Exception as exc:
        failures.append(f"cannot import continue_cmd: {type(exc).__name__}: {exc}")
    else:
        for name in REQUIRED_CONTINUE_FUNCS:
            if not hasattr(continue_cmd, name):
                failures.append(f"continue_cmd missing {name}")
    try:
        importlib.import_module("session_names")
    except Exception:
        # Optional: the TUI has a runtime fallback when session_names is absent.
        pass
    return failures


def generated_core_shim(tui_root: Path | None = None) -> str:
    """Return a small launcher that delegates from GenericAgent to this repo."""

    repo = tui_root or tui_repo_root()
    repo_s = str(repo)
    return dedent(
        f'''\
        """Generated GenericAgent-TUI external launcher.

        Re-run `ga-tui-install-core-shim` after upstream GenericAgent updates if
        this file is replaced.  The real TUI lives outside GenericAgent core.
        """
        from __future__ import annotations

        import os
        from pathlib import Path
        import runpy
        import sys


        def _genericagent_root() -> Path:
            return Path(__file__).resolve().parents[1]


        def _candidate_roots():
            env_repo = os.environ.get("GA_TUI_REPO")
            if env_repo:
                yield Path(env_repo).expanduser()
            yield Path({repo_s!r})
            yield _genericagent_root().parent / "GenericAgent-TUI"
            yield Path.home() / "Programs" / "GenericAgent-TUI"


        def main() -> None:
            os.environ.setdefault("GENERICAGENT_ROOT", str(_genericagent_root()))
            app_path = os.environ.get("GA_TUI_APP")
            if app_path and Path(app_path).expanduser().is_file():
                runpy.run_path(str(Path(app_path).expanduser()), run_name="__main__")
                return
            for root in _candidate_roots():
                src = root / "src"
                if (src / "ga_tui" / "app.py").is_file():
                    sys.path.insert(0, str(src))
                    runpy.run_module("ga_tui.app", run_name="__main__")
                    return
            runpy.run_module("ga_tui.app", run_name="__main__")


        if __name__ == "__main__":
            main()
        '''
    )


def install_core_shim(
    root: Path,
    *,
    target: str = "frontends/tuiapp_curses.py",
    overwrite: bool = False,
) -> Path:
    if target not in {"frontends/tuiapp_curses.py", "frontends/tuiapp.py"}:
        raise ValueError("target must be frontends/tuiapp_curses.py or frontends/tuiapp.py")
    failures = validate_core(root)
    if failures:
        raise RuntimeError("; ".join(failures))
    path = root / target
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        current = path.read_text(encoding="utf-8", errors="replace")
        if "Generated GenericAgent-TUI external launcher" not in current:
            raise FileExistsError(f"{path} exists; pass --overwrite to replace it")
    if path.exists() and target == "frontends/tuiapp.py":
        backup = path.with_suffix(path.suffix + ".genericagent-tui.bak")
        if not backup.exists():
            backup.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    path.write_text(generated_core_shim(), encoding="utf-8")
    return path


def _print_report(root: Path, failures: Iterable[str]) -> int:
    print(f"GenericAgent root: {root}")
    print(f"GenericAgent-TUI root: {tui_repo_root()}")
    if failures:
        print("Status: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Status: OK")
    print("Core imports: agentmain, continue_cmd")
    print("Launch without core patches: ga-tui")
    print("Optional shim: ga-tui-install-core-shim --target tuiapp")
    return 0


def doctor_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate GenericAgent-TUI core integration")
    parser.add_argument("--root", default="", help="GenericAgent root; defaults to auto-discovery")
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve() if args.root else find_genericagent_root()
    return _print_report(root, validate_core(root))


def install_core_shim_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install an external GenericAgent-TUI launcher shim")
    parser.add_argument("--root", default="", help="GenericAgent root; defaults to auto-discovery")
    parser.add_argument(
        "--target",
        choices=("tuiapp-curses", "tuiapp"),
        default="tuiapp-curses",
        help="tuiapp-curses writes an untracked sidecar; tuiapp makes upstream `ga tui` delegate here",
    )
    parser.add_argument("--overwrite", action="store_true", help="replace an existing non-generated target file")
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve() if args.root else find_genericagent_root()
    target = "frontends/tuiapp.py" if args.target == "tuiapp" else "frontends/tuiapp_curses.py"
    path = install_core_shim(root, target=target, overwrite=args.overwrite)
    print(f"Installed GenericAgent-TUI shim: {path}")
    if args.target == "tuiapp":
        print("Upstream `ga tui` should now delegate to the external TUI.")
    else:
        print("Sidecar installed. Run it with: python frontends/tuiapp_curses.py")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GenericAgent-TUI integration utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="validate imports and discovery")
    doctor.add_argument("--root", default="")
    install = sub.add_parser("install-core-shim", help="install launcher shim into GenericAgent")
    install.add_argument("--root", default="")
    install.add_argument("--target", choices=("tuiapp-curses", "tuiapp"), default="tuiapp-curses")
    install.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "doctor":
        doctor_args = []
        if args.root:
            doctor_args += ["--root", args.root]
        return doctor_main(doctor_args)
    if args.command == "install-core-shim":
        install_args = []
        if args.root:
            install_args += ["--root", args.root]
        install_args += ["--target", args.target]
        if args.overwrite:
            install_args.append("--overwrite")
        return install_core_shim_main(install_args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
