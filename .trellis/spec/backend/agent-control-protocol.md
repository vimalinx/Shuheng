# Agent Control Protocol

> Executable contract for Shuheng compatibility control blocks and governed subagent delegation.

## Scenario: Shuheng Naming Surface

### 1. Scope / Trigger

- Trigger: The active product, package, protocol, runtime prompt, tool, docs, and release naming surface is `Shuheng` / `枢衡`.
- Applies to: `pyproject.toml` console scripts, installed console-script wrappers, package import paths, README command examples, integration doctor output, launcher-shim help text, HTTP gateway server/header identifiers, runtime prompts, control protocol schemas, OMP/tool descriptions, active non-archive Trellis task guidance, release checks, wheel/sdist smoke checks, and source distribution metadata.
- Non-goal: This does not remove internal compatibility adapters or quarantined historical prompt cleanup. Those internals must not appear in public release docs, default health-check output, bridge metadata path values, or release-readiness wording.

### 2. Signatures

- Primary console scripts: `shuheng`, `shuheng-agent-bridge`, `shuheng-check`, `shuheng-install-core-shim`, and `shuheng-integration`.
- Retired pre-Shuheng console-script aliases are not exported.
- Python package root: `src/shuheng`.
- Python module entry remains `python -m shuheng` / `python -m shuheng.app`.
- Distribution name in `pyproject.toml`: `shuheng`.
- Current control schema and hidden block: `shuheng-control.v2` and `<shuheng-control>...</shuheng-control>`.
- Current OMP proposal type for governed controls: `proposal_type:"shuheng_control"`.
- Canonical public environment variables use `SHUHENG_*`.
- Default health check: `shuheng-check` / `python -m shuheng.integration doctor`.
- Explicit compatibility check: `python -m shuheng.integration doctor --root <checkout>`.
- Bridge metadata path key: `external_runtime_checkout_configured` is boolean-only and must not expose a local checkout path.

### 3. Contracts

- User-facing docs and doctor output should prefer `Shuheng` and `shuheng*` commands.
- User-facing docs and doctor output must not advertise retired pre-Shuheng aliases as current entry points.
- Current protocol parsers must accept Shuheng control blocks/fences only.
- `shuheng_query`, `shuheng_propose`, and typed OMP tools are Shuheng host tools. They may expose compatibility behavior only through bounded, governed Shuheng schemas.
- OhMyPi / OMP is the default runtime core.
- Default `shuheng-check` must not auto-discover or print optional external runtime checkout details; it validates the Shuheng core by default.
- Explicit `--root` compatibility validation may report configured/unconfigured status, but it must not echo local absolute checkout paths or retired runtime branding.
- Public README, contribution docs, public alpha docs, GitHub issue templates, release-readiness metadata, provider notes, and bridge metadata must describe the final Shuheng source of truth without naming retired runtime branding.
- Archived Trellis task logs and quarantined compatibility cleanup may contain historical facts; active specs and current release-facing docs must describe Shuheng/OMP as the source of truth.

### 4. Validation & Error Matrix

- Missing `shuheng*` console script in `pyproject.toml` -> packaging regression.
- Retired pre-Shuheng console script in `pyproject.toml` -> naming regression.
- Built package metadata refers to the retired pre-Shuheng package or plugin directory -> package metadata regression.
- Built wheel/sdist text members include retired pre-Shuheng package, console-script, protocol, proposal, or old TUI product identifiers -> release artifact naming regression.
- Active parser regexes still target retired control blocks/fences -> protocol regression.
- OMP host-tool proposal enum still exposes a retired control proposal type -> tool API naming regression.
- Doctor output requires an optional external checkout for ordinary Shuheng checks -> runtime ownership regression.
- Runtime strings identify the main orchestrator as a retired TUI alias or as an external core runtime -> product identity regression.
- HTTP gateway `Server` headers or handler `server_version` identify the service with a retired TUI alias -> product identity regression.
- Active non-archive Trellis task guidance points future work at retired package paths, module commands, control schemas, bridge metadata keys, or external-runtime-as-root language -> development guidance regression.
- Public release wording files mention retired runtime branding -> release hygiene regression.
- Bridge metadata exposes a local external runtime checkout path instead of a boolean configured flag -> metadata privacy regression.

### 5. Good/Base/Bad Cases

- Good: `shuheng-check` reports `Shuheng root`, `Core runtime: OhMyPi / OMP`, `Launch without legacy patches: shuheng`, and `Status: OK`.
- Good: `python -m shuheng --help`, `python -m shuheng.integration doctor`, and package smoke checks run without requiring any optional external checkout.
- Good: the local gateway response header contains `ShuhengGateway/1` and installed `shuheng*` wrappers import from `shuheng.*`.
- Base: explicit compatibility checks can be run with `--root <checkout>` when a local adapter validation task needs it.
- Bad: Re-adding retired pre-Shuheng commands, module docs, env aliases, or proposal types as active behavior.
- Bad: Describing an optional external adapter as the Shuheng root/core runtime.
- Bad: `shuheng-check` or gateway wrappers are exported with Shuheng command names but still import from retired module names.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `pyproject.toml` contains all primary `shuheng*` scripts and no retired pre-Shuheng scripts.
- Tests must assert integration doctor report identifies OhMyPi / OMP as the core runtime and avoids optional adapter branding in default output.
- Tests must assert default integration doctor output contains no retired runtime branding and does not auto-print optional checkout details.
- Tests must assert bridge metadata exposes `external_runtime_checkout_configured` as a boolean and does not expose external checkout paths.
- Release hygiene must assert public release wording files contain no retired runtime branding.
- Tests must assert parser regexes, hidden control examples, and OMP proposal schemas use `shuheng-control.v2` / `shuheng_control`.
- Tests must assert release/wheel smoke metadata uses `src/shuheng`, `shuheng` top-level package, and `integrations/omp-shuheng-plugin`.
- Tests must assert active non-archive Trellis task guidance uses current Shuheng package paths, module commands, control schemas, and legacy-provider checkout wording.
- `scripts/wheel_smoke.py` must scan built wheel and sdist text members for retired pre-Shuheng public naming fragments.
- Tests must assert exit prompts, exit reasons, and terminal shutdown text use Shuheng/枢衡 instead of retired product aliases.
- `scripts/check_policy_gates.py` must assert `GatewayRequestHandler.server_version` and a live gateway HTTP response header use `ShuhengGateway/1`, not a retired TUI alias.
- `python3 -m compileall -q src scripts`, `python3 scripts/check_policy_gates.py`, `git diff --check`, and `shuheng-check` must pass.

### 7. Wrong vs Correct

#### Wrong

Move the package to `src/shuheng` but leave built metadata, parser regexes, host-tool enums, public docs, default health checks, or bridge metadata pointing at retired identities or external-runtime-as-core.

#### Correct

Expose Shuheng as the canonical package, CLI, protocol, tool, runtime prompt, docs, and release identity. Keep compatibility internals bounded and absent from public release wording/default outputs.

## Scenario: Open-Source Release Hygiene

### 1. Scope / Trigger

- Trigger: Shuheng is prepared for a public open-source alpha release.
- Applies to: root governance files, package metadata, README release commands,
  CONTRIBUTING local-check commands, GitHub Actions CI, source distribution
  contents, release-readiness metadata, ignored local/private paths, and OMP
  plugin public wording.
- Non-goal: This does not publish the repository, change the remote URL, certify
  A2A/MCP protocol compliance, add production remote gateway auth, or rename
  internal compatibility identifiers such as `src/shuheng`, `SHUHENG_*`,
  `shuheng_query`, and `shuheng.*` schemas.

### 2. Signatures

- Required governance files: `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, and `CHANGELOG.md`.
- Release guard command: `python3 scripts/check_release_hygiene.py`.
- CI workflow: `.github/workflows/ci.yml`.
- Package metadata source: `pyproject.toml`.
- Source distribution manifest: `MANIFEST.in`.
- Ignored private/local paths: `config/*.json`, `references/`, `.codex/`,
  `goal-*`, `memory/`, `temp/`, `tmp/`, local Trellis runtime/cache files,
  `docs/foreign-student-acquisition-research.md`, and
  `docs/homework-pricing-research.md`.
- Local dependency lock: `uv.lock` is ignored for this package-style alpha
  unless a future task explicitly adopts uv-locked application releases.
- Public wording files guarded by release hygiene: `README.md`,
  `README.en.md`, `CONTRIBUTING.md`, `docs/public-alpha-readiness.md`,
  `docs/runtime-provider-control-plane.md`, `docs/app-py-decomposition-plan.md`,
  and `.github/ISSUE_TEMPLATE/bug_report.md`.

### 3. Contracts

- Public release posture stays `experimental local alpha`.
- `scripts/check_release_hygiene.py` must fail on missing governance files,
  missing release scripts, missing package metadata, public legacy `shuheng*`
  console scripts, unignored private/local paths, realistic secret literals,
  local absolute user paths in public files, missing MANIFEST public
  inclusions/private exclusions, or missing public alpha/security wording.
- Public secret/local literal scanning must include packaged test files because
  `tests/` is part of the source distribution.
- Public wording files must not mention retired runtime branding; describe
  Shuheng/OMP as the public source of truth and use provider-neutral
  compatibility wording for explicit adapter checks.
- CI must run Ruff check, release hygiene, policy gates, runtime smoke, pytest,
  compileall, package build, wheel smoke, and `git diff --check`.
- `CONTRIBUTING.md` must list the same reproducible local release checks so
  contributor guidance cannot drift behind CI.
- CI Python matrix must cover the package's minimum `requires-python` version
  and the highest `Programming Language :: Python :: X.Y` classifier advertised
  in `pyproject.toml`.
- CI and README release-command examples must run wheel smoke in its default
  dependency-resolving mode for both the built wheel and the built sdist;
  `--no-deps` and `--wheel-only` are explicit local debugging options and must
  not appear in public release gates.
- `release_readiness_report(...)` must expose repository hygiene booleans and
  include repository-hygiene gaps only when required files are missing.
- `release_readiness_report(...)` must expose a structured
  `distribution_smoke` contract with wheel+sdist artifacts,
  dependency-resolving install mode, public console scripts, checked entrypoint
  behaviors, and debug-only options that are not release gates.
- The sdist must include intended public docs and integration plugin files while
  excluding private research/config/reference paths.
- Wheel smoke must inspect the built wheel archive contents directly so the
  release gate proves wheel metadata, license, entry points, package modules,
  and private/local path exclusions before install.
- Wheel smoke must verify built wheel `RECORD` entries so every non-`RECORD`
  member has a matching `sha256=` hash and byte size before install.
- Wheel smoke must inspect the built sdist archive contents directly so the
  release gate proves the actual tarball, not only `MANIFEST.in` intent.
- Wheel smoke must verify built sdist metadata directly so top-level
  `PKG-INFO`, `src/shuheng.egg-info/PKG-INFO`, `entry_points.txt`, and
  `top_level.txt` prove package name/version and public console scripts before
  install.
- Wheel smoke must verify built sdist `src/shuheng.egg-info/SOURCES.txt`
  directly so the sdist's own file manifest matches actual tarball file
  members, except build-generated top-level `PKG-INFO` and `setup.cfg` members.
- Wheel smoke must scan built wheel and sdist artifact member contents for
  realistic secret-like literals and local absolute paths, not only source
  checkout files.
- Realistic secret/local path scan regexes must live in
  `scripts/release_scan_rules.py`; repository hygiene and wheel/sdist smoke
  checks must import that shared source instead of carrying duplicate regex
  tuples.
- OMP plugin user-facing labels and docs should say Shuheng. Compatibility tool
  ids may remain `shuheng_*`.

### 4. Validation & Error Matrix

- Missing `LICENSE` / `SECURITY.md` / CI -> release hygiene fails.
- Missing `scripts/runtime_smoke.py` or `scripts/wheel_smoke.py` -> release
  hygiene fails.
- `config/mcporter.json` or private research docs are tracked or unignored ->
  release hygiene fails.
- Local runtime state such as `memory/`, `temp/`, `tmp/`, `goal-*`, `.codex/`,
  or local Trellis runtime/cache files are tracked or unignored -> release
  hygiene fails.
- MANIFEST drops release scripts or private-path exclusions -> release hygiene
  fails.
- Built sdist archive omits required public docs/scripts/tests or contains
  private/local paths such as `config/`, `.trellis/`, `memory/`, `temp/`,
  `tmp/`, `goal-*`, or private research docs -> wheel smoke fails.
- Built sdist metadata omits `Name: shuheng`, `Version`, `shuheng` top-level
  package, or any public console-script entry point -> wheel smoke fails.
- Built sdist `SOURCES.txt` is missing, has duplicate/unsafe rows, omits a real
  archive file member, or references a file that is not in the archive -> wheel
  smoke fails.
- Built wheel archive omits required `shuheng` package modules, dist-info
  metadata, license, or public console-script entry point metadata, or contains
  private/local paths -> wheel smoke fails.
- Built wheel `RECORD` omits an archive member, contains rows for missing
  members, uses a non-sha256 hash, or has a hash/size mismatch -> wheel smoke
  fails.
- Built wheel or sdist artifact member content contains realistic API
  key/private-key material or local absolute user paths -> wheel smoke fails.
- `scripts/check_release_hygiene.py` and `scripts/wheel_smoke.py` define their
  own secret/local regex tuples instead of importing `release_scan_rules.py` ->
  release-rule drift risk.
- CI or README release smoke uses `scripts/wheel_smoke.py --no-deps` or
  `--wheel-only` -> release hygiene fails because the public gate no longer
  matches real wheel+sdist installation.
- Public file contains realistic API key/private-key material -> release hygiene
  fails.
- Public file contains a local absolute user path -> release hygiene fails.
- Public wording file mentions retired runtime branding -> release hygiene
  fails.
- `uv.lock` shows as an untracked commit candidate -> release preparation is not
  clean because local dependency resolution state is not intentionally tracked.
- Packaged test file contains realistic API key/private-key material or local
  absolute user paths -> release hygiene fails.
- `pyproject.toml` exports public `shuheng*` scripts -> release hygiene fails.
- CI matrix omits the minimum supported Python version or highest advertised
  Python classifier -> release hygiene fails.
- CI omits `git diff --check` -> release hygiene fails because whitespace and
  generated-diff cleanliness are no longer enforced in the public gate.
- `CONTRIBUTING.md` omits runtime smoke, wheel smoke, package build, or another
  public release command -> release hygiene fails.
- OMP plugin package name is not Shuheng-branded -> release hygiene fails.
- `release_readiness_report(...)` is called with all hygiene booleans true ->
  known gaps do not include repository-level hygiene.
- `release_readiness_report(...)` lacks `distribution_smoke.artifacts:["wheel",
  "sdist"]` or says `install_mode:"no_deps"` -> release posture regression.

### 5. Good/Base/Bad Cases

- Good: `scripts/check_release_hygiene.py` passes, wheel smoke installs both
  the latest wheel and sdist, and the sdist contains `README.en.md`,
  `SECURITY.md`, docs, release scripts, and the OMP plugin, but not private
  research docs or local runtime state.
- Good: `@shuheng/omp-bridge` exposes compatibility tool names
  `shuheng_context_get` and `shuheng_memory_candidate_submit`.
- Good: `git status --short` does not show `uv.lock`, because it is ignored as
  local dependency resolution state.
- Base: Internal schemas and env names keep `shuheng` / `SHUHENG` identifiers for
  compatibility.
- Bad: Publishing `docs/homework-pricing-research.md` or a machine-specific MCP
  config in the public repository.
- Bad: Claiming full A2A/MCP certification without real third-party client E2E
  evidence.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert release-readiness metadata reports
  true license/CI/security booleans and lists release hygiene, Ruff, runtime
  smoke, package build, wheel smoke, `shuheng-check`, and `git diff --check`
  commands.
- `scripts/check_policy_gates.py` must assert release-readiness metadata exposes
  structured wheel+sdist distribution-smoke evidence, dependency-resolving
  install mode, public console script names, isolated `shuheng-check`, and
  debug-only options such as `--no-deps` / `--wheel-only`.
- CI must run `scripts/check_release_hygiene.py`.
- `scripts/check_release_hygiene.py` must assert the GitHub Actions Python
  matrix includes the `requires-python` lower bound and the highest declared
  Python version classifier.
- Manual release verification must run: Ruff check, release hygiene, policy
  gates, runtime smoke, pytest, compileall, build, wheel smoke, isolated wheel
  `shuheng-check`, and `git diff --check`.
- Wheel smoke must assert all public console scripts are installed from both
  the latest wheel and latest sdist. It must inspect the wheel archive member
  list for required modules, dist-info metadata, license, entry points, and
  forbidden private/local paths before installing the wheel. It must verify
  wheel `RECORD` sha256 hashes and byte sizes before installing the wheel. It
  must inspect the sdist archive member list for required public files and
  forbidden private/local paths before installing the sdist. It must verify
  sdist `PKG-INFO`, `src/shuheng.egg-info/PKG-INFO`,
  `src/shuheng.egg-info/entry_points.txt`, and
  `src/shuheng.egg-info/top_level.txt` before installing the sdist. It must
  verify `src/shuheng.egg-info/SOURCES.txt` against actual sdist file members,
  allowing only build-generated top-level `PKG-INFO` and `setup.cfg` to be
  absent from the manifest. It must
  scan both artifact contents for realistic secret-like literals and local
  absolute user paths before installing either artifact. It may run `--help`
  for helper scripts that do not import the full TUI runtime, must run
  `shuheng --help` after each dependency-resolving install, and must run
  installed `shuheng-check` in an isolated install.
- Release hygiene and wheel smoke tests must keep realistic secret/local path
  scanning sourced from `scripts/release_scan_rules.py`, and the shared helper
  must be included in MANIFEST/sdist and public Ruff command lists.
- `scripts/check_release_hygiene.py` must assert README and CI release commands
  use `scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist` without
  `--no-deps` or `--wheel-only`.
- `scripts/check_release_hygiene.py` must assert CI runs `git diff --check`.
- `scripts/check_release_hygiene.py` must assert `CONTRIBUTING.md` lists the
  current public release-check commands.
- `scripts/check_release_hygiene.py` must assert public wording files contain no
  retired runtime branding.
- `scripts/check_release_hygiene.py` must assert runtime state directories such
  as `memory/`, `temp/`, `tmp/`, `goal-*`, and local Trellis runtime/cache files
  are not tracked or unignored and stay excluded from the release manifest.
- `scripts/check_release_hygiene.py` must assert packaged tests are included in
  public secret/local literal scanning.

### 7. Wrong vs Correct

#### Wrong

```text
Publish the repository with local config, private research notes, no license,
and README claims that A2A/MCP are certified production surfaces.
```

#### Correct

```text
Publish as experimental local alpha with MIT license, security/contributing
docs, CI, release hygiene checks, private-path exclusions, compatibility wording,
and explicit known gaps for gateway auth, protocol certification, heuristic eval,
and app.py monolith risk.
```

## Scenario: Session History Titles Ignore Process Summaries

### 1. Scope / Trigger

- Trigger: Runtime providers can emit foldable process blocks such as `**LLM Running (Turn 1) ...**`, `<summary>specific thinking excerpt</summary>`, legacy `<summary>OMP 思考</summary>`, `<thinking>...</thinking>`, tool-call blocks, and tool result fences.
- Applies to: session history preview caching, sidebar title fallback, restored-session preview messages, AI-generated title/description context, internal workflow/subagent task logs, and `session_meta.json` cache reuse.
- Non-goal: This does not remove process summaries from the main transcript renderer. Folded process summaries remain visible as process UI labels when rendering the assistant message itself.

### 2. Signatures

- History row source: `cached_session_rows(state, exclude_pid)` returns `(path, last_user_at, preview, rounds, description)`.
- Sidebar display source: `load_history()` maps `session_names.json` or `preview` into `state.history_names`.
- Sidebar title limit: `SESSION_TITLE_CHARS == 16`; all normal, manual, local, and AI-maintained sidebar names pass through `normalize_session_title(...)` / `history_titles.short_session_title(...)`.
- Recent row selector: `history_store.recent_history_items(history_entries, used_paths, limit)`, wrapped by `app.recent_history_items(...)` for the current default recent-session limit.
- Restore preview compaction: `history_store.compact_ui_preview_messages_from_pairs(...)`, wrapped by `app.compact_ui_preview_messages_from_pairs(...)` to inject app-owned prompt parsing, assistant preview shaping, and default loaded-round count.
- Restore message shaping: `history_store.history_round_count(...)`, `history_store.extract_recent_ui_messages_from_pairs(...)`, and `history_store.history_messages_from_pairs(...)`, wrapped by `app.py` to inject app-owned prompt parsing, tool-result extraction, response-segment formatting, and default loaded-round count.
- Transcript message selector: `history_store.latest_user_message_text(messages)`, re-exported from `app.py` for compatibility.
- Process filtering/title helpers: `history_titles.clamp_session_title_chars()`, `history_titles.short_session_title()`, `history_titles.session_preview_from_pairs()`, `history_titles.session_response_preview_text()`, `history_titles.session_summary_titles_from_text()`, `history_titles.history_cache_has_process_only_preview()`, `history_titles.message_text_for_metadata_context()`, and `history_titles.suggested_session_title()`, wrapped by `app.py` where app-owned prompt parsing or visible-reply extraction is still required.
- Internal task filtering helpers: `history_titles.is_internal_task_session_title()` and `history_titles.history_cache_has_internal_task_preview()` identify workflow fixture/worker-step prompts and subagent work-order transcripts that must not appear as normal user sessions.
- Low-level response-body parser: `history_store.assistant_text_from_response_body(response_body)`, re-exported from `app.py` for compatibility.
- AI metadata refresh source: `generate_ai_session_metadata(agent, messages)` asks once for JSON shaped as `{"title":"...","description":"..."}` and persists title metadata through `description_done` only when the existing title is not manual.
- Persisted title metadata fields: `title_source`, `title_signature`, and `title_updated_at`; manual titles use `title_source:"manual"`, AI/local-maintained titles use `title_source:"ai"`.

### 3. Contracts

- Process-only summaries must not become `preview`, `description`, `ui_preview_messages`, `state.history_names`, or AI metadata context.
- Internal workflow/subagent task logs must not become normal sidebar sessions. They are hidden with `hidden_internal_task_log:true` in `session_meta.json` and the raw transcript file remains untouched.
- If a response contains process markers, `<summary>` content belongs to process rendering, not session naming.
- For process-marked responses, sidebar title fallback should prefer the first user message, then visible final assistant prose.
- Existing cached metadata that already contains process-only preview text must be invalidated and recomputed from the raw model response file.
- Explicit user names in `session_names.json` win unless they are process-only labels such as `OMP 思考`.
- Persisted sidebar titles must be concrete descriptions of 16 characters or fewer. Display width may be wider for layout, but storage/display text is character-clamped.
- Main-runtime `session.rename` remains a valid persisted title path and records model-owned title changes as `title_source:"ai"`.
- Inline AI metadata jobs may maintain both title and description in one request. They write a title only when `title_source` is not `manual`, and write `title_signature` from the process-safe user/assistant content signature.
- Local title fallback for non-inline metadata agents may persist `suggested_session_title(...)` as `title_source:"ai"` with `title_signature`; it must use the same process-summary-safe and 16-character title policy.
- Manual `/rename` or history rename writes `title_source:"manual"` and must not be overwritten by later model-owned `session.rename`, inline metadata refresh, or local fallback.
- A valid `session_meta.json` cache entry with matching `cache_mtime`, `cache_size`, `hidden_subagent_log`, `preview`, `rounds`, `last_user_at`, and `ui_preview_messages` must be served without sampling the transcript file.
- A valid `hidden_internal_task_log:true` entry with matching `cache_mtime` and `cache_size` must be skipped without sampling the transcript file.
- Recent virtual history rows must be selected by normalized source path and descending positive activity timestamp, without mutating metadata or reading `State`.
- Transcript bridge user prompt selection must scan stored `Message` rows from newest to oldest and return the stripped content of the newest non-empty `user` message.
- Standalone progress-dot deltas from OMP (`.` on its own line) are process noise and must not render in the transcript.
- Current OMP thinking process summaries should use a compact excerpt of the thinking text, not the fixed label `OMP 思考`.
- Legacy process blocks with `<summary>OMP 思考</summary>` should render a compact excerpt from the `<thinking>` body.
- `assistant_text_from_response_body(...)` belongs to `history_store.py` because it parses stored model response block bodies into assistant text without reading `State`, session metadata, Web Console payloads, or rendering state.
- `assistant_text_from_response_body(...)` must preserve the stored-transcript parser contract: Python literal response lists join text dicts and string blocks, response dicts read `content` text lists or fallback `content`/`text` fields, malformed bodies fall back to cleaned raw text, and non-text literal values fall back to cleaned strings.
- `recent_history_items(...)` belongs to `history_store.py` because it is a pure history row selector. It may depend on `path_utils.normalized_path(...)` but must not import the app facade to learn storage roots or UI state.
- `compact_ui_preview_messages_from_pairs(...)` belongs to `history_store.py` because it is pure restore-preview message shaping over already-parsed transcript pairs. It accepts prompt-text and assistant-preview callables from the app facade and must not parse/write transcript files, inspect `State`, or own process-summary title policy.
- `history_round_count(...)`, `extract_recent_ui_messages_from_pairs(...)`, and `history_messages_from_pairs(...)` belong to `history_store.py` because they shape already-parsed transcript pairs into recent restore message records. They accept app-provided prompt/tool/response-format callables and must not parse transcript files, switch providers, reset runtime backends, inspect UI state, write metadata, or own process-summary title policy.
- `latest_user_message_text(...)` belongs to `history_store.py` because it is a pure transcript helper. The higher-level `persist_transcript_bridge_turn(...)` stays in `app.py` because it owns provider/runtime checks, temporary-session policy, and normal-session path validation.
- `clamp_session_title_chars(...)`, `short_session_title(...)`, `compact_description(...)`, `text_has_process_markers(...)`, `session_summary_titles_from_text(...)`, `session_response_preview_text(...)`, `session_preview_from_pairs(...)`, `is_process_only_session_title(...)`, `history_cache_has_process_only_preview(...)`, `is_internal_task_session_title(...)`, `history_cache_has_internal_task_preview(...)`, `message_text_for_metadata_context(...)`, `session_description_from_pairs(...)`, and `suggested_session_title(...)` belong to `history_titles.py` because they are process-summary-safe title/preview/description policy over already-parsed text, response bodies, message rows, or transcript pairs. App wrappers inject `_user_text(...)`, `latest_visible_reply_text(...)`, and current display limits where those dependencies remain app/rendering-owned.
- `history_store.py` must not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, Web Console, dashboard, runtime dispatch, command handlers, or renderer functions.
- `history_titles.py` must not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, Web Console, dashboard, runtime dispatch, command handlers, or renderer functions.

### 4. Validation & Error Matrix

- Raw response has `<summary>OMP 思考</summary>` plus final visible prose -> sidebar title uses the user task, not `OMP 思考`.
- Stored response body is a Python literal list/dict -> low-level parser returns the same assistant text that preview/title policy consumes.
- Stored response body is malformed -> low-level parser returns cleaned raw text rather than raising and breaking history restoration.
- Recent selector receives rows with timestamps `30`, `10`, and `0` -> returns the `30` then `10` rows and excludes the `0` row.
- Recent selector receives a `used_paths` set containing a normalized row path -> excludes that row from the virtual Recent group.
- Restore preview compaction receives three non-empty user rounds and a two-round limit -> returns only the last two user rounds and their non-`执行中` assistant previews.
- Restore message shaping receives promptless follow-up pairs between user turns -> groups them into the current assistant message with increasing `LLM Running (Turn N)` process markers.
- Transcript helper receives assistant/system rows plus blank user rows -> returns `""`.
- Transcript helper receives multiple user rows where the newest non-empty content has surrounding spaces -> returns that newest content stripped.
- Cached metadata has `preview:"OMP 思考"` and matching file mtime/size -> cache is treated stale and recomputed.
- Cached metadata has a matching file mtime/size and all required non-process cache fields -> history rows are returned without `sample_file_text(...)` or transcript parsing.
- Transcript first user text is `Review source quality.`, `Collect evidence refs.`, `Use upstream refs. ...`, or `Do unrelated work.` -> the row is marked `hidden_internal_task_log:true` and omitted from sidebar history.
- Transcript first user text is a `╭─ 子 Agent 工作单` work order with target/dispatch metadata -> the row is marked `hidden_internal_task_log:true` and omitted from sidebar history.
- User asks a real question containing the words `review source quality` -> the row remains visible because the internal filter matches only exact worker-step/task-log shapes.
- AI metadata context includes a process block -> context includes user text and visible final prose, not hidden thinking text.
- AI metadata returns a long title -> the persisted sidebar title is clamped to at most 16 characters.
- AI metadata returns a new title for a new content signature -> the unlocked AI-owned sidebar title updates and `title_signature` changes.
- Non-inline metadata runtime gets new process-safe user content -> local fallback may persist a 16-character AI-owned title without calling `raw_ask`.
- Model-owned `session.rename` sees `title_source:"manual"` -> it does not overwrite the title.
- Inline metadata refresh sees `title_source:"manual"` -> it may update description but does not overwrite the title.
- Main-runtime `session.rename` changes an unlocked AI-owned title -> title source remains `ai`; the same control against a manual title is skipped.
- Main transcript renderer sees process blocks -> folded process UI still shows the process label.
- Main transcript renderer sees a legacy thinking block plus a standalone `.` line -> renders the thinking excerpt and suppresses the dot line.
- Main transcript renderer sees multiple `LLM Running` blocks in one assistant message -> collapsed view shows one `过程组 G...` row, not one visible `过程 Turn ...` row per process block; intermediate progress prose stays inside the expandable group while the final user-facing reply remains visible outside the group.
- Main transcript renderer sees a substantive user-facing reply before later housekeeping process turns -> the substantive reply remains visible outside the collapsed group instead of being replaced by a short "nothing further" cleanup sentence.
- Main transcript renderer sees OMP `irc` tool results with `Reply from ...` payloads -> bounded IRC reply snippets remain visible outside the collapsed group while raw receipts, tool ids, and tool JSON stay folded.

### 5. Good/Base/Bad Cases

- Good: History row title is `修复左栏历史会话标题` while restored assistant preview says `已完成历史会话标题修复`.
- Good: A long AI-generated sidebar title is stored as a specific 16-character-or-shorter description.
- Good: Valid cached history metadata renders the sidebar row without re-sampling a large transcript file.
- Good: Workflow test/worker rows such as `Review source quality`, `Collect evidence refs`, `Use upstream refs`, and `Do unrelated work` disappear from `SESSIONS`, while real user conversations stay visible.
- Good: Subagent work-order transcripts are preserved on disk but do not clutter the main sidebar.
- Good: Main transcript shows `过程 Turn 15: Let me observe the page...`, not `过程 Turn 15: OMP 思考`.
- Good: A long OMP research turn with many thinking/tool/status blocks renders as one expandable `过程组` plus the final report, not dozens of separate `过程 Turn` lines.
- Good: An OMP IRC demo shows the final conclusion and `IRC 回复` snippets from DemoAlpha/DemoBeta even if later turns only close the demo agents.
- Base: A normal non-process assistant `<summary>` can still be used as a title candidate.
- Base: The low-level response-body parser may return process-marked text; higher-level preview/title helpers still own process-summary filtering.
- Base: `app.recent_history_items(...)` remains the compatibility wrapper that supplies `RECENT_SESSION_LIMIT` when no explicit limit is passed.
- Base: `app.compact_ui_preview_messages_from_pairs(...)` remains the compatibility wrapper that supplies `RESTORE_DISPLAY_ROUNDS`, `_user_text`, and `session_response_preview_text`.
- Base: `app.history_messages_from_pairs(...)` remains the compatibility wrapper that supplies `RESTORE_DISPLAY_ROUNDS`, `_user_text`, `_tool_results_from_prompt`, `_format_response_segment`, and `Message` conversion behavior through `history_store.py`.
- Base: `app.latest_user_message_text` remains a direct compatibility alias for callers in transcript bridge code.
- Bad: Sidebar `Recent` shows `OMP 思考`, `执行中`, or a tool-call label as the session title.
- Bad: Sidebar names store long prompt-like sentences, generic labels, or strings longer than 16 characters.
- Bad: Startup scans every historical transcript with `sample_file_text(...)` even when cache identity and required cache fields are current.
- Bad: Internal worker/test prompts show up as `S196 Review source qu` or similar normal sidebar sessions.
- Bad: `history_store.py` imports `app.py` so it can call `latest_visible_reply_text(...)`.
- Bad: `history_store.py` imports app runtime provider helpers just to decide whether to persist a transcript bridge turn.
- Bad: Recent selection compares raw paths without normalization, causing duplicate sidebar rows when callers pass normalized `used_paths`.
- Bad: Main transcript shows standalone `.` lines between process turns.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert OMP process summaries do not title history rows.
- `scripts/check_policy_gates.py` must assert `assistant_text_from_response_body` is owned by `history_store.py`, re-exported by `app.py`, and that `history_store.py` has no reverse import into `app.py` or curses/TUI/rendering/Web/dashboard dependencies.
- `scripts/check_policy_gates.py` must assert `recent_history_items` is owned by `history_store.py`, app wrapper parity holds, zero-activity rows are excluded, and normalized `used_paths` de-duplicate virtual history groups.
- `scripts/check_policy_gates.py` must assert `compact_ui_preview_messages_from_pairs` is owned by `history_store.py`, app wrapper parity holds, recent-round selection works, blank user prompts are skipped, and `执行中` assistant previews are excluded.
- `scripts/check_policy_gates.py` must assert restore message shaping helpers are owned by `history_store.py`, app wrapper parity holds, user-round fallback works, promptless follow-up turns are grouped into assistant process markers, and loaded/total restore counts are preserved.
- `scripts/check_policy_gates.py` must assert `latest_user_message_text` is owned by `history_store.py`, app alias parity holds, blank user rows are skipped, and the newest non-empty user content wins.
- `scripts/check_policy_gates.py` must assert history title policy helpers are owned by `history_titles.py`, app wrapper parity holds, session titles clamp to 16 characters, process-only summaries are excluded, normal non-process summaries remain valid title candidates, metadata-context text strips hidden process/control blocks, and `history_titles.py` has no reverse import into `app.py` or curses/TUI/rendering/Web/dashboard/runtime dependencies.
- `scripts/check_policy_gates.py` must assert valid cached history rows with matching mtime/size and required cache fields do not call `sample_file_text(...)`.
- `scripts/check_policy_gates.py` must assert exact internal workflow-step prompts and subagent work-order transcripts are hidden from `load_history()`, but real user questions that merely contain similar words remain visible.
- Unit tests must assert response-body parser behavior for list bodies, dict `content` lists, dict fallback fields, and malformed raw bodies.
- Unit tests must assert recent-history sorting, limit behavior, zero-timestamp exclusion, used-path de-duplication, and app wrapper parity.
- Unit tests must assert transcript helper newest-user selection, blank-user skipping, no-user fallback, and app alias parity.
- The test must seed a stale `session_meta.json` cache with `preview:"OMP 思考"` to prove cache invalidation.
- The test must assert restored preview messages and AI metadata context exclude process-only summary and hidden reasoning.
- Tests must assert automatic persisted title maintenance can use inline AI metadata or model-owned `session.rename`, title updates are marked AI-owned, content-signature changes can update unlocked AI titles, and manual titles remain stable.
- Tests must assert inline metadata title/description maintenance uses one JSON metadata request rather than separate title and description prompts.
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

#### Wrong

```python
# history_store.py
from shuheng.app import RECENT_SESSION_LIMIT, normalized_path
```

#### Correct

```python
# history_store.py
from shuheng import path_utils

def recent_history_items(history_entries, used_paths, limit):
    ...
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
- Tests must assert runtime-agent execution for this command does not prepend `[Shuheng Context Pack]` and records `runtime_context_mode:"lean"`.
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

## Scenario: Dashboard Home Pages And dashboard.update

### 1. Scope / Trigger

- Trigger: The TUI has dedicated home pages for the main Shuheng Orchestrator and persistent subagents, plus a governed `dashboard.update` control action.
- Applies to: startup `State.selected_session`, left/right sidebar selection, `/home`, `/chat`, `/agent-dashboard`, `dashboard.v1` parsing, subagent metadata persistence, main home rendering, persistent-subagent home rendering, and TUI control extraction.
- Non-goal: This does not create a new scheduler implementation, a new artifact store, executable UI widgets, direct memory writes, or dashboard-driven approval decisions.

### 2. Signatures

- UI-only home keys:
  - Main home: `MAIN_HOME_SESSION_KEY == "__home__:main"`.
  - Scheduled-report home: `SCHEDULED_REPORTS_SESSION_KEY == "__home__:scheduled_reports"`.
  - Persistent subagent home: `subagent_home_session_key(agent_id) == "__home__:sub:<safe-agent-id>"`.
- Pure home-key helpers live in `subagent_store.py` and are re-exported from `app.py` for compatibility.
- Commands:
  - `/home [agent]` opens the main home, current persistent-agent home, or named persistent-agent home.
  - `/reports` or `/home reports` opens the scheduled-report home page next to the main home entry.
  - `/chat` switches from the current home page back to the corresponding chat view.
  - `/agent-dashboard <agent>` opens a named persistent-agent home.
- Control action:
  - External action: `{"action":"dashboard.update", ...}`.
  - Internal execution action: `dashboard_update`.
- Persistent storage:
  - Persistent and Secret subagent metadata may contain `dashboard: {...}`.
  - Main Orchestrator dashboard declaration is process-local in the MVP unless a later persistence task adds a main-home store.

### 3. Contracts

- Fresh non-Secret `State` starts on `MAIN_HOME_SESSION_KEY`; runtime navigation is held in `state.selected_session` only.
- Persistent-agent selection from the right sidebar opens the persistent-agent home by default; temporary-agent selection keeps chat-first behavior.
- Dashboard declarations normalize to:
  - `schema_version: "dashboard.v1"`
  - `updated_at`
  - `source`
  - `target`
  - `provenance.task_id`
  - `provenance.artifact_refs`
  - `sections`
  - optional `status_narrative`
  - optional `todos`
  - optional `markdown`
- Supported section types are `function`, `status_narrative`, `todos`, `sessions`, `schedules`, `scheduled_reports`, `tasks`, `artifacts`, `approvals`, `memory`, and `markdown`.
- Shuheng owns the fixed top status card. Agent declarations may control lower-page section order, labels, bounded Markdown, status narrative, and todo text.
- The fixed top status card must render as an authored native TUI control-panel layout, not a flat list of equal-weight label/value lines and not raw Markdown/table syntax. It should keep a full panel frame, status narrative, a visible compact short-metric grid, and lower single-column detail rows for long runtime/governance values so the user can scan current state, workload, ownership, and next context separately.
- The status-card metric grid must default to visible content under a plain `核心指标` divider. The current default should not show `▸/▾` collapsed-state chrome for the whole metric grid.
- Default home pages should show readable function, status, todo, schedule, and recent-task sections below the fixed card. They should not show recent-session sections by default. Approval ids, artifact URIs, and internal owner ids stay behind deliberate `/approvals`, `/artifacts`, and drill-down panels unless an agent explicitly declares a readable dashboard section.
- Explicit `sessions` dashboard sections, when declared, must show readable titles and compact activity metadata only. Main home session rows open normal Shuheng history/current sessions; persistent-subagent session rows open that subagent's own history-backed chat sessions. Home row payloads may carry sanitized history refs or subagent session ids, but the visible text must not dump raw filesystem paths.
- Dashboard schedule sections must render schedule definitions from `scheduled_task_registry(...)` / `latest_schedule_records(...)` only. Schedule run audit records stay in drill-down schedule panels and must not appear as `last:<status>` or task-run ids in the default home-page schedule section.
- Scheduled-report sections render completed child subagent replies for scheduled agent-task runs by joining `scheduledtask.run.v1.task_id` to the task ledger and subagent result artifact rows. They must display the cleaned report body, not just a notification or one-line summary. They must exclude approval-waiting, cancelled, rejected, dispatched-only, and other non-reply audit rows. They are display-only derived views: no extra scheduler, result store, approval action, or memory write is created for the page itself. Default persistent-subagent home pages include a pinned `scheduled_reports` section even when the agent did not declare it, and the main sidebar exposes a global scheduled-report home page.
- Scheduled-report bodies must be user-readable final reply text from the subagent result artifact first, falling back to the task summary only when no artifact body is available. OMP/LLM process markers such as `LLM Running`, `<summary>`, `<thinking>`, tool payloads, approval ids, raw artifact URIs, and task-run ids stay out of the default visible text.
- Dashboard task, approval, and artifact data must be read from the shared task ledger, approval registry, and artifact index. Artifact bodies stay as refs/previews.
- Home-page redraw must not reread and reformat all shared ledgers on every cursor, mouse, or input repaint. It should cache rendered home lines behind a short TTL and file-signature/state key, and shared latest-record helpers should reuse parsed JSONL rows while the backing file signature is unchanged.
- Plain text input on the main home starts the main Orchestrator task and switches to the main task/chat interface (`selected_session == "main"`). Plain text input on a persistent-agent home restores that agent's last entered chat session, auto-switches to that agent's chat interface, and sends the input as direct subagent chat, matching the main-home interaction model. Main home drill-downs stay command-driven through `/tasks`, `/schedules`, `/approvals`, and `/artifacts`.
- Entering a persistent subagent chat through `/chat`, a sidebar subagent-session row, or home plain text input must persist the selected subagent chat session id/ref to subagent metadata so a later restart restores the last entered subagent conversation from canonical history instead of the newest empty session. Subagent metadata must not own the transcript.
- `subagent_store.py` may own pure subagent identity/id, home-key, and sidebar-key shaping, but it must not own dashboard rendering, `State`, `SubAgentRuntime`, history transcript persistence, Secret Vault payload storage, runtime providers, Web Console payloads, or curses rendering.

### 4. Validation & Error Matrix

- Unknown dashboard target -> user-visible `找不到子 agent`.
- Temporary subagent target -> dashboard update is skipped with a temporary-agent message.
- Missing or invalid `dashboard.v1` spec -> render safe default sections.
- Unsupported section type or unsupported fields -> ignore those parts and keep supported sections.
- Home keys passed to selected-history resolution -> not treated as filesystem session paths.
- Secret Vault lock/reset or normal new-session reset -> return to main home, not an arbitrary historical chat.
- Main home plain text input -> starts or queues the main Orchestrator task as before and auto-switches to the main task/chat transcript.

### 5. Good/Base/Bad Cases

- Good: Clicking a persistent agent opens `__home__:sub:<agent_id>` and shows the fixed status card, readable default schedule/task sections, and concise detail-entry actions without dumping artifact URIs or approval ids by default.
- Good: A scheduled subagent task completes, writes a subagent-result artifact, and then appears as a readable final-reply body in both that subagent's home `定时汇报` section and the global `__home__:scheduled_reports` page without exposing raw artifact URIs or process/thinking blocks in the default text.
- Good: A due scheduled task is approval-required or later cancelled; it remains visible in `/schedules` and task/approval drill-downs but does not appear as a scheduled report.
- Good: Repainting the same home page during typing, mouse movement, or scroll reuses the cached rendered home lines until a relevant ledger file signature, dashboard declaration, selected home, width, or expanded-state key changes.
- Good: The fixed status card uses native TUI panel separators such as `├─ 核心指标`; aligned metric tiles are visible by default, and long values stay below in a single `运行详情` section instead of being squeezed into one horizontal line.
- Good: A persistent agent may explicitly declare readable lower sections such as `markdown` or `todos`; those sections render below the card while unsupported fields are dropped.
- Good: Default home pages omit recent-session sections, keeping chat history in the sidebar/session views instead of the dashboard body.
- Good: `/chat` from a persistent-agent home restores the previously entered history-backed subagent chat session and marks its ref as the metadata current session for the next restart.
- Base: An explicitly declared `sessions` dashboard section can still render readable session rows and route them through the same normal-history or subagent-session switching paths as the sidebars.
- Good: A persistent agent emits `dashboard.update` with `sections:[{"type":"markdown"},{"type":"todos"}]`; unsupported fields are dropped and the accepted declaration is persisted in subagent metadata with provenance.
- Base: `/chat` from a home page switches to the corresponding chat session without changing the stored dashboard declaration.
- Bad: Treating a home key as a path for `selected` history operations.
- Bad: Running `latest_task_records()`, `pending_approvals()`, `scheduled_task_registry()`, and `artifact_index_latest()` on every repaint when the home-page inputs are unchanged.
- Bad: Rendering agent-provided script/code as executable UI behavior.
- Bad: Letting a temporary agent persist a dashboard declaration.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert fresh `State` opens `MAIN_HOME_SESSION_KEY` and main home lines render.
- Tests must assert the main and persistent-agent fixed status cards keep native TUI metric-grid rows visible by default, plus lower detail rows instead of flat label/value rows or raw Markdown table text.
- Tests must assert default home pages show readable function/status/todo/schedule/recent-task sections while keeping recent-session sections, schedule run records, artifact URIs, and approval ids out of the default view.
- Tests must assert scheduled subagent result rows and cleaned report body content are visible in the subagent `scheduled_reports` home section and in the global scheduled-report page, while the normal schedule section still shows schedule definitions only.
- Tests must assert scheduled-report rendering strips process/thinking metadata and excludes approval-required or cancelled schedule audit rows.
- Tests must assert entering a persistent subagent chat through `/chat` or a subagent-session switch persists the selected chat session id/ref and a later restart restores that session from canonical history, not from a per-agent transcript store.
- Tests must assert repeated `home_lines(...)` calls for an unchanged home page reuse the cached render instead of rereading the task ledger.
- Tests must assert default main and persistent-agent home rendering shows readable task and schedule rows while keeping raw artifact and approval rows behind detail-entry actions.
- Tests must assert explicitly declared readable dashboard sections still render from persisted dashboard declarations.
- Tests must assert temporary agents do not persist dashboard declarations.
- Tests must assert `dashboard.update` is extracted from `shuheng-control.v2`, normalized to `dashboard_update`, and persisted for persistent subagents.
- Tests must assert unsupported section types and executable-looking fields are ignored.
- Tests must assert old transcript-only behavior explicitly selects `"main"` when testing main chat rendering.
- Tests must assert plain text on main home auto-switches to `selected_session == "main"` after starting a main task, while plain text on persistent-agent homes auto-switches to the corresponding subagent chat and sends the input without requiring `/chat`.
- Tests must keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```json
{
  "action": "dashboard.update",
  "target": "temporary-agent",
  "sections": [{"type": "script", "body": "run this UI code"}]
}
```

#### Correct

```json
{
  "action": "dashboard.update",
  "target": "agent-researcher",
  "dashboard": {
    "sections": [
      {"type": "status_narrative", "title": "当前状态"},
      {"type": "todos", "title": "待办"},
      {"type": "schedules", "title": "最近定时任务"},
      {"type": "artifacts", "title": "产物引用"}
    ],
    "status_narrative": "正在整理最近定时任务结果。",
    "todos": ["复核共享任务账本", "更新 artifact refs"]
  },
  "artifact_refs": ["artifact://artifacts/reports/example.md"]
}
```

## Scenario: Dashboard Helper Module Boundary

### 1. Scope / Trigger

- Trigger: Dashboard section constants, bounded dashboard text cleanup, dashboard section normalization, dashboard spec payload shaping, dashboard cache-signature helpers, or pure status-card string layout helpers are moved out of `src/shuheng/app.py`.
- Applies to: `src/shuheng/dashboard.py`, compatibility aliases in `src/shuheng/app.py`, `dashboard.update` normalization, main/persistent-agent home rendering inputs, policy gates, and dashboard helper unit tests.
- Non-goal: This does not move `State` or `SubAgentRuntime` projections, curses `RenderLine` home rendering, status-card drawing, session/history restore, ledger reads, scheduler reads, approval/action dispatch, or Web Console payloads.

### 2. Signatures

- Lower-level helper module: `src/shuheng/dashboard.py`.
- Compatibility aliases in `app.py`:
  - `SUPPORTED_DASHBOARD_SECTIONS`.
  - `DEFAULT_DASHBOARD_SECTIONS`.
  - `DEFAULT_SUBAGENT_DASHBOARD_SECTIONS`.
  - `bounded_dashboard_text(value, limit=2000)`.
  - `normalize_dashboard_sections(raw_sections)`.
  - `normalize_dashboard_spec_payload(control, source, target)`.
  - `dashboard_cache_signature(raw)`.
  - `status_card_header_line(title, card_width)`.
  - `status_card_divider_line(title, card_width)`.
  - `status_card_content_line(text, card_width)`.
  - `status_card_footer_line(card_width)`.
  - `status_card_metric_rows(items, inner_width)`.
  - `status_card_metric_header(metrics)`.
  - `status_card_detail_rows(items, inner_width)`.

### 3. Contracts

- `dashboard.py` must not import `shuheng.app`, `.app`, `app`, `curses`, `State`, `SubAgentRuntime`, `RenderLine`, `PanelItem`, gateway handlers, runtime dispatch, or draw/home rendering functions.
- `app.py` remains the compatibility facade and exposes the moved names as direct aliases or behavior-identical wrappers.
- Supported section types remain `function`, `status_narrative`, `todos`, `sessions`, `schedules`, `scheduled_reports`, `tasks`, `artifacts`, `approvals`, `memory`, and `markdown`.
- `normalize_dashboard_sections(...)` accepts string or dict section entries, drops unsupported/non-dict entries, bounds titles to 80 characters, bounds markdown/body to 3000 characters, and keeps at most 12 sections.
- `normalize_dashboard_spec_payload(...)` returns `dashboard.v1` with `updated_at`, `source`, `target`, `provenance.task_id`, `provenance.artifact_refs`, `sections`, and optional `status_narrative`, `todos`, and `markdown`.
- `normalize_dashboard_spec_payload(...)` keeps at most 20 todo items, bounds todo text to 180 characters, and keeps at most 12 non-empty artifact refs in provenance.
- `dashboard_cache_signature(...)` returns stable sorted compact JSON for serializable values, `""` for falsey values, and a safe string fallback for non-serializable values.
- Status-card helpers in `dashboard.py` return only strings or lists of strings. They may use lower-level text/cell helpers, but must not allocate `RenderLine`, call `cp(...)`, import curses, read `State`, inspect subagents, or query ledgers.
- `append_status_card(...)`, `append_home_action_panel(...)`, `append_home_section(...)`, and home-line functions remain in `app.py` until rendering types and curses attrs are separated.

### 4. Validation & Error Matrix

- `dashboard.py` imports `shuheng.app`, curses, TUI state, render types, or home-line functions -> policy gate fails.
- App alias differs from module helper for the same input -> unit test or policy gate fails.
- Unknown dashboard section type -> dropped from normalized sections.
- Section title, markdown, status, todos, or payload markdown exceed bounds -> normalized output is truncated.
- Non-dict nested payload -> helper treats the top-level control as the dashboard payload.
- Non-serializable dashboard cache input -> returns `str(raw)` instead of raising.
- Status-card title, metric, or detail values exceed available width -> helpers truncate, wrap, or pad with terminal-cell-aware helpers instead of emitting ragged rows.
- Empty metric or detail inputs -> helpers return readable `暂无指标` or `暂无详情` fallback rows.

### 5. Good/Base/Bad Cases

- Good: `apply_dashboard_control(...)` keeps calling `app.normalize_dashboard_spec_payload(...)`, while the implementation lives in `shuheng.dashboard`.
- Good: Home rendering keeps using `dashboard_sections_for_main(...)` and `dashboard_sections_for_subagent(...)` from `app.py`, with default sections imported from `shuheng.dashboard`.
- Base: `dashboard_status_for_subagent(...)` stays in `app.py` because it reads `SubAgentRuntime` fields.
- Base: `main_home_lines_uncached(...)` and `subagent_home_lines_uncached(...)` stay in `app.py` because they construct `RenderLine` values and read ledgers/live state.
- Base: `append_status_card(...)` stays in `app.py` because it constructs `RenderLine` values and attaches curses attributes; it may call pure status-card line helpers from `dashboard.py`.
- Bad: `dashboard.py` imports `State` so it can decide default status text.
- Bad: `dashboard.py` calls `latest_task_records(...)`, `pending_approvals(...)`, or curses draw helpers.

### 6. Tests Required

- Unit tests must assert section normalization, payload normalization, cache signature behavior, status-card line/layout helpers, and `app.py` wrapper parity.
- `scripts/check_policy_gates.py` must assert `dashboard.py` has no reverse import into `app.py` and no curses, TUI state, rendering, gateway, runtime-dispatch, or home-rendering dependencies.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/dashboard.py scripts/check_policy_gates.py tests/test_dashboard.py` must pass.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py` and `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_dashboard.py -p no:cacheprovider` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# dashboard.py
from shuheng.app import State, RenderLine, latest_task_records
```

#### Correct

```python
# dashboard.py
def normalize_dashboard_sections(raw_sections):
    ...
```

## Scenario: Text Utility Module Boundary

### 1. Scope / Trigger

- Trigger: Pure terminal-cell or compact text helpers are moved out of `src/shuheng/app.py`.
- Applies to: `src/shuheng/text_utils.py`, compatibility aliases in `src/shuheng/app.py`, title/category cleaning, sidebar/history title consumers, dashboard helpers, Web Console helpers, policy gates, and text utility unit tests.
- Non-goal: This does not move history metadata, transcript parsing, Web Console history payloads, dashboard/home rendering, command handlers, runtime providers, ledgers, Secret Vault, or storage roots.

### 2. Signatures

- Lower-level helper module: `src/shuheng/text_utils.py`.
- Compatibility aliases in `app.py`:
  - `ANSI_RE`.
  - `cell_width(text)`.
  - `truncate_cells(text, width)`.
  - `pad_cells(text, width)`.
  - `clean_text(text)`.
  - `wrap_cells(text, width)`.
  - `compact_title(text, max_width=24)`.
  - `compact_category(text)`.
  - `rel_age(mtime)`.
  - `human_tokens(n)`.

### 3. Contracts

- `text_utils.py` must remain a pure leaf module and must not import `shuheng.app`, `.app`, `app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, providers, history stores, ledgers, Web Console, dashboard, or command handlers.
- `compact_title(...)` strips ANSI/control display noise through `clean_text`, removes fenced code, HTML-like tags, lightweight markdown markers, leading user/request boilerplate, and leading completion/summary boilerplate before terminal-cell truncation.
- `compact_category(...)` uses `compact_title(..., 18)` and returns an empty category for sentinel values `-`, `clear`, `none`, `null`, and `未分类`.
- `rel_age(...)` formats elapsed time for sidebar, Web Console, artifact, subagent, and memory display without depending on TUI state.
- `human_tokens(...)` formats token counts for Web Console and status rows without depending on token registries.
- `app.py` remains the compatibility facade and exposes moved helpers as direct aliases or behavior-identical wrappers.

### 4. Validation & Error Matrix

- `text_utils.py` imports `shuheng.app`, curses, TUI state, render types, runtime providers, stores, or command handlers -> policy gate fails.
- App alias differs from module helper for the same input -> unit test or policy gate fails.
- Title input includes code fences, HTML tags, or markdown markers -> helper removes layout/control noise before truncation.
- Category input is a sentinel value -> helper returns `""` so callers can apply their own fallback label.

### 5. Good/Base/Bad Cases

- Good: `session_title_for_path(...)` continues calling `app.compact_title(...)`, while the implementation lives in `shuheng.text_utils`.
- Good: `dashboard.py` and `web_console.py` import lower-level text helpers without depending on `app.py`.
- Base: `app.compact_description(...)` remains the compatibility wrapper; the process-summary-safe implementation lives in `history_titles.py` alongside the process marker regexes it needs.
- Bad: `text_utils.py` imports `TUI_CONTROL_RE` from `app.py`.
- Bad: Moving sidebar row rendering into `text_utils.py` because it would couple text helpers to `State` and curses rendering.

### 6. Tests Required

- Unit tests must assert app wrapper parity, terminal-cell behavior, compact title cleanup, compact category sentinel handling, and no behavior drift for existing text helpers.
- `scripts/check_policy_gates.py` must assert `text_utils.py` has no reverse import into `app.py` and no curses/TUI/runtime/store dependencies.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/text_utils.py scripts/check_policy_gates.py tests/test_cell_utils.py` must pass.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py` and `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_cell_utils.py -p no:cacheprovider` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# text_utils.py
from shuheng.app import TUI_CONTROL_RE, State
```

#### Correct

```python
# text_utils.py
def compact_title(text: str, max_width: int = 24) -> str:
    ...
```

## Scenario: Input Controller Helper Module Boundary

### 1. Scope / Trigger

- Trigger: Pure terminal input cursor/display conversion, prompt-layout, pasted-text cleanup, input-history browse target calculation, text edit transition calculation, mouse-mask classification, and vertical cursor target helpers are moved out of `src/shuheng/app.py`.
- Applies to: `src/shuheng/input_controller.py`, compatibility aliases in `src/shuheng/app.py`, text input display conversion, wrapped input segment geometry, prompt/input line layout, vertical cursor movement callers, input-history browsing callers, input text edit callers, policy gates, and input-controller unit tests.
- Non-goal: This does not move the app-owned `move_input_cursor_vertical(...)` state mutation wrapper, `draw_main(...)`, key handlers, mouse handlers, command completion, rendering, mutable `State`, storage roots, Web Console payloads, dashboard helpers, or runtime dispatch.

### 2. Signatures

- Lower-level helper module: `src/shuheng/input_controller.py`.
- Compatibility aliases in `app.py`:
  - `raw_cursor_to_display(text, cursor)`.
  - `display_cursor_to_raw(text, display_cursor)`.
  - `input_segments(text, width)`.
  - `display_index_for_cell(display, start, end, target_x)`.
  - `input_cursor_info(text, width, cursor)`.
  - `input_layout(text, width, max_lines, cursor, prompt="> ")`.
  - `input_vertical_cursor_target(text, width, cursor, direction)`.
  - `normalize_pasted_text(text)`.
  - `InputHistoryBrowseResult`.
  - `input_history_browse_result(history, text, cursor, history_index, draft, draft_cursor, direction)`.
  - `InputTextEditResult`.
  - `input_insert_result(text, cursor, insertion)`.
  - `input_delete_before_cursor_result(text, cursor)`.
  - `input_delete_at_cursor_result(text, cursor)`.
  - `input_horizontal_cursor_target(text, cursor, delta)`.
  - `mouse_button_mask_from_constants(button_no, constants)`.
  - `mouse_modifier_mask_from_constants(constants)`.
  - `mouse_known_bstate_mask_from_constants(constants, button_count=5)`.
  - `mouse_auxiliary_or_unknown_event_from_constants(bstate, constants, button_count=5)`.
  - `clean_button1_action_from_constants(bstate, allowed_button1_mask, constants, button_count=5)`.
- App-owned curses wrappers:
  - `mouse_button_mask(button_no)`.
  - `mouse_modifier_mask()`.
  - `mouse_known_bstate_mask()`.
  - `mouse_auxiliary_or_unknown_event(bstate)`.
  - `clean_button1_action(bstate, allowed_button1_mask)`.

### 3. Contracts

- `input_controller.py` must not import `shuheng.app`, `.app`, `app`, curses, mutable TUI `State`, `SubAgentRuntime`, `RenderLine`, `PanelItem`, gateway handlers, Web Console, dashboard, runtime dispatch, command handlers, key/mouse handlers, or draw functions.
- `input_controller.py` may import lower-level terminal-cell helpers from `text_utils.py`.
- Raw newlines display as the two-character sequence `\n`.
- Raw cursor positions clamp into the valid source text range.
- Display cursor positions clamp to non-negative values and map escaped newline positions back to the matching raw newline boundary.
- Segment wrapping uses the same terminal-cell semantics as `text_utils.cell_width(...)`, including East Asian wide characters and zero-width combining marks.
- `input_cursor_info(...)` returns `(display, segments, display_cursor, cursor_line, cursor_x)` and preserves the existing segment/cursor-line selection behavior.
- `input_layout(...)` returns `(lines, cursor_y, cursor_x)`, clamps `max_lines` to at least one visible line, uses escaped-newline display text from `input_cursor_info(...)`, keeps the cursor segment visible when scrolled, prefixes the first hidden visible line with `"… "`, and computes cursor x with `cell_width(...)`.
- `input_vertical_cursor_target(...)` returns `(consumed, target_cursor)`. Empty or single-line display input returns `(False, None)`. Moving beyond the first or last wrapped display line returns `(True, None)` so callers can consume the key without mutation. Moving to an available wrapped line returns `(True, <raw cursor>)`, preserving the source display cell x as closely as possible over the same terminal-cell semantics as `input_cursor_info(...)`.
- `normalize_pasted_text(...)` collapses one or more CR/LF runs plus surrounding spaces/tabs into one literal space, replaces remaining tabs with four spaces, and must not inspect terminal, curses, or mutable paste state.
- `input_history_browse_result(...)` returns an immutable browse result over explicit values. Empty history and Down before browsing return `consumed=False`. First Up saves the current draft and cursor and selects the latest entry. Additional Up clamps at the oldest entry. Down moves toward newer entries, and moving beyond the newest entry restores the saved draft while clearing browse state.
- `input_insert_result(...)`, `input_delete_before_cursor_result(...)`, `input_delete_at_cursor_result(...)`, and `input_horizontal_cursor_target(...)` return deterministic text/cursor transitions over explicit values. Non-empty insertion clamps the source cursor, inserts text, and moves the cursor after the inserted value. Empty insertion returns the original text/cursor with `edited=False`. Backspace-style deletion clamps the cursor, deletes only when the cursor is greater than zero, and reports whether text changed. Delete-style deletion clamps the cursor, deletes only when the cursor is before the end of the text, and reports whether text changed. Horizontal movement clamps the target cursor into `[0, len(text)]`.
- Mouse bitmask helpers in `input_controller.py` are deterministic over explicit integer constants. They must not read curses globals directly.
- `mouse_button_mask_from_constants(...)` ORs the supported button state constants (`PRESSED`, `RELEASED`, `CLICKED`, `DOUBLE_CLICKED`, `TRIPLE_CLICKED`) for the requested button.
- `mouse_modifier_mask_from_constants(...)`, `mouse_known_bstate_mask_from_constants(...)`, `mouse_auxiliary_or_unknown_event_from_constants(...)`, and `clean_button1_action_from_constants(...)` preserve the existing primary-button/modifier/auxiliary/unknown-bit filtering semantics over explicit constants.
- `app.py` remains the owner of curses constant lookup for mouse helpers and injects those values into `input_controller.py`.
- `app.py` remains the compatibility facade and the owner of mutable input state, dirty marking, vertical cursor mutation, keyboard/mouse dispatch, command routing, rendering, and runtime side effects.

### 4. Validation & Error Matrix

- `input_controller.py` imports app/TUI/render/runtime/command owners -> policy gate fails.
- App alias differs from module helper for the same input -> unit test or policy gate fails.
- `raw_cursor_to_display("a\nb", 2)` -> `3`.
- `display_cursor_to_raw("a\nb", 2)` and `display_cursor_to_raw("a\nb", 3)` -> `2`.
- East Asian wide text wraps at cell boundaries, not Python string length boundaries.
- Combining marks add no cell width when wrapping or computing cursor x.
- Empty input still produces one empty segment.
- `input_layout("abcdef", 4, 2, 5)` -> `(["… cd", "  ef"], 1, 3)`.
- `input_vertical_cursor_target("abcdef", 4, 5, -1)` -> `(True, 3)`.
- `input_vertical_cursor_target("abcdef", 4, 5, 1)` -> `(True, None)`.
- `normalize_pasted_text(" alpha \n\t beta\r\n gamma\t")` -> `" alpha beta gamma    "`.
- `input_history_browse_result(["old", "new"], "draft", 3, None, "", 0, -1)` -> `InputHistoryBrowseResult(True, "new", 3, 1, "draft", 3)`.
- `input_insert_result("abc", 1, "X")` -> `InputTextEditResult("aXbc", 2, True)`.
- `input_insert_result("abc", 9, "")` -> `InputTextEditResult("abc", 9, False)`.
- `input_delete_before_cursor_result("abc", 2)` -> `InputTextEditResult("ac", 1, True)`.
- `input_delete_at_cursor_result("abc", 1)` -> `InputTextEditResult("ac", 1, True)`.
- `input_horizontal_cursor_target("abc", 1, 9)` -> `3`.
- `mouse_auxiliary_or_unknown_event_from_constants(primary_button_1 | modifier, constants)` -> `False`.
- `mouse_auxiliary_or_unknown_event_from_constants(button_2, constants)` -> `True`.
- `clean_button1_action_from_constants(button_1_clicked | modifier, button_1_clicked, constants)` -> `True`.
- `clean_button1_action_from_constants(button_1_clicked | button_2_clicked, button_1_clicked, constants)` -> `False`.

### 5. Good/Base/Bad Cases

- Good: `move_input_cursor_vertical(...)` stays in `app.py` as the mutable wrapper and delegates target calculation to `input_controller.py`.
- Good: `input_layout(...)` lives in `input_controller.py` because it is pure text geometry and prompt layout, while `draw_main(...)` remains in `app.py` and calls the compatibility alias.
- Good: `normalize_pasted_text(...)` lives in `input_controller.py`, while bracketed paste mode, paste buffer mutation, and `handle_key(...)` stay in `app.py`.
- Good: `input_history_browse_result(...)` lives in `input_controller.py`, while `browse_input_history(...)` stays in `app.py` and owns `State` mutation, command-index reset, and dirty marking.
- Good: text edit transition helpers live in `input_controller.py`, while `app.py` keeps `insert_input_text(...)`, key handlers, command-index reset, input-history browse reset, and dirty marking.
- Good: mouse bitmask classification helpers live in `input_controller.py` over explicit constants, while `app.py` keeps curses constant lookup and `handle_mouse(...)`.
- Base: Future slices may move more input handling only after command and rendering boundaries are stable.
- Bad: `input_controller.py` imports `State` so it can mutate `state.input_cursor`.
- Bad: `input_controller.py` imports curses so it can read `BUTTON1_CLICKED` directly.
- Bad: `input_controller.py` calls command completion, Web Console, dashboard, or curses draw helpers.

### 6. Tests Required

- Unit tests must assert newline display mapping, raw/display cursor round trips, segment wrapping, East Asian width handling, combining-mark handling, display-index lookup, cursor info, input layout line/cursor behavior, vertical cursor target behavior, input-history browse target behavior, and `app.py` alias/wrapper parity.
- Unit tests must assert paste normalization preserves collapsed newline and tab-replacement behavior plus app alias parity.
- Unit tests must assert text insertion, backspace-style deletion, delete-style deletion, horizontal cursor movement, edit/no-edit flags, clamping behavior, app alias parity, and `insert_input_text(...)` wrapper state mutation/reset behavior.
- Unit tests must assert direct mouse mask helper behavior over fake constants and `app.py` wrapper parity over curses constants.
- `scripts/check_policy_gates.py` must assert `input_controller.py` has no reverse dependency into `app.py` and no curses, mutable TUI state, rendering, command-handler, Web Console, dashboard, or runtime-dispatch dependencies.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/input_controller.py scripts/check_policy_gates.py tests/test_input_controller.py` must pass.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py` and `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_input_controller.py -p no:cacheprovider` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# input_controller.py
from shuheng.app import State, mark_dirty
```

#### Correct

```python
# input_controller.py
def raw_cursor_to_display(text: str, cursor: int) -> int:
    ...
```

## Scenario: Command Completion Helper Module Boundary

### 1. Scope / Trigger

- Trigger: Goal 7 decomposes deterministic command-completion constants and
  helper functions out of `src/shuheng/app.py`.
- Applies to: `src/shuheng/commands.py`, compatibility aliases in `app.py`,
  `/agent` subcommand option metadata, `/archived` completion, `/workspace` and
  `/workspaces` completion, `/filter` / `/collapse` / `/expand` category
  command row shaping over explicit category counts, `/approve` / `/reject`
  command row shaping over explicit approval candidates, `/agent settings|model`
  target extraction, top-level visible command prefix matching, completion
  insertion behavior, unit tests, and policy gates.
- Non-goal: This does not move command execution, `command_matches(...)`,
  `subagent_completion_rows(...)`, `agent_command_matches(...)`,
  `category_command_matches(...)`, `approval_command_matches(...)`, mutable
  `State`, role-template lookup, pending approvals, history categories, input
  event handling, Web Console, dashboard, rendering, runtime dispatch, storage
  roots, Secret Vault behavior, ledgers, or artifacts.

### 2. Signatures

- Lower-level helper module: `src/shuheng/commands.py`.
- Compatibility aliases in `app.py`:
  - `AGENT_SUBCOMMANDS`.
  - `AGENT_SUBCOMMANDS_REQUIRING_AGENT`.
  - `AGENT_SUBCOMMANDS_SEND_AFTER_AGENT`.
  - `WORKSPACE_SUBCOMMANDS`.
  - `AgentCommandCompletionDecision`.
  - `completion_insert_text(candidate)`.
  - `top_level_command_matches(text, candidates)`.
  - `category_command_completion_rows(text, category_counts)`.
  - `approval_command_completion_rows(text, approval_candidates)`.
  - `agent_command_completion_decision(text)`.
  - `subagent_settings_target_from_command(text)`.
  - `archived_command_matches(text)`.
  - `workspace_command_matches(text)`.

### 3. Contracts

- `commands.py` must not import `shuheng.app`, `.app`, `app`, curses, mutable
  TUI `State`, `SubAgentRuntime`, `RenderLine`, `PanelItem`, gateway handlers,
  Web Console, dashboard, runtime dispatch, input controller, Secret Vault,
  governance stores, history stores, key/mouse handlers, or draw functions.
- `commands.py` owns deterministic command-completion metadata and matching
  over explicit text values.
- `top_level_command_matches(...)` owns only the static fallback prefix match
  over an explicitly supplied visible command catalog. It must not own
  `COMMANDS`, invent hidden aliases, inspect `State`, or route specialized
  dynamic command families. Non-slash input and stripped input containing a
  space return no matches; matching is case-insensitive.
- `category_command_completion_rows(...)` owns only deterministic row shaping
  for `/filter`, `/collapse`, and `/expand` over an explicitly supplied ordered
  iterable of `(label, count)` pairs. It may add the static `/filter off`,
  `/collapse all`, and `/expand all` rows and may prefix-filter labels
  case-insensitively. It must not inspect `State`, session history, session
  metadata, category registries, or category sort policy. `app.py` remains
  responsible for collecting category counts from history and applying
  `category_sort_key(...)` before delegating to the helper.
- `approval_command_completion_rows(...)` owns only deterministic row shaping
  for `/approve` and `/reject` over an explicitly supplied iterable of
  `(approval_id, summary)` pairs. Prefix filtering remains
  `approval_id.startswith(prefix)` and therefore case-sensitive. It must not
  inspect `State`, pending approval ledgers, policy decisions, governance
  stores, or summary truncation policy. `app.py` remains responsible for
  calling `pending_approvals(state)` and applying `truncate_cells(..., 70)`
  before delegating to the helper.
- `agent_command_completion_decision(...)` owns pure `/agent` input
  classification. It may return static rows, a subagent-completion request, a
  role-template-completion request, or no match, but it must not inspect
  current subagent state or role templates.
- `subagent_settings_target_from_command(...)` owns only deterministic target
  extraction for `/agent settings|setting|config|detail|details|prefs <agent>`
  and `/agent model <agent>`. It returns the single non-space target token or
  `""` for non-matching input, missing targets, or extra trailing tokens. It
  must not inspect `State`, resolve subagents, open modals, set models, mutate
  runtime state, or execute commands.
- `completion_insert_text(...)` returns the command unchanged for sendable
  candidates and appends exactly one trailing space to non-sendable command
  candidates after right-stripping the command.
- `archived_command_matches(...)` completes only `/archived <prefix>` and
  returns the existing `on`, `off`, and `toggle` rows.
- `workspace_command_matches(...)` preserves the existing singular/plural root
  behavior: `/workspaces` and `/workspaces ` are sendable list commands,
  `/workspace ` opens subcommand completion, and only `list`, `current`, and
  `refresh` subcommands are offered.
- `app.py` remains the compatibility facade and the owner of stateful command
  completion dispatch, subagent rows, role-template rows, category rows,
  approval rows, command execution, input event handling, and runtime side
  effects.

### 4. Validation & Error Matrix

- `commands.py` imports app/TUI/render/runtime/storage owners -> policy gate
  fails.
- App alias differs from module helper for the same input -> unit test or
  policy gate fails.
- `completion_insert_text(("/archived on", "", "显示归档", True))` ->
  `"/archived on"`.
- `completion_insert_text(("/workspace", "<cmd>", "...", False))` ->
  `"/workspace "`.
- `top_level_command_matches("/mo", [("/model", "", "...", True)])` ->
  `[("/model", "", "...", True)]`.
- `top_level_command_matches("/ll", [("/model", "", "...", True)])` -> `[]`.
- `top_level_command_matches("/model extra", candidates)` -> `[]`.
- `category_command_completion_rows("/filter ", [("Work", 2)])` ->
  `[("/filter off", "", "关闭分类筛选", True), ("/filter Work", "", "2 个会话",
  True)]`.
- `category_command_completion_rows("/collapse w", [("Work", 2)])` ->
  `[("/collapse Work", "", "2 个会话", True)]`.
- `category_command_completion_rows("/expand ", [("Work", 2)])` ->
  `[("/expand all", "", "全部分类", True), ("/expand Work", "", "2 个会话",
  True)]`.
- `approval_command_completion_rows("/approve ", [("apr-001", "Allow")])` ->
  `[("/approve apr-001", "", "Allow", True)]`.
- `approval_command_completion_rows("/reject APR", [("apr-001", "a"),
  ("APR-002", "b")])` -> `[("/reject APR-002", "", "b", True)]`.
- `archived_command_matches("/archived t")` -> `[("/archived toggle", "",
  "切换归档视图", True)]`.
- `workspace_command_matches("/workspace r")` -> `[("/workspace refresh", "",
  "刷新自动工作区索引", True)]`.
- `workspace_command_matches("/workspaces ")` -> `[("/workspaces", "",
  "列出项目工作区 provenance", True)]`.
- `workspace_command_matches("/workspace refresh ")` -> `[]`.
- `agent_command_completion_decision("/agent")` -> rows containing the
  sendable `/agent` command root.
- `agent_command_completion_decision("/agent ask worker")` -> a pure subagent
  completion request for subcommand `ask` and agent prefix `worker`.
- `agent_command_completion_decision("/agent role worker re")` -> a pure role
  completion request with base `/agent role worker ` and role prefix `re`.
- `agent_command_completion_decision("/agent role worker re extra")` -> no
  match.
- `subagent_settings_target_from_command("/agent settings worker")` ->
  `"worker"`.
- `subagent_settings_target_from_command("/AGENT MODEL Worker-2")` ->
  `"Worker-2"`.
- `subagent_settings_target_from_command("/agent detail worker extra")` -> `""`.
- `command_matches("/workspace r", state)` still delegates to the extracted
  workspace helper before app-owned command dispatch continues.
- `command_matches("/mo", state)` still delegates the final static fallback to
  the extracted top-level helper using app-owned `COMMANDS`, while `/ll` and
  `/models` remain hidden alias non-completions.

### 5. Good/Base/Bad Cases

- Good: `commands.py` owns pure `/archived` and `/workspace` completion
  matching, while `app.py` keeps command routing and stateful completions.
- Good: `/agent` option constants move to `commands.py`, while `app.py` still
  owns subagent runtime row expansion and role-template completion.
- Good: `/agent` completion parsing returns a neutral decision object from
  `commands.py`; `app.py` then expands that decision using `State.subagents`
  and `ROLE_TEMPLATES`.
- Good: `/agent settings|model` target extraction moves to `commands.py`, while
  `app.py` still owns subagent resolution, modal opening, model setting,
  input/key handling, and error display.
- Good: `commands.py` owns `top_level_command_matches(...)` over injected
  candidates, while `app.py` keeps the visible `COMMANDS` catalog and the
  specialized dynamic routing order.
- Good: `commands.py` owns category command row shaping over injected
  `(label, count)` pairs, while `app.py` keeps history/category metadata
  ownership and sorting.
- Good: `commands.py` owns approval command row shaping over injected
  `(approval_id, summary)` pairs, while `app.py` keeps approval ledger access,
  pending approval policy, and summary truncation ownership.
- Base: Future slices may move more command parsing only after state,
  governance, history, rendering, and runtime dependencies are injectable.
- Bad: `commands.py` imports `State` so it can inspect active subagents.
- Bad: `commands.py` imports approvals or history metadata to complete dynamic
  command rows.

### 6. Tests Required

- Unit tests must assert direct `agent_command_completion_decision(...)`,
  `completion_insert_text(...)`, `archived_command_matches(...)`, and
  `workspace_command_matches(...)` behavior plus top-level command prefix
  matching and app alias parity.
- Unit tests must assert app-level `command_matches(...)` still returns the same
  `/archived` and `/workspace` helper rows, and that the final static fallback
  routes `/mo` through the extracted helper without exposing `/llm` or
  `/models` hidden aliases.
- Unit tests must assert direct `category_command_completion_rows(...)`
  behavior for static rows, prefix filtering, count descriptions, and
  non-matching input. App-level tests must assert `category_command_matches(...)`
  still derives counts from `State.history` / session metadata and delegates row
  shaping without moving history ownership into `commands.py`.
- Unit tests must assert direct `approval_command_completion_rows(...)`
  behavior for approve/reject row shaping, case-sensitive id prefix filtering,
  and non-matching input. App-level tests must assert
  `approval_command_matches(...)` still derives candidates from
  `pending_approvals(state)`, applies app-owned summary truncation, and delegates
  row shaping without moving approval ownership into `commands.py`.
- Unit tests must assert direct `subagent_settings_target_from_command(...)`
  behavior for settings aliases, model command targets, case-insensitive command
  words, surrounding whitespace, extra trailing tokens, and non-matching input,
  plus app alias parity.
- `scripts/check_policy_gates.py` must assert `commands.py` owns the moved
  helpers, `app.py` no longer defines the moved functions locally, and the new
  module has no reverse dependency into app/TUI/render/runtime/storage owners.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/commands.py
  scripts/check_policy_gates.py tests/test_commands.py` must pass.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py` and
  `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_commands.py -p
  no:cacheprovider` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# commands.py
from shuheng.app import State, pending_approvals
```

#### Correct

```python
# commands.py
def archived_command_matches(text: str) -> list[tuple[str, str, str, bool]]:
    ...
```

## Scenario: Path Utility Module Boundary

### 1. Scope / Trigger

- Trigger: `app.py` decomposition needs a shared lower-level home for filesystem path normalization and containment checks used by history, Secret Vault import validation, workspace checks, Web Console session refs, and policy gates.
- Applies to: `src/shuheng/path_utils.py`, compatibility aliases in `src/shuheng/app.py`, normal session-log path checks, Shuheng-owned storage-root assertions, and path-safety unit tests.
- Non-goal: This does not move Shuheng storage-root constants, frontend history storage configuration, legacy bootstrap, history metadata, Secret Vault storage behavior, Web Console payloads, commands, rendering, or input handling.

### 2. Signatures

- Leaf helpers: `path_utils.normalized_path(path)` and `path_utils.path_is_within(path, root)`.
- Normal-history predicate: `path_utils.is_normal_session_log_path(path, *, model_responses_dir, session_trash_dir)`.
- App compatibility: `app.normalized_path` and `app.path_is_within` are aliases; `app.is_normal_session_log_path(path)` injects `MODEL_RESPONSES_DIR` and `SESSION_TRASH_DIR`.

### 3. Contracts

- `normalized_path(...)` expands `~` and returns an absolute path.
- `path_is_within(...)` resolves real paths and returns `False` instead of raising on invalid input.
- Normal session logs must be under `MODEL_RESPONSES_DIR`, outside `SESSION_TRASH_DIR`, and named `model_responses*.txt`.
- `path_utils.py` must remain a pure leaf module and must not import `shuheng.app`, curses, `State`, `SubAgentRuntime`, `RenderLine`, history store, Secret Vault, Web Console, dashboard, runtime dispatch, command handlers, or renderer functions.
- Storage-root ownership remains app-configured and test-retargetable; extracted helpers accept roots as parameters rather than reading app globals.

### 4. Validation & Error Matrix

- Path inside history root with `model_responses*.txt` basename -> normal session-log predicate returns true.
- Path under `.trash` -> normal session-log predicate returns false even when basename matches.
- Path outside history root or with a non-session basename -> normal session-log predicate returns false.
- App tests retarget `MODEL_RESPONSES_DIR` / `SESSION_TRASH_DIR` -> app wrapper uses current app globals.

### 5. Good/Base/Bad Cases

- Good: Future lower-level history or Secret Vault extraction imports `path_utils.py` for path containment without importing `app.py`.
- Base: `app.py` still owns actual Shuheng root constants and passes them into the path utility predicate.
- Bad: A lower-level module imports `shuheng.app` solely to call `path_is_within(...)`.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `path_utils.py` owns path normalization/containment helpers and has no reverse import into app/TUI/rendering/runtime modules.
- Unit tests must cover direct module behavior and app compatibility aliases/wrappers.

### 7. Wrong vs Correct

#### Wrong

```python
# history_store.py
from shuheng.app import path_is_within, MODEL_RESPONSES_DIR
```

#### Correct

```python
# history_store.py or another lower-level store
from shuheng import path_utils

path_utils.is_normal_session_log_path(
    path,
    model_responses_dir=model_responses_dir,
    session_trash_dir=session_trash_dir,
)
```

## Scenario: Shared JSONL Ledger Store

### 1. Scope / Trigger

- Trigger: Shuheng reads or writes task ledgers, approvals, artifacts, traces, checkpoints, recovery rows, scheduler rows, gateway rows, or other JSONL governance records.
- Applies to: `src/shuheng/ledger_store.py`, compatibility wrappers in `src/shuheng/app.py`, scheduler runtime callbacks, dashboard home-page registry signatures, task/approval/artifact panels, and policy-gate checks.
- Non-goal: This does not move domain-specific task, approval, artifact, dashboard, or recovery projection logic out of `app.py` in one large rewrite.

### 2. Signatures

- Shared module: `src/shuheng/ledger_store.py`.
- Public helpers:
  - `append_jsonl(path, payload)`
  - `read_jsonl(path, limit=0, on_parse_error=None)`
  - `jsonl_file_signature(path)`
  - `latest_records_by_id(path, key)`
  - `rows_matching(path, key, value)`
  - `clear_jsonl_caches()`
  - `update_json_dict_file(path, updater)`
- Compatibility wrappers in `app.py` may keep the old function names, but should delegate to `ledger_store`.

### 3. Contracts

- JSONL append locking, cross-process `flock`, latest-record cache ownership, cache invalidation, and file signature logic belong to `ledger_store`, not to the curses application module.
- `app.py` remains allowed to own domain projections such as `latest_task_records()`, `approval_latest_records()`, `artifact_index_latest()`, `task_panel_items()`, and home-page rendering, but those projections must consume the shared ledger helpers.
- `latest_records_by_id(...)` returns copies of cached rows so callers cannot mutate process-local cache state by editing returned dictionaries.
- Any successful `append_jsonl(...)` must invalidate latest-record cache entries for that normalized path before later reads can use stale data.
- JSON object files used as governance locks, including `locks.json`, must use
  `ledger_store.update_json_dict_file(...)` so read-modify-write cycles are
  protected by process-local and cross-process locks. Do not split lock acquire
  into independent `load -> mutate -> write_text_atomic` operations.
- `read_jsonl(...)` skips corrupt and non-dict lines. App-level callers may pass a parse-error callback to preserve diagnostics without forcing `ledger_store` to import `app.py`.
- `ledger_store.py` must not import curses, `shuheng.app`, `State`, or `SubAgentRuntime`.

### 4. Validation & Error Matrix

- App source reintroduces `_LATEST_RECORDS_CACHE` or `_jsonl_append_lock` -> policy gate fails.
- App source performs `fcntl.flock` directly for ledger appends -> policy gate fails.
- `single_writer` acquire/release reads `locks.json`, decides ownership, and
  writes with a separate unguarded call -> two writer processes can acquire at
  once and the policy gate/unit tests must fail.
- Returned latest-record row is mutated by a caller -> subsequent latest-record calls still return the original cached data.
- Append a newer row for an existing id -> next latest-record call returns the newer row.
- Corrupt JSONL line -> row is skipped and optional parse diagnostics can be emitted by the caller.

### 5. Good/Base/Bad Cases

- Good: `dashboard home -> latest_task_records() -> latest_records_by_id(...) -> ledger_store cache`.
- Good: `scheduler.py` receives app-provided `read_jsonl` / `append_jsonl` callbacks that ultimately use `ledger_store`.
- Base: `app.py` still owns UI-specific panel projection while the storage/cache mechanics live in `ledger_store`.
- Bad: A future dashboard or approval feature adds a second latest-record cache in `app.py`.

### 6. Tests Required

- `tests/test_jsonl.py` must cover append/read behavior, latest-record cache copy safety, cache invalidation after append, field-history filtering, file signatures, JSON dict update return values, and cross-process serialized read-modify-write updates.
- `scripts/check_policy_gates.py` must assert `ledger_store` has no curses/app dependency and `app.py` no longer owns JSONL append locks or latest-record cache internals.
- `python3 scripts/check_policy_gates.py`, `python3 -m pytest -q -p no:cacheprovider`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# app.py
_LATEST_RECORDS_CACHE = {}
def latest_records_by_id(...):
    ...
```

#### Correct

```python
# app.py
def latest_records_by_id(path, key):
    return ledger_store.latest_records_by_id(path, key)
```

## Scenario: Persistent Progress Ledger

### 1. Scope / Trigger

- Trigger: A task, plan step, subagent task, scheduler run task, recovery action, or approval-blocked task changes state through `append_task_ledger(...)`.
- Applies to: `AGENT_PROGRESS_LEDGER_PATH`, `append_progress_ledger(...)`, `progress_history(...)`, `latest_progress_records(...)`, `context_layers_for_task(...)`, dashboard home-page cache signatures, MCP resources, gateway audit metadata, governance store paths, and baseline comparison.
- Non-goal: This does not replace `tasks.jsonl` as the authoritative task ledger and does not store raw runtime transcripts in progress rows.

### 2. Signatures

- Store path: `~/.shuheng/memory/agent_harness/progress.jsonl`.
- Schema version: `agentprogress.v1`.
- Required fields:
  - `progress_id`
  - `timestamp`
  - `task_id`
  - `parent_task_id`
  - `status`
  - `assigned_agent`
  - `title`
  - `kind`
  - `summary`
  - `error`
  - `artifact_refs`
  - `source`
  - `task_ref`

### 3. Contracts

- Every `append_task_ledger(...)` call appends the original `agenttask.v1` row to `tasks.jsonl` and appends a compact `agentprogress.v1` row to `progress.jsonl`.
- Progress rows are compact status facts for context hydration and recovery scanning. They must not inline artifact bodies, full transcripts, Secret Vault plaintext, or unbounded raw tool output.
- `context_layers_for_task(...)` uses `progress.jsonl` for `L5_progress_ledger`, falling back to recent task rows only when no progress rows exist.
- Home-page cache signatures include `progress.jsonl` so independently appended progress rows can refresh dashboard views.
- MCP resources expose `resource://agent-mail/progress`, and gateway/governance metadata includes the progress store path.
- Architecture baseline comparison treats progress ledger availability as part of the shared-ledger evidence.

### 4. Validation & Error Matrix

- Task row appended -> corresponding progress row with same `task_id` and `status` exists.
- Task status later changes -> progress history has multiple rows and latest-progress lookup includes the newer progress id.
- Context pack generation after progress rows exist -> `L5_progress_ledger.items` includes progress data, not just task ledger rows.
- MCP resource registry misses progress -> policy gate fails.
- Governance store paths miss progress -> policy gate fails.

### 5. Good/Base/Bad Cases

- Good: `append_task_ledger("task_x", status="working", summary="reading files")` writes both `tasks.jsonl` and `progress.jsonl`.
- Good: `L5_progress_ledger` includes compact rows such as `task_x: working reading files`.
- Base: Legacy tasks created before progress support may not have matching progress rows; new task updates populate the progress ledger.
- Bad: `L5_progress_ledger` is only a formatted copy of the last few task rows when `progress.jsonl` already exists.
- Bad: Progress rows include full subagent chat transcripts or Secret plaintext.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert task ledger writes generate `agentprogress.v1` rows, progress history is readable by task id, latest-progress lookup works, context hydration reads progress rows into L5, and MCP/governance/baseline surfaces expose the progress ledger.
- `python3 scripts/check_policy_gates.py`, `python3 -m pytest -q -p no:cacheprovider`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
progress_items = [format_task(row) for row in read_jsonl("tasks.jsonl")]
```

#### Correct

```python
progress_items = [format_progress(row) for row in read_jsonl("progress.jsonl")]
```

## Scenario: Governance Subagent Result Helper Boundary

### 1. Scope / Trigger

- Trigger: `app.py` decomposition moves subagent-result task-ledger row interpretation into `governance.py`.
- Applies to: subagent-result artifact-ref selection, generated artifact body prelude stripping, subagent result display-name derivation, first task timestamp lookup, and completed subagent-result row detection.
- Non-goal: This does not move durable UI system-message backfill, session metadata writes, history restore, scheduled report row construction, Web Console payloads, rendering, command handlers, runtime dispatch, artifact path resolution, or storage-root behavior.

### 2. Signatures

- `governance.subagent_result_artifact_ref(refs) -> str`
- `governance.subagent_result_body_from_text(text) -> str`
- `governance.subagent_name_from_task_row(row, *, agent_name_lookup=None) -> str`
- `governance.subagent_result_task_first_timestamps(rows, *, timestamp_parser=None) -> dict[str, float]`
- `governance.completed_subagent_result_row(row) -> bool`
- `app.py` keeps compatibility wrappers for the old names and injects app-owned artifact file reads, `parse_timestamp_value`, `subagent_meta_path(...)`, `TEMP_SUBAGENTS_DIR`, and `load_subagent_meta_file(...)` where needed.

### 3. Contracts

- `governance.py` may interpret already-loaded task ledger rows and artifact text, but must not import `shuheng.app`, curses, mutable TUI `State`, render types, Web Console, dashboard, command handlers, or draw functions.
- `subagent_result_artifact_ref(...)` returns the first non-empty artifact ref containing `/subagent-results/` from a list; non-list inputs return `""`.
- `subagent_result_body_from_text(...)` strips the generated leading Markdown heading and optional `Task:` prelude from an already-loaded artifact body, returning the remaining body or the original stripped text.
- `subagent_name_from_task_row(...)` strips the existing `子 agent 执行:` / `子 agent 执行：` title prefixes, falls back to title, then uses an injected `agent_name_lookup(agent_id)` before returning the assigned agent id.
- `subagent_result_task_first_timestamps(...)` computes the earliest valid timestamp per task id over already-loaded rows; app wrappers inject the legacy timestamp parser when preserving historical backfill semantics matters.
- `completed_subagent_result_row(...)` preserves the existing task ledger predicate: completed status, subagent-result artifact ref, and either `kind == "subagent_task"` or the existing assigned-agent/title subagent heuristics.
- `app.py` remains the owner of artifact URI to local path resolution, artifact file reads, subagent meta file discovery, durable UI notice persistence, history ownership, scheduled report row construction, rendering, commands, and runtime side effects.

### 4. Validation & Error Matrix

- `artifact_refs` contains a normal artifact then a subagent-results artifact -> returns the subagent-results artifact.
- Non-list `artifact_refs` -> `""`.
- Generated artifact body beginning with `# ...`, blank lines, and `Task: ...` -> returns only the result body.
- Task title `子 agent 执行: Coder` -> display name `Coder`.
- Empty title and assigned agent with injected lookup -> injected display name.
- Duplicate task rows with timestamps -> first timestamp wins.
- Completed non-subagent row without subagent-result artifact -> false.
- Completed `subagent_task` row with subagent-result artifact -> true.

### 5. Good/Base/Bad Cases

- Good: `backfill_durable_subagent_result_messages_for_path(...)` stays in `app.py` but delegates row predicates and artifact body cleanup to `governance.py`.
- Base: `app.py` wrappers still read the artifact file and subagent meta files because those paths are mutable app-owned runtime roots.
- Bad: `governance.py` imports `shuheng.app` to resolve artifact URIs or read `TEMP_SUBAGENTS_DIR`.
- Bad: Governance helpers inline artifact bodies into progress rows or change task ledger schemas.

### 6. Tests Required

- Unit tests must assert direct governance helper behavior for artifact refs, generated body stripping, display names, first timestamps, and completed-row predicates.
- Tests or policy gates must assert app wrapper parity for artifact file reads and subagent meta lookup with retargeted paths.
- `scripts/check_policy_gates.py` must assert `governance.py` has no reverse dependency on `app.py`, curses, mutable TUI `State`, render types, draw functions, or panel/command formatters.
- `python3 scripts/check_policy_gates.py`, `python3 -m pytest -q -p no:cacheprovider`, `python3 -m compileall -q src scripts`, `git diff --check`, and release smoke gates must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# governance.py
from shuheng.app import TEMP_SUBAGENTS_DIR, artifact_path_from_uri
```

#### Correct

```python
# app.py
governance.subagent_name_from_task_row(row, agent_name_lookup=lookup_name)
```

## Scenario: Governance Checkpoint Recovery Helper Boundary

### 1. Scope / Trigger

- Trigger: `app.py` decomposition moves checkpoint/recovery read-model helpers into `governance.py`.
- Applies to: checkpoint-history lookup, recovery-history lookup, recovery-plan-history lookup, checkpoint id lookup, latest-checkpoint selection, checkpoint snapshot reads, and replay-step shaping.
- Non-goal: This does not move checkpoint writes, recovery-plan writes, recovery records, recovery action execution, policy approval queuing, subagent runtime mutation, panel rendering, command handlers, Web Console payloads, or storage-root behavior.

### 2. Signatures

- `governance.checkpoint_history(checkpoint_index_path, task_id) -> list[dict]`
- `governance.recovery_history(recovery_path, task_id) -> list[dict]`
- `governance.recovery_plan_history(recovery_plans_path, task_id) -> list[dict]`
- `governance.checkpoint_index_by_id(checkpoint_index_path, checkpoint_id) -> dict`
- `governance.latest_checkpoint_for_task(checkpoint_index_path, task_id) -> dict`
- `governance.read_checkpoint_snapshot(checkpoint) -> dict`
- `governance.recovery_replay_steps(action) -> list[dict]`
- `app.py` keeps compatibility wrappers for the old names and injects `AGENT_CHECKPOINT_INDEX_PATH`, `AGENT_RECOVERY_PATH`, and `AGENT_RECOVERY_PLANS_PATH`.

### 3. Contracts

- `governance.py` may read already-selected JSONL store paths and checkpoint snapshot files, but must not import `shuheng.app`, curses, mutable TUI state, render types, Web Console, dashboard, command handlers, or draw functions.
- Checkpoint/recovery history helpers filter rows by exact `task_id` and preserve row order from the source ledger.
- `checkpoint_index_by_id(...)` returns the latest matching row by reverse ledger scan, or `{}` when no row exists.
- `latest_checkpoint_for_task(...)` uses existing row timestamp ordering and returns `{}` when a task has no checkpoint.
- `read_checkpoint_snapshot(...)` returns only dictionary JSON payloads; missing path, unreadable file, invalid JSON, or non-dict JSON returns `{}`.
- `recovery_replay_steps(...)` preserves the existing replay-step contract for `retry`, `cancelled`, `failed`, and `release_lock`, with an explicit `manual_review` fallback for unknown actions.
- `app.py` remains the owner of checkpoint creation, recovery-plan artifact creation, recovery action execution, policy approval gates, single-writer release, subagent runtime mutation, panel projection, command routing, and current mutable storage roots.

### 4. Validation & Error Matrix

- Two checkpoint rows for a task -> `checkpoint_history(...)` returns both in ledger order.
- Multiple checkpoints with timestamps -> `latest_checkpoint_for_task(...)` returns the newest row.
- Unknown checkpoint id -> `{}`.
- Bad checkpoint snapshot path, invalid JSON, or JSON list -> `{}`.
- Recovery rows for multiple tasks -> only exact task rows are returned.
- `retry` replay steps include restart/link replacement steps.
- Unknown recovery action -> final step is `manual_review`.

### 5. Good/Base/Bad Cases

- Good: `recovery_panel_items(...)` stays in `app.py` but delegates checkpoint/recovery row lookup through compatibility wrappers.
- Base: `append_recovery_plan(...)` still lives in `app.py` because it creates artifacts, reads app-owned task rows, and records policy state.
- Bad: `governance.py` imports `State` or subagent runtime classes to decide whether a recovery is live.
- Bad: `governance.py` queues approvals or mutates task/subagent runtime state during a read-model lookup.

### 6. Tests Required

- Unit tests must assert direct governance helper behavior for checkpoint histories, recovery histories, latest checkpoint selection, snapshot-read error handling, replay-step shaping, and app wrapper parity under retargeted paths.
- `scripts/check_policy_gates.py` must assert the expanded governance boundary and wrapper parity.
- `python3 scripts/check_policy_gates.py`, `python3 -m pytest -q -p no:cacheprovider`, `python3 -m compileall -q src scripts`, `git diff --check`, and release smoke gates must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# governance.py
from shuheng.app import State, AGENT_CHECKPOINT_INDEX_PATH
```

#### Correct

```python
# app.py
def latest_checkpoint_for_task(task_id):
    return governance.latest_checkpoint_for_task(AGENT_CHECKPOINT_INDEX_PATH, task_id)
```

## Scenario: Governance Task Display Helper Boundary

### 1. Scope / Trigger

- Trigger: `app.py` decomposition moves pure task-ledger display row interpretation into `governance.py`.
- Applies to: task status markers, subagent-task row detection, and task display title fallback over already-loaded rows.
- Non-goal: This does not move owner display-name lookup, subagent meta file IO, mutable TUI state reads, rightbar rows, panel rendering, Web Console payloads, dashboard home lines, command handlers, or storage-root behavior.

### 2. Signatures

- `governance.task_status_marker(status, approval="-") -> str`
- `governance.row_looks_like_subagent_task(row, owner) -> bool`
- `governance.task_display_title(row, *, owner_name="") -> str`
- `app.py` keeps compatibility wrappers for the old names. `task_display_title(row, state=None)` injects app-owned `task_owner_display_name(state, row)`.

### 3. Contracts

- `governance.py` may interpret task ledger row values, status strings, approval status, and an already-resolved owner display name.
- `governance.py` must not import `shuheng.app`, curses, mutable TUI state, render types, Web Console, dashboard, command handlers, draw functions, or subagent meta file IO.
- `task_status_marker(...)` preserves the existing marker mapping: completed -> `✓`, failed/cancelled/rejected/aborted -> `✕`, pending approval/input -> `?`, running/working/accepted/pending -> `●`, and default -> `○`.
- `row_looks_like_subagent_task(...)` preserves the existing predicate: explicit `subagent_task` / `subagent` kind or owner id starting with `agent-` / `tmp-`.
- `task_display_title(...)` preserves existing title precedence: `title`, `display_title`, `task_title`, subagent owner-name fallback, objective/summary/error/task id, then `任务`.
- `app.py` remains the owner of resolving owner display names from live subagents or subagent metadata files and of all visible row rendering.

### 4. Validation & Error Matrix

- Completed, failed, waiting-input, working, and unknown statuses -> expected markers.
- Explicit title fields -> first non-empty title wins.
- Subagent row plus injected owner name -> `子 agent 任务: <name>`.
- Normal row plus owner name -> objective/summary/error/task-id fallback, not subagent title.
- Empty row -> `任务`.

### 5. Good/Base/Bad Cases

- Good: rightbar/panel code stays in `app.py` and calls compatibility wrappers for row title and marker text.
- Base: `task_owner_display_name(...)` stays in `app.py` because it reads live subagents and metadata files.
- Bad: `governance.py` imports `State` or `load_subagent_meta(...)` to resolve names.
- Bad: display-title extraction changes task ledger schema or approval semantics.

### 6. Tests Required

- Unit tests must assert direct governance helper behavior for marker mapping, subagent row predicates, title precedence, owner-name fallback, and wrapper parity.
- `scripts/check_policy_gates.py` must assert the expanded governance boundary and wrapper parity.
- `python3 scripts/check_policy_gates.py`, `python3 -m pytest -q -p no:cacheprovider`, `python3 -m compileall -q src scripts`, `git diff --check`, and release smoke gates must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# governance.py
from shuheng.app import State, load_subagent_meta
```

#### Correct

```python
# app.py
def task_display_title(row, state=None):
    return governance.task_display_title(row, owner_name=task_owner_display_name(state, row))
```

## Scenario: Governance Plan Selection Helper Boundary

### 1. Scope / Trigger

- Trigger: `app.py` decomposition moves pure active-plan selection over already-loaded task rows into `governance.py`.
- Applies to: selecting a plan id from `(task_id, row)` pairs using row kind, preferred id, terminal status, active-only requirements, and timestamp ordering.
- Non-goal: This does not move rightbar selected-plan state, active plan hydration, plan-step resolution, task-plan creation, task ledger writes, command handlers, panel rendering, Web Console payloads, or storage-root behavior.

### 2. Signatures

- `governance.selected_plan_id_from_rows(rows, preferred_plan_id="", require_active=False) -> str`
- `app.py` keeps the compatibility wrapper with the old name and signature.

### 3. Contracts

- `governance.py` may interpret already-loaded task ledger row values, row kind, status strings, and timestamps.
- `governance.py` must not import `shuheng.app`, curses, mutable TUI state, render types, Web Console, dashboard, command handlers, draw functions, or ledger write helpers for plan selection.
- Only rows with `kind == "plan"` are plan candidates.
- A non-empty preferred plan id wins when it exists among plan candidates, even before active filtering.
- Active plans are plan rows whose status is not terminal according to the existing terminal task status predicate.
- `require_active=True` returns `""` when no active plan candidate exists.
- Without active candidates and without `require_active`, the fallback returns the newest plan candidate by existing row timestamp ordering.
- `app.py` remains the owner of resolving the current UI session, mutating active plan state, hydrating plan steps, rightbar/panel rendering, task ledger writes, command routing, and mutable storage roots.

### 4. Validation & Error Matrix

- Preferred id points to a plan row -> returns that id.
- Non-plan rows are newer than plan rows -> ignored.
- Active plan exists and terminal plan is newer -> active plan wins unless the terminal plan is the preferred id.
- `require_active=True` with only terminal plan rows -> `""`.
- Only terminal plan rows with `require_active=False` -> newest terminal plan id.
- No plan rows -> `""`.

### 5. Good/Base/Bad Cases

- Good: `rightbar_selected_plan_id(...)` stays in `app.py` and delegates the row-selection rule through the compatibility wrapper.
- Base: `hydrate_active_plan_from_ledger(...)` stays in `app.py` because it reads latest task records, filters by active UI session, mutates active plan state, and resolves plan steps.
- Bad: `governance.py` imports `State` or reads task ledgers to discover the current plan.
- Bad: plan selection changes task ledger schema, terminal status semantics, active-plan hydration side effects, or auto-continue reset behavior.

### 6. Tests Required

- Unit tests must assert preferred id, active-vs-terminal selection, active-required empty fallback, newest fallback, non-plan filtering, and app wrapper parity.
- `scripts/check_policy_gates.py` must assert the expanded governance boundary and wrapper parity.
- `python3 scripts/check_policy_gates.py`, `python3 -m pytest -q -p no:cacheprovider`, `python3 -m compileall -q src scripts`, `git diff --check`, and release smoke gates must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# governance.py
from shuheng.app import State, latest_task_records
```

#### Correct

```python
# app.py
def selected_plan_id_from_rows(rows, preferred_plan_id="", require_active=False):
    return governance.selected_plan_id_from_rows(rows, preferred_plan_id, require_active=require_active)
```

## Scenario: Secret Vault Value Helper Boundary

### 1. Scope / Trigger

- Trigger: `app.py` decomposition moves Secret Vault value shaping into `secret_vault.py`.
- Applies to: Secret session title fallback, Secret session-state payload titles, Secret import argument parsing, Secret proxy-chain parsing, proxy endpoint string normalization, imported/native Secret entry matching, imported/native link checks, imported native-match lookup, and imported-session raw-log message shaping.
- Non-goal: This does not move Secret unlock/setup state, password-entry UI, Secret prompt rendering, import validation/execution, ordinary-source deletion/archive, encrypted file IO, network health checks, proxy environment mutation, native/imported restore orchestration, backend reset, history parsing, Web Console payloads, commands, rendering, or transcript storage.

### 2. Signatures

- `secret_vault.secret_session_title_for_messages(title, messages) -> str`
- `secret_vault.secret_session_state_payload(session_id, title, messages, source="", origin=None) -> dict`
- `secret_vault.parse_secret_import_args(raw) -> tuple[str, str]`
- `secret_vault.parse_secret_proxy_chain(raw) -> list[str]`
- `secret_vault.normalize_secret_proxy_endpoint(endpoint) -> str`
- `secret_vault.resolve_secret_imported_session_entry(entries, target) -> tuple[dict | None, str]`
- `secret_vault.resolve_secret_native_session_entry(entries, target) -> tuple[dict | None, str]`
- `secret_vault.secret_import_represented_by_native(import_entry, native_entries) -> bool`
- `secret_vault.secret_native_entry_for_import_entry(import_entry, native_entries) -> dict | None`
- `secret_vault.messages_from_secret_import_payload(payload, *, parse_pairs, messages_from_pairs, restore_display_rounds) -> tuple[list[Message], int, int, int]`
- `app.py` re-exports the moved helpers as compatibility aliases or thin wrappers when app-owned state/parser dependencies must be injected.

### 3. Contracts

- Secret value helpers may depend on `Message`, text helpers, and existing history-title fallback policy, but must not import `shuheng.app`, curses, mutable TUI `State`, runtime providers, Web Console, dashboard, command handlers, or rendering owners.
- `secret_session_title_for_messages(...)` strips a `Secret: ` prefix, rejects placeholder titles such as `main` / `Secret Vault` / running or idle labels, and falls back to a message-derived title or `Secret 会话`.
- `secret_session_state_payload(...)` must normalize the persisted payload title through `secret_session_title_for_messages(...)`.
- `parse_secret_import_args(...)` maps delete/archive aliases while preserving unknown text as the target.
- `parse_secret_proxy_chain(...)` accepts comma, whitespace, semicolon, and `->` separators without reading environment variables.
- `normalize_secret_proxy_endpoint(...)` maps `tor` to the default Tor SOCKS endpoint and prefixes bare endpoints with `socks5h://`.
- `resolve_secret_imported_session_entry(...)` owns only pure matching over already-loaded imported session entries: it filters error rows, returns the existing usage message for an empty target, accepts 1-based numeric targets, and matches the existing imported-session candidate set of raw path, normalized path, filename, filename without `.secret`, `stable_id`, and source `basename`.
- `resolve_secret_native_session_entry(...)` owns only pure matching over already-loaded native Secret session entries: it filters error rows, returns the existing usage message for an empty target, accepts 1-based numeric targets, and matches `session_id`, title, or the sidebar-key form after normal sidebar-key normalization.
- `secret_import_represented_by_native(...)` owns only pure imported/native entry linking: it compares normalized import paths, stable ids, and titles over already-loaded entries, and empty fields must not create accidental matches.
- `secret_native_entry_for_import_entry(...)` owns only first-match selection over already-loaded native entries: it skips error rows, delegates match semantics to `secret_import_represented_by_native(...)`, and returns the first matching native entry or `None`.
- `messages_from_secret_import_payload(...)` owns only imported-session payload/raw-log message shaping. It must receive raw-log pair parsing, history-message conversion, and restore-round policy as injected callables/values from `app.py`; it must not import `continue_cmd`, own `_pairs`, parse native provider history, reset runtime state, or restore backend context.
- Imported-session raw logs with parsed pairs use injected history-message conversion; non-empty unparseable raw logs become one assistant message; empty payloads become the existing `Secret 导入会话为空。` system message.
- `app.py` remains the owner of mutable Secret state, approval gates, command wiring, source file migration side effects, proxy env mutation, network health checks, and runtime/backend restore.

### 4. Validation & Error Matrix

- Title `Secret: main` plus a user message -> payload title uses the message-derived title.
- Title `Secret: 手动标题` -> title is `手动标题`.
- Empty title and no messages -> title is `Secret 会话`.
- Import args `archive 2` -> `("archive", "2")`.
- Import args `删除 id:abc` -> `("delete", "id:abc")`.
- Import args with unknown first token -> defaults to delete disposition and treats the whole text as target.
- Proxy chain `tor -> host:9051; http://proxy` -> `["tor", "host:9051", "http://proxy"]`.
- Proxy endpoint `host:9051` -> `socks5h://host:9051`.
- Imported resolver target `id:stable-alpha` -> matching non-error imported entry.
- Imported resolver duplicate stable id -> `匹配到多个 Secret 导入会话：<target>`.
- Native resolver target `secret_session:native-alpha` -> matching non-error native entry.
- Native resolver duplicate title -> `匹配到多个 Secret 会话：<target>`.
- Imported/native link predicate matches by normalized `origin_import_path`, `origin_stable_id`, or title.
- Imported/native link predicate with all-empty values -> no match.
- Native-entry lookup skips error rows and returns the first non-error imported/native match.
- Native-entry lookup with no represented native entry -> `None`.
- Imported-session payload with parsed raw-log pairs -> helper returns injected history messages plus loaded/total round counts.
- Imported-session payload with non-empty unparseable raw log -> helper returns one assistant message and `(loaded_rounds, total_rounds, message_count) == (1, 1, 1)`.
- Imported-session payload with empty raw log -> helper returns the empty Secret import system message and `(loaded_rounds, total_rounds, message_count) == (0, 0, 1)`.

### 5. Good/Base/Bad Cases

- Good: `secret_vault.py` owns Secret payload title normalization, import/proxy value parsing, resolver/link predicates, native-match lookup, and import raw-log message shaping without touching storage or UI state.
- Base: `app.py` calls direct aliases for root-free helpers and keeps wrappers for native-entry loading and import-message shaping because it injects app-owned `State`, history parser, and display policy while still owning command handling and side effects.
- Bad: `secret_vault.py` imports `shuheng.app` to read `SECRET_DEFAULT_TOR_SOCKS` or call command/runtime helpers.
- Bad: A pure parsing helper reads environment variables, checks network sockets, mutates proxy env vars, or queues policy approvals.

### 6. Tests Required

- Unit tests must assert Secret title fallback, payload title normalization, import arg aliases, proxy chain parsing, endpoint normalization, imported/native resolver behavior, imported/native link predicate behavior, native-match lookup behavior, imported payload message shaping, and app alias/wrapper parity.
- `scripts/check_policy_gates.py` must assert moved helper ownership and that `secret_vault.py` has no reverse import into `app.py` or curses/UI owners.
- `python3 scripts/check_policy_gates.py`, `python3 -m pytest -q -p no:cacheprovider`, `python3 -m compileall -q src scripts`, `git diff --check`, and release smoke gates must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# secret_vault.py
from shuheng.app import SECRET_DEFAULT_TOR_SOCKS, State
```

#### Correct

```python
# app.py
normalize_secret_proxy_endpoint = secret_vault_store.normalize_secret_proxy_endpoint
```

## Scenario: Direct Subagent Chat Visibility

### 1. Scope / Trigger

- Trigger: A user sends direct chat text to a selected persistent or temporary subagent through TUI plain text, persistent-subagent home input, `/chat`, or Web-console `agent.chat`.
- Applies to: `start_subagent_chat(...)`, `queue_subagent_chat_input(...)`, `consume_stream_queue_to_ui(...)`, `process_ui_queue(...)`, history-backed subagent chat persistence, subagent event logs, and Web-console runtime pump behavior.
- Non-goal: This does not convert direct chat into a task-ledger `subagent_task`, bypass approval policy, or add free-form peer-to-peer agent chat outside the governed Orchestrator-owned runtime.

### 2. Signatures

- TUI direct chat entry: `submit(state, text)` when `selected_subagent(state)` or `selected_home_subagent(state)` is active.
- Dispatcher: `start_subagent_chat(state, sub, prompt, source="subagent_chat") -> str`.
- Queue path: `queue_subagent_chat_input(state, sub, text, interrupt_requested=False) -> str`.
- Stream path: `consume_subagent_chat_queue(...)` emits `("sub_chat_stream", subagent_id, task_id, text, done)`.
- Web action: `POST /gui/action` with `action:"agent.chat"` resolves a sanitized agent `ui_ref` and calls the same dispatcher.
- Subagent store helpers: `subagent_store.clean_subagent_id(...)`, `subagent_store.normalize_subagent_identity_text(...)`, `subagent_store.compact_identity_text(...)`, `subagent_store.normalize_subagent_skill_refs(...)`, `subagent_store.parse_subagent_new_body(...)`, `subagent_store.unique_*_subagent_id(...)`, `subagent_store.subagent_home(...)`, `subagent_store.subagent_*_path(...)`, `subagent_store.subagent_session_sidebar_key(...)`, `subagent_store.subagent_session_from_sidebar_key(...)`, `subagent_store.subagent_chat_history_meta_matches(...)`, and pure subagent chat title/preview/description/count helpers, with `app.py` wrappers injecting app-owned roots such as `SUBAGENTS_DIR`, supported role keys, role normalization, explicit existing-id sets, or runtime objects such as `SubAgentRuntime`.

### 3. Contracts

- Every non-empty accepted direct-chat input must create visible feedback in the subagent chat pane: a pending assistant row, a completed assistant error row, or a system queue notice.
- A queued direct-chat input must be stored in `sub.chat_queue`, increment `chat_queued` in metadata, and add a readable system notice to the chat session without displacing the trailing unfinished assistant stream row.
- A blocked direct-chat input, such as locked Secret Vault or failed default-model application, must persist the user's attempted message plus a completed assistant error message.
- A runtime `done` frame with no visible text must be converted to an explicit `[ERROR] runtime completed without a visible reply.` message and treated as a runtime failure.
- Non-secret persistent direct-chat transcripts must be saved in canonical Shuheng history under `MODEL_RESPONSES_DIR` with subagent metadata such as `conversation_scope`, `agent_id`, and `subagent_chat_session_id`; per-agent `sessions/*.json` files are legacy import sources only and must not receive new authoritative non-secret transcripts. Subagent runtime agents must use a non-persistent transcript sink such as `os.devnull`, not `sub.home/model_responses.txt`, so agent-local state stays metadata/refs/runtime only.
- Subagent home/path helpers belong to `subagent_store.py` only as metadata/ref path helpers. They must not become a second transcript writer or read/write normal non-secret chat messages.
- `subagent_store.clean_subagent_id(...)`, `subagent_store.normalize_subagent_identity_text(...)`, `subagent_store.compact_identity_text(...)`, and `subagent_store.unique_*_subagent_id(...)` own only pure identity/ref shaping. App wrappers must inject mutable roots or existing runtime ids; the store module must not import `State` or inspect runtime objects.
- `subagent_store.normalize_subagent_skill_refs(...)` owns only pure skill-ref value shaping for metadata fields. It must not scan skill roots, read skill files, assemble prompt packs, persist metadata, inspect runtime state, or import Secret/history/Web/rendering owners.
- `subagent_store.parse_subagent_new_body(body, supported_roles=..., normalize_role=...)` owns only pure `/agent new` body parsing: lifecycle flags/prefixes, profile splitting, and role-prefix recognition. Supported roles and role normalization must be injected by `app.py`, because app remains the role-template and reserved-role policy owner. The store helper must not import role templates, mutate metadata, create subagents, inspect runtime state, or write history.
- `subagent_store.subagent_chat_history_meta_matches(meta, agent_id, session_id)` owns only the pure metadata/ref predicate: scope must be `subagent_chat`, agent id must match, and a non-empty requested session id must match `subagent_chat_session_id`.
- `subagent_store.normalize_loaded_subagent_chat_messages(...)`, `subagent_store.subagent_chat_history_preview_messages(...)`, `subagent_store.subagent_chat_title_for_messages(...)`, `subagent_store.subagent_chat_history_preview(...)`, `subagent_store.subagent_chat_history_description(...)`, `subagent_store.subagent_chat_history_rounds(...)`, and `subagent_store.subagent_chat_history_last_user_at(...)` own only metadata title/preview/description/count shaping. They must not decode Secret Vault message records, parse history transcript files, write history rows, or inspect runtime state.
- `app.subagent_chat_title_for_messages(...)`, `app.subagent_chat_history_preview(...)`, and `app.subagent_chat_history_description(...)` remain compatibility wrappers that inject `SubAgentRuntime` display fields, `latest_visible_reply_text(...)`, and app display limits while preserving the canonical-history ownership invariant.
- Restoring a non-secret persistent direct-chat session must parse the
  canonical Shuheng history transcript first. `session_meta.json` may cache
  title, preview, counts, and routing refs, but it must not be the
  authoritative full transcript source; legacy full-message meta is only a
  fallback when the transcript is missing or empty.
- Subagent metadata must be written from a positive runtime/navigation schema. Saving `meta.json` or encrypted meta must not carry forward stale transcript fields such as `messages`, `subagent_chat_messages`, or embedded session payloads from older metadata files.
- Secret subagent direct-chat transcripts must stay encrypted in Secret Vault storage and must not be copied into normal plaintext history.
- Successful direct-chat replies continue to save chat session messages in canonical history, subagent events, token usage, context-pack artifact refs, and memory-candidate approval notices.
- Direct chat must keep using role permissions, runtime context packs, and memory-candidate approval flow. It must not write task-result artifacts or task-ledger completion rows unless dispatched as `start_subagent_task(...)`.

### 4. Validation & Error Matrix

- Empty prompt -> return `子 agent 聊天输入为空。`; no chat mutation.
- Secret subagent while vault locked -> visible assistant error row; no runtime task.
- Default model cannot be applied -> visible assistant error row; no runtime prompt sent.
- Subagent already running/aborting or runtime has unfinished work -> queue input and render a system queue notice.
- Runtime stream emits partial text -> update the pending assistant row without losing follow-bottom behavior.
- Runtime stream emits empty final text -> visible `[ERROR] runtime completed without a visible reply.` and user-visible failure status.
- Runtime stream emits OMP/RPC terminal error -> release `active_task_id`, keep queued-chat progression, and surface failure in `state.last_error`.
- Non-secret subagent runtime created for direct chat -> runtime `log_path` is `os.devnull`; canonical chat history row exists under `MODEL_RESPONSES_DIR`; no `sub.home/model_responses.txt` transcript file is created.
- `session_meta.json` contains stale legacy `subagent_chat_messages` while the
  canonical history transcript exists -> reload must restore messages from the
  transcript, not the stale meta list.

### 5. Good/Base/Bad Cases

- Good: User types on a persistent-agent home; Shuheng switches to that agent chat, appends `user` + pending `assistant`, then streams the reply.
- Good: User types again while the subagent is still running; the new text appears as a queue system notice and is sent after the current assistant row completes.
- Good: A missing subagent default model writes `user: <attempt>` and `assistant: <model failure>` to the chat session, so the user sees why no runtime reply arrived.
- Base: Direct chat remains a chat session, not a governed work-order artifact, unless the user or Orchestrator dispatches `agent.task`.
- Bad: Returning only `state.last_error` for model failure while the chat pane has no new row.
- Bad: Appending a queue notice after an unfinished assistant row, causing `process_ui_queue()` to stop updating the active stream.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert direct-chat model-block failures create visible user/assistant chat rows and do not send a runtime prompt.
- Tests must assert queued direct-chat input renders a system notice while preserving the trailing unfinished assistant row for stream updates.
- Tests must assert empty runtime `done` output becomes an explicit error and sets the user-visible last-error path to chat failure.
- Tests must keep direct-chat memory-candidate approvals visible and ensure direct chat does not write `subagent-results` artifacts or task-ledger rows.
- Tests must keep TUI home plain-text and Web `agent.chat` on the shared `start_subagent_chat(...)` dispatcher, and assert Web agent conversation can hydrate from canonical history-backed subagent chat state instead of relying only on process-local `sub.messages`.
- Tests must assert non-secret persistent direct-chat persistence is history-backed and does not create new per-agent transcript JSON files or `sub.home/model_responses.txt` runtime transcript files; legacy per-agent JSON files remain non-destructively importable.
- Tests must assert subagent chat metadata matching is owned by `subagent_store.py`, app wrapper parity holds, wrong scope/agent/session rows are rejected, and `subagent_store.py` does not import history transcript or Secret Vault payload modules.
- Tests must assert subagent chat preview/count helpers are owned by `subagent_store.py`, app alias parity holds, interrupted assistant restoration is marked done with the durable suffix, preview rows filter unsupported roles and blank cleaned content, and round counts only include non-blank user rows.
- Tests must assert `/agent new` body parsing is owned by `subagent_store.py`, app wrapper parity holds, lifecycle flags and prefixes preserve existing behavior, unsupported role prefixes remain ordinary names, full-width role separators are accepted, and role-template policy is injected from `app.py` instead of imported by the store module.
- Tests must assert new non-secret history meta does not store a full
  `subagent_chat_messages` copy, and a seeded stale legacy meta copy cannot
  override the canonical transcript on reload.
- Tests must seed stale transcript-like fields in subagent `meta.json`, save metadata again, and assert the saved metadata only keeps runtime/navigation/lifecycle fields.

### 7. Wrong vs Correct

#### Wrong

```text
start_subagent_chat -> default model missing -> return last_error only
chat pane remains unchanged
user thinks the subagent ignored the message
```

#### Correct

```text
start_subagent_chat -> default model missing
chat pane: user attempted message + assistant error row
runtime prompt is not sent
state.last_error carries the same short reason
```

## Scenario: Local Web Console Gateway

### 1. Scope / Trigger

- Trigger: The gateway exposes a local Web GUI that visualizes Shuheng governance data as a restrained collaboration workspace and sends bounded user actions back through the governed Python harness.
- Applies to: `GatewayRequestHandler`, `/gui`, `/dashboard`, `/console`, `/gui/snapshot`, `/gui/action`, dashboard/home derived data, scheduled reports, task ledger summaries, approval summaries, artifact summaries, model summaries, persistent-subagent status cards, and Web-console action dispatch.
- Non-goal: This does not replace the TUI runtime, does not create a new scheduler, task ledger, approval inbox, artifact store, memory writer, model store, or browser-owned mutation system.

### 2. Signatures

- HTTP routes:
  - `GET /gui`, `GET /dashboard`, and `GET /console` return static HTML/CSS/JS for the local console.
  - `GET /gui/snapshot` returns JSON with `schema_version:"shuheng.web_console.snapshot.v1"`.
  - `POST /gui/action` accepts JSON with `schema_version:"shuheng.web_console.action_request.v1"` and returns `schema_version:"shuheng.web_console.action_response.v1"`.
- External GUI loader:
  - `src/shuheng/web_console_static.py`.
  - `web_console_html()` in `app.py` delegates to `shuheng.web_console_static.web_console_html`.
  - `SHUHENG_WEB_GUI_INDEX` points directly at a standalone `index.html`.
  - `SHUHENG_WEB_GUI_DIR` points at a standalone GUI project directory and resolves `public/index.html` or `index.html`.
  - Default local project path: `<home-or-workspace>/Projects/Shuheng-Web-GUI/public/index.html`, with the old sibling `<repo-parent>/Shuheng-Web-GUI/public/index.html` kept only as a compatibility fallback.
- Snapshot top-level fields:
  - `updated_at`
  - `mode:"read_only"`
  - `source`
  - `overview`
  - `agents`
  - `scheduled_reports`
  - `tasks`
  - `schedules`
  - `approvals`
  - `artifacts`
  - `model`
  - `actions`
  - `sidebar`
  - `totals`
  - `navigation`
- Action request fields:
  - `schema_version`
  - `action`
  - `ui_ref` or `target`
  - `payload`
- Action response fields:
  - `schema_version`
  - `ok`
  - `action`
  - `message`
  - optional `snapshot`

### 3. Contracts

- `/gui` serves the standalone local Web GUI HTML through the external loader. The GUI source of truth is outside `src/shuheng/app.py`, normally in `/home/vimalinx/Projects/Shuheng-Web-GUI`.
- The standalone GUI page stays self-contained HTML/CSS/JS and must not require a frontend build step for the local gateway path.
- `app.py` must not reintroduce a large embedded Web Console HTML/JS/CSS string. Backend code owns snapshot/action/state functions; the standalone GUI owns browser source.
- If no standalone GUI file is found, `/gui` returns a clear fallback page explaining `SHUHENG_WEB_GUI_INDEX`, `SHUHENG_WEB_GUI_DIR`, and checked paths; it must not silently write files or mutate gateway state.
- The standalone GUI dev server may proxy `/gui/*` to an existing Shuheng gateway, but browser mutations still go through the same `POST /gui/action` backend route.
- `/gui` default chrome uses a restrained workspace layout: persistent left channel/session/model navigation, a central channel header plus action composer plus open message/list rows, and a right context rail for agents/tasks. It must not default to a card grid, dramatic command-center shell, or raw admin dashboard visual model.
- `/gui` Slack-like navigation is functional, not decorative. Channel entries switch the central view, history/session rows open a sanitized session preview through `session.open`, and agent rows in the left direct-agent list, central agent list, and right context rail select that agent and prefill agent-scoped composer actions.
- `/gui` browser navigation state is keyed by both the active center view and an explicit channel key. The workspace brand mark may navigate home, but only real rail channel buttons participate in active highlighting; main home, `# main`, reports, governance, agents, session preview, and selected-agent states must not double-highlight unrelated channels.
- Leaving an agent-selected surface for main home, `# main`, reports, governance, or session preview must clear the active subagent selection and reset stale `agent.*` composer modes back to the main prompt. Changing the composer target select alone must not navigate or change the active agent.
- `/gui` must collect mutable user input through native in-page controls and forms, not browser prompt/alert dialogs. Row buttons may prefill the governed action composer, while one-click actions still post directly to `/gui/action`.
- `/gui/snapshot` builds a read-only `State` with a non-runtime placeholder agent, loads persisted subagent metadata, and derives display data from the existing shared task ledger, schedule registry, schedule-run records, approval registry, artifact index, and model config.
- `/gui` and `/gui/snapshot` must not call `ensure_gateway_registry(...)`, write `gateway.json`, append JSONL rows, queue approvals, dispatch tasks, mutate schedules, switch models, or write memory.
- `/gui/action` is the only Web-console mutation route. It must validate the request schema, allowlist known actions, resolve sanitized `ui_ref` handles server-side, and call existing governed functions such as `decide_approval(...)`, `apply_schedule_control(...)`, `scheduler_tick(...)`, `recover_task_action(...)`, `start_main_agent_task(...)`, `start_subagent_task(...)`, `start_subagent_chat(...)`, `set_subagent_default_model(...)`, `set_subagent_skill_refs(...)`, and `save_default_model(...)`.
- `/gui/action` must not accept raw task ids, approval ids, artifact URIs, filesystem session paths, or internal agent ids as the normal browser contract. Snapshot rows may carry opaque `ui_ref` values that map back to current server-side ledgers.
- Schedule create/update actions from the browser may submit a sanitized `target_agent_ref`; `/gui/action` resolves it server-side into the existing `agent_task.execution.routing.selected_agent` field before calling the shared scheduler registry.
- Browser-triggered runtime work must still drain the normal runtime queues so task completion, artifacts, token usage, memory candidates, TUI controls, traces, and ledger updates are persisted through the same paths used by the TUI.
- The Web console translates raw governance records into user-readable names, summaries, counts, and report bodies. Default visible HTML/JS-rendered content must not dump raw artifact URIs, approval ids, task ids, or internal agent ids as primary text.
- `session.open` resolves only a sanitized session `ui_ref` against current server-side history rows under `MODEL_RESPONSES_DIR`, marks the session opened when present, and returns a bounded preview payload with title, category, description, rounds, age, and cleaned recent messages. The response must not expose filesystem paths, `model_responses_*.txt` basenames, raw task ids, approval ids, artifact URIs, or internal agent ids.
- Scheduled-report rows must use the same cleaned scheduled-report body path as TUI home pages: completed child subagent replies from subagent result artifacts first, then task summary fallback, with OMP/LLM process markers and approval-only audit rows excluded.
- Artifact rows in the default Web console show type, source title, and size-style metadata only. Raw artifact refs remain available through existing gateway/MCP/resource drill-down routes, not the default GUI.
- Approval rows in the default Web console show approval type, target name, and human-readable summary only. Actual approval decisions must go through `/gui/action` and reuse `decide_approval(...)`.
- `sidebar` is display-only shell data for the Web console's TUI-like layout. It may include current-page entries, sanitized history titles/groups, current/default model summary, and aggregated token usage, but it must not expose normal-session paths, raw task ids, approval ids, or artifact URIs.

### 4. Validation & Error Matrix

- `GET /gui` -> HTML with console shell and client fetch for `/gui/snapshot`.
- `GET /gui` with a valid `SHUHENG_WEB_GUI_INDEX` -> returns that file exactly.
- `GET /gui` with only `SHUHENG_WEB_GUI_DIR` -> tries `<dir>/public/index.html`, then `<dir>/index.html`.
- `GET /gui` with no available standalone GUI file -> returns the fallback page and does not call `ensure_gateway_registry(...)` or mutate ledgers.
- Standalone GUI dev server `GET /` -> returns the same static console shell, while `GET /gui/snapshot` and `POST /gui/action` are proxied to the configured `SHUHENG_API_BASE`.
- `POST /gui/action` with a missing or wrong schema -> rejected without mutating ledgers.
- `POST /gui/action` with an unknown `ui_ref` -> rejected without mutating ledgers.
- `POST /gui/action` with `action:"session.open"` and a valid session `ui_ref` -> returns a sanitized preview payload and a refreshed snapshot; unknown or non-session refs are rejected without mutating ledgers.
- `POST /gui/action` approval approve/reject -> appends through the existing approval decision path and returns a sanitized message plus a fresh snapshot.
- `POST /gui/action` schedule enable/disable/delete/run -> uses the existing schedule registry or scheduler tick path and returns a sanitized message plus a fresh snapshot.
- `POST /gui/action` agent task/chat -> starts real governed runtime work or queues/blocks through existing policy gates, then a Web-console runtime pump drains the same UI queue path used by the TUI.
- `GET /dashboard` or `GET /console` -> same HTML alias as `/gui`.
- `GET /gui/snapshot` with empty ledgers -> valid snapshot with empty arrays and zero counts.
- `GET /gui/snapshot` -> `sidebar` contains `current_sessions`, `history`, `model`, and `tokens` objects derived from read-only state.
- Persistent subagents exist -> snapshot `agents` contains readable name, role, status, default model or inherited-model text, scoped skill refs, status narrative, and compact metrics.
- Scheduled report exists with process/thinking text in the artifact -> snapshot report body excludes process/thinking text and includes final reply text.
- Approval-required or cancelled schedule audit rows exist -> they do not appear in `scheduled_reports`; they may appear only as normal task or approval summaries when applicable.
- Opening `/gui` or `/gui/snapshot` -> task ledger, approval registry, artifact index, and gateway registry file signatures stay unchanged.

### 5. Good/Base/Bad Cases

- Good: `GET /gui/snapshot` shows `overview.metrics`, subagent rows, schedule definitions, full cleaned report bodies, and compact governance queues without writing any files.
- Good: `app.py` delegates `/gui` HTML loading to `web_console_static.py`, and the current browser UI source lives in `/home/vimalinx/Projects/Shuheng-Web-GUI/public/index.html`.
- Good: Running the standalone GUI dev server serves `/` locally and proxies `/gui/snapshot` plus `/gui/action` to a running Shuheng gateway without introducing a Node/Vite dependency.
- Good: `GET /gui` renders a Slack-like shell with channel navigation, a central channel header, open message rows, and a right context rail instead of `hero-card`, `agent-card`, or card-grid defaults.
- Good: Clicking a session row posts `session.open` with `session:<digest>` and opens a center-channel preview; clicking a persistent agent row selects that agent and sets the composer target without exposing its raw `agent-...` id.
- Good: The default GUI says `待审批 3` and shows readable summaries, while approval ids stay out of the visible page.
- Good: The default GUI says an artifact came from `主页巡检` with type `subagent-results`, while the raw `artifact://...` ref stays behind MCP/resource drill-down.
- Good: Clicking approve sends `POST /gui/action` with an approval `ui_ref`; the server resolves it, calls `decide_approval(...)`, and the browser receives only a sanitized result message.
- Good: Clicking a subagent task button starts `start_subagent_task(...)` and later task completion/artifact rows appear because the Web-console runtime pump processed the normal queue.
- Base: A user can still open `/gateway`, `/a2a`, or `/mcp/resources` for raw protocol inspection.
- Bad: The GUI fetch path calls `ensure_gateway_registry(...)` and rewrites `gateway.json` just because a browser opened the console.
- Bad: Re-embedding the full Web Console HTML/JS/CSS in `src/shuheng/app.py`, because that makes the backend module the browser source of truth again.
- Bad: The default GUI becomes a raw ledger viewer that prints `artifact://...`, `appr_...`, `task_...`, or schedule run ids as body text.
- Bad: Browser buttons directly approve, dispatch, delete, switch models, or write memory without reusing existing policy gates and ledgers.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `/gui` serves HTML, references `/gui/snapshot`, and does not include raw artifact URIs, approval ids, or task-id vocabulary in static HTML.
- Tests must assert `SHUHENG_WEB_GUI_INDEX` overrides the default standalone GUI lookup and `app.web_console_html()` returns the external file content.
- Tests must assert the fallback page names `SHUHENG_WEB_GUI_INDEX` and `SHUHENG_WEB_GUI_DIR` when no standalone file is available.
- Standalone GUI tests must assert `public/index.html` contains `/gui/snapshot`, `/gui/action`, and the current action schema; HTTP smoke should start both the Shuheng gateway and standalone GUI proxy and verify root HTML plus proxied snapshot/action error behavior.
- Tests must assert `/gui` contains real in-page action controls, does not use browser prompt dialogs for core actions, and advertises the supported governed action modes.
- Tests must assert `/gui` keeps the restrained collaboration shell structure and does not reintroduce card-grid classes such as `hero-card`, `agent-card`, or `agent-matrix`.
- Tests must assert `/gui` includes the Slack-like global rail, direct-agent section, session preview view, and client handlers for selecting agents and opening session refs.
- Tests must assert `/gui` keeps global rail activation scoped to real rail channel buttons, distinguishes same-view channels such as main home and `# main`, clears stale active subagent state when leaving agent views, and does not treat composer target selection as navigation.
- Tests must assert `/gui/snapshot` returns `shuheng.web_console.snapshot.v1`, `mode:"read_only"`, expected top-level sections, and populated overview metrics.
- Tests must assert `/gui/snapshot.sidebar` has the expected read-only shell sections and still excludes raw session paths or internal ids.
- Tests must assert `/gui` and `/gui/snapshot` do not change signatures for `gateway.json`, task ledger, approval registry, or artifact index.
- Tests must assert `/gui/action` rejects invalid schemas and unknown `ui_ref` values without mutating ledgers.
- Tests must assert `/gui/action` `session.open` accepts a valid sanitized session ref, returns cleaned title/messages, and rejects unknown session refs without mutating ledgers or exposing `model_responses_*.txt`.
- Tests must assert `/gui/action` schedule and approval actions mutate only through the governed registry/approval paths and return sanitized messages/snapshots.
- Tests must assert `/gui/action` schedule create/update can resolve a browser `target_agent_ref` into the server-side subagent routing field without exposing or accepting raw agent ids in the browser contract.
- Tests must assert `/gui/action` and `/gui/snapshot` do not expose raw task ids, approval ids, artifact URIs, filesystem session paths, or internal agent ids in default browser payloads.
- Tests must assert snapshot/default text does not leak raw artifact URIs or approval ids and does not include known schedule-run audit task ids.
- `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```text
GET /gui -> ensure_gateway_registry() -> rewrite gateway.json -> render raw task/artifact/approval ids
```

#### Correct

```text
GET /gui -> static local console
GET /gui/snapshot -> read ledgers -> sanitize display rows -> no writes, no approvals, no dispatch
POST /gui/action -> validate schema -> resolve ui_ref -> call existing governed backend function -> sanitized response + refreshed snapshot
```

#### Wrong

```python
def web_console_html() -> str:
    return """<!doctype html>
    <html>...thousands of lines of browser UI...</html>"""
```

#### Correct

```python
def web_console_html() -> str:
    from shuheng.web_console_static import web_console_html as load_web_console_html

    return load_web_console_html()
```

## Scenario: Web Console Helper Module Boundary

### 1. Scope / Trigger

- Trigger: Browser-facing Web Console helper constants, opaque refs, timestamp sorting, visible-text sanitization, status labels, metric row shaping, action payload shaping, or sanitized action-ref resolution are moved out of `src/shuheng/app.py`.
- Applies to: `src/shuheng/web_console.py`, compatibility aliases in `src/shuheng/app.py`, `/gui/snapshot` row builders, `/gui/action` schema checks, action payload/ref helpers, policy gates, and Web Console helper unit tests.
- Non-goal: This does not move `GatewayRequestHandler`, `/gui/action` mutation routing, snapshot construction, runtime pumping, state construction, scheduler/model/subagent mutation, standalone GUI loading, or storage-root ownership.

### 2. Signatures

- Lower-level helper module: `src/shuheng/web_console.py`.
- Compatibility aliases in `app.py`:
  - `WEB_CONSOLE_ACTION_REQUEST_SCHEMA`.
  - `WEB_CONSOLE_ACTION_RESPONSE_SCHEMA`.
  - `WEB_CONSOLE_REF_KINDS`.
  - `web_console_ref(kind, raw_id)`.
  - `web_console_timestamp(row)`.
  - `web_console_clean_visible(value, limit=320)`.
  - `web_console_status_label(status)`.
  - `web_console_metric(label, value, tone="")`.
  - `web_console_resolve_ref(refs, ui_ref, expected_kind)`.
  - `web_console_action_payload(payload)`.
  - `web_console_action_message(text)`.
  - `web_console_model_name_from_payload(action_data, refs)`.
  - `web_console_schedule_control_from_payload(action_data, refs)`.

### 3. Contracts

- `web_console.py` must not import `shuheng.app`, `.app`, `app`, `curses`, UI renderers, command handlers, `State`, `SubAgentRuntime`, `PanelItem`, `RenderLine`, `GatewayRequestHandler`, or runtime mutation helpers.
- `app.py` remains the compatibility facade and exposes the helper names as direct aliases or behavior-identical wrappers.
- `WEB_CONSOLE_ACTION_REQUEST_SCHEMA` remains `shuheng.web_console.action_request.v1`.
- `WEB_CONSOLE_ACTION_RESPONSE_SCHEMA` remains `shuheng.web_console.action_response.v1`.
- `WEB_CONSOLE_REF_KINDS` remains limited to `agent`, `approval`, `artifact`, `model`, `schedule`, `session`, and `task`.
- `web_console_ref(...)` returns an opaque stable `<kind>:<digest>` value for valid non-empty kinds/ids and `""` for unknown kinds or blank ids. It must not expose raw task ids, approval ids, artifact URIs, filesystem paths, model names, or agent ids.
- `web_console_clean_visible(...)` strips approval-only process markers and masks raw artifact refs, approval ids, approval query values, task ids, schedule run ids, schedule ids, internal agent ids, and temporary agent ids.
- Internal-ref masking must happen before and after inline-markdown stripping, because markdown emphasis rules can otherwise remove underscores from values such as `task_abc` or `schedrun_123` before the masks run.
- `web_console_timestamp(...)` prefers ISO `timestamp`, `updated_at`, `created_at`, then `finished_at`, with `mtime` as fallback.
- `web_console_metric(...)` returns a string-only display dict with `label`, `value`, and `tone`.
- `web_console_resolve_ref(...)` resolves only current server-side opaque refs and returns `(False, "", <Chinese user-facing error>)` for missing refs, unknown refs, or kind mismatch.
- `web_console_action_payload(...)` returns a shallow copy of the nested payload dict or `{}` for non-dict payloads.
- `web_console_action_message(...)` applies Web Console visible-text sanitization and falls back to `动作已执行。` for empty messages.
- `web_console_model_name_from_payload(...)` prefers explicit `model_name` / `model`, then resolves `model_ref` / `model_ui_ref` through `web_console_resolve_ref(...)`.
- `web_console_schedule_control_from_payload(...)` may resolve a browser `target_agent_ref`, `agent_ref`, or `agent_ui_ref` into `execution.routing.selected_agent` and `execution.routing.target_selector.agent_id`, but it must not persist schedules or dispatch work.

### 4. Validation & Error Matrix

- `web_console.py` imports `shuheng.app`, curses, TUI state, gateway handler, or runtime mutation helpers -> policy gate fails.
- App alias differs from module helper for the same input -> unit test or policy gate fails.
- Unknown `ui_ref` kind or blank raw id -> helper returns `""`.
- Sanitized visible text still contains `artifact://`, `appr_`, `approval=appr_`, `task_`, `schedrun_`, `sched_`, `agent-N`, or `tmp-agent-*` -> unit test or policy gate fails.
- Unknown status contains raw internal id vocabulary after label conversion -> unit test fails.
- Timestamp fields are absent or invalid -> helper returns numeric `mtime` fallback or `0.0`.
- Schedule action payload contains an agent `ui_ref` -> helper returns an `agent_task` execution control with server-resolved `selected_agent`.
- Schedule action payload contains a model/task/session ref where an agent ref is required -> helper returns a kind-mismatch error and no control payload.

### 5. Good/Base/Bad Cases

- Good: `/gui/snapshot` rows keep using `app.web_console_clean_visible(...)`, while the implementation is owned by `shuheng.web_console`.
- Good: `/gui/action` keeps schema validation in `app.py` but uses the schema constants from the helper module.
- Base: `web_console_ref_map(...)` stays in `app.py` because it reads ledgers, model config, current history rows, and loaded subagents.
- Base: `web_console_action_response(...)` stays in `app.py` because it may start the Web-console runtime pump and refresh snapshots.
- Base: `web_console_apply_action(...)` stays in `app.py` because it calls governed mutation functions for approvals, schedules, models, tasks, and subagents.
- Bad: `web_console.py` imports `State` so it can build snapshots.
- Bad: `web_console.py` calls `decide_approval(...)`, `start_subagent_task(...)`, or `process_ui_queue(...)`.

### 6. Tests Required

- Unit tests must assert helper behavior for stable opaque refs, invalid kinds, timestamp fallback, sanitization, status labels, metric shape, action payload/message shaping, model ref resolution, schedule target-agent ref mapping, and `app.py` wrapper parity.
- `scripts/check_policy_gates.py` must assert `web_console.py` has no reverse import into `app.py` and no curses, TUI state, rendering, gateway handler, or mutation-dispatch dependencies.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/web_console.py scripts/check_policy_gates.py tests/test_web_console.py` must pass.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py` and `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_web_console.py -p no:cacheprovider` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# web_console.py
from shuheng.app import State, decide_approval, process_ui_queue

def web_console_snapshot() -> dict:
    ...
```

#### Correct

```python
# web_console.py
WEB_CONSOLE_ACTION_REQUEST_SCHEMA = "shuheng.web_console.action_request.v1"

def web_console_ref(kind: str, raw_id: object) -> str:
    ...
```

## Scenario: Per-Agent Dedicated Skills

### 1. Scope / Trigger

- Trigger: The user wants one persistent subagent to have a dedicated skill without giving that skill to other subagents or the main Orchestrator.
- Applies to: `/agent skill ...`, `agent.create`, `agent.skill.update`, persistent and Secret subagent metadata, context pack construction, subagent prompt installation, home-page status cards, A2A agent cards, gateway capability registry, and read-only host tool records.
- Non-goal: This does not create a global skill registry UI, does not auto-install third-party skills, and does not let one subagent read another subagent's skill pack.

### 2. Signatures

- Persistent metadata field: `skill_refs: list[str]`.
- Commands:
  - `/agent skill <agent>`
  - `/agent skill list <agent>`
  - `/agent skill add <agent> <skill-ref ...>`
  - `/agent skill remove <agent> <skill-ref ...>`
  - `/agent skill set <agent> <skill-ref ...>`
  - `/agent skill clear <agent>`
  - `/agent skill <agent> add|remove|set|clear|list <skill-ref ...>`
- Control actions:
  - `agent.create` may include `skills`, `skill`, or `skill_refs`.
  - `agent.skill.update` / `agent.skills.update` map to internal `agent_skill` and must include `target` plus `op` and skill refs unless `op:"clear"`.
- Context-pack fields:
  - `skill_refs`
  - `skill_pack.schema_version == "subagent.skill_pack.v1"`

### 3. Contracts

- `skill_refs` belongs to exactly one `SubAgentRuntime`; it is persisted with that subagent's metadata and rehydrated on `load_subagents(...)` / `load_secret_subagents(...)`.
- Skill refs are normalized and deduplicated without an artificial count cap. Resolved refs load full local `SKILL.md` or markdown skill files from Shuheng/Codex/OMP/repo skill roots; unresolved refs stay visible as unresolved metadata but do not inject arbitrary content.
- `subagent_store.normalize_subagent_skill_refs(...)` owns only pure skill-ref value normalization and de-duplication. Skill root discovery, file resolution, skill-pack assembly, UI formatting, metadata writes, Secret storage, and prompt installation remain outside `subagent_store.py`.
- Only the target subagent's context pack includes its resolved `skill_pack` full body text. Other subagents and the main Orchestrator must show no body text from that skill unless they independently own the same ref.
- `format_context_pack_for_prompt(...)` must label the section as `Dedicated skills for this agent only` so runtime agents know the skill is scoped, not global.
- `subagent_prompt_block(...)`, subagent home status cards, `/agent info`, A2A cards, gateway records, and `shuheng_query`/typed host tool agent records must expose bounded skill refs/summaries for routing and inspection.
- `agent_match` may score a subagent by role tools plus dedicated skill refs/display names so a task requiring a target-only skill can reuse the correct existing agent.
- Updating dedicated skills should reinstall the subagent system prompt when the subagent runtime is already loaded.
- Skill support must not weaken existing role write policy, approval gates, Secret Vault isolation, or single-writer enforcement.

### 4. Validation & Error Matrix

- `/agent skill <missing>` -> user-visible `找不到子 agent`.
- `/agent skill add <agent>` without refs -> usage message, no metadata change.
- `agent.skill.update` without refs and without `op:"clear"` -> user-visible missing skill-ref result.
- Unresolved skill ref -> kept in `skill_refs`, displayed as missing/unresolved, and omitted from injected body text.
- Target agent has `custom-sop`; another agent has no skill refs -> target context prompt contains the custom SOP marker, other context prompt does not.
- Reload after save -> target still has `skill_refs`, other agent still does not.
- Secret Vault subagent metadata -> `skill_refs` is encrypted with the subagent metadata, not written to normal subagent directories.
- Target agent has more than 16 skill refs and a resolved skill body longer than 3500 characters -> all refs persist and the full body remains in the target context pack.

### 5. Good/Base/Bad Cases

- Good: `/agent skill add agent-research custom-sop` persists `["custom-sop"]`; the target agent home shows `专属技能 custom-sop`, and only that target's context pack contains the `custom-sop` instructions.
- Good: `agent.create` with `lifecycle:"persistent"` and `skills:["custom-sop"]` creates a persistent subagent with that dedicated skill from the first turn.
- Good: `agent.skill.update` with `op:"remove"` removes the skill from only the target agent.
- Base: An unresolved ref remains visible for operator diagnosis but injects no body text into prompts.
- Bad: Putting the skill body in the main Orchestrator context pack or every subagent prompt.
- Bad: Treating dedicated skill refs as permission grants that bypass role tools, policy approvals, or single-writer locks.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `/agent skill` command paths update only the selected subagent and persist through reload.
- Tests must assert target context packs and direct-chat prompts include a unique skill marker while another subagent's context packs and direct-chat prompts do not.
- Tests must assert home pages, `/agent info`/agent records, A2A cards, gateway capability registry, and `agent_match` expose/use the target skill refs without leaking skill body text to other agents.
- Tests must assert `agent.create` accepts `skills`/`skill_refs`, and `agent.skill.update` removes or updates the target agent's skills.
- Tests must assert skill-ref normalization is owned by `subagent_store.py`, app alias parity holds, and `subagent_store.py` does not resolve skill files or import runtime/UI/Secret/history owners.
- Tests must assert dedicated skill registration is not capped at 16, all resolved skill pack entries are included, and skill body text is not truncated at 3500 characters.
- Tests must keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
custom-sop installed globally -> every subagent sees custom SOP body text
```

#### Correct

```text
/agent skill add agent-research custom-sop -> only agent-research context_pack.skill_pack includes custom-sop
```

## Scenario: Declarative User Plugins

### 1. Scope / Trigger

- Trigger: Users need local plugin packages that can contribute reusable subagent skills, agent templates, workflow metadata, and read-only registry information without granting executable plugin code.
- Applies to: local `plugin.json` discovery, `plugin://<plugin-id>/skills/<skill-id>` skill refs, `/plugins`, the Plugins harness panel, `/plugin info <plugin-id>`, `/plugin template <plugin-id>/<template-id>`, `/plugin create <plugin-id>/<template-id> [agent-name]`, `/agent plugin ...`, subagent `skill_refs`, context pack construction, subagent prompt installation, policy gates, and registry/query metadata.
- Non-goal: This does not add remote marketplace install, arbitrary Python/JS execution, plugin-native tools, hidden side effects, cross-machine sync, or a replacement for the existing per-agent dedicated skill system.

### 2. Signatures

- Plugin root: `SHUHENG_PLUGINS_DIR == os.path.join(SHUHENG_HOME, "plugins")`.
- Manifest file: `<plugin-root>/<plugin-id>/plugin.json`.
- Manifest schema version: `shuheng.plugin.v1`.
- Skill ref shape: `plugin://<plugin-id>/skills/<skill-id>`.
- Agent template ref shape: `plugin://<plugin-id>/agents/<template-id>`, with `<plugin-id>/<template-id>` accepted as a TUI shorthand.
- Public TUI commands:
  - `/plugins` opens the Plugins panel in the interactive curses Enter path.
  - `/plugin info <plugin-id>`
  - `/plugin template <plugin-id>/<template-id>`
  - `/plugin create <plugin-id>/<template-id> [agent-name]`
  - `/agent plugin add <agent> <plugin-skill-ref ...>`
  - `/agent plugin remove <agent> <plugin-skill-ref ...>`
  - `/agent plugin list <agent>`
  - `/agent plugin <agent> add|remove|set|clear|list <plugin-skill-ref ...>`
- Registry owner module: `plugins.py`.
- Orchestrator wrappers: `user_plugin_roots()`, `user_plugin_registry(...)`, `handle_plugin_command(...)`, `subagent_plugin_command_message(...)`, and `create_subagent_from_plugin_template(...)` in `app.py`.
- Panel wrapper: `plugin_panel_items()` returns read-only `PanelItem` rows for `open_harness_panel(..., "plugins")`.

### 3. Contracts

- MVP plugins are declarative local packages only. Reading `plugin.json` and manifest-declared local files is allowed; executing plugin code or registering plugin tools is forbidden in this scenario.
- `plugins.py` owns pure manifest discovery, validation, stable ref parsing, plugin formatting, and manifest-declared path resolution. It must not import `app.py`, curses, `State`, `SubAgentRuntime`, Secret Vault, Web Console, dashboard, runtime dispatch, GenericAgent handlers, approval queues, ledgers, or provider adapters.
- Plugin skills are stored as ordinary subagent `skill_refs` using `plugin://<plugin-id>/skills/<skill-id>`. There is no separate `plugin_refs` persistence field in this MVP.
- Plugin skill file resolution must go through the manifest. A `plugin://...` ref must not map directly to arbitrary filesystem paths or raw plugin directory guesses.
- Manifest-declared skill and workflow paths must be relative paths that remain inside the plugin root. Absolute paths, `~` paths, and `..` escapes are validation issues and must not resolve.
- Missing or invalid plugin refs stay visible in metadata and `/agent plugin list`, but they inject no body text into prompts.
- Only the target subagent's context pack may include resolved plugin skill body text. The main Orchestrator and unrelated subagents must not receive plugin skill bodies unless they independently own the same `skill_refs`.
- `/agent plugin ...` is an alias over the existing dedicated skill mechanism. It must preserve non-plugin dedicated skills when clearing plugin skills.
- `/plugin create ...` must create subagents through the existing `create_subagent(...)` path and then set `skill_refs` through `set_subagent_skill_refs(...)`; it must not bypass role normalization, persistence selection, Secret Vault metadata handling, prompt installation, or policy gates.
- Plugin manifest `permissions` are descriptive metadata in this scenario. They must not override role write policy, approval gates, Secret Vault isolation, single-writer locks, artifact provenance, task ledgers, or runtime dispatch permissions.
- The app may cache plugin registry discovery by plugin-root/manifest fingerprint. Cache invalidation must not require a TUI repaint and must not read plugin skill body text globally.
- The interactive `/plugins` path must use the existing harness panel browser. Panel rows may show plugin metadata, manifest paths, declared contributions, command hints, and validation issues, but must not show plugin skill body text.
- Non-interactive `/plugins` handling may continue to return bounded text via `format_plugin_list(...)`.
- Secret Vault unlocked mode treats `/plugins` as a normal harness panel and blocks it until `/lock`, matching normal history/harness isolation.

### 4. Validation & Error Matrix

- Missing plugin root -> `/plugins` reports no plugins, no crash.
- Invalid JSON manifest -> registry issue, plugin not loaded.
- Wrong `schema_version` -> registry issue, plugin not loaded.
- Invalid plugin id or contribution id -> registry issue, contribution not loaded.
- Duplicate plugin id -> first discovered plugin wins, later duplicate is reported as ignored.
- Skill path outside plugin root -> registry issue, `plugin_skill_file_for_ref(...) == ""`, no prompt body injection.
- Missing skill file -> registry issue, ref remains visible, no prompt body injection.
- `/plugin info <missing>` -> user-visible missing plugin message.
- `/plugins` in the curses input path -> opens `open_harness_panel(..., "plugins")`.
- `/plugins` with no local plugin packages -> shows a useful empty-state panel row with plugin roots and expected package shape.
- `/plugin create <missing>` -> user-visible missing template message, no subagent created.
- `/agent plugin add <agent>` without plugin refs -> usage message, no metadata change.
- `/agent plugin clear <agent>` -> removes only `plugin://...` refs and preserves ordinary dedicated skill refs.
- Plugin permissions request `write_policy:"approved_only"` while template role is `researcher` -> resulting subagent still has researcher role policy; plugin permissions do not grant writes.

### 5. Good/Base/Bad Cases

- Good: `~/.shuheng/plugins/research-pack/plugin.json` declares `source-review`, `/agent plugin add agent-research research-pack/source-review` persists `["plugin://research-pack/skills/source-review"]`, and only `agent-research` context packs contain the plugin SOP body.
- Good: `/plugin create research-pack/evidence-researcher Evidence Agent` creates a normal subagent through the Orchestrator path with role normalization and plugin skill refs attached.
- Base: `/plugins` lists valid plugins plus bounded validation issues for broken local packages.
- Base: A manifest may declare workflows as metadata before workflow execution is implemented.
- Bad: Scanning a plugin directory and loading every `SKILL.md` without manifest declaration.
- Bad: Injecting all plugin README/SKILL body text into the main Orchestrator as global context.
- Bad: Treating plugin `permissions` as runtime authorization that bypasses role policy, approval requirements, or Secret Vault isolation.

### 6. Tests Required

- `tests/test_plugins.py` must assert manifest discovery, stable ref parsing, path traversal rejection, missing-file validation, agent-template normalization, plugin list/info formatting, and default plugin root behavior.
- `tests/test_subagent_store.py` must assert `normalize_subagent_skill_refs(...)` preserves `plugin://...` refs while keeping `skill://...` compatibility.
- `scripts/check_policy_gates.py` must assert `plugins.py` is a pure registry module and does not import app/runtime/UI/governance owners.
- `scripts/check_policy_gates.py` must create a temp local plugin, attach `plugin://research-pack/skills/source-review` to one subagent, and prove the plugin marker appears only in that target context pack and direct-chat prompt.
- `scripts/check_policy_gates.py` must assert `/plugins`, `/plugin info`, `/plugin template`, `/plugin create`, and `/agent plugin add/remove/list/clear` work through existing governed paths.
- `scripts/check_policy_gates.py` must assert the Plugins panel route is registered in the Enter path and `plugin_panel_items(...)` exposes plugin metadata and validation issue rows without plugin skill body text.
- `scripts/check_policy_gates.py` must assert a manifest-declared outside path does not resolve or inject.
- `scripts/check_policy_gates.py` must assert plugin-declared permissions do not change role write policy.
- Keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, targeted pytest, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
Load every plugin file globally -> main Orchestrator and every subagent see all plugin SOP bodies
```

#### Correct

```text
/agent plugin add agent-research research-pack/source-review -> only agent-research context_pack.skill_pack includes plugin://research-pack/skills/source-review
```

## Scenario: Declarative Workflow Registry And Dry-Run

### 1. Scope / Trigger

- Trigger: Users need local/plugin workflows to be discoverable, inspectable, and dry-runnable before Shuheng adds workflow execution.
- Applies to: `plugin://<plugin-id>/workflows/<workflow-id>` refs, manifest-declared workflow files, `workflows.py`, `/workflows`, `/workflow info <ref>`, `/workflow dry-run <ref>`, the Workflows harness panel, plugin registry cache refresh, Secret Vault command isolation, and policy gates.
- Non-goal: This does not run workflow steps, dispatch subagents, create approvals, write workflow run ledgers, execute tools, run plugin code, schedule workflows, or expose remote A2A/MCP workflow services.

### 2. Signatures

- Workflow ref shape: `plugin://<plugin-id>/workflows/<workflow-id>`.
- Accepted shorthand in TUI commands: `<plugin-id>/<workflow-id>` and `<plugin-id>/workflows/<workflow-id>`.
- Workflow definition schema version: `shuheng.workflow.v1`.
- MVP definition body: JSON object, either as the whole file body or as a fenced JSON object in a Markdown file.
- Supported MVP step types: `prompt`, `agent_task`, `approval`, `artifact_summary`, `pause`, `notify`, and `condition`.
- Public commands:
  - `/workflows`
  - `/workflow info <plugin-id>/<workflow-id>`
  - `/workflow dry-run <plugin-id>/<workflow-id>`
- Registry owner modules:
  - `plugins.py` owns workflow ref parsing and manifest-declared workflow file resolution.
  - `workflows.py` owns pure workflow definition parsing, validation, and bounded formatting.
  - `app.py` owns TUI command routing and panel rendering only.

### 3. Contracts

- Workflow definitions are declarative data only. They must not execute Python, JavaScript, shell commands, plugin-native code, tools, model calls, or subagent tasks during registry load, info rendering, panel rendering, or dry-run.
- Workflow files must be loaded only through manifest-declared `PluginWorkflow` records. App-level code must not guess filesystem paths from a workflow ref.
- `workflows.py` must not import `app.py`, curses, `State`, `SubAgentRuntime`, Secret Vault, Web Console, dashboard, runtime dispatch, GenericAgent handlers, approval queues, ledgers, provider adapters, or subprocess.
- Dry-run output is an execution plan preview. It may show inputs, permissions metadata, ordered steps, dependencies, target agent refs, prompt strings, and validation issues, but must explicitly state that no execution occurred.
- `/workflows` uses the existing harness panel browser and read-only `PanelItem` rows.
- `/workflow info` and `/workflow dry-run` may return text through normal command handling, but must not mutate runtime state beyond adding a system message.
- Workflow `permissions` are metadata only in this scenario. They must not alter role write policy, approval gates, Secret Vault isolation, single-writer locks, artifact provenance, task ledgers, or runtime dispatch permissions.
- Secret Vault unlocked mode treats `/workflows` and `/workflow` as normal harness commands and blocks them until `/lock`.

### 4. Validation & Error Matrix

- Missing plugin root -> `/workflows` reports no workflows, no crash.
- Missing workflow file -> visible workflow validation issue, no execution.
- Non-JSON workflow body without fenced JSON -> visible workflow validation issue, no execution.
- Wrong `schema_version` -> visible validation issue; dry-run still says no execution.
- Workflow id missing or not filesystem-safe -> validation issue.
- Workflow id differs from manifest contribution id -> validation issue.
- Duplicate input id -> validation issue.
- Duplicate step id -> validation issue.
- Unsupported step type -> validation issue.
- Step dependency references a missing step -> validation issue.
- `/workflow info <missing>` -> visible missing workflow message.
- `/workflow dry-run <valid>` -> ordered plan preview plus `No execution occurred.`

### 5. Good/Base/Bad Cases

- Good: `research-pack` declares `compare-sources`, `/workflow dry-run research-pack/compare-sources` renders inputs and ordered steps without starting a subagent or writing a ledger.
- Good: `/workflows` opens a read-only panel that surfaces workflow metadata and validation issues.
- Base: Workflow files may be Markdown files that contain a fenced JSON definition for readability.
- Base: A workflow may include future execution metadata such as `permissions`, `agent`, `depends_on`, and prompt text before the runner exists.
- Bad: `/workflow dry-run` calls `start_subagent_task(...)`.
- Bad: The app maps `plugin://research-pack/workflows/x` directly to `~/.shuheng/plugins/research-pack/workflows/x.json` without consulting the manifest.
- Bad: Workflow `permissions` grants write access or bypasses approvals.
- Bad: Importing runtime dispatch, governance, ledger, or Secret Vault owners into `workflows.py`.

### 6. Tests Required

- `tests/test_workflows.py` must assert valid JSON workflow parsing, fenced JSON parsing, invalid body errors, schema validation, duplicate id validation, unsupported step validation, dependency validation, and dry-run wording.
- `tests/test_plugins.py` must assert workflow ref construction/parsing and shorthand parsing.
- `scripts/check_policy_gates.py` must assert `/workflows` and `/workflow` are visible commands, Secret Vault blocks both normal commands, the Workflows panel route exists, and dry-run does not create subagents or call runtime dispatch/ledger/governance owners.
- `scripts/check_policy_gates.py` must assert `workflows.py` stays pure and does not import app/runtime/UI/governance owners.
- Keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, targeted pytest, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow dry-run research-pack/compare-sources -> dispatches plugin://research-pack/agents/evidence-researcher
```

#### Correct

```text
/workflow dry-run research-pack/compare-sources -> renders plan preview and says "No execution occurred."
```

## Scenario: Built-In Example Workflow Pack V1

### 1. Scope / Trigger

- Trigger: A fresh Shuheng install should expose at least one useful workflow without requiring the user to hand-create a plugin package.
- Applies to: package-data plugin roots, `src/shuheng/builtin_plugins/**`, `plugins.py`, `app.user_plugin_roots()`, `/plugins`, `/workflows`, `/workflow info <ref>`, `/workflow dry-run <ref>`, `/workflow run <ref>`, release hygiene, wheel smoke, `tests/test_plugins.py`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: This does not add executable plugin code, remote marketplace install, starter-file copying into user plugin roots, workflow daemon ownership, hidden model/tool/shell calls, subagent dispatch, or approval/task/artifact side effects from the built-in example.

### 2. Signatures

- Built-in package root helper: `plugins.builtin_plugin_root()`.
- App discovery wrapper: `app.user_plugin_roots()` returns the user plugin root plus the built-in package root.
- Built-in plugin root: `src/shuheng/builtin_plugins`.
- Built-in plugin id: `shuheng-examples`.
- Built-in workflow ref: `plugin://shuheng-examples/workflows/daily-briefing`.
- Distribution manifest entries:
  - `MANIFEST.in` includes `recursive-include src/shuheng/builtin_plugins *.json`.
  - `pyproject.toml` package data includes the built-in plugin manifest and workflow JSON.

### 3. Contracts

- Built-in workflows are read-only package data. Shuheng must not copy, mutate, or scaffold them into `SHUHENG_PLUGINS_DIR` during discovery, info, dry-run, run, panel rendering, package smoke, or policy gates.
- Built-in workflows must be loaded only through the normal `shuheng.plugin.v1` manifest registry and `PluginWorkflow` records. App code must not special-case a built-in workflow ref into a guessed filesystem path.
- User plugin discovery remains unchanged: custom plugins under `SHUHENG_PLUGINS_DIR` still load through the same registry, and user-created workflow saves still write only under `SHUHENG_PLUGINS_DIR`.
- The built-in example workflow must stay safe-only. Running it may append normal planned and completed `shuheng.workflow_run.v1` rows, but it must not create subagents, task rows, progress rows, approval rows, artifact index rows, plugin-code calls, shell calls, tool calls, or provider calls.
- Empty user plugin roots should still make `/plugins`, `/workflows`, `/workflow info shuheng-examples/daily-briefing`, `/workflow dry-run shuheng-examples/daily-briefing`, and `/workflow run shuheng-examples/daily-briefing` useful.
- Package builds must include the built-in plugin manifest and workflow JSON in both sdist and wheel artifacts.

### 4. Validation & Error Matrix

- Empty `SHUHENG_PLUGINS_DIR` -> registry includes `shuheng-examples` from the built-in package root.
- Empty `SHUHENG_PLUGINS_DIR` -> `/plugins` and the Plugins panel show the built-in plugin instead of a no-plugin empty state.
- `/workflow dry-run shuheng-examples/daily-briefing` -> plan preview includes `Daily Briefing`, ordered safe steps, and `No execution occurred.`
- `/workflow run shuheng-examples/daily-briefing` -> exactly normal planned and completed workflow rows are appended, with default inputs applied.
- `/workflow run shuheng-examples/daily-briefing` -> task/progress/approval/artifact ledgers stay unchanged.
- Built-in discovery -> `SHUHENG_PLUGINS_DIR/shuheng-examples` is not created.
- Distribution build omits built-in JSON files -> release hygiene or wheel smoke fails.

### 5. Good/Base/Bad Cases

- Good: A clean install can run `/workflow dry-run shuheng-examples/daily-briefing` and see a safe plan before creating any local plugin.
- Good: A user later runs `/workflow save-last my-pack/my-flow`; the generated files are written under the user plugin root, not into `src/shuheng/builtin_plugins`.
- Base: The built-in root is appended by the app-level discovery wrapper. Low-level `plugins.plugin_roots()` remains compatible unless `include_builtin=True` is requested.
- Bad: Writing starter plugin files into `~/.shuheng/plugins/shuheng-examples` on first launch.
- Bad: Hard-coding `daily-briefing.json` lookup in app command handlers instead of resolving the workflow through the plugin manifest.
- Bad: The built-in workflow dispatches an `agent_task`, queues an approval, writes an artifact, calls a provider, or executes plugin code.

### 6. Tests Required

- `tests/test_plugins.py` must assert `plugins.builtin_plugin_root()`, `plugin_roots(include_builtin=True)`, and the built-in example workflow pack load through manifest-backed discovery.
- `tests/test_workflows.py` must assert the built-in example is available without user plugins, info/dry-run works, running it writes only workflow-run rows, and no `SHUHENG_PLUGINS_DIR/shuheng-examples` directory is created.
- `scripts/check_policy_gates.py` must assert app discovery includes the built-in root, the built-in workflow loads through `user_plugin_registry(force=True)`, the Plugins panel shows the built-in plugin for an otherwise empty user root, and safe built-in runs do not write task/progress/approval/artifact ledgers.
- `scripts/check_release_hygiene.py` and `scripts/wheel_smoke.py` must assert the built-in plugin manifest and workflow JSON are included in package distributions.
- Keep targeted compile/Ruff, `tests/test_plugins.py`, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, release hygiene, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow run shuheng-examples/daily-briefing -> app writes ~/.shuheng/plugins/shuheng-examples and dispatches a hidden agent task
```

#### Correct

```text
/workflow run shuheng-examples/daily-briefing -> manifest-backed built-in package data -> planned/completed workflow rows only
```

## Scenario: Workflow DAG Validation V1

### 1. Scope / Trigger

- Trigger: A manifest-backed workflow definition declares `depends_on` / `after` relationships that are not a valid directed acyclic graph.
- Applies to: `workflows._parse_steps(...)`, workflow definition loading, `/workflow info <ref>`, `/workflow dry-run <ref>`, `/workflow run <ref>`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: This does not topologically reorder steps, add parallel fan-out/fan-in execution, add retries, timeout, cancellation, scheduling, checkpoint/replay, artifact hydration, plugin code execution, model/tool calls, or A2A/MCP workflow service exposure.

### 2. Signatures

- Dependency fields accepted from workflow JSON:
  - `depends_on`
  - `after`
- Pure helper ownership:
  - `workflows._workflow_dependency_issues(steps, workflow_ref, path) -> list[WorkflowIssue]`
- Error message shapes:
  - `steps[<step_id>] depends on itself`
  - `steps[<step_id>] duplicates dependency <dependency_id>`
  - `steps[<step_id>] depends on missing step <dependency_id>`
  - `workflow dependency cycle detected: <step_id> -> ... -> <step_id>`

### 3. Contracts

- Workflow definitions must be DAG-valid before any run ledger row can be created.
- A step must not depend on itself.
- A step must not list the same dependency id more than once.
- A step must not depend on a missing step.
- The full dependency graph must be acyclic, including direct cycles and transitive cycles.
- Valid fan-in dependency shapes remain accepted. Runner v0 may still execute sequentially in file order until a later fan-out/fan-in executor exists.
- DAG validation belongs to the pure workflow definition parser. It must not read workflow run ledgers, task ledgers, artifacts, files beyond the manifest-declared workflow file, environment variables, Secret Vault, model outputs, or tools.
- `workflows.py` remains pure and must not import app/runtime/UI/governance owners, append JSONL rows, dispatch subagents, queue approvals, call providers/tools, or run subprocesses.

### 4. Validation & Error Matrix

- `{"id":"plan","depends_on":["plan"]}` -> validation issue `steps[plan] depends on itself`, no workflow run row on `/workflow run`.
- `plan depends_on ["review"]` and `review depends_on ["plan"]` -> validation issue `workflow dependency cycle detected: plan -> review -> plan`, no workflow run row on `/workflow run`.
- `review depends_on ["collect","collect"]` -> validation issue `steps[review] duplicates dependency collect`.
- `review depends_on ["missing"]` -> existing missing dependency validation remains intact.
- `collect_a`, `collect_b`, `review depends_on ["collect_a","collect_b"]` -> valid workflow definition with no DAG validation issues.
- Invalid cyclic workflow shown in `/workflow dry-run` -> dry-run still reports `No execution occurred.` and lists validation issues.

### 5. Good/Base/Bad Cases

- Good: A generated or hand-written workflow with a dependency cycle is rejected before any planned workflow run row is appended.
- Good: The Workflows panel can surface an invalid cyclic workflow as a validation warning while valid workflows remain runnable.
- Good: A future fan-in workflow can already declare multiple dependencies and pass validation, even if runner v0 executes sequentially.
- Base: Step order remains author-defined in v1; DAG validation only rejects invalid graph shapes.
- Bad: Runner v0 discovers a cycle only after appending a planned run row.
- Bad: App command code duplicates a second dependency graph validator instead of using the workflow loader result.
- Bad: `workflows.py` imports app or ledger owners to check historical workflow runs while validating a definition.

### 6. Tests Required

- `tests/test_workflows.py` must assert self-dependency, duplicate dependency, direct or transitive cycle, missing dependency preservation, valid fan-in acceptance, and dry-run no-execution wording.
- `scripts/check_policy_gates.py` must assert an invalid cyclic workflow is rejected by `/workflow run` with no workflow run row and no task/progress/approval/artifact ledger writes.
- `scripts/check_policy_gates.py` must assert the DAG validation helper remains owned by `workflows.py` and `workflows.py` stays side-effect-free.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow run research-pack/cyclic-flow -> appends planned row, then runner gets stuck because plan depends on review and review depends on plan
```

#### Correct

```text
/workflow run research-pack/cyclic-flow -> loader reports dependency cycle, app shows rejection, no workflow run row is appended
```

## Scenario: Workflow AI Draft Generation

### 1. Scope / Trigger

- Trigger: Users want Shuheng to turn a natural-language workflow goal into a reusable declarative plugin workflow without hand-writing JSON.
- Applies to: `/workflow generate <goal>`, model-output workflow JSON parsing, latest workflow draft state, `/workflow save-last <plugin-id>/<workflow-id>`, user plugin manifests, plugin registry refresh, `workflows.py`, `app.py`, `tests/test_workflows.py`, and policy gates.
- Non-goal: Generation and save do not run workflows, dispatch subagents, create approvals, write workflow run rows, mutate task/progress/artifact ledgers, call tools, execute plugin code, publish plugins, schedule workflows, touch Secret Vault, or expose remote A2A/MCP workflow services.

### 2. Signatures

- Public commands:
  - `/workflow generate <goal>`
  - `/workflow save-last <plugin-id>/<workflow-id>`
- Generated workflow schema version: `shuheng.workflow.v1`.
- Saved plugin manifest schema version: `shuheng.plugin.v1`.
- Draft source tag prefix: `workflow_generate`.
- Pure helper ownership:
  - `workflows.workflow_draft_result_from_text(...)`
  - `workflows.workflow_draft_load_result_from_text(...)`
  - `workflows.workflow_load_result_from_payload(...)`
- App ownership:
  - `app.workflow_generation_prompt(...)`
  - `app.handle_completed_workflow_generation(...)`
  - `app.save_latest_workflow_draft(...)`

### 3. Contracts

- `/workflow generate <goal>` starts a normal main-agent task with a bounded prompt that asks for exactly one declarative workflow JSON object.
- A completed generation task must parse raw model text through the pure workflow parser and store only the latest valid draft payload in `State`.
- Invalid generation output must be reported visibly and must not overwrite the previous valid draft.
- Generation output must not execute TUI controls, interaction payloads, workflow steps, subagent tasks, tools, approval requests, plugin code, or shell/Python/JavaScript.
- `/workflow save-last <plugin-id>/<workflow-id>` must write the latest valid draft into `SHUHENG_PLUGINS_DIR/<plugin-id>/workflows/<workflow-id>.json` and create or update `<plugin-id>/plugin.json`.
- The save target controls the saved plugin id and workflow id. The saved workflow payload id must match `<workflow-id>`.
- Saving must preserve unrelated manifest metadata where possible and only add or update the target `contributes.workflows` entry.
- Saved workflows must immediately load through the normal manifest-backed plugin registry and become visible to `/workflows`, `/workflow info`, `/workflow dry-run`, and `/workflow run`.
- `workflows.py` remains pure. It may parse and validate model text/payloads, but must not import `app.py`, curses, runtime dispatch, approval queues, task/progress ledgers, artifacts, provider adapters, governance owners, Secret Vault, or subprocess.
- `app.py` remains the Orchestrator owner for model calls, state mutation, user-visible messages, file writes, and registry refresh.

### 4. Validation & Error Matrix

- Blank generation goal -> usage message, no model task.
- Valid JSON workflow draft -> latest draft payload stored, visible preview shown, no save or run.
- Fenced JSON workflow draft -> accepted through the same parser used by workflow files.
- Invalid JSON or non-object output -> visible rejection, previous valid draft remains unchanged.
- Wrong schema, unsafe id, duplicate step/input id, unsupported step type, or missing dependency -> visible validation rejection, previous valid draft remains unchanged.
- Save with no valid latest draft -> visible no-op, no files written.
- Save with unsafe plugin id or workflow id -> visible rejection, no files written.
- Save with valid draft and safe target -> plugin manifest and workflow file written, registry refreshes, normal workflow load succeeds.
- Generate or save attempts to include TUI controls or interaction payloads -> controls are ignored on the workflow generation source path.
- Generate/save must leave workflow runs, task ledger, progress ledger, approvals, and artifact index unchanged.

### 5. Good/Base/Bad Cases

- Good: `/workflow generate "research and summarize sources"` stores a validated draft and tells the user to run `/workflow save-last research-pack/source-summary`.
- Good: `/workflow save-last research-pack/source-summary` writes `plugin.json` plus `workflows/source-summary.json`, then `/workflow dry-run research-pack/source-summary` shows `No execution occurred.`
- Base: A generated `agent_task` step may target an existing subagent name or plugin agent template ref; actual dispatch happens only later through `/workflow run`.
- Base: The save command may update an existing manifest workflow entry for the same workflow id.
- Bad: `/workflow generate ...` immediately calls `/workflow run` or `start_subagent_task_structured(...)`.
- Bad: Saving creates a hidden draft registry outside the plugin manifest model.
- Bad: Model output containing a TUI control block is executed during workflow generation.

### 6. Tests Required

- `tests/test_workflows.py` must assert valid generation stores a draft, invalid generation does not overwrite a valid draft, save-last writes manifest-backed plugin files, saved workflows load and dry-run, no-draft save is no-op, unsafe ids are rejected, and generate/save do not write workflow/task/progress/approval/artifact ledgers.
- `scripts/check_policy_gates.py` must assert `/workflow generate` and `/workflow save-last` exist, generation uses a `workflow_generate` source, saved workflows are visible through the registry, and generate/save leave execution ledgers unchanged.
- Policy gates must keep asserting `workflows.py` has no app/runtime/UI/governance imports.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow generate "compare sources" -> model returns JSON -> app dispatches agent_task and appends workflow run rows
```

#### Correct

```text
/workflow generate "compare sources" -> validated draft in State -> /workflow save-last research-pack/compare-sources -> normal manifest-backed workflow file
```

## Scenario: Workflow Generated Draft Save-And-Run

### 1. Scope / Trigger

- Trigger: Users want a shorter explicit path from a validated AI workflow draft to a governed workflow run.
- Applies to: `/workflow run-last <plugin-id>/<workflow-id>`, latest workflow draft state, user plugin manifests, plugin registry refresh, `workflow_runs.jsonl`, `app.save_latest_workflow_draft_result(...)`, `app.run_latest_workflow_draft(...)`, `app.create_workflow_run_v0(...)`, `tests/test_workflows.py`, and policy gates.
- Non-goal: This does not auto-run at `/workflow generate` completion, run in-memory drafts, create a hidden workflow executor, bypass manifest-backed workflow files, duplicate runner/bridge logic, evaluate free-form condition expressions, schedule workflows, run plugin code directly, or expose A2A/MCP workflow services.

### 2. Signatures

- Public command:
  - `/workflow run-last <plugin-id>/<workflow-id>`
- Save helper:
  - `app.save_latest_workflow_draft_result(state, ref) -> tuple[str, str]`
- Run helper:
  - `app.run_latest_workflow_draft(state, ref) -> str`
- Existing governed runner reused after save:
  - `app.create_workflow_run_v0(result, state=state, source_command=...)`

### 3. Contracts

- `/workflow run-last <plugin-id>/<workflow-id>` must first save the latest valid draft as a normal manifest-backed plugin workflow.
- The save target controls the plugin id and workflow id; unsafe ids must be rejected before any file write or run.
- If save fails, no workflow run row, task/progress row, approval row, artifact row, or subagent dispatch may occur.
- After save succeeds, the command must load the saved workflow through `workflow_load_result_for_ref(...)` and `user_plugin_registry(force=True)`.
- Running must call `create_workflow_run_v0(...)`; it must not build workflow rows, dispatch subagents, queue approvals, or continue runs through a second implementation.
- Approval and agent-task side effects, if any, remain owned by the existing Workflow Approval Bridge and Workflow Agent Task Bridge.
- Command output must show both save and run sections so users can audit the conversion and execution start.
- `/workflow generate <goal>` completion remains non-executing; only a later explicit `/workflow run-last ...` may save and run the latest draft.
- `workflows.py` remains pure and does not gain app/runtime/UI/governance imports for this command.

### 4. Validation & Error Matrix

- No latest valid draft -> visible no-op, no files, no ledgers.
- Unsafe plugin id or workflow id -> visible rejection, no files, no ledgers.
- Latest draft fails validation against the target id -> visible rejection, no run.
- Saved workflow fails registry validation -> visible save failure, no run.
- Safe-only valid draft -> workflow file + manifest saved, then planned + completed workflow run rows appended.
- Draft with `approval` blocker -> workflow file + manifest saved, planned + waiting-approval workflow rows appended, and exactly one normal approval row created by the approval bridge.
- Draft with `agent_task` blocker -> workflow file + manifest saved, planned + waiting-task workflow rows appended, and exactly one governed subagent task dispatched by the agent-task bridge.
- Draft with unsupported/string `condition` blocker -> workflow file + manifest saved, planned + blocked workflow rows appended, no side-effect ledgers except workflow runs. Drafts with condition v1 predicates follow the Workflow Inputs and Condition V1 contract below.

### 5. Good/Base/Bad Cases

- Good: `/workflow run-last research-pack/source-summary` writes `workflows/source-summary.json`, then `/workflow runs` shows the resulting run id.
- Good: An approval generated by run-last carries a `source_command` pointing to `/workflow run-last ...`.
- Base: Users may still prefer `/workflow save-last ...` followed by `/workflow dry-run ...` and `/workflow run ...` for a manual inspection pause.
- Bad: The generation callback immediately starts the workflow after parsing model output.
- Bad: `run-last` builds rows directly and skips `create_workflow_run_v0(...)`.
- Bad: `run-last` runs from `State.workflow_draft_payload` without writing and loading a manifest-backed plugin workflow first.

### 6. Tests Required

- `tests/test_workflows.py` must assert `run-last` saves and runs safe generated drafts, uses the existing approval bridge for approval drafts, reports no-op for no draft and unsafe refs, and does not write non-run ledgers unless the existing runner/bridges own those side effects.
- `scripts/check_policy_gates.py` must assert the command exists, save-before-run behavior produces normal workflow rows, no-draft is a no-op, and `workflows.py` remains pure.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow run-last research-pack/source-summary -> builds run rows directly from State.workflow_draft_payload
```

#### Correct

```text
/workflow run-last research-pack/source-summary -> save plugin workflow -> load via registry -> create_workflow_run_v0(...)
```

## Scenario: Workflow Auto Generate-And-Run Command

### 1. Scope / Trigger

- Trigger: Users want AI to create a declarative workflow from a natural-language goal and immediately start it through the governed workflow runner with one explicit command.
- Applies to: `/workflow auto <plugin-id>/<workflow-id> <goal> [-- key=value ...]`, workflow-generation model task completion, latest workflow draft state, user plugin manifests, plugin registry refresh, `workflow_runs.jsonl`, `app.start_workflow_auto_run_generation(...)`, `app.handle_completed_workflow_generation(...)`, `app.run_latest_workflow_draft(...)`, `tests/test_workflows.py`, and policy gates.
- Non-goal: This does not make ordinary `/workflow generate` auto-run, run in-memory drafts, bypass manifest-backed workflow files, duplicate runner/bridge logic, retry invalid model output, auto-select ids, schedule workflows, run plugin code directly, or expose A2A/MCP workflow services.

### 2. Signatures

- Public command:
  - `/workflow auto <plugin-id>/<workflow-id> <goal> [-- key=value ...]`
- Command parsing:
  - First token after `auto` is the save/run target ref.
  - Text before optional `--` is the natural-language generation goal.
  - Tokens after optional `--` are parsed with the existing workflow input override grammar.
- Pending state fields:
  - `State.workflow_auto_run_ref`
  - `State.workflow_auto_run_inputs`
  - `State.workflow_auto_run_source`
  - `State.workflow_auto_run_command`
- Existing helpers reused after generation:
  - `app.save_latest_workflow_draft_result(...)`
  - `app.run_latest_workflow_draft(...)`
  - `app.create_workflow_run_v0(...)`

### 3. Contracts

- `/workflow auto ...` starts a bounded workflow-generation main-agent task with a `workflow_generate:auto:<digest>` source.
- The command must validate the target ref and input override syntax before starting the model task.
- No file or ledger row may be written until the model output completes and validates as a workflow draft.
- On valid generated output, the completion handler must store the draft, save it as a normal manifest-backed plugin workflow, reload it through the plugin registry, and run it through `create_workflow_run_v0(...)`.
- On invalid generated output, the completion handler must render the existing draft rejection, clear the pending auto-run request, append no workflow rows, write no plugin files, and not overwrite any previous valid draft.
- Normal `/workflow generate <goal>` must clear stale auto-run state and remain non-executing.
- Auto-run output must show that auto generation completed and include the existing save/run audit sections.
- Approval and agent-task side effects, if any, remain owned by the existing Workflow Approval Bridge and Workflow Agent Task Bridge.
- `workflows.py` remains pure and does not gain app/runtime/UI/governance imports for this command.

### 4. Validation & Error Matrix

- Missing ref or goal -> usage message, no model task.
- Unsafe plugin id or workflow id -> usage message, no model task.
- Invalid input override after `--` -> visible parse error, no model task.
- Valid safe generated draft -> plugin workflow saved, then planned + completed workflow run rows appended.
- Valid approval generated draft -> plugin workflow saved, planned + waiting-approval workflow rows appended, exactly one approval row created by the approval bridge.
- Valid agent-task generated draft -> plugin workflow saved, planned + waiting-task workflow rows appended, exactly one governed subagent task dispatched by the agent-task bridge.
- Invalid generated output -> no save, no run, no non-workflow side effects, previous valid draft preserved.
- Ordinary `/workflow generate` after a prior auto request -> draft ready only, no save/run.

### 5. Good/Base/Bad Cases

- Good: `/workflow auto generated-pack/source-summary summarize sources -- ready=true` generates JSON, saves `generated-pack/source-summary`, and starts a normal workflow run with `inputs.ready=true`.
- Good: An approval generated by auto-run carries a `source_command` pointing to the original `/workflow auto ...` command.
- Base: Users may still use `/workflow generate`, inspect, then `/workflow save-last` or `/workflow run-last` when they want a manual review pause.
- Bad: `/workflow auto ...` starts running before model output has been validated and saved.
- Bad: `/workflow generate ...` inherits stale auto-run state from a previous command and unexpectedly runs.
- Bad: Auto-run builds workflow rows directly from `State.workflow_draft_payload` without saving and loading a manifest-backed workflow first.

### 6. Tests Required

- `tests/test_workflows.py` must assert auto-run safe generated drafts are saved and run with parsed inputs.
- `tests/test_workflows.py` must assert auto-run approval drafts use the existing approval bridge and preserve source command provenance.
- `tests/test_workflows.py` must assert unsafe refs and invalid generated output produce no save/run side effects and clear pending auto-run state.
- `tests/test_workflows.py` must assert normal generate remains non-executing after auto-run paths.
- `scripts/check_policy_gates.py` must assert `/workflow auto` exists, starts a `workflow_generate:auto` source, saves before running, and keeps `workflows.py` pure.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow auto generated-pack/source-summary summarize -> model returns JSON -> app directly builds workflow_runs.jsonl rows from State.workflow_draft_payload
```

#### Correct

```text
/workflow auto generated-pack/source-summary summarize -> validated draft -> save plugin workflow -> load via registry -> create_workflow_run_v0(...)
```

## Scenario: Workflow Do One-Command Generate-And-Run

### 1. Scope / Trigger

- Trigger: Users want AI to build and run a workflow from natural language without first selecting a plugin id or workflow id.
- Applies to: `/workflow do <goal> [-- key=value ...]`, generated workflow refs, user plugin manifests, workflow-generation completion, `app.workflow_do_ref_for_goal(...)`, `app.start_workflow_auto_run_generation(...)`, `app.run_latest_workflow_draft(...)`, `tests/test_workflows.py`, and policy gates.
- Non-goal: This does not replace `/workflow auto`, add an in-memory executor, mutate built-in plugin data, bypass manifest-backed workflow files, retry invalid model output, schedule workflows, run plugin code directly, or expose A2A/MCP workflow services.

### 2. Signatures

- Public command:
  - `/workflow do <goal> [-- key=value ...]`
- Default user plugin id:
  - `shuheng-auto-workflows`
- Generated workflow id shape:
  - Filesystem-safe slug from the goal plus a stable digest suffix.
- Existing helpers reused:
  - `app.workflow_do_ref_for_goal(goal)`
  - `app.parse_workflow_do_command_args(...)`
  - `app.start_workflow_auto_run_generation(...)`
  - `app.run_latest_workflow_draft(...)`
  - `app.create_workflow_run_v0(...)`

### 3. Contracts

- `/workflow do ...` must derive a safe workflow ref automatically under the normal user plugin root.
- The derived ref must be stable for the same goal and must not point at the read-only built-in plugin root.
- The command must parse optional run inputs after `--` with the same grammar as `/workflow run` and `/workflow auto`.
- The command must start the same bounded workflow-generation task used by `/workflow auto`, with a `workflow_generate:auto:<digest>` source and pending auto-run state.
- No file or ledger row may be written until generated model output validates as a workflow draft.
- On valid output, the draft must be saved as a normal manifest-backed user plugin workflow, loaded through the plugin registry, and run through `create_workflow_run_v0(...)`.
- On invalid output, the pending auto-run request is cleared, the previous valid draft is preserved, and no workflow/plugin files or ledgers are written.
- Existing `/workflow auto <plugin-id>/<workflow-id> ...` behavior remains compatible and continues to let users choose explicit refs.
- Approval and agent-task side effects, if any, remain owned by the existing Workflow Approval Bridge and Workflow Agent Task Bridge.

### 4. Validation & Error Matrix

- `/workflow do` with no goal -> usage message, no model task.
- `/workflow do summarize sources -- ready=true` -> pending auto-run ref under `plugin://shuheng-auto-workflows/workflows/...` and parsed inputs `{"ready":true}`.
- Valid safe generated draft -> workflow JSON and plugin manifest saved under `SHUHENG_PLUGINS_DIR/shuheng-auto-workflows`, then normal workflow run rows appended.
- Valid approval or agent-task generated draft -> side effects go only through existing approval/task bridges.
- Invalid generated output -> no save, no run, no non-workflow side effects, previous valid draft preserved.
- Built-in plugin root -> unchanged by `/workflow do`.

### 5. Good/Base/Bad Cases

- Good: `/workflow do summarize sources -- ready=true` generates a stable `shuheng-auto-workflows/<slug>-<digest>` workflow, saves it as a user plugin, and starts a governed workflow run.
- Good: `/workflow auto generated-pack/source-summary ...` still works for users who want explicit package ids.
- Base: A non-ASCII goal may fall back to `workflow-<digest>` for the workflow id while preserving stable ref generation.
- Bad: `/workflow do ...` writes to `src/shuheng/builtin_plugins`.
- Bad: `/workflow do ...` executes model output directly from `State.workflow_draft_payload`.
- Bad: `/workflow do ...` appends workflow rows without first saving and reloading a manifest-backed workflow.

### 6. Tests Required

- `tests/test_workflows.py` must assert `/workflow do` derives a default ref, starts `workflow_generate:auto`, saves to the user plugin root, runs through the normal workflow runner, and accepts input overrides.
- `tests/test_workflows.py` must assert blank goals and invalid input overrides are no-ops with usage or parse errors.
- `scripts/check_policy_gates.py` must assert `/workflow do` exists, uses `workflow_do_ref_for_goal(...)`, starts a workflow-generation auto source, saves to `SHUHENG_PLUGINS_DIR`, and keeps task/progress/approval/artifact ledgers unchanged for safe workflows.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow do summarize -> model JSON -> direct run rows from in-memory draft
```

#### Correct

```text
/workflow do summarize -> generated safe ref -> validated draft -> save user plugin workflow -> load via registry -> create_workflow_run_v0(...)
```

## Scenario: Workflow Inputs and Condition V1

### 1. Scope / Trigger

- Trigger: Users need manifest-backed workflows to accept explicit run inputs and make safe deterministic branches without adding a hidden expression engine.
- Applies to: workflow `inputs`, `/workflow run <ref> key=value ...`, `/workflow run-last <plugin-id>/<workflow-id> key=value ...`, `workflow_runs.jsonl`, `workflows.resolve_workflow_run_inputs(...)`, `workflows.advance_workflow_run_v0(...)`, `app.create_workflow_run_v0(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: This does not add Python/JavaScript/shell expression execution, prompt templating, artifact/task/file/env/Secret Vault reads, model/tool calls, plugin code execution, fan-out/fan-in, scheduling, retries, rollback, UI forms, or A2A/MCP workflow services.

### 2. Signatures

- Public commands:
  - `/workflow run <plugin-id>/<workflow-id> [key=value ...]`
  - `/workflow run-last <plugin-id>/<workflow-id> [key=value ...]`
- Input declaration source: workflow definition `inputs` object or list already parsed into `WorkflowInput`.
- Condition v1 source: a JSON object under a condition step's `condition` or `when` field.
- Supported condition operators:
  - `{"ref":"inputs.<id>","equals":<value>}`
  - `{"ref":"inputs.<id>","not_equals":<value>}`
  - `{"ref":"inputs.<id>","exists":true|false}`
  - `{"ref":"inputs.<id>","truthy":true|false}`
  - `{"ref":"inputs.<id>","in":[...]}`
  - `{"all":[...]}`, `{"any":[...]}`, and `{"not":{...}}`
- Pure helper ownership:
  - `workflows.resolve_workflow_run_inputs(definition, inputs=None)`
  - `workflows.build_workflow_run_record(result, run_id, timestamp, inputs=None, source="workflow_command")`
  - `workflows.advance_workflow_run_v0(row, timestamp=...)`
- App ownership:
  - `app.parse_workflow_run_command_args(...)`
  - `app.create_workflow_run_v0(result, state=None, inputs=None, source_command=...)`
  - `app.run_latest_workflow_draft(state, ref, inputs=None, source_command=...)`

### 3. Contracts

- Input resolution must happen before any workflow run row is appended.
- If a workflow declares no inputs, `build_workflow_run_record(..., inputs=...)` preserves the previous behavior and stores the explicit input snapshot as-is.
- If a workflow declares inputs, unknown explicit input keys must reject run creation with visible validation issues.
- Required inputs without explicit values or non-`null` defaults must reject run creation with visible validation issues.
- Optional/defaulted inputs must be resolved into the planned workflow row before runner v0 advances.
- CLI overrides use `key=value` syntax. `true`, `false`, `null`, JSON arrays/objects/strings, and simple numbers may be parsed into JSON-like values; validation still belongs to the workflow input contract.
- Condition v1 may read only `inputs.<id>`. Any other ref namespace is unsupported.
- A true condition marks the condition step `completed`, increments normal runner-v0 completed-step progress, and allows later dependent safe steps to continue.
- A false condition marks the condition step `skipped`, leaves downstream dependent steps pending, sets the workflow run status to `blocked`, and must not create side-effect ledgers.
- Unsupported condition shapes, string `expression` fields, invalid refs, or invalid operator payloads remain `blocked` with a clear reason and no side effects.
- `workflows.py` remains pure: no app/runtime/UI/governance imports, no JSONL writes, no approval queue writes, no subagent dispatch, no tools/providers/subprocess, and no Secret Vault access.
- `app.py` remains the Orchestrator owner for command parsing, run id/timestamp selection, file writes, registry refresh, state mutation, and ledger appends.

### 4. Validation & Error Matrix

- `/workflow run research-pack/flow` with missing required input -> visible rejection, no workflow/task/progress/approval/artifact ledger writes.
- `/workflow run research-pack/flow ready=true typo=x` when `typo` is undeclared -> visible rejection, no workflow run row.
- Optional/defaulted input omitted -> planned row contains the resolved default.
- `prompt -> condition -> notify` with `ready=true` and a matching condition v1 predicate -> planned + completed workflow rows, all three steps completed, no side-effect ledgers.
- Same workflow with `ready=false` -> planned + blocked workflow rows, condition step `skipped`, notify step pending, no task/progress/approval/artifact ledgers.
- String `expression` condition -> blocked and side-effect-free.
- Condition ref such as `artifacts.output` or `files.x` -> blocked and side-effect-free.
- `/workflow run-last generated-pack/flow ready=true` -> saves the latest valid draft, reloads it through the plugin registry, then creates normal workflow run rows with resolved inputs.

### 5. Good/Base/Bad Cases

- Good: `/workflow run research-pack/review ready=true mode=safe` stores `{"ready": true, "mode": "safe"}` in the planned row and completes the safe branch if the condition predicate matches.
- Good: A false condition is auditable as a skipped condition step, not as a silent success.
- Good: A generated workflow can include `{"condition":{"ref":"inputs.ready","equals":true}}`, then `/workflow run-last ... ready=true` saves and runs through the same manifest-backed path as hand-written workflows.
- Base: String `expression` remains allowed as inert future metadata only when validation accepts the workflow; runner v0 must not execute it.
- Bad: `workflows.py` uses `eval`, `exec`, Python AST evaluation, JavaScript, shell, or plugin code to evaluate a condition.
- Bad: Condition predicates read artifacts, task results, files, environment variables, Secret Vault entries, model output, or tool results in this slice.
- Bad: Missing inputs create a planned workflow row and fail later during runner advancement.

### 6. Tests Required

- `tests/test_workflows.py` must assert input defaults, missing required input rejection, unknown input rejection, app command `key=value` parsing, true/false/unsupported condition behavior, run-last with inputs, and side-effect ledger invariants.
- `scripts/check_policy_gates.py` must assert missing/unknown inputs write no workflow rows, condition v1 true completes, condition v1 false skips and blocks, unsupported/string conditions remain blocked, and `workflows.py` purity holds.
- Existing workflow approval, agent-task, auto-continue, generation, save-last, run-last, run inspection, and continue tests must remain green.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow run research-pack/review ready=true -> eval("inputs.ready == true") inside workflows.py
```

#### Correct

```text
/workflow run research-pack/review ready=true -> resolve inputs -> evaluate finite JSON predicate -> append audited workflow rows
```

## Scenario: Planned Workflow Run Ledger Skeleton

### 1. Scope / Trigger

- Trigger: Shuheng needs a durable initial workflow run identity and audit row before any runner advances the row.
- Applies to: `workflow_runs.jsonl`, `shuheng.workflow_run.v1`, `workflows.py` run-record helpers, `/workflow run <ref>` initial row creation, `app.py` workflow command routing, and policy gates.
- Non-goal: The planned row builder does not execute steps, advance step state, dispatch subagents, create approvals, write artifacts, call tools, mutate task/progress ledgers, schedule work, run plugin code, or expose remote A2A/MCP workflow services.

### 2. Signatures

- Public command:
  - `/workflow run <plugin-id>/<workflow-id>`
  - `/workflow run plugin://<plugin-id>/workflows/<workflow-id>`
- Ledger path: `AGENT_WORKFLOW_RUNS_PATH = os.path.join(AGENT_HARNESS_DIR, "workflow_runs.jsonl")`.
- Ledger row schema version: `shuheng.workflow_run.v1`.
- Initial run status: `planned`.
- Initial step status: `pending`.
- Pure helper ownership:
  - `workflows.build_workflow_run_record(result, run_id, timestamp, inputs=None, source="workflow_command")`
  - `workflows.format_workflow_run_created(row)`
  - `workflows.format_workflow_run_rejected(result, issues)`
- App ownership:
  - `app.create_planned_workflow_run(result)` remains the compatibility helper that chooses run id/timestamp and appends exactly one planned workflow run row.
  - `app.workflow_run_records(limit=0)` reads workflow run rows.

### 3. Contracts

- `build_workflow_run_record(...)` creates the initial planned row used by `/workflow run` before any runner-specific advancement.
- Workflow definitions must pass the existing parser/validation path before a run row is appended.
- Invalid workflow definitions must produce a visible rejection message and must not append a workflow run row.
- `workflows.py` remains pure. It may build dictionaries from `WorkflowLoadResult`, but must not import `app.py`, curses, runtime dispatch, approval queues, task/progress ledgers, artifacts, provider adapters, governance owners, Secret Vault, or subprocess.
- `app.py` owns the concrete harness path and JSONL append operation.
- Workflow `permissions` copied into a run row are metadata only. They must not grant tools, write permissions, approval bypasses, Secret Vault access, single-writer locks, or runtime dispatch capability.
- The planned row's `execution` block must explicitly record zero execution side effects for this skeleton: zero steps executed, zero subagents dispatched, zero approvals created, zero tools called, zero artifacts written, zero task/progress ledger rows written, no plugin code executed, and no runner started.

### 4. Validation & Error Matrix

- Missing workflow ref -> visible "Workflow not found" rejection, no run row.
- Invalid workflow body -> visible validation rejection, no run row.
- Wrong schema version -> visible validation rejection, no run row.
- Unsupported step type -> visible validation rejection, no run row.
- Duplicate step/input id -> visible validation rejection, no run row.
- Valid workflow -> initial `planned` run row with pending step snapshots.
- Valid workflow containing `agent_task` or `approval` steps -> the initial row is still only planned; no subagent or approval row is created by this helper.

### 5. Good/Base/Bad Cases

- Good: `build_workflow_run_record(...)` returns one initial `planned` row with pending step snapshots.
- Good: A planned row captures workflow ref, source path, permissions metadata, input snapshot, and ordered pending step snapshots.
- Base: Input snapshot may be `{}` until a later task adds command input binding.
- Bad: Planned row creation calls `start_subagent_task(...)`.
- Bad: Planned row creation writes `tasks.jsonl`, `progress.jsonl`, `approvals.jsonl`, or `artifacts.jsonl`.
- Bad: `workflows.py` imports app/runtime/governance modules to append records directly.

### 6. Tests Required

- `tests/test_workflows.py` must assert planned run row shape, pending step snapshots, no-op execution counters, and invalid workflow rejection.
- App command tests or policy gates must assert the initial row is planned before any runner v0 advanced row is appended.
- `scripts/check_policy_gates.py` must assert `shuheng.workflow_run.v1`, `status=planned`, zero execution side effects, and that `workflows.py` remains independent from app/runtime/UI/governance owners.
- Keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, targeted pytest, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
build_workflow_run_record(...) -> creates subagent task and approval rows immediately
```

#### Correct

```text
build_workflow_run_record(...) -> returns a planned workflow run row with pending step snapshots and zero execution side effects
```

## Scenario: Workflow Runner V0

### 1. Scope / Trigger

- Trigger: Users want workflow runner v0 to make deterministic safe progress after the planned run ledger skeleton exists.
- Applies to: `/workflow run <ref>`, `workflow_runs.jsonl`, `shuheng.workflow_run.v1`, `workflows.advance_workflow_run_v0(...)`, `workflows.format_workflow_run_advanced(...)`, `app.create_workflow_run_v0(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: The pure runner does not dispatch subagents, create approval rows, call model providers, execute tools, run shell commands, execute plugin code, evaluate free-form condition expressions, write artifacts, mutate task/progress ledgers, write memory, touch Secret Vault, schedule work, or expose A2A/MCP workflow services. App-side bridge contracts may act after the pure runner reaches a supported blocking step.

### 2. Signatures

- Public command:
  - `/workflow run <plugin-id>/<workflow-id>`
  - `/workflow run plugin://<plugin-id>/workflows/<workflow-id>`
- Pure helper ownership:
  - `workflows.advance_workflow_run_v0(row, timestamp=...)`
  - `workflows.format_workflow_run_advanced(result)`
- App ownership:
  - `app.create_workflow_run_v0(result, state=None)` chooses run id/timestamps, appends one initial planned row, advances the copied row through runner v0, then lets app-owned bridge contracts attach approval or subagent task side effects before appending the second row with the same `run_id`.
- Runner v0 safe step types: `prompt`, `notify`, `pause`, and `artifact_summary`.
- Runner v0 blocking step types: `approval`, `agent_task`, unsupported/string `condition`, false condition v1, and any future step type not explicitly classified as safe.
- Advanced row execution mode: `workflow_runner_v0`.

### 3. Contracts

- `/workflow run` must validate workflow definitions through the manifest-backed workflow loader before appending rows.
- A successful `/workflow run` appends exactly two rows to `workflow_runs.jsonl`: first `planned`, then the advanced runner v0 row with the same `run_id`, optionally upgraded by an app-owned approval or agent-task bridge.
- `advance_workflow_run_v0(...)` operates on a run row copy and must not perform I/O.
- Safe steps may be marked `completed` in order after their dependencies are completed.
- `steps_executed` records the count of safe steps completed by runner v0. It is the only execution counter that may be non-zero in the pure runner result before app-owned bridge contracts run.
- `approval` stops the run at `waiting_approval`, sets workflow-run approval metadata to pending, and must not write `approvals.jsonl`.
- `agent_task` stops the pure runner at `blocked` and must not call `start_subagent_task(...)`, runtime dispatch, or task/progress ledger writers from `workflows.py`. Real dispatch is owned only by the Workflow Agent Task Bridge scenario below.
- `condition` may evaluate only the finite condition v1 JSON predicate operators documented in the Workflow Inputs and Condition V1 scenario. It must not evaluate string expressions, inspect runtime state, call tools, call model providers, or read anything outside resolved run inputs.
- Dependency gaps stop the run at `blocked` rather than reordering or guessing execution.
- `workflows.py` remains pure and must not import `app.py`, curses, runtime dispatch, approval queues, task/progress ledgers, artifacts, provider adapters, governance owners, Secret Vault, or subprocess.
- Workflow `permissions` remain metadata. They must not grant tools, write permissions, approval bypasses, Secret Vault access, single-writer locks, artifact provenance writes, task ledgers, or runtime dispatch capability.
- User-facing `/workflow run` output must report the advanced status, completed safe-step count, stop step/reason when applicable, and any bridge-created approval or subagent side effects. Workflow-owned tools, plugin code, condition expressions, and direct artifact writes remain forbidden.

### 4. Validation & Error Matrix

- Missing workflow ref -> visible "Workflow not found" rejection, no workflow run row.
- Invalid workflow body -> visible validation rejection, no workflow run row.
- Wrong schema version -> visible validation rejection, no workflow run row.
- Unsupported definition step type -> visible validation rejection, no workflow run row.
- Safe-only valid workflow -> two rows, latest row `status=completed`, safe steps `completed`, no side-effect counters except `steps_executed`.
- Valid workflow with safe step then `approval` -> two rows, latest row `status=waiting_approval`, prior safe steps `completed`, approval step `waiting_approval`, no approval row.
- Pure helper with safe step then `agent_task` -> latest copied row `status=blocked`, prior safe steps `completed`, agent task `blocked`, no subagent/task/progress rows.
- App `/workflow run` with safe step then bridgeable `agent_task` -> two workflow rows, latest row `status=waiting_task`, one governed subagent task dispatched by the Workflow Agent Task Bridge.
- Valid workflow with unsupported/string `condition` -> two rows, latest row `status=blocked`, no expression evaluation.
- Valid workflow with true condition v1 -> two rows, latest row may continue through later safe steps.
- Valid workflow with false condition v1 -> two rows, latest row `status=blocked`, condition step `skipped`, no side-effect ledgers.
- Valid workflow with unmet dependency order -> latest row `status=blocked`, no reordering.

### 5. Good/Base/Bad Cases

- Good: `advance_workflow_run_v0(...)` completes the `prompt` step, then blocks at `agent_task` without side effects.
- Good: `/workflow run research-pack/compare-sources` may append a second row upgraded to `waiting_task` after the app-owned Workflow Agent Task Bridge dispatches through `start_subagent_task_structured(...)`.
- Good: A safe-only workflow ends with `status=completed` and `execution.mode="workflow_runner_v0"`.
- Good: A workflow requiring approval stops at `waiting_approval` without creating `approvals.jsonl` rows.
- Base: `pause` is a ledger-only no-op checkpoint in v0, not a timer or scheduler integration.
- Base: `artifact_summary` is ledger-only in v0 and must not create artifact index rows.
- Bad: `workflows.advance_workflow_run_v0(...)` calls `start_subagent_task(...)` for `agent_task`.
- Bad: Runner v0 writes `tasks.jsonl`, `progress.jsonl`, `approvals.jsonl`, or `artifacts.jsonl`.
- Bad: Runner v0 evaluates a `condition` string expression from plugin workflow data.
- Bad: Runner v0 imports app/runtime/governance modules into `workflows.py` to append records directly.

### 6. Tests Required

- `tests/test_workflows.py` must assert safe-only completion, approval wait without approval-row creation in the pure helper, agent-task blocking without subagent/task/progress rows in the pure helper, unsupported/string condition blocking without expression evaluation, condition v1 true/false behavior, planned-row compatibility, invalid workflow rejection, and app command side effects.
- `scripts/check_policy_gates.py` must assert the pure helper advances a planned row, `/workflow run` appends exactly two workflow run rows, latest status/step statuses are correct for bridged and unbridged cases, condition rows keep side-effect ledgers unchanged, and `workflows.py` remains independent from app/runtime/UI/governance owners.
- Keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, targeted pytest, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow run research-pack/compare-sources -> starts plugin://research-pack/agents/evidence-researcher and writes task/progress rows
```

#### Correct

```text
/workflow run research-pack/compare-sources -> appends planned + runner_v0 rows, completes safe steps, then blocks before agent dispatch
```

## Scenario: Workflow Durable Run Event History V1

### 1. Scope / Trigger

- Trigger: Workflow runs need an explicit event history foundation before Shuheng adds replay, recovery, idempotent retry, timers, workflow-owned actions, or parallel DAG scheduling.
- Applies to: `workflow_events.jsonl`, `shuheng.workflow_event.v1`, `workflows.build_workflow_run_event(...)`, `workflows.workflow_run_event_idempotency_key(...)`, `app.workflow_event_records(...)`, `app.append_workflow_run_event(...)`, `/workflow run`, `/workflow continue|resume`, `/workflow cancel`, `/workflow trace`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: This does not add a workflow-owned executor, replay engine, parallel/fan-out/fan-in scheduler, timer/sleep service, timeout daemon, webhook/event bus service, direct tool/model/shell/plugin-code execution, Secret Vault workflow execution, memory writes, or A2A/MCP workflow service exposure.

### 2. Signatures

- Event schema version: `shuheng.workflow_event.v1`.
- Event ledger path: `AGENT_WORKFLOW_EVENTS_PATH = <agent_harness>/workflow_events.jsonl`.
- Pure helper ownership:
  - `workflows.build_workflow_run_event(row, event_id, timestamp, event_type, source_command="", row_index=0, message="")`
  - `workflows.workflow_run_event_idempotency_key(row, event_type=..., source_command="", row_index=0)`
- App ownership:
  - `app.workflow_event_records(limit=0)`
  - `app.append_workflow_event(row)`
  - `app.append_workflow_run_event(row, event_type=..., source_command="", message="")`
- Event fields: `schema_version`, `event_id`, `run_id`, `workflow_ref`, `timestamp`, `event_type`, `status`, `idempotency_key`, `source_command`, `row_index`, `step_id`, `step_type`, `approval_id`, `task_id`, `artifact_refs`, and `message`.

### 3. Contracts

- Workflow events are append-only audit/provenance records. They must not replace `workflow_runs.jsonl`; run rows remain the source of current workflow state.
- `workflows.py` may build event rows and idempotency keys, but must not append JSONL rows or import app/runtime/UI/governance owners.
- `app.py` remains the only owner for appending workflow event rows.
- A successful `/workflow run <ref>` must append event rows for the initial `run_planned` row and the subsequent runner/bridge row.
- `/workflow continue|resume <run_id>` must append an event for every known run outcome, including continued, completed, no-progress, approval-created, approval-pending, approval-rejected, task-dispatched, task-pending, task-retried, task-terminal, already-completed, and already-terminal outcomes.
- `/workflow cancel <run_id>` must append an event for real cancellation and for already-completed/already-terminal no-op cancellations. Unknown run ids have no row to attach and append no event.
- Event rows must not mutate task/progress/approval/artifact ledgers. Approval and agent-task side effects remain owned by their existing bridge contracts.
- `idempotency_key` must be deterministic for the same run/status/blocker/source transition shape and must hash source command content rather than storing raw prompt text in the key.
- `source_command` and `message` are bounded text fields for audit display. Raw workflow step prompts, model payloads, artifact contents, and trace payloads must not be inlined into workflow events.
- `/workflow trace <run-id>` must include linked workflow event rows and keep raw event payloads out of normal rendering.
- Workflow event rows are an execution-history foundation only. They do not by themselves authorize replay, recovery, timers, tool execution, scheduler fan-out, or approval bypasses.

### 4. Validation & Error Matrix

- Invalid event id -> pure helper returns an issue and no event row.
- Missing run id -> pure helper returns an issue and no event row.
- Planned run -> appends `run_planned` event with `row_index=1`.
- Runner/bridge row after `/workflow run` -> appends `run_completed`, `run_advanced`, `run_approval_created`, or `run_task_dispatched`.
- Continue on blocked condition with no progress -> appends `continue_no_progress` and no workflow run row.
- Continue while agent task is still non-terminal -> appends `continue_task_pending` and no workflow run row.
- Continue after completed agent task -> appends `continue_completed` or `continue_advanced` on the newly appended workflow run row.
- Continue after failed agent task with remaining attempts -> appends `continue_task_retried` on the retry-dispatched row.
- Cancel active run -> appends one cancelled workflow run row and one `cancel_cancelled` event.
- Cancel already terminal run -> appends no workflow run row and one no-op cancellation event.
- Trace rendering with event rows -> shows event id/type/status/row index/blocker refs/idempotency key, but not raw payloads.

### 5. Good/Base/Bad Cases

- Good: `/workflow run research-pack/compare-sources` creates two workflow run rows and two workflow event rows.
- Good: Repeated `/workflow continue <run-id>` on an unchanged blocked condition appends repeat `continue_no_progress` events with the same idempotency key but no duplicate workflow run row.
- Good: `/workflow trace <run-id>` shows `workflow_events:` with bounded event summaries.
- Base: `workflow_events.jsonl` is not yet a replay log; it is the durable event-history substrate for a later replay/recovery engine.
- Bad: `workflows.build_workflow_run_event(...)` calls `append_jsonl(...)`.
- Bad: Event idempotency keys include raw user prompts or full source command text.
- Bad: Writing a workflow event creates approval, task, progress, artifact, memory, scheduler, or trace rows.

### 6. Tests Required

- `tests/test_workflows.py` must assert pure event construction, deterministic idempotency key shape, bounded source/message fields, run/continue/cancel event append behavior, trace rendering, and raw payload exclusion.
- `scripts/check_policy_gates.py` must assert `WORKFLOW_EVENT_SCHEMA_VERSION`, `AGENT_WORKFLOW_EVENTS_PATH`, event helper ownership, app-owned append path, `/workflow trace` event integration, and `workflows.py` purity.
- Keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, targeted pytest, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

## Scenario: Workflow Run Inspection Commands

### 1. Scope / Trigger

- Trigger: Users need to inspect append-only workflow run history before Shuheng adds workflow resume, real approval bridge, or agent dispatch.
- Applies to: `/workflow runs`, `/workflow show <run_id>`, `workflow_runs.jsonl`, `shuheng.workflow_run.v1`, `workflows.format_workflow_runs(...)`, `workflows.format_workflow_run_detail(...)`, `app.workflow_run_records(...)`, `app.latest_workflow_run_records(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: Inspection commands do not continue runs, dispatch subagents, create approvals, call model providers, execute tools, run shell commands, execute plugin code, evaluate conditions, write artifacts, mutate task/progress ledgers, write memory, touch Secret Vault, schedule work, or expose A2A/MCP workflow services.

### 2. Signatures

- Public commands:
  - `/workflow runs`
  - `/workflow show <run_id>`
  - `/workflow run-info <run_id>` and `/workflow runinfo <run_id>` may alias the same detail view.
- Ledger path: `AGENT_WORKFLOW_RUNS_PATH = os.path.join(AGENT_HARNESS_DIR, "workflow_runs.jsonl")`.
- Read helper ownership:
  - `app.workflow_run_records(limit=0)` reads raw workflow run JSONL rows.
  - `app.latest_workflow_run_records()` returns latest rows by `run_id`.
- Pure formatting ownership:
  - `workflows.format_workflow_runs(rows, limit=20)`
  - `workflows.format_workflow_run_detail(run_id, rows)`

### 3. Contracts

- `/workflow runs` reads `workflow_runs.jsonl`, groups append-only rows by `run_id`, and renders the latest row per run id in recent-first order.
- `/workflow runs` must show run id, status, workflow ref, completed/total step count, last timestamp, and stop reason when present.
- `/workflow show <run_id>` reads `workflow_runs.jsonl`, filters rows for that run id, renders the latest row, and includes the number of append-only history rows for that run.
- `/workflow show <run_id>` must show status, workflow ref, timestamps, execution counters, approval metadata, step statuses, task/approval ids when present, and stop reason when present.
- Empty or missing `workflow_runs.jsonl` must render a no-runs message, not a traceback.
- Unknown run id must render a not-found message and must not mutate state beyond adding a system message.
- Inspection commands are read-only. They must not append workflow run rows or write task/progress/approval/artifact ledgers.
- `workflows.py` remains pure and must not import `app.py`, curses, runtime dispatch, approval queues, task/progress ledgers, artifacts, provider adapters, governance owners, Secret Vault, or subprocess.

### 4. Validation & Error Matrix

- Missing workflow run ledger -> `/workflow runs` displays no runs.
- Empty workflow run ledger -> `/workflow runs` displays no runs.
- Multiple rows for the same `run_id` -> `/workflow runs` displays only the latest row for that run id.
- Known run id -> `/workflow show <run_id>` displays latest state plus `history_rows`.
- Unknown run id -> visible not-found message, no ledger writes.
- Rows without `run_id` -> ignored by grouped run listing.
- Run row with missing optional fields -> displays blanks/default counters, no crash.

### 5. Good/Base/Bad Cases

- Good: After `/workflow run research-pack/compare-sources`, `/workflow runs` shows one run id with latest `blocked` status and safe-step progress.
- Good: `/workflow show wfr_...` shows `history_rows: 2`, execution counters, approval metadata, and each step status.
- Base: Inspection output is text-first in the TUI command stream; a panel view can be added later using the same pure formatting or projection helpers.
- Bad: `/workflow show <run_id>` calls `advance_workflow_run_v0(...)` or appends a new run row.
- Bad: `/workflow runs` writes `tasks.jsonl`, `progress.jsonl`, `approvals.jsonl`, or `artifacts.jsonl`.
- Bad: Inspection commands dispatch subagents, evaluate conditions, call tools, or run plugin code.

### 6. Tests Required

- `tests/test_workflows.py` must assert empty listing, grouped latest-row listing, detail output with history count and step statuses, unknown run id output, and app command read-only behavior.
- `scripts/check_policy_gates.py` must assert `/workflow runs` and `/workflow show <run_id>` can inspect rows created by `/workflow run`, do not append extra workflow run rows, and leave subagents plus task/progress/approval/artifact ledgers unchanged.
- Keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, targeted pytest, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow show wfr_123 -> resumes the workflow and starts the blocked agent_task
```

#### Correct

```text
/workflow show wfr_123 -> reads workflow_runs.jsonl and renders the latest row plus history count without side effects
```

## Scenario: Workflow Run Trace / Provenance View V1

### 1. Scope / Trigger

- Trigger: Users need an auditable per-run trace view that links workflow run history to task, approval, artifact, and trace ledgers without manually joining JSONL files.
- Applies to: `/workflow trace <run_id>`, `/workflow provenance <run_id>`, `workflow_runs.jsonl`, `tasks.jsonl`, `approvals.jsonl`, `artifacts.jsonl`, `traces.jsonl`, `workflows.format_workflow_run_trace(...)`, `app.handle_workflow_command(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: Trace/provenance inspection does not continue, cancel, retry, approve, reject, dispatch subagents, execute tools, call providers, inline raw artifacts, inline raw trace payloads, write memory, mutate plugin files, or expose A2A/MCP workflow services.

### 2. Signatures

- Public commands:
  - `/workflow trace <run_id>`
  - `/workflow provenance <run_id>`
- Pure formatter:
  - `workflows.format_workflow_run_trace(run_id, workflow_rows, task_rows=..., approval_rows=..., artifact_rows=..., trace_rows=...) -> str`
- App command ownership:
  - `app.handle_workflow_command(...)` reads the relevant ledgers and passes row lists into the pure formatter.

### 3. Contracts

- `/workflow trace <run_id>` and `/workflow provenance <run_id>` are aliases for the same read-only projection.
- Unknown or blank run ids must render `Workflow run not found: <run_id>` and append no ledger rows.
- The trace view must render latest workflow status, workflow ref, history row count, timestamps, completed/total step count, and stop reason when present.
- The trace view must render the append-only run timeline in history order. Each timeline row must include row index, status, update timestamp, completed/total step count, blocked step/type, and reason.
- The trace view must render latest step state, including task ids, task status, agent ids, approval ids, retry counters, artifact refs, and errors when present.
- The trace view must link task rows by task ids referenced from workflow steps, including retry attempt task ids.
- The trace view must link approval rows by approval ids referenced from workflow run approval metadata or step metadata.
- The trace view must link artifact refs from workflow rows, workflow steps, and linked task rows, then show matching artifact index rows by URI/ref.
- The trace view must link trace refs by task ids referenced from workflow steps.
- The trace view must not inline raw artifact content or raw trace payloads. It may show refs, ids, statuses, summaries, kinds, provenance summaries, and bounded metadata.
- `workflows.py` remains pure. `format_workflow_run_trace(...)` accepts row lists as parameters and must not read files, import app/runtime/UI/governance owners, append JSONL rows, queue approvals, dispatch subagents, or call tools/providers.

### 4. Validation & Error Matrix

- Missing run id -> visible not-found message, no ledger writes.
- Unknown run id -> visible not-found message, no ledger writes.
- Known run with one row -> timeline has one row and latest step projection.
- Known run with multiple rows -> timeline shows append-only row order and latest step state comes from the latest row.
- Run references a task id -> linked task row is shown if present; missing task row leaves linked task section empty.
- Run references an approval id -> linked approval row is shown if present; missing approval row leaves linked approval section empty.
- Run and linked task rows reference artifact refs -> refs are listed; matching artifact index rows are listed by URI without body content.
- Linked task has trace rows -> trace refs are listed by trace id/event/status without raw payload.

### 5. Good/Base/Bad Cases

- Good: `/workflow trace wfr_...` shows `timeline`, `latest_steps`, `linked_tasks`, `linked_approvals`, `artifact_refs`, `artifact_index`, and `trace_refs`.
- Good: A workflow run waiting on `task_...` links the latest task row and trace refs for that task.
- Good: A completed workflow with artifact refs shows artifact URIs and provenance summaries without opening artifact files.
- Base: The trace view is a command-stream text projection. A future panel or web timeline should reuse the same pure formatter or projection helpers.
- Bad: `/workflow trace <run_id>` calls `continue_workflow_run_v0(...)` to refresh status.
- Bad: `/workflow trace <run_id>` appends a new trace row saying it was inspected.
- Bad: `format_workflow_run_trace(...)` reads `AGENT_TRACES_PATH` or imports `app.py`.
- Bad: The trace view inlines raw artifact bodies or trace payloads into the chat.

### 6. Tests Required

- `tests/test_workflows.py` must assert missing-run formatting, timeline formatting, latest-step projection, linked task rows, linked approval rows, artifact refs/index rows, trace refs, raw payload exclusion, and `/workflow trace|provenance` command read-only behavior.
- `scripts/check_policy_gates.py` must assert command aliases route to the pure formatter, the app reads trace/artifact/task/approval ledgers only for projection, inspection appends no workflow/task/progress/approval/artifact/trace rows, and `workflows.py` remains side-effect-free.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow trace wfr_123 -> append_trace(..., event="workflow_inspected")
```

#### Correct

```text
/workflow trace wfr_123 -> read ledgers -> format_workflow_run_trace(...)
```

## Scenario: Workflow Next Action Diagnostics V1

### 1. Scope / Trigger

- Trigger: Users and AI operators need a concise read-only answer for what an append-only workflow run is waiting on and which existing command should be used next.
- Applies to: `/workflow next <run_id>`, `/workflow diagnose <run_id>`, `/workflow next-json <run_id>`, `/workflow diagnose-json <run_id>`, `workflow_runs.jsonl`, `tasks.jsonl`, `approvals.jsonl`, `workflows.workflow_run_next_action_projection(...)`, `workflows.format_workflow_run_next_action(...)`, `app.handle_workflow_command(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: Diagnostics do not continue, cancel, retry, approve, reject, dispatch subagents, execute tools, call providers, create approvals, append workflow rows, mutate task/progress/artifact/trace ledgers, inline raw artifacts, edit workflow definitions, schedule work, or expose A2A/MCP workflow services.

### 2. Signatures

- Public commands:
  - `/workflow next <run_id>`
  - `/workflow diagnose <run_id>`
  - `/workflow next-json <run_id>`
  - `/workflow diagnose-json <run_id>`
- Pure projection:
  - `workflows.workflow_run_next_action_projection(run_id, workflow_rows, task_rows=..., approval_rows=...) -> dict`
- Pure formatter:
  - `workflows.format_workflow_run_next_action(run_id, workflow_rows, task_rows=..., approval_rows=...) -> str`
- App command ownership:
  - `app.handle_workflow_command(...)` reads workflow/task/approval ledgers and passes row lists into the pure projection or formatter.
- JSON schema:
  - `schema_version: "shuheng.workflow_next_action.v1"`
  - `run_id`, `found`, `status`, `workflow_ref`, `history_rows`, `blocked_step`, `stop_reason`, `next_action`, `commands`, `approval`, `task`, `read_only`, and `rows_appended`.

### 3. Contracts

- `/workflow next <run_id>` and `/workflow diagnose <run_id>` are aliases for the same read-only projection.
- `/workflow next-json <run_id>` and `/workflow diagnose-json <run_id>` are aliases for the same machine-readable projection.
- Unknown or blank run ids in the text command must render `Workflow run not found: <run_id>` and append no ledger rows.
- Unknown or blank run ids in the JSON command must render valid JSON with `found:false`, `rows_appended:false`, `read_only:true`, and an `error` string.
- The projection must render latest workflow status, workflow ref, append-only history row count, blocked step id/type when present, stop reason when present, and a `next_action:` classification.
- The JSON projection must render the same classification as text output without requiring AI agents to parse human prose.
- `workflows.format_workflow_run_next_action(...)` must derive text output from `workflow_run_next_action_projection(...)` so text and JSON cannot drift.
- Valid next-action classifications are text labels for user guidance, not executable state transitions. Current labels include `continue`, `wait_task`, `approve_or_reject`, `inspect_trace`, `cancel_or_edit`, and `none`.
- Planned runs should recommend `/workflow continue <run_id>`.
- Completed or terminal runs should recommend `/workflow trace <run_id>` and optional rerun through `/workflow run <workflow-ref>`, never hidden continuation.
- Waiting approval runs with a pending approval row should recommend `/approve <approval_id>` or `/reject <approval_id>`, then `/workflow continue <run_id>`.
- Waiting approval runs with an approved or rejected approval row should recommend `/workflow continue <run_id>` so the existing continue command observes the human decision.
- Waiting agent-task runs with a non-terminal task row should recommend waiting and `/workflow trace <run_id>`.
- Waiting agent-task runs with a terminal task row, or blocked `agent_task` rows without a task id, should recommend `/workflow continue <run_id>` so the existing Workflow Agent Task Bridge owns dispatch/result handling.
- Condition or unsupported blockers should recommend trace/cancel/edit guidance, not pretend safe automatic progress exists.
- `workflows.py` remains pure. `workflow_run_next_action_projection(...)` and `format_workflow_run_next_action(...)` accept row lists as parameters and must not read files, import app/runtime/UI/governance owners, append JSONL rows, queue approvals, dispatch subagents, or call tools/providers.

### 4. Validation & Error Matrix

- Missing run id -> visible not-found message, no ledger writes.
- Unknown run id -> visible not-found message, no ledger writes.
- Missing or unknown run id through `next-json` / `diagnose-json` -> JSON object with `found:false`, no ledger writes.
- Latest row `planned` -> `next_action: continue`, command `/workflow continue <run_id>`.
- Latest row `completed` -> `next_action: none`, command `/workflow trace <run_id>`, no continue recommendation.
- Latest row terminal failed/rejected/cancelled/canceled/aborted -> `next_action: inspect_trace`, command `/workflow trace <run_id>`, no continue recommendation.
- Latest row `waiting_approval` plus pending approval row -> `next_action: approve_or_reject`, commands `/approve <approval_id>`, `/reject <approval_id>`, and `/workflow continue <run_id>`.
- Latest row `waiting_approval` plus approved/rejected approval row -> `next_action: continue`, command `/workflow continue <run_id>`.
- Latest row `waiting_task` plus non-terminal task row -> `next_action: wait_task`, command `/workflow trace <run_id>`, no duplicate dispatch.
- Latest row `waiting_task` plus terminal task row -> `next_action: continue`, command `/workflow continue <run_id>`.
- Latest row blocked by condition/unsupported step -> `next_action: cancel_or_edit`, commands `/workflow trace <run_id>` and `/workflow cancel <run_id> <reason>`.
- JSON projection commands must be plain command strings such as `/workflow continue <run_id>`, not bullet-prefixed human lines.

### 5. Good/Base/Bad Cases

- Good: `/workflow next wfr_...` on a pending approval shows the approval id and only tells the user to approve/reject through existing approval commands.
- Good: `/workflow next-json wfr_...` on the same pending approval returns `{"next_action":"approve_or_reject","approval":{"approval_id":"appr_...","status":"pending"},"commands":["/approve appr_...","/reject appr_...","/workflow continue wfr_..."]}`.
- Good: `/workflow diagnose wfr_...` on a working subagent task shows the task id/status and recommends waiting plus trace inspection.
- Good: A completed workflow reports `next_action: none` and uses trace/rerun guidance instead of trying to continue a terminal run.
- Base: Diagnostics are command-stream text projections. A future panel or A2A/MCP gateway can reuse the pure formatter or expose the same classification as structured data.
- Bad: `/workflow next <run_id>` calls `continue_workflow_run_v0(...)` to refresh the run before rendering.
- Bad: `/workflow diagnose <run_id>` appends a trace row or approval row saying diagnostics were viewed.
- Bad: `/workflow next-json <run_id>` returns text embedded inside a JSON string instead of structured fields.
- Bad: `workflow_run_next_action_projection(...)` imports `app.py` to call `terminal_task_status(...)` or read ledger paths.

### 6. Tests Required

- `tests/test_workflows.py` must assert missing-run formatting, planned/completed/terminal classifications, pending and approved approval classifications, non-terminal and terminal task classifications, condition-blocked classification, command suggestions, JSON schema fields, text/JSON source-of-truth reuse, and app command read-only behavior for `/workflow next|diagnose|next-json|diagnose-json`.
- `scripts/check_policy_gates.py` must assert command aliases route to the pure projection/formatter, the app reads workflow/task/approval ledgers only for projection, diagnostics append no workflow/task/progress/approval/artifact/trace rows, and `workflows.py` remains side-effect-free.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow next wfr_123 -> continue_workflow_run_v0(...) -> dispatches the blocked subagent task
/workflow next-json wfr_123 -> {"message":"Workflow next action: ..."}
```

#### Correct

```text
/workflow next wfr_123 -> read ledgers -> format_workflow_run_next_action(...) -> suggest /workflow continue wfr_123
/workflow next-json wfr_123 -> read ledgers -> workflow_run_next_action_projection(...) -> {"next_action":"continue","commands":["/workflow continue wfr_123"],"rows_appended":false}
```

## Scenario: Workflow Autopilot Tick V1

### 1. Scope / Trigger

- Trigger: Users want Shuheng to automatically advance workflow runs that are already safe to continue, without turning workflows into an unbounded executor or bypassing human/task gates.
- Applies to: `/workflow tick`, `/workflow autopilot`, `workflows.workflow_autopilot_tick_plan(...)`, `workflows.format_workflow_autopilot_tick_plan(...)`, `app.parse_workflow_tick_command_args(...)`, `app.run_workflow_autopilot_tick(...)`, `app.continue_workflow_run_v0(...)`, `workflow_runs.jsonl`, `workflow_events.jsonl`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: This does not add a daemon, background thread, timer, watcher, cron loop, workflow-owned executor, direct model/tool/shell/plugin-code execution, approval bypass, Secret Vault workflow execution, parallel/fan-out/fan-in scheduler, or A2A/MCP workflow service exposure.

### 2. Signatures

- Public commands:
  - `/workflow tick [--dry-run] [--limit N] [run-id ...]`
  - `/workflow autopilot [--dry-run] [--limit N] [run-id ...]`
- Pure projection:
  - `workflows.workflow_autopilot_tick_plan(workflow_rows, task_rows=..., approval_rows=..., run_ids=None, limit=25) -> dict`
- Pure formatter:
  - `workflows.format_workflow_autopilot_tick_plan(plan, dry_run=False, continued_count=0, event_count=0) -> str`
- JSON schema:
  - `schema_version: "shuheng.workflow_autopilot_tick.v1"`
  - `candidate_count`, `considered_count`, `selected_count`, `skipped_count`, `limit`, `run_ids`, `items`, `read_only`, and `rows_appended`.
- App owner:
  - `app.run_workflow_autopilot_tick(...)` reads ledgers, executes only selected items through `continue_workflow_run_v0(...)`, appends workflow event rows, and renders the bounded result.

### 3. Contracts

- The pure tick plan must derive each item from `workflow_run_next_action_projection(...)` so autopilot and diagnostics cannot drift.
- The only selected runs are those with `next_action == "continue"`.
- Runs with `next_action == "approve_or_reject"`, `wait_task`, `cancel_or_edit`, `inspect_trace`, or `none` must be skipped with a visible reason and command guidance where available.
- `/workflow tick --dry-run` must append no workflow, task, progress, approval, artifact, trace, or workflow event rows.
- Mutating `/workflow tick` and `/workflow autopilot` may append workflow event rows for selected/skipped/continued/no-progress/summary audit events.
- Mutating tick must call `continue_workflow_run_v0(run_id, state=state)` for actual progression. It must not duplicate runner, approval bridge, agent-task bridge, retry, or condition logic.
- Approval creation, approval decision application, subagent task dispatch, task retry, task-result application, and safe-step advancement remain owned by the existing app Orchestrator bridge functions.
- Pending approvals must remain pending until `/approve` or `/reject` changes the approval row. Tick must not self-approve or reject.
- Non-terminal subagent tasks must remain waiting. Tick must not dispatch duplicates for a working task.
- Completed and terminal runs must be skipped without calling continue.
- `workflows.py` remains pure. It may project and format tick plans from row lists, but must not read files, import app/runtime/UI/governance owners, append JSONL rows, queue approvals, dispatch subagents, or call tools/providers.

### 4. Validation & Error Matrix

- No workflow runs -> tick reports zero considered and appends no events.
- Planned run -> selected, then app mutating tick calls `/workflow continue` bridge semantics for that run.
- Waiting approval with pending approval row -> skipped with approval id/status and approve/reject command guidance; no workflow run row appended for that run.
- Waiting approval with approved/rejected approval row -> selected; actual decision handling remains inside `continue_workflow_run_v0(...)`.
- Waiting task with working task row -> skipped with task id/status; no duplicate task dispatch.
- Waiting task with terminal task row -> selected; actual result/retry handling remains inside `continue_workflow_run_v0(...)`.
- Blocked condition/unsupported step -> skipped with cancel/edit guidance.
- Completed run -> skipped as `next_action:none`.
- Failed/rejected/cancelled/aborted run -> skipped as `inspect_trace`.
- Invalid tick CLI option -> usage message, no mutation.

### 5. Good/Base/Bad Cases

- Good: `/workflow tick --dry-run` shows that one planned run would continue and one approval run would be skipped, with no ledger changes.
- Good: `/workflow autopilot` continues only the selected planned/approved/task-terminal runs and appends audit events.
- Good: A pending approval remains pending after tick and still requires `/approve <approval_id>` or `/reject <approval_id>`.
- Base: Tick is an explicit user command, not an always-on worker. A future scheduler can call the same app helper after its own governance gate.
- Bad: Tick scans workflow rows and directly calls `advance_workflow_run_v0(...)`, bypassing app-owned approval and task bridge behavior.
- Bad: Tick auto-approves a pending approval because the workflow definition says it is safe.
- Bad: Tick dispatches another subagent task while the existing task row is still `working`.
- Bad: `workflows.workflow_autopilot_tick_plan(...)` imports `app.py` or reads JSONL files.

### 6. Tests Required

- `tests/test_workflows.py` must assert pure plan selection/skipping, dry-run no-mutation behavior, mutating tick continuation, skipped approval/task/terminal behavior, command alias, and event append behavior.
- `scripts/check_policy_gates.py` must assert `/workflow tick` and `/workflow autopilot` exist, the pure plan helper consumes `workflow_run_next_action_projection(...)`, app execution calls `continue_workflow_run_v0(...)`, dry-run appends no rows, pending approvals/tasks are skipped, mutating tick appends audit events, and `workflows.py` purity holds.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow tick -> advance_workflow_run_v0(...) directly -> dispatch task / approve gate from tick logic
```

#### Correct

```text
/workflow tick -> workflow_autopilot_tick_plan(...) -> selected next_action=continue -> continue_workflow_run_v0(...)
```

## Scenario: Workflow Run Panel V1

### 1. Scope / Trigger

- Trigger: Users enter `/workflows` and need to inspect both workflow definitions and active/completed workflow runs from the TUI panel instead of command output only.
- Applies to: `/workflows`, `open_harness_panel(..., "workflows")`, `PanelItem`, `app.workflow_panel_items(...)`, `app.workflow_run_panel_items(...)`, `app.workflow_panel_run_action(...)`, `workflow_runs.jsonl`, `workflows.latest_workflow_run_rows(...)`, `workflows.workflow_run_step_counts(...)`, `workflows.workflow_run_stop_reason(...)`, `workflows.format_workflow_run_detail(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: The panel does not create a new workflow executor, edit workflow definitions, visualize a graph canvas, prompt for custom cancel reasons, retry/timeout/schedule runs, auto-approve approvals, dispatch Secret Vault work, execute plugin code, call tools/providers directly, mutate plugin files, prompt for optional/custom run inputs when required inputs are already satisfied, or expose A2A/MCP workflow services.

### 2. Signatures

- Panel entry command:
  - `/workflows`
- Definition rows:
  - `PanelItem.payload.item_type = "workflow_definition"` for valid workflow definition rows.
  - `PanelItem.payload.workflow_ref`
- Run rows:
  - `PanelItem.key = "workflow-run:<run_id>"`
  - `PanelItem.payload.item_type = "workflow_run"`
  - `PanelItem.payload.run_id`
  - `PanelItem.payload.workflow_ref`
  - `PanelItem.payload.status`
  - `PanelItem.payload.history_rows`
  - `PanelItem.payload.steps_completed`
  - `PanelItem.payload.steps_total`
- Panel action helper:
  - `app.workflow_panel_run_action(state, item, "continue"|"resume"|"cancel") -> str`
- Pure run projection helpers:
  - `workflows.latest_workflow_run_rows(rows)`
  - `workflows.workflow_run_step_counts(row)`
  - `workflows.workflow_run_stop_reason(row)`

### 3. Contracts

- `/workflows` must keep using the existing harness panel browser route.
- `workflow_panel_items()` must include manifest-backed workflow definition rows and latest workflow run rows from `workflow_runs.jsonl`.
- Definition row detail must expose the matching `/workflow info`, `/workflow dry-run`, and `/workflow run` commands, plus the Enter/c panel run action.
- Run rows must be latest-row projections grouped by `run_id` in recent-first ledger order.
- Run row list text must show run id, latest status, workflow ref, completed/total step count, and update timestamp when present.
- Run row detail must reuse `format_workflow_run_detail(...)` so it shows history rows, workflow ref, timestamps, execution counters, approval metadata, per-step status, task ids, approval ids, agent ids, artifact refs, and errors.
- Pressing Enter or `c` on a valid workflow definition row must reload that workflow through `workflow_load_result_for_ref(workflow_ref, user_plugin_registry(force=True))` and may call only `create_workflow_run_v0(result, state=state, source_command=f"/workflows panel run {workflow_ref}")`.
- Definition-row execution must append only the normal workflow run rows produced by `create_workflow_run_v0(...)`. It must not build workflow rows directly, bypass manifest refs, mutate plugin files, duplicate runner logic, or create a second panel-specific executor.
- Safe definition rows with default inputs may complete immediately. Definitions that need missing inputs, approval, agent-task dispatch, or validation handling must use the existing runner/bridge behavior and visible messages from `create_workflow_run_v0(...)`.
- Pressing Enter or `c` on a run row may call only `continue_workflow_run_v0(run_id, state=state)`.
- Pressing `x` on a run row may call only `cancel_workflow_run_v0(run_id, reason="cancelled from workflow panel")`.
- Pressing `x` on a definition row must be a visible no-op and append no workflow run row.
- Pressing run action keys on issue or empty rows must be a visible no-op and append no workflow run row.
- Refreshing the workflow panel may clear the plugin registry cache and reread workflow ledgers, but must not advance, cancel, dispatch, approve, reject, or mutate task/progress/approval/artifact ledgers.
- `workflows.py` remains pure. The new projection helpers may read dictionaries passed to them, but must not import app/runtime/UI/governance owners, append JSONL rows, queue approvals, dispatch subagents, or call tools/providers.

### 4. Validation & Error Matrix

- No workflow definitions and no workflow runs -> existing no-workflows empty row.
- Valid definitions and no runs -> definition rows only; Enter/c on a safe defaulted definition starts a normal workflow run.
- Existing workflow run rows -> latest run rows are included after definition/issue rows.
- Multiple rows for the same run id -> exactly one panel row for that run id, with `history_rows` equal to the append-only row count.
- Run with artifact refs -> detail includes top-level and per-step artifact refs.
- Enter/c on a safe definition row with defaults -> planned + advanced workflow rows are appended through `create_workflow_run_v0(...)`, with no task/progress/approval/artifact side-effect ledgers for safe workflows.
- Enter/c on a definition row that requires missing inputs or has validation issues -> visible runner rejection and no workflow run row.
- x on a definition row -> visible no-op and no workflow run row.
- x on a non-terminal run row -> append at most one cancelled workflow row through the existing cancel helper.
- Enter/c on a terminal run row -> existing continue helper reports already terminal/completed and appends no row.

### 5. Good/Base/Bad Cases

- Good: `/workflows` shows `Run · wfr_...` with `waiting_task · steps:1/3 · plugin://...` and a detail pane containing the subagent `task_id`.
- Good: Pressing Enter on `plugin://shuheng-examples/workflows/daily-briefing` reloads it through the manifest registry and appends the same planned/completed rows as `/workflow run shuheng-examples/daily-briefing`.
- Good: Pressing `x` on a blocked run appends one `cancelled` workflow row and leaves task/progress/approval/artifact ledgers untouched.
- Good: Pressing Enter on a run waiting for an already completed task delegates to `continue_workflow_run_v0(...)`, which owns artifact-copy and runner-v0 continuation semantics.
- Base: The panel remains a text/list browser; richer graph visualization can reuse the same run projections later.
- Bad: The panel directly mutates step statuses or appends workflow rows without `continue_workflow_run_v0(...)` / `cancel_workflow_run_v0(...)`.
- Bad: The panel starts a definition row by constructing a workflow run dictionary itself or resolving a plugin path without the manifest-backed loader.
- Bad: The panel starts a subagent, creates an approval, or interprets a workflow condition itself.
- Bad: `workflows.py` imports `PanelItem`, curses, `State`, `app.py`, or ledger/runtime owners.

### 6. Tests Required

- `tests/test_workflows.py` must assert workflow panel items include definition rows plus run rows, run payload shape, history row count, detail content, artifact refs, definition-row Enter/c run through the existing runner, definition-row safe runs do not write task/progress/approval/artifact ledgers, cancel delegation, and already-terminal continue no-op after cancellation.
- `scripts/check_policy_gates.py` must assert `/workflows` panel route exposes run rows after `/workflow run`, panel run actions delegate to existing helpers, definition-row Enter/c starts a safe workflow through `create_workflow_run_v0(...)`, definition-row safe runs do not write side-effect ledgers, cancel appends at most one row through the existing helper, and `workflows.py` remains side-effect-free.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflows panel x -> manually sets row["status"]="cancelled" and writes workflow_runs.jsonl
```

#### Correct

```text
/workflows panel x -> workflow_panel_run_action(...) -> cancel_workflow_run_v0(run_id, reason="cancelled from workflow panel")
```

#### Correct

```text
/workflows panel Enter on workflow definition -> workflow_load_result_for_ref(...) -> create_workflow_run_v0(...)
```

## Scenario: Workflow Panel Run Input Prompt V1

### 1. Scope / Trigger

- Trigger: Users run a manifest-backed workflow definition from `/workflows`, and the definition has required inputs with no defaults.
- Applies to: `/workflows`, `open_harness_panel(..., "workflows")`, `PanelItem` definition rows, `app.workflow_panel_continue_action(...)`, `app.workflow_panel_definition_load_result(...)`, `app.workflow_panel_required_input_ids(...)`, `app.workflow_panel_input_prompt_lines(...)`, `app.parse_workflow_panel_input_tail(...)`, `app.open_workflow_run_input_prompt(...)`, `app.workflow_panel_run_action(..., inputs=...)`, `workflow_helpers.resolve_workflow_run_inputs(...)`, `parse_workflow_run_command_args(...)`, `create_workflow_run_v0(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: The prompt is not a graph editor, multi-field form system, optional-input editor, plugin mutator, workflow executor, approval bypass, Secret Vault UI, tool runner, provider call path, scheduler, or A2A/MCP workflow service.

### 2. Signatures

- Panel action route:
  - `app.workflow_panel_continue_action(stdscr, state, item) -> str`
- Definition loader:
  - `app.workflow_panel_definition_load_result(item) -> workflow_helpers.WorkflowLoadResult`
- Required-input projection:
  - `app.workflow_panel_required_input_ids(result) -> tuple[str, ...]`
- Prompt copy:
  - `app.workflow_panel_input_prompt_lines(result) -> list[str]`
- Prompt parser:
  - `app.parse_workflow_panel_input_tail(workflow_ref, text) -> tuple[dict[str, Any], str]`
- Modal entry:
  - `app.open_workflow_run_input_prompt(stdscr, state, result) -> dict[str, Any] | None`
- Existing runner bridge:
  - `app.workflow_panel_run_action(state, item, "continue", inputs=inputs)`
  - `create_workflow_run_v0(result, state=state, inputs=inputs, source_command=f"/workflows panel run {workflow_ref}")`

### 3. Contracts

- Definition row detail must list required run input ids. If none are required, it must show an explicit none value rather than hiding the field.
- Pressing Enter or `c` on a workflow definition row must reload the workflow through `workflow_panel_definition_load_result(...)`, which in turn must use `workflow_load_result_for_ref(workflow_ref, user_plugin_registry(force=True))`.
- If `workflow_panel_required_input_ids(result)` returns an empty tuple, the panel must run immediately through `workflow_panel_run_action(...)` and must not open an input prompt.
- If required inputs are missing, the panel must open a panel-local prompt that accepts the same key/value tail grammar as `/workflow run`.
- Prompt parsing must call `parse_workflow_run_command_args(...)` by prepending the workflow ref to the user-entered tail. The panel must not introduce a second input grammar.
- Prompt submission must validate required inputs with `workflow_helpers.resolve_workflow_run_inputs(...)` before closing the modal. The final authority remains `create_workflow_run_v0(...)`; the modal validation is only user-facing convenience.
- A submitted prompt must call `workflow_panel_run_action(..., inputs=parsed_inputs)`, and the run action must call only `create_workflow_run_v0(...)` for definition rows.
- Cancelling the prompt with Escape, Ctrl-C, or equivalent must return `None`, render a visible cancellation message, and append no workflow run row.
- Parse or validation errors must remain visible inside the prompt and must not append workflow/task/progress/approval/artifact rows.
- The prompt must not create, continue, cancel, approve, reject, or dispatch workflow runs itself. It only collects input for the existing runner.
- The prompt must not mutate plugin files, workflow definition files, user registry state beyond the existing forced reload path, task/progress/approval/artifact ledgers, memory, or Secret Vault.

### 4. Validation & Error Matrix

- Definition has no missing required inputs -> no prompt opens; `create_workflow_run_v0(...)` receives `inputs={}` through the existing panel run action.
- Definition has one required input with no default -> prompt opens; definition row detail includes that input id.
- User enters valid `key=value` pairs -> parser returns typed inputs from the existing `/workflow run` grammar, and `create_workflow_run_v0(...)` receives the parsed dictionary.
- User enters malformed input such as a bare key -> visible parse error, prompt remains open, and no ledger is appended.
- User omits a required input -> visible resolver issue, prompt remains open, and no ledger is appended.
- User cancels prompt -> visible cancellation message, no workflow run row, no task row, no progress row, no approval row, and no artifact row.
- Existing runner rejects inputs after prompt validation -> runner message is surfaced by `workflow_panel_run_action(...)`; no panel-specific fallback row is written.

### 5. Good/Base/Bad Cases

- Good: Pressing Enter on `plugin://research-pack/workflows/input-flow` opens a key/value prompt for `ready`, accepts `ready=true mode="panel"`, and appends normal planned/completed workflow rows through `create_workflow_run_v0(...)`.
- Good: Pressing Escape in the prompt returns `Workflow run input prompt cancelled. No workflow run was started.` and leaves every ledger count unchanged.
- Base: The prompt is a single text input, not a generated form. This keeps `/workflow run` and `/workflows` on the same grammar.
- Bad: The prompt writes `workflow_runs.jsonl` directly after parsing inputs.
- Bad: The panel accepts a separate JSON/YAML input syntax that `/workflow run` does not understand.
- Bad: The prompt creates task, progress, approval, or artifact rows before `create_workflow_run_v0(...)` receives the inputs.

### 6. Tests Required

- `tests/test_workflows.py` must assert required input ids appear in definition detail, prompt lines list required inputs, prompt parser reuses the `/workflow run` grammar for typed values, invalid syntax returns a visible parse error, cancelled prompts append no workflow/task/progress/approval/artifact rows, and prompted runs call the existing runner with parsed inputs.
- `scripts/check_policy_gates.py` must assert the source contains the prompt/action ownership helpers, a manifest-backed workflow with missing required inputs opens the prompt path, cancel is side-effect-free, valid prompted inputs append normal workflow rows through the existing runner, and side-effect ledgers remain unchanged for safe prompted workflows.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflows panel prompt -> parse custom JSON -> append workflow_runs.jsonl directly
```

#### Correct

```text
/workflows panel prompt -> parse_workflow_run_command_args(...) -> create_workflow_run_v0(...)
```

## Scenario: Workflow Continue Command

### 1. Scope / Trigger

- Trigger: Users need to resume a durable append-only workflow run from its latest `workflow_runs.jsonl` row.
- Applies to: `/workflow continue <run_id>`, `/workflow resume <run_id>`, `workflow_runs.jsonl`, `shuheng.workflow_run.v1`, `workflows.WorkflowRunContinueResult`, `workflows.workflow_run_has_meaningful_transition(...)`, `workflows.format_workflow_continue_result(...)`, `app.continue_workflow_run_v0(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: Continue commands do not call model providers directly, execute tools, run shell commands, execute plugin code, evaluate free-form condition expressions, write workflow-owned artifacts, write memory, touch Secret Vault, schedule work, or expose A2A/MCP workflow services. Approval rows and subagent task rows may be created only through the separate Workflow Approval Bridge and Workflow Agent Task Bridge contracts.

### 2. Signatures

- Public commands:
  - `/workflow continue <run_id>`
  - `/workflow resume <run_id>`
- App ownership:
  - `app.continue_workflow_run_v0(run_id)` reads all workflow run rows, selects the latest row for the run id by ledger order, and appends at most one advanced row.
- Pure helper ownership:
  - `workflows.workflow_run_has_meaningful_transition(before, after)`
  - `workflows.format_workflow_continue_result(result)`
  - `workflows.WorkflowRunContinueResult(...)`
- Runner ownership:
  - `workflows.advance_workflow_run_v0(row, timestamp=...)` remains the only runner-v0 state transition helper.

### 3. Contracts

- `/workflow continue <run_id>` must resume from the latest row for the given `run_id`, not from the first row and not from a user-supplied workflow ref.
- Unknown or blank run id must render a not-found message and append no workflow run row.
- A latest row with `status=completed` must render an already-completed message and append no workflow run row.
- A latest row with terminal status `failed`, `rejected`, `cancelled`, `canceled`, or `aborted` must render an already-terminal message and append no workflow run row.
- A latest row that cannot make runner-v0 safe progress must render a no-progress message and append no workflow run row.
- A latest row that can make runner-v0 safe progress must append exactly one new row with the same `run_id`.
- Meaningful continuation is defined by status, completed/error state, step status/artifact/approval/task/error fields, blocked-step metadata, or approval metadata changing. Timestamp-only updates are not meaningful and must not create a duplicate row.
- Continue uses runner-v0 semantics for safe steps and condition v1 predicates; `approval` and `agent_task` blockers are delegated to their bridge contracts, while unsupported/string conditions, unsupported step types, and unmet dependencies still block.
- Continue output must report whether a row was appended, latest status, safe-step count when progressed, history row count, and stop reason when present.
- Continue must not mutate task/progress/artifact ledgers or change `state.subagents` except through the Workflow Agent Task Bridge. Approval-ledger writes are allowed only for the Workflow Approval Bridge.
- `workflows.py` remains pure and must not import `app.py`, curses, runtime dispatch, approval queues, task/progress ledgers, artifacts, provider adapters, governance owners, Secret Vault, or subprocess.

### 4. Validation & Error Matrix

- Missing run id -> visible not-found message, no row append.
- Unknown run id -> visible not-found message, no row append.
- Latest row already completed -> visible already-completed message, no row append.
- Latest row already failed/rejected/cancelled/canceled/aborted -> visible already-terminal message, no row append.
- Latest row blocked at `agent_task` without a `task_id` -> delegated to the Workflow Agent Task Bridge; a successful dispatch appends one `waiting_task` workflow row with the new `task_id`.
- Latest row waiting at `agent_task` with a non-terminal `task_id` -> visible waiting message, no workflow row append, no duplicate subagent/task dispatch.
- Latest row waiting at `agent_task` with a completed task row -> append one workflow row that marks the step completed, copies artifact refs, and then advances later runner-v0 safe steps.
- Latest row waiting at `agent_task` with a failed/rejected/cancelled task row and no remaining retry attempts -> append one terminal workflow row and do not continue later steps.
- Latest row waiting at `agent_task` with a failed/rejected/cancelled task row and remaining retry attempts -> prepare one retry row and dispatch the next attempt only through the Workflow Agent Task Bridge.
- Latest row waiting at `approval` -> handled by the Workflow Approval Bridge contract below; it must not self-approve or skip the human gate.
- Latest row planned with safe steps -> append exactly one runner-v0 row and complete safe steps until completion or first blocked step.
- Latest row with timestamp-only runner-v0 output -> no workflow row append.

### 5. Good/Base/Bad Cases

- Good: A planned safe-only run continued with `/workflow continue wfr_...` appends one completed row and leaves side-effect ledgers empty.
- Good: A planned run with `prompt -> agent_task` may append one `waiting_task` row after dispatching through the Workflow Agent Task Bridge.
- Good: Continuing a `waiting_task` row while the task is still `working` reports the current task status and appends no duplicate row.
- Base: `/workflow resume <run_id>` is a command alias for `/workflow continue <run_id>`.
- Base: The approval bridge may create or observe a real approval row; this command can then advance only later runner-v0 safe steps after the approval row is approved.
- Bad: Continuing a blocked `agent_task` run creates a workflow-owned executor or writes task/progress rows outside `start_subagent_task_structured(...)`.
- Bad: Continuing a `waiting_approval` run self-approves, bypasses `/approve`, or creates duplicate approval rows for the same bridged step.
- Bad: Continuing an unchanged blocked row appends another row only to update timestamps.

### 6. Tests Required

- `tests/test_workflows.py` must assert meaningful-transition detection, continuation formatting, planned run continuation, completed no-op, terminal failed/rejected/cancelled no-op, unknown run no-op, condition blocked no-progress, alias behavior, bridged agent-task continuation, and side-effect ledger invariants.
- `scripts/check_policy_gates.py` must assert continue/resume can advance a planned row, keeps condition rows side-effect-free, appends at most one workflow row per explicit continue, never duplicate-dispatches an existing `task_id`, treats completed/terminal workflow rows as no-op, and routes agent-task side effects only through the Workflow Agent Task Bridge. Approval-ledger changes must be covered by the Workflow Approval Bridge tests below.
- Keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, targeted pytest, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow continue wfr_123 -> starts a hidden workflow executor that writes tasks.jsonl/progress.jsonl directly
```

#### Correct

```text
/workflow continue wfr_123 -> either advances safe runner-v0 state or delegates approval/agent_task blockers to their bridge contracts
```

## Scenario: Workflow Cancel Command V1

### 1. Scope / Trigger

- Trigger: Users need an explicit manual terminal lifecycle control for a durable append-only workflow run.
- Applies to: `/workflow cancel <run_id> [reason...]`, `workflow_runs.jsonl`, `shuheng.workflow_run.v1`, `workflows.WorkflowRunCancelResult`, `workflows.cancel_workflow_run_v0(...)`, `workflows.format_workflow_cancel_result(...)`, `app.cancel_workflow_run_v0(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: Cancel does not abort running subagent tasks, kill subprocesses, reject approval rows, retry steps, schedule cleanup hooks, run plugin code, hydrate artifacts, checkpoint/replay, expose A2A/MCP workflow services, or continue later steps.

### 2. Signatures

- Public command:
  - `/workflow cancel <run_id> [reason...]`
- Pure helper ownership:
  - `workflows.cancel_workflow_run_v0(row, *, timestamp, reason="") -> WorkflowRunCancelResult`
  - `workflows.format_workflow_cancel_result(result) -> str`
- App ownership:
  - `app.cancel_workflow_run_v0(run_id, reason="")` reads all workflow run rows, selects the latest row for the run id by ledger order, and appends at most one cancelled row.

### 3. Contracts

- `/workflow cancel <run_id>` must target a workflow run id, not a workflow definition ref.
- Unknown or blank run id must render a not-found message and append no workflow run row.
- A latest row with `status=completed` must render an already-completed message and append no workflow run row.
- A latest row with terminal status `failed`, `rejected`, `cancelled`, `canceled`, or `aborted` must render an already-terminal message and append no workflow run row.
- A latest non-terminal row must append exactly one new row with the same `run_id`, canonical top-level `status=cancelled`, `completed_at`, `updated_at`, and a human-readable cancellation reason.
- If the latest row has a current blocked or waiting step, that step may be marked `cancelled`; later pending steps must remain pending and must not be advanced.
- Cancel must not call `advance_workflow_run_v0(...)` in a way that continues safe steps after the cancellation request.
- Cancel must not dispatch subagents, create approval rows, call model providers, execute tools, run shell commands, execute plugin code, write workflow-owned artifacts, mutate task/progress/approval/artifact ledgers, write memory, touch Secret Vault, or change `state.subagents`.
- `workflows.py` remains pure and must not import `app.py`, curses, runtime dispatch, approval queues, task/progress ledgers, artifacts, provider adapters, governance owners, Secret Vault, or subprocess.
- `app.py` remains the Orchestrator owner for latest-row lookup and append-only workflow ledger writes.

### 4. Validation & Error Matrix

- Missing run id -> visible not-found message, no row append.
- Unknown run id -> visible not-found message, no row append.
- Latest row already completed -> visible already-completed message, no row append.
- Latest row already failed/rejected/cancelled/canceled/aborted -> visible already-terminal message, no row append.
- Latest row planned with only pending steps -> append one top-level `cancelled` row without marking pending steps completed.
- Latest row blocked at `condition` -> append one `cancelled` row, mark the current blocked condition step `cancelled`, leave later pending steps pending.
- Latest row waiting at `approval` -> append one `cancelled` workflow row only; do not reject, approve, or delete approval rows.
- Latest row waiting at `agent_task` -> append one `cancelled` workflow row only; do not abort the underlying task, delete task rows, or duplicate-dispatch.

### 5. Good/Base/Bad Cases

- Good: `/workflow cancel wfr_... no longer needed` appends one terminal row and later `/workflow continue wfr_...` reports already terminal.
- Good: A cancelled run remains visible through `/workflow runs` and `/workflow show <run_id>` with append-only history.
- Good: Cancelling a workflow waiting on a subagent task stops workflow continuation while the governed task ledger remains the source of truth for the underlying task.
- Base: Later task-abort, cleanup hooks, retry, timeout, and checkpoint/replay features can build on this terminal run-state primitive.
- Bad: Cancel calls `start_subagent_task_structured(...)`, `decide_approval(...)`, or any task/progress/artifact ledger writer.
- Bad: Cancel advances pending safe steps before marking the run cancelled.
- Bad: `workflows.py` reads `workflow_runs.jsonl` or imports app/runtime modules to perform cancellation.

### 6. Tests Required

- `tests/test_workflows.py` must assert pure cancellation marks only the current blocked/waiting step and leaves future pending steps pending.
- `tests/test_workflows.py` must assert `/workflow cancel <run_id>` appends exactly one cancelled row for a non-terminal run.
- `tests/test_workflows.py` must assert unknown, completed, and already-terminal runs are no-op.
- `tests/test_workflows.py` must assert cancellation leaves task/progress/approval/artifact ledgers and `state.subagents` unchanged.
- `scripts/check_policy_gates.py` must assert the command exists, the pure helper/formatter exist, `workflows.py` remains side-effect-free, cancel appends at most one workflow row, and no side-effect ledgers change.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow cancel wfr_123 -> kills the subagent task, rejects approvals, advances notify, and writes progress rows
```

#### Correct

```text
/workflow cancel wfr_123 -> appends one workflow_runs.jsonl row with status=cancelled and leaves other ledgers untouched
```

## Scenario: Workflow Agent Task Bridge

### 1. Scope / Trigger

- Trigger: Workflow `agent_task` steps must run real AI work without bypassing Shuheng's governed subagent task pipeline.
- Applies to: `/workflow run <ref>`, `/workflow continue <run_id>`, `/workflow resume <run_id>`, `workflow_runs.jsonl`, `tasks.jsonl`, `progress.jsonl`, result artifacts, `shuheng.workflow_run.v1`, plugin agent template refs, `workflows.py` pure task-state helpers, and `app.py` Orchestrator bridge helpers.
- Non-goal: The bridge does not create a workflow-owned executor, evaluate `condition`, run parallel/fan-out/fan-in graphs, own event-driven auto-continuation, add timeout/scheduling, dispatch Secret Vault subagents, call tools/providers directly, or expose A2A/MCP workflow services. Retry policy belongs only to the Workflow Retry Policy V1 contract below. Event-driven continuation after terminal task ledger writes belongs only to the Workflow Auto-Continue Event Bridge below.

### 2. Signatures

- Supported step type: `agent_task`.
- Supported target refs:
  - Existing subagent id/name through `resolve_subagent(state, step["agent"])`.
  - Plugin agent template ref through `plugin://<plugin-id>/agents/<template-id>`.
- Workflow step snapshot fields:
  - `status`: `waiting_task`, `completed`, `failed`, `rejected`, or `cancelled` while the bridge owns the step.
  - `task_id`: the governed subagent task id returned by `start_subagent_task_structured(...)`.
  - `task_status`: latest task-ledger status observed by the workflow bridge.
  - `agent_id`: concrete subagent runtime id used for dispatch.
  - `artifact_refs`: artifact refs copied from the terminal task row.
- Pure helper ownership:
  - `workflows.pending_workflow_agent_task_step(row)`
  - `workflows.workflow_agent_task_id(row)`
  - `workflows.attach_workflow_agent_task(row, task_id, timestamp, agent_id="", task_status="working", message="")`
  - `workflows.fail_workflow_agent_task_dispatch(row, timestamp, error, status="failed")`
  - `workflows.apply_workflow_agent_task_result(row, task_row, timestamp)`
- App ownership:
  - `app.resolve_workflow_agent_task_subagent(state, step)` resolves existing subagents or plugin templates.
  - `app.bridge_workflow_agent_task(row, state, source_command)` dispatches through `start_subagent_task_structured(...)`.
  - `app.continue_workflow_run_v0(run_id, state=None)` observes `latest_task_records()` and appends at most one workflow row per explicit continue.
  - `app.auto_continue_workflows_for_agent_task(state, task_id, source=...)` may reuse `continue_workflow_run_v0(...)` only after the event bridge observes a terminal task ledger row.

### 3. Contracts

- Workflow `agent_task` execution authority is the existing subagent task pipeline. The workflow row stores only references and status snapshots; it must not duplicate task/progress/artifact ledgers.
- A `/workflow run` that reaches a bridgeable `agent_task` appends exactly two workflow rows: initial `planned`, then `waiting_task` with the returned `task_id`.
- A `/workflow continue` that reaches an unbridged `agent_task` may append one `waiting_task` row after dispatching exactly one subagent task.
- If a workflow step already has `task_id`, continuation must never call `start_subagent_task_structured(...)` again for that step.
- Non-terminal task statuses such as `working`, `running`, `pending`, `created`, `queued`, and `approval_required` must produce a visible waiting message and append no workflow row.
- Terminal `completed` task status must mark the step completed, copy `artifact_refs` into the step and top-level workflow row, then advance later runner-v0 safe steps.
- Terminal `failed`, `rejected`, `cancelled`, `canceled`, or `aborted` task status must append one terminal workflow row and leave later steps pending unless the Workflow Retry Policy V1 contract prepares a retry attempt and redispatches through this bridge.
- Plugin template refs may create one concrete subagent through `create_subagent_from_plugin_template(...)` at dispatch time.
- Secret Vault subagents are out of scope and must fail the workflow step visibly instead of dispatching.
- `workflows.py` remains pure and must not import app/runtime/UI/governance owners, append JSONL rows, queue approvals, dispatch subagents, or call tools/providers.
- `app.py` remains the strong Orchestrator owner for target resolution, template creation, policy gates, single-writer locks, task/progress ledgers, context packs, traces, checkpoints, mail, and result artifact provenance.

### 4. Validation & Error Matrix

- Missing `agent` target -> append one terminal failed workflow row with a visible error.
- `agent` target matches existing subagent -> dispatch exactly one governed subagent task.
- `agent` target matches plugin template ref -> create or reuse one scoped subagent, then dispatch exactly one governed subagent task.
- Target subagent is Secret Vault scoped -> append one terminal failed workflow row; no dispatch.
- Target subagent is already busy -> do not duplicate-dispatch; report blocked/no-progress until a later explicit continue can dispatch.
- Missing prompt/description/workflow fallback text -> append one terminal failed workflow row.
- Dispatch returns no `task_id` -> append one terminal failed workflow row.
- Existing `task_id` and missing task row -> visible no-progress message, no workflow row append.
- Existing non-terminal `task_id` -> visible waiting message, no workflow row append, no duplicate task/progress rows.
- Existing completed `task_id` -> append one completed/advanced workflow row and copy task artifact refs.
- Existing failed/rejected/cancelled `task_id` -> append one terminal workflow row and stop.

### 5. Good/Base/Bad Cases

- Good: `/workflow run research-pack/compare-sources` reaches `agent_task`, dispatches through `start_subagent_task_structured(...)`, writes normal task/progress rows, and stores the returned `task_id` in the workflow row.
- Good: `/workflow continue wfr_...` while the task is still `working` reports `task_pending` and appends no workflow row.
- Good: After `process_ui_queue(...)` records a completed subagent task with result artifacts, the Workflow Auto-Continue Event Bridge reuses `continue_workflow_run_v0(...)` to copy artifact refs and complete later safe steps such as `notify`.
- Good: A plugin `agent_task.agent = "plugin://research-pack/agents/evidence-researcher"` creates one concrete scoped subagent before dispatch.
- Base: Manual `/workflow continue` remains supported for already-waiting tasks, but subagent completion events may auto-resume only through the separate Workflow Auto-Continue Event Bridge.
- Base: Task `approval_required` is treated as non-terminal task waiting; the subagent policy gate remains the task pipeline's responsibility.
- Bad: Workflow code writes `tasks.jsonl` or `progress.jsonl` directly.
- Bad: `workflows.py` imports `app.py` to resolve subagents or read task ledgers.
- Bad: `/workflow continue` dispatches a second subagent task for a step that already has a `task_id`.
- Bad: The bridge treats many agents chatting as workflow success without task ids, artifact refs, ledgers, and auditable provenance.

### 6. Tests Required

- `tests/test_workflows.py` must assert `prompt -> agent_task -> notify` creates `planned` plus `waiting_task` rows, attaches `task_id`, writes real task/progress rows, reports pending without duplicate dispatch, completes after the task reaches `completed`, copies artifact refs, and advances later safe steps through the Workflow Auto-Continue Event Bridge.
- `tests/test_workflows.py` must assert failed subagent task termination leaves later workflow steps pending.
- `tests/test_workflows.py` must assert plugin template refs create a concrete subagent and do not duplicate-create or duplicate-dispatch on pending continue.
- `tests/test_workflows.py` must keep condition-step tests side-effect-free and approval bridge behavior unchanged.
- `scripts/check_policy_gates.py` must assert the bridge changes task/progress/artifact ledgers only through the governed subagent pipeline, never imports side-effect owners into `workflows.py`, and never duplicate-dispatches an existing `task_id`.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow continue wfr_agent -> workflow runner writes tasks.jsonl directly and starts a hidden executor
```

#### Correct

```text
/workflow continue wfr_agent -> app bridge calls start_subagent_task_structured(...), stores task_id, and later resumes from latest_task_records()
```

## Scenario: Workflow Step Output Artifact Context V1

### 1. Scope / Trigger

- Trigger: A workflow `agent_task` step is dispatched after earlier workflow steps have completed with task or artifact references.
- Applies to: `shuheng.workflow_run.v1`, per-step `task_id`, `agent_id`, and `artifact_refs`, `workflows.workflow_upstream_step_output_context(...)`, `workflows.format_workflow_step_output_context(...)`, `app.workflow_agent_task_prompt(...)`, `app.bridge_workflow_agent_task(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: This does not read artifact files, task output bodies, full subagent transcripts, model response text, Secret Vault plaintext, environment variables, tools, provider state, or arbitrary template expressions. It does not add retry, timeout, fan-out/fan-in, scheduling, webhook triggers, A2A/MCP workflow services, or a new workflow-owned executor.

### 2. Signatures

- Pure context record:
  - `workflows.WorkflowStepOutputContext(step_id, step_type, task_id="", agent_id="", artifact_refs=())`
- Pure collection helper:
  - `workflows.workflow_upstream_step_output_context(row, target_step) -> tuple[WorkflowStepOutputContext, ...]`
- Pure formatter:
  - `workflows.format_workflow_step_output_context(contexts) -> str`
- App-owned prompt wrapper:
  - `app.workflow_agent_task_prompt(row, step) -> str`
- Prompt context heading:
  - `Workflow upstream context (reference-only; artifact contents are not loaded):`

### 3. Contracts

- The workflow run row is the only source of upstream step context for this slice.
- Context includes only completed upstream steps with at least one reference field: `task_id`, `agent_id`, or `artifact_refs`.
- If the target step declares `depends_on`, context is scoped to completed dependency steps only, preserving workflow run step order.
- If the target step has no explicit `depends_on`, context falls back to completed prior steps before the target step in workflow run order.
- Duplicate artifact refs must be removed while preserving first-seen order.
- Missing upstream refs must produce no context block and must preserve the base prompt string exactly.
- `app.workflow_agent_task_prompt(...)` may append the formatted context block after the base prompt. It must not mutate the workflow row, dispatch a task, append ledgers, read artifacts, or evaluate a template language.
- `workflows.py` remains pure and must not import app/runtime/UI/governance owners, append JSONL rows, read task ledgers, dispatch subagents, read artifact files, or call tools/providers.

### 4. Validation & Error Matrix

- Target `agent_task` depends on a completed upstream `agent_task` with `task_id`, `agent_id`, and artifact refs -> downstream prompt includes the upstream step id, step type, task id, agent id, and deduped artifact refs.
- Target `agent_task` has explicit `depends_on=["collect"]` and another prior completed step exists -> context includes `collect` only.
- Target `agent_task` has no explicit dependencies -> context includes completed prior reference-bearing steps in run order.
- Upstream completed step has duplicate artifact refs -> formatted context contains each ref once.
- Upstream completed step has no `task_id`, no `agent_id`, and no artifact refs -> it contributes no context.
- Upstream step is pending, blocked, waiting, failed, rejected, cancelled, skipped, or aborted -> it contributes no context.
- Base prompt is empty -> the bridge still fails visibly through the existing missing-prompt path; context must not create a synthetic task prompt.

### 5. Good/Base/Bad Cases

- Good: First workflow `agent_task` completes and writes `artifact_refs`; a later explicit `/workflow continue <run_id>` dispatches the next `agent_task` with a reference-only context block.
- Good: The downstream task sees `artifact://...` refs and the upstream `task_id`, but not raw artifact file content or raw subagent result text.
- Good: Existing workflows with no upstream refs still dispatch the exact same prompt string as before.
- Base: The downstream agent may later request artifact hydration through governed artifact/tool paths; this slice only passes references.
- Base: Approval, condition, auto-continue, and workflow inspection behavior remain unchanged.
- Bad: The prompt wrapper opens an artifact path and inlines its content.
- Bad: The workflow runner writes a new task/progress/artifact ledger row only to represent context passing.
- Bad: `workflows.py` imports `app.py`, `ledger_store`, `runtime_dispatch`, `secret_vault`, `curses`, or `subprocess`.

### 6. Tests Required

- `tests/test_workflows.py` must assert pure context collection scopes explicit dependencies, falls back to prior completed steps when no dependencies are declared, dedupes artifact refs, and formats the reference-only block.
- `tests/test_workflows.py` must assert `app.workflow_agent_task_prompt(...)` preserves the base prompt exactly when no upstream refs exist.
- `tests/test_workflows.py` must assert a later workflow `agent_task` receives upstream `step_id`, `task_id`, `agent_id`, and artifact refs in the dispatched prompt after an earlier `agent_task` completes.
- `scripts/check_policy_gates.py` must assert the real app bridge injects reference-only context through `workflow_agent_task_prompt(...)`, routes dispatch through the governed subagent task pipeline, appends no workflow row during direct prompt bridging, and keeps `workflows.py` side-effect-free.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow continue wfr_review -> reads artifact://policy/upstream-report.md and pastes the file body into the next agent prompt
```

#### Correct

```text
/workflow continue wfr_review -> app prompt wrapper lists upstream task/artifact refs only, then dispatches through start_subagent_task_structured(...)
```

## Scenario: Workflow Auto-Continue Event Bridge

### 1. Scope / Trigger

- Trigger: `process_ui_queue(...)` processes a non-Secret `sub_stream` completion and the governed subagent task pipeline has already written the terminal task ledger row, result artifact refs, checkpoint, trace, eval rows, and user-visible result state.
- Applies to: `process_ui_queue(...)`, `latest_task_records()`, `latest_workflow_run_records()`, `workflow_runs.jsonl`, `tasks.jsonl`, result artifact refs, `app.workflow_run_ids_waiting_on_agent_task(...)`, `app.auto_continue_workflows_for_agent_task(...)`, `app.continue_workflow_run_v0(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: The bridge does not create a workflow-owned executor, dispatch subagents directly, run timers/schedulers, evaluate conditions, resume approval waits, self-approve, write workflow-owned artifacts, auto-continue Secret Vault subagents, run parallel/fan-out/fan-in graphs, or expose A2A/MCP workflow services. If a failed task is retried, the event bridge still delegates to `continue_workflow_run_v0(...)`; retry decision and redispatch are owned by the Workflow Retry Policy V1 contract and Workflow Agent Task Bridge.

### 2. Signatures

- Event source:
  - `app.process_ui_queue(state)` in the non-Secret `kind == "sub_stream"` terminal branch.
- App-owned helpers:
  - `app.workflow_run_ids_waiting_on_agent_task(task_id) -> list[str]`
  - `app.auto_continue_workflows_for_agent_task(state, task_id, source="subagent_task_completed") -> list[tuple[str, str]]`
  - `app.continue_workflow_run_v0(run_id, state=state)` remains the only helper that appends the advanced workflow row.
- Pure workflow helpers reused by `continue_workflow_run_v0(...)`:
  - `workflows.pending_workflow_agent_task_step(row)`
  - `workflows.apply_workflow_agent_task_result(row, task_row, timestamp)`
  - `workflows.advance_workflow_run_v0(row, timestamp=...)`
  - `workflows.format_workflow_continue_result(result)`
- User-visible notice kind: `workflow_auto_continue`.

### 3. Contracts

- The event bridge may run only after the terminal task ledger row exists for the completed subagent task id.
- The event bridge must find only latest workflow run rows whose pending `agent_task` step has the exact same `task_id`.
- The event bridge must call `continue_workflow_run_v0(run_id, state=state)` for each matched workflow run id instead of duplicating task-result, artifact-copy, or runner-v0 logic.
- A completed task result must append one workflow run row that marks the `agent_task` completed, copies `artifact_refs`, and advances later runner-v0 safe steps.
- A failed, rejected, cancelled, canceled, or aborted task result must append one terminal workflow run row and leave later workflow steps pending unless the latest workflow step has remaining retry attempts; retry must still happen only through `continue_workflow_run_v0(...)` and the Workflow Agent Task Bridge.
- If no workflow run is waiting on the task id, the event bridge must do nothing.
- If the latest workflow row is already terminal, the event bridge must append no row.
- If the task row is missing or non-terminal, the event bridge must append no row.
- The event bridge must not call `start_subagent_task_structured(...)`, create task/progress rows, create approval rows, mutate Secret Vault state, or alter `state.subagents` except for normal completed-task cleanup already owned by `process_ui_queue(...)`.
- The event bridge may add one system notice after a workflow row is appended so users can see that workflow continuation happened automatically.
- `workflows.py` remains pure and must not import app/runtime/UI/governance owners, append JSONL rows, read task ledgers, dispatch subagents, or call tools/providers.

### 4. Validation & Error Matrix

- Completed non-Secret subagent task whose `task_id` matches one latest `waiting_task` row -> append exactly one completed/advanced workflow row and add a `workflow_auto_continue` notice.
- Failed/rejected/cancelled/canceled/aborted non-Secret subagent task whose `task_id` matches one latest `waiting_task` row -> append exactly one terminal workflow row and add a `workflow_auto_continue` notice.
- Completed non-Secret subagent task whose `task_id` matches no latest workflow row -> no workflow row append and no auto-continue notice.
- Latest matched workflow row already `completed`, `failed`, `rejected`, `cancelled`, `canceled`, or `aborted` -> no workflow row append.
- Matched workflow row waits on the same `task_id` but latest task status is non-terminal -> no workflow row append.
- Secret Vault subagent task completion -> no workflow auto-continuation in this slice.
- Pending approval workflow row -> no auto-resume; `/workflow continue <run_id>` remains explicit after human approval.
- Auto-continued completed workflow followed by explicit `/workflow continue <run_id>` -> already-completed message and no extra row.
- Auto-terminated failed workflow followed by explicit `/workflow continue <run_id>` -> already-terminal message and no extra row.

### 5. Good/Base/Bad Cases

- Good: `/workflow run research-pack/compare-sources` reaches `waiting_task`; later `process_ui_queue(...)` records the subagent task as `completed`; the bridge appends a completed workflow row and a visible auto-continue notice without user input.
- Good: If the terminal task row has result `artifact_refs`, the auto-continued workflow row copies those refs into the agent-task step and top-level workflow row.
- Good: If an unrelated subagent task completes outside any workflow, workflow ledgers remain unchanged.
- Base: Explicit `/workflow continue <run_id>` is still valid while a task is pending, after a terminal row was missed by an older process, or after a restart where no in-process event bridge fired.
- Base: Approval waits remain human-driven and explicit even when other workflow event bridges exist.
- Bad: `process_ui_queue(...)` starts a second subagent task when the first task completes.
- Bad: The auto-continue bridge writes task/progress ledgers directly or reimplements artifact-copy semantics instead of calling `continue_workflow_run_v0(...)`.
- Bad: A failed auto-terminated workflow can be continued again into a new `blocked` row.
- Bad: Secret Vault task completion auto-resumes a normal workflow without a dedicated Secret Vault continuation contract.

### 6. Tests Required

- `tests/test_workflows.py` must assert `prompt -> agent_task -> notify` reaches `waiting_task` on `/workflow run`, then completes automatically after `process_ui_queue(...)` records the terminal subagent task result.
- `tests/test_workflows.py` must assert completed auto-continuation copies subagent artifact refs and advances later runner-v0 safe steps.
- `tests/test_workflows.py` must assert failed subagent task results auto-append one terminal workflow row and explicit continue after that row is no-op.
- `tests/test_workflows.py` must assert unrelated completed subagent tasks do not append workflow rows or auto-continue notices.
- `tests/test_workflows.py` must keep explicit continue compatibility for pending tasks and already-completed no-ops.
- `scripts/check_policy_gates.py` must assert `process_ui_queue(...)` auto-continues matching workflow tasks, explicit continue after auto-completion appends no extra row, task/progress/artifact provenance still comes from the governed subagent task pipeline, and `workflows.py` stays side-effect-free.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
process_ui_queue(task_done) -> workflow bridge starts another agent_task or appends synthetic task/progress rows
```

#### Correct

```text
process_ui_queue(task_done) -> terminal task row already exists -> auto_continue_workflows_for_agent_task(...) -> continue_workflow_run_v0(...)
```

## Scenario: Workflow Retry Policy V1

### 1. Scope / Trigger

- Trigger: AI-generated workflows need bounded recovery from transient `agent_task` failures without users manually reconstructing the run.
- Applies to: workflow step JSON `retry.max_attempts`, `shuheng.workflow.v1`, `shuheng.workflow_run.v1`, `workflow_runs.jsonl`, `tasks.jsonl`, `workflows.workflow_step_retry_state(...)`, `workflows.workflow_agent_task_retry_available(...)`, `workflows.prepare_workflow_agent_task_retry(...)`, `workflows.attach_workflow_agent_task(...)`, `app.continue_workflow_run_v0(...)`, `app.bridge_workflow_agent_task(...)`, `app.auto_continue_workflows_for_agent_task(...)`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: This does not add wall-clock timeout timers, backoff scheduling, task abort/kill, Secret Vault retries, approval retries, condition retries, parallel/fan-out/fan-in execution, plugin code execution, model/tool calls outside subagent tasks, or A2A/MCP workflow services.

### 2. Signatures

- Workflow step declaration:
  - `{"type": "agent_task", "retry": {"max_attempts": 2}}`
- Retry policy bound:
  - `WORKFLOW_STEP_RETRY_MAX_ATTEMPTS_LIMIT = 5`
- Run step snapshot fields:
  - `step.retry.max_attempts`
  - `step.retry.attempt`
  - `step.retry.remaining_attempts`
  - `step.retry.task_attempts[]`
- Pure helper ownership:
  - `workflows.workflow_step_retry_state(step) -> dict`
  - `workflows.workflow_agent_task_retry_available(row) -> bool`
  - `workflows.prepare_workflow_agent_task_retry(row, timestamp, reason="") -> dict`
- App ownership:
  - `app.continue_workflow_run_v0(run_id, state=None)` observes terminal task rows and decides whether to retry.
  - `app.bridge_workflow_agent_task(row, state, source_command)` remains the only retry dispatch path.

### 3. Contracts

- `retry.max_attempts` means total dispatch attempts for that step, including the first attempt.
- Omitted retry policy is normalized to `max_attempts=1`, `attempt=0`, `remaining_attempts=1`, and `task_attempts=[]`.
- Invalid retry policies must make the workflow load result invalid: `retry` must be an object, `max_attempts` must be an integer, must be at least 1, and must be no greater than `WORKFLOW_STEP_RETRY_MAX_ATTEMPTS_LIMIT`.
- Every `attach_workflow_agent_task(...)` dispatch increments `step.retry.attempt` and recomputes `remaining_attempts`.
- When a terminal failed/rejected/cancelled/canceled/aborted task row is observed and attempts remain, the workflow must preserve the prior task id/status/error/artifact refs under `retry.task_attempts[]`, clear the current step's `task_id`/`task_status`/`agent_id`/current artifact refs, mark the step `blocked`, then redispatch through `bridge_workflow_agent_task(...)`.
- Retry must append at most one workflow run row per `continue_workflow_run_v0(...)` call or auto-continue event.
- Retry must never write task/progress rows directly from `workflows.py`; only `start_subagent_task_structured(...)` inside the Workflow Agent Task Bridge may own those side effects.
- If attempts are exhausted, the existing terminal failed/rejected/cancelled behavior remains unchanged and later workflow steps remain pending.
- Cancellation wins over retry: `/workflow cancel <run_id>` on a waiting retry-capable task appends one cancelled workflow row, does not abort the task, and does not prepare a retry.
- `workflows.py` remains pure and must not import app/runtime/UI/governance owners, append JSONL rows, read task ledgers, dispatch subagents, or call tools/providers.

### 4. Validation & Error Matrix

- `retry` omitted -> no retry after failed task; one failed workflow row is appended.
- `retry = 3` -> validation issue, no run creation.
- `retry.max_attempts = 0` -> validation issue, no run creation.
- `retry.max_attempts = 99` -> validation issue, no run creation.
- `retry.max_attempts = 2`, first task fails -> one retry workflow row is appended and a second governed subagent task is dispatched.
- `retry.max_attempts = 2`, second task completes -> workflow marks the step completed and advances later safe steps.
- `retry.max_attempts = 2`, second task fails -> one terminal failed workflow row is appended and no third task is dispatched.
- Explicit `/workflow continue <run_id>` and event-driven auto-continue use the same retry path.

### 5. Good/Base/Bad Cases

- Good: `prompt -> agent_task(retry=2) -> notify`; attempt 1 fails; `process_ui_queue(...)` calls `continue_workflow_run_v0(...)`, records prior task provenance, dispatches attempt 2 through the subagent task pipeline, then completes after attempt 2 succeeds.
- Good: `/workflow show <run_id>` shows `retry=2/2` and `previous_attempts=1`, so the retry is auditable.
- Base: A workflow without retry policy keeps the prior fail-fast behavior.
- Base: Retry is step-local; future graph-level retry policies must get their own contract.
- Bad: Retry writes synthetic task/progress rows or starts a hidden workflow executor.
- Bad: Retry silently loops forever or ignores `max_attempts`.
- Bad: Retry clears prior task provenance instead of preserving task id/status/error/artifact refs.

### 6. Tests Required

- `tests/test_workflows.py` must assert retry policy validation, first failure retry dispatch, prior attempt provenance, second-attempt success, attempt-exhausted failure, and no-retry fail-fast compatibility.
- `tests/test_workflows.py` must assert `/workflow show` includes retry counters for retried runs.
- `scripts/check_policy_gates.py` must assert app retry dispatch passes through `prepare_workflow_agent_task_retry(...)` and `bridge_workflow_agent_task(...)`, `workflows.py` remains side-effect-free, invalid retry policy is rejected, and terminal task auto-continue can trigger exactly one retry.
- Keep targeted compile/Ruff, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
failed task -> workflow retry loop writes tasks.jsonl manually until success
```

#### Correct

```text
failed task -> continue_workflow_run_v0(...) -> prepare_workflow_agent_task_retry(...) -> bridge_workflow_agent_task(...) -> start_subagent_task_structured(...)
```

## Scenario: Workflow Approval Bridge

### 1. Scope / Trigger

- Trigger: A runner-v0 workflow reaches an `approval` step and the user must approve or reject it through Shuheng's existing governed approval surface.
- Applies to: `/workflow run <ref>`, `/workflow continue <run_id>`, `/workflow resume <run_id>`, `workflow_runs.jsonl`, `approvals.jsonl`, `agentapproval.v1`, `shuheng.workflow_run.v1`, `workflows.py` pure approval-state helpers, `app.py` approval-queue integration, `/approvals`, `/approve <approval_id>`, `/reject <approval_id>`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: The bridge does not dispatch subagents, evaluate conditions, call tools or model providers, execute plugin code, write artifacts, mutate task/progress ledgers, write memory, touch Secret Vault, schedule work, auto-continue inside `/approve`, or expose A2A/MCP workflow services.

### 2. Signatures

- Approval row type: `workflow_step_approval`.
- Approval row schema: existing `agentapproval.v1`.
- Approval payload must include `run_id`, `workflow_ref`, `workflow_id`, `workflow_name`, `workflow_path`, `step_id`, `step_name`, `step_type`, `source`, and `source_command`.
- Workflow run top-level approval fields:
  - `approval.approval_status`: `pending`, `approved`, or `rejected` while the bridge owns the step.
  - `approval.approval_id`: the `agentapproval.v1` id for the bridged workflow step.
  - `approval.approval_required_for`: the blocked workflow step id list.
- Approval step snapshot fields:
  - `status`: `waiting_approval`, `completed`, or `rejected`.
  - `approval_id`: the same `agentapproval.v1` id.
- Pure helper ownership:
  - `workflows.pending_workflow_approval_step(row)`
  - `workflows.workflow_approval_id(row)`
  - `workflows.attach_workflow_step_approval(row, approval_id, timestamp)`
  - `workflows.apply_workflow_step_approval_decision(row, approval_id, approved, timestamp, reason="")`
- App ownership:
  - `app.queue_workflow_step_approval(row, source_command=...)` writes the concrete `agentapproval.v1` row through existing `queue_approval(...)`.
  - `app.continue_workflow_run_v0(run_id, state=None)` consults latest approval rows and appends at most one workflow run row per explicit continue call.

### 3. Contracts

- A `/workflow run` that stops at an `approval` step must append exactly two workflow rows: the initial `planned` row and the runner-v0 `waiting_approval` row.
- The `waiting_approval` row must contain the approval id both in top-level approval metadata and in the blocked approval step snapshot.
- The bridge must create exactly one pending `agentapproval.v1` row for the blocked workflow approval step.
- `/approvals` must show workflow approvals because they are normal approval-ledger rows.
- `/approve <approval_id>` and `/reject <approval_id>` must remain generic approval-decision commands. They update the approval ledger but must not automatically continue the workflow.
- `/workflow continue <run_id>` with a pending approval must append no workflow row and must report the pending approval id.
- `/workflow continue <run_id>` after an approved `workflow_step_approval` must mark the approval step completed, preserve the approval id, and then advance only runner-v0 safe steps from that resulting state.
- `/workflow continue <run_id>` after a rejected `workflow_step_approval` must append one terminal rejected workflow row and must not continue later steps.
- Legacy `waiting_approval` rows without an `approval_id` must be bridgeable: the next `/workflow continue <run_id>` creates one approval row, attaches the id, and appends one updated `waiting_approval` workflow row.
- `workflows.py` remains pure. It may copy and transform workflow run dictionaries, but must not import app/runtime/UI/governance owners, append JSONL rows, queue approvals, dispatch subagents, or call tools/providers.
- Workflow approval bridge rows may increment `execution.approvals_created` to `1`. All other side-effect counters for subagents, tools, artifacts, task ledger rows, progress ledger rows, and plugin code must stay zero.

### 4. Validation & Error Matrix

- Valid workflow with `prompt -> approval -> notify` run through `/workflow run` -> two workflow rows, one pending approval row, latest row `waiting_approval`, approval id attached at top level and step level.
- `/workflow continue <run_id>` before the approval decision -> no workflow row append, pending approval id shown.
- `/approve <approval_id>` then `/workflow continue <run_id>` -> one workflow row append, approval step `completed`, later safe steps continue, final status `completed` if no later blocker exists.
- `/reject <approval_id>` then `/workflow continue <run_id>` -> one workflow row append, approval step `rejected`, final status `rejected`, later safe steps remain pending.
- Latest workflow row has `waiting_approval` and no approval id -> `/workflow continue <run_id>` creates one pending approval row and appends one bridged waiting row.
- Latest workflow row has `waiting_approval` with approval id but the approval row is missing or not decidable -> no workflow row append; visible no-progress message.
- Latest approval row is already approved or rejected -> continuation must use that latest decision row, not an older pending row.
- Blocked `agent_task` or `condition` rows -> no approval row creation. `condition` remains side-effect-free; `agent_task` execution, if any, belongs only to the Workflow Agent Task Bridge.

### 5. Good/Base/Bad Cases

- Good: `/workflow run research-pack/approval-flow` creates `agentapproval.v1 type=workflow_step_approval` and shows the same id in `/workflow show <run_id>`.
- Good: `/workflow continue wfr_...` reports "waiting for approval" until the user runs `/approve appr_...`.
- Good: After approval, runner v0 completes only safe steps such as `notify`; it still blocks at later `agent_task` or `condition` steps.
- Base: `/approve` records the human decision only. The user must run `/workflow continue <run_id>` to resume the workflow.
- Base: Approval payload is audit/resume context, not executable plugin code.
- Bad: `/approve appr_...` automatically resumes a workflow.
- Bad: `/workflow continue wfr_...` self-approves a pending approval.
- Bad: The bridge creates a second approval mechanism or writes a new approval type outside `agentapproval.v1`.
- Bad: `workflows.py` imports `app.py`, governance, ledgers, runtime dispatch, curses, Secret Vault, provider adapters, or subprocess.

### 6. Tests Required

- `tests/test_workflows.py` must assert approval creation during `/workflow run`, top-level and step-level approval id attachment, `/approvals` visibility, pending continue no-op, approved continuation, rejected termination, legacy waiting-row bridge, and side-effect invariants.
- `tests/test_workflows.py` must keep the pure runner test that `advance_workflow_run_v0(...)` alone does not write approval rows.
- `scripts/check_policy_gates.py` must assert the approval bridge creates only the expected approval rows, leaves task/progress/artifact ledgers unchanged for approval-only flows, does not change `state.subagents`, and does not claim ownership of `agent_task` dispatch.
- `scripts/check_policy_gates.py` must keep asserting `workflows.py` has no app/runtime/UI/governance imports.
- Keep `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, targeted pytest, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
/workflow continue wfr_approval -> marks deploy_gate approved because the model thinks it is safe
```

#### Correct

```text
/workflow continue wfr_approval -> waits until /approve appr_... records a human decision, then continues only runner-v0 safe steps
```

## Scenario: Running Indicator, Process Summary, Visible Reply Cleanup, Turn Marker Splitting, And Selection Geometry Rendering

### 1. Scope / Trigger

- Trigger: The visible main or subagent transcript contains an unfinished assistant message while `display_status(state)` is `running` or `aborting`.
- Applies to: `State.run_frame`, `RenderLine` metadata, process preview/summary text helpers, process turn-marker splitting, `message_lines_cached()`, rendered-line selection geometry, `draw_main()`, and the main curses event loop.
- Non-goal: This does not change runtime provider streaming, transcript persistence, token accounting, process folding, or session history naming.

### 2. Signatures

- Frame source: `RUN_FRAMES` and `running_indicator(frame)`, implemented in `src/shuheng/rendering.py` and re-exported from `src/shuheng/app.py`.
- Curses-free helper module: `src/shuheng/rendering.py` owns `RUN_FRAMES`, `running_indicator(frame)`, `running_indicator_cell_width()`, and `render_running_indicator_line(line, frame)`.
- Process text helper ownership: `rendering.strip_meta_blocks(text)`, `rendering.process_preview(text)`, `rendering.process_summary_text(text)`, and `rendering.process_title_text_from_parts(summary, has_search_noise, preview)`, re-exported by `app.py` for compatibility where applicable.
- Process turn-marker splitter ownership: `rendering.next_nonblank_line(lines, start)`, `rendering.line_numbered_file_line(line)`, `rendering.stray_line_numbered_fence_close(line, previous_nonblank, next_nonblank)`, and `rendering.split_top_level_turn_markers(text)`, re-exported by `app.py` for compatibility.
- Markdown fence balancing ownership: `rendering.close_unbalanced_markdown_fence(text)`, re-exported by `app.py` for compatibility.
- Visible reply cleanup ownership: `rendering.strip_tool_output_blocks(text)`, `rendering.strip_standalone_dot_lines(text)`, and `rendering.visible_reply_text(body, hide_detail_fences=False)`, with `TOOL_CALL_BLOCK_RE`, `TOOL_RESULT_FENCE_RE`, and `FINAL_RESPONSE_INFO_RE` owned by `rendering.py` and re-exported by `app.py` for compatibility.
- Inline markdown cleanup ownership: `rendering.strip_inline_markdown(text)`, re-exported by `app.py` for compatibility.
- Interaction card/answer/footer/visible ask-user card text ownership: `rendering.sanitize_interaction_candidates(raw)`, `rendering.render_interaction_card(payload)`, `rendering.visible_ask_user_card_text(payload)`, `rendering.interaction_answer_from_text(text, candidates, selected)`, `rendering.compose_request_user_input_answer(payload, answers)`, `rendering.interaction_input_prompt_text(has_payload, is_approval=..., current_question_index=...)`, `rendering.interaction_footer_text(has_payload, has_candidates=..., is_approval=..., has_questions=...)`, and `rendering.interaction_hint_layout_lines(...)` own deterministic ask-user/request-user-input visible card, default visible ask-user card fallback, answer, multi-question answer, prompt-label, footer text, and neutral hint-row text layout over explicit inputs. `app.py` keeps interaction request extraction, pending interaction state, approval payload construction, current question/candidate traversal, selection mutation, answer submission, `interaction_hint_lines(...)` attr conversion, curses hint rows, and input handling.
- Subagent result notice/metadata ownership: `rendering.parse_subagent_result_notice(...)`, `rendering.split_subagent_result_reply_and_metadata(...)`, `rendering.subagent_result_metadata_*`, `rendering.count_list_like_metadata_value(...)`, and `rendering.subagent_meta_label(...)`, with `SUBAGENT_RESULT_HEADER_RE` and `SUBAGENT_RESULT_META_LABEL_RE` owned by `rendering.py` and re-exported by `app.py` for compatibility.
- Subagent result card layout ownership: `rendering.subagent_result_card_layout_lines(notice, metadata_lines, expanded_meta, body_width)` returns neutral card chrome/layout records for title, metadata summary, optional metadata-detail insertion, reply header, and footer. `app.py` keeps `subagent_result_card_blocks(...)` as the wrapper that parses notices, renders/splits bodies, invokes markdown/plain block rendering, inserts metadata detail blocks, and converts neutral records into `RenderLine` rows with curses attrs.
- Markdown table parser helper ownership: `rendering.is_table_separator(cells)` and `rendering.split_table_row(line)`, re-exported by `app.py` for compatibility.
- Latest visible reply selection ownership: `rendering.latest_visible_reply_text(text, has_tool_noise=None)` owns turn-aware final-prose selection; `app.py` keeps the legacy `latest_visible_reply_text(text)` wrapper and injects app-owned `process_has_tool_noise(...)`.
- Visible reply policy ownership: `rendering.visible_reply_is_substantive(text)`, `rendering.visible_reply_is_housekeeping_summary(text)`, and `rendering.visible_reply_has_section_shape(text)`, re-exported by `app.py` for compatibility.
- Preferred group reply selection ownership: `rendering.preferred_group_visible_reply_text(visible_items, irc_replies)` owns final grouped visible-reply choice over already-cleaned visible replies and already-extracted IRC reply lines; `app.py` keeps `preferred_group_visible_reply(process_turns)` as the wrapper that traverses process turns and injects app-owned cleanup/parsing.
- Process-turn line selection ownership: `rendering.process_turn_lines(final_text, ..., collapsed_line, speech_header_line, summary_line, detail_line, fallback_summary_line)` owns deterministic process-turn output line selection over already-computed flags and already-formatted line strings. `app.py` keeps the legacy `append_process_turn(rendered, marker, body, current, fold_details=True, collapse_whole=False)` wrapper that computes process noise flags, visible final text, summary/title fallback, and formatted process lines before extending `rendered`.
- Process-group header aggregation ownership: `rendering.process_group_header_parts(summary_values, tool_groups, turn_count, tool_limit=3)` owns deterministic group title and bounded tool-list aggregation over explicit process summaries and already-parsed tool-name lists. `app.py` keeps `process_group_header(label, turns, current, expanded)` as the wrapper that traverses process turns, calls app-owned `process_summary_text(...)` and `process_tools(...)`, and formats the final header through `rendering.process_group_header_text(...)`.
- Process-line formatter ownership: `rendering.process_turn_label(marker)`, `rendering.process_tool_suffix(tools)`, `rendering.process_turn_no(marker, fallback)`, `rendering.collapsed_process_line_text(...)`, `rendering.process_detail_line_text(...)`, `rendering.process_speech_header_text(...)`, `rendering.process_speech_summary_line_text(...)`, `rendering.process_display_summary_text(summary, preview)`, `rendering.process_summary_append_lines(summary, summary_line)`, `rendering.expanded_process_header_text(...)`, `rendering.process_group_header_text(...)`, `rendering.collapsed_process_child_line_text(...)`, and `rendering.expanded_process_child_header_text(...)` own deterministic process row/header string formatting and summary-display/summary-row append policy over explicit values. `app.py` keeps the legacy process-row functions as wrappers that inject app-owned process title, summary, preview, and tool parsing, and keeps `append_process_summary_line(rendered, marker, body)` as the wrapper that mutates the caller-provided rendered list.
- Process-child detail formatter ownership: `rendering.process_child_detail_text(cleaned_body, preview, limit=12000)` owns deterministic cleaned detail fallback, truncation, and indentation. `app.py` keeps the legacy `process_child_detail(body, limit=12000)` wrapper and injects app-owned `strip_tui_controls(...)` plus the preview text.
- Process-noise predicate ownership: `rendering.process_has_tool_call_noise_text(body, tools)`, `rendering.process_has_tool_result_noise_text(body)`, `rendering.process_has_tool_noise_text(body, tools)`, and `rendering.process_has_search_noise_text(body, tools)` own deterministic tool/result/search-noise detection over explicit body text and app-provided tool names. `app.py` keeps the legacy predicate names as wrappers that inject `process_tools(body)`.
- Process scope-key ownership: `rendering.process_group_scope_key(display_scope, label)`, `rendering.process_turn_scope_key(display_scope, label)`, and `rendering.subagent_meta_scope_key(display_scope, label)` own deterministic expansion-key formatting over explicit display-scope and label strings. `app.py` keeps `display_scope_key(state)` and the legacy `process_group_key(state, label)`, `process_turn_key(state, label)`, and `subagent_meta_key(state, label)` wrappers that inject app-owned scope selection.
- Message cache helper ownership: `rendering.scoped_subagent_meta_keys(process_scope, expanded_subagent_meta)`, `rendering.message_cache_signature(messages)`, and `rendering.message_render_cache_key(...)`, re-exported by `app.py` for compatibility.
- Selection geometry helpers: `rendering.char_index_for_cell(text, target_x)`, `rendering.ordered_selection_points(selection_start, selection_end)`, and `rendering.selection_span_for_line_points(points, line_idx, text)`, with `app.py` retaining the legacy `ordered_selection_points(state)` and `selection_span_for_line(state, line_idx, text)` wrappers.
- Boxed user-message text layout ownership: `rendering.boxed_user_lines(text, width)`, re-exported by `app.py` for compatibility.
- Cached line marker: `RenderLine.kind == "running_indicator"`.
- Visible row state: `State.running_indicator_rect`.
- Lightweight redraw helper: `draw_running_indicator_frame(stdscr, state)`.

### 3. Contracts

- `run_frame` must not be part of `message_render_cache_key()` or the `message_lines_cached()` key.
- `message_render_cache_key(...)` accepts the existing `run_frame` argument for call-site compatibility, but the returned key must ignore it so animation ticks do not invalidate cached message blocks.
- `scoped_subagent_meta_keys(...)` is pure over explicit scope strings and expanded metadata ids. It returns all expanded keys when no process scope is active, otherwise only keys under `"<scope>:submeta:"` with that prefix stripped.
- `message_cache_signature(...)` is pure over explicit message-like objects and returns tuples of `(id(message), role, content_length, done)`. It must not inspect `State`, mutate caches, read message cache storage, allocate `RenderLine`, call curses, or include `run_frame`; app-owned `message_lines_cached(...)` remains responsible for combining this signature with `State.message_version` and mutable UI cache fields.
- `rendering.py` may depend on lower-level terminal-cell helpers and `RenderLine`, but must not import `shuheng.app`, curses, mutable TUI `State`, runtime dispatch, command handlers, Web Console, dashboard, input handlers, or draw functions.
- Process preview/summary helpers in `rendering.py` are deterministic text transforms. They may reuse process-safe history-title regex and description helpers, but must not parse JSON-ish tool payloads, inspect interaction state, read history stores, mutate message caches, allocate `RenderLine`, or call curses.
- `process_preview(...)` prefers the last explicit `<summary>` title, otherwise strips fenced detail blocks, meta blocks, and simple tool markers before choosing the first compact visible line, falling back to `执行中`.
- `process_summary_text(...)` returns the last compact summary, and when that summary is a legacy process-only label such as `OMP 思考`, it falls back to the latest `<thinking>` / `<think>` body excerpt.
- `process_title_text_from_parts(summary, has_search_noise, preview)` is a deterministic title-priority helper over explicit facts. It returns a non-empty summary first, then `搜索/浏览输出已折叠` for search/browser noise with no summary, otherwise the provided preview. It must not call `process_tools(...)`, `process_has_search_noise(...)`, `process_preview(...)`, or `process_summary_text(...)`, parse JSON-ish payloads, inspect interaction state, inspect `State`, mutate caches, allocate `RenderLine`, or call curses. `app.process_title_text(body)` remains responsible for raw body parsing and injected search-noise policy.
- `process_display_summary_text(summary, preview)` is a deterministic display-summary policy helper over explicit facts. It returns summary first, otherwise preview, but suppresses empty values and the in-progress sentinel `执行中`; when summary itself is `执行中`, it must not fall back to preview. It must not parse raw process bodies, call `process_summary_text(...)`, call `process_preview(...)`, call `process_speech_summary_line_text(...)`, call `process_tools(...)`, mutate rendered lists, inspect `State`, allocate `RenderLine`, or call curses. App-owned render paths remain responsible for raw body parsing, preview generation, formatted process row construction, list mutation, and compatibility return values.
- `process_summary_append_lines(summary, summary_line)` is a deterministic summary-row append policy helper over explicit facts. It returns one preformatted summary line when the summary is non-empty and not equal to `执行中`, otherwise returns an empty list. It must not parse raw process bodies, call `process_summary_text(...)`, call `process_speech_summary_line_text(...)`, call `process_tools(...)`, mutate rendered lists, inspect `State`, allocate `RenderLine`, or call curses. `app.append_process_summary_line(rendered, marker, body)` remains responsible for raw body parsing, app-owned tool injection through `process_speech_summary_line(...)`, list mutation, and the legacy boolean return.
- Process scope-key helpers are deterministic string formatters over explicit `display_scope` and label strings. `process_group_scope_key(display_scope, label)` returns `"<scope>:<label>"`, `process_turn_scope_key(display_scope, label)` preserves the legacy group-prefix segment for labels like `G2T7` and the empty middle segment for non-group labels, and `subagent_meta_scope_key(display_scope, label)` returns `"<scope>:submeta:<label>"`. They must not call `display_scope_key(...)`, inspect `State`, mutate expanded sets, allocate `RenderLine`, or call curses. App wrappers remain responsible for app-owned display-scope selection.
- `split_top_level_turn_markers(...)` is a deterministic text parser over already-loaded assistant text. It splits only top-level `LLM Running (Turn N) ...` markers, treats fenced content as opaque data, and preserves the legacy line-numbered file-output guard so a stray closing fence after `N|...` does not swallow the next top-level turn marker.
- `split_top_level_turn_markers(...)` may reuse `history_titles.TURN_MARKER_RE`, but must not parse tools/interactions, inspect `State`, read history stores, mutate caches, allocate `RenderLine`, or call curses.
- `close_unbalanced_markdown_fence(...)` is a deterministic text transform over already-cleaned visible assistant text. It appends the original opening fence tick sequence only when a markdown fence remains open, treats suffix-bearing close lines as content, and must not parse tools/interactions, inspect `State`, read history stores, mutate caches, allocate `RenderLine`, or call curses.
- `visible_reply_text(...)` is a deterministic text transform over already-loaded assistant text. It removes hidden meta blocks, standalone progress-dot lines, `tool_use` blocks, tool headers, and final-response info; it keeps detail/result fences in default mode and removes tool-call/detail/result blocks only when `hide_detail_fences=True`.
- `visible_reply_text(...)` may reuse process-safe history-title regexes but must not call `process_tools(...)`, parse JSON-ish tool payloads, inspect interaction state, read history stores, mutate caches, allocate `RenderLine`, or call curses.
- `strip_inline_markdown(...)` is a deterministic inline markdown cleanup helper over already-loaded text. It converts image markdown to `[alt]`, converts links to `text (url)`, removes inline-code backticks, and removes bold/italic emphasis markers. It must not own table rendering, markdown block rendering, `RenderLine` allocation, curses attrs, process/tool parsing, subagent metadata parsing, mutable `State`, caches, history stores, or runtime side effects. App-owned table, markdown block, and metadata helpers may call the compatibility alias but remain app-owned until later explicit slices.
- `sanitize_interaction_candidates(...)`, `render_interaction_card(...)`, `visible_ask_user_card_text(...)`, `interaction_answer_from_text(...)`, `compose_request_user_input_answer(...)`, `interaction_input_prompt_text(...)`, `interaction_footer_text(...)`, and `interaction_hint_layout_lines(...)` are deterministic interaction-display/input-text helpers over explicit raw candidate values, already-extracted interaction payload dictionaries, explicit selected indexes, explicit answer lists, explicit prompt-state flags, explicit footer-state flags, or explicit hint-row facts. They may trim numbered/quoted/list-like candidate labels, format the visible Chinese ask-user/request-user-input card, format the default visible ask-user waiting card when no extracted payload exists, resolve numeric/free-text/blank-candidate answers, format multi-question `request_user_input` answer text, return prompt labels such as `"> "`, `"approval> "`, `"qN> "`, and `"? "`, choose the existing footer strings from explicit payload/candidate/approval/question booleans, and return neutral `(kind, text)` hint layout rows for headers, body text, candidate rows, muted overflow rows, and footer rows. They must not parse tool payloads, call `process_tools(...)`, call `extract_interaction_request(...)`, inspect `State.pending_interaction`, read approval ledgers, mutate interaction selection, allocate `RenderLine`, choose curses attrs, or handle keyboard/input submission. App-owned `extract_interaction_request(...)`, approval interaction payloads, `normalize_interaction_payload(...)`, `interaction_current_candidates(...)`, `interaction_selection(...)`, `visible_ask_user_text(...)`, `interaction_answer_from_input(...)`, `interaction_input_prompt(...)`, `interaction_footer(...)`, `interaction_hint_lines(...)`, and input handlers remain responsible for parsing, state, approval, current-question traversal, selection mutation, curses attr conversion, and submission behavior.
- Subagent result notice/metadata helpers are deterministic text transforms over already-loaded system notice text or already-rendered subagent result bodies. They parse the `子 agent 回复 · <name> (<agent_id>)` header, optional `Task:` / `Artifact:` lines, visible body text, metadata footers, labels, values, grouped entries, list-like counts, summary chips, and stable `Sxxxxxxxx` metadata ids. They may use lower-level `clean_text(...)`, `strip_inline_markdown(...)`, `truncate_cells(...)`, and hashing, but must not allocate `RenderLine`, choose curses attrs, inspect `State`, read ledgers or artifact files, mutate message caches, call Web Console/dashboard/runtime/input/command owners, or perform storage/runtime side effects. App-owned `subagent_result_metadata_detail_blocks(...)`, `subagent_result_card_blocks(...)`, `message_block_lines(...)`, and subagent context-update wrappers remain responsible for `RenderLine` allocation, color attrs, task-ledger/artifact/meta lookups, current-session context injection, and message rendering.
- `subagent_result_notice_body_text(raw, rendered, final_reply, has_tool_noise, limit)`, `format_subagent_result_notice_text(name, agent_id, bus_task_id, artifact_ref, body)`, and `subagent_result_metadata_detail_lines(notice, metadata_lines, width)` are deterministic subagent-result notice format helpers over explicit inputs. The app wrapper must inject `render_assistant_text(...)`, `latest_visible_reply_text(...)`, `process_has_tool_noise(...)`, `SubAgentRuntime` fields, and `RenderLine(..., cp(9))` conversion; `rendering.py` must not import those app-owned dependencies or allocate `RenderLine` for the notice/card path.
- `subagent_result_reply_excerpt_text(rendered, limit)`, `subagent_result_context_confidence(metadata_lines)`, `format_subagent_result_context_update_text(...)`, and `bounded_subagent_context_updates(updates, update_limit, total_limit)` are deterministic subagent-result context-update helpers over explicit inputs. The app wrapper must inject `render_subagent_result_body(...)`, `latest_task_records(...)`, `session_key(...)`, notice parsing, and `Message` traversal; `rendering.py` must not read task ledgers, resolve session paths, inspect `State`, read artifacts, mutate history, allocate `RenderLine`, call curses, or perform runtime/storage side effects for context updates.
- `subagent_result_card_layout_lines(...)` is a deterministic subagent-result card chrome helper over explicit notice dictionaries, metadata lines, expanded metadata ids, and body width. It may call subagent metadata label/summary helpers and terminal-cell truncation, but must not parse notice text, render subagent bodies, call markdown/plain block renderers, allocate `RenderLine`, choose curses attrs beyond neutral record kinds, inspect `State`, read ledgers or artifacts, traverse messages, mutate caches/history, or perform runtime/storage side effects. `app.subagent_result_card_blocks(...)` remains responsible for invalid-notice fallback, `render_subagent_result_body(...)`, `split_subagent_result_reply_and_metadata(...)`, `subagent_result_metadata_detail_blocks(...)`, `markdown_blocks(...)`, `plain_blocks(...)`, reply-body prefixing, and all `RenderLine` attr conversion.
- `is_table_separator(...)` and `split_table_row(...)` are deterministic markdown table parser helpers over already-loaded table row strings or already-split cell strings. `split_table_row(...)` trims outer pipes/cell whitespace and applies `strip_inline_markdown(...)`; `is_table_separator(...)` recognizes markdown alignment separator cells. They must not render tables, allocate `RenderLine`, choose curses attrs, parse markdown blocks, inspect message caches, inspect `State`, read stores, or perform runtime side effects. App-owned `render_table(...)` and `markdown_blocks(...)` may call the compatibility aliases but remain app-owned until later explicit slices.
- `table_layout_lines(...)`, `markdown_layout_blocks(...)`, and `plain_layout_lines(...)` return neutral layout records over already-loaded text. `table_layout_lines(...)` owns column sizing and table row records, `markdown_layout_blocks(...)` owns deterministic block parsing for code fences, tables, blank lines, rules, headings, quotes, task items, bullets, numbered items, and body text, and `plain_layout_lines(...)` owns plain text wrapping via the lower-level terminal-cell wrapper. They may use lower-level text wrapping/inline cleanup helpers, but must not allocate `RenderLine`, choose curses attrs, inspect `State`, read or mutate message caches, parse process/tool payloads, call Web Console/dashboard/runtime/input/command owners, or perform storage/runtime side effects. App-owned `render_table(...)`, `markdown_blocks(...)`, and `plain_blocks(...)` remain compatibility wrappers that convert neutral records or strings into existing `RenderLine` values with `cp(...)` and curses attrs.
- `latest_visible_reply_text(...)` is a deterministic selector over already-loaded assistant text. It may use `split_top_level_turn_markers(...)` and `visible_reply_text(...)`, but any tool-noise decision must be injected by the app wrapper or caller; it must not call `process_tools(...)`, parse JSON-ish tool payloads, inspect `State`, read history stores, mutate caches, allocate `RenderLine`, or call curses.
- Visible reply policy helpers are deterministic text predicates over already-cleaned assistant prose. They may use lower-level text cleanup and local regexes, but must not call `process_tools(...)`, parse JSON-ish tool payloads, inspect `State`, read history stores, mutate caches, allocate `RenderLine`, or call curses.
- `preferred_group_visible_reply_text(...)` is deterministic selection over already-cleaned visible reply strings and already-extracted IRC reply lines. It chooses the latest visible reply by default, may prefer a richer earlier substantive reply over a short/housekeeping latest reply using the visible-reply policy helpers, and appends unique IRC reply lines under `### IRC 回复` when they are not already present in the chosen text. It must not traverse process turns, call `visible_reply_text(...)`, call `process_has_tool_noise(...)`, call `process_tools(...)`, parse JSON-ish tool payloads, extract IRC snippets, inspect interaction state, inspect `State`, mutate caches, allocate `RenderLine`, or call curses. App wrappers remain responsible for process-turn traversal, tool-noise cleanup, and IRC result parsing.
- `process_turn_lines(...)` is deterministic process-turn line selection over explicit final text, noise flags, fold/collapse flags, and preformatted process lines. It may call `close_unbalanced_markdown_fence(...)` for visible final text when call-noise details are folded, but must not call `visible_reply_text(...)`, `process_tools(...)`, `process_summary_text(...)`, `process_title_text(...)`, parse JSON-ish payloads, inspect interaction state, inspect `State`, mutate caches, allocate `RenderLine`, or call curses. `app.append_process_turn(...)` remains responsible for app-owned body parsing, summary/title fallback selection, and compatibility mutation of the passed `rendered` list.
- `process_group_header_parts(...)` is deterministic process-group title/tool aggregation over explicit summary strings, explicit tool-name groups, a turn count, and a tool cap. It de-duplicates non-empty summaries in input order, compacts the joined summary title, de-duplicates non-empty tool names in input order up to the cap, and falls back to `"<turn_count> 条过程"` when no summary exists. It must not traverse process turns, call `process_tools(...)`, call `process_summary_text(...)`, call `process_title_text(...)`, parse JSON-ish payloads, inspect interaction state, inspect `State`, mutate caches, allocate `RenderLine`, or call curses. `app.process_group_header(...)` remains responsible for process-turn traversal and app-owned process-body parsing before delegating to this helper.
- Process-line formatter helpers are deterministic string formatters over explicit marker, summary/title, tool-name, status, label, and title values. They must not call `process_tools(...)`, `process_summary_text(...)`, `process_title_text(...)`, parse JSON-ish payloads, inspect interaction state, inspect `State`, mutate caches, allocate `RenderLine`, or call curses. App wrappers remain responsible for injecting app-owned process parsing and search-noise title policy.
- `process_child_detail_text(...)` is a deterministic text transform over an app-cleaned process body and an app-provided preview. It may strip process meta blocks and normalize text, but must not call `strip_tui_controls(...)`, `process_tools(...)`, `process_preview(...)`, parse JSON-ish payloads, inspect interaction state, inspect `State`, mutate caches, allocate `RenderLine`, or call curses.
- Process-noise predicate helpers are deterministic predicates over body text and explicit tool-name lists. They may inspect shared rendering regexes for visible tool headers, result fences, final-response info, and static browser/search markers, but must not call `process_tools(...)`, parse JSON-ish payloads, inspect interaction state, inspect `State`, mutate caches, allocate `RenderLine`, or call curses. App wrappers remain responsible for turning raw process bodies into tool-name lists.
- `app.py` remains the owner of visible row state, `record_running_indicator_rect(...)`, `draw_running_indicator_frame(...)`, full `draw_main(...)`, and event-loop frame advancement.
- `char_index_for_cell(...)` maps terminal-cell x coordinates to Python character indices with the same East Asian wide-character and zero-width combining-mark behavior as the existing text helpers.
- `ordered_selection_points(...)` is pure over explicit `(line, column)` points and returns `None` for missing or zero-length selections. App wrappers inject `State.selection_start` and `State.selection_end`.
- `selection_span_for_line_points(...)` is pure over already-ordered explicit points, clamps character columns to the current rendered text length, returns `None` for empty spans, and does not read `State`, line caches, mouse position, or clipboard state.
- `boxed_user_lines(...)` is a deterministic terminal-cell text layout helper. It wraps user text to `max(8, width - 4)`, preserves one empty body row for empty text, computes the inner box width from wrapped body cell widths bounded by the inner limit, and returns only plain border/body strings. It may use lower-level `wrap_cells(...)`, `cell_width(...)`, and `pad_cells(...)`, but must not allocate `RenderLine`, choose curses attrs, inspect `State`, read message caches, mutate caches, or call curses. App-owned `message_block_lines(...)` remains responsible for turning these strings into `RenderLine(line, cp(2))`.
- `clear_selection(...)`, `selected_text(...)`, `shift_selection_lines(...)`, mouse hit testing, auto-scroll, clipboard copy, Secret copy gates, and curses drawing stay in `app.py`.
- Long assistant messages must not run through markdown/process rendering on every animation tick.
- Full `draw_main()` may render the current spinner frame from cached `RenderLine` metadata without mutating the cache.
- The main event loop must not set `state.dirty` solely because `run_frame` advanced.
- When the transcript spinner row is visible and the screen is otherwise clean, the animation tick may refresh only that row and then restore the input cursor.
- Lightweight spinner refresh must no-op when the spinner row is not visible, text selection is active, or a session popup is open.

### 4. Validation & Error Matrix

- `run_frame` changes from 0 to 1 -> message block cache keys and cached block object identities remain stable.
- Visible unfinished assistant message + clean screen + frame tick -> one row is updated and curses refreshes once.
- Hidden spinner row, active selection, popup, idle status, or aborted/finished message -> no lightweight row update.
- Reversed selection points -> pure helper sorts them before span calculation.
- Same start/end selection points or columns clamped to the same value -> no selection span.
- Legacy `<summary>OMP 思考</summary><thinking>...</thinking>` process text -> summary helper returns the compact thinking excerpt.
- Tool/fence-heavy process text with one visible line -> preview helper returns the compact visible line instead of a raw tool marker.
- Process title policy with explicit summary, search-noise flag, and preview -> summary wins; otherwise search/browser noise returns `搜索/浏览输出已折叠`; otherwise preview is used.
- Process display-summary policy with explicit summary and preview -> summary wins; with no summary -> preview is used; with summary or preview equal to `执行中` -> no display summary is returned, and an explicit `执行中` summary does not fall back to preview.
- Process scope-key helpers with scope `session:main` and labels `G2`, `G2T7`, `Turn7`, and `S1234abcd` -> return `session:main:G2`, `session:main:G2:G2T7`, `session:main::Turn7`, and `session:main:submeta:S1234abcd` respectively; app wrappers return the same values after injecting `display_scope_key(state)`.
- Top-level `LLM Running (Turn N) ...` markers -> splitter returns alternating preamble/marker/body parts compatible with `render_assistant_text(...)` and `latest_visible_reply_text(...)`.
- `LLM Running (Turn N) ...` inside a fenced block -> splitter leaves it inside the surrounding content rather than treating it as a process turn.
- Stray ````` fence close after line-numbered file output and immediately before a top-level marker -> splitter keeps the marker visible for splitting instead of entering an opaque fence block.
- Visible reply cleanup in default mode -> strips hidden meta, `tool_use`, tool headers, final-response info, standalone dot lines, and collapsed extra blank lines while preserving five-backtick result fences.
- Visible reply cleanup with `hide_detail_fences=True` -> strips tool-call blocks, `tool_use` blocks, result fences, tool headers, final-response info, standalone dot lines, and collapsed extra blank lines.
- Inline markdown cleanup with images, links, inline code, bold, italic, or underscore emphasis -> returns the same plain text as the legacy app helper without invoking table or block rendering.
- Interaction card/answer/footer/visible ask-user formatting with normal candidate prompts, approval prompts, multi-question `request_user_input` prompts, empty fallback payloads, default visible ask-user fallback cards, numeric candidate answers, free-text answers, blank selected-candidate fallback, multi-question answer composition, prompt labels, and footer labels -> returns the same visible text/answer strings as the legacy app helpers while leaving extraction/state/current-selection/input handling in `app.py`.
- Interaction hint layout with no payload, normal candidates, approval preview text, multi-question prompts, selected-candidate windows, and footers -> `rendering.py` returns neutral `(kind, text)` rows, while `app.interaction_hint_lines(...)` returns the same `(text, attr)` rows as before by injecting current payload facts and mapping kinds to curses attrs.
- Subagent result notice parsing with a Chinese header plus optional `Task:` / `Artifact:` lines -> returns name, agent id, task id, artifact ref, and body text without reading ledgers or artifacts.
- Subagent result metadata footer with separator, findings, confidence, and risks -> reply/body split, metadata entries, labels, count summaries, and stable meta labels match the legacy app helper without allocating `RenderLine`.
- Subagent result notice body formatting with short rendered text -> returns rendered text directly; with tool/process-heavy output and a visible final reply -> prefixes the folded-process notice and truncates long final replies with the existing artifact suffix; with no final reply -> truncates rendered/raw body with the existing artifact suffix.
- Subagent result metadata detail formatting -> `rendering.py` returns plain prefixed wrapped strings, and `app.py` alone converts them to `RenderLine(..., cp(9))`.
- Subagent result context-update formatting -> `rendering.py` shapes reply excerpts, extracts confidence, formats explicit context-update text, and selects bounded unique updates; `app.py` still injects rendered bodies, task-ledger parent/plan/role fields, session keys, notice parsing, and message traversal.
- Subagent result card layout formatting -> `rendering.py` returns neutral title/metadata/reply/footer records with folded/expanded metadata state, and `app.py` alone inserts detail/body blocks and converts rows into `RenderLine` values with `cp(...)` and curses attrs.
- Markdown table parser helpers with alignment rows, outer pipes, cell whitespace, and inline markdown -> separator detection and split-cell cleanup match the legacy app helper without invoking table rendering or allocating `RenderLine`.
- Latest visible reply selection with multiple top-level turns -> returns the latest turn body that has visible prose after detail-fence hiding; if the latest turn is only tool/result/meta noise, it falls back to the previous visible turn.
- Latest visible reply selection without top-level turns -> uses the injected `has_tool_noise` predicate to decide whether fallback cleanup should hide detail/result fences.
- Visible reply policy helpers distinguish substantive prose/section-shaped replies from short or housekeeping-only summaries, so grouped process replies can prefer a richer earlier answer when a later turn is just a completion summary.
- Preferred group reply selection with multiple cleaned visible replies -> returns the latest visible reply unless it is short or housekeeping-only and an earlier richer substantive reply satisfies the existing length/section-shape thresholds; extracted IRC lines are appended once, in order, and skipped when already present in the chosen text.
- Process-turn line selection with final visible text plus call noise -> returns the speech header, markdown-fence-balanced final text when details are folded, and folded detail line. With whole-process collapse and process noise -> returns final text plus the collapsed process line only when details are folded. With no final text -> returns title fallback plus optional detail line, or the collapsed process line for pure process noise.
- Process-group header aggregation with duplicate summaries and duplicate tool names -> returns a compact de-duplicated summary title and at most three unique tool names in first-seen order. With no non-empty summaries -> returns `N 条过程` while still preserving the bounded unique tool list.
- Boxed user-message layout with short, empty, wrapped, or wide-character text -> returns stable plain string borders/body rows with equal terminal-cell widths and no `RenderLine` allocation.
- Process-line formatter helpers preserve legacy Chinese process row strings, turn-number fallback parsing, tool suffix truncation with `+N`, group expand/collapse status labels, child row label insertion, summary-display fallback, and summary-row append policy while receiving already-parsed title/summary/preview/tool data or already-formatted summary rows from `app.py`.
- Process-child detail formatter receives text after app-owned TUI control stripping -> hidden controls stay out of expanded child details while meta stripping, fallback preview, truncation suffix, and four-space indentation remain stable.
- Wide or combining characters in text hit testing -> cell coordinate maps to the same character index as the legacy app helper.
- Terminal resize or full redraw -> `draw_main()` recomputes `State.running_indicator_rect` from currently visible lines.

### 5. Good/Base/Bad Cases

- Good: A long streaming OMP reply keeps the transcript cache stable while `[=     ] running...` animates smoothly.
- Base: A normal dirty redraw caused by input, scroll, history refresh, or clock refresh still redraws the whole TUI.
- Base: `draw_main()` still calls `selection_span_for_line(state, idx, text)` through the app facade, while the pure span computation lives in `rendering.py`.
- Base: `render_assistant_text(...)` still calls `split_top_level_turn_markers(...)` through the app facade while the splitter implementation lives in `rendering.py`.
- Base: `app.latest_visible_reply_text(...)` is a compatibility wrapper that injects app-owned `process_has_tool_noise(...)`; the deterministic latest-reply selection implementation lives in `rendering.py`.
- Base: `app.visible_ask_user_text(...)` still calls `extract_interaction_request(...)` and only delegates the already-extracted or missing payload to `rendering.visible_ask_user_card_text(...)`.
- Base: `process_title_text(...)`, `process_tools(...)`, process grouping/folding, `message_block_lines(...)`, and `message_lines_from_cache(...)` stay in `app.py` until their JSON-ish parsing, mutable cache, and curses/render-line dependencies have clean boundaries. `app.process_title_text(...)` may delegate the explicit summary/search/preview priority decision to `rendering.process_title_text_from_parts(...)`, but app-owned parsing and search-noise detection stay in `app.py`. Process-line formatter, summary append policy, and noise predicate helpers can live in `rendering.py` only because `app.py` injects the parsed title/summary/tool values, preformatted summary rows, or tool-name lists.
- Base: `app.process_child_detail(...)` strips TUI controls and injects `process_preview(...)`, while `rendering.process_child_detail_text(...)` only formats the already-cleaned body and preview.
- Base: `app.process_has_tool_call_noise(...)`, `app.process_has_tool_noise(...)`, and `app.process_has_search_noise(...)` inject `process_tools(body)` before delegating to rendering helpers; `process_tools(...)` itself remains app-owned.
- Base: `app.preferred_group_visible_reply(process_turns)` still traverses process turns, calls `visible_reply_text(..., hide_detail_fences=process_has_tool_noise(body))`, and extracts IRC replies with `irc_reply_snippets_from_process_body(...)`; only the final choice/dedupe/append policy lives in `rendering.preferred_group_visible_reply_text(...)`.
- Base: `app.process_group_header(label, turns, current, expanded)` still traverses process turns and injects app-owned `process_summary_text(...)` plus `process_tools(...)`; only summary/tool de-duplication, title fallback, and tool cap aggregation live in `rendering.process_group_header_parts(...)`.
- Base: `message_block_lines(...)` still owns user-message `RenderLine` creation and color attrs, while `rendering.boxed_user_lines(...)` only returns plain boxed strings.
- Base: `parse_subagent_result_notice(...)`, `split_subagent_result_reply_and_metadata(...)`, subagent result metadata helpers, and `subagent_meta_label(...)` are rendering-owned text transforms re-exported by `app.py`; `subagent_result_metadata_detail_blocks(...)`, `subagent_result_card_blocks(...)`, `message_block_lines(...)`, and context-update wrappers stay in `app.py` as compatibility and Orchestrator-owned wrappers for `RenderLine` values, curses attrs, ledgers, artifacts, history, and session context.
- Base: `app.subagent_result_notice_body(...)` still injects app-owned assistant rendering, visible-reply cleanup, and process-noise detection before delegating to `rendering.subagent_result_notice_body_text(...)`; `app.format_subagent_result_notice(...)` still injects `SubAgentRuntime` fields; `app.subagent_result_metadata_detail_blocks(...)` still owns `RenderLine(..., cp(9))` conversion.
- Base: `app.subagent_result_reply_excerpt(...)` still injects app-owned subagent-result body rendering before delegating to `rendering.subagent_result_reply_excerpt_text(...)`; `app.format_subagent_result_context_update(...)` still injects task-ledger parent/plan/role fields; `app.subagent_context_updates_from_messages(...)` still owns `Message` traversal and `session_key(...)` injection.
- Base: `app.subagent_result_card_blocks(...)` still parses notices, injects rendered subagent bodies, chooses markdown/plain block renderers, inserts metadata-detail blocks, prefixes body rows, and converts neutral `subagent_result_card_layout_lines(...)` records into `RenderLine` values with existing attrs.
- Base: `is_table_separator(...)`, `split_table_row(...)`, `table_layout_lines(...)`, `markdown_layout_blocks(...)`, and `plain_layout_lines(...)` are rendering-owned parser/layout helpers re-exported by `app.py`; `render_table(...)`, `markdown_blocks(...)`, and `plain_blocks(...)` stay in `app.py` as compatibility wrappers that convert neutral records or strings into `RenderLine` values with curses attrs.
- Bad: Adding `run_frame` to the message cache key or setting `state.dirty = True` every 120ms.
- Bad: Moving `selected_text(...)`, clipboard behavior, mouse drag mutation, or curses selection drawing into `rendering.py`.
- Bad: Moving `extract_interaction_request(...)`, approval interaction payload construction, `State.pending_interaction` mutation, the `interaction_hint_lines(...)` curses-attr wrapper, or input submission into `rendering.py`.
- Bad: Moving `process_tools(...)` into `rendering.py` together with JSON-ish interaction parsing before those dependencies have a separate lower-level boundary.
- Bad: Moving `irc_reply_snippets_from_process_body(...)`, JSON-ish IRC result parsing, or process-turn traversal into `rendering.py`.
- Bad: Moving message-block `RenderLine` allocation, curses attrs, or full `message_block_lines(...)` into `rendering.py` before render-line dependencies have stable lower-level boundaries.
- Bad: Moving `render_assistant_text(...)` into `rendering.py` before process grouping, interaction cards, markdown/plain block rendering, and `RenderLine` dependencies have stable lower-level boundaries.
- Bad: Moving table rendering, markdown block rendering, subagent result card `RenderLine` rendering, task-ledger/session/artifact/meta lookup, rendered-body injection, metadata-detail insertion, reply-body block rendering, or `RenderLine` allocation into `rendering.py` as part of notice/metadata/context-update/card-layout helper extraction.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert run-frame changes do not invalidate message block cache keys.
- Unit tests and `scripts/check_policy_gates.py` must assert running-indicator helpers are owned by `rendering.py`, app compatibility aliases match, helper output wraps by modulo, cached non-indicator lines pass through unchanged, indicator lines use `prefix_cells`, boxed user-message layout preserves min-width, empty-body, wrapping, wide-character padding, and app alias parity, inline markdown cleanup preserves image/link/code/bold/italic/underscore behavior and app alias parity, interaction card/answer/footer/visible ask-user formatting preserves candidate cleanup, normal ask-user cards, approval cards, request-user-input multi-question cards, empty fallback cards, default visible ask-user fallback cards, numeric/free-text/blank selected-candidate answers, request-user-input answer composition, prompt labels, footer labels, neutral hint layout rows, app hint attr-wrapper parity, and app alias/wrapper parity, subagent result notice/metadata helpers preserve header parsing, task/artifact/body extraction, metadata footer splitting, label/value extraction, grouped entries, list-like counts, summary text, stable meta ids, body shaping, final notice text assembly, metadata detail wrapped strings, context-update excerpt/confidence/text/budget shaping, card layout title/metadata/reply/footer records, collapsed/expanded metadata state, no-metadata card chrome, app wrapper injection, and app-owned `RenderLine(..., cp(...))` conversion, markdown table parser/layout helpers preserve separator detection, row trimming, inline markdown cleanup, header/body/separator layout records, column capping, app alias parity, and `app.render_table(...)` conversion to existing `RenderLine` attrs, markdown/plain block layout helpers preserve representative block/plain wrapping output plus app wrapper attr conversion and alias parity, process preview/summary/title-policy helpers preserve legacy summary, search-noise fallback, preview fallback, and metadata-stripping behavior, process display-summary helpers preserve summary priority, preview fallback, and `执行中` suppression without raw body parsing, process-scope key helpers preserve group/turn/subagent metadata key shapes plus app wrapper scope injection, process-line formatter helpers preserve legacy row/header/group strings, summary-row append policy, and app wrapper dependency injection, process-group header aggregation preserves summary de-duplication, fallback `N 条过程`, bounded unique tool list, and app wrapper parity, process-turn line selection preserves final-text header/detail output, whole-process collapse, fallback summary, collapsed-noise fallback, and app wrapper parity, process-child detail formatting preserves fallback preview, truncation suffix, four-space indentation, and app-owned TUI control stripping, process-noise/search-noise predicates preserve tool-name injection, visible tool-header detection, result/final-response detection, static search markers, and app wrapper parity, visible-reply cleanup preserves default-vs-hide-detail fence behavior, strips standalone dot lines, collapses extra blank lines, and keeps app alias parity, latest-visible-reply selection preserves latest-turn preference, empty-latest-turn fallback, injected tool-noise cleanup, and app wrapper parity, visible-reply policy helpers preserve substantive, housekeeping-summary, and section-shape decisions plus app alias parity, preferred-group reply selection preserves latest-visible default choice, richer-earlier-over-housekeeping fallback, IRC reply append/dedupe/already-present skipping, and app wrapper ownership of process-turn traversal/tool-noise cleanup/IRC parsing, turn-marker splitter helpers preserve top-level splitting, fenced-marker opacity, line-numbered stray-fence handling, and app alias parity, selection geometry helpers preserve app wrapper behavior, and `rendering.py` has no reverse dependency into app/curses/state/runtime/command/Web/dashboard/input owners.
- Unit tests must assert `char_index_for_cell(...)` handles negative targets, ASCII boundaries, wide CJK characters, and combining marks; pure selection helpers handle missing/equal/reversed points, same-line and multiline spans, out-of-range lines, clamped columns, empty spans, and app wrapper parity.
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

## Scenario: Stream Queue First-Chunk Coalescing

### 1. Scope / Trigger

- Trigger: Runtime provider queues emit a burst of `{"next": ...}` chunks followed by `{"done": ...}`.
- Applies to: `consume_stream_queue_to_ui(...)`, main stream queues, subagent task streams, subagent chat streams, and token-usage queue emission.
- Non-goal: This does not change provider protocol parsing, final transcript rendering, or token accounting semantics.

### 2. Signatures

- Function: `consume_stream_queue_to_ui(state, kind, target_ref, task_id, dq)`.
- Timing constant: `STREAM_UI_FLUSH_INTERVAL`.
- UI queue items:
  - `(kind, target_ref, task_id, text, False)` for partial stream flushes.
  - `(kind, target_ref, task_id, text, True)` for terminal completion.
  - `("token_usage", kind, target_ref, task_id, usage)` for usage payloads.

### 3. Contracts

- The first visible `next` chunk must flush immediately, independent of `time.monotonic()` uptime and independent of `STREAM_UI_FLUSH_INTERVAL` size.
- Later burst chunks may be coalesced until the interval elapses or the terminal `done` item arrives.
- A terminal `done` item must still emit token usage before the final stream item when usage is present.
- The first-chunk behavior must be shared by main, subagent task, and subagent chat stream consumers because they all call the same helper.

### 4. Validation & Error Matrix

- System uptime is less than `STREAM_UI_FLUSH_INTERVAL` -> first chunk still emits as a partial stream item.
- Multiple chunks arrive immediately -> first chunk emits, intermediate chunks are coalesced, final `done` emits complete text.
- Usage is attached to `done` -> `token_usage` item is queued before the final stream item.

### 5. Good/Base/Bad Cases

- Good: With interval `3600.0`, chunks `a b c d e` plus `done:abcde` produce partial `a`, usage, and final `abcde`.
- Base: With normal interval, long streams still coalesce intermediate chunks to avoid repaint storms.
- Bad: Initializing `last_emit_at` to `0.0`, making first-chunk behavior depend on host uptime.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert burst updates emit the first partial chunk and final completion even when `STREAM_UI_FLUSH_INTERVAL` is much larger than the current process runtime.
- Tests must assert usage payloads still reach the UI queue.

### 7. Wrong vs Correct

#### Wrong

```python
last_emit_at = 0.0
```

#### Correct

```python
last_emit_at = time.monotonic() - STREAM_UI_FLUSH_INTERVAL
```

## Scenario: OMP Runtime Permission Profiles

### 1. Scope / Trigger

- Trigger: OMP is used as the main Shuheng runtime provider and receives a generated context pack.
- Applies to: `permissions_for_role()`, `build_context_pack()`, `build_main_runtime_context_pack()`, `format_context_pack_for_prompt()`, OMP runtime task requests, isolated OMP config generation, and OMP RPC extension-UI approval responses.
- Non-goal: This does not give OMP direct ownership of Shuheng memory, approvals, ledgers, schedules, or system-level `~/.omp/agent` configuration.

### 2. Signatures

- Permission profiles: `standard`, `read_only`, `full`.
- OMP profile env override: `SHUHENG_OMP_PERMISSION_PROFILE`.
- Generic fallback env override: `SHUHENG_DEFAULT_PERMISSION_PROFILE`.
- OMP tool approval env override: `SHUHENG_OMP_APPROVAL_MODE=always-ask|write|yolo`.
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
- OMP RPC backend does not expose `raw_ask`; inline AI metadata jobs such as automatic description generation must skip OMP instead of surfacing UI errors.
- Sidebar session category is Shuheng-owned index metadata. When `raw_ask` is unavailable, Shuheng must still maintain a bounded local category fallback from visible user/assistant text, cached title/description, and existing category labels without opening an OMP metadata turn.
- Manual category metadata remains locked: `category_source:"manual"` must not be overwritten by AI or local automatic category refresh.

### 4. Validation & Error Matrix

- No env override + main OMP context -> `role:"main_orchestrator"`, `permission_profile:"full"`, `write_policy:"single_writer"`, full tool list, empty `tools_forbidden`, empty `approval_required_for`, and `memory_write:"candidate_only"`.
- No env override + main OMP runtime task request -> `role:"main_orchestrator"`, prompt contains `role: main_orchestrator` plus `permission_profile: full`, and the request carries the same full permission set.
- `SHUHENG_OMP_PERMISSION_PROFILE=read_only` + main OMP context -> `permission_profile:"read_only"`, `write_policy:"none"`, no bash in `tools_allowed`.
- Subagent context without an explicit profile -> `permission_profile:"standard"` and role-bounded tools.
- OMP isolated config generation -> `tools.approvalMode:"yolo"` and `PI_CODING_AGENT_DIR` under the Shuheng-owned harness.
- OMP RPC approval select for safe `bash` under full profile -> respond `Approve`.
- OMP RPC approval select for risky `rm -rf` under full profile -> respond `Approve`.
- OMP RPC approval select under `standard` profile -> respond `Deny`.
- OMP active session completes a normal task -> inline description workers are not started through unsupported `raw_ask`, no metadata `RuntimeError` appears, and sidebar category still lands in `session_meta.json` through the local fallback.
- OMP process summaries, hidden thinking text, tool calls, and `model_responses*.txt` basenames -> do not influence the local sidebar category.

### 5. Good/Base/Bad Cases

- Good: Main OMP runtime receives `role:"main_orchestrator"` and `permission_profile:"full"`, shows `write_policy:"single_writer"`, has an empty runtime deny/approval list, can use normal write/search/bash/browser capabilities, and still reports `memory_write:"candidate_only"`.
- Good: A role-bounded researcher subagent receives `permission_profile:"standard"` with `tools_allowed:["web","read"]` and `write_policy:"none"`.
- Good: An OMP-backed Shuheng sidebar-history bug session is categorized as `Shuheng` by the local fallback without calling `raw_ask`.
- Base: Operator sets `SHUHENG_OMP_PERMISSION_PROFILE=read_only`; OMP main runtime starts in compatibility mode and does not advertise bash/write tools.
- Base: Operator sets `SHUHENG_OMP_APPROVAL_MODE=always-ask`; command/config generation preserves the override.
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

## Scenario: shuheng-control v2 Delegation

### 1. Scope / Trigger

- Trigger: Main-agent TUI controls, subagent creation, task planning, and subagent delegation must use the `shuheng-control.v2` / `agenttask.v2` contract.
- Applies to: hidden control blocks emitted by the main agent, JSON code-fence controls in recovery paths, auto-continuation prompts, and policy-gate regression tests.
- Historical markup cleanup belongs in quarantine compatibility code only; it must not define executable external protocol behavior.

### 2. Signatures

- Hidden block: `<shuheng-control>{...}</shuheng-control>`
- Fenced block: ````shuheng-control`
- Implementation module: `src/shuheng/control_protocol.py` owns the current protocol regexes, schema constants, action sets, JSON repair/parsing, extraction, stripping, lifecycle/reuse field parsing, subagent lifecycle/reuse intent helpers, AgentTask prompt envelope parsing, AgentTask explicit and inferred policy-action extraction, control-result line formatting, control-result continuation helper parsing/formatting, and v2-to-internal-action coercion.
- Execution module: `src/shuheng/app.py` may re-export protocol helpers for compatibility, but state-mutating execution functions stay in `app.py` unless they are extracted behind an explicit state boundary.
- Batch envelope:

```json
{
  "schema_version": "shuheng-control.v2",
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

- `shuheng-control.v2.actions[]` accepts strong typed dotted action names only.
- Supported session actions: `session.pin`, `session.unpin`, `session.category`, `session.filter`, `session.clear_filter`, `session.collapse_category`, `session.expand_category`, `session.archive`, `session.unarchive`, `session.delete`, `session.rename`, `session.show_archived`, `session.hide_archived`.
- Supported task actions: `task.plan.create`, `task.update`, `task.done`, `task.start`, `task.fail`, `task.cancel`.
- Supported agent actions: `agent.create`, `agent.profile.update`, `agent.role.update`, `agent.model.update`, `agent.stop`, `agent.delete`.
- Supported delegation action: `delegate.create`.
- Supported memory action: `memory.candidate`.
- `delegate.create` must carry `routing`, `work_order`, `capability_contract`, `context_contract`, and `output_contract`.
- `delegate.create.work_order.objective` is the policy-gate source of truth. Capability fields such as `tools_forbidden:["deploy","email.send"]` must not trigger deployment or external-send approval by themselves.
- Generated `[Shuheng AgentTask Envelope v2]` prompt blocks must be parsed by `control_protocol.py`. `agenttask_payload_from_prompt()` extracts only a valid JSON object envelope; `policy_relevant_subagent_prompt_text()` must prefer `work_order.objective`, then top-level `objective`, then the original prompt. `explicit_policy_action_for_subagent_task()` owns only explicit structured fields in this order: top-level `policy_action`, top-level `approval_required_for`, nested `approval.policy_action`, nested `approval.approval_required_for`, and nested `capability_contract.policy_action`; string values are stripped/lowercased with hyphens normalized to underscores, and list values use the first non-empty item. `inferred_policy_action_for_subagent_task()` owns deterministic text/role/write-policy inference over explicit facts supplied by the app facade; `app.py` may keep `infer_policy_action_for_subagent_task(sub, prompt)` only as a wrapper that derives `normalized_subagent_role(sub.role)` and `role_write_policy(role)` before delegating.
- `agent.create` is ephemeral by default. Long-running, scheduled, recurring, or dedicated responsibilities must be expressed with explicit structured fields such as `lifecycle:"persistent"` or `persistent:true`; the runtime must not infer lifecycle from `name`, `profile`, visible prose, or other natural-language descriptions.
- `agent.create` may carry `model`, `default_model`, or `model_name`; after create-or-reuse the runtime applies that value as the target subagent's default model through the same validation path as `agent.model.update`.
- `agent.model.update` / `/agent model <agent> <model|inherit>` can target persistent or temporary subagents. Persistent subagents save the default model in persistent metadata; temporary subagents save it in their session-scoped temp metadata.
- Clearing a subagent default model with `inherit` / `global` / `clear` must restore the configured global default model from `/model` (`mixin_config.llm_nos[0]`) when the runtime has that model available, not blindly switch to model index 0.
- `main_orchestrator` is reserved for the main Shuheng runtime only. Any subagent creation, subagent role update, subagent command parsing, or loaded subagent metadata that requests `main_orchestrator` must normalize the subagent role to `specialist` and surface a bounded user-visible note instead of creating a main-orchestrator subagent.
- Reuse intent must be explicit. `reuse_policy:"force_new"` / `force_new:true` forces a new agent; visible prose such as "do not reuse" is not a runtime signal unless the model also emits the structured field.
- Plan binding must be explicit. Controls that belong to a plan step must carry `plan_step_id`, `parent_task_id`, or an equivalent explicit step reference; the runtime must not bind steps by matching words like "self-introduction", "chat", or "summary".
- Executable `<shuheng-control>` blocks are only for real operations. Capability explanations, tutorials, and examples must not include literal executable tags; use escaped text such as `&lt;shuheng-control&gt;...&lt;/shuheng-control&gt;` or show only the JSON payload.
- Literal `<shuheng-control>` snippets inside ordinary Markdown/code/tool-output fences are display text, not executable control blocks, and must not emit parse-error system messages. Only top-level hidden tags, explicit `shuheng-control` fences, and opt-in JSON recovery fences are executable.
- Automatic current-session title maintenance is an allowed `session.rename` control exception and the only automatic persisted-title path: the main runtime may emit it at the end of a normal reply when the title is stale or misleading, and must stay silent when the title is already accurate.
- When a real control block is needed, append it after all user-visible prose. Do not place hidden controls in the middle of a visible section, because stripping the control block will leave the visible answer looking truncated.
- Inline-code labels such as `` `<shuheng-control>` `` in visible prose are not executable control starts and must not consume a later real closing tag.
- `install_tui_control_hint()` must replace any previous historical TUI hint block before installing the current `shuheng-control.v2` hint, and repeated installation must leave exactly one current hint block per backend prompt.
- Protocol parser helpers must have one source of truth in `src/shuheng/control_protocol.py`; do not redefine `extract_tui_controls()`, `strip_tui_controls()`, `lifecycle_is_persistent()`, `subagent_control_persistence_intent()`, `subagent_control_force_new_intent()`, `control_result_continuation_*()` helpers, `control_explicitly_requests_continuation()`, `format_control_result_continuation_prompt()`, `format_agent_control_result()`, `explicit_policy_action_for_subagent_task()`, `inferred_policy_action_for_subagent_task()`, `policy_relevant_subagent_prompt_text()`, `agenttask_*()` helpers, or schema/action constants inside `app.py`.
- `src/shuheng/control_protocol.py` must not import curses, GenericAgent runtime classes, or mutable TUI `State`. It may depend on quarantined compatibility cleanup from `compat_legacy.py` to strip retired markup without making retired vocabulary executable.

### 4. Validation & Error Matrix

- Missing `schema_version:"shuheng-control.v2"` on a batch envelope -> no controls are extracted.
- Missing `schema_version:"agenttask.v2"` on a standalone action -> no controls are extracted.
- Unknown action -> ignored during extraction.
- Historical hidden markup -> stripped by quarantine compatibility cleanup only, not executed.
- Previous system hint block present in a backend extra prompt -> removed before the current hint is installed.
- Current hint already present in a backend extra prompt -> do not append another copy.
- Invalid JSON -> ignored.
- Invalid JSON inside an ordinary code/tool-output fence -> ignored as display text without a parse-error system message.
- `agent.create` with explicit lifecycle markers such as `lifecycle:"ephemeral"` / `temporary:true` -> creates an ephemeral session agent.
- `agent.create` with `role:"main_orchestrator"` -> creates a bounded `specialist` subagent with a note that `main_orchestrator` is main-runtime only.
- `agent.role.update` or `/agent role ... main_orchestrator` -> never assigns `main_orchestrator` to a subagent; the requested role is normalized to `specialist`.
- `agent.create` with recurring/daily/archive-building responsibility language but without explicit persistent lifecycle fields -> remains ephemeral.
- `agent.create` with `lifecycle:"persistent"` / `persistent:true` -> creates a persistent subagent under `SUBAGENTS_DIR`.
- `agent.create` with `default_model:"beta"` -> creates or reuses the subagent and applies `beta` as that agent's default model if the model config exists.
- `agent.model.update` on a temporary subagent -> updates session-scoped temp metadata and applies the model to its live agent when idle.
- `agent.model.update` with `inherit` -> clears the subagent override and applies the current global default model when available.
- `shuheng-control` JSON that only misses trailing `}` / `]` closers -> repair the missing tail and execute if it parses into known actions.
- Visible prose containing inline-code `` `<shuheng-control>` `` followed by a real control block -> parse and execute only the real control block, keep the inline label visible, and do not report parse_error.
- Unrepairable `shuheng-control` JSON -> add an `Agent 控制结果` parse-error message instead of silently swallowing the control block.
- `delegate.create` without a resolvable target -> runtime reports missing subagent target.
- `agent.delete` on a running or aborting subagent -> runtime refuses deletion and asks for a stop first.
- `agent.delete` on an idle subagent -> soft-delete from the TUI list, retain the original directory for audit, and persist `deleted:true`.
- Risky work-order objective -> policy gate queues or rejects according to policy rules.

### 5. Good/Base/Bad Cases

- Good: Batch envelope creates a plan, creates a researcher, then delegates with full routing/work/output contracts.
- Good: A user asks "what can subagents do?" and the assistant answers in visible prose without emitting `<shuheng-control>`.
- Good: A search result shows source code containing `f'<shuheng-control>{{...` inside a `python` fence; Shuheng keeps it as text and emits no parse-error control result.
- Good: A model mistakenly requests `role:"main_orchestrator"` for a persistent subagent; Shuheng creates a `specialist` subagent and reports that the main-orchestrator role is reserved.
- Base: Single `agenttask.v2` action in a JSON fence is extracted only when the action is known.
- Bad: A visible "example" section contains a literal `<shuheng-control>` block; the runtime will execute and strip it, leaving the section blank.
- Base: A visible diagnosis says `` `<shuheng-control>` 标签没正确闭合 `` and then appends a real `<shuheng-control>{...}</shuheng-control>` block; the inline label is display text only.
- Bad: Bare JSON without the required current schema envelope is ignored.
- Bad: A current envelope with an unknown or non-dotted action name is ignored by the generic schema boundary.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `shuheng-control.v2` extraction, JSON-fence extraction, current hint install de-duplicates and replaces previous hints, auto-continuation prompt examples, subagent creation, explicit lifecycle handling, soft deletion, delegation, secret-control isolation, and policy-gate behavior.
- Quarantine checks may assert that historical hidden markup is stripped but must not treat it as an executable protocol.
- `scripts/check_policy_gates.py` must assert common missing-tail JSON repair for `<shuheng-control>` and visible parse-error reporting for unrepairable control JSON.
- `scripts/check_policy_gates.py` must assert inline-code `<shuheng-control>` labels do not capture later real control blocks.
- `scripts/check_policy_gates.py` must assert ordinary code/tool-output fences containing literal `<shuheng-control>` examples are not extracted, stripped, or reported as parse errors.
- `scripts/check_policy_gates.py` must assert subagent creation, `/agent new` role parsing, role updates, saved metadata, and loaded metadata normalize `main_orchestrator` to `specialist` for subagents while preserving the main runtime's `main_orchestrator` role.
- `scripts/check_policy_gates.py` must assert per-subagent default models can be set for persistent and temporary subagents, persist to the correct metadata scope, apply to the live runtime when idle, and clear back to the configured global default.
- `scripts/check_policy_gates.py` must assert `app.py` re-exports key protocol helpers from `shuheng.control_protocol` and that the protocol module does not import curses.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/control_protocol.py scripts/check_policy_gates.py` must pass.
- `python3 scripts/check_policy_gates.py` must pass.
- `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass when validating an optional legacy GenericAgent provider checkout.

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

## Scenario: AgentTask Policy Action Source Of Truth

### 1. Scope / Trigger

- Trigger: AgentTask prompt envelope parsing or subagent-task policy-action inference is changed, moved, or extended.
- Applies to: `src/shuheng/control_protocol.py`, the compatibility wrapper `infer_policy_action_for_subagent_task(sub, prompt)` in `src/shuheng/app.py`, `policy_gate_for_subagent_task(...)`, Secret subagent dispatch, scheduled subagent dispatch, tests, and policy gates.
- Non-goal: This does not move policy decisions, approval queueing, ledgers, runtime dispatch, `SubAgentRuntime`, role template lookup, Secret Vault behavior, mutable `State`, artifacts, storage roots, dashboard, rendering, or command execution out of `app.py`.

### 2. Signatures

- `control_protocol.agenttask_payload_from_prompt(prompt: str) -> dict[str, Any]`
- `control_protocol.policy_relevant_subagent_prompt_text(prompt: str) -> str`
- `control_protocol.explicit_policy_action_for_subagent_task(prompt: str) -> str`
- `control_protocol.inferred_policy_action_for_subagent_task(prompt: str, *, role: str = "", write_policy: str = "") -> str`
- `app.infer_policy_action_for_subagent_task(sub: SubAgentRuntime, prompt: str) -> str`
- `app.policy_gate_for_subagent_task(sub: SubAgentRuntime, prompt: str, *, source: str, bus_task_id: str, parent_task_id: str = "", task_title: str = "", queue_if_required: bool = True) -> PolicyDecision`

### 3. Contracts

- `agenttask_payload_from_prompt(...)` only parses the generated `[Shuheng AgentTask Envelope v2]` block and returns `{}` for missing, invalid, or non-object payloads.
- `policy_relevant_subagent_prompt_text(...)` must use only `work_order.objective`, then top-level `objective`, then the original prompt. Capability text, `tools_forbidden`, tool names, boundaries, non-goals, and examples are not policy-source text.
- `explicit_policy_action_for_subagent_task(...)` has higher precedence than text inference. It checks fields in this order: top-level `policy_action`, top-level `approval_required_for`, `approval.policy_action`, `approval.approval_required_for`, and `capability_contract.policy_action`.
- Explicit string values are stripped, lowercased, and hyphen-normalized to underscores. Explicit list values use the first non-empty item only.
- `inferred_policy_action_for_subagent_task(...)` owns the deterministic keyword and role/write-policy inference table. It accepts only explicit facts from the app facade: prompt, normalized role, and role write policy.
- Inference order is fixed: explicit action -> policy-relevant objective text keywords -> ops privileged-operation tokens -> `write_policy=="single_writer"` repo-write fallback -> `read_only`.
- `app.infer_policy_action_for_subagent_task(...)` may only derive `role = normalized_subagent_role(sub.role)` and `write_policy = role_write_policy(role)` before delegating to `control_protocol.inferred_policy_action_for_subagent_task(...)`.
- `policy_gate_for_subagent_task(...)` remains app-owned because it creates `PolicyDecision` payloads, queues approvals, references subagent identity, writes gate metadata, and owns Orchestrator side effects.
- `src/shuheng/control_protocol.py` must remain a restricted protocol module: no curses, no `State`, no `SubAgentRuntime`, no ledger stores, no approval queue writes, no runtime dispatch, no Secret Vault storage, no dashboard/rendering/command ownership.

### 4. Validation & Error Matrix

- Missing AgentTask envelope -> payload `{}`, policy text is the original prompt, explicit action is `""`.
- Invalid AgentTask JSON -> payload `{}`, policy text is the original prompt, explicit action is `""`.
- AgentTask envelope contains `work_order.objective:"read docs"` and `capability_contract.tools_forbidden:["deploy","email.send"]` -> inferred action is `read_only`, not `deploy` or `external_send`.
- AgentTask envelope contains `policy_action:"Deploy-Service"` -> inferred action is `deploy_service` even if objective contains unrelated secret-like words.
- AgentTask envelope contains `approval_required_for:["", "ignored"]` and nested approval policy -> first non-empty field in the documented field order wins.
- Prompt text contains `api key`, `secret`, `token`, `credential`, `password`, `密码`, `密钥`, `凭据`, or `令牌` in the policy-relevant objective -> inferred action is `access_secret`.
- Prompt text contains deploy/release/production, payment, external-send, publish, delete-file, permission-policy, or high-risk-batch tokens in the policy-relevant objective -> inferred action follows the current keyword table in `control_protocol.py`.
- Role is `ops` and policy-relevant text contains `sudo`, `root`, `systemctl`, `pacman`, `docker`, `firewall`, `ufw`, `iptables`, `内核`, `服务`, or `重启` -> inferred action is `long_running_privilege_escalation`.
- Role write policy is `single_writer` and no earlier action matched -> inferred action is `repo_write`.
- Role write policy is not `single_writer` and no earlier action matched -> inferred action is `read_only`.

### 5. Good/Base/Bad Cases

- Good: A generated AgentTask delegate has `work_order.objective:"read local docs and summarize"` plus `tools_forbidden:["deploy","email.send"]`; policy inference returns `read_only` because forbidden capabilities are not the requested operation.
- Good: A generated AgentTask delegate explicitly sets `approval.policy_action:"deploy"`; policy inference returns `deploy` before reading objective text.
- Good: An ops subagent receives objective text `sudo systemctl restart service`; policy inference returns `long_running_privilege_escalation` and the app-owned policy gate decides whether approval is required.
- Base: A coder subagent receives ordinary implementation work with no risky tokens; inference returns `repo_write` from `write_policy:"single_writer"`.
- Base: A researcher subagent receives ordinary summarization work with no risky tokens; inference returns `read_only`.
- Bad: `app.py` keeps a second keyword table for `api key`, `deploy`, `publish`, or `sudo`, causing policy drift from `control_protocol.py`.
- Bad: `control_protocol.py` imports `SubAgentRuntime` or `State` so it can inspect role templates directly.
- Bad: Policy inference scans `capability_contract.tools_forbidden` and treats a safety boundary as a requested risky action.

### 6. Tests Required

- `tests/test_control_protocol.py` must assert app alias parity for `agenttask_payload_from_prompt(...)`, `policy_relevant_subagent_prompt_text(...)`, `explicit_policy_action_for_subagent_task(...)`, and `inferred_policy_action_for_subagent_task(...)`.
- `tests/test_control_protocol.py` must cover missing/invalid/non-object envelope fallback, `work_order.objective` precedence, top-level objective fallback, and empty-objective fallback.
- `tests/test_control_protocol.py` must cover explicit policy-action field order, string normalization, list handling, and explicit-over-text precedence.
- `tests/test_control_protocol.py` must cover inferred actions for access-secret, spend-money, deploy, external-send, publish, delete-file, modify-permission-policy, high-risk batch, ops privileged operations, single-writer repo-write fallback, and read-only fallback.
- `tests/test_control_protocol.py` must include a case where `tools_forbidden:["deploy","email.send"]` does not trigger deployment or external-send approval when the objective is read-only.
- `tests/test_control_protocol.py` must assert `app.infer_policy_action_for_subagent_task(...)` delegates through role/write-policy facts for representative coder, ops, researcher, and read-only prompts.
- `scripts/check_policy_gates.py` must assert `inferred_policy_action_for_subagent_task.__module__ == "shuheng.control_protocol"` and `app.inferred_policy_action_for_subagent_task is control_protocol.inferred_policy_action_for_subagent_task`.
- `scripts/check_policy_gates.py` must assert app-local duplicate keyword-table ownership is absent, including `POLICY_ACTION_KEYWORD_CHECKS` and `OPS_PRIVILEGED_OPERATION_TOKENS`.
- `scripts/check_policy_gates.py` must keep the protocol module no-curses/no-runtime-class boundary green.
- Targeted verification for this boundary is `python3 -m py_compile src/shuheng/app.py src/shuheng/control_protocol.py tests/test_control_protocol.py scripts/check_policy_gates.py`, `python3 -m pytest -q tests/test_control_protocol.py -p no:cacheprovider`, and `python3 scripts/check_policy_gates.py`.

### 7. Wrong vs Correct

#### Wrong

```python
# app.py
def infer_policy_action_for_subagent_task(sub, prompt):
    text = policy_relevant_subagent_prompt_text(prompt).lower()
    if "deploy" in text or "api key" in text:
        ...
```

#### Correct

```python
# app.py
def infer_policy_action_for_subagent_task(sub: SubAgentRuntime, prompt: str) -> str:
    role = normalized_subagent_role(sub.role)
    return inferred_policy_action_for_subagent_task(
        prompt,
        role=role,
        write_policy=role_write_policy(role),
    )
```

#### Wrong

```python
# control_protocol.py
from shuheng.app import SubAgentRuntime, role_write_policy
```

#### Correct

```python
# control_protocol.py
def inferred_policy_action_for_subagent_task(prompt: str, *, role: str = "", write_policy: str = "") -> str:
    ...
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
- The unified manager must also let the user set per-subagent default models from the same `/model` panel: `g` assigns the selected model to the current subagent target, `c` clears that target back to global inheritance, and `o` cycles the target across available subagents.
- The subagent target row must initialize to the active subagent chat/home when present, otherwise to the first available subagent, and must show readable name/scope/default-model state without dumping opaque internal ids into the normal panel.
- When `/model` is opened from an active subagent chat/home, `Enter` / `s` applies the selected model to that subagent target's default model. From the main page, `Enter` / `s` continues to switch the main current dialogue model.
- Adding a provider must not require `/models` endpoint compatibility when the user has supplied a concrete manual `Model`. If `/models` probing fails but the new entry has a complete Base URL and Model, save the single manual entry, show the probe failure as a warning, and direct the user to `t` test or Enter switch.
- Manual fallback saving is only for the add-provider path. Existing-row model extraction with `p` must keep the stricter behavior: a failed `/models` probe does not mutate the configured model list.
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
- Add provider with a working manual `Model` but a 404/unsupported `/models` endpoint -> the provider/model is still saved once, the warning says `/models 提取失败`, and no duplicate is created if the same Base URL + Model already exists.
- Add provider with no manual `Model` and a failed `/models` endpoint -> no entry is saved, because runtime providers cannot route an empty model id.
- Selected row belongs to a different active tab after reload/edit/delete -> normalize selection to the first visible row in the active category.
- Active provider tab has no visible rows -> display a no-models-in-provider message and keep navigation safe.
- Active `常用` tab -> display configured recent models in recent order and keep provider switching/navigation behavior unchanged.
- Many provider tabs -> vertical rail scrolls around the active provider without changing model-selection up/down behavior.
- Runtime cannot find a named model -> error tells the user to reload from `/model`.

### 5. Good/Base/Bad Cases

- Good: `/model` opens one panel where the user can switch the current dialogue model, set the default, add a provider, extract provider models, test a model, and batch validate all models grouped by supplier.
- Good: `/model` lets a user keep the selected model row and choose whether it applies to the current dialogue, the global default, or a selected subagent default without leaving the model manager.
- Good: `/model` lets a user set `context_win:1050000` for a large-window OpenAI-compatible model without editing `mykey.py` by hand.
- Good: A custom OpenAI-compatible provider whose `/models` route is unavailable still appears in the model list when the user filled the exact model id manually.
- Good: Providers render as a left-side vertical list, and the filtered model list renders to the right.
- Good: `常用` appears as a peer rail item when recent configured models exist, while empty common providers stay grey until configured.
- Good: DeepSeek and OpenAI-compatible entries with known template base URLs appear under `DeepSeek` and `OpenAI`, not together under one broad `OpenAI` protocol category.
- Base: `/llm` and `/models` still work for users who type them directly, but they are absent from `/help`, README command tables, and command completion.
- Base: A custom endpoint such as `https://api.example.invalid/v1` appears under a stable `example.invalid` tab.
- Bad: `/llm` appears as a normal command row, because that splits the visible command ontology again.
- Bad: `/model` opens a switch-only panel that cannot add/edit/delete or probe provider models.
- Bad: Forcing users to leave `/model` and type `/agent model <id> <model>` for ordinary per-subagent model assignment, because model routing would be split across two daily-use surfaces.
- Bad: Treating a failed `/models` probe during add as a hard failure when the user already supplied a manual Model, because many OpenAI-compatible gateways support chat/responses but not model listing.
- Bad: The model panel shows every known provider template as an empty tab.
- Bad: Provider labels are rendered as one long horizontal tab line that truncates useful providers on narrower terminals.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `/model` is present in `COMMANDS` and `/llm` / `/models` are absent.
- `scripts/check_policy_gates.py` must assert `/mo` completes to `/model` and hidden aliases do not complete.
- `scripts/check_policy_gates.py` must assert `/llm`, `/model`, and `/models` help text describes the unified manager and compatibility aliases.
- `scripts/check_policy_gates.py` must assert `/model` exposes `context_win` and saving/reloading model config preserves it.
- `scripts/check_policy_gates.py` must assert add-provider manual fallback saves a complete manual entry after `/models` probe failure and refuses duplicate Base URL + Model pairs.
- `scripts/check_policy_gates.py` must assert model category helpers group OpenAI, DeepSeek, custom endpoint, common-provider, and non-common configured providers correctly.
- `scripts/check_policy_gates.py` must assert the model manager renders a vertical provider rail and does not render the old horizontal `供应商 Tabs:` line.
- `scripts/check_policy_gates.py` must assert the model manager renders subagent default-model controls and that `/model` key handling can assign, cycle, and clear a subagent default model.
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
- Non-goal: These tools must never mutate sessions, tasks, agents, approvals, artifacts, memory, or files. Real state changes still require `shuheng-control.v2`.

### 2. Signatures

- Tool names exposed to the model are snake_case function tools: `agent_list`, `agent_get`, `agent_match`, `task_list`, `task_get`, `approval_list`, `artifact_list`, `capability_list`.
- User-facing documentation may refer to dotted names: `agent.list`, `agent.get`, `agent.match`, `task.list`, `task.get`, `approval.list`, `artifact.list`, `capability.list`.
- `agent_get` requires `target`.
- `agent_match` requires `objective`.
- `task_get` requires `task_id`.

### 3. Contracts

- Every response is JSON-safe and starts with `schema_version:"shuheng.query.v1"` plus `status:"ok"` or `status:"error"`.
- Query tools are installed by wrapping `agentmain.load_tool_schema()` and appending TUI schemas idempotently after every GenericAgent schema reload.
- Query handlers are installed by patching `agentmain.GenericAgentHandler` with `do_<tool_name>` methods.
- Runtime state is provided through `agent._shuheng_state`; if a handler has no bound state, the tool returns an error response instead of guessing.
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
- Bad: The model emits `<shuheng-control>` while only explaining available subagent capabilities.
- Bad: The model spawns a new OMP/IRC worker with a copied steward profile and reports "the persistent steward replied" instead of "a clone/persona simulation replied".

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert all query tool schemas are installed exactly once.
- Tests must assert handler methods exist and return `StepOutcome` with `next_prompt:"\n"`.
- Tests must assert `agent_list`, `agent_get`, and `agent_match` expose current subagent records, interaction modes, identity contracts, clone warnings, and recommend reuse when a matching idle agent exists.
- Tests must assert `task_list` hides terminal tasks by default and includes them with `include_completed:true`.
- Tests must assert `task_get` returns latest ledger details and approval references.
- Tests must assert `approval_list` does not inline raw payload bodies.
- `python3 -m py_compile src/shuheng/app.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

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
- Applies to: `src/shuheng/genericagent_provider.py`, compatibility re-exports from `src/shuheng/app.py`, runtime provider registration, model switching, subagent runtime preparation, query tools, and schedule tools.
- Non-goal: The provider module must not own TUI state mutation, curses rendering, ledgers, scheduler registries, Secret Vault storage, or subagent query implementation details.

### 2. Signatures

- Provider module: `src/shuheng/genericagent_provider.py`.
- Runtime configuration entrypoint: `configure_genericagent_provider_runtime(agentmain, generic_agent_cls, step_outcome_cls, is_state, tool_handlers, thread_factory=...)`.
- Compatibility re-exports from `app.py`: `TUI_AGENT_CONTROL_HINT`, `TUI_QUERY_TOOL_SCHEMAS`, `TUI_SCHEDULE_TOOL_SCHEMAS`, `install_tui_query_runtime()`, `install_tui_control_hint()`, and `GenericAgentRuntimeAdapter`.
- Handler methods installed on `agentmain.GenericAgentHandler`: `do_agent_list`, `do_agent_get`, `do_agent_match`, `do_task_list`, `do_task_get`, `do_approval_list`, `do_artifact_list`, `do_capability_list`, `do_schedule_create`, and `do_schedule_list`.

### 3. Contracts

- `genericagent_provider.py` owns the active GenericAgent-facing control hint, query tool schemas, schedule tool schemas, tool schema injection, `agentmain.load_tool_schema()` wrapping, `GenericAgentHandler` patching, `_shuheng_state` binding, `install_tui_control_hint()`, and `GenericAgentRuntimeAdapter`.
- `app.py` may re-export provider names for compatibility, but must not locally redefine the moved installers, handler patch functions, control-hint installer, or `GenericAgentRuntimeAdapter`.
- The provider module must not import `shuheng.app`, curses, or mutable TUI `State`. App-layer behavior is injected through `configure_genericagent_provider_runtime()`.
- Tool handlers remain app-layer callbacks because they read TUI state, subagent registries, ledgers, approvals, artifacts, Secret Vault state, gateway capabilities, and scheduler registries.
- Repeated `install_tui_query_runtime()` calls must append each query/schedule schema at most once and must not add duplicate handler side effects.
- A GenericAgent tool schema reload must re-append TUI tool schemas exactly once.
- Handler methods must return the configured `StepOutcome` class with `next_prompt:"\n"`.
- `GenericAgentRuntimeAdapter.create_agent()` creates the configured GenericAgent class, installs the tool runtime, and sets `inc_out:true`; `prepare_agent()` installs tools and the current control hint; `start_agent()` starts `agent.run()` in a daemon thread.

### 4. Validation & Error Matrix

- Provider module imported before configuration -> runtime installation and adapter creation fail explicitly with a configuration error.
- Missing bound TUI state on a handler call -> injected app-layer tool callback returns the standard TUI tool/query error response.
- Unknown tool kind -> provider returns a JSON-safe `shuheng.query.v1` error response instead of mutating state.
- Repeated provider configuration -> subsequent handler calls use the latest injected callback map because handler methods dispatch through provider runtime state.
- Provider source imports `shuheng.app`, curses, or TUI `State` -> boundary violation.
- `app.py` locally defines moved GenericAgent glue after the extraction -> boundary violation.

### 5. Good/Base/Bad Cases

- Good: `app.py` configures the provider with `agentmain`, `GenericAgent`, `StepOutcome`, `isinstance(value, State)`, and a map of `tui_tool_*` callbacks; the provider installs schemas and handler methods.
- Good: Model switching calls the provider's compatibility re-exported `install_tui_query_runtime()` and `install_tui_control_hint()` after selecting the backend model.
- Base: A future runtime provider adds its own adapter without importing curses or TUI state classes.
- Bad: `app.py` defines a second local `GenericAgentRuntimeAdapter` or local `do_agent_list` patch method.
- Bad: `genericagent_provider.py` imports `shuheng.app` to call `tui_tool_agent_list()` directly, creating a reverse dependency from provider to composition.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert app compatibility re-exports are identical to `shuheng.genericagent_provider` names.
- Tests must assert moved functions and `GenericAgentRuntimeAdapter` have `__module__ == "shuheng.genericagent_provider"`.
- Tests must assert `genericagent_provider.py` has no reverse import into `app.py` and no curses import.
- Tests must assert `app.py` no longer locally defines the moved GenericAgent glue functions or adapter class.
- Tests must preserve query/schedule schema idempotency, handler method presence, `StepOutcome(next_prompt:"\n")`, state-bound tool dispatch, and control-hint de-duplication checks.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/genericagent_provider.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

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

## Scenario: Runtime Dispatch Helper Module Boundary

### 1. Scope / Trigger

- Trigger: Provider-neutral runtime identity, metadata, request-construction, or task-submit helper logic is moved out of `src/shuheng/app.py`.
- Applies to: `src/shuheng/runtime_dispatch.py`, compatibility wrappers in `src/shuheng/app.py`, `RuntimeTaskRequest` construction, OMP native session/context usage readers, runtime task submission fallback, policy gates, and unit tests.
- Non-goal: This does not move runtime stream queue consumption, TUI message mutation, subagent task/chat state transitions, scheduler dispatch, Web Console runtime pumping, or runtime context-pack full/ref prompt selection.

### 2. Signatures

- Dataclass owner: `src/shuheng/runtime.py` owns `RuntimeTaskRequest` and `RuntimeTaskEvent`.
- Lower-level helper module: `src/shuheng/runtime_dispatch.py`.
- Compatibility wrappers in `app.py`:
  - `agent_runtime_provider_id(agent)`.
  - `is_ohmypi_runtime_agent(agent)`.
  - `ohmypi_native_session_file(agent)`.
  - `ohmypi_native_context_usage(agent)`.
  - `runtime_task_request_for_agent(...)`.
  - `put_agent_runtime_task(agent, request)`.

### 3. Contracts

- `runtime_dispatch.py` must not import `shuheng.app`, `.app`, `app`, `curses`, UI renderers, command handlers, `State`, `SubAgentRuntime`, `PanelItem`, or `RenderLine`.
- `runtime_dispatch.py` may import `RuntimeTaskRequest` from `runtime.py`; `runtime.py` remains the schema/dataclass owner.
- `app.py` remains the compatibility facade and delegates the wrapper names to `runtime_dispatch.py`.
- `runtime_task_request_for_agent(...)` must preserve every `RuntimeTaskRequest` field: task ids, provider id, agent id, role, objective, prompt, source, context-pack ref, model, permissions, approval policy, output contract, artifact refs, and metadata.
- Full prompts are allowed only inside the in-memory request object. Durable request records remain governed by `RuntimeTaskRequest.to_record()` and must store bounded `prompt_preview`, `prompt_chars`, context-pack refs, and artifact refs instead of raw prompt bodies.
- Provider id fallback is `"unknown"` when `_shuheng_runtime_provider_id` is missing or blank.
- Model fallback is an empty string when `agent.get_llm_name(model=True)` is missing or raises.
- If explicit `artifact_refs` is absent and `context_pack_ref` exists, the request artifact refs default to `[context_pack_ref]`.
- `put_agent_runtime_task(...)` must call `agent.put_runtime_task(request)` when available; otherwise it must fall back to `agent.put_task(request.prompt, source=request.source)`.
- OMP native context usage normalization accepts both `contextWindow` and `context_window`, computes percent when absent, rejects invalid/non-dict usage payloads, and returns `{}` when both tokens and context window are unavailable.

### 4. Validation & Error Matrix

- `runtime_dispatch.py` imports app/UI/state symbols -> policy gate fails.
- App wrapper request differs from module request for the same agent and args -> policy gate fails.
- Agent has blank provider id -> provider id is `"unknown"`.
- Agent model lookup raises -> request model is `""`.
- Agent lacks `put_runtime_task` but has `put_task` -> legacy submit path receives the original prompt and source.
- Agent has invalid OMP native usage -> metadata helper returns `{}`.
- Request has a context-pack ref and no explicit artifact refs -> artifact refs include that context-pack ref.

### 5. Good/Base/Bad Cases

- Good: `app.runtime_task_request_for_agent(...)` delegates to `runtime_dispatch.runtime_task_request_for_agent(...)` and returns an identical frozen dataclass.
- Good: `runtime_dispatch.py` builds a request from a generic agent object without reading `State` or any app-global path.
- Base: `runtime_context_prompt_for_agent(...)` stays in `app.py` because it mutates OMP per-agent context prompt counters and calls app-level context formatting wrappers.
- Bad: `runtime_dispatch.py` imports `State` so it can decide which stream queue to update.
- Bad: `runtime_dispatch.py` appends traces or task-ledger rows directly.
- Bad: `runtime_dispatch.py` stores the raw prompt in durable JSONL records.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `runtime_dispatch.py` has no reverse app/UI dependency and that app wrappers preserve request/metadata parity.
- Tests must cover provider id fallback, OMP detection by provider id or provider module, OMP native session/context usage helpers, request field preservation, model fallback, artifact-ref defaulting, and `put_runtime_task` vs `put_task` fallback.
- Existing runtime provider tests must continue proving `RuntimeTaskRequest.to_record()` keeps bounded durable prompt records and OMP runtime events preserve request/context-pack refs.
- Release verification must keep `python3 scripts/check_policy_gates.py`, Ruff, pytest, compileall, runtime smoke, build, wheel smoke, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```python
from shuheng.app import State

def put_agent_runtime_task(state: State, request):
    append_trace(request.task_id, "runtime_task_requested", payload={"prompt": request.prompt})
    state.agent.put_runtime_task(request)
```

#### Correct

```python
def put_agent_runtime_task(agent, request):
    if hasattr(agent, "put_runtime_task"):
        return agent.put_runtime_task(request)
    return agent.put_task(request.prompt, source=request.source)
```

## Scenario: Oh My Pi Runtime Provider

### 1. Scope / Trigger

- Trigger: Shuheng treats Oh My Pi / OMP as the default local runtime core.
- Applies to: `src/shuheng/ohmypi_provider.py`, runtime provider registration in `src/shuheng/app.py`, runtime registry records, provider selection, Shuheng memory prompt injection, app-injected TUI host tool registration, typed host-tool routing, governed proposal routing, memory candidate signaling, runtime task request/event records, RPC queue/event mapping, and OMP usage-to-token-registry bridging.
- Non-goal: This provider must not own curses rendering, mutable TUI `State`, GenericAgent tool schema injection, TUI approval storage, scheduler registries, or first-class TUI subagent ledger mutation.

### 2. Signatures

- Provider module: `src/shuheng/ohmypi_provider.py`.
- Provider id: `ohmypi`.
- Runtime adapter: `OhMyPiRuntimeAdapter(RuntimeAdapter)`.
- Queue-compatible wrapper: `OhMyPiRpcAgent`.
- Provider metadata helper: `ohmypi_provider_spec(root_dir, harness_dir, recent_models_path, schedules_path, binary=None, command=None)`.
- App-layer refresh helper: `refresh_agent_runtime_model_config(agent)`.
- Provider-local refresh method: `OhMyPiRpcAgent.refresh_configured_models(models, env=None, command=None)`.
- Provider-neutral runtime envelopes: `RuntimeTaskRequest` and `RuntimeTaskEvent` in `src/shuheng/runtime.py`.
- RPC command helpers: `resolve_ohmypi_binary(binary=None)` and `ohmypi_rpc_command(binary=None, extra_args=None, append_system_prompt=None)`.
- Memory append prompt helpers: `write_ohmypi_memory_prompt(root_dir, harness_dir)` and `ohmypi_memory_prompt_path(harness_dir)`.
- Isolated runtime helpers: `ohmypi_runtime_root(harness_dir)`, `ohmypi_isolated_agent_dir(harness_dir)`, `ohmypi_config_path(agent_dir)`, `ohmypi_models_path(agent_dir)`, `write_ohmypi_runtime_files(...)`, and `ohmypi_subprocess_env(...)`.
- Isolated runtime records: `OhMyPiRuntimeConfig` and `OhMyPiRuntimeModel`.
- Compatibility TUI host tools exposed to OMP: `shuheng_query` and `shuheng_propose`.
- Typed TUI host tools exposed to OMP include `agent_list`, `agent_get`, `agent_match`, `task_list`, `task_get`, `approval_list`, `artifact_list`, `capability_list`, `schedule_list`, `memory_context_get`, `proposal_submit`, `memory_candidate_submit`, and `schedule_create`.
- Read-only host tool definition helper: `ohmypi_tui_readonly_host_tool_definitions()`.
- Typed read-only host tool definition helper: `ohmypi_typed_readonly_host_tool_definitions()`.
- Governed proposal host tool definition helper: `ohmypi_tui_proposal_host_tool_definition()`.
- Typed governed host tool definition helper: `ohmypi_typed_governed_host_tool_definitions()`.
- Combined host tool definition helper: `ohmypi_tui_host_tool_definitions()`.
- Combined host tool callback helper: `ohmypi_tui_host_tool_handler(state=None)`.
- Backward-compatible query callback helper: `ohmypi_tui_query_host_tool_handler(state=None)`.
- Environment keys:
  - `SHUHENG_HOME` overrides the Shuheng-owned storage root; legacy internal `SHUHENG_HOME` remains an accepted compatibility override.
  - unset `SHUHENG_RUNTIME_PROVIDER` selects `ohmypi`.
  - `SHUHENG_RUNTIME_PROVIDER=genericagent` selects the optional legacy GenericAgent adapter only when a valid legacy checkout is available.
  - `SHUHENG_OHMYPI_BIN` overrides the executable.
  - `SHUHENG_OHMYPI_ARGS` appends shell-split extra CLI arguments.
- OMP subprocess environment:
  - `PI_CODING_AGENT_DIR` must point to the Shuheng-owned isolated OMP agent directory under `${AGENT_HARNESS_DIR}/runtime/ohmypi/agent`.
  - Generated per-process API key env vars use `SHUHENG_OMP_API_KEY_<digest>` and must be passed only through the OMP child process env.
- Default RPC command shape: `<resolved-omp> --mode rpc --no-title --approval-mode yolo --append-system-prompt <generated-memory-file>`.

### 3. Contracts

- `OhMyPiRpcAgent.put_task(prompt, source="", images=None)` must return a `queue.Queue` immediately and remain as the compatibility shim for existing hot paths.
- `OhMyPiRpcAgent.put_runtime_task(RuntimeTaskRequest)` must accept provider-neutral task requests and preserve `task_id`, `provider_id`, `agent_id`, `role`, `objective`, `source`, `context_pack_ref`, artifact refs, permissions, approval policy, output contract, and metadata in normalized runtime events.
- Durable `runtime.task_request.v1` records must not store the full prompt; they store bounded `prompt_preview`, `prompt_chars`, and artifact/context refs. The full prompt remains in-memory for runtime dispatch only.
- Oh My Pi RPC `message_update` frames with `assistantMessageEvent.type:"text_delta"` map to queue items shaped as `{"next": <delta>, "source": "ohmypi"}`.
- OMP may emit a standalone `"."` text delta as a tool-turn placeholder or as real punctuation inside normal prose, numbered lists, or decimals. The provider must delay standalone dot deltas until the next visible text delta: append them to the next text delta for normal prose, drop them when a process/tool block starts, and flush them before a normal terminal completion.
- Oh My Pi non-final process frames must be normalized into the existing Shuheng foldable process text protocol instead of adding a second renderer. The emitted text uses `**LLM Running (Turn N) ...**`, `<summary>...</summary>`, tool args fences, and result fences that `render_assistant_text(..., fold_process:true)` already understands.
- OMP `message_update` thinking/reasoning deltas are buffered and emitted as a bounded `<thinking>...</thinking>` process turn before the next visible text/tool/final event. The final assistant reply must remain normal assistant text, not hidden inside a thinking block.
- OMP `tool_execution_start` / `tool_execution_end` frames and Shuheng `host_tool_call` / `host_tool_result` bridge activity must become bounded, redacted tool process turns so tool args/results are folded by default while the final reply remains visible.
- Generated OMP context packs, context refs, memory append prompts, and `memory_candidate_submit` descriptions must tell OMP to finish every user turn with a normal user-facing reply in the user's language. Tool results, `Result:` status lines, and memory-candidate submitted/deferred notices must not replace the final reply.
- Generated OMP context packs, context refs, and memory append prompts must mark Shuheng context metadata as internal execution metadata. Follow-up pronouns such as `这个`, `这个东西`, `它`, `this`, or `that` must resolve to the recent visible conversation/task topic unless the user explicitly names the context pack/ref.
- Generated OMP context packs, context refs, and memory append prompts must treat explicit user requests to create a persistent/long-term Shuheng agent as an executable control requirement: success requires `agent.create` with `lifecycle:"persistent"` / `persistent:true`, or reuse of a matching existing persistent `agent_id`. Scripts, schedules, memory candidates, or future-agent suggestions alone do not satisfy the request.
- OMP memory-candidate governance must reject target mismatches from declared candidate responsibility metadata. If a candidate declares `target_role`, `scope`, or `responsibility`, the selected persistent subagent's role/name/profile must match that declaration; otherwise the candidate must not be queued or approved.
- Process normalization belongs inside `ohmypi_provider.py`; `app.py` must not contain OMP-specific RPC parsing or a second OMP renderer.
- OMP process args/results included in assistant text must be bounded and secret-redacted before entering the display queue, history, artifacts, traces, or memory-candidate extraction.
- OMP memory-candidate signal extraction must strip normalized process markers, `<thinking>` blocks, tool args, and tool result fences before deciding whether a durable candidate exists.
- Oh My Pi RPC `turn_end` captures the completed visible turn but must not release the active prompt until `agent_end`, because real OMP may still be finalizing UI/status events and will reject a next prompt as `Agent is already processing`.
- Oh My Pi RPC `turn_end` with `stopReason:"toolUse"` or non-empty `toolResults` is an intermediate tool turn and must not start the short missing-`agent_end` grace fallback, because real OMP may need another model turn to produce the final assistant reply after tools finish.
- A Shuheng host tool result must start a longer host-tool follow-up watchdog. If no `agent_end` or visible assistant text arrives before that watchdog expires, the provider emits a bounded `[Oh My Pi]` fallback `done` item summarizing the host tool result so the TUI leaves running state without pretending it is a model-authored final reply.
- Oh My Pi RPC `agent_end` maps the active prompt to one queue item shaped as `{"done": <buffer>, "source": "ohmypi"}`. If `agent_end` is absent, a short provider-owned grace fallback may complete from the captured `turn_end` payload for compatibility with older/fake streams.
- OMP terminal events are necessary but not sufficient for normal completion: before emitting `done`, the provider must validate that the visible final reply does not look structurally incomplete, such as ending on a connector, soft break punctuation, or unclosed Markdown/code.
- If a terminal visible final reply looks incomplete, the provider keeps the same active prompt and same native OMP session, materializes any terminal-only final text into the visible buffer, and sends a bounded internal continuation prompt. It must not release `is_running`, decrement unfinished task state, emit memory candidates, or mark the runtime task completed before the continuation resolves.
- If the reply remains incomplete after the bounded continuation cap, the provider emits an explicit incomplete terminal result and runtime event instead of silently treating the half reply as normal success.
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
- The provider module must not import `shuheng.app`, curses, or mutable TUI `State`.
- Oh My Pi unrestricted host tools remain disabled in provider metadata: `capabilities.host_tools:false`.
- The only allowed host tool bridge is app-injected TUI governance querying, typed read-only control-plane tools, and governed proposal routing: `capabilities.tui_readonly_host_tools:true`, `capabilities.tui_governed_proposal_tools:true`, and `capabilities.tui_typed_host_tools:true`.
- Provider metadata must advertise `capabilities.runtime_task_requests:true` and `capabilities.runtime_task_events:true` once OMP execution is wrapped by `runtime.task_request.v1` and `runtime.task_event.v1`.
- `OhMyPiRpcAgent` may register host tools through `set_host_tools` only from definitions injected by `app.py`; provider code must not invent writable tools or import TUI `State`.
- Embedded OMP must use a Shuheng-owned runtime root and must not read or write system-level `~/.omp/agent/config.yml`, `~/.omp/agent/models.yml`, sessions, auth storage, or cache as its active agent directory.
- Embedded OMP must run with the Shuheng app root as its subprocess `cwd`, while Shuheng harness paths, memory, ledgers, isolated OMP runtime files, and provider metadata use the `SHUHENG_HOME` / `${AGENT_HARNESS_DIR}` ownership boundary.
- `app.py` owns translation from Shuheng `/model` entries to isolated OMP `config.yml` and `models.yml`; `ohmypi_provider.py` owns only generic runtime file writing, subprocess env, OMP binary discovery, command construction, and RPC behavior.
- After `/model` save, edit, delete, default selection, or reload while the TUI is idle, Shuheng must rebuild the isolated OMP config files and refresh the current OMP wrapper's configured model list, child env, and command without requiring a TUI restart.
- `OhMyPiRpcAgent.load_llm_sessions()` must not overwrite Shuheng-projected `configured_models` with RPC `get_available_models` results when the app has already supplied a configured list. OMP's internal model discovery is only a fallback for unconfigured wrappers.
- `OhMyPiRpcAgent` must initialize its active local `llmclient` from the projected default model selector so the TUI model panel and status card do not depend on a later OMP `get_state` response to display the default.
- When Shuheng has supplied `configured_models`, OMP `get_state` responses may update native session/context usage but must not overwrite the current local model selection. Otherwise a stale state response can mix an old provider/model id with the newly selected entry's base URL.
- When Shuheng has supplied `configured_models`, OMP `set_model` / `cycle_model` confirmations may move the active index to a matching configured model and refresh context-window metadata, but must preserve Shuheng-projected display fields such as provider label, model id, and base URL.
- Refreshing `OhMyPiRpcAgent.configured_models` must preserve the current model by selector, display name, provider/model id, or model/base URL where possible, and update any pending model switch so the next lazy RPC startup sends the refreshed provider/model pair.
- OMP binary discovery order is explicit `binary` argument, `SHUHENG_OHMYPI_BIN`, `PATH` lookup for `omp`, then user-local Bun install at `$HOME/.bun/bin/omp`. A still-missing executable remains a visible startup error instead of mutating user shell configuration.
- Generated OMP `config.yml` must set `modelRoles.default` to the Shuheng default model selector when a complete matching `/model` entry exists.
- Generated OMP `config.yml` must set `todo.eager:"default"` and must not write boolean `true` or `"always"` by default. Eager todo forces first-turn `tool_choice:"todo"`, which thinking-mode OpenAI-compatible providers such as DeepSeek can reject before the model answers.
- Generated OMP `models.yml` must represent complete Shuheng OpenAI-compatible entries as custom OMP providers with `baseUrl`, `apiKey`, `api`, and `models[].id`; API keys must be referenced through child-process env var names instead of written as secrets in the generated file.
- Generated OMP API protocol must be inferred from explicit `api_mode` and known endpoint shape, not only from the historical config variable prefix. In particular, `https://open.bigmodel.cn/api/coding/paas/v4` and `https://api.z.ai/api/paas/v4` are OpenAI-compatible PAAS v4 bases and must generate `api:"openai-completions"` unless `api_mode:"responses"` explicitly requests Responses; `https://open.bigmodel.cn/api/anthropic` remains Anthropic Messages.
- Generated OMP `models.yml` must project `/model` `context_win` to OMP `models[].contextWindow`; if `max_tokens` is configured, it must project to `models[].maxTokens`.
- Incomplete Shuheng model entries without API key, base URL, or model id are skipped when generating OMP model providers.
- OMP runtime model rows exposed to the TUI must preserve enough provider/model/base URL metadata for `/model` current-session switching to call OMP `set_model` with structured `provider` and `modelId`.
- Embedded OMP must not auto-resume stale internal OMP sessions; Shuheng owns visible session history and resets the OMP RPC session when Shuheng opens a fresh main/temporary/restored runtime context.
- A long-running OMP process must receive at most one full `[Shuheng Context Pack]` prompt per Shuheng runtime session. Later context refreshes should pass a bounded `[Shuheng Context Ref]` with the artifact ref, so OMP history does not accumulate repeated full context packs.
- `shuheng_query` is read-only and must never mutate sessions, tasks, agents, approvals, artifacts, memory, or files.
- `shuheng_propose` accepts only bounded proposal payloads with `proposal_type:"shuheng_control"` or `proposal_type:"memory_candidate"`.
- `shuheng_propose` with `proposal_type:"shuheng_control"` must require a current-schema `shuheng-control.v2` envelope or `agenttask.v2` action object, validate that it maps to known current controls, and route execution through `apply_tui_controls_from_text(..., source="agent:ohmypi_host_tool")` so existing policy gates and ledgers remain the source of truth.
- `shuheng_propose` with `proposal_type:"memory_candidate"` must resolve the target subagent from the bound TUI `State` and call `queue_curated_memory_candidate(...)`; direct long-term memory writes remain forbidden.
- `shuheng_propose` results use `schema_version:"shuheng.proposal.v1"` and return JSON-safe `status`, `kind`, result lines/messages, ids, and artifact refs where available.
- Typed read-only tools must call the same app-layer query functions as the compatibility query endpoint. They must not mutate sessions, tasks, approvals, long-term memory, or ledgers.
- `memory_context_get` may generate a Shuheng-owned context-pack artifact and return `context_pack_ref` plus a JSON-safe pack. This is the allowed way for OMP to hydrate memory/context; it is not a long-term memory write.
- `memory_candidate_submit` must call the same governed memory-candidate path as `shuheng_propose` with `proposal_type:"memory_candidate"`.
- `proposal_submit` must call the same governed proposal path as `shuheng_propose`.
- `schedule_create` may create a TUI-owned schedule through the scheduler service; it must use the existing schedule registry and must not call OMP or any runtime directly.
- Host tool registration must happen after OMP emits `{"type":"ready"}` and before the first prompt command is sent for that process.
- OMP `host_tool_call` frames must be answered with `host_tool_result` using the same frame `id`.
- Host tool result payloads must be AgentToolResult-shaped JSON, with bounded redacted text under `content:[{"type":"text","text":"..."}]`.
- Unknown tools, missing handlers, invalid arguments, and callback failures must return `host_tool_result` with `isError:true` instead of crashing the stdout reader or active prompt.
- OMP `host_tool_cancel` frames must be accepted safely and must not mutate TUI state.
- OMP terminal error details from `message_end`, `turn_end`, or `agent_end` must map to a visible queue `done` item when frames carry `stopReason:"error"`, `errorMessage`, or `errorStatus`; error turns must not become empty assistant replies.
- Host URI schemes and TUI approval mapping remain disabled until a separate explicit task designs those governance contracts.
- Oh My Pi is the default runtime provider when `SHUHENG_RUNTIME_PROVIDER` is unset.
- GenericAgent must remain selectable with `SHUHENG_RUNTIME_PROVIDER=genericagent` when a valid legacy checkout is available.
- Missing GenericAgent must not break `import shuheng.app`, `python -m shuheng.app --help`, `python -m shuheng --help`, `shuheng-check`, or OMP provider registration.
- When GenericAgent discovery is disabled or absent, the runtime registry may contain only `ohmypi`; this is a healthy Shuheng core state, not a degraded core.
- The TUI should generate a bounded `Shuheng Layered Memory Guidance` append prompt from Shuheng-owned memory sources under `${SHUHENG_HOME}/memory` and pass it through `--append-system-prompt`.
- Oh My Pi completion output may emit memory candidate signals, and `shuheng_propose` may submit curated memory candidates, but long-term memory writes remain governed by TUI memory candidate records and human approval.
- Main OMP tasks and worker/subagent OMP tasks should include generated Shuheng context pack artifacts when using the structured runtime request path.
- OMP runtime events for requested tasks, host tool calls/results, completion, failure, and abort must be normalized into `runtime.task_event.v1` records and appended to Shuheng traces when a concrete task id exists.
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
- OMP `host_tool_call` for `shuheng_query` -> provider runs the app-injected read-only callback and sends a JSON-safe `host_tool_result`.
- OMP `host_tool_call` for a typed read-only tool such as `agent_list`, `schedule_list`, or `memory_context_get` -> app callback routes through the same control-plane query/context helpers and sends a JSON-safe `host_tool_result`.
- OMP `host_tool_call` for `memory_candidate_submit` -> app callback routes through `queue_curated_memory_candidate(...)` and returns candidate/approval/artifact refs when queued.
- OMP `host_tool_call` for `schedule_create` -> app callback writes a TUI-owned `scheduledtask.v1` row with default provider `ohmypi` when no explicit provider is supplied.
- OMP `host_tool_call` for `shuheng_propose` memory candidate -> app callback routes through `queue_curated_memory_candidate(...)` and returns a JSON-safe proposal result with candidate/approval/artifact refs when queued.
- OMP `host_tool_call` for `shuheng_propose` current-schema control -> app callback routes through `apply_tui_controls_from_text(...)` and returns control result lines.
- OMP `host_tool_call` for `shuheng_propose` with unknown proposal type, missing required fields, missing TUI state, unresolved target, invalid schema, or no known action -> callback returns `schema_version:"shuheng.proposal.v1"` with `status:"error"`.
- OMP `host_tool_call` for an unregistered tool -> provider sends `host_tool_result` with `isError:true`.
- OMP `host_tool_call` whose callback raises -> provider sends `host_tool_result` with `isError:true`.
- OMP `host_tool_cancel` -> provider records the cancellation safely and continues normal prompt handling.
- Complete Shuheng model entry -> isolated OMP `models.yml` gets one provider/model mapping and the child env gets a matching `SHUHENG_OMP_API_KEY_<digest>` value.
- Complete Shuheng model entry with historical `native_claude_config_*` name but PAAS v4 base such as `https://open.bigmodel.cn/api/coding/paas/v4` -> isolated OMP `models.yml` uses `api:"openai-completions"`, validation/probe use Bearer auth and `/chat/completions` / `/models`, and no `/v1/messages` suffix is appended.
- Complete Shuheng model entry with Anthropic base such as `https://open.bigmodel.cn/api/anthropic` -> isolated OMP `models.yml` uses `api:"anthropic-messages"` and validation/probe use `x-api-key` plus Anthropic Messages endpoints.
- Complete Shuheng model entry with `context_win:1050000` -> isolated OMP `models.yml` writes `contextWindow:1050000` for that model.
- Incomplete Shuheng model entry -> omitted from isolated OMP `models.yml`; no invalid OMP provider is generated.
- Selected Shuheng default model -> OMP command may include `--model <isolated-provider>/<model-id>` and isolated `config.yml` carries the same `modelRoles.default`.
- Selected Shuheng default model -> a new OMP wrapper must queue that selected model for confirmed `set_model` synchronization before the first prompt, because OMP native sessions can otherwise retain a previous workspace model even when the Shuheng UI displays the projected default.
- DeepSeek or another thinking-mode OpenAI-compatible model -> isolated OMP `config.yml` carries `todo.eager:"default"` so OMP does not send a forced `tool_choice:"todo"` before the first model answer.
- Existing OMP wrapper + changed `mykey.py` -> `refresh_agent_runtime_model_config(agent)` updates wrapper `configured_models`, regenerated env, command `--model`, and isolated files before the next switch/prompt.
- Existing OMP wrapper + stale `get_state` model payload after a current-session switch -> the status card keeps the newly selected configured model instead of displaying old provider/model fields with the new base URL.
- Existing OMP wrapper + `set_model` confirmation after a current-session switch -> the status card keeps the configured provider label/base URL while accepting matching context-window metadata.
- Existing OMP wrapper with an already selected model -> refresh keeps the matching selected model when it still exists and sends the refreshed provider/model id before the next prompt.
- OMP configured-model synchronization has one explicit state record with `desired_selector`, `pending_selector`, `confirmed_selector`, `status`, and `error`. UI selection, `/model`, subagent defaults, refreshes, and prompt submission must update this state instead of maintaining separate ad hoc pending/confirmed flags.
- Configured OMP model switches must wait for `set_model` confirmation when the RPC process is already running or immediately before prompt submission. A rejected, timed-out, unknown, or wrong-model confirmation is a switch failure and must block the prompt instead of silently running on the previous model.
- OMP process restart or replacement invalidates process-local model confidence: the wrapper must force a fresh `set_model` before the first prompt on the new process, even if `confirmed_selector` matched the desired selector in the previous process.
- Legacy `next_llm()` calls on configured OMP models must use the same confirmed switch path as `/model`; they must not fire-and-forget a `set_model` request and then clear pending state before confirmation.
- Current-model UI lines and model orchestration registry must read the active effective model owner: active subagent runtime first, otherwise the main agent. They must not display the main agent model as the current model while the visible interaction target is a subagent.
- New Shuheng main or temporary session -> active OMP RPC session receives a `new_session` reset when the process is running, and a later first runtime task may inject one fresh full context pack.
- User system OMP config exists -> policy checks must verify its hash remains unchanged across embedded OMP runtime setup.
- OMP adapter registration -> subprocess `cwd` is the Shuheng app root so relative repo paths such as `AGENTS.md` resolve to this project while isolated runtime files still live under the Shuheng-owned harness directory.
- OMP error frame with `stopReason:"error"` and `errorMessage` -> active TUI queue receives a visible `[Oh My Pi] ...` done item.
- OMP terminal runtime errors delivered through subagent task/chat streams, including `429`, `RPC prompt failed`, and `Agent is already processing`, must release the subagent active task state; subagent tasks record `failed` in task ledgers/mail/checkpoints/traces, keep an audit artifact, and must not create eval rows, memory candidates, orchestrator result injections, or plan continuations.
- OMP `message_end` / assistant-message error frames are not final turn ownership by themselves. The wrapper must keep the active prompt busy until `agent_end` / `turn_end` or a bounded terminal grace expires, so OMP internal retries after a 429 cannot receive the next prompt and produce `Agent is already processing`.
- Subagent default models must be applied immediately before every subagent task or direct-chat prompt. If the configured model cannot be applied to the live runtime, startup is blocked before the prompt is sent so the subagent never silently runs on the previous model.
- OMP `turn_end` followed by an immediate next `put_task()` before `agent_end` -> wrapper rejects the next prompt as concurrent instead of sending it to OMP and surfacing `Agent is already processing`.
- OMP `turn_end` followed by `agent_end` -> active queue receives the done item and the next prompt can then be sent normally.
- OMP `agent_end` with a visible assistant reply ending mid-sentence, such as `手机内置马达的振动强度**根本不够**用于实际` -> wrapper sends a same-session internal continuation prompt and does not complete the queue until the continuation produces a complete visible reply.
- Repeated incomplete terminal replies beyond the continuation cap -> wrapper emits a terminal queue item with an explicit incomplete notice and runtime event status `incomplete`, not a silent `completed` status.
- OMP incomplete terminal notices delivered through subagent task/chat streams -> subagent runtime error detection records the work as failed, releases the active task/chat state, and must not write a completed task ledger row.
- OMP text deltas split punctuation as `"1"`, `"."`, `" item"` or `"0"`, `"."`, `"6"` -> the final queue text preserves `1.` and `0.6`; if `agent_end.messages` also carries the complete final assistant message, the answer appears once.
- OMP `message_end` and `agent_end.messages` carry the same assistant message usage -> token usage is counted once.
- OMP host tool result followed by no post-tool `agent_end` or visible assistant text -> host-tool follow-up watchdog emits a bounded `[Oh My Pi]` fallback `done` item, clears `is_running`, decrements unfinished task count, and does not emit a memory candidate, even if pre-tool progress text already exists in the active buffer.
- OMP RPC frames omit non-zero usage but the isolated session JSONL contains assistant-message usage created after the active prompt baseline -> token usage is recovered from the session file and counted once.
- OMP `agent_end` arrives before the isolated session JSONL flushes usage -> the provider waits for the short stable-flush window, attaches the recovered usage, and only then emits the terminal queue item.
- OMP terminal queue item carries usage -> the TUI main thread writes the active session row in `session_token_usage.json`, and the left status panel reads that row through `session_token_stats()`.
- OMP terminal queue item carries usage for a devnull temporary session -> no token usage registry row is written.
- Two consecutive OMP main turns in one Shuheng runtime session -> first prompt contains `[Shuheng Context Pack]`; second prompt contains `[Shuheng Context Ref]` and does not repeat the full pack.
- OMP thinking delta + tool execution frames + final text delta -> active TUI queue receives GA-style process markers plus the final reply; `render_assistant_text(..., fold_process:true)` folds thinking/tool noise and keeps the final reply visible.
- OMP host tool calls/results -> active TUI queue receives folded GA-style tool process turns while RPC still receives matching `host_tool_result` frames.
- OMP memory-candidate signal extraction over normalized process output -> candidate statement contains only the final durable reply, not thinking text, tool args, or tool results.
- OMP follow-up `这个是啥啊？` after a visible BSpace Agent Arcade URL/task -> answer about the Agent Arcade/game/API task, not about the Shuheng Context Pack/Ref.
- OMP memory candidate declaring `target_role:"ops"` or `scope:"ops.*"` while targeting a generic `researcher` -> rejected with `target_mismatch_candidate_responsibility` and no subagent memory append occurs, even if a stale approval row is later approved.
- `put_runtime_task(RuntimeTaskRequest)` -> provider emits at least `runtime_task_requested` and a terminal `runtime_task_completed`, `runtime_task_failed`, or `runtime_task_aborted` event carrying the original request and context-pack artifact refs.

### 5. Good/Base/Bad Cases

- Good: unset `SHUHENG_RUNTIME_PROVIDER` selects `OhMyPiRuntimeAdapter`, starts `omp --mode rpc` lazily with the generated memory append prompt, streams text deltas into the existing TUI message renderer, and keeps GenericAgent available as an explicit fallback.
- Good: `/model` entries are projected into `${AGENT_HARNESS_DIR}/runtime/ohmypi/agent/models.yml`, OMP is launched with `PI_CODING_AGENT_DIR` pointing at that directory, and system `~/.omp/agent/config.yml` is untouched.
- Good: generated `models.yml` stores `apiKey: SHUHENG_OMP_API_KEY_<digest>` while the secret value is supplied only in the child process env.
- Good: After adding a provider in `/model`, the running Shuheng wrapper's model list immediately includes it and a later selection uses the refreshed OMP provider id instead of a stale pending model.
- Good: Missing `omp` produces an assistant-visible error message instead of crashing startup.
- Base: `/runtimes` shows `ohmypi` as default and shows `genericagent` only when the optional legacy provider is available.
- Base: Oh My Pi can query bounded TUI governance facts through `shuheng_query` without mutating task ledgers, approvals, artifacts, or long-term memory.
- Base: Oh My Pi can use typed tools such as `agent_list`, `schedule_list`, and `memory_context_get`; compatibility aliases remain available during migration.
- Base: Oh My Pi can propose current-schema actions through `shuheng_propose`, while Shuheng remains the Orchestrator and policy/ledger owner.
- Base: Oh My Pi can submit a durable memory candidate through `shuheng_propose` or `memory_candidate_submit`, while the TUI Memory Curator creates artifacts and a human approval request before any long-term memory write.
- Base: A durable completed Oh My Pi output records a memory candidate signal for later approval instead of writing long-term memory directly.
- Base: Oh My Pi task request/completion/host-tool events are normalized into trace rows when they have a Shuheng task id.
- Bad: The provider imports `app.py` to read TUI state or mutate ledgers directly.
- Bad: Embedded OMP inherits `~/.omp/agent` or uses the user's system OMP `modelRoles.default`, because `/model` would no longer be the single Shuheng settings surface.
- Bad: Generated OMP `models.yml` writes raw API key values.
- Bad: Saving `mykey.py` but leaving the active `OhMyPiRpcAgent.llmclients` list unchanged until a full TUI restart, because `/model` then appears to do nothing.
- Bad: Letting an RPC `get_available_models` response from an already-running process replace the Shuheng-projected `/model` list after a save.
- Bad: The adapter enables arbitrary OMP host tools, host URI schemes, writable operations, or auto-approval before TUI policy gates can audit and approve those operations.
- Bad: `app.py` contains Oh My Pi RPC parsing logic instead of provider-local parsing.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `ohmypi` appears in the runtime registry and is the default provider.
- Tests must assert `SHUHENG_RUNTIME_PROVIDER=genericagent` selects the GenericAgent legacy adapter when it is configured, and falls back to healthy OMP core behavior when GenericAgent is unavailable.
- Tests must assert disabling GenericAgent discovery still allows `shuheng.app` import, `shuheng-check`, and an OMP-only runtime registry.
- Tests must assert `ohmypi_provider.py` has no reverse import into `app.py` and no curses import.
- Tests must assert the generated memory append prompt is bounded, redacted, and passed to `omp` through `--append-system-prompt`.
- Tests must assert generated OMP context packs/context refs, memory append prompts, and memory-candidate tool descriptions contain the final-reply rule so memory-candidate status cannot become the only visible completion.
- Tests must assert generated OMP context packs/context refs and memory append prompts contain the deictic-reference rule that prevents `这个`/`this` from resolving to internal context metadata by default.
- Tests must assert generated OMP context packs/context refs and memory append prompts contain the persistent-agent request rule, and that memory candidates with declared target role/scope/responsibility mismatches are rejected both at queue time and approval time.
- Tests must assert OMP command construction discovers `$HOME/.bun/bin/omp` when `omp` is absent from `PATH`, while explicit `SHUHENG_OHMYPI_BIN` remains authoritative.
- Tests must assert completed Oh My Pi output can produce a governed memory candidate signal and that empty, too-short, secret-looking, and Secret-context outputs are skipped.
- Tests must assert a fake RPC process maps `ready`, `prompt` ack, `message_update` deltas, and `agent_end` into queue `next`/`done` items.
- Tests must assert standalone dot deltas preserve real punctuation in normal streamed final text, still hide tool-turn placeholder dots, and do not cause terminal final-message fallback duplication.
- Tests must assert OMP `usage` payloads are normalized, de-duplicated across repeated terminal frames, recovered from isolated OMP session JSONL when RPC frames omit non-zero usage, diffed against the active prompt baseline rather than a provider-lifetime seen set, attached to queue `done` items after the stable-flush wait, included in runtime completion event payloads, persisted into `session_token_usage.json`, and skipped for devnull temporary sessions.
- Tests must assert `turn_end` does not release the active prompt before `agent_end`, preventing immediate next-prompt races against real OMP finalization.
- Tests must assert structurally incomplete OMP terminal replies trigger bounded same-session continuation and do not emit `done` until the continuation completes.
- Tests must assert repeated incomplete terminal replies stop at the continuation cap and surface explicit incomplete status instead of silent success.
- Tests must assert OMP incomplete terminal notices in subagent streams fail subagent task ledgers instead of being recorded as completed output.
- Tests must assert `turn_end` carrying `stopReason:"toolUse"` or tool results waits for the final assistant answer instead of completing from the tool-result turn.
- Tests must assert a stalled Shuheng host-tool follow-up exits running state through the host-tool watchdog fallback without creating an Oh My Pi memory candidate, including mixed outputs where pre-tool progress text precedes the provider fallback.
- Tests must assert a fake RPC process maps OMP thinking/tool events into Shuheng foldable process blocks, that the existing assistant renderer folds them, and that final replies remain visible.
- Tests must assert `put_runtime_task(RuntimeTaskRequest)` emits `runtime.task_event.v1` rows that preserve `runtime.task_request.v1`, `prompt_preview`, `prompt_chars`, `context_pack_ref`, and artifact refs without storing the raw prompt.
- Tests must assert a fake RPC process with no `text_delta` still produces non-empty `done` text when final assistant text is carried by `message_end.message.content` or terminal-frame `message.content`.
- Tests must assert a fake RPC process receives app-injected `set_host_tools` definitions before the prompt frame.
- Tests must assert fake `host_tool_call` frames receive `host_tool_result` success frames.
- Tests must assert unknown or failing host tool calls receive `host_tool_result` with `isError:true`.
- Tests must assert `host_tool_cancel` frames are handled safely.
- Tests must assert `shuheng_query` remains read-only and `shuheng_propose` supports governed `shuheng_control` and `memory_candidate` proposals.
- Tests must assert typed OMP tools include read-only state queries, `memory_context_get`, `memory_candidate_submit`, and `schedule_create`.
- Tests must assert `memory_context_get` writes a Shuheng context-pack artifact under the harness and returns its artifact ref.
- Tests must assert `shuheng_propose` memory candidates create existing memory approval artifacts/approval rows and invalid proposals return structured errors.
- Tests must assert provider metadata advertises `tui_readonly_host_tools:true`, `tui_governed_proposal_tools:true`, `tui_typed_host_tools:true`, `runtime_task_requests:true`, and `runtime_task_events:true` while keeping unrestricted `host_tools:false`.
- Tests must assert isolated OMP runtime files are generated under `${AGENT_HARNESS_DIR}/runtime/ohmypi/agent`, not under `~/.omp/agent`.
- Tests must assert the OMP runtime adapter subprocess `cwd` is the Shuheng app root, not a legacy-provider checkout.
- Tests must assert generated OMP API keys are env references in `models.yml`, raw key values are absent from generated files, and child-process env carries `PI_CODING_AGENT_DIR`.
- Tests must assert PAAS v4 OpenAI-compatible bases such as `https://open.bigmodel.cn/api/coding/paas/v4` do not inherit Anthropic `/v1/messages` routing from a historical `native_claude_config_*` variable name.
- Tests must assert generated OMP model rows preserve `contextWindow` / `maxTokens` from `/model`, embedded OMP `config.yml` disables `autoResume`, and repeated runtime turns use a context ref instead of repeating the full context pack.
- Tests must assert embedded OMP `config.yml` writes `todo.eager:"default"` so thinking-mode providers are not sent forced `tool_choice:"todo"` by default.
- Tests must assert `refresh_agent_runtime_model_config()` updates an existing OMP wrapper after `mykey.py` changes, `OhMyPiRpcAgent` initializes to the projected default model selector, stale `get_state` model payloads and normal `set_model` confirmations cannot corrupt the current configured model display, and `OhMyPiRpcAgent.refresh_configured_models()` preserves a selected model while updating env, command, and pending `set_model` provider id.
- Tests must assert a wrong-model OMP `set_model` confirmation fails the switch and keeps the previous local selection.
- Tests must assert `/model` default selection maps to isolated OMP `modelRoles.default` and RPC `set_model` can be sent before the first prompt when a TUI model is selected.
- Tests must assert a new OMP wrapper sends the selected default model through `set_model` before its first prompt, even if the UI already points at that model locally.
- Tests must assert an OMP process restart sends the desired configured model through `set_model` again before the first prompt on the replacement process.
- Tests must assert legacy `next_llm()` does not falsely mark configured OMP model switches complete after a wrong-model `set_model` confirmation.
- Tests must assert current-model UI lines prefer the active subagent runtime model over the main agent model while the selected view is a subagent.
- Tests must assert OMP error `message_end` frames keep the active prompt busy until a terminal frame or grace timeout, and that a second prompt during that window is blocked locally rather than sent to OMP.
- Tests must assert `/model` `Enter` from an active subagent view sets that subagent's default model instead of switching the main agent.
- Tests must assert OMP terminal error frames surface `errorMessage` / `errorStatus` visibly instead of an empty done item.
- Tests must assert OMP terminal errors on subagent task/chat streams fail and release the subagent without generating eval/memory/orchestrator-continuation side effects, and that subagent default-model application failure blocks startup before sending a prompt.
- Tests must assert system `~/.omp/agent/config.yml` hash remains unchanged when present.
- Tests must assert missing binary failure and `abort()` cleanup decrement unfinished task state.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/ohmypi_provider.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```python
# ohmypi_provider.py
self.llm_no = index
self.llmclient = self.llmclients[index]
self._pending_model = None  # UI looks switched, but OMP never confirmed it.
```

#### Correct

```python
# ohmypi_provider.py
self._set_desired_model(self.configured_models[index], force=True)
ok, message = self._apply_pending_model(wait=True)
if not ok:
    restore_previous_selection()
```

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
    from shuheng.app import queue_curated_memory_candidate
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
- `schedule_create` response uses `schema_version:"shuheng.tool.v1"` and returns the appended `scheduledtask.v1` row plus the current schedule registry snapshot.
- `schedule_list` response uses `schema_version:"shuheng.tool.v1"` and returns the TUI `scheduledtask.registry.v1` snapshot.

### 3. Contracts

- `schedule_create` is a governed state-changing TUI tool, not a read-only query tool.
- `schedule_create` must call the same schedule registration path used by `shuheng-control.v2` `schedule.create`.
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

- Trigger: The main agent emits real `shuheng-control.v2` controls for an intermediate workflow step and explicitly requests continuation with structured metadata such as `continue_after:true` or `workflow_state:"in_progress"`, but does not create an executable task ledger and does not emit the next delegation/configuration controls.
- Applies to: normal non-Secret main-agent turns after `apply_tui_controls_from_text()` has executed controls.
- Non-goal: This must not manually execute the business workflow in the TUI. It only feeds control results back to the main agent so the orchestrator can continue emitting governed controls.

### 2. Signatures

- Auto continuation source: `shuheng:auto_control_continue`.
- Continuation prompt block: `[Shuheng Control Result Continuation] ... [/Shuheng Control Result Continuation]`.
- State counters: per-signature `auto_control_continue_attempts`, session cap `auto_control_continue_count`.
- Structured continuation fields: `continue_after`, `next_action_required`, `requires_continuation`, `workflow_state`, `orchestrator_state`, and `next_action`.
- Pure helper ownership: `control_protocol.py` owns continuation action/state constants, result signatures, metadata discovery, explicit-continuation predicates, continuation-needed predicates, and prompt text formatting over explicit inputs.
- Result-line formatter ownership: `control_protocol.py` owns `format_agent_control_result(action, target, result)` so the visible `Agent 控制结果` line shape is shared by the app compatibility facade and protocol tests.

### 3. Contracts

- `apply_tui_controls_from_text()` returns formatted control result lines while still adding the visible `Agent 控制结果` system message.
- The continuation only runs when the executed control envelope or action explicitly carries continuation metadata such as `continue_after:true`, `next_action_required:true`, `requires_continuation:true`, `workflow_state:"in_progress"`, or a non-empty `next_action`.
- Visible prose must never trigger continuation by itself.
- Controls that already delegated child work, such as `delegate.create`, must not trigger this fallback because the next event should be the subagent result.
- If an executable task plan exists, `maybe_queue_orchestrator_plan_continuation()` remains the primary mechanism and this fallback does not run.
- New user-started main tasks reset the control-continuation counters.
- `app.py` remains the Orchestrator owner for `maybe_queue_orchestrator_control_continuation(...)`, state gating, per-signature/session counters, blocked-system messages, and `start_main_agent_task(...)` side effects.

### 4. Validation & Error Matrix

- No real controls -> no continuation.
- Active plan exists -> use plan continuation instead.
- Active subagent work, pending interaction, or non-idle main state -> no continuation.
- Same control result signature repeats -> stop after one retry and add an `orchestrator_auto_continue_blocked` system message.
- Session reaches the continuation cap -> stop and add an `orchestrator_auto_continue_blocked` system message.

### 5. Good/Base/Bad Cases

- Good: The assistant emits `agent.create` with `continue_after:true`; TUI creates the agent, then starts `shuheng:auto_control_continue` with the control result so the assistant can continue with ledger/delegation/configuration.
- Base: The assistant creates an agent as a complete one-step user request without structured continuation metadata; no auto continuation fires.
- Base: The assistant creates an agent and writes "Step 1" in visible prose but omits structured continuation metadata; no auto continuation fires.
- Bad: The assistant emits `delegate.create` and TUI immediately starts another main turn before the subagent result arrives.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert structured continuation metadata plus `agent.create` starts a second main-agent prompt with source `shuheng:auto_control_continue`.
- The continuation prompt must include the control result, the created agent name, and instruction to continue the approved workflow without repeating controls.
- Existing auto-plan continuation tests must continue to pass and remain primary when a task ledger exists.

### 7. Wrong vs Correct

#### Wrong

```text
Visible text says "Step 1.1 create agent" but the control has no continuation metadata -> Agent 控制结果 shows success -> main agent stops because the control did not request continuation.
```

#### Correct

```text
agent.create includes continue_after:true -> Agent 控制结果 shows success -> shuheng:auto_control_continue feeds the result back to the orchestrator -> orchestrator emits the next governed controls.
```

## Scenario: Scheduled Task Scheduler

### 1. Scope / Trigger

- Trigger: TUI schedule records must execute recurring or one-shot work without bypassing the governed subagent/task protocol.
- Applies to: `schedule.create`, `schedule.update`, `schedule.enable`, `schedule.disable`, `schedule.delete`, `/schedules`, `/scheduler`, MCP schedule resources, runtime provider registry metadata, and scheduler tick tests.
- Non-goal: A schedule must not directly call `agent.put_task()` or choose a worker from natural-language similarity.

### 2. Signatures

- Schedule registry path: `AGENT_SCHEDULES_PATH`, JSONL rows with `schema_version:"scheduledtask.v1"`.
- Schedule run audit path: `AGENT_SCHEDULE_RUNS_PATH`, JSONL rows with `schema_version:"scheduledtask.run.v1"`.
- Implementation module: `src/shuheng/scheduler.py` owns schedule registry helpers, trigger parsing, due calculation, run audit shaping, tick aggregation, and scheduler text formatting.
- Composition module: `src/shuheng/app.py` may re-export scheduler helpers for compatibility, but it supplies mutable TUI dependencies through `configure_scheduler_runtime()` instead of being imported by `scheduler.py`.
- TUI commands:
  - `/schedules` shows registry, due state, run count, and last-run state.
  - `/scheduler status` shows scheduler state.
  - `/scheduler tick` evaluates due jobs and records manual skip/invalid outcomes.
  - `/scheduler run <schedule_id>` force-runs one enabled schedule.
- Supported trigger fields: `at`, `interval`, `cron`, and standardized `trigger` strings prefixed as `at:...`, `interval:...`, or `cron:...`.
- Users express scheduling intent in natural language. The main model translates that intent into the current `ScheduleCreate` trigger schema before emitting `shuheng-control.v2`. Schema-outside fields are handled by the generic boundary; active runtime, prompts, docs, user-facing errors, and normal tests should not enumerate retired field names.
- Daemon tick interval env: `SHUHENG_SCHEDULER_TICK_SECONDS`, minimum 5 seconds, default 30 seconds.
- MCP resources include `resource://agent-mail/schedules` and `resource://agent-mail/schedule-runs`.

### 3. Contracts

- Agent-work schedule dispatch must build an explicit `agenttask.v2` `delegate.create` envelope and reuse the existing delegation path.
- TUI-local reminder dispatch must execute only explicit `execution.mode:"tui_action"` rows and write schedule-run audit rows; it must not infer actions from schedule names or natural-language objectives.
- A dispatchable agent-task schedule must include `execution.work_order.objective` and an explicit structured routing target.
- A TUI-action reminder schedule must include `execution.action`; it does not require `work_order.objective` or an agent target.
- Due jobs reserve an `idempotency_key` by appending a `starting` run row before dispatching.
- Final run rows reuse the same `run_id` and append status such as `dispatched`, `queued`, `approval_required`, `failed`, `rejected`, `duplicate`, `skipped`, or `invalid`.
- Agent-task final run status must come from a structured dispatch result (`status`, `message`, `task_id`, `approval_id`, `error`, `provider_id`) rather than parsing localized UI text returned to ordinary callers.
- The scheduler does not write report pages directly. Scheduled-report UI derives subagent replies from the final run row `task_id`, the latest task ledger row, and subagent-result artifact refs.
- Schedule run rows must record `provider_id`. If a schedule does not explicitly carry a provider id, scheduler dispatch resolves it through the injected runtime default, which is `ohmypi`.
- Agent-task final run rows should also record `runtime_provider_id` from the structured dispatch result or the resolved schedule provider.
- After each run row, the latest schedule record is updated append-only with `last_run_id`, `last_run_status`, `last_run_at`, and `last_idempotency_key`.
- Due calculation for interval schedules must use the latest real dispatch attempt (`starting`, `dispatched`, `queued`, `approval_required`, `failed`, or `rejected`) as its anchor. Observation-only rows such as `duplicate`, `skipped`, and `invalid` may be displayed as the latest run, but must not move the next interval due time.
- Disabled, deleted, cancelled, and canceled schedules are not dispatched.
- Schedule execution must enter `start_subagent_task()` so policy gates, single-writer locks, task ledger, agent mail, checkpoints, traces, and artifacts remain active.
- `src/shuheng/scheduler.py` must not import curses, GenericAgent runtime classes, `StepOutcome`, mutable TUI `State`, or `shuheng.app`.
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
- Schedule without explicit `provider_id` -> due run rows record `provider_id:"ohmypi"` and final agent-task rows record `runtime_provider_id:"ohmypi"`.

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
- Tests must assert `app.py` re-exports key scheduler helpers from `shuheng.scheduler` and that `src/shuheng/scheduler.py` does not import curses, GenericAgent runtime classes, `StepOutcome`, mutable TUI `State`, or `shuheng.app`.
- Tests that retarget harness paths must reconfigure scheduler runtime paths in the same step, otherwise scheduler JSONL helpers can silently write to the previous harness directory.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/runtime.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```text
At 08:00, scheduler calls agent.put_task("Generate daily digest") directly and stores only the visible result.
```

#### Correct

```text
At 08:00, scheduler writes scheduledtask.run.v1 starting, converts the schedule to agenttask.v2 delegate.create, calls start_subagent_task(), then appends the final run status and relies on task ledger/artifact refs for execution evidence.
```

## Scenario: Scheduled Workflow Run Trigger V1

### 1. Scope / Trigger

- Trigger: A `scheduledtask.v1` row should start an existing workflow run on a timer without adding a second workflow executor.
- Applies to: `execution.mode:"workflow_run"`, `dispatch_contract:"workflow_run.v1"`, `src/shuheng/scheduler.py`, `src/shuheng/app.py`, `/scheduler run <schedule_id>`, scheduler ticks, `schedule_runs.jsonl`, `workflow_runs.jsonl`, `tests/test_scheduler_parsing.py`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: This does not add parallel/fan-out/fan-in execution, workflow daemon ownership, workflow-specific backoff, workflow timeouts, graph editing, approval auto-resume, plugin code execution, direct tool/model calls, or A2A/MCP workflow service exposure.

### 2. Signatures

- Schedule execution shape:
  - `{"mode":"workflow_run","workflow_ref":"<plugin-id>/<workflow-id>","inputs":{...}}`
- Workflow refs may use the same manifest-backed refs and shorthands accepted by `/workflow run`.
- Schedule record dispatch contract: `workflow_run.v1`.
- Scheduler callback injection:
  - `SchedulerRuntime.dispatch_workflow_run(state, schedule_row, source, schedule_id, execution) -> SchedulerDispatchResult`
- App-owned callback:
  - `_scheduler_dispatch_workflow_run(...)` loads through `workflow_load_result_for_ref(workflow_ref, user_plugin_registry(force=True))`.
  - The callback starts the run only through `create_workflow_run_v0(result, state=state, inputs=inputs, source_command=f"/scheduler run {schedule_id}")`.
- Schedule final run rows may include:
  - `workflow_run_id`
  - `workflow_ref`
  - `result`
  - `error`
  - existing trigger, idempotency, provider, source, and dispatch contract metadata.

### 3. Contracts

- `scheduler.py` owns parsing, validation, due/idempotency handling, and schedule-run audit rows only.
- `scheduler.py` must not import `app.py`, `workflows.py`, plugin helpers, curses, mutable TUI `State`, runtime provider classes, approval queues, task/progress/artifact ledgers, or governance owners.
- `scheduler.py` must not resolve workflow refs, append workflow run rows, dispatch subagents, queue approvals, evaluate workflow steps, or duplicate workflow runner behavior.
- `app.py` remains the strong Orchestrator owner for plugin registry refresh, workflow ref resolution, workflow run creation, approval bridging, agent-task bridging, retries, artifact refs, and workflow ledger writes.
- A workflow-run schedule must be rejected at create/update validation when `execution.workflow_ref` is missing or blank.
- `execution.inputs` is JSON-safe schedule data passed to the workflow runner unchanged; scheduler validation must not interpret workflow input schemas.
- A due workflow-run schedule appends the normal `scheduledtask.run.v1` `starting` row before app callback dispatch and one final schedule-run row after the callback returns.
- A successful app callback appends normal `shuheng.workflow_run.v1` rows through `create_workflow_run_v0(...)`, then the final schedule-run row links `workflow_run_id` and canonical `workflow_ref`.
- A missing or invalid workflow produces a failed final schedule-run row and no workflow run rows.
- Existing `execution.mode:"tui_action"` and `execution.mode:"agent_task"` behavior remains compatible.

### 4. Validation & Error Matrix

- Valid workflow-run schedule with `workflow_ref` and inputs -> schedule record `dispatch_contract:"workflow_run.v1"` and empty `target`.
- Workflow-run schedule missing `workflow_ref` -> visible create/update validation error, no schedule record append.
- Forced `/scheduler run <id>` for a safe workflow schedule -> `starting` and final `dispatched` schedule-run rows, plus planned and advanced workflow-run rows.
- Workflow ref not found -> `starting` and final `failed` schedule-run rows, no workflow-run rows.
- Workflow definition invalid -> final `failed` schedule-run row with the workflow rejection message, no workflow-run rows.
- Scheduler runtime callback missing -> final `failed` schedule-run row, no workflow-run rows.
- Workflow that reaches approval or agent-task bridge -> final schedule-run row links the workflow run id; approval/task side effects remain owned by the existing app workflow bridge.

### 5. Good/Base/Bad Cases

- Good: `interval:"1h"` plus `execution.mode:"workflow_run"` starts `plugin://schedule-pack/workflows/daily-flow` through `create_workflow_run_v0(...)` and records the workflow run id in `schedule_runs.jsonl`.
- Good: A scheduled workflow that reaches `agent_task` dispatches only through the existing Workflow Agent Task Bridge and stores task ids in the workflow row, not in scheduler-owned synthetic task rows.
- Base: `schedule_list`, `/schedules`, and gateway registry may still show `agenttask.v2` as the historical default dispatch contract while individual workflow schedule rows use `workflow_run.v1`.
- Bad: `scheduler.py` imports `workflows.py` and calls `advance_workflow_run_v0(...)` directly.
- Bad: Scheduler appends `workflow_runs.jsonl` itself or starts subagents directly for workflow steps.
- Bad: A failed workflow ref silently falls back to an `agent_task` schedule.

### 6. Tests Required

- `tests/test_scheduler_parsing.py` must assert workflow-run execution parsing, required `workflow_ref`, JSON-safe inputs, create/update `dispatch_contract:"workflow_run.v1"`, and empty scheduler target.
- `tests/test_workflows.py` must assert a forced scheduler run for a valid workflow schedule appends schedule-run rows and normal workflow-run rows through the app runner.
- `tests/test_workflows.py` must assert a missing workflow schedule appends a failed schedule-run final row and no workflow-run rows.
- `scripts/check_policy_gates.py` must assert `workflow_run` is exposed in schedule control/tool schemas, scheduler runtime retargeting injects `dispatch_workflow_run`, scheduler module ownership remains pure, and safe scheduled workflow runs do not write task/progress/approval/artifact ledgers.
- Keep targeted compile/Ruff, `tests/test_scheduler_parsing.py`, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
schedule workflow_run -> scheduler.py loads plugin workflow, advances steps, writes workflow_runs.jsonl, and dispatches subagents
```

#### Correct

```text
schedule workflow_run -> scheduler.py writes scheduledtask.run.v1 starting -> injected app callback -> create_workflow_run_v0(...) -> final schedule-run row links workflow_run_id
```

## Scenario: Scheduled Workflow Autopilot Trigger V1

### 1. Scope / Trigger

- Trigger: A `scheduledtask.v1` row should periodically run the existing workflow autopilot tick so ready workflow runs can advance without adding a workflow daemon or weakening Orchestrator ownership.
- Applies to: `execution.mode:"workflow_autopilot"`, `dispatch_contract:"workflow_autopilot.v1"`, `src/shuheng/scheduler.py`, `src/shuheng/app.py`, `/scheduler run <schedule_id>`, scheduler ticks, `schedule_runs.jsonl`, `workflow_runs.jsonl`, `workflow_events.jsonl`, `tests/test_scheduler_parsing.py`, `tests/test_workflows.py`, and `scripts/check_policy_gates.py`.
- Non-goal: This does not add a new daemon, background thread, timer owner, workflow-specific executor, approval auto-resume, approval auto-decision, duplicate subagent dispatch, workflow retry engine, direct model/tool/plugin-code execution, or A2A/MCP workflow service exposure.

### 2. Signatures

- Schedule execution shape:
  - `{"mode":"workflow_autopilot","run_ids":["<run-id>", "..."],"limit":25,"dry_run":false}`
- `run_ids` is optional. When omitted or empty, the app helper considers latest workflow run ids up to `limit`.
- `limit` defaults to `25` and must be greater than zero.
- `dry_run` defaults to `false`. When `true`, the schedule appends only schedule-run audit rows.
- Schedule record dispatch contract: `workflow_autopilot.v1`.
- Scheduler callback injection:
  - `SchedulerRuntime.dispatch_workflow_autopilot(state, schedule_row, source, schedule_id, execution) -> SchedulerDispatchResult`
- App-owned callback:
  - `_scheduler_dispatch_workflow_autopilot(...)` calls `run_workflow_autopilot_tick(state, dry_run=..., run_ids=..., limit=..., source_command=f"/scheduler run {schedule_id}")`.
- Schedule final run rows must include:
  - `workflow_run_ids`
  - `selected_count`
  - `considered_count`
  - `continued_count`
  - `skipped_count`
  - `workflow_event_count`
  - `result`
  - `runtime_provider_id`
  - existing trigger, idempotency, provider, source, and dispatch contract metadata.

### 3. Contracts

- `scheduler.py` owns parsing, validation, due/idempotency handling, and schedule-run audit rows only.
- `scheduler.py` must not import `app.py`, `workflows.py`, plugin helpers, curses, mutable TUI `State`, runtime provider classes, approval queues, task/progress/artifact ledgers, workflow ledgers, or governance owners.
- `scheduler.py` must not resolve workflow refs, append workflow run/event rows, inspect workflow/task/approval rows, dispatch subagents, queue approvals, apply approval decisions, evaluate workflow steps, or duplicate workflow runner behavior.
- `app.py` remains the strong Orchestrator owner for reading workflow/task/approval ledgers, appending workflow run/event rows, approval bridging, agent-task bridging, retries, artifact refs, and the call to `continue_workflow_run_v0(...)`.
- `workflows.py` remains pure. It may project and format autopilot tick plans from row lists, but must not read files, import app/runtime/UI/governance owners, append JSONL rows, queue approvals, dispatch subagents, or call tools/providers.
- Scheduled autopilot must use the same app helper as `/workflow tick` and `/workflow autopilot`; it must not implement a parallel selection or continuation path.
- Only runs selected by `workflow_autopilot_tick_plan(...)` with `next_action:"continue"` may call `continue_workflow_run_v0(...)`.
- Pending approvals must remain pending until `/approve` or `/reject` changes the approval row. Scheduled autopilot must not self-approve or reject.
- Non-terminal subagent tasks must remain waiting. Scheduled autopilot must not dispatch duplicate tasks while an existing task row is non-terminal.
- Existing `execution.mode:"workflow_run"`, `tui_action`, and `agent_task` behavior remains compatible.

### 4. Validation & Error Matrix

- Valid workflow-autopilot schedule -> schedule record `dispatch_contract:"workflow_autopilot.v1"` and empty `target`.
- Hyphenated mode `workflow-autopilot` -> normalized to `workflow_autopilot`.
- `run_ids` as a list or string -> normalized to a JSON-safe list of non-empty unique strings.
- Missing `limit` -> default `25`.
- `limit <= 0` -> visible create/update validation error and no schedule record append.
- Invalid non-integer `limit` -> visible create/update validation error and no schedule record append.
- Forced `/scheduler run <id>` for dry-run autopilot -> starting and final schedule-run rows only; no workflow run, workflow event, task, progress, approval, or artifact rows are appended.
- Forced `/scheduler run <id>` for mutating autopilot -> starting and final schedule-run rows plus app-owned workflow event rows and any workflow run rows produced by `continue_workflow_run_v0(...)`.
- Ready planned run -> selected and continued through app helper.
- Waiting approval with pending approval row -> skipped; approval row remains pending.
- Waiting task with non-terminal task row -> skipped; no duplicate task dispatch.
- Completed or terminal run -> skipped without calling continue.
- Scheduler runtime callback missing -> final failed schedule-run row; no workflow ledger rows are appended.

### 5. Good/Base/Bad Cases

- Good: `interval:"5m"` plus `execution.mode:"workflow_autopilot"` dry-run reports one ready run and one pending approval run while appending no workflow/event/task/progress/approval/artifact rows.
- Good: Mutating scheduled autopilot continues only a planned run and records selected/continued/skipped/event counts in `schedule_runs.jsonl`.
- Good: A pending approval remains pending and still requires `/approve <approval_id>` or `/reject <approval_id>`.
- Base: Scheduled autopilot is a scheduler trigger for the existing app-owned tick helper, not a new always-on workflow worker.
- Bad: `scheduler.py` imports `workflows.py`, scans `workflow_runs.jsonl`, and calls `advance_workflow_run_v0(...)`.
- Bad: Scheduler appends workflow event rows directly or decides that a pending approval is safe to approve.
- Bad: Scheduled autopilot dispatches another subagent task while the latest task row is still working.

### 6. Tests Required

- `tests/test_scheduler_parsing.py` must assert workflow-autopilot execution parsing, hyphen normalization, JSON-safe `run_ids`, `limit` and `dry_run` preservation, invalid `limit <= 0`, create/update `dispatch_contract:"workflow_autopilot.v1"`, and empty scheduler target.
- `tests/test_workflows.py` must assert a forced scheduler dry-run appends only schedule-run rows and no workflow run/event/task/progress/approval/artifact rows.
- `tests/test_workflows.py` must assert a forced mutating scheduler run continues only ready runs, skips pending approval/task runs, and writes selected/continued/skipped/event counts in the final schedule-run row.
- `scripts/check_policy_gates.py` must assert scheduler module ownership remains pure, scheduler exposes `workflow_autopilot.v1`, scheduler runtime retargeting injects `dispatch_workflow_autopilot`, app owns `_scheduler_dispatch_workflow_autopilot`, dry-run is no-mutation outside schedule-run rows, and mutating scheduled autopilot does not bypass approvals or duplicate tasks.
- Keep targeted compile/Ruff, `tests/test_scheduler_parsing.py`, `tests/test_workflows.py`, `python3 scripts/check_policy_gates.py`, full pytest, build/wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```text
schedule workflow_autopilot -> scheduler.py reads workflow_runs.jsonl -> scheduler.py advances ready rows and auto-approves gates
```

#### Correct

```text
schedule workflow_autopilot -> scheduler.py writes scheduledtask.run.v1 starting -> injected app callback -> run_workflow_autopilot_tick(...) -> continue_workflow_run_v0(...) only for selected ready runs -> final schedule-run row records counts
```

## Scenario: Shuheng-Owned Storage And Archive-Backed Sidebar Rows

### 1. Scope / Trigger

- Trigger: Shuheng must own its state independently of any legacy GenericAgent checkout while still allowing GenericAgent as an optional runtime/source provider.
- Applies to: Shuheng storage path selection, `load_history()`, `cached_session_rows()`, `continue_cmd`, `session_meta.json`, `session_names.json`, harness ledgers/artifacts/traces, persistent and temporary subagents, Secret Vault, isolated OMP runtime files, sidebar display, and history restore behavior.
- Non-goal: This bridge must not delete, move, unzip, or destructively modify legacy GenericAgent history or memory files.

### 2. Signatures

- Shuheng history home defaults to `~/.shuheng`; `SHUHENG_HOME` overrides it, and legacy internal `SHUHENG_HOME` remains an accepted override.
- `SHUHENG_MEMORY_DIR` defaults to `~/.shuheng/memory`.
- `SHUHENG_TEMP_DIR` defaults to `~/.shuheng/temp`.
- Raw session rows are read from `MODEL_RESPONSES_DIR/model_responses*.txt`, where `MODEL_RESPONSES_DIR` defaults to `~/.shuheng/model_responses`.
- `session_meta.json`, `session_token_usage.json`, `.trash`, and `session_names.json` live under the Shuheng-owned history tree, not `GenericAgent/temp/model_responses`.
- `AGENT_HARNESS_DIR` defaults to `~/.shuheng/memory/agent_harness`.
- `SUBAGENTS_DIR` defaults to `~/.shuheng/memory/subagents`.
- `TEMP_SUBAGENTS_DIR` defaults to `~/.shuheng/temp/subagents`.
- Parameterized subagent store path helpers accept `SUBAGENTS_DIR` from `app.py`; the lower-level module must not import the app facade to discover storage roots.
- Deterministic subagent control alias helpers live in `subagent_store.py`: `subagent_control_alias_keys(...)` shapes explicit target/name/id values, and `resolve_subagent_control_alias(alias_map, target)` resolves already-built alias maps without reading `State` or `SubAgentRuntime`.
- Deterministic subagent control lifecycle/reuse intent helpers live in `control_protocol.py`: `subagent_control_persistence_intent(...)` interprets only explicit structured lifecycle fields and defaults to ephemeral/session-scoped behavior, while `subagent_control_force_new_intent(...)` interprets only explicit force-new/reuse fields. They must not infer persistence or no-reuse from natural-language target, value, name, profile, or context text.
- `app.py` remains the Orchestrator owner for `register_subagent_control_aliases(...)`, `apply_subagent_control(...)`, runtime subagent resolution, state mutation, ledgers, approvals, artifacts, and dispatch side effects.
- `SECRET_VAULT_DIR` defaults to `~/.shuheng/memory/secret_vault`.
- New Secret Vault verifier plaintext is `Shuheng Secret Vault v1`; historical verifier plaintext may be accepted only during unlock compatibility and must not be written for newly created vaults.
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
- `GENERICAGENT_ROOT` remains only an optional legacy-provider checkout path, not a Shuheng state root or core startup requirement.
- Missing-source rows may use metadata preview, description, rounds, last-user timestamp, and display name to remain visible.
- Missing-source rows must not pretend to be normal raw sessions.
- New main-agent sessions must bind their agent/client/backend log path to the Shuheng-owned `MODEL_RESPONSES_DIR` before runtime work starts.
- Session naming must persist through the same Shuheng-owned `session_names.json` registry; it must not use GenericAgent's default `frontends/session_names.py` storage path.
- Harness writes for tasks, approvals, artifacts, traces, schedules, gateway metadata, runtime provider metadata, and memory candidates must live under the Shuheng-owned `AGENT_HARNESS_DIR` by default.
- Persistent subagent memory must live under Shuheng-owned `SUBAGENTS_DIR`; temporary subagents must live under Shuheng-owned `TEMP_SUBAGENTS_DIR`.
- Persistent subagent home helpers must keep profile, memory, event, and metadata refs under `SUBAGENTS_DIR`; ordinary non-secret conversation turns remain history-owned under `MODEL_RESPONSES_DIR`.
- Secret Vault encrypted storage must live under Shuheng-owned `SECRET_VAULT_DIR` by default.
- New Secret Vault creation must encrypt the Shuheng verifier sentinel; legacy sentinels are accepted only as an isolated compatibility path for existing encrypted vaults.
- OMP memory append prompts must read Shuheng-owned memory sources, not GenericAgent `memory/`.
- On normal first launch with the default `~/.shuheng` home and a discovered legacy GenericAgent checkout, Shuheng may bootstrap existing GenericAgent state by copying missing files from that checkout's `temp/model_responses` and `memory` directories into the Shuheng-owned tree.
- Legacy bootstrap must be copy-missing-only: existing Shuheng files win over old GenericAgent files.
- Legacy `session_meta.json`, `session_names.json`, and `session_token_usage.json` are merged as JSON objects when Shuheng sidecars already exist; Shuheng keys win on conflict.
- Legacy bootstrap must not copy stale embedded runtime config from `memory/agent_harness/runtime/**`; isolated OMP runtime files are regenerated under Shuheng.
- Legacy bootstrap writes `.legacy_import.json` so later launches do not repeatedly scan and copy the same source tree.
- `restore_history()` must refuse direct restore when the source path is absent and must leave the active runtime untouched.
- When a raw source file reappears, cached raw-session processing clears missing-source markers.

### 4. Validation & Error Matrix

- Default import with no env override -> `MODEL_RESPONSES_DIR` is `~/.shuheng/model_responses`.
- Default import with no env override -> `AGENT_HARNESS_DIR`, `SUBAGENTS_DIR`, `TEMP_SUBAGENTS_DIR`, `SECRET_VAULT_DIR`, and isolated OMP runtime paths are all under `~/.shuheng`.
- Default import with no GenericAgent checkout -> Shuheng still imports and `shuheng-check` reports OMP core healthy.
- `SHUHENG_HOME=/tmp/shuheng-home` before import -> Shuheng history paths derive from `/tmp/shuheng-home`.
- `SHUHENG_HOME=/tmp/compat-home` before import and no `SHUHENG_HOME` -> Shuheng history paths derive from `/tmp/compat-home`.
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
- Good: `/rename`, model-owned `session.rename`, `/continue` parsing, and cached round counts all use Shuheng-owned sidecars.
- Base: The GenericAgent checkout still supplies `continue_cmd.py` and `session_names.py` code, but their storage globals are retargeted at runtime.
- Base: Operators can disable implicit bootstrap with `SHUHENG_DISABLE_LEGACY_IMPORT=1` or force it in custom-home tests with `SHUHENG_IMPORT_LEGACY=1`.
- Base: Test harnesses may retarget `MODEL_RESPONSES_DIR` to a temp directory, but must call `configure_frontend_history_storage()` after changing the path constants.
- Bad: Editing only `MODEL_RESPONSES_DIR` while leaving `continue_cmd._LOG_DIR` or `session_names._REG_PATH` on GenericAgent's default directory.
- Bad: Moving session history but leaving harness ledgers, subagent memory, Secret Vault, or OMP isolated runtime under the GenericAgent checkout.
- Bad: Migrating, deleting, or mutating old GenericAgent history files without an explicit migration task.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert default session history paths are inside Shuheng home and not inside `GenericAgent/temp/model_responses`.
- Tests must assert `AGENT_HARNESS_DIR`, `SUBAGENTS_DIR`, `TEMP_SUBAGENTS_DIR`, `SECRET_VAULT_DIR`, and isolated OMP runtime paths are inside Shuheng home and not inside the GenericAgent checkout.
- Tests must assert new Secret Vaults use the Shuheng verifier sentinel while existing legacy verifier sentinels still unlock through the isolated compatibility path.
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

## Scenario: Shared User Profile And Work-State Memory

### 1. Scope / Trigger

- Trigger: The user wants every Shuheng agent to share one description of the user's profile, current state, active projects, and work direction, and to keep that state updated from normal interactions.
- Applies to: Shuheng memory files, main-runtime context packs, subagent context packs, OMP append-system-prompt generation, memory inventory, and normal user/subagent-chat input paths.
- Non-goal: This does not let runtime providers or subagents directly write approved L2 facts, does not store secrets, and does not hydrate Secret Vault or temporary-session content into the normal shared profile.

### 2. Signatures

- Shared Markdown profile: `~/.shuheng/memory/user_profile.md`.
- Shared machine state: `~/.shuheng/memory/user_profile_state.json`.
- Context-pack fields:
  - top-level `shared_user_profile`.
  - `layers.L1_user_profile.included == true`.
  - `memory_pack.included[].scope == "user.shared-profile"`.
- OMP memory prompt section: `Shared User Profile`.

### 3. Contracts

- All main and persistent-subagent context packs must include the same shared user profile refs and a bounded redacted summary.
- The shared profile is an operational interaction-state summary, not an approved L2 long-term fact store.
- Normal user-originated main prompts, direct subagent chats, user-originated subagent tasks, and Web Console `main.prompt` / `agent.chat` / `agent.task` actions update interaction count, last interaction time, bounded recent intents, focus terms, project hints, source counts, and estimated work time.
- Secret Vault sessions and temporary sessions must not write into the normal shared profile.
- OMP append-system-prompt generation must read the same `user_profile.md` path without importing `app.py` or mutating TUI state.
- If the shared profile conflicts with an explicit current user instruction, agents must treat the profile as stale context and obey the current instruction.

### 4. Validation & Error Matrix

- Missing `user_profile.md` or `user_profile_state.json` -> layered memory initialization creates bounded default files.
- Main context pack -> includes `shared_user_profile.path == ~/.shuheng/memory/user_profile.md` and `L1_user_profile.included:true`.
- Persistent subagent context pack -> includes the same shared profile path and `user.shared-profile` memory hydration scope.
- OMP memory prompt generation -> includes `Shared User Profile` and the same file path.
- Temporary session input -> does not increase shared profile interaction count.
- Secret Vault input -> does not write normal shared profile state.
- Web Console `agent.chat` -> dispatches through the shared direct-chat path and updates the normal shared profile once.

### 5. Good/Base/Bad Cases

- Good: A user asks to update Shuheng agent memory behavior; the next main and subagent context packs both show the same shared profile, interaction count, focus terms, and profile refs.
- Base: A fresh install has an empty/default shared profile that agents can read without inventing personal facts.
- Bad: A subagent writes its own divergent user-profile file and other agents do not see it.
- Bad: Secret Vault task text or temporary scratch prompts appear in `user_profile.md`.
- Bad: The OMP provider imports `shuheng.app` just to obtain the profile path.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert shared user profile files are created, normal interactions and Web Console user actions update the machine state, main and subagent context packs hydrate the same profile refs, OMP memory prompt includes the profile, and temporary or Secret Vault sessions do not mutate the normal shared profile.
- `python3 -m py_compile src/shuheng/app.py src/shuheng/ohmypi_provider.py scripts/check_policy_gates.py`, `python3 scripts/check_policy_gates.py`, `python3 -m compileall -q src scripts`, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` must pass.

### 7. Wrong vs Correct

#### Wrong

```text
subagent A writes memory/subagents/A/user_profile.md -> only A sees the user profile.
```

#### Correct

```text
normal user input -> ~/.shuheng/memory/user_profile_state.json -> ~/.shuheng/memory/user_profile.md -> main and subagent context packs share the same L1_user_profile refs.
```

## Scenario: Context Pack Helper Module Boundary

### 1. Scope / Trigger

- Trigger: Shuheng context-pack, memory-hydration, context-layer, prompt-formatting, or context-ref-formatting helper logic is moved out of `src/shuheng/app.py`.
- Applies to: `src/shuheng/context_packs.py`, compatibility wrappers in `src/shuheng/app.py`, `build_context_pack()`, `memory_context_get`, OMP runtime context/ref prompts, policy gates, and unit tests.
- Non-goal: This does not move runtime dispatch, Web Console action routing, dashboard rendering, command handlers, storage-root selection, or context-pack artifact writing out of `app.py` unless a later task defines those boundaries explicitly.

### 2. Signatures

- Lower-level module: `src/shuheng/context_packs.py`.
- Compatibility wrappers in `app.py`:
  - `compact_nonempty_lines(text, limit=12, width=220)`.
  - `memory_hydration_pack(...)`.
  - `context_layers_for_task(...)`.
  - `indent_text(text, prefix)`.
  - `format_context_pack_for_prompt(pack)`.
  - `format_context_ref_for_prompt(pack, context_ref)`.
- Explicit module inputs include task ids, role/security context, profile/memory text, shared profile payloads, layered memory payloads, workspace context payloads, recent task/progress/trace/artifact rows, agent profile/memory refs, and default permission profile.

### 3. Contracts

- `context_packs.py` must not import `shuheng.app`, `.app`, `app`, `curses`, UI renderers, command handlers, `State`, `SubAgentRuntime`, `PanelItem`, or `RenderLine`.
- `context_packs.py` owns pure shaping of memory hydration rows, L0-L8 context layers, context-pack prompt text, context-ref prompt text, and small text formatting helpers that can operate from explicit inputs.
- `app.py` remains the compatibility facade and passes mutable runtime facts explicitly: shared user profile, Shuheng layered memory, workspace context, agent profile/memory refs, progress/task/artifact/trace rows, permission defaults, and security context.
- `build_context_pack()` still owns runtime orchestration, Secret Vault context-pack writes, normal context-pack artifact writes, and artifact index updates until a separate artifact-writer boundary exists.
- Context formatting must keep final-reply, deictic-reference, persistent-agent-request, dedicated-skill-scope, permission-profile, memory-hydration, workspace-provenance, and recent-artifact-ref sections semantically equivalent to the previous app-layer behavior.
- `context_layers_for_task(...)` must prefer progress ledger rows for `L5_progress_ledger` and fall back to task rows only when no progress rows are provided.
- Raw traces remain reference-only in `L8_raw_trace`; trace payloads, raw logs, Secret plaintext, and unbounded tool output must not be inlined.

### 4. Validation & Error Matrix

- `context_packs.py` imports `shuheng.app` or `curses` -> policy gate fails.
- `app.py` formatter wrapper produces different prompt text from `context_packs.py` for the same pack and default permission profile -> policy gate fails.
- `memory_hydration_pack(...)` omits `user.shared-profile`, `shuheng.layered-memory`, or `project.agent-harness` -> unit test or policy gate fails.
- Workspace context is included -> hydration uses `workspace.project-provenance` as secondary provenance, not primary memory ownership.
- Recent progress rows are provided -> `L5_progress_ledger.items` uses compact progress summaries.
- Recent trace rows are provided -> only trace refs appear in `L8_raw_trace`; payloads stay excluded.
- OMP receives a context ref after the first full context pack -> prompt contains `context_pack_ref` and does not repeat the full context pack body.

### 5. Good/Base/Bad Cases

- Good: `app.format_context_pack_for_prompt(pack)` delegates to `context_packs.format_context_pack_for_prompt(pack, default_permission_profile=PERMISSION_PROFILE_STANDARD)` and returns identical text.
- Good: `context_packs.context_layers_for_task(...)` receives explicit recent progress/artifact/trace rows and returns L0-L8 without reading app globals.
- Base: `build_context_pack()` still writes the context-pack artifact through app-owned artifact paths because mutable path retargeting remains in the app facade.
- Bad: `context_packs.py` imports `State` so it can read `state.current_title` directly.
- Bad: `context_packs.py` opens `AGENT_TRACES_PATH` directly and inlines raw trace payloads.
- Bad: A test imports only `shuheng.app` and never verifies the extracted module boundary.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `context_packs.py` has no reverse app/UI dependency and that app wrappers preserve formatter parity.
- Tests must assert `compact_nonempty_lines(...)`, `memory_hydration_pack(...)`, `context_layers_for_task(...)`, `format_context_pack_for_prompt(...)`, and `format_context_ref_for_prompt(...)` work directly from `context_packs.py`.
- Tests must assert memory hydration includes shared profile, layered memory, agent harness, subagent profile/memory, optional workspace provenance, and agent-mail refs.
- Tests must assert L0-L8 layer keys are returned, progress rows populate L5 when present, artifacts stay as refs, and raw trace payloads stay excluded.
- Release verification must keep `python3 scripts/check_policy_gates.py`, Ruff, pytest, compileall, build, wheel smoke, `git diff --check`, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent` green.

### 7. Wrong vs Correct

#### Wrong

```python
from shuheng.app import State

def context_layers_for_task(state: State, sub):
    traces = read_jsonl(AGENT_TRACES_PATH)
    return {"L8_raw_trace": {"payloads": traces}}
```

#### Correct

```python
def context_layers_for_task(*, recent_traces, active_session):
    return {
        "L8_raw_trace": {
            "included": False,
            "trace_refs": [row["trace_id"] for row in recent_traces if row.get("trace_id")],
        }
    }
```

## Scenario: Temporary Non-Persistent Main Sessions

### 1. Scope / Trigger

- Trigger: A user enters `/temp` to start a temporary main-agent session.
- Applies to: command routing, main-agent log path binding, session metadata, automatic local naming, description/category jobs, durable UI system messages, memory candidate creation, token usage persistence, and background session switching.
- Non-goal: This is not a Secret Vault session and does not encrypt or restore temporary content. It is an in-memory session that disappears when closed or replaced.

### 2. Signatures

- Command: `/temp`.
- Runtime state field: `State.temporary_session:true`.
- Backend log path: `os.devnull`.
- UI title: `临时会话`.

### 3. Contracts

- `/temp` starts a fresh main-agent context and binds the active agent plus LLM backends to `os.devnull`.
- Temporary sessions must not create `model_responses*.txt` history logs.
- Temporary sessions must not write `session_meta.json`, session names, automatic description/category metadata, model-owned persisted title renames, durable UI system messages, token usage registry rows, memory candidates, or direct subagent memory updates.
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

## Scenario: Shuheng Agent Bridge And OMP Plugin Client

### 1. Scope / Trigger

- Trigger: Agent clients that are not directly launched by the TUI need Shuheng-owned project context and governed proposal submission.
- Applies to: `src/shuheng/agent_bridge.py`, `shuheng-agent-bridge`, `python -m shuheng.agent_bridge`, repo-managed OMP plugin files under `integrations/omp-shuheng-plugin`, OMP `--tool` loading, and future Codex/Claude Code adapters that consume the same bridge contract.
- Non-goal: This bridge does not make OMP, Codex, Claude Code, or any plugin the owner of long-term memory, approval queues, schedule registries, task ledgers, artifacts, or traces.

### 2. Signatures

- Python module: `src/shuheng/agent_bridge.py`.
- Console script: `shuheng-agent-bridge`.
- Module command: `python -m shuheng.agent_bridge`.
- Bridge schema: `shuheng.agent_bridge.v1`.
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

- OMP plugin package: `integrations/omp-shuheng-plugin/package.json`.
- OMP custom tool entry: `integrations/omp-shuheng-plugin/tools/index.ts`.
- OMP plugin tools: `shuheng_context_get` and `shuheng_memory_candidate_submit`.
- Environment keys:
  - `SHUHENG_REPO` or `SHUHENG_ROOT`: Shuheng checkout used by the plugin when locating `src/shuheng/agent_bridge.py`.
  - `SHUHENG_BRIDGE_PYTHON`: Python executable used by the OMP plugin, default `python3`.
  - `GENERICAGENT_ROOT`: optional GenericAgent legacy-provider override consumed by `shuheng.app` discovery.
  - `SHUHENG_HARNESS_DIR`: harness directory override for bridge tests or isolated runs.
  - `SHUHENG_SECRET_VAULT_DIR`: secret vault directory override for bridge tests or isolated runs.

### 3. Contracts

- `AgentBridgeService` must be a thin facade over existing app-owned services; it must not reimplement memory, approval, context-pack, or scheduler governance.
- `memory_context_get` must call the same app-layer `memory_context_get` query path used by OMP host tools and must return `shuheng.query.v1` with `context_pack_ref` plus a JSON-safe context pack.
- `memory_candidate_submit` must call the same governed memory-candidate proposal path as OMP host tools and must return `shuheng.proposal.v1`.
- Bridge-submitted memory candidates must use source provenance such as `agent:omp_plugin`, not pretend to be direct human or internal TUI writes.
- Long-term memory writes remain `candidate_only`; the bridge may queue memory candidates and approval rows but must not append to subagent memory files directly.
- The default OMP usage path should be process-local `omp --tool <repo>/integrations/omp-shuheng-plugin/tools/index.ts` so a user can test the plugin without linking it into the system OMP plugin store.
- Persistent `omp plugin link <repo>/integrations/omp-shuheng-plugin` is optional and must be documented as an explicit user choice.
- The OMP plugin must call the bridge CLI with `PYTHONPATH=<repo>/src` so it can run from a checkout without requiring package installation.
- The OMP plugin must not read or write Shuheng JSONL stores directly.
- The OMP plugin must not call `queue_approval`, `queue_curated_memory_candidate`, scheduler helpers, or artifact writers itself; only Python Shuheng code owns those operations.
- Bridge metadata must report owner `shuheng.control_plane`, supported actions, relevant paths, and policy fields showing provider direct writes are disabled.
- Bridge metadata paths must distinguish `app_root_dir` from optional `genericagent_legacy_provider_checkout`; it must not expose a generic `root_dir` that can be mistaken for the Shuheng core root.

### 4. Validation & Error Matrix

- Bridge payload is not a JSON object -> `shuheng.agent_bridge.v1` error.
- Unknown bridge action -> `shuheng.agent_bridge.v1` error with `supported_actions`.
- `query` without endpoint -> `shuheng.agent_bridge.v1` error.
- `memory_context_get` target not found or ambiguous -> `shuheng.query.v1` error from the existing app query path.
- `memory_candidate_submit` without target or statement -> `shuheng.proposal.v1` error.
- `memory_candidate_submit` target is temporary/non-persistent -> no direct memory write; return the existing governed no-op result.
- Candidate text contains secrets or weak/empty content -> existing Memory Curator rejection path writes a rejected candidate record and no approval row.
- OMP plugin cannot parse bridge stdout as JSON -> plugin tool execution throws a user-visible tool error instead of fabricating success.
- Bridge CLI exits non-zero with a structured error payload -> plugin returns that structured error payload to the model.

### 5. Good/Base/Bad Cases

- Good: OMP loads `shuheng_context_get` through `--tool`, requests project context, and receives a context-pack artifact ref without mutating any ledger except the context-pack artifact index.
- Good: OMP calls `shuheng_memory_candidate_submit`; Shuheng validates the target, builds a memory-candidate artifact, appends a pending candidate row, queues a human approval, and records provenance.
- Base: A user links the plugin persistently with `omp plugin link` only after explicitly choosing to let OMP remember the repo-managed plugin.
- Base: Codex or Claude Code later calls the same bridge action names and gets the same schemas without OMP-specific contract names.
- Bad: A plugin writes directly to `${SUBAGENTS_DIR}/*/memory.md` or `memory_candidates.jsonl`.
- Bad: A plugin scrapes `context_packs/` or `subagents/` files directly instead of calling the bridge.
- Bad: The bridge adds a second memory-candidate schema instead of reusing `queue_curated_memory_candidate(...)`.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `AgentBridgeService` metadata includes `schema_version:"shuheng.agent_bridge.v1"`, owner `shuheng.control_plane`, supported bridge actions, and `provider_direct_writes:false`.
- Tests must assert bridge metadata includes `app_root_dir` and `genericagent_legacy_provider_checkout` and does not expose ambiguous `root_dir`.
- Tests must assert bridge `memory_context_get` writes a context-pack artifact and returns a `shuheng.query.v1` response with `context_pack_ref`.
- Tests must assert bridge `memory_candidate_submit` queues a `shuheng.proposal.v1` memory candidate through the existing approval path and records source `agent:omp_plugin`.
- Tests must assert unknown bridge actions return a structured bridge error.
- Tests must assert the repo-managed OMP plugin manifest points to `tools/index.ts`.
- Tests must assert the OMP plugin tool source contains `shuheng_context_get`, `shuheng_memory_candidate_submit`, `shuheng.agent_bridge`, and `PYTHONPATH=<repo>/src` wiring.
- Smoke checks should include `PYTHONPATH=src python3 -m shuheng.agent_bridge ...`, Bun-loading the plugin tool factory, and a temporary-HOME OMP plugin dry-run or process-local `--tool` smoke so the user's real system OMP config is not mutated.

### 7. Wrong vs Correct

#### Wrong

```text
OMP plugin opens `${SUBAGENTS_DIR}/researcher/memory.md` and appends a learned fact directly.
```

#### Correct

```text
OMP plugin calls shuheng-agent-bridge memory-candidate-submit; Shuheng builds a memory_candidate.v1 record, writes artifact refs, queues human approval, and only approved memory writes reach subagent memory.
```

## Scenario: Release Readiness And Evidence Posture

### 1. Scope / Trigger

- Trigger: Shuheng exposes public release, gateway, baseline, scheduler, and eval metadata that can otherwise overstate maturity.
- Applies to: `src/shuheng/release_readiness.py`, `src/shuheng/runtime_evidence.py`, `src/shuheng/baseline.py`, `src/shuheng/gateway_registry.py`, app compatibility wrappers such as `ensure_gateway_registry(...)`, `gateway_baseline_evidence(...)`, `gateway_service_descriptor(...)`, `architecture_baseline_report(...)`, `append_task_eval(...)`, `append_runtime_evidence(...)`, scheduler registry metadata, README release wording, and gateway/policy/runtime smoke tests.
- Non-goal: This does not certify full A2A/MCP compliance, install an always-on scheduler service, or replace heuristic eval with an authoritative external evaluator.

### 2. Signatures

- Release readiness report:
  - `schema_version:"shuheng.release_readiness.v1"`
  - `status:"experimental_alpha"`
  - `public_position`
  - `support_level.stable_local_surfaces`
  - `support_level.experimental_surfaces`
  - `support_level.known_gaps`
  - `monolith_risk`
  - `repository_hygiene`
  - `distribution_smoke`
  - `verification_commands`
- Gateway service descriptor:
  - `schema_version:"agentgateway.service.v1"`
  - `status:"local_no_auth_compatibility_surface"`
  - `security.schema_version:"shuheng.gateway_bind_safety.v1"`
  - `security.auth:"none"`
  - `security.local_only`
  - `security.allowed`
  - `release_posture:"experimental_alpha"`
- Gateway baseline evidence:
  - `gateway_baseline_evidence(state=None) -> dict`
  - `a2a_gateway.schema_version:"a2a.gateway.v1"`
  - `a2a_gateway.agent_cards[]`
  - `a2a_gateway.tasks[]`, `messages[]`, `artifacts[]`
  - `mcp_gateway.schema_version:"mcp.gateway.v1"`
  - `mcp_gateway.tools[]`, `resources[]`
  - `capability_registry`
  - `governance_components`
  - `gateway_service`
  - `bridge_registry`
- Baseline item fields:
  - `evidence_checks[]` with `ok`, `description`, and `level`
  - `evidence_levels`
  - `strongest_evidence_level`
  - `claim_limit`
- Runtime evidence rows:
  - `schema_version:"agentruntime.evidence.v1"`
  - `target_items[]`
  - `targets[]`
  - `check_id`
  - `level:"runtime"|"e2e"|"structural"|"unknown"`
  - `passed`
  - `summary`
  - `source`
  - `command`
  - `evidence_refs[]`
- Eval rows:
  - `score_method.method:"heuristic"`
  - `score_method.basis`
  - `score_method.limitations`

### 3. Contracts

- Public release posture must be explicit: stable local surfaces, experimental surfaces, and known gaps are separate lists.
- A2A and MCP gateway metadata must use compatibility-surface wording until real third-party client end-to-end tests exist.
- Gateway/Web Console has no built-in auth. It should bind to loopback by default; non-loopback daemon/serve binds require `SHUHENG_GATEWAY_ALLOW_REMOTE_BIND=1`.
- Baseline completion must not mean protocol certification. Structural checks such as callable existence, configured paths, schemas, and registry rows must be labeled as structural evidence.
- Runtime/e2e checks must be persisted in `runtime_evidence.jsonl` under the Shuheng-owned `AGENT_HARNESS_DIR`; baseline reports may upgrade an item's strongest evidence level only from passed runtime evidence whose `target_items` match that baseline item.
- Runtime evidence from local smoke tests is behavioral evidence for Shuheng's local harness path. It must not be described as A2A/MCP protocol certification or third-party client conformance.
- Release-readiness distribution-smoke metadata must be structured rather than
  only implied by command strings: it lists wheel and sdist artifacts,
  dependency-resolving install mode, public console scripts, checked entrypoint
  behaviors, and debug-only options that are not release gates.
- `architecture_baseline_report(...)` must be self-contained: when `gateway_data` is omitted, it must build a no-write `gateway_baseline_evidence(...)` snapshot instead of reporting existing A2A/MCP/gateway evidence as missing due to caller ordering.
- No-write evidence construction may read ledgers and daemon status, but must not rewrite `gateway.json`, `governance_components.json`, `bridge_registry.json`, runtime provider prompt files, ledgers, approvals, or artifacts.
- `ensure_gateway_registry(...)` remains the write path for refreshing the durable gateway registry file; direct baseline reporting is only a report/evidence path.
- Eval scores are heuristic. Factual/citation/source quality inferred from text/artifact presence must include limitations explaining that correctness is not independently verified.
- Scheduler registry metadata must say scheduler work is evaluated by the TUI loop or gateway/manual ticks, not by an installed always-on service by default.
- Release-readiness helpers should remain pure and must not import `app.py`.
- Runtime evidence, baseline item formatting, and gateway descriptor/resource payload helpers live outside `app.py`. These helper modules must not import `shuheng.app`; `app.py` owns runtime state, paths, daemon state, HTTP handlers, and compatibility wrapper names.

### 4. Validation & Error Matrix

- `/gateway` registry missing `release_readiness` -> release posture regression.
- Gateway service status is `network_capable` without no-auth/local wording -> overclaiming regression.
- Non-loopback gateway daemon start without `SHUHENG_GATEWAY_ALLOW_REMOTE_BIND=1` -> failed daemon status with `remote_bind_requires_SHUHENG_GATEWAY_ALLOW_REMOTE_BIND`.
- A2A/MCP status says certified/network-capable without compatibility metadata -> protocol overclaiming regression.
- Direct `architecture_baseline_report()` call without prebuilt `gateway_data` marks A2A/MCP as missing while `ensure_gateway_registry()` would mark it complete -> caller-ordering regression.
- Direct baseline report rewrites `gateway.json`, `governance_components.json`, or `bridge_registry.json` -> read-only evidence regression.
- Baseline item has no `evidence_checks` or `strongest_evidence_level` -> baseline evidence regression.
- `runtime_evidence.py`, `baseline.py`, or `gateway_registry.py` imports `shuheng.app` -> monolith backslide regression.
- Eval row has no `score_method` or limitations -> heuristic eval honesty regression.
- Scheduler registry says `always_on:true` by default -> scheduler ownership regression.
- Release readiness omits `distribution_smoke`, lists only wheel, or marks
  `--no-deps` / `--wheel-only` as a release gate -> distribution evidence
  regression.

### 5. Good/Base/Bad Cases

- Good: `/gateway` says Shuheng is `experimental_alpha`, A2A/MCP are compatibility surfaces, gateway auth is `none`, and baseline items show structural evidence limits.
- Good: `architecture_baseline_report()` called directly still reports A2A/MCP, governance, and external bridge evidence from a no-write snapshot.
- Good: `scripts/runtime_smoke.py` runs in a temporary `SHUHENG_HOME`, uses fake agents and loopback HTTP only, writes passed `agentruntime.evidence.v1` rows, and then the baseline report upgrades matching items to runtime/e2e evidence.
- Good: A completed subagent task writes `agenteval.v2` with heuristic score limitations and audit refs.
- Base: Local `127.0.0.1` gateway works without auth because it is loopback-only by default.
- Base: Operator deliberately sets `SHUHENG_GATEWAY_ALLOW_REMOTE_BIND=1` and handles external access control outside Shuheng.
- Bad: README or gateway metadata implies production-ready remote gateway or certified A2A/MCP support without client E2E evidence.
- Bad: Baseline report marks a component complete only because a function exists while hiding that evidence is structural only.
- Bad: A runtime smoke result is printed to stdout but not stored in `runtime_evidence.jsonl`, so later baseline reports cannot audit it.
- Bad: Baseline report depends on the caller remembering to call `ensure_gateway_registry(...)` first.

### 6. Tests Required

- `scripts/check_policy_gates.py` must assert `/gateway` contains `release_readiness` with stable, experimental, and known-gap lists.
- Tests must assert `/gateway` release readiness exposes structured
  distribution-smoke metadata for wheel+sdist, dependency-resolving install
  mode, public console scripts, and debug-only non-gate options.
- Tests must assert gateway service descriptors use `local_no_auth_compatibility_surface`, `security.auth:"none"`, and loopback safety by default.
- Tests must assert non-loopback gateway daemon start fails unless `SHUHENG_GATEWAY_ALLOW_REMOTE_BIND=1` is present.
- Tests must assert A2A/MCP metadata carries `certification:"not_protocol_certified"`.
- Tests must assert baseline reports contain evidence model, per-item evidence checks, strongest evidence level, and claim limits.
- Tests must assert `runtime_evidence.jsonl` is registered in governance paths, MCP resources, and gateway internal-mail metadata.
- Tests must assert a passed runtime/e2e evidence row upgrades a matching baseline item's `strongest_evidence_level` without changing the protocol-certification wording.
- Tests must assert extracted release/baseline/gateway helper modules stay independent from `shuheng.app` and preserve the app compatibility wrapper behavior.
- CI must run `scripts/runtime_smoke.py` as an isolated local smoke path in addition to function-level policy gates.
- Tests must assert direct `architecture_baseline_report()` completes A2A/MCP, governance, and external-bridge baseline items without mutating gateway/governance/bridge registry file signatures.
- Tests must assert eval rows contain `score_method.method:"heuristic"` and limitations explaining factual/citation correctness is not independently verified.
- Tests must assert scheduler registry has `runtime_ownership.always_on:false`.

### 7. Wrong vs Correct

#### Wrong

```json
{
  "gateway_service": {"status": "network_capable"},
  "a2a_gateway": {"status": "network_capable"},
  "baseline_comparison": {"items": [{"status": "complete"}]}
}
```

```python
def architecture_baseline_report(state=None, gateway_data=None):
    gateway = gateway_data or {}
    # Existing gateway evidence is now invisible unless caller remembered
    # to call ensure_gateway_registry(...) first.
```

#### Correct

```json
{
  "gateway_service": {
    "status": "local_no_auth_compatibility_surface",
    "security": {"auth": "none", "local_only": true}
  },
  "a2a_gateway": {
    "status": "compatibility_surface",
    "compatibility": {"certification": "not_protocol_certified"}
  },
  "baseline_comparison": {
    "items": [
      {
        "status": "complete",
        "strongest_evidence_level": "structural",
        "claim_limit": "Structural evidence only..."
      }
    ]
  }
}
```

```python
def architecture_baseline_report(state=None, gateway_data=None):
    gateway = gateway_data or gateway_baseline_evidence(state)
```
