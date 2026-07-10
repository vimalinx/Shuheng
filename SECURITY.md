# Security Policy

## Supported Status

Shuheng is currently an experimental local alpha. The supported security posture
is local-first use on a trusted workstation.

## Reporting Vulnerabilities

Please report suspected vulnerabilities through GitHub's
[private vulnerability reporting](https://github.com/vimalinx/Shuheng/security/advisories/new)
before publishing exploit details. The repository setting is enabled. Include:

- Affected version or commit.
- Steps to reproduce.
- Expected and actual behavior.
- Whether secrets, local files, network exposure, or external side effects are involved.

## Security Boundaries

- Shuheng's supported interaction surfaces are the local curses TUI and the
  local JSONL stdio agent gateway. Agent Mail and resource registries remain
  local operator-owned state. The persistent gateway exposes only agent
  discovery, governed message dispatch, task status, and gateway status; its
  JSONL frames do not expose internal metadata or machine-specific paths.
- `shuheng-agent-bridge` and `python -m shuheng.agent_bridge` are trusted local
  provider-integration interfaces, not public-gateway aliases. Do not attach an
  untrusted client to those internal commands.
- OMP is a local coding-agent runtime. Its tools can read, write, execute, and
  make network requests with the current user's operating-system authority.
  Shuheng's default posture is governed. Prompt-free broad authority requires
  both `full` permissions and `yolo` approval; `yolo` without `full` is
  programmatically downgraded, while prompted `full` mode retains the high-risk
  action gate.
- OMP receives a narrow subprocess environment by default. Explicitly adding a
  variable to its allowlist may expose that variable to the model and its Tools.
- OMP/Bun probes and installers, plus Pi-native install and health processes,
  also receive minimal environments; ambient cloud, API, and SSH credentials
  are not forwarded.
- Pi-native Agent Project Tools are trusted local JavaScript. Capability grants
  decide which Tool is loaded; they are not an OS filesystem, syscall, or
  network sandbox.
- Model credentials belong in Shuheng-owned private state. Secret Vault content,
  model credentials, normal session logs, runtime state, local workflow state,
  and machine-specific paths must not be committed.
- Shuheng creates its root local state directory with mode `0700`; credential
  files, credential backups, and credential temporary files use mode `0600`.
- A2A/MCP-shaped data is local metadata for adapter design, not a reachable or
  certified protocol implementation.

## Operator Responsibilities

- Review Agent Project Tool source before granting executable Tools.
- Keep `full`/`yolo` disabled when working in an untrusted repository or with
  untrusted instructions.
- Do not run Shuheng with credentials or filesystem access that the task does
  not require.
- Treat third-party OMP/Pi packages and plugins as executable dependencies and
  keep them on versions supported by the release notes.

## Disclosure Expectations

For high-impact issues, allow reasonable time for triage and a fix before public
disclosure. If you are unsure whether something is security-sensitive, report it
privately first.
