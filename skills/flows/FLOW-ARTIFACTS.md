# Domino Flow Artifacts

A flow can produce hundreds of intermediate outputs. Flow Artifacts mark the few that matter
(a cleaned dataset, a trained model, a report) so they are easy to find, preview, download, and
export, with lineage back to the run that produced them.

## Declare an Artifact

```python
from flytekitplugins.domino.artifact import Artifact, DATA, MODEL, REPORT

DataArtifact = Artifact(name="Merged Data", type=DATA)
ModelArtifact = Artifact(name="Random Forest Model", type=MODEL)
ReportArtifact = Artifact(name="TFL Reports", type=REPORT)
```

| Type | Meaning |
|------|---------|
| `DATA` | Files that may later be added as a new Dataset snapshot |
| `MODEL` | Files that may later be registered as a model |
| `REPORT` | Files that together make up a report |

Attach a file to an artifact anywhere an output type is declared with `.File(name="...")`.
The file type is inferred from the extension, so no `FlyteFile[TypeVar(...)]` is needed:

```python
from typing import TypeVar
from flytekit import workflow
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask
from flytekitplugins.domino.artifact import Artifact, DATA, MODEL

DataArtifact = Artifact(name="My Data", type=DATA)
ModelArtifact = Artifact(name="My Model", type=MODEL)

@workflow
def training_workflow(data_path: str) -> ModelArtifact.File(name="model.pt"):
    data_prep_job = DominoJobTask(
        name="Prep data",
        domino_job_config=DominoJobConfig(Command="python prep-data.py"),
        inputs={"data_path": str},
        outputs={"processed_data": DataArtifact.File(name="data.csv")},   # task output as artifact file
        use_latest=True,
    )
    data_prep_results = data_prep_job(data_path=data_path)

    training_job = DominoJobTask(
        name="Train model",
        domino_job_config=DominoJobConfig(Command="python train-model.py"),
        inputs={"processed_data": FlyteFile[TypeVar("csv")]},
        outputs={"model": FlyteFile[TypeVar("pt")]},
        use_latest=True,
    )
    training_results = training_job(processed_data=data_prep_results["processed_data"])

    return training_results["model"]   # flow output as artifact file
```

The stage script still writes the output under its declared name (`/workflow/outputs/processed_data`);
the artifact file name (`data.csv`) is how it appears in the Artifacts tab.

Rules:

- An artifact may collect files from different tasks, and there is no limit on artifact count or
  files per artifact.
- One artifact cannot contain the same file name twice.
- If `name` has no extension, pass `type=`: `ModelArtifact.File(name="classes", type="txt")`.
- With the helper: `Output(name="model", type=ModelArtifact.File(name="model.pkl"))`.
- Returning a flow-level output does not make it an artifact; use `.File(...)` for that.

Users inspect, preview, download, bookmark, and assign `DATA` artifacts to a Dataset from
**Flows > run > Artifacts** in the UI, and from Governance bundles as attachments.

## Export Artifacts to Datasets and NetApp Volumes

`run_launch_export_artifacts_task` exports artifact files to a Domino Dataset and/or a NetApp
Volume automatically at the end of a run, so new outputs flow into versioned storage without a
manual step.

```python
from typing import TypeVar
from flytekit import workflow
from flytekit.types.file import FlyteFile
from flytekitplugins.domino.task import DominoJobConfig, DominoJobTask
from flytekitplugins.domino.artifact import (
    Artifact, DATA, MODEL,
    ExportArtifactToDatasetsSpec, ExportArtifactToNetAppVolumesSpec, FileCollisionSetting,
    run_launch_export_artifacts_task,
)

DataArtifact = Artifact(name="My Data", type=DATA)
ModelArtifact = Artifact(name="My Model", type=MODEL)

@workflow
def training_workflow(data_path: str) -> ModelArtifact.File(name="model.pt"):
    data_prep_job = DominoJobTask(
        name="Prep data",
        domino_job_config=DominoJobConfig(Command="python prep-data.py"),
        inputs={"data_path": str},
        outputs={"processed_data": DataArtifact.File(name="data.csv")},
        use_latest=True,
    )
    data_prep_results = data_prep_job(data_path=data_path)

    training_job = DominoJobTask(
        name="Train model",
        domino_job_config=DominoJobConfig(Command="python train-model.py"),
        inputs={"processed_data": FlyteFile[TypeVar("csv")]},
        outputs={"model": FlyteFile[TypeVar("pt")]},
        use_latest=True,
    )
    training_results = training_job(processed_data=data_prep_results["processed_data"])

    run_launch_export_artifacts_task(
        spec_list=[
            ExportArtifactToDatasetsSpec(
                artifact=DataArtifact,
                dataset_id="681d3030ae3a706ef9c7f08b",
            ),
            ExportArtifactToNetAppVolumesSpec(
                artifact=DataArtifact,
                netapp_volume_id="5d1204c2-24c8-47df-a47f-69185efa602b",
                target_relative_path="flows-data",
                file_collision_setting=FileCollisionSetting.RENAME,
            ),
        ],
        environment_name="Domino Standard Environment",   # must be DSE >= 6.0 or built on it
        hardware_tier_id="small-k8s",                      # minimal tier; this task only launches the export
        use_project_defaults_for_omitted=True,
    )

    return training_results["model"]
```

### `run_launch_export_artifacts_task` parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `spec_list` | `List[ExportArtifactToDatasetsSpec \| ExportArtifactToNetAppVolumesSpec]` | What to export, where |
| `use_project_defaults_for_omitted` | bool | Fill omitted settings from project defaults |
| `environment_name` / `environment_id` / `environment_revision_id` | str | Must resolve to the Domino Standard Environment 6.0+ or a derivative (needs Flyte Python and `jq`) |
| `hardware_tier_name` / `hardware_tier_id` | str | Use a minimal-resource tier |
| `retries` | int | |
| `timeout` | `timedelta \| int`, default 3h | Set longer than the whole workflow; the export waits for the run to finish |

### `ExportArtifactToDatasetsSpec`

| Parameter | Type | Notes |
|-----------|------|-------|
| `artifact` | `Artifact` | The artifact to export |
| `dataset_id` | str | Target Domino Dataset ID |

### `ExportArtifactToNetAppVolumesSpec`

| Parameter | Type | Notes |
|-----------|------|-------|
| `artifact` | `Artifact` | The artifact to export |
| `netapp_volume_id` | str | Target NetApp Volume ID |
| `target_relative_path` | str, default `""` | Directory on the volume; empty writes to the root |
| `file_collision_setting` | `FileCollisionSetting`, default `RENAME` | `RENAME`, `IGNORE`, or `OVERWRITE` when a file already exists |

### How the export runs

- The call adds a small launch task to the graph. It can appear early (for example at `n0`) and
  finish before the data tasks do. That is expected: it only triggers a **separate export
  execution**, which waits for the main run to finish and for every referenced artifact to exist.
- To check export progress, open the export execution linked from the launch task's logs; it has
  per-artifact logs.
- A long-running flow needs a `timeout` on the export task that exceeds the flow's duration.

## Finding IDs

Dataset IDs for `dataset_id` (route `GET /api/datasetrw/v1/datasets`, present in the 6.3 and
Cloud public API specs; response is `{"datasets": [{"id", "name", "projectId", ...}]}`):

```bash
TOKEN=$(curl -s http://localhost:8899/access-token)
curl -s -H "Authorization: Bearer $TOKEN" \
  "$DOMINO_API_HOST/api/datasetrw/v1/datasets?projectId=$DOMINO_PROJECT_ID" \
  | jq -r '.datasets[] | "\(.id)\t\(.name)"'
```

NetApp Volume IDs for `netapp_volume_id` come from the volume's details page in the UI or the
remotefs API; see the `netapp-volumes` skill.

## Documentation

- Define Flow Artifacts: https://docs.domino.ai/cloud/platform-capabilities/features/flows/define-flow-artifacts
- Examine Flow Artifacts: https://docs.domino.ai/cloud/platform-capabilities/features/flows/examine-flow-artifacts
