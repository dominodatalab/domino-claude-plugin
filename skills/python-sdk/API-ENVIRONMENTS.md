# Domino Environments API

## Overview
The Environments API allows you to create, manage, and version Domino Compute Environments programmatically.

## Authentication
```python
import requests

headers = {"X-Domino-Api-Key": "YOUR_API_KEY"}
base_url = "https://your-domino.com"
```

---

## Endpoints

### List Environments
```
GET /api/environments/beta/environments
```

Get environments visible to the user.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `offset` | int | Pagination offset |
| `limit` | int | Results per page |
| `name` | string | Filter by name |

**Example:**
```python
response = requests.get(
    f"{base_url}/api/environments/beta/environments",
    headers=headers,
    params={"limit": 50}
)
environments = response.json()

for env in environments['data']:
    print(f"{env['name']}: {env['id']}")
```

**Response:**
```json
{
  "data": [
    {
      "id": "env-123",
      "name": "Domino Standard Environment",
      "description": "Default environment with Python and R",
      "visibility": "Global",
      "latestRevisionId": "rev-456",
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ],
  "offset": 0,
  "limit": 50,
  "totalCount": 10
}
```

---

### Create Environment
```
POST /api/environments/beta/environments
```

Create a new custom environment.

**Request Body:**
```json
{
  "name": "custom-ml-env",
  "description": "Custom ML environment with TensorFlow",
  "visibility": "Private",
  "baseEnvironmentId": "env-123"
}
```

**Example:**
```python
response = requests.post(
    f"{base_url}/api/environments/beta/environments",
    headers=headers,
    json={
        "name": "pytorch-gpu-env",
        "description": "PyTorch environment with GPU support",
        "visibility": "Private",
        "baseEnvironmentId": "base-env-id"
    }
)
environment = response.json()
print(f"Created environment: {environment['id']}")
```

---

### Get Environment
```
GET /api/environments/v1/environments/{environmentId}
```

Get detailed information about an environment.

**Example:**
```python
env_id = "env-123"
response = requests.get(
    f"{base_url}/api/environments/v1/environments/{env_id}",
    headers=headers
)
environment = response.json()
```

**Response:**
```json
{
  "id": "env-123",
  "name": "custom-ml-env",
  "description": "Custom ML environment",
  "visibility": "Private",
  "latestRevision": {
    "id": "rev-789",
    "number": 3,
    "status": "Succeeded",
    "dockerImage": "docker.domino.tech/env-123:rev-789"
  },
  "dockerfileInstructions": "RUN pip install tensorflow==2.13.0"
}
```

---

### Archive Environment
```
DELETE /api/environments/v1/environments/{environmentId}
```

Archive an environment (soft delete).

**Example:**
```python
response = requests.delete(
    f"{base_url}/api/environments/v1/environments/{env_id}",
    headers=headers
)
```

---

## Environment Revisions

### Create Revision
```
POST /api/environments/beta/environments/{environmentId}/revisions
```

Create a new revision with updated Dockerfile instructions.

**Request Body:**
```json
{
  "dockerfileInstructions": "RUN pip install pandas==2.0.0 numpy scikit-learn"
}
```

**Example:**
```python
response = requests.post(
    f"{base_url}/api/environments/beta/environments/{env_id}/revisions",
    headers=headers,
    json={
        "dockerfileInstructions": """
RUN pip install --no-cache-dir \\
    pandas==2.0.0 \\
    numpy>=1.24.0 \\
    scikit-learn==1.3.0 \\
    tensorflow==2.13.0
"""
    }
)
revision = response.json()
print(f"Created revision: {revision['id']}")
```

---

### Update Revision Restriction
```
PATCH /api/environments/beta/environments/{environmentId}/revisions/{revisionId}
```

Update revision settings (e.g., restrict usage).

**Request Body:**
```json
{
  "restricted": true
}
```

---

## Python SDK Examples

### List Environments
```python
from domino import Domino

domino = Domino("owner/project-name")

# List all environments
environments = domino.environments_list()
for env in environments:
    print(f"{env['name']}: {env['id']}")
```

### Get Environment Details
```python
env = domino.environment_get("env-123")
print(f"Name: {env['name']}")
print(f"Latest Revision: {env['latestRevision']['number']}")
```

---

## Dockerfile Instructions

When creating or updating environments, use proper Dockerfile syntax:

### Install Python Packages
```dockerfile
RUN pip install --no-cache-dir \
    pandas==2.0.0 \
    numpy>=1.24.0 \
    scikit-learn==1.3.0
```

### Install System Packages
```dockerfile
RUN apt-get update && apt-get install -y \
    libpq-dev \
    graphviz \
    && rm -rf /var/lib/apt/lists/*
```

### Install R Packages
```dockerfile
RUN R -e "install.packages(c('tidyverse', 'caret'), repos='https://cloud.r-project.org')"
```

### Set Environment Variables
```dockerfile
ENV MODEL_PATH=/mnt/artifacts/model.pkl
ENV PYTHONPATH=/opt/custom:$PYTHONPATH
```

### GPU Libraries
```dockerfile
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

## Environment Workflow

```python
# 1. Create new environment
response = requests.post(
    f"{base_url}/api/environments/beta/environments",
    headers=headers,
    json={
        "name": "ml-training-env",
        "description": "Environment for ML model training",
        "visibility": "Private",
        "baseEnvironmentId": "domino-standard-env-id"
    }
)
env = response.json()
env_id = env['id']

# 2. Add Dockerfile instructions via revision
response = requests.post(
    f"{base_url}/api/environments/beta/environments/{env_id}/revisions",
    headers=headers,
    json={
        "dockerfileInstructions": """
RUN pip install --no-cache-dir \\
    xgboost==2.0.0 \\
    lightgbm==4.1.0 \\
    catboost==1.2.0 \\
    optuna==3.4.0
"""
    }
)
revision = response.json()

# 3. Wait for build to complete
# Check revision status periodically
import time
while True:
    env_details = requests.get(
        f"{base_url}/api/environments/v1/environments/{env_id}",
        headers=headers
    ).json()

    status = env_details['latestRevision']['status']
    if status == 'Succeeded':
        print("Environment build complete!")
        break
    elif status == 'Failed':
        print("Environment build failed!")
        break
    else:
        print(f"Building... Status: {status}")
        time.sleep(30)

# 4. Use environment in job
response = requests.post(
    f"{base_url}/api/jobs/v1/jobs",
    headers=headers,
    json={
        "projectId": project_id,
        "commandToRun": "python train.py",
        "environmentId": env_id,
        "hardwareTierId": "medium"
    }
)
```

---

## Best Practices

1. **Base on Standard Environments**: Start from Domino Standard Environments
2. **Pin Versions**: Always specify exact package versions
3. **Combine RUN Commands**: Reduce layers by combining installations
4. **Clean Up**: Remove cache files to reduce image size
5. **Test Locally**: Verify Dockerfile syntax before creating revisions
