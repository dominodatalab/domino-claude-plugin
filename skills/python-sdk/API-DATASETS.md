# Domino Datasets API

## Overview
The Datasets API allows you to create, manage, and version Domino Datasets programmatically.

## Authentication
```python
import requests

headers = {"X-Domino-Api-Key": "YOUR_API_KEY"}
base_url = "https://your-domino.com"
```

---

## Endpoints

### List Datasets
```
GET /api/datasetrw/v2/datasets
```

Get datasets the user has access to.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `projectId` | string | Filter by project |
| `offset` | int | Pagination offset |
| `limit` | int | Results per page |

**Example:**
```python
response = requests.get(
    f"{base_url}/api/datasetrw/v2/datasets",
    headers=headers,
    params={"limit": 50}
)
datasets = response.json()
```

**Response:**
```json
{
  "data": [
    {
      "id": "dataset-123",
      "name": "training-data",
      "description": "Training dataset for ML model",
      "projectId": "project-456",
      "createdAt": "2024-01-15T10:00:00Z",
      "sizeBytes": 1073741824
    }
  ],
  "offset": 0,
  "limit": 50,
  "totalCount": 1
}
```

---

### Create Dataset
```
POST /api/datasetrw/v1/datasets
```

Create a new dataset.

**Request Body:**
```json
{
  "name": "training-data",
  "description": "Training dataset for classification model",
  "projectId": "project-123"
}
```

**Example:**
```python
response = requests.post(
    f"{base_url}/api/datasetrw/v1/datasets",
    headers=headers,
    json={
        "name": "customer-features",
        "description": "Processed customer features for modeling",
        "projectId": "project-123"
    }
)
dataset = response.json()
print(f"Created dataset: {dataset['id']}")
```

---

### Get Dataset
```
GET /api/datasetrw/v1/datasets/{datasetId}
```

**Example:**
```python
dataset_id = "dataset-123"
response = requests.get(
    f"{base_url}/api/datasetrw/v1/datasets/{dataset_id}",
    headers=headers
)
dataset = response.json()
```

---

### Update Dataset
```
PATCH /api/datasetrw/v1/datasets/{datasetId}
```

Update dataset metadata.

**Request Body:**
```json
{
  "name": "new-name",
  "description": "Updated description"
}
```

---

### Delete Dataset
```
DELETE /api/datasetrw/v1/datasets/{datasetId}
```

Delete a dataset (marks for deletion).

---

## Snapshots

### List Snapshots
```
GET /api/datasetrw/v1/datasets/{datasetId}/snapshots
```

Get all snapshots for a dataset.

**Example:**
```python
response = requests.get(
    f"{base_url}/api/datasetrw/v1/datasets/{dataset_id}/snapshots",
    headers=headers
)
snapshots = response.json()

for snapshot in snapshots['data']:
    print(f"Snapshot: {snapshot['id']} - Created: {snapshot['createdAt']}")
```

**Response:**
```json
{
  "data": [
    {
      "id": "snapshot-789",
      "datasetId": "dataset-123",
      "createdAt": "2024-01-15T10:00:00Z",
      "tags": ["v1.0", "production"]
    }
  ]
}
```

---

### Create Snapshot
```
POST /api/datasetrw/v1/datasets/{datasetId}/snapshots
```

Create a new snapshot of the current dataset state.

**Request Body:**
```json
{
  "tag": "v1.0"
}
```

**Example:**
```python
response = requests.post(
    f"{base_url}/api/datasetrw/v1/datasets/{dataset_id}/snapshots",
    headers=headers,
    json={"tag": "v2.0"}
)
snapshot = response.json()
print(f"Created snapshot: {snapshot['id']}")
```

---

### Get Snapshot
```
GET /api/datasetrw/v1/snapshots/{snapshotId}
```

Get details for a specific snapshot.

---

## Tags

### Add Tag to Snapshot
```
POST /api/datasetrw/v1/datasets/{datasetId}/tags
```

Tag a snapshot in the dataset.

**Request Body:**
```json
{
  "snapshotId": "snapshot-789",
  "tagName": "production"
}
```

**Example:**
```python
response = requests.post(
    f"{base_url}/api/datasetrw/v1/datasets/{dataset_id}/tags",
    headers=headers,
    json={
        "snapshotId": "snapshot-789",
        "tagName": "production"
    }
)
```

### Remove Tag
```
DELETE /api/datasetrw/v1/datasets/{datasetId}/tags/{tagName}
```

---

## Grants (Permissions)

### Get Dataset Grants
```
GET /api/datasetrw/v1/datasets/{datasetId}/grants
```

Get permission grants for a dataset.

### Add Grant
```
POST /api/datasetrw/v1/datasets/{datasetId}/grants
```

**Request Body:**
```json
{
  "principalType": "user",
  "principalId": "user-456",
  "permission": "read"
}
```

**Permission Values:**
- `read` - View dataset
- `write` - Modify dataset
- `admin` - Full control

### Remove Grant
```
DELETE /api/datasetrw/v1/datasets/{datasetId}/grants
```

**Request Body:**
```json
{
  "principalType": "user",
  "principalId": "user-456"
}
```

---

## Python SDK Examples

### Create and Manage Dataset
```python
from domino import Domino

domino = Domino("owner/project-name")

# Create dataset
dataset = domino.datasets_create(
    name="model-training-data",
    description="Preprocessed training data"
)
print(f"Created: {dataset['id']}")

# List datasets
datasets = domino.datasets_list()
for ds in datasets:
    print(f"  {ds['name']}: {ds['id']}")
```

### Create Snapshot
```python
# Create snapshot with tag
snapshot = domino.datasets_snapshot(
    dataset_name="model-training-data",
    tag="v1.0"
)
print(f"Snapshot: {snapshot['id']}")
```

---

## Working with Dataset Data

### Upload Data (In Workspace/Job)
```python
import pandas as pd

# Write to dataset mount path
df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
df.to_parquet("/mnt/data/my-dataset/data.parquet")
```

### Read Data
```python
import pandas as pd

# Read from dataset
df = pd.read_parquet("/mnt/data/my-dataset/data.parquet")
```

### Access Specific Snapshot
```python
# Access tagged snapshot
df = pd.read_parquet("/mnt/data/my-dataset@v1.0/data.parquet")

# Access by snapshot ID
df = pd.read_parquet("/mnt/data/my-dataset@snapshot-789/data.parquet")
```

---

## Dataset Workflow Example

```python
import requests
import pandas as pd

# Create dataset
response = requests.post(
    f"{base_url}/api/datasetrw/v1/datasets",
    headers=headers,
    json={
        "name": "feature-store",
        "description": "Centralized feature storage",
        "projectId": project_id
    }
)
dataset = response.json()
dataset_id = dataset['id']

# After uploading data, create snapshot
response = requests.post(
    f"{base_url}/api/datasetrw/v1/datasets/{dataset_id}/snapshots",
    headers=headers,
    json={"tag": "baseline"}
)

# Grant access to another user
response = requests.post(
    f"{base_url}/api/datasetrw/v1/datasets/{dataset_id}/grants",
    headers=headers,
    json={
        "principalType": "user",
        "principalId": "data-scientist-user-id",
        "permission": "read"
    }
)

print(f"Dataset ready: {dataset_id}")
```
