# Publish Shuheng Public Alpha

## Goal

Publish the current clean Shuheng repository state as an experimental local alpha without pushing to the old repository remote.

## Requirements

* Preserve the existing old `origin` remote until a safe public remote is configured.
* Create or reuse a public GitHub repository named `vimalinx/Shuheng`.
* Add a dedicated `public` remote for the new repository if one does not exist.
* Re-run the full release gate before pushing.
* Build wheel and sdist into `/tmp/shuheng-dist`.
* Create an alpha tag for this release.
* Push `main` and the alpha tag to the public Shuheng remote.
* Create a GitHub prerelease with release notes and attach the wheel/sdist artifacts when tooling/auth allows.

## Acceptance Criteria

* [x] `git status --short` is clean before release push except for Trellis task bookkeeping.
* [x] Full release gate passes.
* [x] Public remote points at `vimalinx/Shuheng`, not the old repository.
* [x] Public GitHub repository exists.
* [x] `main` is pushed to the public remote.
* [x] Release tag is pushed to the public remote.
* [x] GitHub prerelease exists with artifacts, or the blocker is recorded clearly.

## Definition of Done

* Release actions are complete or blocked by a concrete external authentication/permission issue.
* No private local runtime state is pushed.
* Work commit is not needed unless release notes/docs need edits; Trellis archive and journal still record the publishing task.

## Technical Approach

Use a dedicated `public` remote for `https://github.com/vimalinx/Shuheng.git` so the old `origin` remains untouched. Use `gh` if authenticated to create the repo/release; fall back to plain `git push` where possible.

## Out of Scope

* PyPI publication.
* Homebrew, apt, or OS package publication.
* macOS/Windows native support certification.
* Changing product code or release posture.
