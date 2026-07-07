# Add Transient Skill Invocation And Completion

## Goal

Let users invoke an OMP skill for a single prompt with `$skill-name ...` or tolerated `$+skill-name ...`, and make `$` use the same lightweight completion experience as command completion. `$skill` is only a Shuheng alias for OMP's native `/skill:<name>` command. It must not introduce a second skill registry, marketplace, plugin execution layer, new permission model, or Shuheng-side prompt-level skill-body injection.

## What I Already Know

- Existing dedicated skills are stored as `skill_refs` on one subagent and resolved from Shuheng/Codex/OMP/repo skill roots.
- `subagent_skill_roots()` already includes `~/.agents/skills` and `~/.omp/agent/skills`.
- Existing skill-pack construction reads only the selected refs through `subagent_skill_pack_for_refs(...)`.
- Long-term skill assignment already exists through `/agent skill add|remove|set|clear`.
- The new `$skill` behavior should be transient: it affects the current user prompt only and must not persist into subagent metadata.
- The user explicitly wants to rely on OMP's own `/skill:<name>` loader rather than building a separate Shuheng prompt-level skill framework.

## Requirements

- Detect `$<skill-ref>` and `$+<skill-ref>` at the beginning of a submitted prompt.
- Strip the leading `$<skill-ref>` token from the task text before dispatching to the model/subagent.
- Do not build or inject a Shuheng transient skill body pack for `$skill`.
- When dispatching to an OMP runtime agent and the first transient ref is command-safe, convert the runtime prompt to OMP native `/skill:<ref> ...` while keeping the stripped Shuheng task/context payload in the command args.
- Preserve permanent `/agent skill ...` behavior unchanged.
- Add `$` completion candidates sourced from existing skill roots.
- Rank completion candidates by skill name first, then description/summary second.
- Show a bounded candidate label and description without loading every full skill body into the normal prompt.
- Keep `$skill` visible as transient metadata for audit, but let OMP decide whether the command name exists in its own loaded skill set.
- Preserve root containment checks: explicit paths may resolve only if they are inside allowed skill roots.
- Record transient skill refs in task/context metadata where useful for audit, but do not write them into subagent metadata.

## Acceptance Criteria

- [ ] `$huashu-info-search 调研...` dispatches an OMP prompt starting with `/skill:huashu-info-search ` for that prompt only.
- [ ] `$+huashu-info-search 调研...` normalizes to the same transient skill ref and task text.
- [ ] OMP runtime dispatch for a command-safe `$skill` starts with `/skill:<name>` and does not send a queued plain prompt that bypasses OMP's skill loader.
- [ ] `@researcher $huashu-info-search 调研...` dispatches to `researcher` with that transient skill for that prompt only.
- [ ] `/agent skill add researcher huashu-info-search` remains the long-term assignment path.
- [ ] `$` completion lists skills from current allowed roots, including `~/.agents/skills` and `~/.omp/agent/skills` when present.
- [ ] Completion ranking prefers name matches over description matches.
- [ ] Completion rows expose name/source/summary only, not full skill bodies.
- [ ] Transient skill refs are recorded as metadata only and do not persist to subagent `skill_refs`.
- [ ] Tests and policy gates prove no arbitrary outside path injection and no cross-agent skill leakage.

## Definition Of Done

- Code implemented with existing command completion and skill-pack patterns.
- Backend spec updated with the `$skill` transient invocation contract.
- Unit tests cover parsing, completion ranking, OMP `/skill:` prompt prefixing, metadata-only context formatting, non-persistence, and outside-path non-injection.
- Policy gate updated for the new boundary.
- Targeted and full quality gates pass where feasible.
- Commit created for this task only, excluding unrelated `_knowledge_base/`.

## Out Of Scope

- No new skill marketplace.
- No new plugin execution.
- No automatic background skill installation.
- No global injection of all skill descriptions into the main prompt.
- No replacement of `/agent skill ...`.
- No remote/web/mobile surface.

## Technical Notes

- Likely files: `src/shuheng/app.py`, `src/shuheng/commands.py`, `tests/test_context_packs.py`, `tests/test_subagent_store.py`, `scripts/check_policy_gates.py`, `.trellis/spec/backend/agent-control-protocol.md`.
- Existing source of truth: `.trellis/spec/backend/agent-control-protocol.md` scenario `Per-Agent Dedicated Skills`.
- Existing context-pack formatter labels permanent skill content as `Dedicated skills for this agent only`; transient skills should have a distinct label so the worker knows the skill came from the current user prompt.
