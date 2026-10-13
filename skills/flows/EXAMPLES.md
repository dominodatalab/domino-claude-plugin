# Domino Flows Examples

Complete, production-ready flow examples for Domino Flows.

> ⚠️ **Critical**: Use `DominoJobTask` + `DominoJobConfig` (or `run_domino_job_task`). Native `@task` decorators are NOT supported.

Conventions used throughout:

- A task's declared output `name` is the file it must write at `/workflow/outputs/<name>`.
- Files move between tasks as `FlyteFile[TypeVar("<ext>")]` outputs; small metadata moves as a JSON-encoded `str`.
- Nothing written to `/mnt/artifacts` or `/mnt/code` survives a Flow task. See [Data Sharing Between Stages](#data-sharing-between-stages).

## Example 1: Data Processing Pipeline

### Flow Definition (`flows/data_pipeline.py`)

```python
from typing import TypeVar
from flytekit import workflow
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

load_task = DominoJobTask(
    name="Load Data",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/load.py'",
    ),
    inputs={"source_path": str, "dataset_version": str},
    outputs={"loaded": FlyteFile[TypeVar("parquet")], "load_stats": str},
    use_latest=True,
)

clean_task = DominoJobTask(
    name="Clean Data",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/clean.py'",
    ),
    inputs={"loaded": FlyteFile[TypeVar("parquet")]},
    outputs={"cleaned": FlyteFile[TypeVar("parquet")]},
    use_latest=True,
)

feature_task = DominoJobTask(
    name="Create Features",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/features.py'",
    ),
    inputs={"cleaned": FlyteFile[TypeVar("parquet")]},
    outputs={"features": FlyteFile[TypeVar("parquet")]},
    use_latest=True,
)

@workflow
def data_pipeline(
    source_path: str = "/mnt/data/raw/raw.csv",   # a Dataset snapshot, mounted at its Workspace path
    dataset_version: str = "1.0",
) -> FlyteFile[TypeVar("parquet")]:
    load_output = load_task(source_path=source_path, dataset_version=dataset_version)
    clean_output = clean_task(loaded=load_output["loaded"])
    features_output = feature_task(cleaned=clean_output["cleaned"])
    return features_output["features"]
```

### Stage Script (`flows/stages/load.py`)

```python
import json, os
import pandas as pd

INPUTS = "/workflow/inputs"
OUTPUTS = "/workflow/outputs"

def main():
    source_path = open(f"{INPUTS}/source_path").read().strip()
    dataset_version = open(f"{INPUTS}/dataset_version").read().strip()

    df = pd.read_csv(source_path)

    os.makedirs(OUTPUTS, exist_ok=True)
    # File output: write the parquet file itself under the declared output name
    df.to_parquet(f"{OUTPUTS}/loaded", index=False)
    # Metadata output: JSON string
    with open(f"{OUTPUTS}/load_stats", "w") as f:
        f.write(json.dumps({"row_count": len(df), "dataset_version": dataset_version}))

if __name__ == "__main__":
    main()
```

The next stage reads the file directly: `df = pd.read_parquet("/workflow/inputs/loaded")`.

## Example 2: Model Training Pipeline

### Flow Definition (`flows/training_pipeline.py`)

```python
from typing import TypeVar
from flytekit import workflow
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

prepare_task = DominoJobTask(
    name="Prepare Training Data",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/prepare.py'",
    ),
    inputs={"data_path": str, "test_size": float},
    outputs={"train": FlyteFile[TypeVar("parquet")], "test": FlyteFile[TypeVar("parquet")]},
    use_latest=True,
)

train_task = DominoJobTask(
    name="Train Model",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/train.py'",
        HardwareTierId="gpu-k8s",              # per-task hardware override (ID, not name)
    ),
    inputs={"train": FlyteFile[TypeVar("parquet")], "model_type": str},
    outputs={"model": FlyteFile[TypeVar("pkl")], "train_metrics": str},
    use_latest=True,
)

evaluate_task = DominoJobTask(
    name="Evaluate Model",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/evaluate.py'",
    ),
    inputs={"model": FlyteFile[TypeVar("pkl")], "test": FlyteFile[TypeVar("parquet")]},
    outputs={"eval_metrics": str},
    use_latest=True,
)

@workflow
def training_pipeline(
    data_path: str = "/mnt/data/features/features.parquet",
    test_size: float = 0.2,
    model_type: str = "xgboost",
) -> str:
    prepared = prepare_task(data_path=data_path, test_size=test_size)
    trained = train_task(train=prepared["train"], model_type=model_type)
    evaluated = evaluate_task(model=trained["model"], test=prepared["test"])
    return evaluated["eval_metrics"]
```

### Stage Script (`flows/stages/train.py`)

```python
import json, os, pickle
import mlflow
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import r2_score

INPUTS = "/workflow/inputs"
OUTPUTS = "/workflow/outputs"

def main():
    df = pd.read_parquet(f"{INPUTS}/train")                 # FlyteFile input: read directly
    model_type = open(f"{INPUTS}/model_type").read().strip()

    X = df.drop(columns=["target"])
    y = df["target"]

    with mlflow.start_run() as run:
        model = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1)
        model.fit(X, y)
        r2 = r2_score(y, model.predict(X))
        mlflow.log_metric("r2_score", r2)
        mlflow.xgboost.log_model(model, "model")

    os.makedirs(OUTPUTS, exist_ok=True)
    with open(f"{OUTPUTS}/model", "wb") as f:                # FlyteFile output: the pickle itself
        pickle.dump(model, f)
    with open(f"{OUTPUTS}/train_metrics", "w") as f:
        f.write(json.dumps({"run_id": run.info.run_id, "r2_score": r2, "model_type": model_type}))
    print(f"Training complete: R²={r2:.4f}, run_id={run.info.run_id}")

if __name__ == "__main__":
    main()
```

## Example 3: Production Pins and Git References

The same training flow pinned for production: no `use_latest`, explicit environment, hardware,
dataset snapshot, main-repo ref, and a pinned imported repository. See
[Pin Git references per task](./FLOW-BASICS.md#pin-git-references-per-task).

```python
from typing import TypeVar
from flytekit import workflow
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.task import (
    DatasetSnapshot, DominoJobConfig, DominoJobTask,
    EnvironmentRevisionSpecification, EnvironmentRevisionType,
    GitRef, ImportedGitRepoOverride,
)

ENV_ID = "66b5324c495c6c124cfb0a28"
ENV_REV = EnvironmentRevisionSpecification(EnvironmentRevisionType.SomeRevision, "4")
CODE_REF = GitRef(Type="tags", Value="v1.4.0")
SHARED_UTILS_REF = ImportedGitRepoOverride(
    Name="shared-utils",                                         # imported repo name on the project
    Ref=GitRef(Type="commitId", Value="2f1cb9bf696921f0858"),
)

def pinned_config(command: str, hardware_tier_id: str) -> DominoJobConfig:
    return DominoJobConfig(
        Command=command,
        EnvironmentId=ENV_ID,
        EnvironmentRevisionSpec=ENV_REV,
        HardwareTierId=hardware_tier_id,
        MainRepoGitRef=CODE_REF,
        ImportedGitRepoOverrides=[SHARED_UTILS_REF],
        UseLatestGitRef=False,                                   # relaunches reuse the resolved commits
        DatasetSnapshots=[DatasetSnapshot(Id="6615af2820a4", Version=3)],   # mounted at /mnt/data/<name>
        VolumeSizeGiB=20.0,
    )

prepare_task = DominoJobTask(
    name="Prepare Training Data",
    domino_job_config=pinned_config(
        "bash -c 'PYTHONPATH=/mnt/code:/mnt/imported/code/shared-utils python /mnt/code/flows/stages/prepare.py'",
        "small-k8s",
    ),
    inputs={"data_path": str, "test_size": float},
    outputs={"train": FlyteFile[TypeVar("parquet")], "test": FlyteFile[TypeVar("parquet")]},
    use_latest=False,
    cache=True,
    cache_version="1.0",
)

train_task = DominoJobTask(
    name="Train Model",
    domino_job_config=pinned_config(
        "bash -c 'PYTHONPATH=/mnt/code:/mnt/imported/code/shared-utils python /mnt/code/flows/stages/train.py'",
        "gpu-k8s",
    ),
    inputs={"train": FlyteFile[TypeVar("parquet")], "model_type": str},
    outputs={"model": FlyteFile[TypeVar("pkl")], "train_metrics": str},
    use_latest=False,
    retries=1,
)

@workflow
def training_pipeline_prod(test_size: float = 0.2, model_type: str = "xgboost") -> str:
    prepared = prepare_task(data_path="/mnt/data/features/features.parquet", test_size=test_size)
    trained = train_task(train=prepared["train"], model_type=model_type)
    return trained["train_metrics"]
```

To move this to a new release, change `CODE_REF` and re-run `pyflyte run --remote`, or leave the
code alone and apply a Git reference override to the affected task in the **Re-run** dialog.

## Example 4: Flow Artifacts and Export

See [FLOW-ARTIFACTS.md](./FLOW-ARTIFACTS.md) for marking outputs as `DATA` / `MODEL` / `REPORT`
artifacts and exporting them to a Dataset or NetApp Volume with `run_launch_export_artifacts_task`.

## Running Flows

### Trigger Remotely

```bash
# Always commit and push first — jobs run against remote repo state
git add -A && git commit -m "..." && git push

# Trigger the flow (registers a new version if the definition changed).
# --name is optional and must be unique across all flows in the project; --tag is optional.
PYTHONPATH=/mnt/code pyflyte run --remote \
    --name training-2026-10-13 \
    --tag team=ml \
    flows/training_pipeline.py training_pipeline \
    --test_size 0.2 \
    --model_type xgboost
```

### Rerun from the UI

**Flows > flow > version > run > Re-run**: set a run name, choose whether to overwrite cache,
reuse or change inputs, then add per-task overrides (Compute Environment, Hardware Tier, Git ref).
Use **Recover** on a run that failed for a transient reason to resume from the failed node, and
**Rerun Node** to rerun one node with new inputs. UI reruns require an unchanged definition.

### Monitor Execution

```python
from flytekit.remote import FlyteRemote
from flytekit.configuration import Config
import time

remote = FlyteRemote(
    config=Config.auto(),   # reads ~/.flyte/config.yaml
    default_project="<your-project-id>",
    default_domain="development",
)

PHASES = {0:"UNDEFINED",1:"QUEUED",2:"RUNNING",3:"SUCCEEDING",4:"SUCCEEDED",
          5:"FAILING",6:"FAILED",7:"ABORTED",8:"TIMED_OUT"}

exec_id = "my-execution-name"   # from pyflyte run output
for _ in range(60):
    execution = remote.fetch_execution(name=exec_id)
    remote.sync(execution, sync_nodes=True)
    phase = PHASES[execution.closure.phase]

    node_statuses = {
        nid: PHASES[ne.closure.phase]
        for nid, ne in execution.node_executions.items()
    }
    print(f"{phase}: {node_statuses}")

    if phase in ("SUCCEEDED", "FAILED", "ABORTED"):
        break
    time.sleep(30)
```

### Debug Failed Stage

```python
for node_id, node_exec in execution.node_executions.items():
    phase = PHASES[node_exec.closure.phase]
    if phase in ("FAILED", "FAILING"):
        for te in (node_exec.task_executions or []):
            full_te = remote.client.get_task_execution(te.id)
            if full_te.closure.error:
                # Full error message includes Python traceback from the job
                print(f"=== {node_id} error ===")
                print(full_te.closure.error.message)
```

## Data Sharing Between Stages

Each stage is an isolated Domino Job in its own pod, and Flow jobs do not commit code or snapshot
results when they finish. Only declared outputs and mounted snapshots are shared:

| Storage | Path in task | Use |
|---------|--------------|-----|
| Typed task outputs | `/workflow/outputs/<name>` → next task's `/workflow/inputs/<name>` | Any file or value a later task needs; versioned in Flow blob storage with lineage |
| Dataset snapshot | `/mnt/data/<dataset>/...` (shared: `/mnt/imported/data/<dataset>/...`) | Read-only versioned inputs, same path as a Workspace |
| NetApp Volume snapshot | `/mnt/netapp-volumes/<volume>/...` | Read-only versioned inputs, same path as a Workspace |
| `Output(path="/mnt/data/...")` via helper | Workspace path | Write back to a data path and propagate it downstream; optionally snapshot at run end |
| `/mnt/artifacts`, `/mnt/code` | — | **Not shared, not persisted** in Flow tasks |

**Pattern**: write large files directly as `FlyteFile` outputs and pass small metadata as JSON.

```python
# Stage 2 writes a parquet output and a JSON summary
df_results.to_parquet(f"{OUTPUTS}/results", index=False)
with open(f"{OUTPUTS}/results_summary", "w") as f:
    f.write(json.dumps({"row_count": len(df_results)}))

# Stage 3 declares inputs {"results": FlyteFile[TypeVar("parquet")], "results_summary": str}
df = pd.read_parquet(f"{INPUTS}/results")
summary = json.loads(open(f"{INPUTS}/results_summary").read())
```

To publish a final result outside the flow, declare it as a Flow Artifact and export it to a
Dataset or NetApp Volume ([FLOW-ARTIFACTS.md](./FLOW-ARTIFACTS.md)).
