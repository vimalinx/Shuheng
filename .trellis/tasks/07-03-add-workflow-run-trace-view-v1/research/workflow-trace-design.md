# Workflow Trace View Design Notes

## Design Decision

Implement a read-only text trace command before graph editing or arbitrary
workflow tool execution.

## Reasoning

- Durable workflow engines and agent orchestration baselines emphasize
  inspectable execution state, human-in-the-loop pause points, artifact
  references, and traceability before advanced visual editing.
- Shuheng already writes the authoritative state to append-only ledgers, so the
  next useful step is to make that state queryable per workflow run.
- A pure formatter in `workflows.py` keeps orchestration boundaries intact:
  `app.py` reads ledgers, while `workflows.py` projects rows into text.

## MVP Boundary

- Add command aliases `/workflow trace <run_id>` and
  `/workflow provenance <run_id>`.
- Render linked refs only; do not inline raw artifacts or raw trace payloads.
- Do not continue, cancel, approve, dispatch, write traces, or mutate any
  workflow row.
