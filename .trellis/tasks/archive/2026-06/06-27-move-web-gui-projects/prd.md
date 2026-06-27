# Move Standalone Web GUI Project To Projects

## Goal

Move the standalone Shuheng Web GUI project from `/home/vimalinx/Programs/Shuheng-Web-GUI` to `/home/vimalinx/Projects/Shuheng-Web-GUI`, then update Shuheng references so the backend gateway continues to find the external GUI at its new location.

## Requirements

* Move the full standalone Git project directory to `/home/vimalinx/Projects/Shuheng-Web-GUI`.
* Preserve the standalone project's Git history and working tree state.
* Update Shuheng default Web GUI lookup paths and documentation from the old Programs path to the new Projects path.
* Do not touch unrelated dirty files in the Shuheng repo.

## Acceptance Criteria

* [x] `/home/vimalinx/Projects/Shuheng-Web-GUI` exists and is a Git repo.
* [x] `/home/vimalinx/Programs/Shuheng-Web-GUI` no longer exists as the active project directory.
* [x] Shuheng `web_console_static` can load the GUI from the new location without env overrides.
* [x] README references point to `/home/vimalinx/Projects/Shuheng-Web-GUI`.
* [x] Targeted tests or smoke checks pass.

## Technical Approach

Move the directory with `mv`, then update the Shuheng loader candidate list and README text. Run loader tests and a direct `app.web_console_html()` check.

## Verification

* `test ! -e /home/vimalinx/Programs/Shuheng-Web-GUI && test -d /home/vimalinx/Projects/Shuheng-Web-GUI/.git`: passed.
* `PYTHONPATH=src python3 - <<'PY' ... app.web_console_html() ...`: loaded the new default path and found `Shuheng Console` plus `/gui/snapshot`.
* `PYTHONPATH=src python3 -m unittest discover -s tests` in `/home/vimalinx/Projects/Shuheng-Web-GUI`: passed.
* `pytest -q tests/test_web_console_static.py` in `/home/vimalinx/Programs/Shuheng`: passed.
* `python3 -m compileall -q src scripts` in both repositories: passed.
* `git diff --check` in both repositories: passed.

## Out of Scope

* Redesigning the GUI.
* Changing `/gui/snapshot` or `/gui/action` backend behavior.
