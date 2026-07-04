# Shuheng OMP Bridge Plugin

Project-managed Oh My Pi plugin for consuming Shuheng-owned context and submitting governed memory proposals.

## Use Without Mutating System OMP

```bash
SHUHENG_REPO=/path/to/Shuheng \
  omp --tool /path/to/Shuheng/integrations/omp-shuheng-plugin/tools/index.ts
```

This loads the Shuheng bridge tools for that OMP process without linking the
plugin into the user's global OMP plugin store.

## Optional Persistent Link

Only run this if you explicitly want OMP to remember the plugin link:

```bash
omp plugin link /path/to/Shuheng/integrations/omp-shuheng-plugin
```

## Tools

- `shuheng_context_get`: read a Shuheng context pack and artifact ref.
- `shuheng_memory_candidate_submit`: submit a memory candidate through Shuheng validation and human approval.

The plugin does not write Shuheng memory, approvals, schedules, or ledgers directly. It calls `shuheng.agent_bridge`, and Shuheng remains the source of truth. The `shuheng_*` tool names are preserved as compatibility identifiers.
