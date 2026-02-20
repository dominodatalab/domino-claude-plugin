---
name: domino-genai-tracing
description: Trace and evaluate GenAI applications including LLM calls, agents, RAG pipelines, and multi-step AI systems in Domino. Uses the Domino SDK (@add_tracing decorator, DominoRun context) with MLflow 3.2.0. Captures token usage, latency, cost, tool calls, and errors. Supports LLM-as-judge evaluators and custom metrics. Use when building agents, debugging LLM applications, or needing audit trails for GenAI systems.
---

# Domino GenAI Tracing Skill

This skill provides comprehensive knowledge for tracing and evaluating GenAI applications in Domino Data Lab, including LLM calls, agents, RAG pipelines, and multi-step AI systems.

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

1. **`@add_tracing` decorator** - Wraps functions to capture traces
2. **`DominoRun` context manager** - Groups traces into runs with aggregation
3. **Evaluators** - Custom functions to score outputs
4. **MLflow integration** - View traces in Experiment Manager

## Related Documentation

- [TRACING-SETUP.md](./TRACING-SETUP.md) - Environment & SDK setup
- [ADD-TRACING-DECORATOR.md](./ADD-TRACING-DECORATOR.md) - @add_tracing usage
- [DOMINO-RUN.md](./DOMINO-RUN.md) - DominoRun context manager
- [EVALUATORS.md](./EVALUATORS.md) - LLM-as-judge, custom evaluators
- [MULTI-AGENT-EXAMPLE.md](./MULTI-AGENT-EXAMPLE.md) - Complete multi-agent example

## Quick Start

### 1. Environment Setup

Requires MLflow 3.2.0 and Domino SDK with AI systems support:

```dockerfile
RUN pip install mlflow==3.2.0
RUN pip install --no-cache-dir "git+https://github.com/dominodatalab/python-domino.git@master#egg=dominodatalab[data,aisystems]"
```

### 2. Basic Tracing

```python
import mlflow
from domino.agents.tracing import add_tracing
from domino.agents.logging import DominoRun

@add_tracing(name="my_agent", autolog_frameworks=["openai"])
def my_agent(query: str) -> str:
    response = llm.invoke(query)
    return response

# Run with tracing
with DominoRun() as run:
    result = my_agent("What is machine learning?")
```

### 3. With Evaluators

```python
def quality_evaluator(inputs, output):
    """Evaluate response quality."""
    return {"quality_score": assess_quality(output)}

@add_tracing(name="my_agent", evaluator=quality_evaluator)
def my_agent(query: str) -> str:
    return llm.invoke(query)
```

## Framework Support

| Framework | Auto-log Command |
|-----------|------------------|
| OpenAI | `mlflow.openai.autolog()` |
| Anthropic | `mlflow.anthropic.autolog()` |
| LangChain | `mlflow.langchain.autolog()` |

## Viewing Traces

1. Navigate to **Experiments** in your Domino project
2. Select the experiment (format: `tracing-{username}`)
3. Select a run
4. View the **Traces** tab for span tree visualization

## Blueprint Reference

Official GenAI Tracing Tutorial:
https://github.com/dominodatalab/GenAI-Tracing-Tutorial

## Documentation Links

- Domino GenAI Tracing: https://docs.dominodatalab.com/en/cloud/user_guide/fc1922/set-up-and-run-genai-traces/
