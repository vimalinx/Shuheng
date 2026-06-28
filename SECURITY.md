# Security Policy

## Supported Status

Shuheng is currently an experimental local alpha. The supported security posture
is local-first use on a trusted workstation.

## Reporting Vulnerabilities

Please report suspected vulnerabilities privately by opening a private advisory
or contacting the maintainer before publishing exploit details. Include:

- Affected version or commit.
- Steps to reproduce.
- Expected and actual behavior.
- Whether secrets, local files, network exposure, or external side effects are involved.

## Security Boundaries

- The Gateway and Web Console have no built-in authentication and should bind to
  loopback by default.
- Non-loopback Gateway binding requires `GA_TUI_GATEWAY_ALLOW_REMOTE_BIND=1` and
  a trusted external access boundary.
- Secret Vault content, normal session logs, runtime model credentials, and local
  machine paths must not be committed.
- A2A/MCP surfaces are compatibility surfaces unless backed by real third-party
  client conformance tests.

## Disclosure Expectations

For high-impact issues, allow reasonable time for triage and a fix before public
disclosure. If you are unsure whether something is security-sensitive, report it
privately first.
