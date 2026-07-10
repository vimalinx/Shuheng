# Runtime Governance Contract

## Ownership

OMP is Shuheng's permanent main Agent and default Provider. Shuheng remains the
Orchestrator and owns user-visible sessions, task/progress ledgers, approvals,
artifact references, memory candidates, schedules, recovery records, and trace
normalization. Optional Providers are bounded workers and cannot silently
replace the main runtime.

Runtime modules must not reverse-import the TUI composition module merely to
reach mutable state. App-owned callbacks should be injected at composition
time. Provider events are observations; only the Orchestrator may turn them
into authoritative task, approval, memory, or recovery transitions.

## Authority and approvals

The default OMP posture must be governed. Broad host access remains available
for expert local use, but `full` permissions and `yolo` approval are explicit
operator choices. They must never be inferred from a missing value or malformed
configuration. `yolo` is effective only with `full`; prompted `full` modes must
retain the program-level high-risk action gate.

Long-term memory remains candidate-only. Provider tools may read bounded state
or submit governed proposals, but they may not directly approve work, mutate
ledgers, publish externally, or write durable memory.

Every bounded worker assignment carries an explicit objective, role,
capability intersection, output contract, task id, and provenance references.
Agent Project workers additionally carry an immutable Build digest and Run
Manifest. Executable Tool grants and task-policy approval are separate facts.

## Credentials and subprocesses

Model configuration belongs under Shuheng-owned state, never the source tree.
Directories containing credentials use mode `0700`; secret-bearing files,
temporary files, and backups use mode `0600`. Errors and logs must not include
credential values.

OMP receives a narrow child environment assembled for its task. Host credential
variables, SSH agent sockets, cloud credentials, and unrelated application
tokens are excluded by default. Operators may explicitly allow additional
variable names when their environment requires them. Shuheng-generated model
key variables remain transient and are referenced from generated OMP model
files rather than written there as plaintext.

OMP/Bun probes and installers, plus Pi-native install and live-health commands,
reuse minimal runtime environments. Ambient cloud/API credentials and SSH agent
sockets are not forwarded to third-party runtime code.

## Scenario: Runtime authority and setup

### 1. Scope / Trigger

Apply this contract whenever OMP/Pi setup, provider launch arguments,
permission profiles, approval modes, or child-process environment wiring
changes. These paths cross the CLI, generated provider config, runtime process,
and Shuheng policy layers.

### 2. Signatures

```text
shuheng runtime setup-omp [--replace] [--json]
shuheng runtime setup-pi [--json]
shuheng runtime check [--require-pi] [--json]
shuheng-check [--package-only]

governed_ohmypi_approval_mode(value, *, permission_profile) -> str
ohmypi_rpc_command(..., approval_mode=None, permission_profile=None) -> list[str]
pi_native_subprocess_env(base_env=None) -> dict[str, str]
```

### 3. Contracts

- OMP is pinned to `@oh-my-pi/pi-coding-agent@16.1.7` and requires Bun
  `>=1.3.14`; Pi is pinned to `@earendil-works/pi-coding-agent@0.80.6` through
  the shipped lockfile.
- Default authority is `standard + write`. `SHUHENG_OMP_APPROVAL_MODE=yolo`
  becomes effective only when `SHUHENG_OMP_PERMISSION_PROFILE=full` is also
  present. Operator-supplied extra CLI arguments cannot override this gate.
- `full + write/always-ask` keeps the high-risk action list and denies a risky
  extension approval request. Long-term memory remains candidate-only in every
  profile.
- OMP task processes inherit only the runtime allowlist plus valid names listed
  by `SHUHENG_OMP_INHERIT_ENV`. Generated `SHUHENG_OMP_API_KEY_*` values may be
  injected explicitly. Probe/install processes use their own minimal allowlist.
- `runtime check` requires OMP. Pi affects the exit code only with
  `--require-pi`. OMP success requires both pinned version checks and a fresh,
  isolated RPC ready/state round trip. `shuheng-check --package-only` proves
  package entrypoints only and is not runtime-readiness evidence.

### 4. Validation & Error Matrix

| Condition | Required result |
| --- | --- |
| OMP executable missing | non-zero; action is `shuheng runtime setup-omp` |
| Existing unsupported OMP, no `--replace` | preserve it and return an explicit replacement action |
| Bun below `1.3.14` | stop before installation with an upgrade action |
| OMP prints the expected version but cannot complete RPC state | non-zero `rpc_unavailable` result |
| `yolo` without `full` | normalize to `write` in generated config and RPC argv |
| Risky prompted Tool under `full` | deny at the program-level approval gate |
| Pi lock/package version mismatch | non-zero when Pi is required; exact setup action |
| Ambient cloud/API/SSH variables | absent from OMP/Bun/npm/Node child environments |
| Invalid inherited environment name | ignore it; never synthesize or expand it |

### 5. Good / Base / Bad Cases

- Good: an expert sets both `full` and `yolo`, understands that OMP receives
  prompt-free broad host authority, and runs only in a trusted checkout.
- Base: no overrides produce `standard + write`; OMP is usable while risky
  actions and durable state changes remain governed.
- Bad: forwarding `os.environ`, accepting `--approval-mode=yolo` from extra
  args, or treating an optional missing Pi SDK as proof that OMP is unusable.

### 6. Tests Required

- Unit-test both keys of the approval matrix and assert the final generated
  config and RPC command, not merely the normalization helper.
- Assert risky extension prompts fail closed under `full + write` and that a
  low-risk allowed Tool follows the prompted path.
- Execute fake OMP, Bun, npm, and Node processes that fail if representative
  API, cloud, or SSH variables are present.
- Exercise clean `HOME`, custom `BUN_INSTALL`, missing binaries, incompatible
  versions, explicit replacement, OMP RPC failure, optional Pi, and required Pi
  exit codes.

### 7. Wrong vs Correct

```python
# Wrong: a single environment value silently grants prompt-free authority.
mode = normalized_ohmypi_approval_mode(os.environ["SHUHENG_OMP_APPROVAL_MODE"])

# Correct: the final launch value is governed by both authority inputs.
mode = governed_ohmypi_approval_mode(
    requested_mode,
    permission_profile=permission_profile,
)
```

## Workers, ledgers, and artifacts

Read-only work may run in parallel. Repository writes participate in the shared
single-writer policy. A busy worker queue must preserve the original task id,
approval references, expected Build identity, and explicit grants.

Durable rows keep bounded previews and artifact/context references, not full
prompts, frozen source bytes, credentials, or mutable source paths. Terminal
status must remain truthful: failed, cancelled, aborted, incomplete, and
completed are distinct outcomes.

## Recovery and external protocols

Recovery may replay only inputs that were intentionally made durable and whose
authority is still valid. Agent Project source is privacy-first and not stored
as replayable frozen bytes, so stale runs require a new build confirmation.

A2A/MCP-shaped objects are local inspection and adapter records until real
third-party conformance tests exist. The supported gateway is local JSONL stdio,
with Agent Mail and resource registries owned by the local control plane.

The persistent stdio gateway has a positive public action schema:
`agent_directory`, `message_send`, `task_status`, and `gateway_status`. Its
startup frame and responses must not expose bridge metadata, internal paths,
credential names, context packs, or private ledger locations. Internal bridge
actions remain outside this process boundary. `shuheng-agent-bridge` and the
`shuheng.agent_bridge` module are trusted local integration interfaces, not
aliases for the public gateway. Unknown, empty, malformed, or private action
requests fail closed against that positive public action schema.
