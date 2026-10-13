# Domino Flows Basics

This guide covers the fundamentals of building workflows with Domino Flows.

> ⚠️ **Critical**: Domino Flows does NOT support native Flyte `@task` decorators.
> All tasks must use `DominoJobTask` + `DominoJobConfig` from `flytekitplugins.domino.task`,
> or the `run_domino_job_task` helper from `flytekitplugins.domino.helpers`.
> Only `@workflow` from `flytekit` is used unchanged.

## Task Definition

### Basic DominoJobTask

Each task runs as a Domino Job. The `Command` in `DominoJobConfig` specifies the script to run.
Inputs and outputs are passed via files at `/workflow/inputs/<name>` and `/workflow/outputs/<name>`,
where `<name>` is the key you choose in the `inputs=` / `outputs=` dicts.

```python
from typing import TypeVar
from flytekit import workflow
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

my_task = DominoJobTask(
    name="My Task Name",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/my_script.py'",
    ),
    inputs={"input_value": str},                         # type per named input
    outputs={"summary": str,                             # outputs are named by you
             "table": FlyteFile[TypeVar("csv")]},        # file outputs: FlyteFile with extension
    use_latest=True,                                     # resolve hardware/environment from project defaults
)
```

### Stage Script Pattern

Each task's script reads from `/workflow/inputs/<name>` and writes every declared output to
`/workflow/outputs/<name>`. The file name must exactly match the declared name (no extension added).

```python
# my_script.py
import json, os
import pandas as pd

INPUTS = "/workflow/inputs"
OUTPUTS = "/workflow/outputs"

def main():
    # Read inputs (primitives are plain text files; file inputs are the file itself)
    input_value = open(f"{INPUTS}/input_value").read().strip()

    # Do work
    df = pd.DataFrame({"processed": [input_value]})
    result = {"processed": input_value, "status": "done"}

    # Write every declared output under its exact name
    os.makedirs(OUTPUTS, exist_ok=True)
    with open(f"{OUTPUTS}/summary", "w") as f:
        f.write(json.dumps(result))
    df.to_csv(f"{OUTPUTS}/table", index=False)

if __name__ == "__main__":
    main()
```

> If any declared output is missing at the end of the Domino Job, the task fails.

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
from typing import TypeVar
from flytekit import workflow
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

ingest_task = DominoJobTask(
    name="Stage 1: Ingest",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/stage1.py'",
    ),
    inputs={"source_path": str},
    outputs={"raw_data": FlyteFile[TypeVar("parquet")]},
    use_latest=True,
)

train_task = DominoJobTask(
    name="Stage 2: Train",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/stage2.py'",
    ),
    inputs={"raw_data": FlyteFile[TypeVar("parquet")]},
    outputs={"metrics": str},
    use_latest=True,
)

@workflow
def my_pipeline(source_path: str = "/mnt/data/raw/raw.csv") -> str:
    """Connect tasks in a sequential DAG."""
    ingest_output = ingest_task(source_path=source_path)
    result = train_task(raw_data=ingest_output["raw_data"])
    return result["metrics"]
```

Index a task's result by output name (`ingest_output["raw_data"]`). Passing one task's output
into another's input is what creates the dependency edge.

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
    outputs={"ranking": str},
    use_latest=True,
)
```

In the stage script, read ints/floats as:
```python
n_top = int(open(f"{INPUTS}/n_top").read().strip())
threshold = float(open(f"{INPUTS}/threshold").read().strip())
```

### Helper: `run_domino_job_task`

The helper defines the config, task, inputs, and outputs in one call and runs it immediately.
Inputs are `Input(name=, type=, value=)`; outputs are `Output(name=, type=)`.

```python
from typing import TypeVar
from flytekit import workflow
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.helpers import Input, Output, run_domino_job_task

@workflow
def training_workflow(data_path: str) -> FlyteFile[TypeVar("pt")]:
    prep = run_domino_job_task(
        flyte_task_name="Prepare data",
        command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/prep.py'",
        inputs=[Input(name="data_path", type=str, value=data_path)],
        output_specs=[Output(name="processed_data", type=FlyteFile[TypeVar("csv")])],
        use_project_defaults_for_omitted=True,
    )
    train = run_domino_job_task(
        flyte_task_name="Train model",
        command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/train.py'",
        inputs=[Input(name="processed_data", type=FlyteFile[TypeVar("csv")], value=prep["processed_data"])],
        output_specs=[Output(name="model", type=FlyteFile[TypeVar("pt")])],
        use_project_defaults_for_omitted=True,
        hardware_tier_id="gpu-k8s",
    )
    return train["model"]
```

Helper keyword names mirror `DominoJobConfig` in snake_case: `environment_id`, `environment_name`,
`environment_revision_id`, `hardware_tier_id`, `hardware_tier_name`, `main_git_repo_ref`,
`imported_git_repo_overrides`, `dataset_snapshots`, `netapp_volume_snapshots`,
`external_data_volume_ids`, `volume_size_gib`, `cache`, `cache_version`,
`cache_ignore_input_vars`, `retries`, `timeout`, `job_title`.

## Supported Input/Output Types

| Type | Declared as | How it appears in `/workflow/inputs/<name>` |
|------|-------------|----------------------------------------------|
| Primitives | `str`, `bool`, `int`, `float`, `datetime` | Plain text (`"42"`, `"3.14"`, `"True"`) |
| Containers | `list`, `dict` | Serialized blob; needs Flyte-aware deserialization |
| Files | `FlyteFile[TypeVar("csv")]`, `FlyteFile[TypeVar("pdf")]`, ... | The file itself, readable directly |
| Data science | `pandas.DataFrame`, `np.ndarray`, `pyspark.DataFrame`, `torch.Tensor`, `torch.nn.Module`, `sklearn.base.BaseEstimator`, `tf.keras.Model` | Serialized blob; needs Flyte-aware deserialization |

Types drive validation before execution, caching keys, lineage, and file previews in the UI.
Declare the extension on `FlyteFile` (or use a Flow Artifact file) or the UI cannot render the file.

> **Best practice for plain scripts**: pass files as `FlyteFile[...]` outputs and pass small
> structured metadata as a JSON-encoded `str`. Both read back with ordinary file I/O and
> avoid Flyte-specific deserialization inside the stage script.

```python
# In stage script: serialize small metadata as a JSON string output
result = {"key": "value", "count": 42}
with open(f"{OUTPUTS}/summary", "w") as f:
    f.write(json.dumps(result))

# In next stage: deserialize
data = json.loads(open(f"{INPUTS}/summary").read())
```

## Data paths: `/workflow` vs `/mnt`

Flow tasks use the same data mount paths as a Workspace or standalone Job, so code written for a
Workspace runs unchanged inside a Flow task. Two kinds of paths exist in a task container:

| Path | Contents | Writable / persisted |
|------|----------|----------------------|
| `/workflow/inputs/<name>` | Declared inputs | Read |
| `/workflow/outputs/<name>` | Declared outputs; must exist when the job ends | Write; stored in Flow blob storage with lineage |
| `/mnt/data/<dataset>` | Local Dataset snapshot (Git-based project) | Read-only mount |
| `/mnt/imported/data/<dataset>` | Shared Dataset snapshot (Git-based project) | Read-only mount |
| `/mnt/netapp-volumes/<volume>` | NetApp Volume snapshot (Git-based project) | Read-only mount |
| `/domino/datasets/local/<name>`, `/domino/datasets/<name>`, `/domino/netapp-volumes/<name>` | Same, for DFS projects | Read-only mount |
| `/mnt/code`, `/mnt/artifacts` | Project code and results | **Not persisted**: Flow jobs make no commit or snapshot at job end |

Rules that follow from this:

- Snapshot mounts have no snapshot ID in the path. Code that reads `/mnt/data/my-dataset/file.csv`
  in a Workspace reads the pinned snapshot at the same path in a Flow task.
- Only Dataset and NetApp Volume **snapshots** can be mounted (not the read-write `version 0`).
  Take a snapshot first. One snapshot per Dataset/Volume per task; `use_latest=True` mounts the latest.
- Anything a downstream task needs, or that must survive the run, is a declared output.
  Writing to `/mnt/artifacts` or `/mnt/code` inside a Flow task does not persist and is not visible
  to other tasks (each task is its own pod).

### Declare `/mnt` paths as inputs and outputs

With the `Input`/`Output` helpers, `path=` lets a task read or write a file at its Workspace
location instead of `/workflow/...`. Files under `/mnt/data` or `/mnt/netapp-volumes` can be both
an input and an output: Domino populates them when the task starts and propagates them to
downstream tasks as outputs. Data written back to a data path can optionally become a new snapshot
at the end of the flow run.

```python
from typing import TypeVar
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.helpers import Input, Output, run_domino_job_task

clean = run_domino_job_task(
    flyte_task_name="Clean data",
    command="python /mnt/code/clean.py",   # reads and writes /mnt/data/numbers/... like a Workspace
    inputs=[
        Input(name="raw", type=FlyteFile[TypeVar("csv")], path="/mnt/data/numbers/raw.csv"),
        Input(name="n", type=int, value=13),
    ],
    output_specs=[
        Output(name="clean", type=FlyteFile[TypeVar("csv")], path="/mnt/data/numbers/clean.csv"),
    ],
    use_project_defaults_for_omitted=True,
)
```

Without `path=`, the default locations are `/workflow/inputs/<name>` and `/workflow/outputs/<name>`.

## Hardware and Environment Configuration

`use_latest=True` (or `use_project_defaults_for_omitted=True`) fetches the project's default
hardware tier, environment, and commit for anything you did not set. For production, set
`use_latest=False` and pin everything explicitly so a later change to project defaults cannot
change what a re-registered flow runs on.

```python
DominoJobConfig(
    Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/gpu_stage.py'",
    HardwareTierId="gpu-k8s",                     # ID, not display name
    EnvironmentId="698505e4701849448243f120",     # ID, not name or revision ID
)
```

### `DominoJobConfig` parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `Command` | str, required | Command run in the Job |
| `Title` | str | Job title; ignored for cache version |
| `CommitId` | str | DFS projects: code commit. Git-based projects: artifacts commit |
| `MainRepoGitRef` | `GitRef` | Branch/commit/tag of the main repo (Git-based only), e.g. `GitRef(Type="branches", Value="main")` |
| `ResolvedMainRepoGitRef` | str | Explicit resolved commit for a floating ref |
| `UseLatestGitRef` | bool, default `False` | `True`: floating refs in `MainRepoGitRef` and `ImportedGitRepoOverrides` re-resolve on every run and relaunch. `False`: resolved once on first run and reused on relaunch |
| `ImportedGitRepoOverrides` | `List[ImportedGitRepoOverride]` | Pin a ref per imported repo; `Name` must match an imported repo on the project |
| `HardwareTierId` | str | Hardware tier ID; ignored for cache version |
| `EnvironmentId` | str | Environment ID |
| `EnvironmentRevisionSpec` | `EnvironmentRevisionSpecification` | e.g. `EnvironmentRevisionSpecification(EnvironmentRevisionType.SomeRevision, "6659daf5fc8de")` |
| `ComputeClusterProperties` | `ClusterProperties` | On-demand Spark/Ray/Dask cluster for the task |
| `VolumeSizeGiB` | float | Disk size; ignored for cache version |
| `DatasetSnapshots` | `List[DatasetSnapshot]` | e.g. `[DatasetSnapshot(Id="6615af2820a4", Version=1)]`; version 0 is not allowed |
| `NetAppVolumeSnapshots` | `List[NetAppVolumeSnapshot]` | e.g. `[NetAppVolumeSnapshot(Id="5d1204c2-24c8", Version=1)]`; version 0 is not allowed |
| `ExternalVolumeMountIds` | `List[str]` | External data volume IDs |
| `cache_ignore_vars` | `Tuple[str, ...]` | Config args excluded from the cache version, e.g. `("EnvironmentId",)` |

### `DominoJobTask` parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `name` | str, required | Task name; part of the cache key |
| `domino_job_config` | `DominoJobConfig`, required | |
| `inputs`, `outputs` | `Dict[str, Type]` | Named, typed interface |
| `use_latest` | bool | Fill omitted settings from project defaults (dev only) |
| `cache` | `bool \| Cache`, default `False` | Enable result reuse |
| `cache_version` | str | Bump to invalidate when logic changes but signature does not |
| `cache_ignore_input_vars` | `Tuple[str, ...]` | Inputs excluded from the cache key |
| `retries` | int | Automatic retries for transient failures |
| `timeout` | `timedelta \| int` | Kill the task past this duration |

## Pin Git references per task

Flow tasks in Git-based projects can pin the main repository and any imported repository to a
branch, commit, or tag. This is how a task pulls code from more than one repository, and how a
relaunch is kept on exactly the code that ran before.

```python
from flytekitplugins.domino.task import (
    DominoJobConfig, DominoJobTask, GitRef, ImportedGitRepoOverride,
)

training_job_config = DominoJobConfig(
    Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/stages/train.py'",
    MainRepoGitRef=GitRef(Type="branches", Value="main"),
    ImportedGitRepoOverrides=[
        ImportedGitRepoOverride(
            Name="shared-utils",                                      # imported repo name on the project
            Ref=GitRef(Type="commitId", Value="2f1cb9bf696921f0858"),
        ),
    ],
    UseLatestGitRef=False,   # resolve "main" once; relaunches reuse that commit
)
```

- `GitRef(Type=..., Value=...)` accepts the same reference types as Jobs
  (`GitRef` schema in the public API): `head`, `branches`, `commitId`, `tags`, `custom`.
- The resolved commits of every Git input are part of the task's cache version, so a new commit
  on a floating ref with `UseLatestGitRef=True` is a cache miss.
- The `run_domino_job_task` helper takes `main_git_repo_ref=` and `imported_git_repo_overrides=`.
- When a Git override is applied at rerun time, the files the task reads as inputs must exist at
  the new ref.

## Triggering and Monitoring

### Run Remotely

```bash
# Trigger flow execution; the flow is serialized, registered as a new version, and started
PYTHONPATH=/mnt/code pyflyte run --remote \
    app/flow/my_flow.py my_pipeline \
    --source_path "/mnt/data/raw/raw.csv"

# Optional: fixed run name (must be unique across all flows in the project) and tags
PYTHONPATH=/mnt/code pyflyte run --remote --name nightly-2026-10-13 --tag team=ml \
    app/flow/my_flow.py my_pipeline --source_path "/mnt/data/raw/raw.csv"
```

Any change to the flow definition file produces a new flow version at the next `pyflyte run`.
Registered flows are stored serialized; commit the source so the definition is not lost.

### Rerun, recover, and override from the UI

Once a flow has run once, you can relaunch it without touching code:

1. **Flows > flow > version > run > Re-run**. Name the run and choose whether to overwrite cache.
2. Reuse the previous inputs or enter new input values.
3. **Override task-specific settings** per task: Compute Environment, Hardware Tier, or Git
   reference for the task code. Each task can carry its own override. The same overrides are
   available from the UI, API, and CLI.
4. **Recover**: if a run failed for a transient reason (timeout, capacity, spot preemption,
   internal error), click **Recover** on the run to resume from the failed node, reusing the
   outputs already produced. For a code bug, fix the code and `pyflyte run` again instead.
5. **Rerun Node**: rerun a single node with different inputs from the execution view.

UI relaunch only works while the registered definition is unchanged; a changed `workflow.py`
must go through `pyflyte run --remote` to register a new version. On relaunch, floating Git
refs follow the task's `UseLatestGitRef` setting.

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

The Domino UI (**Flows > flow > run > Nodes/Graph**) shows per-node inputs, outputs, logs, and a
link to the underlying Domino Job. The native Flyte console is served from the Domino host at
`/flows/console/select-project` for timeline views and blob URIs.

## Common Pitfalls

### 1. DatasetSnapshots — Verify Version Before Use

`DominoJobConfig.DatasetSnapshots` lets you mount Domino Datasets, but the `Version`
must match an existing snapshot or Domino will return a 500 error at job creation time.
`resolveJobDefaults` echoes back whatever version you provide without validation.
Version 0 (the read-write directory) is never accepted; take a snapshot first.

The mounted snapshot appears at the Workspace path (`/mnt/data/<dataset>`), so stage code can
read it exactly as it does in a Workspace. If you cannot guarantee a snapshot exists, add a
fallback in the stage:

```python
# In each stage script — self-healing data loading
try:
    df = load_features()           # Try reading from the mounted snapshot
except FileNotFoundError:
    df = prepare_dataset()         # Generate from raw files if absent
```

### 2. resolveJobDefaults Overwrites DatasetSnapshots

When `use_latest=True`, `resolve_job_properties()` calls `resolveJobDefaults` which
**unconditionally overwrites** `DatasetSnapshots` with what the API returns.
If the project has no default datasets, `DatasetSnapshots` becomes `[]` regardless of
what you set — unless the API returns your dataset back (which only happens if the version
is valid).

### 3. Code Version Is Resolved at Registration or First Run

With `use_latest=True` and no `MainRepoGitRef`, `resolveJobDefaults` returns the latest synced
commit from the project's linked repo. Always commit and push before triggering a flow — the job
runs against the **remote repo state**, not local files. There may be a sync delay of seconds to
minutes between pushing and Domino's internal git mirror updating.

To control this explicitly, set `MainRepoGitRef` (and `ImportedGitRepoOverrides` for secondary
repos) and choose `UseLatestGitRef`: `False` pins the commit resolved on the first run for every
relaunch; `True` re-resolves the branch or tag each time.

### 4. Writes Outside `/workflow/outputs` Do Not Persist

Flow jobs do not commit code or snapshot `/mnt/artifacts` when they finish, and each task runs in
its own pod. A file written to `/mnt/artifacts/model.pkl` in one task is gone for the next task.
Declare it as a `FlyteFile` output (or an `Output(path="/mnt/data/...")`) instead.

### 5. No `@task` Decorator

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
    outputs={"upper": str},
    use_latest=True,
)
```

### 6. Not Yet Supported Flyte Features

Dynamic workflows and map tasks are not available in Domino Flows. Model fan-out with
explicitly declared tasks or subflows.
