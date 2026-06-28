# Release Audit Baseline

## Local Evidence

* `pytest` passed with 171 tests in the audit turn.
* `scripts/check_policy_gates.py` passed.
* `git diff --check` passed.
* Wheel/sdist build passed with `python3 -m build --sdist --wheel`.
* Isolated wheel install could run `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.
* Narrow secret-pattern scan did not find realistic API key/private key literals.

## Current Gaps

* No root `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, or CI workflow.
* `pyproject.toml` is minimal and lacks release metadata such as license, authors, classifiers, keywords, and project URLs.
* Untracked local/private files exist and should not be published: `config/mcporter.json`, `references/taste-ledger.md`, `docs/foreign-student-acquisition-research.md`, and `docs/homework-pricing-research.md`.
* README already labels Shuheng as experimental alpha, but release checks are not automated.
* OMP plugin docs/package still present user-facing GA-TUI branding and old local path examples.
* Gateway/Web Console has no built-in authentication and must remain loopback/default-local unless protected by an external trusted boundary.
* A2A/MCP surfaces are compatibility metadata/surfaces, not certified implementations.
* Eval scores are heuristic and should not be marketed as factual/citation proof.
* `app.py` remains a large composition module; release hardening should expose this as a known gap rather than hide it.

## Recommended Implementation

* Add project governance files and package metadata.
* Add CI and a local release hygiene script.
* Ignore known private local paths without deleting user files.
* Update public docs and plugin wording to match Shuheng alpha positioning.
* Add a pragmatic lint baseline that can run in CI without forcing unrelated monolith rewrites.
* Keep compatibility identifiers stable until a dedicated migration exists.
