# Workflow Capability Benchmark

## Sources

- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph human-in-the-loop: https://docs.langchain.com/oss/python/langchain/frontend/human-in-the-loop
- Temporal workflow execution overview: https://docs.temporal.io/workflow-execution
- OpenAI Agents SDK handoffs: https://openai.github.io/openai-agents-python/handoffs/
- Prefect introduction: https://docs.prefect.io/v3/get-started
- Apache Airflow DAGs: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- Dagster jobs: https://docs.dagster.io/guides/build/jobs
- MCP specification: https://modelcontextprotocol.io/specification/2025-06-18
- A2A specification: https://github.com/a2aproject/A2A/blob/main/docs/specification.md

## Findings

- Durable workflow systems separate definition from execution/run state. Temporal treats a workflow execution as a durable, recoverable unit with persisted state transitions and replay.
- Agent workflow systems need explicit pause/resume points. LangGraph positions durable execution, streaming, and human-in-the-loop as core orchestration capabilities; its HITL pattern persists the interrupt so the run can resume from the pause.
- Production workflow systems expose run monitoring and control. Prefect, Airflow, and Dagster all make runs inspectable from a UI and support scheduled or triggered execution.
- Workflow UX must collect runtime parameters without bypassing the runner. Prefect emphasizes parameterized, monitored runs; this maps to Shuheng keeping `/workflows` input collection as a panel convenience while preserving `create_workflow_run_v0(...)` as the execution owner.
- Agent orchestration needs delegation contracts, not free chat. OpenAI Agents SDK handoffs model delegation to specialist agents; MCP separates tools/resources/prompts; A2A standardizes remote agent tasks, artifacts, streaming, push notifications, and context grouping.

## Implications For Shuheng

- Current workflow v0 is correctly ledger-first and orchestrator-owned, but it is still a lightweight local runner, not a Temporal-class durable executor.
- The highest-value near-term UI improvement is parameterized run creation from `/workflows`, because it removes the manual command gap without expanding runner authority.
- Future workflow work should prioritize run observability, resumability, human approval, artifact provenance, and task/agent bridge contracts before adding visual graph editing or arbitrary tool execution.
- The panel prompt must not become a second runner. It should collect typed key/value inputs, validate missing required values, and then hand off to the existing manifest-backed runner.
