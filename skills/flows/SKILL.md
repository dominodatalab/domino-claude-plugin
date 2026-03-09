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

> ⚠️ **Critical**: Domino Flows does NOT support native Flyte `@task` decorators.
> Tasks must use `DominoJobTask` + `DominoJobConfig`. Only `@workflow` is unchanged.

### Basic Flow

Each task runs as a Domino Job. Stage scripts read from `/workflow/inputs/<name>`
and write to `/workflow/outputs/o0`. Pass `PYTHONPATH=/mnt/code` in the command.

```python
from flytekit import workflow
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

preprocess_task = DominoJobTask(
    name="Preprocess Data",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/preprocess.py'",
    ),
    inputs={"input_path": str},
    outputs={"o0": str},
    use_latest=True,
)

train_task = DominoJobTask(
    name="Train Model",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/train.py'",
    ),
    inputs={"preprocess_output": str},
    outputs={"o0": str},
    use_latest=True,
)

@workflow
def training_pipeline(input_path: str = "/mnt/data/raw.csv") -> str:
    preprocess_output = preprocess_task(input_path=input_path)
    result = train_task(preprocess_output=preprocess_output)
    return result
```

### Stage Script Pattern

```python
# stages/preprocess.py
import json, os

INPUTS, OUTPUTS = "/workflow/inputs", "/workflow/outputs"

def main():
    input_path = open(f"{INPUTS}/input_path").read().strip()
    # ... do work ...
    os.makedirs(OUTPUTS, exist_ok=True)
    with open(f"{OUTPUTS}/o0", "w") as f:
        f.write(json.dumps({"output_path": "/mnt/artifacts/processed.parquet"}))

if __name__ == "__main__":
    main()
```

### Running the Flow

```bash
# Always commit and push first — jobs run against remote repo state
git add -A && git commit -m "..." && git push

# Trigger remotely
PYTHONPATH=/mnt/code pyflyte run --remote \
    my_flow.py training_pipeline \
    --input_path "/mnt/data/raw.csv"
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
