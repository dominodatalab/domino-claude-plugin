# DominoRun Context Manager Guide

The `DominoRun` context manager groups traces into runs, enabling aggregation, configuration tracking, and organized experiment viewing.

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

### Progress Tracking

```python
from tqdm import tqdm
from domino.agents.logging import DominoRun

with DominoRun(run_name="full-evaluation") as run:
    for item in tqdm(test_data, desc="Processing"):
        result = my_agent(item)
```

## Accessing Run Information

### During Run

```python
with DominoRun() as run:
    # Access run ID
    print(f"Run ID: {run.run_id}")

    # Access experiment info
    print(f"Experiment: {run.experiment_id}")

    result = my_agent(query)
```

### After Run

```python
import mlflow

# Get run by ID
run = mlflow.get_run(run_id)

# Access metrics
print(run.data.metrics)

# Access parameters (from config.yaml)
print(run.data.params)

# Access artifacts
artifacts = mlflow.artifacts.list_artifacts(run_id)
```

## Multiple Runs Comparison

### Sequential Runs

```python
run_ids = []

for config_version in ["v1", "v2", "v3"]:
    with DominoRun(run_name=f"config-{config_version}") as run:
        for item in test_data:
            result = my_agent(item, config=config_version)
        run_ids.append(run.run_id)

# Compare runs
import mlflow
runs = mlflow.search_runs(run_ids=run_ids)
print(runs[["run_id", "metrics.accuracy_mean"]])
```

### A/B Testing Pattern

```python
from domino.agents.logging import DominoRun

def run_ab_test(test_data, model_a, model_b):
    results = {}

    # Test Model A
    with DominoRun(run_name=f"ab-test-model-a") as run_a:
        for item in test_data:
            result = agent_with_model(item, model_a)
        results["model_a"] = run_a.run_id

    # Test Model B
    with DominoRun(run_name=f"ab-test-model-b") as run_b:
        for item in test_data:
            result = agent_with_model(item, model_b)
        results["model_b"] = run_b.run_id

    return results
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

### Run-Level Error Tracking

```python
from domino.agents.logging import DominoRun
import mlflow

with DominoRun() as run:
    error_count = 0
    for item in data:
        try:
            result = my_agent(item)
        except Exception as e:
            error_count += 1

    # Log run-level metric
    mlflow.log_metric("total_errors", error_count)
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

### 2. Match Aggregation to Evaluator Metrics

```python
# Evaluator returns these metrics
def evaluator(inputs, output):
    return {
        "accuracy": 0.9,
        "latency_ms": 150,
    }

# Aggregations should match
aggregated_metrics = [
    ("accuracy", "mean"),      # Matches "accuracy"
    ("latency_ms", "mean"),    # Matches "latency_ms"
]
```

### 3. Use Config Files for Reproducibility

```python
# Always log configuration
with DominoRun(agent_config_path="config.yaml") as run:
    pass

# Now you can reproduce any run by checking its parameters
```

### 4. Keep Runs Focused

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
