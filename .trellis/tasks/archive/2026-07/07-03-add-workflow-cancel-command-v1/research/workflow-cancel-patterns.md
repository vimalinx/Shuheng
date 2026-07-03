# Workflow Cancel Patterns

## Sources

* Temporal cancellation docs: https://docs.temporal.io/develop/python/cancellation
* Argo Workflows stop docs: https://argo-workflows.readthedocs.io/en/latest/cli/argo_stop/
* Argo Workflows terminate docs: https://argo-workflows.readthedocs.io/en/latest/cli/argo_terminate/
* GitHub Actions REST workflow-runs docs: https://docs.github.com/en/rest/actions/workflow-runs
* LangGraph persistence docs: https://docs.langchain.com/oss/python/langgraph/persistence

## Findings

Temporal distinguishes cancellation from abrupt termination and expects workflow code to handle cancellation cooperatively. That maps well to Shuheng's long-term target, but v1 should not pretend to cooperatively cancel subagents until task abort and checkpoint semantics exist.

Argo exposes both stop and terminate controls. Stop still runs exit handlers; terminate stops immediately without exit handlers. The useful pattern for Shuheng is separating a normal cancellation lifecycle from a future force/kill lifecycle.

GitHub Actions exposes workflow-run cancellation as a first-class lifecycle endpoint on a run id. The useful product convention is that cancellation is addressed to a run, not a definition, and is visible as a terminal run state.

LangGraph emphasizes durable execution via checkpoints and persistence. This reinforces that cancellation should be a ledgered lifecycle transition first; replay/recovery should be a later layer rather than mixed into v1 cancel.

## Implications For This Task

* Use `/workflow cancel <run_id>` rather than cancelling by workflow definition.
* Write a terminal workflow run state, not a hidden in-memory flag.
* Do not read or hydrate artifacts during cancellation.
* Do not abort subagent tasks in v1 because Shuheng has not yet defined cooperative task cancellation.
* Leave checkpoint/replay, cleanup hooks, and retry policies for future tasks.
