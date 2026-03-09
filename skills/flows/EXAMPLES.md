# Domino Flows Examples

Complete, production-ready flow examples for Domino Flows.

> ⚠️ **Critical**: Use `DominoJobTask` + `DominoJobConfig`. Native `@task` decorators are NOT supported.

## Example 1: Data Processing Pipeline

### Flow Definition (`flows/data_pipeline.py`)

```python
from flytekit import workflow
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

load_task = DominoJobTask(
    name="Load Data",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/load.py'",
    ),
    inputs={"source_path": str, "dataset_version": str},
    outputs={"o0": str},
    use_latest=True,
)

clean_task = DominoJobTask(
    name="Clean Data",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/clean.py'",
    ),
    inputs={"load_output": str},
    outputs={"o0": str},
    use_latest=True,
)

feature_task = DominoJobTask(
    name="Create Features",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/features.py'",
    ),
    inputs={"clean_output": str},
    outputs={"o0": str},
    use_latest=True,
)

@workflow
def data_pipeline(
    source_path: str = "/mnt/data/raw.csv",
    dataset_version: str = "1.0",
) -> str:
    load_output = load_task(source_path=source_path, dataset_version=dataset_version)
    clean_output = clean_task(load_output=load_output)
    features_output = feature_task(clean_output=clean_output)
    return features_output
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

    # Save to shared location (e.g., /mnt/artifacts/ or /mnt/data/)
    output_path = "/mnt/artifacts/loaded_data.parquet"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)

    result = {
        "output_path": output_path,
        "row_count": len(df),
        "dataset_version": dataset_version,
    }
    os.makedirs(OUTPUTS, exist_ok=True)
    with open(f"{OUTPUTS}/o0", "w") as f:
        f.write(json.dumps(result))

if __name__ == "__main__":
    main()
```

## Example 2: Model Training Pipeline

### Flow Definition (`flows/training_pipeline.py`)

```python
from flytekit import workflow
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

prepare_task = DominoJobTask(
    name="Prepare Training Data",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/prepare.py'",
    ),
    inputs={"data_path": str, "test_size": float},
    outputs={"o0": str},
    use_latest=True,
)

train_task = DominoJobTask(
    name="Train Model",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/train.py'",
        # Override hardware for GPU training:
        # HardwareTierId="gpu-k8s",
    ),
    inputs={"prepare_output": str, "model_type": str},
    outputs={"o0": str},
    use_latest=True,
)

evaluate_task = DominoJobTask(
    name="Evaluate Model",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/flows/stages/evaluate.py'",
    ),
    inputs={"train_output": str},
    outputs={"o0": str},
    use_latest=True,
)

@workflow
def training_pipeline(
    data_path: str = "/mnt/data/features.parquet",
    test_size: float = 0.2,
    model_type: str = "xgboost",
) -> str:
    prepare_output = prepare_task(data_path=data_path, test_size=test_size)
    train_output = train_task(prepare_output=prepare_output, model_type=model_type)
    eval_output = evaluate_task(train_output=train_output)
    return eval_output
```

### Stage Script (`flows/stages/train.py`)

```python
import json, os
import mlflow
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

INPUTS = "/workflow/inputs"
OUTPUTS = "/workflow/outputs"

def main():
    prepare_output = json.loads(open(f"{INPUTS}/prepare_output").read())
    model_type = open(f"{INPUTS}/model_type").read().strip()

    df = pd.read_parquet(prepare_output["train_path"])
    X = df.drop(columns=["target"])
    y = df["target"]

    with mlflow.start_run() as run:
        model = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1)
        model.fit(X, y)

        preds = model.predict(X)
        r2 = r2_score(y, preds)
        mlflow.log_metric("r2_score", r2)
        mlflow.xgboost.log_model(model, "model")

    result = {
        "run_id": run.info.run_id,
        "r2_score": r2,
        "model_type": model_type,
    }
    os.makedirs(OUTPUTS, exist_ok=True)
    with open(f"{OUTPUTS}/o0", "w") as f:
        f.write(json.dumps(result))
    print(f"Training complete: R²={r2:.4f}, run_id={run.info.run_id}")

if __name__ == "__main__":
    main()
```

## Example 3: Multi-Stage ML Pipeline (Full Reference)

This is the Engine Forge 7-stage pipeline — a complete production example.

### Flow Definition

```python
"""7-stage engine design pipeline."""
import logging
from flytekit import workflow
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask

logger = logging.getLogger(__name__)

def _make_task(stage_num: int, name: str, inputs: dict, outputs: dict = None) -> DominoJobTask:
    """Helper to create a stage task with consistent config."""
    return DominoJobTask(
        name=f"Stage {stage_num}: {name}",
        domino_job_config=DominoJobConfig(
            Command=f"bash -c 'PYTHONPATH=/mnt/code python /mnt/code/app/flow/stages/stage{stage_num}_{name.lower().replace(' ', '_')}.py'",
        ),
        inputs=inputs,
        outputs=outputs or {"o0": str},
        use_latest=True,
    )

ingest_task = DominoJobTask(
    name="Stage 1: Ingest Data",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/app/flow/stages/stage1_ingest.py'",
    ),
    inputs={"dataset_version": str, "component_id": str, "spec_json": str, "n_top": int},
    outputs={"o0": str},
    use_latest=True,
)

analyze_task = DominoJobTask(
    name="Stage 2: Analyze Designs",
    domino_job_config=DominoJobConfig(
        Command="bash -c 'PYTHONPATH=/mnt/code python /mnt/code/app/flow/stages/stage2_analyze.py'",
    ),
    inputs={"snapshot": str},
    outputs={"o0": str},
    use_latest=True,
)

# ... stages 3-6 follow same pattern ...

@workflow
def engine_forge_pipeline(
    component_id: str = "engine-bracket",
    dataset_version: str = "1.0",
    spec_json: str = '{"max_stress_mpa": 1200.0}',
    n_top: int = 2,
) -> str:
    snapshot = ingest_task(
        dataset_version=dataset_version,
        component_id=component_id,
        spec_json=spec_json,
        n_top=n_top,
    )
    analysis_output = analyze_task(snapshot=snapshot)
    # ... chain remaining stages ...
    return analysis_output
```

## Running Flows

### Trigger Remotely

```bash
# Always commit and push first — jobs run against remote repo state
git add -A && git commit -m "..." && git push

# Trigger the flow
PYTHONPATH=/mnt/code pyflyte run --remote \
    app/flow/my_flow.py my_pipeline \
    --arg1 "value1" \
    --arg2 42
```

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

Since each stage is an isolated Domino Job, persistent data must use shared storage:

| Storage | Path | Use Case |
|---------|------|----------|
| Domino Artifacts | `/mnt/artifacts/` | Model files, reports (persisted) |
| Domino Datasets | `/mnt/data/<name>/` | Read-only reference data |
| Flow messages | `/workflow/inputs|outputs/` | Small JSON metadata between stages |

**Pattern**: Write large files to `/mnt/artifacts/`, pass the path as a JSON string through `/workflow/outputs/o0`.

```python
# Stage 2 writes parquet to artifacts, passes path via flow
output_path = "/mnt/artifacts/analysis_results.parquet"
df_results.to_parquet(output_path)
result = {"results_path": output_path, "row_count": len(df_results)}
with open(f"{OUTPUTS}/o0", "w") as f:
    f.write(json.dumps(result))

# Stage 3 reads from artifacts using the path
analysis_output = json.loads(open(f"{INPUTS}/analysis_output").read())
df = pd.read_parquet(analysis_output["results_path"])
```
