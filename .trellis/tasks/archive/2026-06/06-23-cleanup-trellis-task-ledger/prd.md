# Clean Up Trellis Task Ledger

## Goal

Bring the Trellis task ledger back into a truthful, low-noise state so future Shuheng work can resume from a clear active task list. This cleanup is about Trellis metadata and session bookkeeping, not changing Shuheng runtime behavior.

## What I Already Know

* The user asked to "organize first" after the current state review.
* Current active task pointer is `.trellis/tasks/06-23-cleanup-trellis-task-ledger`.
* `main` is the active branch and is aligned with `origin/main` at `cc15c38 fix: bound gateway SSE streams and retire sha1 hashes`.
* The code worktree has no dirty tracked code changes.
* The only dirty paths are untracked Trellis task directories:
  * `.trellis/tasks/06-20-shuheng-genericagent-memory-mode/`
  * `.trellis/tasks/06-22-shuheng-main-archive-legacy/`
  * `.trellis/tasks/06-23-cleanup-trellis-task-ledger/`
* Trellis reports 11 active task directories after creating this cleanup task.
* Two tasks are marked `completed` but remain under `.trellis/tasks/` instead of archive:
  * `06-20-auto-shuheng-workspace-selection`
  * `06-20-shuheng-memory-workspace-redesign`
* `06-22-shuheng-main-archive-legacy` has acceptance criteria checked in its PRD, but `task.json` still says `in_progress`.
* `06-20-shuheng-genericagent-memory-mode` remains `in_progress`; its PRD still has unchecked acceptance criteria and should be treated as a real unfinished development task unless evidence proves otherwise.
* The workspace journal currently records completed sessions through Session 22 on 2026-06-15, while later Shuheng commits and Trellis tasks exist.
* Trellis itself reports an available update: `0.5.19 -> 0.6.3, run npm install -g @mindfoldhq/trellis@latest`.

## Assumptions

* "整理" means reduce Trellis ledger noise and make task state match reality.
* Existing task PRDs should be preserved rather than deleted.
* Completed Trellis task directories can be archived through `task.py archive` when the task status and contents show they are complete.
* Old in-progress tasks that are likely stale should not be silently deleted; they should either be archived as completed only when evidence is strong, or left active with a clear note.
* This cleanup should not force-push, change branches, or modify business/runtime code.

## Open Questions

* None blocking.

## Requirements

* Do not touch business code.
* Preserve all Trellis task PRDs and task metadata unless deliberately archiving via Trellis tooling.
* Archive tasks already marked `completed` if their files are consistent.
* Reconcile `06-22-shuheng-main-archive-legacy` because its PRD says the branch-promotion work is done but `task.json` remains `in_progress`.
* Keep `06-20-shuheng-genericagent-memory-mode` visible as unfinished unless we verify its acceptance criteria are complete.
* Keep a concise record of what was cleaned and what remains intentionally active.
* Run a post-cleanup status check with `task.py list`, `task.py current --source`, and `git status --porcelain`.

## Acceptance Criteria

* [x] Completed tasks no longer appear in the active task list.
* [x] The branch-promotion task state matches its PRD evidence.
* [x] The active task list clearly separates real unfinished work from completed bookkeeping.
* [x] No runtime/business source files are modified.
* [x] Untracked Trellis task directories are either intentionally tracked as this cleanup's output or removed by archive movement.
* [x] Final report states the remaining active Trellis tasks and next recommended development task.

## Definition Of Done

* Trellis metadata cleanup is applied.
* `python3 ./.trellis/scripts/task.py list` reflects the intended state.
* `python3 ./.trellis/scripts/task.py current --source` points to this cleanup task until the cleanup is finished.
* `git status --porcelain=v1` contains only expected Trellis bookkeeping changes.
* If Trellis archive/journal commands create commits automatically, those commits are identified explicitly.

## Feasible Approaches

### Approach A: Conservative Cleanup (Recommended)

Archive tasks that are explicitly completed, mark the branch-promotion task completed only if its PRD and branch evidence agree, and leave old ambiguous `in_progress` tasks active. This minimizes accidental loss of task intent.

### Approach B: Aggressive Ledger Reset

Archive all stale tasks that appear superseded by current commits, including older May and early June in-progress items. This produces the cleanest active list but risks hiding unfinished work.

### Approach C: Metadata-Only Report

Do not archive or edit task state yet. Produce a written cleanup map and wait for a later pass. This is safest but leaves the Trellis noise in place.

## Recommendation

Use Approach A now. It should clean the obvious ledger drift without erasing unfinished work, then resume `06-20-shuheng-genericagent-memory-mode` as the next real development task.

## Decision (ADR-lite)

Context: The Trellis ledger has obvious completed-task drift plus older ambiguous `in_progress` tasks. Deleting or archiving all stale-looking tasks would make the list cleaner but could hide real unfinished work.

Decision: Use conservative cleanup. Archive only tasks with strong completion evidence, reconcile the 2026-06-22 branch-promotion task because its PRD and git branch state agree, and keep ambiguous unfinished tasks active.

Consequences: The active list remains somewhat noisy, but it becomes truthful. Follow-up work can address older stale tasks one by one if needed.

## Out Of Scope

* Updating Trellis itself from 0.5.19 to 0.6.3.
* Changing Shuheng runtime code.
* Solving the unfinished layered-memory task.
* Rewriting old PRDs for historical accuracy beyond minimal notes needed for cleanup.
* Force-pushing or changing remote branch state.

## Technical Notes

* Current task command: `python3 ./.trellis/scripts/task.py current --source`.
* Active task listing command: `python3 ./.trellis/scripts/task.py list`.
* Archive command is available as `python3 ./.trellis/scripts/task.py archive <task-dir>`.
* The relevant backend spec index is `.trellis/spec/backend/index.md`; this cleanup mainly touches Trellis metadata, not backend behavior.
* The architecture baseline requirement still applies when reporting Shuheng/agent-harness changes, but this task is bookkeeping-only.

## Completion Notes

* Archived `06-20-auto-shuheng-workspace-selection` with `--no-commit`.
* Archived `06-20-shuheng-memory-workspace-redesign` with `--no-commit`.
* Added completion notes to `06-22-shuheng-main-archive-legacy` and archived it with `--no-commit`.
* Left `06-20-shuheng-genericagent-memory-mode` active because its PRD still has unchecked acceptance criteria and it remains the likely next Shuheng development task.
* Post-cleanup `task.py list` shows 8 active tasks, including this cleanup task while it remains current.
* No runtime or business source files were modified.
* `git diff --check` passed.
* `python3 scripts/check_policy_gates.py` passed.
* `python3 -m py_compile src/ga_tui/app.py src/ga_tui/scheduler.py src/ga_tui/ohmypi_provider.py scripts/check_policy_gates.py` passed.
* `python3 -m pytest -q` passed with 168 tests.
* Spec update review completed: no `.trellis/spec` changes needed because no executable product contract changed.
* Architecture baseline review: moving completed work out of the active Trellis list makes the task ledger more truthful and therefore closer to the governed-orchestrator baseline. No new gaps were introduced in orchestrator responsibility, restricted subagents, approval gates, memory, artifacts, recovery, trace, A2A, or MCP compatibility.
