---
name: domino-genai-tracing
description: Trace and evaluate GenAI applications including LLM calls, agents, RAG pipelines, and multi-step AI systems in Domino. Uses the Domino SDK (@add_tracing decorator, DominoRun context) with MLflow 3.2.0. Captures token usage, latency, cost, tool calls, and errors. Supports LLM-as-judge evaluators and custom metrics. Use when building agents, debugging LLM applications, or needing audit trails for GenAI systems.
---

# Domino GenAI Tracing Skill

This skill provides comprehensive knowledge for tracing and evaluating GenAI applications in Domino Data Lab, including LLM calls, agents, RAG pipelines, and multi-step AI systems.

## Two Deployment Modes

GenAI tracing works differently depending on where your code runs:

| Mode | Where traces appear | When to use |
|------|-------------------|-------------|
| **Deployed App** (Production) | App **Performance tab** | FastAPI/Flask apps deployed as Domino Apps |
| **Development / Evaluation** | **Experiments** UI | Batch scripts, Domino Jobs, Workspaces |

**Critical difference:** In a deployed Domino App, Domino auto-creates an experiment named `agent_experiment_{app_id}` and the Performance tab reads from it. If you call `mlflow.set_experiment()` or wrap calls in `DominoRun()`, traces go to your custom experiment instead — and the Performance tab won't see them.

## Key Concepts

### What GenAI Tracing Captures

The Domino SDK automatically captures:
- **Token usage** - Input and output tokens per call
- **Latency** - Time for each operation
- **Cost** - Estimated cost per call
- **Tool calls** - Function/tool invocations
- **Errors** - Exceptions and failure modes
- **Model parameters** - Temperature, max_tokens, etc.

### Core Components

1. **`@add_tracing` decorator** - Wraps agent functions to capture traces (works standalone — no `DominoRun` required)
2. **`mlflow.start_span()`** - Creates child spans for LLM calls and tool executions inside the agent loop
3. **`DominoRun` context manager** - Groups traces into runs for development/evaluation (Experiments UI only)
4. **Evaluators** - Custom functions to score outputs
5. **MLflow integration** - View traces in Experiment Manager or App Performance tab

## Related Documentation

- [TRACING-SETUP.md](./TRACING-SETUP.md) - Environment & SDK setup
- [ADD-TRACING-DECORATOR.md](./ADD-TRACING-DECORATOR.md) - @add_tracing usage, span_type, autolog_frameworks
- [DOMINO-RUN.md](./DOMINO-RUN.md) - DominoRun context manager (development/evaluation only)
- [EVALUATORS.md](./EVALUATORS.md) - LLM-as-judge, custom evaluators
- [MULTI-AGENT-EXAMPLE.md](./MULTI-AGENT-EXAMPLE.md) - Complete multi-agent example

## Quick Start — Deployed App (Production)

For a FastAPI app deployed as a Domino App. Traces appear in the **App Performance tab**.

```python
# main.py — lifespan: autolog only, NO set_experiment, NO DominoRun
import mlflow
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Each autolog in its own try/except so one failure doesn't block the other
    try:
        mlflow.openai.autolog()
    except Exception:
        pass
    try:
        mlflow.anthropic.autolog()
    except Exception:
        pass
    yield

app = FastAPI(lifespan=lifespan)
```

```python
# orchestrator.py — @add_tracing on the core agent function
import mlflow
from domino.agents.tracing import add_tracing

@add_tracing(
    name="agent_turn",
    span_type="AGENT",
    autolog_frameworks=["openai", "anthropic"],
)
async def run_agent(messages: list[dict]) -> dict:
    # LLM calls and tool calls go here (see ADD-TRACING-DECORATOR.md)
    ...

# router.py — call the traced function directly, NO DominoRun wrapper
@app.post("/chat")
async def chat(request: ChatRequest):
    return await run_agent(request.messages)
```

## Quick Start — Development / Evaluation

For batch scripts, Domino Jobs, or Workspaces. Traces appear in the **Experiments UI**.

```python
import mlflow
from domino.agents.tracing import add_tracing
from domino.agents.logging import DominoRun

mlflow.openai.autolog()

@add_tracing(name="my_agent", autolog_frameworks=["openai"])
def my_agent(query: str) -> str:
    response = llm.invoke(query)
    return response

# DominoRun groups traces into a run visible in Experiments
with DominoRun() as run:
    result = my_agent("What is machine learning?")
```

## Framework Support

| Framework | Auto-log Command |
|-----------|------------------|
| OpenAI | `mlflow.openai.autolog()` |
| Anthropic | `mlflow.anthropic.autolog()` |
| LangChain | `mlflow.langchain.autolog()` |

## Viewing Traces

### Deployed Apps (Production)

1. Navigate to your Domino App
2. Click the **Performance** tab
3. Traces appear automatically (routed to `agent_experiment_{app_id}`)

### Development / Evaluation

1. Navigate to **Experiments** in your Domino project
2. Select the experiment
3. Select a run
4. View the **Traces** tab for span tree visualization

## Blueprint Reference

Official GenAI Tracing Tutorial:
https://github.com/dominodatalab/GenAI-Tracing-Tutorial

## Documentation Links

- Domino GenAI Tracing: https://docs.dominodatalab.com/en/cloud/user_guide/fc1922/set-up-and-run-genai-traces/
