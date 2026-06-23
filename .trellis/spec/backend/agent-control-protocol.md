# Agent Control Protocol

> Executable contract for Shuheng / GenericAgent-TUI compatibility control blocks and governed subagent delegation.

## Scenario: Shuheng Brand Entry Points

### 1. Scope / Trigger

- Trigger: The user-facing product name is `Shuheng` / `枢衡`; legacy `ga-tui` command aliases have been removed from public entry points while protocol and Python module compatibility identifiers remain internal surfaces.
- Applies to: `pyproject.toml` console scripts, README command examples, integration doctor output, core shim help text, runtime prompts, and OMP/tool descriptions.
- Non-goal: This does not rename `src/ga_tui`, `GA_TUI_*` environment variables, `ga-tui.*` schema versions, `ga_tui_query`, `ga_tui_propose`, existing JSONL context ids, or historical compatibility markers.

### 2. Signatures

- Primary console scripts: `shuheng`, `shuheng-agent-bridge`, `shuheng-check`, `shuheng-install-core-shim`, and `shuheng-integration`.
- Public `ga-tui*` console scripts are not exported.
- Python module entry remains `python -m ga_tui` / `python -m ga_tui.app`.
- Distribution name in `pyproject.toml`: `shuheng`.

### 3. Contracts

- User-facing docs and doctor output should prefer `Shuheng` and `shuheng*` commands.
- User-facing docs and doctor output must not advertise `ga-tui*` aliases.
- Protocol-level identifiers keep their current stable values until an explicit migration task exists.
- Core shim discovery should search both `Shuheng` and historical `GenericAgent-TUI` checkout directory names.

### 4. Validation & Error Matrix

- Missing `shuheng*` console script in `pyproject.toml` -> packaging regression.
- Public `ga-tui*` console script in `pyproject.toml` -> brand regression.
- Doctor output says primary launch is `ga-tui` -> brand regression.
- Doctor output mentions a `ga-tui` compatibility alias -> brand regression.
- Runtime strings identify the main orchestrator only as `GA-TUI` -> product identity regression.
- Exit prompts or terminal shutdown messages mention `ga tui` -> brand regression.

### 5. Good/Base/Bad Cases

- Good: `shuheng-check --root <GenericAgent>` reports `Shuheng root` and `Launch without core patches: shuheng` without advertising a `ga-tui` alias.
- Base: OMP host tools keep names such as `ga_tui_query` because they are protocol compatibility tool ids.
- Bad: Re-adding public `ga-tui*` commands or exit messages while the product is Shuheng-only.
- Bad: Renaming `ga_tui_query`, `GA_TUI_*`, or `ga-tui.query.v1` in a brand-only task, because that breaks external clients without a schema migration.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `pyproject.toml` contains all primary `shuheng*` scripts and no public `ga-tui*` scripts.
- Tests must assert integration doctor report prefers `shuheng` and does not mention `ga-tui` as a compatibility command.
- Tests must assert exit prompts, exit reasons, and terminal shutdown text use Shuheng/枢衡 instead of `ga tui`.
- `python3 -m compileall -q src scripts`, `python3 scripts/check_policy_gates.py`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

Keep advertising `ga-tui` as a user-facing compatibility command, or rename every `ga-tui`, `ga_tui`, and `GA_TUI` token in one sweep.

#### Correct

Expose only `shuheng*` user commands and Shuheng/枢衡 UI strings, while preserving legacy protocol/module/env names until a dedicated compatibility migration is designed.

## Scenario: Session History Titles Ignore Process Summaries

### 1. Scope / Trigger

- Trigger: Runtime providers can emit foldable process blocks such as `**LLM Running (Turn 1) ...**`, `<summary>specific thinking excerpt</summary>`, legacy `<summary>OMP 思考</summary>`, `<thinking>...</thinking>`, tool-call blocks, and tool result fences.
- Applies to: session history preview caching, sidebar title fallback, restored-session preview messages, AI-generated title/description context, and `session_meta.json` cache reuse.
- Non-goal: This does not remove process summaries from the main transcript renderer. Folded process summaries remain visible as process UI labels when rendering the assistant message itself.

### 2. Signatures

- History row source: `cached_session_rows(state, exclude_pid)` returns `(path, last_user_at, preview, rounds, description)`.
- Sidebar display source: `load_history()` maps `session_names.json` or `preview` into `state.history_names`.
- Process filtering helpers: `session_preview_from_pairs()`, `session_response_preview_text()`, `session_summary_titles_from_text()`, and `history_cache_has_process_only_preview()`.

### 3. Contracts

- Process-only summaries must not become `preview`, `description`, `ui_preview_messages`, `state.history_names`, or AI title-generation context.
- If a response contains process markers, `<summary>` content belongs to process rendering, not session naming.
- For process-marked responses, sidebar title fallback should prefer the first user message, then visible final assistant prose.
- Existing cached metadata that already contains process-only preview text must be invalidated and recomputed from the raw model response file.
- Explicit user names in `session_names.json` win unless they are process-only labels such as `OMP 思考`.
- Automatic AI session titles should be re-evaluated whenever the user/assistant content signature changes, so each completed round can refine the visible session name.
- Main-runtime agents may maintain the current title by emitting `session.rename`; those model-owned title changes are recorded as `title_source:"ai"`.
- Manual `/rename` or history rename writes `title_source:"manual"` and must not be overwritten by later automatic AI title reviews.
- Standalone progress-dot deltas from OMP (`.` on its own line) are process noise and must not render in the transcript.
- Current OMP thinking process summaries should use a compact excerpt of the thinking text, not the fixed label `OMP 思考`.
- Legacy process blocks with `<summary>OMP 思考</summary>` should render a compact excerpt from the `<thinking>` body.

### 4. Validation & Error Matrix

- Raw response has `<summary>OMP 思考</summary>` plus final visible prose -> sidebar title uses the user task, not `OMP 思考`.
- Cached metadata has `preview:"OMP 思考"` and matching file mtime/size -> cache is treated stale and recomputed.
- AI title context includes a process block -> context includes user text and visible final prose, not hidden thinking text.
- AI title review sees a new content signature after another completed round -> a new title job can run and update the AI-owned session title.
- AI title review sees `title_source:"manual"` -> it does not start or overwrite the title.
- Main-runtime `session.rename` changes an unlocked AI-owned title -> title source remains `ai`; the same control against a manual title is skipped.
- Main transcript renderer sees process blocks -> folded process UI still shows the process label.
- Main transcript renderer sees a legacy thinking block plus a standalone `.` line -> renders the thinking excerpt and suppresses the dot line.
- Main transcript renderer sees multiple `LLM Running` blocks in one assistant message -> collapsed view shows one `过程组 G...` row, not one visible `过程 Turn ...` row per process block; intermediate progress prose stays inside the expandable group while the final user-facing reply remains visible outside the group.
- Main transcript renderer sees a substantive user-facing reply before later housekeeping process turns -> the substantive reply remains visible outside the collapsed group instead of being replaced by a short "nothing further" cleanup sentence.
- Main transcript renderer sees OMP `irc` tool results with `Reply from ...` payloads -> bounded IRC reply snippets remain visible outside the collapsed group while raw receipts, tool ids, and tool JSON stay folded.

### 5. Good/Base/Bad Cases

- Good: History row title is `修复左栏历史会话标题` while restored assistant preview says `已完成历史会话标题修复`.
- Good: Main transcript shows `过程 Turn 15: Let me observe the page...`, not `过程 Turn 15: OMP 思考`.
- Good: A long OMP research turn with many thinking/tool/status blocks renders as one expandable `过程组` plus the final report, not dozens of separate `过程 Turn` lines.
- Good: An OMP IRC demo shows the final conclusion and `IRC 回复` snippets from DemoAlpha/DemoBeta even if later turns only close the demo agents.
- Base: A normal non-process assistant `<summary>` can still be used as a title candidate.
- Bad: Sidebar `Recent` shows `OMP 思考`, `执行中`, or a tool-call label as the session title.
- Bad: Main transcript shows standalone `.` lines between process turns.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert OMP process summaries do not title history rows.
- The test must seed a stale `session_meta.json` cache with `preview:"OMP 思考"` to prove cache invalidation.
- The test must assert restored preview messages and AI title context exclude process-only summary and hidden reasoning.
- Tests must assert AI-owned session titles are reviewed again when content signatures change, while manual titles remain stable.
- Tests must assert model-owned `session.rename` updates are marked AI-owned and do not override manual titles.
- Tests must assert OMP thinking summaries use thinking excerpts, legacy `OMP 思考` summaries render from `<thinking>`, and standalone dot deltas/lines are suppressed.
- Tests must assert mixed OMP process turns, including thinking-only summaries, tool turns, and short progress prose, collapse into one expandable process group while the final response stays visible.
- Tests must assert a grouped OMP IRC exchange preserves the substantive conclusion and bounded `Reply from ...` snippets when later housekeeping turns are shorter.

### 7. Wrong vs Correct

#### Wrong

```text
SESSIONS
S01 OMP 思考
```

#### Correct

```text
SESSIONS
S01 修复左栏历史会话标题
```

## Scenario: History Curator Skill Command

### 1. Scope / Trigger

- Trigger: Users want categorized history to be summarized as a reusable skill workflow with progressive disclosure, memory-candidate extraction, and long-running subagent recommendations.
- Applies to: `/curate-history`, `/history-curate`, history index generation, category summaries, artifact refs, memory-candidate recommendation text, and persistent-subagent recommendation text.
- Non-goal: This command does not directly write long-term memory, does not directly create persistent subagents, and does not read full raw session logs before the curator asks for deeper disclosure.

### 2. Signatures

- Commands: `/curate-history [scope]` and `/history-curate [scope]`.
- Scope forms:
  - empty, `recent`, or `最近` -> recent visible sessions.
  - `all` or `全部` -> all visible sessions up to the bounded limit.
  - `pinned`, `pin`, or `置顶` -> pinned visible sessions.
  - `cat:<name>`, `category:<name>`, or `分类:<name>` -> sessions in a category.
  - `search:<query>`, `q:<query>`, or `查找:<query>` -> cached title/summary/category search.
  - `limit=N`, `--limit N`, `限制 N`, or trailing number -> bounded result count.
- Prompt builder: `history_curator_skill_prompt(state, raw_args)` returns `(prompt, artifact_ref, rows)`.
- Index writer: `write_harness_artifact("history-curation-index", ...)` stores the index under Shuheng-owned `AGENT_HARNESS_DIR`.

### 3. Contracts

- The first curator turn receives only history index fields and cached summaries: stable id, title, category, rounds, age, flags, evidence ref, source path, and cached description.
- The first curator turn must label the disclosure level as `index+cached_summary_only`.
- The generated prompt must include nested mental subskills: `history-classifier`, `category-digest`, `memory-curator`, and `subagent-recommender`.
- The curator output contract must include Category Digest, Memory Candidates, Archive Only / Do Not Memorize, Persistent Subagent Recommendations, and Needs Deeper Disclosure.
- Memory candidates are recommendation-only in this command. Any actual memory write must later go through `queue_curated_memory_candidate(...)` and human approval.
- Persistent subagent creation is recommendation-only in this command. Any actual creation must later use explicit `agent.create` with `lifecycle:"persistent"` or `persistent:true`.
- The curator may request deeper disclosure for at most 3 stable session ids per turn and must state why each raw session is needed.
- The command starts a main-agent task with source `user:history_curator_skill` and shows the literal command as the visible user message.
- The command must run its main runtime request in `runtime_context_mode:"lean"`: do not prepend the full Shuheng runtime context pack because the curation prompt already contains the scoped index, artifact ref, and governance rules.

### 4. Validation & Error Matrix

- No matching rows -> user-visible message says there is no history to curate and no main-agent task is started.
- Category scope with no matching category -> same empty-history behavior.
- Limit above maximum -> clamped to the command maximum.
- Hidden/deleted rows -> not included because `load_history()` and `session_meta` filtering remain the source of truth.
- Secret Vault unlocked -> normal command isolation blocks this command before it can read normal history.
- Curator says a memory should be stored -> it must still be output as a candidate, not appended to memory files.
- Curator says a long-running agent is useful -> it must still be output as a recommendation, not an executable creation control unless the user separately asks for creation.

### 5. Good/Base/Bad Cases

- Good: `/curate-history cat:Shuheng limit=5` creates a `history-curation-index` artifact and starts a main-agent task that only sees Shuheng category cached summaries.
- Good: The output proposes `Memory Candidates` with `evidence_refs:["session://..."]` and confidence, but does not write approved memory.
- Good: The output recommends a persistent `History Curator` subagent with role/profile/boundaries, but does not create it.
- Base: `/curate-history recent` summarizes the currently visible recent history list.
- Bad: The command reads every raw `model_responses*.txt` file before deciding which sessions matter.
- Bad: The command emits an executable persistent `agent.create` control block without a separate user request.
- Bad: The command appends directly to `subagents/*/memory.md`.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert category-scoped `/curate-history` builds an index artifact with only matching session rows.
- Tests must assert the generated prompt contains progressive disclosure rules, nested subskill names, candidate-only memory wording, and recommendation-only persistent-subagent wording.
- Tests must assert the command starts the main agent with source `user:history_curator_skill` and preserves the literal command as the visible user message.
- Tests must assert runtime-agent execution for this command does not prepend `[GA TUI Context Pack]` and records `runtime_context_mode:"lean"`.
- Tests must assert non-matching category scopes do not start a main-agent task.

### 7. Wrong vs Correct

#### Wrong

```text
/curate-history -> read all raw history -> append facts to memory.md -> create persistent agents automatically
```

#### Correct

```text
/curate-history cat:Shuheng limit=5 -> index artifact + cached summaries -> candidate recommendations + subagent recommendations -> user-approved follow-up actions
```

## Scenario: Running Indicator Rendering

### 1. Scope / Trigger

- Trigger: The visible main or subagent transcript contains an unfinished assistant message while `display_status(state)` is `running` or `aborting`.
- Applies to: `State.run_frame`, `RenderLine` metadata, `message_lines_cached()`, `draw_main()`, and the main curses event loop.
- Non-goal: This does not change runtime provider streaming, transcript persistence, token accounting, process folding, or session history naming.

### 2. Signatures

- Frame source: `RUN_FRAMES` and `running_indicator(frame)`.
- Cached line marker: `RenderLine.kind == "running_indicator"`.
- Visible row state: `State.running_indicator_rect`.
- Lightweight redraw helper: `draw_running_indicator_frame(stdscr, state)`.

### 3. Contracts

- `run_frame` must not be part of `message_render_cache_key()` or the `message_lines_cached()` key.
- Long assistant messages must not run through markdown/process rendering on every animation tick.
- Full `draw_main()` may render the current spinner frame from cached `RenderLine` metadata without mutating the cache.
- The main event loop must not set `state.dirty` solely because `run_frame` advanced.
- When the transcript spinner row is visible and the screen is otherwise clean, the animation tick may refresh only that row and then restore the input cursor.
- Lightweight spinner refresh must no-op when the spinner row is not visible, text selection is active, or a session popup is open.

### 4. Validation & Error Matrix

- `run_frame` changes from 0 to 1 -> message block cache keys and cached block object identities remain stable.
- Visible unfinished assistant message + clean screen + frame tick -> one row is updated and curses refreshes once.
- Hidden spinner row, active selection, popup, idle status, or aborted/finished message -> no lightweight row update.
- Terminal resize or full redraw -> `draw_main()` recomputes `State.running_indicator_rect` from currently visible lines.

### 5. Good/Base/Bad Cases

- Good: A long streaming OMP reply keeps the transcript cache stable while `[=     ] running...` animates smoothly.
- Base: A normal dirty redraw caused by input, scroll, history refresh, or clock refresh still redraws the whole TUI.
- Bad: Adding `run_frame` to the message cache key or setting `state.dirty = True` every 120ms.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert run-frame changes do not invalidate message block cache keys.
- Tests must assert a visible running indicator can be refreshed with a single row update and one curses refresh while preserving the cache and input cursor.

### 7. Wrong vs Correct

#### Wrong

```python
state.run_frame += 1
state.dirty = True
```

#### Correct

```python
state.run_frame += 1
draw_running_indicator_frame(stdscr, state)
```

## Scenario: OMP Runtime Permission Profiles

### 1. Scope / Trigger

- Trigger: OMP is used as the main GA-TUI runtime provider and receives a generated context pack.
- Applies to: `permissions_for_role()`, `build_context_pack()`, `build_main_runtime_context_pack()`, `format_context_pack_for_prompt()`, OMP runtime task requests, isolated OMP config generation, and OMP RPC extension-UI approval responses.
- Non-goal: This does not give OMP direct ownership of GA-TUI memory, approvals, ledgers, schedules, or system-level `~/.omp/agent` configuration.

### 2. Signatures

- Permission profiles: `standard`, `read_only`, `full`.
- OMP profile env override: `GA_TUI_OMP_PERMISSION_PROFILE`.
- Generic fallback env override: `GA_TUI_DEFAULT_PERMISSION_PROFILE`.
- OMP tool approval env override: `GA_TUI_OMP_APPROVAL_MODE=always-ask|write|yolo`.
- Default OMP main-runtime profile: `full`.
- Default OMP main-runtime role: `main_orchestrator`.
- Default subagent profile: `standard`.
- Default isolated OMP approval mode: `yolo`.

### 3. Contracts

- `standard` means role-derived permissions from `ROLE_TEMPLATES`.
- `read_only` means no write policy and no bash/browser/task write-capability expansion.
- `full` means the main OMP runtime context pack advertises practical read/write/search/bash/browser/eval/git/LSP/host-tool/task/artifact/memory-candidate capabilities.
- The main OMP context pack and runtime task request must identify the worker role as `main_orchestrator`, not `specialist`; bounded subagents keep their role-specific identities.
- `full` must keep `memory_write:"candidate_only"` and must not enable direct long-term memory writes.
- `full` means no runtime tool deny-list and no runtime approval-required list for the main OMP request; OMP tools run directly inside the isolated runtime directory.
- `build_main_runtime_context_pack()` must default to the OMP permission profile, which defaults to `full`.
- `build_context_pack()` for subagents must default to `standard` unless explicitly passed another profile.
- `format_context_pack_for_prompt()` must include `permission_profile` so OMP can answer capability questions without claiming read-only mode.
- OMP isolated runtime config must be written under the Shuheng-owned harness runtime directory and must not mutate the user's system OMP config.
- OMP isolated runtime config defaults `tools.approvalMode` to `yolo`, so OMP runtime tools do not stop for OMP approval prompts.
- If OMP still emits an RPC extension-UI approval prompt, it may be auto-approved when the active runtime request has `permission_profile:"full"` and the requested tool maps to an allowed capability.
- OMP RPC backend does not expose `raw_ask`; inline AI metadata jobs such as automatic title and description generation must skip OMP instead of surfacing UI errors.
- Sidebar session category is Shuheng-owned index metadata. When `raw_ask` is unavailable, Shuheng must still maintain a bounded local category fallback from visible user/assistant text, cached title/description, and existing category labels without opening an OMP metadata turn.
- Manual category metadata remains locked: `category_source:"manual"` must not be overwritten by AI or local automatic category refresh.

### 4. Validation & Error Matrix

- No env override + main OMP context -> `role:"main_orchestrator"`, `permission_profile:"full"`, `write_policy:"single_writer"`, full tool list, empty `tools_forbidden`, empty `approval_required_for`, and `memory_write:"candidate_only"`.
- No env override + main OMP runtime task request -> `role:"main_orchestrator"`, prompt contains `role: main_orchestrator` plus `permission_profile: full`, and the request carries the same full permission set.
- `GA_TUI_OMP_PERMISSION_PROFILE=read_only` + main OMP context -> `permission_profile:"read_only"`, `write_policy:"none"`, no bash in `tools_allowed`.
- Subagent context without an explicit profile -> `permission_profile:"standard"` and role-bounded tools.
- OMP isolated config generation -> `tools.approvalMode:"yolo"` and `PI_CODING_AGENT_DIR` under the Shuheng-owned harness.
- OMP RPC approval select for safe `bash` under full profile -> respond `Approve`.
- OMP RPC approval select for risky `rm -rf` under full profile -> respond `Approve`.
- OMP RPC approval select under `standard` profile -> respond `Deny`.
- OMP active session completes a normal task -> automatic title/description workers are not started through unsupported `raw_ask`, no `AI title: RuntimeError` appears, and sidebar category still lands in `session_meta.json` through the local fallback.
- OMP process summaries, hidden thinking text, tool calls, and `model_responses*.txt` basenames -> do not influence the local sidebar category.

### 5. Good/Base/Bad Cases

- Good: Main OMP runtime receives `role:"main_orchestrator"` and `permission_profile:"full"`, shows `write_policy:"single_writer"`, has an empty runtime deny/approval list, can use normal write/search/bash/browser capabilities, and still reports `memory_write:"candidate_only"`.
- Good: A role-bounded researcher subagent receives `permission_profile:"standard"` with `tools_allowed:["web","read"]` and `write_policy:"none"`.
- Good: An OMP-backed Shuheng sidebar-history bug session is categorized as `Shuheng` by the local fallback without calling `raw_ask`.
- Base: Operator sets `GA_TUI_OMP_PERMISSION_PROFILE=read_only`; OMP main runtime starts in compatibility mode and does not advertise bash/write tools.
- Base: Operator sets `GA_TUI_OMP_APPROVAL_MODE=always-ask`; command/config generation preserves the override.
- Bad: Main OMP runtime inherits `specialist` role permissions and tells users it only has `read, reason`.
- Bad: OMP is launched without the default `--approval-mode yolo`, causing runtime tools to stop for OMP approval prompts in the normal main-runtime path.
- Bad: `permission_profile:"full"` turns into direct long-term memory writes outside Shuheng-owned memory paths.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert default full main context with `role:"main_orchestrator"`, main runtime task request role/permissions/prompt/output-contract wiring, read-only env override, standard subagent context, isolated OMP approval mode, runtime provider metadata, and OMP RPC extension approval bridge behavior.
- `scripts/check_policy_gates.py` must assert OMP inline AI metadata generation is disabled when the backend marks `supports_raw_ask:false`.
- `scripts/check_policy_gates.py` must assert OMP/raw-ask-disabled sessions still get local sidebar categories, manual categories are not overwritten, and process summaries/hidden thinking do not decide the category.
- `python3 -m compileall -q src scripts` must pass.
- `python3 scripts/check_policy_gates.py` must pass.

### 7. Wrong vs Correct

#### Wrong

```text
permission_profile: standard
write_policy: none
tools_allowed: read, reason
```

#### Correct

```text
permission_profile: full
role: main_orchestrator
write_policy: single_writer
tools_allowed: read, reason, search, repo.read, repo.write, edit, write, test, bash, shell, browser, eval, python, javascript, web.search, web_search, git, lsp, artifact.read, artifact.write, host_tools, task, subagent.delegate, memory.candidate
tools_forbidden:
approval_required_for:
memory_write: candidate_only
```

## Scenario: OMP Native Session And Context Boundary

### 1. Scope / Trigger

- Trigger: Shuheng uses OMP as the main runtime provider and must restore sessions, show context usage, and persist history without replaying display transcripts as provider context.
- Applies to: `OhMyPiRpcAgent`, `restore_backend_and_recent_messages()`, session metadata, left status token lines, and OMP RPC state handling.
- Non-goal: This does not make OMP own Shuheng memory, session category metadata, history archive flags, approvals, or long-term memory writes.

### 2. Signatures

- OMP RPC state command: `{ "type": "get_state" }`.
- OMP RPC switch command: `{ "type": "switch_session", "sessionPath": "<absolute OMP session jsonl>" }`.
- OMP RPC compact command: `{ "type": "compact", "customInstructions"?: "<text>" }`.
- Provider attributes: `native_session_file`, `native_session_id`, `native_session_name`, `native_message_count`, `native_auto_compaction_enabled`, and `native_context_usage`.
- Shuheng metadata fields: `runtime_provider:"ohmypi"`, `ohmypi_session_file`, `ohmypi_session_id`, `ohmypi_session_name`, `ohmypi_message_count`, `ohmypi_context_usage`, and `ohmypi_updated_at`.

### 3. Contracts

- OMP provider startup and task completion must refresh native state with `get_state`.
- `contextUsage.tokens`, `contextUsage.contextWindow`, and `contextUsage.percent` from OMP are the source of truth for OMP context display.
- When an OMP-backed Shuheng session completes, Shuheng stores the OMP `sessionFile` in `session_meta.json` for the visible `model_responses*.txt` row.
- Restoring a history row with an existing `ohmypi_session_file` must call OMP `switch_session` and must not parse the visible `model_responses*.txt` transcript back into provider history.
- If the OMP session file is missing or switching fails, Shuheng may fall back to legacy transcript parsing, but the fallback must be explicit and must not be treated as the native OMP path.
- Shuheng left history remains a Shuheng-owned UI/index surface; the provider context remains OMP's active `SessionManager` state.

### 4. Validation & Error Matrix

- `get_state.contextUsage` is present -> token panel shows OMP context tokens/window instead of `tracker unavailable`.
- `get_state.model.contextWindow` is present -> backend `contextWindow` and `context_win` mirror it.
- `ohmypi_session_file` exists -> restore calls `switch_runtime_session()` and avoids `reset_runtime_session()` plus backend-history replay.
- `ohmypi_session_file` missing -> restore uses the legacy Shuheng transcript fallback.
- `switch_session` returns `cancelled:true` or RPC error -> restore falls back and includes a visible native-switch failure note.
- `compact` succeeds -> provider refreshes `get_state` before exposing updated context usage.

### 5. Good/Base/Bad Cases

- Good: A restored OMP history row switches to `/.../sessions/<session>.jsonl`, then the next prompt continues from OMP's compacted provider context.
- Good: The left status panel shows `ctx 123k/1.00M 12%` from OMP `contextUsage`.
- Base: A legacy Shuheng-only transcript has no OMP session metadata and still restores with the old parser.
- Bad: Restoring an OMP row builds backend history from folded process/UI transcript text.
- Bad: Token display estimates context from transcript characters when OMP has supplied `contextUsage`.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert OMP provider consumes `get_state.contextUsage`, `sessionFile`, `sessionId`, `sessionName`, and `messageCount`.
- Tests must assert `switch_runtime_session()` sends `switch_session` with `sessionPath` and refreshes native state.
- Tests must assert `compact_runtime_session()` refreshes native context usage after compacting.
- Tests must assert restoring a Shuheng row with `ohmypi_session_file` uses native switch and does not call `reset_runtime_session()`.
- Tests must assert OMP token panel lines render OMP `contextUsage` even when Shuheng's cost tracker is unavailable.

### 7. Wrong vs Correct

#### Wrong

```text
restore -> parse model_responses*.txt -> backend.history = parsed visible transcript -> prompt
token panel -> estimate context from Shuheng transcript chars
```

#### Correct

```text
restore -> OMP switch_session(sessionPath=ohmypi_session_file) -> prompt
token panel -> OMP get_state.contextUsage
```

## Scenario: ga-control v2 Delegation

### 1. Scope / Trigger

- Trigger: Main-agent TUI controls, subagent creation, task planning, and subagent delegation must use the `ga-control.v2` / `agenttask.v2` contract.
- Applies to: hidden control blocks emitted by the main agent, JSON code-fence controls in recovery paths, auto-continuation prompts, and policy-gate regression tests.
- Historical markup cleanup belongs in quarantine compatibility code only; it must not define executable external protocol behavior.

### 2. Signatures

- Hidden block: `<ga-control>{...}</ga-control>`
- Fenced block: ````ga-control`
- Implementation module: `src/ga_tui/control_protocol.py` owns the current protocol regexes, schema constants, action sets, JSON repair/parsing, extraction, stripping, lifecycle/reuse field parsing, and v2-to-internal-action coercion.
- Execution module: `src/ga_tui/app.py` may re-export protocol helpers for compatibility, but state-mutating execution functions stay in `app.py` unless they are extracted behind an explicit state boundary.
- Batch envelope:

```json
{
  "schema_version": "ga-control.v2",
  "actions": []
}
```

- Single action item:

```json
{
  "schema_version": "agenttask.v2",
  "action": "delegate.create"
}
```

### 3. Contracts

- `ga-control.v2.actions[]` accepts strong typed dotted action names only.
- Supported session actions: `session.pin`, `session.unpin`, `session.category`, `session.filter`, `session.clear_filter`, `session.collapse_category`, `session.expand_category`, `session.archive`, `session.unarchive`, `session.delete`, `session.rename`, `session.show_archived`, `session.hide_archived`.
- Supported task actions: `task.plan.create`, `task.update`, `task.done`, `task.start`, `task.fail`, `task.cancel`.
- Supported agent actions: `agent.create`, `agent.profile.update`, `agent.role.update`, `agent.model.update`, `agent.stop`, `agent.delete`.
- Supported delegation action: `delegate.create`.
- Supported memory action: `memory.candidate`.
- `delegate.create` must carry `routing`, `work_order`, `capability_contract`, `context_contract`, and `output_contract`.
- `delegate.create.work_order.objective` is the policy-gate source of truth. Capability fields such as `tools_forbidden:["deploy","email.send"]` must not trigger deployment or external-send approval by themselves.
- `agent.create` is ephemeral by default. Long-running, scheduled, recurring, or dedicated responsibilities must be expressed with explicit structured fields such as `lifecycle:"persistent"` or `persistent:true`; the runtime must not infer lifecycle from `name`, `profile`, visible prose, or other natural-language descriptions.
- Reuse intent must be explicit. `reuse_policy:"force_new"` / `force_new:true` forces a new agent; visible prose such as "do not reuse" is not a runtime signal unless the model also emits the structured field.
- Plan binding must be explicit. Controls that belong to a plan step must carry `plan_step_id`, `parent_task_id`, or an equivalent explicit step reference; the runtime must not bind steps by matching words like "self-introduction", "chat", or "summary".
- Executable `<ga-control>` blocks are only for real operations. Capability explanations, tutorials, and examples must not include literal executable tags; use escaped text such as `&lt;ga-control&gt;...&lt;/ga-control&gt;` or show only the JSON payload.
- Automatic current-session title maintenance is an allowed `session.rename` control exception: the main runtime may emit it at the end of a normal reply when the title is stale or misleading, and must stay silent when the title is already accurate.
- When a real control block is needed, append it after all user-visible prose. Do not place hidden controls in the middle of a visible section, because stripping the control block will leave the visible answer looking truncated.
- Inline-code labels such as `` `<ga-control>` `` in visible prose are not executable control starts and must not consume a later real closing tag.
- `install_tui_control_hint()` must replace any previous GenericAgent-TUI hint block before installing the current `ga-control.v2` hint, and repeated installation must leave exactly one current hint block per backend prompt.
- Protocol parser helpers must have one source of truth in `src/ga_tui/control_protocol.py`; do not redefine `extract_tui_controls()`, `strip_tui_controls()`, `lifecycle_is_persistent()`, `agenttask_*()` helpers, or schema/action constants inside `app.py`.
- `src/ga_tui/control_protocol.py` must not import curses, GenericAgent runtime classes, or mutable TUI `State`. It may depend on quarantined compatibility cleanup from `compat_legacy.py` to strip retired markup without making retired vocabulary executable.

### 4. Validation & Error Matrix

- Missing `schema_version:"ga-control.v2"` on a batch envelope -> no controls are extracted.
- Missing `schema_version:"agenttask.v2"` on a standalone action -> no controls are extracted.
- Unknown action -> ignored during extraction.
- Historical hidden markup -> stripped by quarantine compatibility cleanup only, not executed.
- Previous system hint block present in a backend extra prompt -> removed before the current hint is installed.
- Current hint already present in a backend extra prompt -> do not append another copy.
- Invalid JSON -> ignored.
- `agent.create` with explicit lifecycle markers such as `lifecycle:"ephemeral"` / `temporary:true` -> creates an ephemeral session agent.
- `agent.create` with recurring/daily/archive-building responsibility language but without explicit persistent lifecycle fields -> remains ephemeral.
- `agent.create` with `lifecycle:"persistent"` / `persistent:true` -> creates a persistent subagent under `SUBAGENTS_DIR`.
- `ga-control` JSON that only misses trailing `}` / `]` closers -> repair the missing tail and execute if it parses into known actions.
- Visible prose containing inline-code `` `<ga-control>` `` followed by a real control block -> parse and execute only the real control block, keep the inline label visible, and do not report parse_error.
- Unrepairable `ga-control` JSON -> add an `Agent 控制结果` parse-error message instead of silently swallowing the control block.
- `delegate.create` without a resolvable target -> runtime reports missing subagent target.
- `agent.delete` on a running or aborting subagent -> runtime refuses deletion and asks for a stop first.
- `agent.delete` on an idle subagent -> soft-delete from the TUI list, retain the original directory for audit, and persist `deleted:true`.
- Risky work-order objective -> policy gate queues or rejects according to policy rules.

### 5. Good/Base/Bad Cases

- Good: Batch envelope creates a plan, creates a researcher, then delegates with full routing/work/output contracts.
- Good: A user asks "what can subagents do?" and the assistant answers in visible prose without emitting `<ga-control>`.
- Base: Single `agenttask.v2` action in a JSON fence is extracted only when the action is known.
- Bad: A visible "example" section contains a literal `<ga-control>` block; the runtime will execute and strip it, leaving the section blank.
- Base: A visible diagnosis says `` `<ga-control>` 标签没正确闭合 `` and then appends a real `<ga-control>{...}</ga-control>` block; the inline label is display text only.
- Bad: Bare JSON without the required current schema envelope is ignored.
- Bad: A current envelope with an unknown or non-dotted action name is ignored by the generic schema boundary.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `ga-control.v2` extraction, JSON-fence extraction, current hint install de-duplicates and replaces previous hints, auto-continuation prompt examples, subagent creation, explicit lifecycle handling, soft deletion, delegation, secret-control isolation, and policy-gate behavior.
- Quarantine checks may assert that historical hidden markup is stripped but must not treat it as an executable protocol.
- `scripts/check_policy_gates.py` must assert common missing-tail JSON repair for `<ga-control>` and visible parse-error reporting for unrepairable control JSON.
- `scripts/check_policy_gates.py` must assert inline-code `<ga-control>` labels do not capture later real control blocks.
- `scripts/check_policy_gates.py` must assert `app.py` re-exports key protocol helpers from `ga_tui.control_protocol` and that the protocol module does not import curses.
- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/control_protocol.py scripts/check_policy_gates.py` must pass.
- `python3 scripts/check_policy_gates.py` must pass.
- `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass when the sibling GenericAgent checkout exists.

### 7. Wrong vs Correct

#### Wrong

```json
{"schema_version":"agenttask.v2","action":"delegate_create","target":"研究员","prompt":"查一下这个库"}
```

#### Correct

```json
{
  "schema_version": "agenttask.v2",
  "action": "delegate.create",
  "routing": {
    "mode": "agent_as_tool",
    "selected_agent": "研究员",
    "target_selector": {
      "role": "researcher",
      "capabilities_required": ["web.search", "source.verify"],
      "reuse_policy": "prefer_existing",
      "security_context": "standard"
    }
  },
  "work_order": {
    "objective": "查一下这个库",
    "success_criteria": ["cite evidence", "return risks"],
    "stop_condition": "return structured result and stop"
  },
  "capability_contract": {
    "tools_allowed": ["web.search", "read"],
    "tools_forbidden": ["repo.write", "deploy", "email.send"],
    "write_policy": "none",
    "max_subagents": 0
  },
  "context_contract": {
    "history_mode": "summary",
    "artifact_reference_only": true,
    "include_raw_logs": false
  },
  "output_contract": {
    "format": "structured_markdown",
    "required_sections": ["summary", "findings", "evidence_refs", "risks", "artifact_refs", "confidence"],
    "schema_validation": "strict"
  }
}
```

## Scenario: Temporary Subagent Owner Fallback

### 1. Scope / Trigger

- Trigger: Temporary subagents are created or reloaded while the active UI session has no durable session key.
- Applies to: `/agent new --temp ...`, `agent.create` with an ephemeral lifecycle, `create_subagent()`, `load_subagents()`, `subagent_home_dirs_for_session()`, and `/agent ask <id|name> ...`.
- Non-goal: This does not promote temporary subagents to persistent storage and does not hydrate long-term memory.

### 2. Signatures

- Temporary subagent root: `TEMP_SUBAGENTS_DIR`.
- Empty-session fallback owner: `current`.
- Empty-session path shape: `TEMP_SUBAGENTS_DIR/current/<agent_id>/meta.json`.
- Session-keyed path shape: `TEMP_SUBAGENTS_DIR/<active_ui_session_key>/<agent_id>/meta.json`.

### 3. Contracts

- `create_subagent(..., persistent=False)` must compute the temp owner as `active_ui_session_key(state) or "current"`.
- `subagent_home_dirs_for_session(state)` must inspect the same temp owner expression as creation: `active_ui_session_key(state) or "current"`.
- Persistent subagents under `SUBAGENTS_DIR` are always loaded independently of the temp owner.
- A keyed TUI session must load only its keyed temp owner and must not load the `current` fallback temp subagents.
- Empty-session fallback temp subagents remain non-persistent and must keep `persistent:false` in metadata/runtime state.

### 4. Validation & Error Matrix

- Empty active session key + temp subagent created -> metadata stored under `TEMP_SUBAGENTS_DIR/current/...`.
- Empty active session key + `load_subagents()` -> the `current` temp owner is scanned and the subagent resolves by id and name.
- Keyed active session + `load_subagents()` -> only that keyed temp owner is scanned; `current` fallback temp agents remain hidden.
- Missing temp owner directory -> no error and no temp subagents loaded.

### 5. Good/Base/Bad Cases

- Good: `/agent new --temp reviewer:TUI-Smoke | ...` creates `tmp-tui-smoke-...` under `TEMP_SUBAGENTS_DIR/current/...`; `/agent ask tmp-tui-smoke-... ...` starts the subagent in the same TUI session.
- Base: A persistent subagent continues to load from `SUBAGENTS_DIR` regardless of session key.
- Bad: Creation writes to `current` but reload only scans keyed owner directories, causing `/agent ask` to report `找不到子 agent` immediately after creation.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert empty-session temp subagent creation writes under the `current` temp owner.
- Tests must clear in-memory `state.subagents`, call `load_subagents()`, and assert resolution by both id and display name.
- Tests must assert a keyed state does not load a temp subagent from the `current` fallback owner.
- Real TUI smoke should create a temp subagent and immediately run `/agent ask <created-id> ...` without a missing-subagent error.

### 7. Wrong vs Correct

#### Wrong

```python
owner = active_ui_session_key(state)
if owner:
    temp_root = os.path.join(TEMP_SUBAGENTS_DIR, owner)
```

#### Correct

```python
owner = active_ui_session_key(state) or "current"
temp_root = os.path.join(TEMP_SUBAGENTS_DIR, owner)
```

## Scenario: Unified Model Command Surface

### 1. Scope / Trigger

- Trigger: The TUI model command surface must expose one visible command while preserving compatibility for older muscle-memory commands.
- Applies to: command help, command completion, direct command execution, model-manager rendering, model config persistence, model probing, model health checks, current-session switching, and default-model selection.
- Non-goal: This does not change `mykey.py` storage shape, provider API probing endpoints, or GenericAgent runtime model semantics.

### 2. Signatures

- Visible TUI command: `/model`
- Hidden compatible execution aliases: `/llm`, `/models`
- Main entrypoint: `open_model_manager(stdscr, state, manage_configs=True)`
- Rendering entrypoint: `draw_model_manager(..., active_category="<provider-tab-label>")`
- Category helpers: `model_entry_category(entry)`, `model_entry_categories(entries)`, `model_entry_indices_for_category(entries, category)`
- Model-manager virtual category helpers: `model_manager_category_index(entries, recent_names, health)`, `model_manager_categories(entries, recent_names)`, `model_manager_entry_indices_for_category(entries, category, recent_names)`, `model_manager_category_status(entries, category, health, recent_names)`

### 3. Contracts

- `COMMANDS` must include `/model` exactly once for the model surface.
- `COMMANDS` must not include `/llm` or `/models`; hidden aliases execute only through explicit command handling.
- `command_matches("/mo", state)` may return `/model`; `command_matches("/ll", state)` and `command_matches("/models", state)` must return no model alias rows.
- `/model`, `/llm`, and `/models` all open the unified model manager with config-management actions enabled.
- `/model` add/edit forms must expose a manual `context_win` field after the model id; saving must persist it as an integer in the existing model config entry.
- The unified manager must keep current-session switching, default selection, recent-model jumping, add/edit/delete, model extraction, single-model test, batch health check, and reload actions.
- Model rows are grouped by concrete provider tabs, not broad protocol categories.
- Provider labels must render as a vertical provider rail inside the model manager, with model rows rendered beside the rail. Do not collapse providers back into one horizontal `供应商 Tabs: A / B / C` line.
- Recent/frequently used models must render as a `常用` virtual rail category parallel to provider categories when matching configured models exist.
- Provider rail colors must summarize category state: configured/no-known-failure is blue, no configured model is grey, and any known failed health/test result is yellow.
- Hot rendering/navigation paths must use a precomputed model-manager category index instead of recalculating provider category membership once per rail row.
- Provider tabs must include configured providers plus the common-provider set derived from template order: `Anthropic`, `OpenAI`, `DeepSeek`, `Kimi`, `Qwen`, and `Zhipu` when those provider templates exist.
- Known provider identity should prefer normalized provider-template `apibase` matches, then provider/template name matches. Unknown/custom providers should fall back to a stable endpoint host label or config display name.
- Non-common template providers must not appear as empty tabs; they appear only after the user configures a model/API for that provider.
- Generated `mykey.py` comments and user-facing empty-state errors must point users to `/model`, not `/llm`.

### 4. Validation & Error Matrix

- User types `/llm` or `/models` -> open unified `/model` manager as a hidden compatibility alias.
- User requests command completion for `/ll` or `/models` -> do not show hidden aliases.
- No configured models -> `/model` manager displays an empty-state message that says to add a provider/API with `/model`.
- User edits `Context Win` -> the saved `context_win` value survives `mykey.py` round-trip and is available to runtime providers.
- Selected row belongs to a different active tab after reload/edit/delete -> normalize selection to the first visible row in the active category.
- Active provider tab has no visible rows -> display a no-models-in-provider message and keep navigation safe.
- Active `常用` tab -> display configured recent models in recent order and keep provider switching/navigation behavior unchanged.
- Many provider tabs -> vertical rail scrolls around the active provider without changing model-selection up/down behavior.
- Runtime cannot find a named model -> error tells the user to reload from `/model`.

### 5. Good/Base/Bad Cases

- Good: `/model` opens one panel where the user can switch the current dialogue model, set the default, add a provider, extract provider models, test a model, and batch validate all models grouped by supplier.
- Good: `/model` lets a user set `context_win:1050000` for a large-window OpenAI-compatible model without editing `mykey.py` by hand.
- Good: Providers render as a left-side vertical list, and the filtered model list renders to the right.
- Good: `常用` appears as a peer rail item when recent configured models exist, while empty common providers stay grey until configured.
- Good: DeepSeek and OpenAI-compatible entries with known template base URLs appear under `DeepSeek` and `OpenAI`, not together under one broad `OpenAI` protocol category.
- Base: `/llm` and `/models` still work for users who type them directly, but they are absent from `/help`, README command tables, and command completion.
- Base: A custom endpoint such as `https://api.example.invalid/v1` appears under a stable `example.invalid` tab.
- Bad: `/llm` appears as a normal command row, because that splits the visible command ontology again.
- Bad: `/model` opens a switch-only panel that cannot add/edit/delete or probe provider models.
- Bad: The model panel shows every known provider template as an empty tab.
- Bad: Provider labels are rendered as one long horizontal tab line that truncates useful providers on narrower terminals.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `/model` is present in `COMMANDS` and `/llm` / `/models` are absent.
- `scripts/check_policy_gates.py` must assert `/mo` completes to `/model` and hidden aliases do not complete.
- `scripts/check_policy_gates.py` must assert `/llm`, `/model`, and `/models` help text describes the unified manager and compatibility aliases.
- `scripts/check_policy_gates.py` must assert `/model` exposes `context_win` and saving/reloading model config preserves it.
- `scripts/check_policy_gates.py` must assert model category helpers group OpenAI, DeepSeek, custom endpoint, common-provider, and non-common configured providers correctly.
- `scripts/check_policy_gates.py` must assert the model manager renders a vertical provider rail and does not render the old horizontal `供应商 Tabs:` line.
- `scripts/check_policy_gates.py` must assert the model manager exposes `常用` as a virtual category and renders provider rail status colors for configured, empty, and failed categories.
- `scripts/check_policy_gates.py` must assert `draw_model_manager(...)` can render from a supplied precomputed category index without recalculating provider categories.
- README command tables must document `/model` as the single visible model command.

### 7. Wrong vs Correct

#### Wrong

```python
COMMANDS = [
    ("/llm", "", "manage model configs", True),
    ("/model", "", "switch current model", True),
    ("/models", "", "alias for /model", True),
]
```

#### Correct

```python
COMMANDS = [
    ("/model", "", "manage/switch/extract/test/default", True),
]

if text.strip().lower() in {"/llm", "/models", "/model"}:
    open_model_manager(stdscr, state, manage_configs=True)
```

## Scenario: TUI Read-Only Query Tools

### 1. Scope / Trigger

- Trigger: The main agent needs current TUI dashboard facts before creating, reusing, stopping, or delegating to subagents.
- Applies to: GenericAgent tool schema injection, GenericAgentHandler `do_*` dispatch methods, bound TUI `State`, shared task ledger queries, approval summaries, artifact metadata, and capability discovery.
- Non-goal: These tools must never mutate sessions, tasks, agents, approvals, artifacts, memory, or files. Real state changes still require `ga-control.v2`.

### 2. Signatures

- Tool names exposed to the model are snake_case function tools: `agent_list`, `agent_get`, `agent_match`, `task_list`, `task_get`, `approval_list`, `artifact_list`, `capability_list`.
- User-facing documentation may refer to dotted names: `agent.list`, `agent.get`, `agent.match`, `task.list`, `task.get`, `approval.list`, `artifact.list`, `capability.list`.
- `agent_get` requires `target`.
- `agent_match` requires `objective`.
- `task_get` requires `task_id`.

### 3. Contracts

- Every response is JSON-safe and starts with `schema_version:"ga-tui.query.v1"` plus `status:"ok"` or `status:"error"`.
- Query tools are installed by wrapping `agentmain.load_tool_schema()` and appending TUI schemas idempotently after every GenericAgent schema reload.
- Query handlers are installed by patching `agentmain.GenericAgentHandler` with `do_<tool_name>` methods.
- Runtime state is provided through `agent._ga_tui_state`; if a handler has no bound state, the tool returns an error response instead of guessing.
- `agent_list` returns bounded agent records: id, name, role, lifecycle, status, busy reason, security context, capabilities, write policy, permissions, queues, active task refs, profile summary, interaction modes, and identity contract.
- `agent_get` returns one detailed bounded record with profile summary/full bounded profile, memory summary, output contract, queue previews, recent assigned tasks, interaction modes, and identity contract.
- `agent_match` scores current agents using structured selectors only: explicit target, role, capability, security context, lifecycle, and busy state. It must not score arbitrary natural-language objective/profile similarity.
- The identity contract must distinguish same-agent routing from persona cloning: a reply only counts as coming from a persistent subagent when it is routed to that existing `agent_id` through Shuheng subagent task/direct-chat controls; OMP native task spawn, IRC demo agents, or copied profile/persona workers must be reported as clones or simulations.
- `task_list` returns latest ledger rows with terminal rows hidden by default unless `include_completed:true`.
- `task_get` returns latest row, bounded history, child tasks, recent traces, approval refs, and artifact refs.
- `approval_list` returns approval metadata and payload keys only; it must not inline raw approval payload bodies.
- `artifact_list` returns artifact metadata and refs only; artifact contents must be read by explicit artifact/file reads.
- `capability_list` returns role templates, permissions, write policies, and registered agents from the gateway capability registry.

### 4. Validation & Error Matrix

- Missing bound TUI state -> `status:"error"` with a clear runtime-binding message.
- `agent_get` target missing, ambiguous, or not found -> `status:"error"`.
- `agent_match` without objective -> `status:"error"`.
- `task_get` without `task_id` or unknown task -> `status:"error"`.
- Repeated `install_tui_query_runtime()` calls -> no duplicate tool schemas and no duplicate handler side effects.
- GenericAgent model switch or `load_tool_schema()` reload -> query schemas are re-appended exactly once.
- Secret Vault unlocked -> subagent query refresh uses Secret subagents instead of normal `SUBAGENTS_DIR`.
- Persistent subagent has `runtime_loaded:false` -> `agent_get` still exposes same-agent task/direct-chat routes, but the model must not claim a separate spawned persona is that persistent agent.

### 5. Good/Base/Bad Cases

- Good: Before answering "which subagent should handle this?", call `agent_match`, then emit `delegate.create` only if execution is intended.
- Good: Before saying "that task is blocked", call `task_get` and `approval_list` to inspect ledger and approval gates.
- Good: To test whether a persistent steward can answer, target its existing `agent_id` with Shuheng subagent task/direct-chat controls and report the returned `assigned_agent`/`subagent-chat:<id>` lane.
- Base: A capability explanation calls `capability_list` or `agent_list` and answers in prose without a control block.
- Bad: A query tool creates an agent, starts a task, approves a gate, writes memory, or reads full artifact contents.
- Bad: The model emits `<ga-control>` while only explaining available subagent capabilities.
- Bad: The model spawns a new OMP/IRC worker with a copied steward profile and reports "the persistent steward replied" instead of "a clone/persona simulation replied".

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert all query tool schemas are installed exactly once.
- Tests must assert handler methods exist and return `StepOutcome` with `next_prompt:"\n"`.
- Tests must assert `agent_list`, `agent_get`, and `agent_match` expose current subagent records, interaction modes, identity contracts, clone warnings, and recommend reuse when a matching idle agent exists.
- Tests must assert `task_list` hides terminal tasks by default and includes them with `include_completed:true`.
- Tests must assert `task_get` returns latest ledger details and approval references.
- Tests must assert `approval_list` does not inline raw payload bodies.
- `python3 -m py_compile src/ga_tui/app.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```text
The model guesses there is no suitable researcher, creates another subagent, and delegates immediately.
```

#### Correct

```text
Call agent_match(objective="...", role="researcher", capabilities_required=["web.search", "read"]) first.
If the recommendation is reuse_existing, emit delegate.create targeting that agent.
If the recommendation is create_new and the user asked for execution, create a bounded agent and delegate with full agenttask.v2 contracts.
```

## Scenario: GenericAgent Provider Adapter Boundary

### 1. Scope / Trigger

- Trigger: GenericAgent-specific runtime integration code is needed for tool schema injection, `GenericAgentHandler` method patching, TUI state binding, control-hint installation, or agent lifecycle startup.
- Applies to: `src/ga_tui/genericagent_provider.py`, compatibility re-exports from `src/ga_tui/app.py`, runtime provider registration, model switching, subagent runtime preparation, query tools, and schedule tools.
- Non-goal: The provider module must not own TUI state mutation, curses rendering, ledgers, scheduler registries, Secret Vault storage, or subagent query implementation details.

### 2. Signatures

- Provider module: `src/ga_tui/genericagent_provider.py`.
- Runtime configuration entrypoint: `configure_genericagent_provider_runtime(agentmain, generic_agent_cls, step_outcome_cls, is_state, tool_handlers, thread_factory=...)`.
- Compatibility re-exports from `app.py`: `TUI_AGENT_CONTROL_HINT`, `TUI_QUERY_TOOL_SCHEMAS`, `TUI_SCHEDULE_TOOL_SCHEMAS`, `install_tui_query_runtime()`, `install_tui_control_hint()`, and `GenericAgentRuntimeAdapter`.
- Handler methods installed on `agentmain.GenericAgentHandler`: `do_agent_list`, `do_agent_get`, `do_agent_match`, `do_task_list`, `do_task_get`, `do_approval_list`, `do_artifact_list`, `do_capability_list`, `do_schedule_create`, and `do_schedule_list`.

### 3. Contracts

- `genericagent_provider.py` owns the active GenericAgent-facing control hint, query tool schemas, schedule tool schemas, tool schema injection, `agentmain.load_tool_schema()` wrapping, `GenericAgentHandler` patching, `_ga_tui_state` binding, `install_tui_control_hint()`, and `GenericAgentRuntimeAdapter`.
- `app.py` may re-export provider names for compatibility, but must not locally redefine the moved installers, handler patch functions, control-hint installer, or `GenericAgentRuntimeAdapter`.
- The provider module must not import `ga_tui.app`, curses, or mutable TUI `State`. App-layer behavior is injected through `configure_genericagent_provider_runtime()`.
- Tool handlers remain app-layer callbacks because they read TUI state, subagent registries, ledgers, approvals, artifacts, Secret Vault state, gateway capabilities, and scheduler registries.
- Repeated `install_tui_query_runtime()` calls must append each query/schedule schema at most once and must not add duplicate handler side effects.
- A GenericAgent tool schema reload must re-append TUI tool schemas exactly once.
- Handler methods must return the configured `StepOutcome` class with `next_prompt:"\n"`.
- `GenericAgentRuntimeAdapter.create_agent()` creates the configured GenericAgent class, installs the tool runtime, and sets `inc_out:true`; `prepare_agent()` installs tools and the current control hint; `start_agent()` starts `agent.run()` in a daemon thread.

### 4. Validation & Error Matrix

- Provider module imported before configuration -> runtime installation and adapter creation fail explicitly with a configuration error.
- Missing bound TUI state on a handler call -> injected app-layer tool callback returns the standard TUI tool/query error response.
- Unknown tool kind -> provider returns a JSON-safe `ga-tui.query.v1` error response instead of mutating state.
- Repeated provider configuration -> subsequent handler calls use the latest injected callback map because handler methods dispatch through provider runtime state.
- Provider source imports `ga_tui.app`, curses, or TUI `State` -> boundary violation.
- `app.py` locally defines moved GenericAgent glue after the extraction -> boundary violation.

### 5. Good/Base/Bad Cases

- Good: `app.py` configures the provider with `agentmain`, `GenericAgent`, `StepOutcome`, `isinstance(value, State)`, and a map of `tui_tool_*` callbacks; the provider installs schemas and handler methods.
- Good: Model switching calls the provider's compatibility re-exported `install_tui_query_runtime()` and `install_tui_control_hint()` after selecting the backend model.
- Base: A future runtime provider adds its own adapter without importing curses or TUI state classes.
- Bad: `app.py` defines a second local `GenericAgentRuntimeAdapter` or local `do_agent_list` patch method.
- Bad: `genericagent_provider.py` imports `ga_tui.app` to call `tui_tool_agent_list()` directly, creating a reverse dependency from provider to composition.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert app compatibility re-exports are identical to `ga_tui.genericagent_provider` names.
- Tests must assert moved functions and `GenericAgentRuntimeAdapter` have `__module__ == "ga_tui.genericagent_provider"`.
- Tests must assert `genericagent_provider.py` has no reverse import into `app.py` and no curses import.
- Tests must assert `app.py` no longer locally defines the moved GenericAgent glue functions or adapter class.
- Tests must preserve query/schedule schema idempotency, handler method presence, `StepOutcome(next_prompt:"\n")`, state-bound tool dispatch, and control-hint de-duplication checks.
- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/genericagent_provider.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# app.py
def install_tui_query_handler_methods():
    setattr(agentmain.GenericAgentHandler, "do_agent_list", ...)
```

#### Correct

```python
# app.py
configure_genericagent_provider_runtime(
    agentmain=agentmain,
    generic_agent_cls=GenericAgent,
    step_outcome_cls=StepOutcome,
    is_state=lambda value: isinstance(value, State),
    tool_handlers={"agent_list": tui_tool_agent_list},
)
```

## Scenario: Oh My Pi Runtime Provider

### 1. Scope / Trigger

- Trigger: GenericAgent-TUI integrates Oh My Pi as the experiment-branch default local runtime provider.
- Applies to: `src/ga_tui/ohmypi_provider.py`, runtime provider registration in `src/ga_tui/app.py`, runtime registry records, provider selection, Shuheng memory prompt injection, app-injected TUI host tool registration, typed host-tool routing, governed proposal routing, memory candidate signaling, runtime task request/event records, RPC queue/event mapping, and OMP usage-to-token-registry bridging.
- Non-goal: This provider must not own curses rendering, mutable TUI `State`, GenericAgent tool schema injection, TUI approval storage, scheduler registries, or first-class TUI subagent ledger mutation.

### 2. Signatures

- Provider module: `src/ga_tui/ohmypi_provider.py`.
- Provider id: `ohmypi`.
- Runtime adapter: `OhMyPiRuntimeAdapter(RuntimeAdapter)`.
- Queue-compatible wrapper: `OhMyPiRpcAgent`.
- Provider metadata helper: `ohmypi_provider_spec(root_dir, harness_dir, recent_models_path, schedules_path, binary=None, command=None)`.
- Provider-neutral runtime envelopes: `RuntimeTaskRequest` and `RuntimeTaskEvent` in `src/ga_tui/runtime.py`.
- RPC command helpers: `resolve_ohmypi_binary(binary=None)` and `ohmypi_rpc_command(binary=None, extra_args=None, append_system_prompt=None)`.
- Memory append prompt helpers: `write_ohmypi_memory_prompt(root_dir, harness_dir)` and `ohmypi_memory_prompt_path(harness_dir)`.
- Isolated runtime helpers: `ohmypi_runtime_root(harness_dir)`, `ohmypi_isolated_agent_dir(harness_dir)`, `ohmypi_config_path(agent_dir)`, `ohmypi_models_path(agent_dir)`, `write_ohmypi_runtime_files(...)`, and `ohmypi_subprocess_env(...)`.
- Isolated runtime records: `OhMyPiRuntimeConfig` and `OhMyPiRuntimeModel`.
- Compatibility TUI host tools exposed to OMP: `ga_tui_query` and `ga_tui_propose`.
- Typed TUI host tools exposed to OMP include `agent_list`, `agent_get`, `agent_match`, `task_list`, `task_get`, `approval_list`, `artifact_list`, `capability_list`, `schedule_list`, `memory_context_get`, `proposal_submit`, `memory_candidate_submit`, and `schedule_create`.
- Read-only host tool definition helper: `ohmypi_tui_readonly_host_tool_definitions()`.
- Typed read-only host tool definition helper: `ohmypi_typed_readonly_host_tool_definitions()`.
- Governed proposal host tool definition helper: `ohmypi_tui_proposal_host_tool_definition()`.
- Typed governed host tool definition helper: `ohmypi_typed_governed_host_tool_definitions()`.
- Combined host tool definition helper: `ohmypi_tui_host_tool_definitions()`.
- Combined host tool callback helper: `ohmypi_tui_host_tool_handler(state=None)`.
- Backward-compatible query callback helper: `ohmypi_tui_query_host_tool_handler(state=None)`.
- Environment keys:
  - `SHUHENG_HOME` overrides the Shuheng-owned storage root; legacy internal `GA_TUI_HOME` remains an accepted compatibility override.
  - unset `GA_TUI_RUNTIME_PROVIDER` selects `ohmypi` on this experiment branch.
  - `GA_TUI_RUNTIME_PROVIDER=genericagent` selects the fallback GenericAgent adapter.
  - `GA_TUI_OHMYPI_BIN` overrides the executable.
  - `GA_TUI_OHMYPI_ARGS` appends shell-split extra CLI arguments.
- OMP subprocess environment:
  - `PI_CODING_AGENT_DIR` must point to the Shuheng-owned isolated OMP agent directory under `${AGENT_HARNESS_DIR}/runtime/ohmypi/agent`.
  - Generated per-process API key env vars use `GA_TUI_OMP_API_KEY_<digest>` and must be passed only through the OMP child process env.
- Default RPC command shape: `<resolved-omp> --mode rpc --no-title --approval-mode yolo --append-system-prompt <generated-memory-file>`.

### 3. Contracts

- `OhMyPiRpcAgent.put_task(prompt, source="", images=None)` must return a `queue.Queue` immediately and remain as the compatibility shim for existing hot paths.
- `OhMyPiRpcAgent.put_runtime_task(RuntimeTaskRequest)` must accept provider-neutral task requests and preserve `task_id`, `provider_id`, `agent_id`, `role`, `objective`, `source`, `context_pack_ref`, artifact refs, permissions, approval policy, output contract, and metadata in normalized runtime events.
- Durable `runtime.task_request.v1` records must not store the full prompt; they store bounded `prompt_preview`, `prompt_chars`, and artifact/context refs. The full prompt remains in-memory for runtime dispatch only.
- Oh My Pi RPC `message_update` frames with `assistantMessageEvent.type:"text_delta"` map to queue items shaped as `{"next": <delta>, "source": "ohmypi"}`.
- OMP may emit a standalone `"."` text delta as a tool-turn placeholder or as real punctuation inside normal prose, numbered lists, or decimals. The provider must delay standalone dot deltas until the next visible text delta: append them to the next text delta for normal prose, drop them when a process/tool block starts, and flush them before a normal terminal completion.
- Oh My Pi non-final process frames must be normalized into the existing GenericAgent-TUI foldable process text protocol instead of adding a second renderer. The emitted text uses `**LLM Running (Turn N) ...**`, `<summary>...</summary>`, tool args fences, and result fences that `render_assistant_text(..., fold_process:true)` already understands.
- OMP `message_update` thinking/reasoning deltas are buffered and emitted as a bounded `<thinking>...</thinking>` process turn before the next visible text/tool/final event. The final assistant reply must remain normal assistant text, not hidden inside a thinking block.
- OMP `tool_execution_start` / `tool_execution_end` frames and GA-TUI `host_tool_call` / `host_tool_result` bridge activity must become bounded, redacted tool process turns so tool args/results are folded by default while the final reply remains visible.
- Generated OMP context packs, context refs, memory append prompts, and `memory_candidate_submit` descriptions must tell OMP to finish every user turn with a normal user-facing reply in the user's language. Tool results, `Result:` status lines, and memory-candidate submitted/deferred notices must not replace the final reply.
- Generated OMP context packs, context refs, and memory append prompts must mark Shuheng context metadata as internal execution metadata. Follow-up pronouns such as `这个`, `这个东西`, `它`, `this`, or `that` must resolve to the recent visible conversation/task topic unless the user explicitly names the context pack/ref.
- Generated OMP context packs, context refs, and memory append prompts must treat explicit user requests to create a persistent/long-term Shuheng agent as an executable control requirement: success requires `agent.create` with `lifecycle:"persistent"` / `persistent:true`, or reuse of a matching existing persistent `agent_id`. Scripts, schedules, memory candidates, or future-agent suggestions alone do not satisfy the request.
- OMP memory-candidate governance must reject obvious target mismatches. Cloudflare/domain traffic/monitoring/scheduled ops memory must target an `ops` or clearly dedicated Cloudflare/domain/traffic agent; it must not be queued or approved into generic researcher/search agents.
- Process normalization belongs inside `ohmypi_provider.py`; `app.py` must not contain OMP-specific RPC parsing or a second OMP renderer.
- OMP process args/results included in assistant text must be bounded and secret-redacted before entering the display queue, history, artifacts, traces, or memory-candidate extraction.
- OMP memory-candidate signal extraction must strip normalized process markers, `<thinking>` blocks, tool args, and tool result fences before deciding whether a durable candidate exists.
- Oh My Pi RPC `turn_end` captures the completed visible turn but must not release the active prompt until `agent_end`, because real OMP may still be finalizing UI/status events and will reject a next prompt as `Agent is already processing`.
- Oh My Pi RPC `turn_end` with `stopReason:"toolUse"` or non-empty `toolResults` is an intermediate tool turn and must not start the short missing-`agent_end` grace fallback, because real OMP may need another model turn to produce the final assistant reply after tools finish.
- Oh My Pi RPC `agent_end` maps the active prompt to one queue item shaped as `{"done": <buffer>, "source": "ohmypi"}`. If `agent_end` is absent, a short provider-owned grace fallback may complete from the captured `turn_end` payload for compatibility with older/fake streams.
- When streamed text already contains the final assistant answer and `agent_end.messages` repeats that answer, terminal fallback text must not be appended again. The de-duplication must tolerate benign punctuation/whitespace differences between streamed chunks and the terminal message.
- OMP assistant message `usage` payloads must be normalized inside `ohmypi_provider.py` and attached to the terminal queue item as `usage:{requests,input,output,cache_create,cache_read}`.
- OMP usage mapping is `input -> input`, `output -> output`, `cacheRead -> cache_read`, and `cacheWrite` / `cacheCreate` -> `cache_create`; each distinct usage-bearing assistant message increments `requests` by 1.
- OMP usage from repeated terminal frames such as `message_end` followed by `agent_end.messages` must be de-duplicated by stable message/response ids when available.
- If RPC terminal frames do not carry non-zero usage, `ohmypi_provider.py` must fall back to the Shuheng-owned isolated OMP session JSONL files under `PI_CODING_AGENT_DIR/sessions`, diff against the active prompt's session-file baseline, count only assistant-message usage rows created for that prompt, and then attach the same normalized queue `usage`.
- The session-file fallback must tolerate OMP writing JSONL usage shortly after `agent_end`: normal completions should wait for a short stable-flush window before emitting the terminal queue item, while startup, abort, prompt-failure, and terminal-error paths should not wait for usage.
- `app.py` owns persistence of provider-normalized usage into `session_token_usage.json` for the active Shuheng session key; provider code must not import app state or write the registry directly.
- Temporary/devnull sessions must not persist OMP token usage, matching the `/temp` non-persistence contract.
- If no `text_delta` populated the active buffer, the done text must fall back to visible assistant text carried by assistant `message_end`, terminal-frame assistant `message.content`, `assistantMessageEvent` text payloads, or the last assistant entry in `agent_end.messages`.
- User and `toolResult` `message_end` frames must not overwrite the final assistant fallback text.
- Startup, prompt, or missing-binary failures must map to a queue `done` item instead of raising into the TUI caller after `put_task()` returns.
- The wrapper must expose the current GenericAgent-shaped compatibility surface used by existing TUI hot paths: `put_task()`, `abort()`, `get_llm_name()`, `list_llms()`, `load_llm_sessions()`, `next_llm()`, `is_running`, `task_queue.unfinished_tasks`, `log_path`, `llmclient.backend`, and `llmclients`.
- `OhMyPiRuntimeAdapter.start_agent()` must not block on model or network startup. RPC process startup is lazy and happens on first prompt.
- The provider module must not import `ga_tui.app`, curses, or mutable TUI `State`.
- Oh My Pi unrestricted host tools remain disabled in provider metadata: `capabilities.host_tools:false`.
- The only allowed host tool bridge is app-injected TUI governance querying, typed read-only control-plane tools, and governed proposal routing: `capabilities.tui_readonly_host_tools:true`, `capabilities.tui_governed_proposal_tools:true`, and `capabilities.tui_typed_host_tools:true`.
- Provider metadata must advertise `capabilities.runtime_task_requests:true` and `capabilities.runtime_task_events:true` once OMP execution is wrapped by `runtime.task_request.v1` and `runtime.task_event.v1`.
- `OhMyPiRpcAgent` may register host tools through `set_host_tools` only from definitions injected by `app.py`; provider code must not invent writable tools or import TUI `State`.
- Embedded OMP must use a Shuheng-owned runtime root and must not read or write system-level `~/.omp/agent/config.yml`, `~/.omp/agent/models.yml`, sessions, auth storage, or cache as its active agent directory.
- Embedded OMP must run with the GenericAgent-TUI repository root as its subprocess `cwd`, while Shuheng harness paths, memory, ledgers, isolated OMP runtime files, and provider metadata use the `SHUHENG_HOME` / `${AGENT_HARNESS_DIR}` ownership boundary.
- `app.py` owns translation from GA-TUI `/model` entries to isolated OMP `config.yml` and `models.yml`; `ohmypi_provider.py` owns only generic runtime file writing, subprocess env, OMP binary discovery, command construction, and RPC behavior.
- OMP binary discovery order is explicit `binary` argument, `GA_TUI_OHMYPI_BIN`, `PATH` lookup for `omp`, then user-local Bun install at `$HOME/.bun/bin/omp`. A still-missing executable remains a visible startup error instead of mutating user shell configuration.
- Generated OMP `config.yml` must set `modelRoles.default` to the GA-TUI default model selector when a complete matching `/model` entry exists.
- Generated OMP `models.yml` must represent complete GA-TUI OpenAI-compatible entries as custom OMP providers with `baseUrl`, `apiKey`, `api`, and `models[].id`; API keys must be referenced through child-process env var names instead of written as secrets in the generated file.
- Generated OMP `models.yml` must project `/model` `context_win` to OMP `models[].contextWindow`; if `max_tokens` is configured, it must project to `models[].maxTokens`.
- Incomplete GA-TUI model entries without API key, base URL, or model id are skipped when generating OMP model providers.
- OMP runtime model rows exposed to the TUI must preserve enough provider/model/base URL metadata for `/model` current-session switching to call OMP `set_model` with structured `provider` and `modelId`.
- Embedded OMP must not auto-resume stale internal OMP sessions; Shuheng owns visible session history and resets the OMP RPC session when Shuheng opens a fresh main/temporary/restored runtime context.
- A long-running OMP process must receive at most one full `[GA TUI Context Pack]` prompt per Shuheng runtime session. Later context refreshes should pass a bounded `[GA TUI Context Ref]` with the artifact ref, so OMP history does not accumulate repeated full context packs.
- `ga_tui_query` is read-only and must never mutate sessions, tasks, agents, approvals, artifacts, memory, or files.
- `ga_tui_propose` accepts only bounded proposal payloads with `proposal_type:"ga_control"` or `proposal_type:"memory_candidate"`.
- `ga_tui_propose` with `proposal_type:"ga_control"` must require a current-schema `ga-control.v2` envelope or `agenttask.v2` action object, validate that it maps to known current controls, and route execution through `apply_tui_controls_from_text(..., source="agent:ohmypi_host_tool")` so existing policy gates and ledgers remain the source of truth.
- `ga_tui_propose` with `proposal_type:"memory_candidate"` must resolve the target subagent from the bound TUI `State` and call `queue_curated_memory_candidate(...)`; direct long-term memory writes remain forbidden.
- `ga_tui_propose` results use `schema_version:"ga-tui.proposal.v1"` and return JSON-safe `status`, `kind`, result lines/messages, ids, and artifact refs where available.
- Typed read-only tools must call the same app-layer query functions as the compatibility query endpoint. They must not mutate sessions, tasks, approvals, long-term memory, or ledgers.
- `memory_context_get` may generate a Shuheng-owned context-pack artifact and return `context_pack_ref` plus a JSON-safe pack. This is the allowed way for OMP to hydrate memory/context; it is not a long-term memory write.
- `memory_candidate_submit` must call the same governed memory-candidate path as `ga_tui_propose` with `proposal_type:"memory_candidate"`.
- `proposal_submit` must call the same governed proposal path as `ga_tui_propose`.
- `schedule_create` may create a TUI-owned schedule through the scheduler service; it must use the existing schedule registry and must not call OMP or any runtime directly.
- Host tool registration must happen after OMP emits `{"type":"ready"}` and before the first prompt command is sent for that process.
- OMP `host_tool_call` frames must be answered with `host_tool_result` using the same frame `id`.
- Host tool result payloads must be AgentToolResult-shaped JSON, with bounded redacted text under `content:[{"type":"text","text":"..."}]`.
- Unknown tools, missing handlers, invalid arguments, and callback failures must return `host_tool_result` with `isError:true` instead of crashing the stdout reader or active prompt.
- OMP `host_tool_cancel` frames must be accepted safely and must not mutate TUI state.
- OMP terminal error details from `message_end`, `turn_end`, or `agent_end` must map to a visible queue `done` item when frames carry `stopReason:"error"`, `errorMessage`, or `errorStatus`; error turns must not become empty assistant replies.
- Host URI schemes and TUI approval mapping remain disabled until a separate explicit task designs those governance contracts.
- On this experiment branch, Oh My Pi is the default runtime provider when `GA_TUI_RUNTIME_PROVIDER` is unset.
- GenericAgent must remain selectable with `GA_TUI_RUNTIME_PROVIDER=genericagent`.
- The TUI should generate a bounded `GA/TUI Memory Guidance` append prompt from Shuheng-owned memory sources under `${SHUHENG_HOME}/memory` and pass it through `--append-system-prompt`.
- Oh My Pi completion output may emit memory candidate signals, and `ga_tui_propose` may submit curated memory candidates, but long-term memory writes remain governed by TUI memory candidate records and human approval.
- Main OMP tasks and worker/subagent OMP tasks should include generated GA-TUI context pack artifacts when using the structured runtime request path.
- OMP runtime events for requested tasks, host tool calls/results, completion, failure, and abort must be normalized into `runtime.task_event.v1` records and appended to GA-TUI traces when a concrete task id exists.
- OMP runtime events for Secret-context tasks must not be appended to the normal trace store, and OMP memory candidate extraction must ignore `secret-*` sources.

### 4. Validation & Error Matrix

- `omp` executable missing after explicit/env/PATH/user-local Bun discovery -> provider spec status is `missing`; prompt queue receives a user-visible startup failure.
- RPC process does not emit `{"type":"ready"}` before timeout -> prompt queue receives an RPC ready timeout failure and the process is terminated.
- Prompt command receives `success:false` -> active prompt queue receives `RPC prompt failed: ...`.
- Concurrent `put_task()` while one prompt is active -> second queue receives a user-visible concurrency error.
- RPC stdout emits non-JSON -> line is recorded in provider stderr tail and ignored.
- RPC extension UI request `confirm` -> provider replies `confirmed:false`.
- RPC extension UI request `select`, `input`, or `editor` -> provider replies `cancelled:true`.
- `abort()` called during a prompt -> provider sends RPC `abort`, emits a queue `done` item, clears `is_running`, and decrements `task_queue.unfinished_tasks`.
- OMP `ready` with configured app-injected TUI tools -> provider sends `set_host_tools` before the prompt frame.
- OMP `host_tool_call` for `ga_tui_query` -> provider runs the app-injected read-only callback and sends a JSON-safe `host_tool_result`.
- OMP `host_tool_call` for a typed read-only tool such as `agent_list`, `schedule_list`, or `memory_context_get` -> app callback routes through the same control-plane query/context helpers and sends a JSON-safe `host_tool_result`.
- OMP `host_tool_call` for `memory_candidate_submit` -> app callback routes through `queue_curated_memory_candidate(...)` and returns candidate/approval/artifact refs when queued.
- OMP `host_tool_call` for `schedule_create` -> app callback writes a TUI-owned `scheduledtask.v1` row with default provider `ohmypi` when no explicit provider is supplied.
- OMP `host_tool_call` for `ga_tui_propose` memory candidate -> app callback routes through `queue_curated_memory_candidate(...)` and returns a JSON-safe proposal result with candidate/approval/artifact refs when queued.
- OMP `host_tool_call` for `ga_tui_propose` current-schema control -> app callback routes through `apply_tui_controls_from_text(...)` and returns control result lines.
- OMP `host_tool_call` for `ga_tui_propose` with unknown proposal type, missing required fields, missing TUI state, unresolved target, invalid schema, or no known action -> callback returns `schema_version:"ga-tui.proposal.v1"` with `status:"error"`.
- OMP `host_tool_call` for an unregistered tool -> provider sends `host_tool_result` with `isError:true`.
- OMP `host_tool_call` whose callback raises -> provider sends `host_tool_result` with `isError:true`.
- OMP `host_tool_cancel` -> provider records the cancellation safely and continues normal prompt handling.
- Complete GA-TUI model entry -> isolated OMP `models.yml` gets one provider/model mapping and the child env gets a matching `GA_TUI_OMP_API_KEY_<digest>` value.
- Complete GA-TUI model entry with `context_win:1050000` -> isolated OMP `models.yml` writes `contextWindow:1050000` for that model.
- Incomplete GA-TUI model entry -> omitted from isolated OMP `models.yml`; no invalid OMP provider is generated.
- Selected GA-TUI default model -> OMP command may include `--model <isolated-provider>/<model-id>` and isolated `config.yml` carries the same `modelRoles.default`.
- New Shuheng main or temporary session -> active OMP RPC session receives a `new_session` reset when the process is running, and a later first runtime task may inject one fresh full context pack.
- User system OMP config exists -> policy checks must verify its hash remains unchanged across embedded OMP runtime setup.
- OMP adapter registration -> subprocess `cwd` is the GenericAgent-TUI app root so relative repo paths such as `AGENTS.md` resolve to the TUI project while isolated runtime files still live under the Shuheng-owned harness directory.
- OMP error frame with `stopReason:"error"` and `errorMessage` -> active TUI queue receives a visible `[Oh My Pi] ...` done item.
- OMP `turn_end` followed by an immediate next `put_task()` before `agent_end` -> wrapper rejects the next prompt as concurrent instead of sending it to OMP and surfacing `Agent is already processing`.
- OMP `turn_end` followed by `agent_end` -> active queue receives the done item and the next prompt can then be sent normally.
- OMP text deltas split punctuation as `"1"`, `"."`, `" item"` or `"0"`, `"."`, `"6"` -> the final queue text preserves `1.` and `0.6`; if `agent_end.messages` also carries the complete final assistant message, the answer appears once.
- OMP `message_end` and `agent_end.messages` carry the same assistant message usage -> token usage is counted once.
- OMP RPC frames omit non-zero usage but the isolated session JSONL contains assistant-message usage created after the active prompt baseline -> token usage is recovered from the session file and counted once.
- OMP `agent_end` arrives before the isolated session JSONL flushes usage -> the provider waits for the short stable-flush window, attaches the recovered usage, and only then emits the terminal queue item.
- OMP terminal queue item carries usage -> the TUI main thread writes the active session row in `session_token_usage.json`, and the left status panel reads that row through `session_token_stats()`.
- OMP terminal queue item carries usage for a devnull temporary session -> no token usage registry row is written.
- Two consecutive OMP main turns in one Shuheng runtime session -> first prompt contains `[GA TUI Context Pack]`; second prompt contains `[GA TUI Context Ref]` and does not repeat the full pack.
- OMP thinking delta + tool execution frames + final text delta -> active TUI queue receives GA-style process markers plus the final reply; `render_assistant_text(..., fold_process:true)` folds thinking/tool noise and keeps the final reply visible.
- OMP host tool calls/results -> active TUI queue receives folded GA-style tool process turns while RPC still receives matching `host_tool_result` frames.
- OMP memory-candidate signal extraction over normalized process output -> candidate statement contains only the final durable reply, not thinking text, tool args, or tool results.
- OMP follow-up `这个是啥啊？` after a visible BSpace Agent Arcade URL/task -> answer about the Agent Arcade/game/API task, not about the GA TUI Context Pack/Ref.
- OMP memory candidate about Cloudflare/domain traffic monitoring targeting `搜索代理` or another generic `researcher` -> rejected with `target_mismatch_ops_memory_requires_ops_or_dedicated_agent` and no subagent memory append occurs, even if a stale approval row is later approved.
- `put_runtime_task(RuntimeTaskRequest)` -> provider emits at least `runtime_task_requested` and a terminal `runtime_task_completed`, `runtime_task_failed`, or `runtime_task_aborted` event carrying the original request and context-pack artifact refs.

### 5. Good/Base/Bad Cases

- Good: unset `GA_TUI_RUNTIME_PROVIDER` selects `OhMyPiRuntimeAdapter`, starts `omp --mode rpc` lazily with the generated memory append prompt, streams text deltas into the existing TUI message renderer, and keeps GenericAgent available as an explicit fallback.
- Good: `/model` entries are projected into `${AGENT_HARNESS_DIR}/runtime/ohmypi/agent/models.yml`, OMP is launched with `PI_CODING_AGENT_DIR` pointing at that directory, and system `~/.omp/agent/config.yml` is untouched.
- Good: generated `models.yml` stores `apiKey: GA_TUI_OMP_API_KEY_<digest>` while the secret value is supplied only in the child process env.
- Good: Missing `omp` produces an assistant-visible error message instead of crashing startup.
- Base: `/runtimes` shows both `genericagent` and `ohmypi`, while the experiment-branch default is `ohmypi`.
- Base: Oh My Pi can query bounded TUI governance facts through `ga_tui_query` without mutating task ledgers, approvals, artifacts, or long-term memory.
- Base: Oh My Pi can use typed tools such as `agent_list`, `schedule_list`, and `memory_context_get`; compatibility aliases remain available during migration.
- Base: Oh My Pi can propose current-schema actions through `ga_tui_propose`, while GenericAgent-TUI remains the Orchestrator and policy/ledger owner.
- Base: Oh My Pi can submit a durable memory candidate through `ga_tui_propose` or `memory_candidate_submit`, while the TUI Memory Curator creates artifacts and a human approval request before any long-term memory write.
- Base: A durable completed Oh My Pi output records a memory candidate signal for later approval instead of writing long-term memory directly.
- Base: Oh My Pi task request/completion/host-tool events are normalized into trace rows when they have a GA-TUI task id.
- Bad: The provider imports `app.py` to read TUI state or mutate ledgers directly.
- Bad: Embedded OMP inherits `~/.omp/agent` or uses the user's system OMP `modelRoles.default`, because `/model` would no longer be the single GA-TUI settings surface.
- Bad: Generated OMP `models.yml` writes raw API key values.
- Bad: The adapter enables arbitrary OMP host tools, host URI schemes, writable operations, or auto-approval before TUI policy gates can audit and approve those operations.
- Bad: `app.py` contains Oh My Pi RPC parsing logic instead of provider-local parsing.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `ohmypi` appears in the runtime registry and is the experiment-branch default.
- Tests must assert `GA_TUI_RUNTIME_PROVIDER=genericagent` selects the GenericAgent fallback adapter.
- Tests must assert `ohmypi_provider.py` has no reverse import into `app.py` and no curses import.
- Tests must assert the generated memory append prompt is bounded, redacted, and passed to `omp` through `--append-system-prompt`.
- Tests must assert generated OMP context packs/context refs, memory append prompts, and memory-candidate tool descriptions contain the final-reply rule so memory-candidate status cannot become the only visible completion.
- Tests must assert generated OMP context packs/context refs and memory append prompts contain the deictic-reference rule that prevents `这个`/`this` from resolving to internal context metadata by default.
- Tests must assert generated OMP context packs/context refs and memory append prompts contain the persistent-agent request rule, and that ops/Cloudflare memory candidates targeting generic search/research agents are rejected both at queue time and approval time.
- Tests must assert OMP command construction discovers `$HOME/.bun/bin/omp` when `omp` is absent from `PATH`, while explicit `GA_TUI_OHMYPI_BIN` remains authoritative.
- Tests must assert completed Oh My Pi output can produce a governed memory candidate signal and that empty, too-short, secret-looking, and Secret-context outputs are skipped.
- Tests must assert a fake RPC process maps `ready`, `prompt` ack, `message_update` deltas, and `agent_end` into queue `next`/`done` items.
- Tests must assert standalone dot deltas preserve real punctuation in normal streamed final text, still hide tool-turn placeholder dots, and do not cause terminal final-message fallback duplication.
- Tests must assert OMP `usage` payloads are normalized, de-duplicated across repeated terminal frames, recovered from isolated OMP session JSONL when RPC frames omit non-zero usage, diffed against the active prompt baseline rather than a provider-lifetime seen set, attached to queue `done` items after the stable-flush wait, included in runtime completion event payloads, persisted into `session_token_usage.json`, and skipped for devnull temporary sessions.
- Tests must assert `turn_end` does not release the active prompt before `agent_end`, preventing immediate next-prompt races against real OMP finalization.
- Tests must assert `turn_end` carrying `stopReason:"toolUse"` or tool results waits for the final assistant answer instead of completing from the tool-result turn.
- Tests must assert a fake RPC process maps OMP thinking/tool events into GenericAgent-TUI foldable process blocks, that the existing assistant renderer folds them, and that final replies remain visible.
- Tests must assert `put_runtime_task(RuntimeTaskRequest)` emits `runtime.task_event.v1` rows that preserve `runtime.task_request.v1`, `prompt_preview`, `prompt_chars`, `context_pack_ref`, and artifact refs without storing the raw prompt.
- Tests must assert a fake RPC process with no `text_delta` still produces non-empty `done` text when final assistant text is carried by `message_end.message.content` or terminal-frame `message.content`.
- Tests must assert a fake RPC process receives app-injected `set_host_tools` definitions before the prompt frame.
- Tests must assert fake `host_tool_call` frames receive `host_tool_result` success frames.
- Tests must assert unknown or failing host tool calls receive `host_tool_result` with `isError:true`.
- Tests must assert `host_tool_cancel` frames are handled safely.
- Tests must assert `ga_tui_query` remains read-only and `ga_tui_propose` supports governed `ga_control` and `memory_candidate` proposals.
- Tests must assert typed OMP tools include read-only state queries, `memory_context_get`, `memory_candidate_submit`, and `schedule_create`.
- Tests must assert `memory_context_get` writes a GA-TUI context-pack artifact under the harness and returns its artifact ref.
- Tests must assert `ga_tui_propose` memory candidates create existing memory approval artifacts/approval rows and invalid proposals return structured errors.
- Tests must assert provider metadata advertises `tui_readonly_host_tools:true`, `tui_governed_proposal_tools:true`, `tui_typed_host_tools:true`, `runtime_task_requests:true`, and `runtime_task_events:true` while keeping unrestricted `host_tools:false`.
- Tests must assert isolated OMP runtime files are generated under `${AGENT_HARNESS_DIR}/runtime/ohmypi/agent`, not under `~/.omp/agent`.
- Tests must assert the OMP runtime adapter subprocess `cwd` is the GenericAgent-TUI app root, not the GenericAgent harness root.
- Tests must assert generated OMP API keys are env references in `models.yml`, raw key values are absent from generated files, and child-process env carries `PI_CODING_AGENT_DIR`.
- Tests must assert generated OMP model rows preserve `contextWindow` / `maxTokens` from `/model`, embedded OMP `config.yml` disables `autoResume`, and repeated runtime turns use a context ref instead of repeating the full context pack.
- Tests must assert `/model` default selection maps to isolated OMP `modelRoles.default` and RPC `set_model` can be sent before the first prompt when a TUI model is selected.
- Tests must assert OMP terminal error frames surface `errorMessage` / `errorStatus` visibly instead of an empty done item.
- Tests must assert system `~/.omp/agent/config.yml` hash remains unchanged when present.
- Tests must assert missing binary failure and `abort()` cleanup decrement unfinished task state.
- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/ohmypi_provider.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# app.py
if provider_id == "ohmypi":
    line = process.stdout.readline()
    frame = json.loads(line)
```

#### Correct

```python
# ohmypi_provider.py
class OhMyPiRuntimeAdapter(RuntimeAdapter):
    def create_agent(self) -> OhMyPiRpcAgent:
        return OhMyPiRpcAgent()
```

#### Wrong

```python
# ohmypi_provider.py
def handle_memory_candidate(statement):
    from ga_tui.app import queue_curated_memory_candidate
    queue_curated_memory_candidate(...)
```

#### Correct

```python
# app.py
def ohmypi_tui_propose_host_tool_handler(state, args):
    if args["proposal_type"] == "memory_candidate":
        return ohmypi_tui_propose_memory_candidate(state, args)
```

#### Wrong

```python
event_payload = runtime_request.to_record()
event_payload["prompt"] = full_prompt
append_trace(task_id, "runtime_task_requested", payload=event_payload)
```

#### Correct

```python
event_payload = runtime_request.to_record()
# to_record() stores prompt_preview, prompt_chars, and artifact refs only.
append_trace(task_id, "runtime_task_requested", payload=event_payload)
```

## Scenario: TUI Governed Schedule Tools

### 1. Scope / Trigger

- Trigger: The main model needs to create or inspect scheduled work from a natural-language user request.
- Applies to: GenericAgent tool schema injection, GenericAgentHandler `do_*` dispatch methods, `scheduledtask.v1` registry writes, schedule registry reads, and prompt guidance.
- Non-goal: The model must not inspect, modify, or start external scheduler files, external scheduler SOPs, or another program's scheduler directory to satisfy TUI scheduling requests.

### 2. Signatures

- Tool names exposed to the model are snake_case function tools: `schedule_create` and `schedule_list`.
- User-facing documentation may refer to dotted names: `schedule.create` and `schedule.list`.
- `schedule_create` accepts the current `ScheduleCreate` trigger schema: `cron`, `interval`, `at`, or standardized `trigger` strings prefixed as `cron:`, `interval:`, or `at:`.
- `schedule_create` must include a discriminated `execution` object.
- `execution.mode:"tui_action"` runs a bounded local TUI action. The current supported action is `action:"beep"` for audible reminders that do not require a subagent.
- `execution.mode:"agent_task"` dispatches governed work through `agenttask.v2` and carries `routing`, `work_order`, `capability_contract`, `context_contract`, and `output_contract`.
- `schedule_create` response uses `schema_version:"ga-tui.tool.v1"` and returns the appended `scheduledtask.v1` row plus the current schedule registry snapshot.
- `schedule_list` response uses `schema_version:"ga-tui.tool.v1"` and returns the TUI `scheduledtask.registry.v1` snapshot.

### 3. Contracts

- `schedule_create` is a governed state-changing TUI tool, not a read-only query tool.
- `schedule_create` must call the same schedule registration path used by `ga-control.v2` `schedule.create`.
- Created schedule rows must carry `schema_version:"scheduledtask.v1"`, an explicit `execution` object, a matching `dispatch_contract`, and `source:"tool:schedule_create"`.
- Agent-task schedule rows use `dispatch_contract:"agenttask.v2"` and keep agent routing plus work/capability/context/output contracts under `execution`.
- TUI-action reminder rows use `dispatch_contract:"tui_action.v1"` plus the bounded TUI action data under `execution`. They are audited through `scheduledtask.run.v1` rows but do not create task-ledger rows.
- `schedule_list` reads only the TUI schedule registry and schedule-run audit data.
- Natural-language timing is translated by the model into the current positive trigger schema before tool invocation.
- Schema-outside fields are handled by the generic boundary. Active prompts, docs, runtime, user-facing errors, and normal tests should not enumerate retired trigger vocabulary.

### 4. Validation & Error Matrix

- Missing bound TUI state on `schedule_create` -> `status:"error"`.
- Missing current trigger field -> generic missing-trigger error.
- Missing `execution.mode` -> creation/update error.
- `execution.mode:"tui_action"` with `action:"beep"` -> valid TUI reminder schedule.
- Unsupported TUI action -> creation/update error; an already-persisted invalid row records a failed schedule-run row at dispatch time.
- `execution.mode:"agent_task"` without `work_order.objective` -> creation/update error.
- `execution.mode:"agent_task"` without an explicit structured routing target -> creation/update error.
- `schedule_list include_inactive:false` hides disabled, deleted, cancelled, and canceled rows from the returned jobs list.
- Repeated `install_tui_query_runtime()` calls -> no duplicate schedule tool schemas and no duplicate handler side effects.

### 5. Tests Required

- `scripts/check_policy_gates.py` must assert `schedule_create` and `schedule_list` schemas are installed exactly once.
- Tests must assert handler methods exist and return `StepOutcome` with `next_prompt:"\n"`.
- Tests must assert `schedule_create` appends `scheduledtask.v1` rows through the shared registry path for both execution modes.
- Tests must assert an agent-task schedule stores `execution.mode:"agent_task"` and `dispatch_contract:"agenttask.v2"`.
- Tests must assert a TUI beep schedule stores `execution.mode:"tui_action"`, writes `dispatch_contract:"tui_action.v1"`, and appends a completed schedule-run row without requiring an agent target.
- Tests must assert `schedule.update` without an execution object preserves the existing execution contract, and trigger updates leave one current trigger source of truth.
- Tests must assert `schedule_list` reports the TUI schedule registry without requiring any external scheduler file.
- Tests should assert current schedule tool/schema vocabulary and active-prompt absence invariants without locking exact prose.

## Scenario: Control Result Continuation

### 1. Scope / Trigger

- Trigger: The main agent emits real `ga-control.v2` controls for an intermediate workflow step and explicitly requests continuation with structured metadata such as `continue_after:true` or `workflow_state:"in_progress"`, but does not create an executable task ledger and does not emit the next delegation/configuration controls.
- Applies to: normal non-Secret main-agent turns after `apply_tui_controls_from_text()` has executed controls.
- Non-goal: This must not manually execute the business workflow in the TUI. It only feeds control results back to the main agent so the orchestrator can continue emitting governed controls.

### 2. Signatures

- Auto continuation source: `ga-tui:auto_control_continue`.
- Continuation prompt block: `[GA TUI Control Result Continuation] ... [/GA TUI Control Result Continuation]`.
- State counters: per-signature `auto_control_continue_attempts`, session cap `auto_control_continue_count`.
- Structured continuation fields: `continue_after`, `next_action_required`, `requires_continuation`, `workflow_state`, `orchestrator_state`, and `next_action`.

### 3. Contracts

- `apply_tui_controls_from_text()` returns formatted control result lines while still adding the visible `Agent 控制结果` system message.
- The continuation only runs when the executed control envelope or action explicitly carries continuation metadata such as `continue_after:true`, `next_action_required:true`, `requires_continuation:true`, `workflow_state:"in_progress"`, or a non-empty `next_action`.
- Visible prose must never trigger continuation by itself.
- Controls that already delegated child work, such as `delegate.create`, must not trigger this fallback because the next event should be the subagent result.
- If an executable task plan exists, `maybe_queue_orchestrator_plan_continuation()` remains the primary mechanism and this fallback does not run.
- New user-started main tasks reset the control-continuation counters.

### 4. Validation & Error Matrix

- No real controls -> no continuation.
- Active plan exists -> use plan continuation instead.
- Active subagent work, pending interaction, or non-idle main state -> no continuation.
- Same control result signature repeats -> stop after one retry and add an `orchestrator_auto_continue_blocked` system message.
- Session reaches the continuation cap -> stop and add an `orchestrator_auto_continue_blocked` system message.

### 5. Good/Base/Bad Cases

- Good: The assistant emits `agent.create` with `continue_after:true`; TUI creates the agent, then starts `ga-tui:auto_control_continue` with the control result so the assistant can continue with ledger/delegation/configuration.
- Base: The assistant creates an agent as a complete one-step user request without structured continuation metadata; no auto continuation fires.
- Base: The assistant creates an agent and writes "Step 1" in visible prose but omits structured continuation metadata; no auto continuation fires.
- Bad: The assistant emits `delegate.create` and TUI immediately starts another main turn before the subagent result arrives.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert structured continuation metadata plus `agent.create` starts a second main-agent prompt with source `ga-tui:auto_control_continue`.
- The continuation prompt must include the control result, the created agent name, and instruction to continue the approved workflow without repeating controls.
- Existing auto-plan continuation tests must continue to pass and remain primary when a task ledger exists.

### 7. Wrong vs Correct

#### Wrong

```text
Visible text says "Step 1.1 create agent" but the control has no continuation metadata -> Agent 控制结果 shows success -> main agent stops because the control did not request continuation.
```

#### Correct

```text
agent.create includes continue_after:true -> Agent 控制结果 shows success -> ga-tui:auto_control_continue feeds the result back to the orchestrator -> orchestrator emits the next governed controls.
```

## Scenario: Scheduled Task Scheduler

### 1. Scope / Trigger

- Trigger: TUI schedule records must execute recurring or one-shot work without bypassing the governed subagent/task protocol.
- Applies to: `schedule.create`, `schedule.update`, `schedule.enable`, `schedule.disable`, `schedule.delete`, `/schedules`, `/scheduler`, MCP schedule resources, runtime provider registry metadata, and scheduler tick tests.
- Non-goal: A schedule must not directly call `agent.put_task()` or choose a worker from natural-language similarity.

### 2. Signatures

- Schedule registry path: `AGENT_SCHEDULES_PATH`, JSONL rows with `schema_version:"scheduledtask.v1"`.
- Schedule run audit path: `AGENT_SCHEDULE_RUNS_PATH`, JSONL rows with `schema_version:"scheduledtask.run.v1"`.
- Implementation module: `src/ga_tui/scheduler.py` owns schedule registry helpers, trigger parsing, due calculation, run audit shaping, tick aggregation, and scheduler text formatting.
- Composition module: `src/ga_tui/app.py` may re-export scheduler helpers for compatibility, but it supplies mutable TUI dependencies through `configure_scheduler_runtime()` instead of being imported by `scheduler.py`.
- TUI commands:
  - `/schedules` shows registry, due state, run count, and last-run state.
  - `/scheduler status` shows scheduler state.
  - `/scheduler tick` evaluates due jobs and records manual skip/invalid outcomes.
  - `/scheduler run <schedule_id>` force-runs one enabled schedule.
- Supported trigger fields: `at`, `interval`, `cron`, and standardized `trigger` strings prefixed as `at:...`, `interval:...`, or `cron:...`.
- Users express scheduling intent in natural language. The main model translates that intent into the current `ScheduleCreate` trigger schema before emitting `ga-control.v2`. Schema-outside fields are handled by the generic boundary; active runtime, prompts, docs, user-facing errors, and normal tests should not enumerate retired field names.
- Daemon tick interval env: `GA_TUI_SCHEDULER_TICK_SECONDS`, minimum 5 seconds, default 30 seconds.
- MCP resources include `resource://agent-mail/schedules` and `resource://agent-mail/schedule-runs`.

### 3. Contracts

- Agent-work schedule dispatch must build an explicit `agenttask.v2` `delegate.create` envelope and reuse the existing delegation path.
- TUI-local reminder dispatch must execute only explicit `execution.mode:"tui_action"` rows and write schedule-run audit rows; it must not infer actions from schedule names or natural-language objectives.
- A dispatchable agent-task schedule must include `execution.work_order.objective` and an explicit structured routing target.
- A TUI-action reminder schedule must include `execution.action`; it does not require `work_order.objective` or an agent target.
- Due jobs reserve an `idempotency_key` by appending a `starting` run row before dispatching.
- Final run rows reuse the same `run_id` and append status such as `dispatched`, `queued`, `approval_required`, `failed`, `rejected`, `duplicate`, `skipped`, or `invalid`.
- Agent-task final run status must come from a structured dispatch result (`status`, `message`, `task_id`, `approval_id`, `error`, `provider_id`) rather than parsing localized UI text returned to ordinary callers.
- Schedule run rows must record `provider_id`. If a schedule does not explicitly carry a provider id, scheduler dispatch resolves it through the injected runtime default, which is `ohmypi` on this branch.
- Agent-task final run rows should also record `runtime_provider_id` from the structured dispatch result or the resolved schedule provider.
- After each run row, the latest schedule record is updated append-only with `last_run_id`, `last_run_status`, `last_run_at`, and `last_idempotency_key`.
- Due calculation for interval schedules must use the latest real dispatch attempt (`starting`, `dispatched`, `queued`, `approval_required`, `failed`, or `rejected`) as its anchor. Observation-only rows such as `duplicate`, `skipped`, and `invalid` may be displayed as the latest run, but must not move the next interval due time.
- Disabled, deleted, cancelled, and canceled schedules are not dispatched.
- Schedule execution must enter `start_subagent_task()` so policy gates, single-writer locks, task ledger, agent mail, checkpoints, traces, and artifacts remain active.
- `src/ga_tui/scheduler.py` must not import curses, GenericAgent runtime classes, `StepOutcome`, mutable TUI `State`, or `ga_tui.app`.
- App-layer dependencies required by scheduler execution must be injected through scheduler runtime configuration: JSONL readers/writers, paths, `now_iso`, JSON-safe conversion, default provider lookup, text truncation, TUI beep callback, subagent resolver, and structured subagent dispatch callback.
- TUI beep emission stays in `app.py` or another UI composition layer; scheduler dispatch calls it through an injected callback so the scheduler module remains UI-free.

### 4. Validation & Error Matrix

- Missing `schedule_id` -> invalid/failed run row.
- Unsupported trigger -> `invalid` run row with reason.
- `at` trigger already ran -> duplicate, no dispatch.
- Cron minute already ran -> duplicate, no dispatch.
- Interval slot already ran -> duplicate, no dispatch.
- Explicitly provided `seen_keys:set()` -> use that set exactly, even when empty; do not fall back to global persisted idempotency keys.
- Input outside the current trigger schema -> generic missing trigger or unsupported field handling.
- Unprefixed free-form `trigger` text -> unsupported trigger / invalid; the model should emit current schema fields such as `interval:"1m"` instead.
- Disabled/deleted schedule -> skipped, no dispatch.
- Missing `execution.mode` -> failed run row, no dispatch.
- Agent-task execution without `work_order.objective` -> failed run row, no dispatch.
- Agent-task execution without a structured routing target -> failed run row, no natural-language fallback.
- Unsupported TUI action -> failed run row.
- Target subagent not found -> failed run row.
- Risky scheduled work -> governed subagent dispatch queues approval and writes a final schedule-run row with `status:"approval_required"`, `task_id`, and `approval_id`.
- Schedule without explicit `provider_id` -> due run rows record `provider_id:"ohmypi"` and final agent-task rows record `runtime_provider_id:"ohmypi"` on this branch.

### 5. Good/Base/Bad Cases

- Good: A due `at` schedule with `routing.selected_agent` dispatches through `start_subagent_task()`, writes task ledger rows, and records `starting` then `dispatched` schedule-run rows with OMP provider provenance by default.
- Good: A due TUI beep schedule executes the local TUI action, writes `starting` then `completed` schedule-run rows, and creates no task-ledger row.
- Base: A disabled schedule is shown in `/schedules` and may record a manual skip, but it never dispatches.
- Base: A cron schedule is evaluated once per matching minute and idempotency prevents repeat dispatch inside that minute.
- Base: A manual skip/duplicate row appears in the audit log and `/schedules`, but the next interval due time is still anchored to the latest real dispatch attempt.
- Good: The user says "every morning at 8"; the main model emits `cron:"0 8 * * *"` in `schedule.create`.
- Bad: Scheduler calls backend `put_task()` directly and skips task ledger / approval gates.
- Bad: The latest `skipped` or `duplicate` row is used as the interval anchor, pushing the next due time forward.
- Bad: The runtime parses free-form prose or schema-outside fields to guess schedule intent.
- Bad: Scheduler sees `role:"researcher"` and guesses a worker by fuzzy matching the objective text.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert schedule registration still records `dispatch_contract:"agenttask.v2"`.
- Tests must assert a due enabled schedule writes `scheduledtask.run.v1` rows and delegates to a fake subagent through the existing task ledger.
- Tests must assert a due enabled schedule without explicit provider records `provider_id:"ohmypi"` and `runtime_provider_id:"ohmypi"` in schedule-run audit rows.
- Tests must assert risky scheduled work records `approval_required` from structured dispatch fields and includes the matching task/approval ids plus OMP provider provenance by default.
- Tests must assert duplicate scheduler ticks do not dispatch a second task for the same idempotency key.
- Tests must assert observation-only rows do not change interval due anchors.
- Tests must assert the positive trigger schema and generic schema-boundary behavior without behavior-testing retired field names.
- Tests must assert the control hint tells the main model to translate natural user intent into new `cron` / `interval` / `at` fields.
- Tests must assert disabled schedules skip and invalid schedules write audit records without dispatching.
- Tests must assert MCP/gateway registries include both schedule registry and schedule-run audit paths.
- Tests must assert `app.py` re-exports key scheduler helpers from `ga_tui.scheduler` and that `src/ga_tui/scheduler.py` does not import curses, GenericAgent runtime classes, `StepOutcome`, mutable TUI `State`, or `ga_tui.app`.
- Tests that retarget harness paths must reconfigure scheduler runtime paths in the same step, otherwise scheduler JSONL helpers can silently write to the previous harness directory.
- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/runtime.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```text
At 08:00, scheduler calls agent.put_task("Generate daily digest") directly and stores only the visible result.
```

#### Correct

```text
At 08:00, scheduler writes scheduledtask.run.v1 starting, converts the schedule to agenttask.v2 delegate.create, calls start_subagent_task(), then appends the final run status and relies on task ledger/artifact refs for execution evidence.
```

## Scenario: Shuheng-Owned Storage And Archive-Backed Sidebar Rows

### 1. Scope / Trigger

- Trigger: Shuheng must own its state independently of the GenericAgent checkout while still using GenericAgent as an optional runtime/source dependency.
- Applies to: Shuheng storage path selection, `load_history()`, `cached_session_rows()`, `continue_cmd`, `session_meta.json`, `session_names.json`, harness ledgers/artifacts/traces, persistent and temporary subagents, Secret Vault, isolated OMP runtime files, sidebar display, and history restore behavior.
- Non-goal: This bridge must not delete, move, unzip, or destructively modify legacy GenericAgent history or memory files.

### 2. Signatures

- Shuheng history home defaults to `~/.shuheng`; `SHUHENG_HOME` overrides it, and legacy internal `GA_TUI_HOME` remains an accepted override.
- `SHUHENG_MEMORY_DIR` defaults to `~/.shuheng/memory`.
- `SHUHENG_TEMP_DIR` defaults to `~/.shuheng/temp`.
- Raw session rows are read from `MODEL_RESPONSES_DIR/model_responses*.txt`, where `MODEL_RESPONSES_DIR` defaults to `~/.shuheng/model_responses`.
- `session_meta.json`, `session_token_usage.json`, `.trash`, and `session_names.json` live under the Shuheng-owned history tree, not `GenericAgent/temp/model_responses`.
- `AGENT_HARNESS_DIR` defaults to `~/.shuheng/memory/agent_harness`.
- `SUBAGENTS_DIR` defaults to `~/.shuheng/memory/subagents`.
- `TEMP_SUBAGENTS_DIR` defaults to `~/.shuheng/temp/subagents`.
- `SECRET_VAULT_DIR` defaults to `~/.shuheng/memory/secret_vault`.
- OMP isolated runtime files default to `~/.shuheng/memory/agent_harness/runtime/ohmypi/agent`.
- Legacy bootstrap marker: `~/.shuheng/.legacy_import.json`.
- `SHUHENG_IMPORT_LEGACY=1` forces a non-destructive legacy import for targeted runs.
- `SHUHENG_DISABLE_LEGACY_IMPORT=1` disables the legacy import.
- `continue_cmd` must be runtime-configured to use the same `MODEL_RESPONSES_DIR` and a Shuheng-owned rounds cache.
- Missing-source archives live under `~/.shuheng/memory/L4_raw_sessions` by default.
- Missing-source rows are synthesized from TUI metadata keys whose basename matches `model_responses*.txt` and whose source file is absent.
- Missing-source metadata fields:
  - `source_missing:true`
  - `archive_backed:true`
  - `source_state:"missing"`
  - `source_path`
  - `original_basename`

### 3. Contracts

- Physical archival must not remove a known sidebar row when TUI metadata still knows the session.
- GenericAgent `ROOT_DIR` remains only a runtime/source discovery root, not a Shuheng state root.
- Missing-source rows may use metadata preview, description, rounds, last-user timestamp, and display name to remain visible.
- Missing-source rows must not pretend to be normal raw sessions.
- New main-agent sessions must bind their agent/client/backend log path to the Shuheng-owned `MODEL_RESPONSES_DIR` before runtime work starts.
- Session naming must persist through the same Shuheng-owned `session_names.json` registry; it must not use GenericAgent's default `frontends/session_names.py` storage path.
- Harness writes for tasks, approvals, artifacts, traces, schedules, gateway metadata, runtime provider metadata, and memory candidates must live under the Shuheng-owned `AGENT_HARNESS_DIR` by default.
- Persistent subagent memory must live under Shuheng-owned `SUBAGENTS_DIR`; temporary subagents must live under Shuheng-owned `TEMP_SUBAGENTS_DIR`.
- Secret Vault encrypted storage must live under Shuheng-owned `SECRET_VAULT_DIR` by default.
- OMP memory append prompts must read Shuheng-owned memory sources, not GenericAgent `memory/`.
- On normal first launch with the default `~/.shuheng` home, Shuheng may bootstrap existing GenericAgent state by copying missing files from `${ROOT_DIR}/temp/model_responses` and `${ROOT_DIR}/memory` into the Shuheng-owned tree.
- Legacy bootstrap must be copy-missing-only: existing Shuheng files win over old GenericAgent files.
- Legacy `session_meta.json`, `session_names.json`, and `session_token_usage.json` are merged as JSON objects when Shuheng sidecars already exist; Shuheng keys win on conflict.
- Legacy bootstrap must not copy stale embedded runtime config from `memory/agent_harness/runtime/**`; isolated OMP runtime files are regenerated under Shuheng.
- Legacy bootstrap writes `.legacy_import.json` so later launches do not repeatedly scan and copy the same source tree.
- `restore_history()` must refuse direct restore when the source path is absent and must leave the active runtime untouched.
- When a raw source file reappears, cached raw-session processing clears missing-source markers.

### 4. Validation & Error Matrix

- Default import with no env override -> `MODEL_RESPONSES_DIR` is `~/.shuheng/model_responses`.
- Default import with no env override -> `AGENT_HARNESS_DIR`, `SUBAGENTS_DIR`, `TEMP_SUBAGENTS_DIR`, `SECRET_VAULT_DIR`, and isolated OMP runtime paths are all under `~/.shuheng`.
- `SHUHENG_HOME=/tmp/shuheng-home` before import -> Shuheng history paths derive from `/tmp/shuheng-home`.
- `GA_TUI_HOME=/tmp/compat-home` before import and no `SHUHENG_HOME` -> Shuheng history paths derive from `/tmp/compat-home`.
- Normal default launch with old GenericAgent session files and empty Shuheng history -> copied Shuheng-owned session files appear in `load_history()` and the sidebar.
- `SHUHENG_IMPORT_LEGACY=1` with a test/custom Shuheng home -> same non-destructive bootstrap runs against the custom target.
- Existing Shuheng memory file conflicts with legacy GenericAgent memory file -> Shuheng file remains unchanged.
- Legacy `memory/agent_harness/runtime/ohmypi/agent/config.yml` exists -> it is not copied into Shuheng's isolated runtime directory.
- `continue_cmd` import -> `_LOG_DIR`, `_LOG_GLOB`, and `_ROUNDS_CACHE_PATH` are retargeted to the Shuheng-owned history tree.
- `session_names` import -> `_LOG_DIR` and `_REG_PATH` are retargeted to the active Shuheng-owned `MODEL_RESPONSES_DIR`.
- New main runtime agent -> agent, LLM client, and backend `log_path` all point at a normal `model_responses_*.txt` file under `MODEL_RESPONSES_DIR`.
- Missing-source row restore without an L4 match -> user-visible restore error and no active runtime log-path switch.
- Missing-source row restore with an L4 match -> source file is reconstructed under `MODEL_RESPONSES_DIR` and normal restore continues.

### 5. Good/Base/Bad Cases

- Good: A fresh `shuheng` launch creates and reads sidebar history, harness ledgers, subagents, Secret Vault, and OMP isolated runtime files under `~/.shuheng` and leaves `/home/vimalinx/Programs/GenericAgent/memory` and `temp/model_responses` untouched.
- Good: A user upgrades from old GenericAgent-backed storage; Shuheng copies missing sessions, global memory files, and persistent subagents into `~/.shuheng`, then the sidebar reads only the copied Shuheng-owned paths.
- Good: `/rename`, AI title jobs, `/continue` parsing, and cached round counts all use Shuheng-owned sidecars.
- Base: The GenericAgent checkout still supplies `continue_cmd.py` and `session_names.py` code, but their storage globals are retargeted at runtime.
- Base: Operators can disable implicit bootstrap with `SHUHENG_DISABLE_LEGACY_IMPORT=1` or force it in custom-home tests with `SHUHENG_IMPORT_LEGACY=1`.
- Base: Test harnesses may retarget `MODEL_RESPONSES_DIR` to a temp directory, but must call `configure_frontend_history_storage()` after changing the path constants.
- Bad: Editing only `MODEL_RESPONSES_DIR` while leaving `continue_cmd._LOG_DIR` or `session_names._REG_PATH` on GenericAgent's default directory.
- Bad: Moving session history but leaving harness ledgers, subagent memory, Secret Vault, or OMP isolated runtime under the GenericAgent checkout.
- Bad: Migrating, deleting, or mutating old GenericAgent history files without an explicit migration task.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert default session history paths are inside Shuheng home and not inside `GenericAgent/temp/model_responses`.
- Tests must assert `AGENT_HARNESS_DIR`, `SUBAGENTS_DIR`, `TEMP_SUBAGENTS_DIR`, `SECRET_VAULT_DIR`, and isolated OMP runtime paths are inside Shuheng home and not inside the GenericAgent checkout.
- Tests must assert `continue_cmd` and `session_names` are retargeted to the active `MODEL_RESPONSES_DIR`.
- Tests must assert legacy bootstrap copies old GenericAgent history and memory into Shuheng, preserves existing Shuheng conflicts, skips stale OMP runtime files, writes a marker, and does not delete source files.
- Tests must assert `new_agent()` starts with a normal `model_responses_*.txt` log path under the active Shuheng history directory.
- `scripts/check_policy_gates.py` must assert `load_history()` includes a missing-source row from `session_meta.json`.
- Tests must assert the row is marked `source_missing:true` and `archive_backed:true`.
- Tests must assert direct restore of a missing-source row reports a clear error and does not bind the active agent log path to the missing file.

### 7. Wrong vs Correct

#### Wrong

```python
SUBAGENTS_DIR = os.path.join(ROOT_DIR, "memory", "subagents")
AGENT_HARNESS_DIR = os.path.join(ROOT_DIR, "memory", "agent_harness")
```

#### Correct

```python
SHUHENG_HOME = default_shuheng_home()
SHUHENG_MEMORY_DIR = os.path.join(SHUHENG_HOME, "memory")
MODEL_RESPONSES_DIR = os.path.join(SHUHENG_HOME, "model_responses")
SUBAGENTS_DIR = os.path.join(SHUHENG_MEMORY_DIR, "subagents")
AGENT_HARNESS_DIR = os.path.join(SHUHENG_MEMORY_DIR, "agent_harness")
configure_frontend_history_storage()
maybe_bootstrap_shuheng_legacy_state()
```

## Scenario: Automatic Shuheng Workspace Memory

### 1. Scope / Trigger

- Trigger: Shuheng project memory is hydrated through an automatically inferred project/workdir workspace.
- Applies to: workspace storage paths, `/workspace` commands, workspace manifests/indexes, L4 cold archive indexes, `memory_inventory()`, `memory_hydration_pack()`, `context_layers_for_task()`, `build_context_pack()`, and `memory_context_get`.
- Non-goal: This does not mine L4 archives into approved long-term facts and does not let OMP/Codex/plugins write long-term memory directly.

### 2. Signatures

- Workspace root: `SHUHENG_WORKSPACES_DIR = os.path.join(SHUHENG_HOME, "workspaces")`.
- Workspace observation state: `SHUHENG_WORKSPACE_STATE_PATH = os.path.join(SHUHENG_WORKSPACES_DIR, "active.json")`.
- Workspace files:
  - `~/.shuheng/workspaces/<workspace_id>/manifest.json`
  - `~/.shuheng/workspaces/<workspace_id>/memory.md`
  - `~/.shuheng/workspaces/<workspace_id>/index.json`
  - `~/.shuheng/workspaces/<workspace_id>/l4_index.json`
- Commands: `/workspace list`, `/workspace current`, `/workspace refresh`, and `/workspaces`.
- Context-pack field: `workspace_context` with `included`, `reason`, `workspace`, `items`, `refs`, and optional `l4`.
- Workspace id derivation: `<workspace-root-basename-slug>-<sha1(abs-root)[:8]>`.

### 3. Contracts

- Workspace ids are normalized filesystem-safe slugs; callers must not be able to escape `SHUHENG_WORKSPACES_DIR`.
- Workspace root inference uses the current process working directory's Git root when available; otherwise it uses the current working directory.
- Context-pack generation must call the automatic inference/ensure path. A fresh Shuheng home with no `active.json` still creates and hydrates the inferred workspace.
- Creating or refreshing a workspace writes a manifest, an initial `memory.md`, a generated `index.json`, and a generated non-destructive L4 index.
- `active.json` records the latest automatically inferred workspace for observability; it is not required for hydration.
- `build_context_pack()` hydrates workspace memory by default when automatic inference succeeds and the context is not Secret Vault.
- Workspace manifests must carry automatic provenance such as `selection_mode:"auto"`, source `auto.cwd_git_root`, and `root_aliases` containing the inferred root.
- L4 handling is index-only: `l4_index.json` stores `l4://<archive>/<member>` refs, archive/member metadata, counts, and samples. It must not unzip, delete, rewrite, or mine archive content.
- `memory_inventory()` reports workspace manifest, memory, workspace index, observation state, and L4 index files as `Workspace` entries without hiding legacy memory visibility.
- `memory_context_get` and OMP prompt generation consume the same app-layer context-pack behavior; plugins must not scrape workspace files directly.

### 4. Validation & Error Matrix

- No `active.json` -> context pack creates/refreshes the inferred workspace and contains `workspace_context.included:true`.
- Current directory inside a Git repo -> inferred root is the Git top-level directory.
- Current directory outside a Git repo -> inferred root is the current working directory.
- Root changes -> a different stable workspace id is inferred from the new absolute root.
- Secret Vault context -> normal workspace memory is not hydrated.
- `/workspace current` -> reports the inferred root, workspace id, memory path, index path, and L4 ref count.
- `/workspace refresh` -> regenerates the inferred workspace manifest/index/L4 index.
- L4 zip exists -> `l4_index.json` contains exact `l4://` refs.
- L4 zip read fails -> index row records the archive error, but workspace creation/context generation does not destructively modify archives.

### 5. Good/Base/Bad Cases

- Good: User launches Shuheng from a project repo; context packs automatically include `workspace_context.workspace.workspace_id` for that repo.
- Good: User runs `/workspace current` and sees the exact root used for automatic workspace memory.
- Base: A workspace has empty `memory.md`; context pack may include the workspace identity and an empty-memory marker but no invented facts.
- Base: L4 archives are indexed as cold refs so a future Memory Curator can cite exact zip members.
- Bad: OMP or a plugin writes directly to `~/.shuheng/workspaces/*/memory.md`.
- Bad: L4 indexing deletes raw sessions, rewrites zips, or mines facts into approved memory without candidate approval.
- Bad: Context hydration depends on a user running a prior workspace command before a new session becomes useful.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert workspace root and observation state paths are under `SHUHENG_HOME`.
- Tests must assert a fresh home with no `active.json` still produces `workspace_context.included:true`.
- Tests must assert nested current directories infer the Git top-level root.
- Tests must assert automatic workspace creation writes manifest/memory/index/L4 index files with `selection_mode:"auto"` and root aliases.
- Tests must assert automatic workspace memory appears in L2 project memory plus `workspace.project` hydration entries.
- Tests must assert L4 zip indexing creates exact `l4://` member refs and does not rewrite archive bytes.
- Tests must assert `/workspace` completion/command paths can list/current/refresh workspaces.
- Tests must assert `memory_inventory()` includes `Workspace` entries for manifest and memory files.

### 7. Wrong vs Correct

#### Wrong

```python
workspace_id = read_required_workspace_selection()
if not workspace_id:
    pack["workspace_context"] = {"included": False}
```

#### Correct

```python
manifest = ensure_auto_workspace(current_workspace_root())
workspace_context = workspace_context_payload(security_context=sub.security_context)
pack["workspace_context"] = workspace_context
```

## Scenario: Temporary Non-Persistent Main Sessions

### 1. Scope / Trigger

- Trigger: A user enters `/temp` to start a temporary main-agent session.
- Applies to: command routing, main-agent log path binding, session metadata, automatic naming/description/category jobs, durable UI system messages, memory candidate creation, token usage persistence, and background session switching.
- Non-goal: This is not a Secret Vault session and does not encrypt or restore temporary content. It is an in-memory session that disappears when closed or replaced.

### 2. Signatures

- Command: `/temp`.
- Runtime state field: `State.temporary_session:true`.
- Backend log path: `os.devnull`.
- UI title: `临时会话`.

### 3. Contracts

- `/temp` starts a fresh main-agent context and binds the active agent plus LLM backends to `os.devnull`.
- Temporary sessions must not create `model_responses*.txt` history logs.
- Temporary sessions must not write `session_meta.json`, session names, automatic title/description/category metadata, durable UI system messages, token usage registry rows, memory candidates, or direct subagent memory updates.
- If a normal task is running, `/temp` may park it as a background session and then open a temporary active session.
- If a temporary session is parked in the background and later restored, it remains temporary and keeps `os.devnull` as its backend log path.
- `/new` exits temporary mode and creates a normal persistent session log path under the Shuheng-owned `MODEL_RESPONSES_DIR`.
- Secret Vault mode blocks `/temp`; the user must lock Secret Vault before opening a normal temporary session.

### 4. Validation & Error Matrix

- `/temp` while a subagent chat is selected -> user-visible message asking to return to the main orchestrator first.
- `/temp` while Secret Vault is unlocked -> blocked by the normal-command isolation rule.
- Durable UI system message persistence in temporary mode -> no-op.
- Memory candidate or subagent memory write in temporary mode -> user-visible no-op.
- Automatic naming/description/category jobs in temporary mode -> no-op.

### 5. Tests Required

- `scripts/check_policy_gates.py` must assert `/temp` sets `State.temporary_session:true`, binds the active agent/client/backend log path to `os.devnull`, and exposes the command in completions.
- Tests must assert durable UI system message persistence writes no session metadata during temporary sessions.
- Tests must assert memory candidate creation writes no memory candidate or approval rows during temporary sessions.
- Tests must assert `/new` exits temporary mode and restores a normal `model_responses_*.txt` log path.

## Scenario: GA-TUI Agent Bridge And OMP Plugin Client

### 1. Scope / Trigger

- Trigger: Agent clients that are not directly launched by the TUI need Shuheng-owned project context and governed proposal submission.
- Applies to: `src/ga_tui/agent_bridge.py`, `shuheng-agent-bridge`, `python -m ga_tui.agent_bridge`, repo-managed OMP plugin files under `integrations/omp-ga-tui-plugin`, OMP `--tool` loading, and future Codex/Claude Code adapters that consume the same bridge contract.
- Non-goal: This bridge does not make OMP, Codex, Claude Code, or any plugin the owner of long-term memory, approval queues, schedule registries, task ledgers, artifacts, or traces.

### 2. Signatures

- Python module: `src/ga_tui/agent_bridge.py`.
- Console script: `shuheng-agent-bridge`.
- Module command: `python -m ga_tui.agent_bridge`.
- Bridge schema: `ga-tui.agent_bridge.v1`.
- Bridge actions: `metadata`, `query`, `memory_context_get`, `memory_candidate_submit`, and `proposal_submit`.
- JSON call shape:

```json
{
  "action": "memory_context_get",
  "args": {
    "target": "optional-subagent-id-or-name",
    "objective": "task objective",
    "task_id": "optional-task-id",
    "parent_task_id": "optional-parent-task-id"
  }
}
```

- OMP plugin package: `integrations/omp-ga-tui-plugin/package.json`.
- OMP custom tool entry: `integrations/omp-ga-tui-plugin/tools/index.ts`.
- OMP plugin tools: `ga_tui_context_get` and `ga_tui_memory_candidate_submit`.
- Environment keys:
  - `GA_TUI_REPO` or `GA_TUI_ROOT`: GenericAgent-TUI checkout used by the plugin when locating `src/ga_tui/agent_bridge.py`.
  - `GA_TUI_BRIDGE_PYTHON`: Python executable used by the OMP plugin, default `python3`.
  - `GENERICAGENT_ROOT`: GenericAgent root override consumed by `ga_tui.app` discovery.
  - `GA_TUI_HARNESS_DIR`: harness directory override for bridge tests or isolated runs.
  - `GA_TUI_SECRET_VAULT_DIR`: secret vault directory override for bridge tests or isolated runs.

### 3. Contracts

- `AgentBridgeService` must be a thin facade over existing app-owned services; it must not reimplement memory, approval, context-pack, or scheduler governance.
- `memory_context_get` must call the same app-layer `memory_context_get` query path used by OMP host tools and must return `ga-tui.query.v1` with `context_pack_ref` plus a JSON-safe context pack.
- `memory_candidate_submit` must call the same governed memory-candidate proposal path as OMP host tools and must return `ga-tui.proposal.v1`.
- Bridge-submitted memory candidates must use source provenance such as `agent:omp_plugin`, not pretend to be direct human or internal TUI writes.
- Long-term memory writes remain `candidate_only`; the bridge may queue memory candidates and approval rows but must not append to subagent memory files directly.
- The default OMP usage path should be process-local `omp --tool <repo>/integrations/omp-ga-tui-plugin/tools/index.ts` so a user can test the plugin without linking it into the system OMP plugin store.
- Persistent `omp plugin link <repo>/integrations/omp-ga-tui-plugin` is optional and must be documented as an explicit user choice.
- The OMP plugin must call the bridge CLI with `PYTHONPATH=<repo>/src` so it can run from a checkout without requiring package installation.
- The OMP plugin must not read or write GA-TUI JSONL stores directly.
- The OMP plugin must not call `queue_approval`, `queue_curated_memory_candidate`, scheduler helpers, or artifact writers itself; only Python GA-TUI code owns those operations.
- Bridge metadata must report owner `ga-tui.control_plane`, supported actions, relevant paths, and policy fields showing provider direct writes are disabled.

### 4. Validation & Error Matrix

- Bridge payload is not a JSON object -> `ga-tui.agent_bridge.v1` error.
- Unknown bridge action -> `ga-tui.agent_bridge.v1` error with `supported_actions`.
- `query` without endpoint -> `ga-tui.agent_bridge.v1` error.
- `memory_context_get` target not found or ambiguous -> `ga-tui.query.v1` error from the existing app query path.
- `memory_candidate_submit` without target or statement -> `ga-tui.proposal.v1` error.
- `memory_candidate_submit` target is temporary/non-persistent -> no direct memory write; return the existing governed no-op result.
- Candidate text contains secrets or weak/empty content -> existing Memory Curator rejection path writes a rejected candidate record and no approval row.
- OMP plugin cannot parse bridge stdout as JSON -> plugin tool execution throws a user-visible tool error instead of fabricating success.
- Bridge CLI exits non-zero with a structured error payload -> plugin returns that structured error payload to the model.

### 5. Good/Base/Bad Cases

- Good: OMP loads `ga_tui_context_get` through `--tool`, requests project context, and receives a context-pack artifact ref without mutating any ledger except the context-pack artifact index.
- Good: OMP calls `ga_tui_memory_candidate_submit`; GA-TUI validates the target, builds a memory-candidate artifact, appends a pending candidate row, queues a human approval, and records provenance.
- Base: A user links the plugin persistently with `omp plugin link` only after explicitly choosing to let OMP remember the repo-managed plugin.
- Base: Codex or Claude Code later calls the same bridge action names and gets the same schemas without OMP-specific contract names.
- Bad: A plugin writes directly to `${SUBAGENTS_DIR}/*/memory.md` or `memory_candidates.jsonl`.
- Bad: A plugin scrapes `context_packs/` or `subagents/` files directly instead of calling the bridge.
- Bad: The bridge adds a second memory-candidate schema instead of reusing `queue_curated_memory_candidate(...)`.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `AgentBridgeService` metadata includes `schema_version:"ga-tui.agent_bridge.v1"`, owner `ga-tui.control_plane`, supported bridge actions, and `provider_direct_writes:false`.
- Tests must assert bridge `memory_context_get` writes a context-pack artifact and returns a `ga-tui.query.v1` response with `context_pack_ref`.
- Tests must assert bridge `memory_candidate_submit` queues a `ga-tui.proposal.v1` memory candidate through the existing approval path and records source `agent:omp_plugin`.
- Tests must assert unknown bridge actions return a structured bridge error.
- Tests must assert the repo-managed OMP plugin manifest points to `tools/index.ts`.
- Tests must assert the OMP plugin tool source contains `ga_tui_context_get`, `ga_tui_memory_candidate_submit`, `ga_tui.agent_bridge`, and `PYTHONPATH=<repo>/src` wiring.
- Smoke checks should include `PYTHONPATH=src python3 -m ga_tui.agent_bridge ...`, Bun-loading the plugin tool factory, and a temporary-HOME OMP plugin dry-run or process-local `--tool` smoke so the user's real system OMP config is not mutated.

### 7. Wrong vs Correct

#### Wrong

```text
OMP plugin opens `${SUBAGENTS_DIR}/researcher/memory.md` and appends a learned fact directly.
```

#### Correct

```text
OMP plugin calls shuheng-agent-bridge memory-candidate-submit; Shuheng builds a memory_candidate.v1 record, writes artifact refs, queues human approval, and only approved memory writes reach subagent memory.
```
