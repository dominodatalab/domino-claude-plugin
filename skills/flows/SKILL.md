---
name: domino-flows
description: Orchestrate multi-step ML workflows using Domino Flows (built on Flyte). Define DAGs with typed inputs/outputs, heterogeneous environments, automatic lineage, and reproducibility. Use when building data pipelines, multi-stage training workflows, or processes requiring orchestration and monitoring.
compatibility: Domino 6.3 and Domino Cloud. Requires a Workspace or Job on the Domino Standard Environment (DSE) 6.0 or later, or an environment built on it, for the flytekit Domino plugin and pyflyte CLI.
---

# Domino Flows Skill

Applies to Domino 6.3 and Domino Cloud.

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
| **Flow** | DAG connecting tasks; declared with `@workflow`. A flow can nest other flows (subflows) |
| **Node** | One executing unit in a run: a task or a subflow |
| **Task inputs/outputs** | Typed, named values passed between tasks via `/workflow/inputs/<name>` and `/workflow/outputs/<name>`; stored in Flow blob storage with lineage |
| **Flow Artifact** | A task output elevated as `DATA`, `MODEL`, or `REPORT` for discovery, preview, and export to Datasets or NetApp Volumes |

## Related Documentation

- [FLOW-BASICS.md](./FLOW-BASICS.md) - DAG concepts, task definitions, data paths, Git refs, reruns
- [FLOW-ARTIFACTS.md](./FLOW-ARTIFACTS.md) - Flow Artifacts and programmatic export
- [EXAMPLES.md](./EXAMPLES.md) - Common flow patterns

## Quick Start

> ⚠️ **Critical**: Domino Flows does NOT support native Flyte `@task` decorators.
> Tasks must use `DominoJobTask` + `DominoJobConfig` (or the `run_domino_job_task` helper). Only `@workflow` is unchanged.

### Basic Flow

Each task runs as a Domino Job. Stage scripts read from `/workflow/inputs/<name>`
and write to `/workflow/outputs/<name>`, where `<name>` exactly matches the key you
declare in `inputs=` / `outputs=`. Pass `PYTHONPATH=/mnt/code` in the command.

```python
from typing import TypeVar
from flytekit import workflow
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

preprocess_task = DominoJobTask(
    name="Preprocess Data",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/preprocess.py'",
    ),
    inputs={"input_path": str},
    outputs={"processed_data": FlyteFile[TypeVar("parquet")]},
    use_latest=True,
)

train_task = DominoJobTask(
    name="Train Model",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/train.py'",
    ),
    inputs={"processed_data": FlyteFile[TypeVar("parquet")]},
    outputs={"metrics": str},
    use_latest=True,
)

@workflow
def training_pipeline(input_path: str = "/mnt/data/raw/raw.csv") -> str:
    preprocess_output = preprocess_task(input_path=input_path)
    result = train_task(processed_data=preprocess_output["processed_data"])
    return result["metrics"]
```

### Stage Script Pattern

```python
# stages/preprocess.py
import os
import pandas as pd

INPUTS, OUTPUTS = "/workflow/inputs", "/workflow/outputs"

def main():
    input_path = open(f"{INPUTS}/input_path").read().strip()   # str input: plain text
    df = pd.read_csv(input_path)
    # ... do work ...
    os.makedirs(OUTPUTS, exist_ok=True)
    df.to_parquet(f"{OUTPUTS}/processed_data", index=False)     # FlyteFile output: write the file itself

if __name__ == "__main__":
    main()
```

### Where data lives in a Flow task

| Path | What it is | Persisted? |
|------|------------|------------|
| `/workflow/inputs/<name>`, `/workflow/outputs/<name>` | Declared task inputs/outputs | Yes, Flow blob storage with lineage |
| `/mnt/data/<dataset>`, `/mnt/imported/data/<dataset>`, `/mnt/netapp-volumes/<volume>` | Dataset / NetApp Volume **snapshots**, mounted read-only at the same path a Workspace uses (Git-based projects) | Read-only; writes persist only when declared as an `Output(path=...)` |
| `/mnt/code`, `/mnt/artifacts` | Project code and results directories | **No.** Flow jobs do not commit or snapshot at the end of the job |

Anything a downstream task needs must be a declared output. See [Data paths](./FLOW-BASICS.md#data-paths-workflow-vs-mnt).

### Running the Flow

```bash
# Always commit and push first — jobs run against remote repo state
git add -A && git commit -m "..." && git push

# Trigger remotely (registers a new flow version automatically)
PYTHONPATH=/mnt/code pyflyte run --remote \
    --name my-run-001 \
    my_flow.py training_pipeline \
    --input_path "/mnt/data/raw/raw.csv"
```

After the first run, rerun from **Flows > flow > version > run > Re-run** in the UI with new
inputs and per-task overrides (environment, hardware tier, Git ref) without editing code.
See [Rerun, recover, and override](./FLOW-BASICS.md#rerun-recover-and-override-from-the-ui).

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

- Orchestrate with Flows (Cloud): https://docs.domino.ai/cloud/platform-capabilities/features/flows
- Orchestrate with Flows (6.3): https://docs.domino.ai/6.3/platform-capabilities/features/flows
- Define Flows: https://docs.domino.ai/cloud/platform-capabilities/features/flows/define-flows
- Define Flow Artifacts: https://docs.domino.ai/cloud/platform-capabilities/features/flows/define-flow-artifacts
- Launch Flows: https://docs.domino.ai/cloud/platform-capabilities/features/flows/launch-flows
- Flyte Documentation: https://docs.flyte.org/
