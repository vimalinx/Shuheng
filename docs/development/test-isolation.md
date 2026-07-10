# Test Isolation and Shared-State Contract

## Import-time storage isolation

Tests importing `shuheng.app` must establish an isolated `SHUHENG_HOME` before
test-module collection imports the application. Harness and Secret Vault paths
must be descendants of that root. Do not globally replace `HOME` for the whole
suite; tests that exercise home expansion should override it locally.

A test must never read or write the maintainer's real `~/.shuheng`, model
configuration, Secret Vault, OMP configuration, sessions, task ledgers, or
agent projects. Forked children must not delete a temporary root owned by their
parent process.

## Shared JSON state

Application read-modify-write operations use one transaction covering the
latest read, normalization, mutation, durable temporary-file flush, atomic
replace, and bounded compensation. Locking only the final save can lose updates.

Whole-file replacement helpers are for tests or callers that intentionally own
the entire snapshot. Production code must not separately load a shared registry,
mutate it, and then overwrite changes made by another process.

No-op transactions do not replace the file. Nested mutations count as changes,
and committed results must not share mutable references with the transaction's
working copy. On failure, preserve the original exception and clean temporary
files.

## Required evidence

Storage changes need focused failure, rollback, atomicity, nested-mutation, and
multiprocess coverage. Release-sensitive changes also need a fresh subprocess
whose simulated real home remains untouched.

Run the full suite with bytecode/cache writes disabled for the release gate.
When concurrency or import-order behavior changes, include at least one clean
subprocess or spawned-process test rather than relying only on mocks.

Patch a dependency in the module that owns the function's runtime globals.
Replacing a re-exported alias does not affect calls made inside the original
module and can create a false green when the maintainer machine happens to
provide the external service that CI lacks.
