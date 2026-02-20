---
name: domino-flows
description: Orchestrate multi-step ML workflows using Domino Flows (built on Flyte). Define DAGs with typed inputs/outputs, heterogeneous environments, automatic lineage, and reproducibility. Use when building data pipelines, multi-stage training workflows, or processes requiring orchestration and monitoring.
---

# Domino Flows Skill

This skill provides comprehensive knowledge for orchestrating ML workflows using Domino Flows, built on the Flyte platform.

## Key Concepts

### What are Domino Flows?

Domino Flows enable:
- **DAG-based orchestration**: Define workflows as directed acyclic graphs
- **Typed interfaces**: Strong typing for inputs and outputs
- **Heterogeneous environments**: Different environments per task
- **Automatic lineage**: Track data and model provenance
- **Reproducibility**: Version-controlled workflows
- **Scalability**: Distributed execution across compute resources

### Core Components

| Component | Description |
|-----------|-------------|
| **Task** | Single unit of work (runs as a Domino Job) |
| **Workflow** | DAG connecting tasks |
| **Artifact** | Typed input/output passed between tasks |
| **Launch Plan** | Configured workflow execution |

## Related Documentation

- [FLOW-BASICS.md](./FLOW-BASICS.md) - DAG concepts, task definitions
- [EXAMPLES.md](./EXAMPLES.md) - Common flow patterns

## Quick Start

### Basic Flow

```python
from flytekit import task, workflow

@task
def preprocess_data(input_path: str) -> str:
    """Task 1: Data preprocessing"""
    # Processing logic
    output_path = "/mnt/data/processed.parquet"
    return output_path

@task
def train_model(data_path: str) -> str:
    """Task 2: Model training"""
    # Training logic
    model_path = "/mnt/artifacts/model.pkl"
    return model_path

@workflow
def training_pipeline(input_path: str) -> str:
    """Workflow connecting tasks"""
    processed = preprocess_data(input_path=input_path)
    model = train_model(data_path=processed)
    return model
```

### Running the Flow

```python
# Local execution
result = training_pipeline(input_path="/data/raw.csv")

# Submit to Domino
# Use Domino UI or CLI to trigger the flow
```

## When to Use Flows

### Good Use Cases

- Data processing → Model training pipelines
- ETL with ML steps
- Multi-stage training with different environments
- Processes requiring reproducibility and lineage
- Scheduled/triggered workflows

### Not Ideal For

- Single dataset with many small computations
- Tasks that write to mutable shared state
- Simple single-step processes
- Real-time inference (use Model APIs instead)

## Documentation Links

- Domino Flows: https://docs.dominodatalab.com/en/latest/user_guide/78acf5/orchestrate-with-flows/
- Flyte Documentation: https://docs.flyte.org/
