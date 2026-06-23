# Promote Shuheng To Main And Archive Legacy State

## Goal

Make the current Shuheng line the repository's primary local `main` branch and move older local branch names out of the active branch namespace while preserving recoverability.

## What I Already Know

- User requested: "直接把shuheng弄成主分支，旧的那些归档吧。"
- Current branch is `experiment/ohmypi-runtime-memory`.
- Local branches are `experiment/ohmypi-runtime-memory`, `main`, and `backup/pre-clean-public-main-20260601`.
- Current branch is ahead of local `main` and represents the Shuheng/OHMYPI runtime-memory line.
- Remote is `origin https://github.com/vimalinx/GenericAgent-TUI.git`.
- Remote `origin/main` is older than the current local Shuheng branch.
- Worktree has existing uncommitted changes in `src/ga_tui/agent_bridge.py`, `src/ga_tui/app.py`, `src/ga_tui/ohmypi_provider.py`, plus Trellis task files.

## Assumptions

- "Shuheng as main branch" means the current local branch should become local `main`.
- "Old ones" means old local branch references, especially the previous local `main` and the old `backup/pre-clean-public-main-20260601`.
- Archive means preserve old commits under `archive/*` branch names, not delete history.
- Do not force-push or delete remote branches unless the user explicitly asks after local state is correct.
- Existing dirty code changes are user/WIP state and must be preserved.

## Requirements

- Preserve the current dirty worktree.
- Preserve the old local `main` commit under an archive branch.
- Preserve the old backup branch under an archive branch.
- Rename the current Shuheng branch to local `main`.
- Avoid destructive commands such as `git reset --hard`.
- Verify branch layout after the change.
- Report remote status separately from local status.

## Acceptance Criteria

- [x] `git branch --show-current` returns `main`.
- [x] The old local `main` commit is reachable from an `archive/*` branch.
- [x] The old backup branch is reachable from an `archive/*` branch.
- [x] Existing dirty worktree changes remain present.
- [x] No remote force-push or remote branch deletion is performed.
- [x] Final status clearly states whether `origin/main` still points at the older remote commit.

## Completion Notes

- Local `main` now points to `c76e59bfe24ea68ccfcfde507734af6c226ba2fb`.
- Previous local `main` is archived as `archive/main-before-shuheng-20260622` at `e8772fec5e51766e533da4bbaef2494c2e591533`.
- Previous local `backup/pre-clean-public-main-20260601` is archived as `archive/pre-clean-public-main-20260601` at `c400d293deca77aa7d21c6c33f29a4149d61bac1`.
- `origin/main` still points to `cb39fef0fb551e22df5ed7df7fa3c77df4e824bb`; no remote push or remote deletion was performed.
- Existing dirty worktree changes were preserved.

## Definition Of Done

- Local branch promotion completed.
- Archive branches verified.
- Dirty worktree preserved.
- User receives concise final status and any remaining remote follow-up.

## Out Of Scope

- Completing the layered-memory code task.
- Committing dirty WIP changes.
- Force-pushing `main` to GitHub.
- Deleting remote branches.
- Archiving in-progress Trellis tasks that are unrelated to branch promotion.

## Technical Notes

- Use non-destructive git branch rename operations.
- Existing local `main` must be renamed away before renaming the current branch to `main`.
- Suggested archive names:
  - `archive/main-before-shuheng-20260622`
  - `archive/pre-clean-public-main-20260601`
