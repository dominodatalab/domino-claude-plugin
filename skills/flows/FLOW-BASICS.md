# Domino Flows Basics

This guide covers the fundamentals of building workflows with Domino Flows.

> ⚠️ **Critical**: Domino Flows does NOT support native Flyte `@task` decorators.
> All tasks must use `DominoJobTask` + `DominoJobConfig` from `flytekitplugins.domino.task`.
> Only `@workflow` from `flytekit` is used unchanged.

## Task Definition

### Basic DominoJobTask

Each task runs as a Domino Job. The `Command` in `DominoJobConfig` specifies the script to run.
Inputs and outputs are passed via files at `/workflow/inputs/<name>` and `/workflow/outputs/<name>`.

```python
from flytekit import workflow
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

my_task = DominoJobTask(
    name="My Task Name",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/my_script.py'",
    ),
    inputs={"input_value": str},   # type hints for each input
    outputs={"o0": str},           # outputs named o0, o1, etc.
    use_latest=True,               # resolve hardware/environment from project defaults
)
```

### Stage Script Pattern

Each task's script reads from `/workflow/inputs/<name>` and writes to `/workflow/outputs/o0`:

```python
# my_script.py
import json, os

INPUTS = "/workflow/inputs"
OUTPUTS = "/workflow/outputs"

def main():
    # Read inputs (each input is a plain text file)
    input_value = open(f"{INPUTS}/input_value").read().strip()

    # Do work
    result = {"processed": input_value, "status": "done"}

    # Write output (always named o0, o1, etc.)
    os.makedirs(OUTPUTS, exist_ok=True)
    with open(f"{OUTPUTS}/o0", "w") as f:
        f.write(json.dumps(result))

if __name__ == "__main__":
    main()
```

### PYTHONPATH Requirement

Domino Jobs do not inherit the workspace Python path. Always set `PYTHONPATH` explicitly:

```python
# ✅ Correct: Set PYTHONPATH so app imports work
Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/app/stages/my_stage.py'"

# ❌ Wrong: Module 'app' not found
Command="python /mnt/code/app/stages/my_stage.py"
```

## Workflow Definition

### Basic Sequential Workflow

```python
from flytekit import workflow
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

ingest_task = DominoJobTask(
    name="Stage 1: Ingest",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/stage1.py'",
    ),
    inputs={"source_path": str},
    outputs={"o0": str},
    use_latest=True,
)

train_task = DominoJobTask(
    name="Stage 2: Train",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/stage2.py'",
    ),
    inputs={"ingest_output": str},
    outputs={"o0": str},
    use_latest=True,
)

@workflow
def my_pipeline(source_path: str = "/mnt/data/raw") -> str:
    """Connect tasks in a sequential DAG."""
    ingest_output = ingest_task(source_path=source_path)
    result = train_task(ingest_output=ingest_output)
    return result
```

### Multiple Inputs

```python
multi_input_task = DominoJobTask(
    name="Multi Input Task",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/multi.py'",
    ),
    inputs={
        "dataset_version": str,
        "component_id": str,
        "n_top": int,           # int inputs are written as plain text: "2"
        "threshold": float,     # float inputs: "0.95"
    },
    outputs={"o0": str},
    use_latest=True,
)
```

In the stage script, read ints/floats as:
```python
n_top = int(open(f"{INPUTS}/n_top").read().strip())
threshold = float(open(f"{INPUTS}/threshold").read().strip())
```

## Supported Input/Output Types

Domino Flows passes all data between stages as serialized text files:

| Python Type | How it appears in `/workflow/inputs/<name>` |
|-------------|----------------------------------------------|
| `str` | Plain text |
| `int` | "42" |
| `float` | "3.14" |
| `bool` | "True" or "False" |

> **Best practice**: Use `str` for complex data by JSON-serializing dicts/lists.
> This avoids type conversion issues and works reliably across all stages.

```python
# In stage script: serialize output as JSON string
result = {"key": "value", "count": 42}
with open(f"{OUTPUTS}/o0", "w") as f:
    f.write(json.dumps(result))

# In next stage: deserialize
data = json.loads(open(f"{INPUTS}/prev_output").read())
```

## Hardware and Environment Configuration

`use_latest=True` calls `resolveJobDefaults` to fetch the project's default hardware tier,
environment, and commit ID. To override, set fields explicitly on `DominoJobConfig`:

```python
DominoJobConfig(
    Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/gpu_stage.py'",
    HardwareTierId="gpu-k8s",           # Override hardware tier
    EnvironmentId="698505e4701849448243f120",  # Override environment
)
```

## Triggering and Monitoring

### Run Remotely

```bash
# Trigger flow execution
PYTHONPATH=/mnt/code pyflyte run --remote \
    app/flow/my_flow.py my_pipeline \
    --source_path "/mnt/data/raw"
```

### Monitor Status

```python
from flytekit.remote import FlyteRemote
from flytekit.configuration import Config

# Use Config.auto() — reads ~/.flyte/config.yaml (endpoint: 127.0.0.1:8181)
remote = FlyteRemote(
    config=Config.auto(),
    default_project="<project-id>",
    default_domain="development",    # pyflyte run --remote uses "development"
)

PHASES = {0:"UNDEFINED",1:"QUEUED",2:"RUNNING",3:"SUCCEEDING",4:"SUCCEEDED",
          5:"FAILING",6:"FAILED",7:"ABORTED",8:"TIMED_OUT"}

execution = remote.fetch_execution(name="my-execution-name")
remote.sync(execution, sync_nodes=True)
print(f"Phase: {PHASES[execution.closure.phase]}")
for node_id, node_exec in sorted(execution.node_executions.items()):
    print(f"  {node_id}: {PHASES[node_exec.closure.phase]}")
```

### Get Error Details

```python
for node_id, node_exec in execution.node_executions.items():
    for te in (node_exec.task_executions or []):
        full_te = remote.client.get_task_execution(te.id)
        if full_te.closure.error:
            print(full_te.closure.error.message)
```

## Common Pitfalls

### 1. DatasetSnapshots — Verify Version Before Use

`DominoJobConfig.DatasetSnapshots` lets you mount Domino Datasets, but the `snapshotVersion`
must match an existing snapshot or Domino will return a 500 error at job creation time.
`resolveJobDefaults` echoes back whatever version you provide without validation.

**Safest approach**: Don't specify `DatasetSnapshots`. Instead, add a fallback in each stage:

```python
# In each stage script — self-healing data loading
try:
    df = load_features()           # Try reading from mounted/cached parquet
except FileNotFoundError:
    df = prepare_dataset()         # Generate from raw files if absent
```

### 2. resolveJobDefaults Overwrites DatasetSnapshots

When `use_latest=True`, `resolve_job_properties()` calls `resolveJobDefaults` which
**unconditionally overwrites** `DatasetSnapshots` with what the API returns.
If the project has no default datasets, `DatasetSnapshots` becomes `[]` regardless of
what you set — unless the API returns your dataset back (which only happens if the version
is valid).

### 3. CommitId Is Pinned at Registration Time

`resolveJobDefaults` returns the latest synced commit ID from the project's linked repo.
Always commit and push before triggering a flow — the job runs against the **remote repo state**,
not local files. There may be a sync delay of seconds to minutes between pushing to GitHub
and Domino's internal git mirror updating.

### 4. No `@task` Decorator

```python
# ❌ This will NOT work in Domino Flows
from flytekit import task

@task
def my_task(x: str) -> str:
    return x.upper()

# ✅ This is the correct pattern
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

my_task = DominoJobTask(
    name="My Task",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/my_script.py'",
    ),
    inputs={"x": str},
    outputs={"o0": str},
    use_latest=True,
)
```
