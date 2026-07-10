# Release Engineering Contract

## Source boundary

The public repository and built archives contain Shuheng-owned source,
contributor documentation, tests, integrations, and governance files. Local
agent-framework state, task journals, credentials, sessions, private research,
runtime caches, and dependency trees are not public source.

Every retained third-party-derived file needs an explicit compatible license
and attribution. Root MIT metadata must not be used to relabel upstream code.

## Reproducibility

Release claims are proved from a clean source archive, not a maintainer checkout.
The CI matrix covers the minimum supported Python and the highest advertised
classifier. Build isolation must succeed with the declared minimum build
backend. Tests may not require sibling repositories, existing OMP sessions,
local credentials, or maintainer-specific paths.

The release gate includes Ruff, repository hygiene, policy checks, stdio
gateway dogfood, runtime smoke, full pytest, compileall, package build, direct
wheel/sdist inspection, installed entrypoint checks, and `git diff --check`.

## Install and upgrade

The recommended installer creates a user-owned virtual environment and launcher
directory. It must either establish a usable permanent OMP runtime or stop with
an exact setup instruction. A doctor result is successful only when required
runtime components are actually available.

Optional Pi-native setup is exposed through an installed command and remains
separate from the OMP main-runtime requirement. Installer dry-run mode cannot
write files or require a network response.

Package versions follow PEP 440 and must compare newer than every previously
published distribution. Before tagging, test both a clean install and an
ordinary pip upgrade from the previous public release.

## Artifacts and publication

Inspect wheel and sdist member lists, metadata, entrypoints, license files,
manifest consistency, wheel RECORD hashes/sizes, realistic secret patterns,
and local absolute paths before installation. Release assets receive SHA-256
checksums.

CI must pass on the exact public commit that will be tagged. A local green run
is supporting evidence, not a substitute. Publishing, pushing, or creating a
GitHub release remains a separate human-approved action.

## Branch topology and promotion

`main` is the default, release-ready OMP core line. `dev` is the integration
line for Pi ecosystem, custom Agent, Skill/Plugin, scheduler, and other forward
development. Both branches run the full CI matrix on push; pull requests run
the same matrix independently of their base branch.

Normal work starts from `dev` or a short-lived `feature/*` branch. A release
candidate moves through a `dev -> main` pull request only after the strict
Python 3.10 and 3.13 checks pass on an up-to-date head. `main` uses linear
history and forbids force pushes and deletion. `dev` accepts normal integration
pushes but also forbids force pushes and deletion.

Hotfixes branch from `main`, return to `main` through a pull request, and are
then synchronized back into `dev`. The repository default remains `main`, so
public browsing and installer references resolve to the release-ready line.
Optional Pi setup remains explicit on `main`; experimental work belongs on
`dev` until promoted through the same release gate.

## Scenario: Alpha build, install, and upgrade proof

### 1. Scope / Trigger

Apply this contract to package metadata, installer defaults, runtime dependency
pins, manifests, CI, wheel/sdist inspection, and release-version changes.

### 2. Signatures

```text
python -m build --sdist --wheel --outdir <dist-dir>
python scripts/wheel_smoke.py --dist-dir <dist-dir>
python scripts/wheel_smoke.py --dist-dir <dist-dir> --upgrade-from-alpha1
sh scripts/install.sh [--version TAG | --wheel-url URL | --source PATH]
shuheng --version
```

### 3. Contracts

- Human tag `v0.2.0-alpha.1` maps to PEP 440 package version `0.2.0a1`.
  `pyproject.toml`, `shuheng.__version__`, CLI output, artifact filenames, and
  installed metadata must agree.
- The public source set is Git-tracked files plus intentional untracked release
  additions; ignored maintainer state, credentials, caches, and dependency
  trees never enter source archives.
- Wheel and sdist checks cover members, metadata, entrypoints, license files,
  manifest consistency, RECORD hashes/sizes, secret-like literals, and local
  absolute paths before running installed entrypoints.
- Artifact smoke may use `shuheng-check --package-only`; the recommended
  installer must run the real OMP setup/doctor path and fail when it is unusable.
- Upgrade proof installs the published alpha.1 artifact and then `0.2.0a1` with
  ordinary pip semantics. It must not use `--force-reinstall`.

### 4. Validation & Error Matrix

| Condition | Required result |
| --- | --- |
| Version sources disagree | release hygiene fails |
| Private/local member in wheel or sdist | archive inspection fails before install |
| Missing/mismatched RECORD hash or size | wheel inspection fails |
| Source archive omits a required public contract | sdist inspection fails |
| OMP cannot be established by installer | installer exits non-zero with exact action |
| `0.2.0a1` does not replace installed `0.1.0` | upgrade smoke fails |
| Declared minimum backend cannot build | minimum-backend CI gate fails |

### 5. Good / Base / Bad Cases

- Good: a clean public snapshot builds under Python 3.10 and 3.13, installs the
  exact artifacts, verifies OMP, and upgrades from alpha.1.
- Base: package-only smoke validates an artifact in isolation while clearly
  reporting that runtime readiness was not checked.
- Bad: building from a maintainer checkout containing ignored local state, or
  making a doctor return success solely because Python imports work.

### 6. Tests Required

- Run Ruff, hygiene, policy, stdio dogfood, runtime smoke, full pytest,
  compileall, Node syntax/live health, and `git diff --check`.
- Build with the declared minimum setuptools as well as isolated build mode.
- Inspect and install both wheel and sdist; test console scripts and version.
- Run the normal alpha.1-to-current pip upgrade in an isolated environment.
- Run at least the minimum and highest advertised Python versions from a public
  source snapshot without sibling repositories or maintainer credentials.

### 7. Wrong vs Correct

```text
Wrong: shuheng-check --package-only -> claim the machine is runtime-ready
Correct: artifact smoke uses --package-only; installer/CI separately run the
         pinned OMP setup and real runtime check
```

## Security posture

The release remains an experimental local alpha. Security documentation states
the real local host/tool boundary, provides a working private reporting route,
and distinguishes trusted local executable Tools from an OS sandbox. Active
documentation and templates describe the supported local curses TUI and JSONL
stdio contracts as the release interaction surfaces.
