from pathlib import Path

import ga_tui.app as app
from ga_tui import web_console_static


def test_web_console_loader_prefers_explicit_index(tmp_path: Path, monkeypatch) -> None:
    index = tmp_path / "index.html"
    index.write_text("<!doctype html><title>external gui</title>", encoding="utf-8")

    monkeypatch.setenv("SHUHENG_WEB_GUI_INDEX", str(index))

    assert "external gui" in web_console_static.web_console_html()


def test_app_web_console_html_uses_external_loader(tmp_path: Path, monkeypatch) -> None:
    index = tmp_path / "index.html"
    index.write_text("<!doctype html><title>app external gui</title>", encoding="utf-8")

    monkeypatch.setenv("SHUHENG_WEB_GUI_INDEX", str(index))

    assert "app external gui" in app.web_console_html()


def test_missing_web_console_has_operational_hint(monkeypatch) -> None:
    monkeypatch.setenv("SHUHENG_WEB_GUI_INDEX", "/definitely/missing/index.html")
    monkeypatch.setenv("SHUHENG_WEB_GUI_DIR", "/definitely/missing/project")

    html = web_console_static.missing_web_gui_html()

    assert "Shuheng Web GUI is externalized" in html
    assert "SHUHENG_WEB_GUI_INDEX" in html
    assert "SHUHENG_WEB_GUI_DIR" in html
