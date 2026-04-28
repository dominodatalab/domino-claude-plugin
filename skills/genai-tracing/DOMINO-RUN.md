# DominoRun Context Manager Guide

The `DominoRun` context manager groups traces into runs, enabling aggregation, configuration tracking, and organized experiment viewing.

## When to Use DominoRun (and When NOT To)

| Context | Use DominoRun? | Why |
|---------|---------------|-----|
| Batch evaluation scripts | Yes | Groups traces into a named run in Experiments UI |
| Domino Jobs | Yes | Run-level aggregation and config tracking |
| **Deployed Domino Apps** | **No** | `DominoRun` overrides Domino's auto-routing. Traces go to a custom experiment instead of `agent_experiment_{app_id}`, and the **App Performance tab won't see them**. |
| Workspaces (interactive) | Optional | Useful for development, but not required |

**For deployed Apps:** Let `@add_tracing` create traces directly (no `DominoRun` wrapper, no `mlflow.set_experiment()`). Domino auto-routes traces to the app's `agent_experiment_{app_id}` experiment, which the Performance tab reads from.

```python
# DEPLOYED APP — do NOT use DominoRun
@router.post("/chat")
async def chat(request: ChatRequest):
    return await run_agent_turn(request)  # @add_tracing handles tracing

# BATCH EVALUATION — use DominoRun
with DominoRun(run_name="evaluation-batch") as run:
    for item in test_data:
        result = run_agent_turn(item)
```

## Basic Usage

### Simple Run

```python
from domino.agents.logging import DominoRun

with DominoRun() as run:
    result = my_traced_function(input_data)
    print(f"Run ID: {run.run_id}")
```

### With Run Name

```python
with DominoRun(run_name="production-evaluation-2024") as run:
    for item in test_data:
        result = my_agent(item)
```

### Resilient Wrapper Pattern

In production code, wrap `DominoRun` to tolerate import failures and broken MLflow state:

```python
from contextlib import contextmanager

try:
    from domino.agents.logging import DominoRun as _DominoRun
    _HAS_DOMINO_SDK = True
except ImportError:
    _HAS_DOMINO_SDK = False
    _DominoRun = None

@contextmanager
def DominoRun():
    """DominoRun that tolerates broken MLflow tracking state."""
    if _DominoRun is None:
        yield None
        return
    try:
        with _DominoRun() as run:
            yield run
    except Exception:
        yield None
```

## Configuration File

### Loading Agent Configuration

Use `agent_config_path` to log configuration as MLflow parameters:

```python
from domino.agents.logging import DominoRun

with DominoRun(agent_config_path="config.yaml") as run:
    result = my_agent(query)
```

### config.yaml Example

```yaml
# Agent configuration
models:
  primary: gpt-4o-mini
  fallback: gpt-3.5-turbo
  judge: gpt-4o

agents:
  classifier:
    temperature: 0.3
    max_tokens: 500
    system_prompt: "You are a classifier..."

  responder:
    temperature: 0.7
    max_tokens: 1500
    system_prompt: "You are a helpful assistant..."

  evaluator:
    temperature: 0.1
    max_tokens: 100

settings:
  retry_count: 3
  timeout_seconds: 30
  batch_size: 10
```

### Accessing Configuration in Code

```python
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

classifier_temp = config["agents"]["classifier"]["temperature"]
```

## Aggregated Metrics

### Defining Summary Metrics

Use `custom_summary_metrics` to aggregate metrics across all traces in a run:

```python
from domino.agents.logging import DominoRun

aggregated_metrics = [
    ("classification_confidence", "mean"),
    ("impact_score", "median"),
    ("response_quality", "stdev"),
    ("processing_time", "max"),
    ("token_count", "min"),
]

with DominoRun(
    agent_config_path="config.yaml",
    custom_summary_metrics=aggregated_metrics
) as run:
    for item in batch:
        result = triage_incident(item)
```

### Aggregation Types

| Type | Description |
|------|-------------|
| `mean` | Average of all values |
| `median` | Middle value (50th percentile) |
| `stdev` | Standard deviation |
| `min` | Minimum value |
| `max` | Maximum value |

### How Aggregation Works

1. Each traced function logs individual metrics via evaluators
2. At run end, `DominoRun` aggregates metrics across all traces
3. Aggregated metrics appear in the run's metrics in Domino UI

Example:
```python
# If these traces occurred:
# Trace 1: response_quality = 0.8
# Trace 2: response_quality = 0.9
# Trace 3: response_quality = 0.85

# With aggregation: ("response_quality", "mean")
# Run metric: response_quality_mean = 0.85
```

## Complete Example with All Features

```python
import mlflow
from domino.agents.tracing import add_tracing
from domino.agents.logging import DominoRun
from openai import OpenAI

mlflow.openai.autolog()
client = OpenAI()

def quality_evaluator(inputs, output):
    return {
        "response_length": len(output.get("response", "")),
        "confidence": output.get("confidence", 0),
    }

@add_tracing(name="qa_agent", evaluator=quality_evaluator)
def qa_agent(question: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}]
    )
    return {
        "response": response.choices[0].message.content,
        "confidence": 0.9,
    }

# Define aggregations
aggregated_metrics = [
    ("response_length", "mean"),
    ("response_length", "max"),
    ("confidence", "mean"),
    ("confidence", "min"),
]

# Run with full configuration
with DominoRun(
    run_name="qa-evaluation-batch",
    agent_config_path="config.yaml",
    custom_summary_metrics=aggregated_metrics
) as run:
    questions = [
        "What is machine learning?",
        "How do neural networks work?",
        "What is deep learning?",
    ]

    for question in questions:
        result = qa_agent(question)
        print(f"Q: {question}")
        print(f"A: {result['response'][:100]}...")

    print(f"\nRun ID: {run.run_id}")
```

## Batch Processing Pattern

### Processing Large Datasets

```python
from domino.agents.logging import DominoRun

def process_batch(items, batch_name):
    aggregated_metrics = [
        ("accuracy", "mean"),
        ("latency", "mean"),
        ("error_count", "max"),
    ]

    with DominoRun(
        run_name=f"batch-{batch_name}",
        custom_summary_metrics=aggregated_metrics
    ) as run:
        results = []
        for item in items:
            try:
                result = process_item(item)
                results.append(result)
            except Exception as e:
                print(f"Error processing {item}: {e}")
        return results

# Process multiple batches
for i, batch in enumerate(batches):
    results = process_batch(batch, f"batch-{i}")
```

## Error Handling

### Graceful Error Handling

```python
from domino.agents.logging import DominoRun

with DominoRun() as run:
    for item in data:
        try:
            result = my_agent(item)
        except Exception as e:
            # Error is logged in trace
            print(f"Error: {e}")
            continue  # Continue with next item
```

## Best Practices

### 1. Use Descriptive Run Names

```python
# Good
with DominoRun(run_name="customer-support-eval-2024-01-15"):
with DominoRun(run_name="model-comparison-gpt4-vs-claude"):

# Bad
with DominoRun(run_name="test"):
with DominoRun():  # No name at all
```

### 2. Don't Use DominoRun in Deployed Apps

```python
# BAD — traces won't appear in App Performance tab
@router.post("/chat")
async def chat(request):
    with DominoRun():  # Don't do this in a deployed app
        return await run_agent(request)

# GOOD — @add_tracing handles tracing, Domino auto-routes to Performance tab
@router.post("/chat")
async def chat(request):
    return await run_agent(request)  # run_agent has @add_tracing
```

### 3. Don't Call mlflow.set_experiment() in Deployed Apps

```python
# BAD — overrides Domino's auto-routing
@asynccontextmanager
async def lifespan(app):
    mlflow.set_experiment("my-custom-experiment")  # Don't do this
    yield

# GOOD — just enable autolog, let Domino handle experiment routing
@asynccontextmanager
async def lifespan(app):
    try:
        mlflow.openai.autolog()
    except Exception:
        pass
    try:
        mlflow.anthropic.autolog()
    except Exception:
        pass
    yield
```

### 4. Keep Runs Focused (Evaluation Mode)

```python
# Good: One run per evaluation type
with DominoRun(run_name="accuracy-evaluation"):
    evaluate_accuracy(data)

with DominoRun(run_name="latency-evaluation"):
    evaluate_latency(data)

# Bad: Everything in one run
with DominoRun():
    evaluate_accuracy(data)
    evaluate_latency(data)
    do_other_stuff()
```

## Next Steps

- [EVALUATORS.md](./EVALUATORS.md) - Create custom evaluators
- [MULTI-AGENT-EXAMPLE.md](./MULTI-AGENT-EXAMPLE.md) - Complete example
