"""External Web Console loader.

The browser UI source lives in the standalone Shuheng-Web-GUI project. This
module keeps the gateway route stable while avoiding a large embedded HTML
string in the backend/TUI module.
"""

from __future__ import annotations

import os
from html import escape
from pathlib import Path


WEB_GUI_INDEX_ENV = "SHUHENG_WEB_GUI_INDEX"
WEB_GUI_DIR_ENV = "SHUHENG_WEB_GUI_DIR"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def web_gui_index_candidates() -> list[Path]:
    candidates: list[Path] = []
    explicit_index = os.environ.get(WEB_GUI_INDEX_ENV)
    if explicit_index:
        candidates.append(Path(explicit_index).expanduser())

    explicit_dir = os.environ.get(WEB_GUI_DIR_ENV)
    if explicit_dir:
        base = Path(explicit_dir).expanduser()
        candidates.extend([base / "public" / "index.html", base / "index.html"])

    root = repo_root()
    candidates.extend([
        root.parent / "Shuheng-Web-GUI" / "public" / "index.html",
        root / "web-gui" / "public" / "index.html",
    ])
    return candidates


def read_web_gui_index() -> tuple[str, Path] | tuple[None, None]:
    for candidate in web_gui_index_candidates():
        try:
            path = candidate.resolve()
        except OSError:
            path = candidate
        if not path.exists() or not path.is_file():
            continue
        try:
            return path.read_text(encoding="utf-8"), path
        except OSError:
            continue
    return None, None


def missing_web_gui_html() -> str:
    candidates = "\n".join(f"<li><code>{escape(str(path))}</code></li>" for path in web_gui_index_candidates())
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Shuheng Web GUI Missing</title>
  <style>
    body {{ font-family: sans-serif; margin: 3rem; line-height: 1.5; color: #20201d; background: #f7f5ef; }}
    main {{ max-width: 48rem; background: #fffefa; border: 1px solid #ddd7ca; border-radius: 0.75rem; padding: 1.5rem; }}
    code {{ background: #f0ece3; padding: 0.08rem 0.28rem; border-radius: 0.25rem; }}
  </style>
</head>
<body>
  <main>
    <h1>Shuheng Web GUI is externalized</h1>
    <p>The backend gateway is running, but the standalone Web GUI project was not found.</p>
    <p>Set <code>{WEB_GUI_INDEX_ENV}</code> to an <code>index.html</code> file, or set <code>{WEB_GUI_DIR_ENV}</code> to a standalone GUI project directory.</p>
    <p>Checked paths:</p>
    <ul>{candidates}</ul>
  </main>
</body>
</html>
"""


def web_console_html() -> str:
    html, _path = read_web_gui_index()
    if html is not None:
        return html
    return missing_web_gui_html()
