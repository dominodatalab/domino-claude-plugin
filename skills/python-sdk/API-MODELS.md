# Domino Models API

## Overview
The Models API covers Model APIs (deployed endpoints), Model Deployments, and the Model Registry.

## Authentication
```python
import requests

headers = {"X-Domino-Api-Key": "YOUR_API_KEY"}
base_url = "https://your-domino.com"
```

---

## Model APIs (Deployed Endpoints)

### List Model APIs
```
GET /api/modelServing/v1/modelApis
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `projectId` | string | Filter by project |
| `offset` | int | Pagination offset |
| `limit` | int | Results per page |

**Example:**
```python
response = requests.get(
    f"{base_url}/api/modelServing/v1/modelApis",
    headers=headers,
    params={"projectId": "project-123"}
)
models = response.json()
```

---

### Create Model API
```
POST /api/modelServing/v1/modelApis
```

Deploy a model as an API endpoint.

**Request Body:**
```json
{
  "projectId": "project-123",
  "name": "fraud-detector",
  "description": "Fraud detection model",
  "modelFile": "model.py",
  "modelFunction": "predict",
  "environmentId": "env-789",
  "hardwareTierId": "small"
}
```

**Example:**
```python
response = requests.post(
    f"{base_url}/api/modelServing/v1/modelApis",
    headers=headers,
    json={
        "projectId": "project-123",
        "name": "customer-churn",
        "description": "Predicts customer churn probability",
        "modelFile": "serve.py",
        "modelFunction": "predict",
        "environmentId": "env-789",
        "hardwareTierId": "small"
    }
)
model_api = response.json()
print(f"Model API ID: {model_api['id']}")
```

---

### Get Model API
```
GET /api/modelServing/v1/modelApis/{modelApiId}
```

**Response:**
```json
{
  "id": "model-api-456",
  "name": "fraud-detector",
  "status": "Running",
  "url": "https://your-domino.com/models/model-api-456/latest/model",
  "projectId": "project-123",
  "createdAt": "2024-01-15T10:00:00Z"
}
```

---

### Update Model API
```
PUT /api/modelServing/v1/modelApis/{modelApiId}
```

---

### Delete Model API
```
DELETE /api/modelServing/v1/modelApis/{modelApiId}
```

---

## Model API Versions

### List Versions
```
GET /api/modelServing/v1/modelApis/{modelApiId}/versions
```

### Create New Version
```
POST /api/modelServing/v1/modelApis/{modelApiId}/versions
```

**Request Body:**
```json
{
  "modelFile": "model_v2.py",
  "modelFunction": "predict",
  "environmentId": "env-789"
}
```

### Get Version Details
```
GET /api/modelServing/v1/modelApis/{modelApiId}/versions/{versionId}
```

---

## Model API Logs

### Build Logs
```
GET /api/modelServing/v1/modelApis/{modelApiId}/versions/{versionId}/buildLogs
```

### Export Logs
```
GET /api/modelServing/v1/modelApis/{modelApiId}/versions/{versionId}/exportLogs
```

### Instance Logs
```
GET /api/modelServing/v1/modelApis/{modelApiId}/versions/{versionId}/instanceLogs
```

---

## Model Deployments

### List Deployments
```
GET /api/modelServing/v1/modelDeployments
```

### Create Deployment
```
POST /api/modelServing/v1/modelDeployments
```

**Request Body:**
```json
{
  "name": "production-deployment",
  "modelVersionId": "version-123",
  "hardwareTierId": "medium",
  "replicas": 2
}
```

### Get Deployment
```
GET /api/modelServing/v1/modelDeployments/{deploymentId}
```

### Update Deployment
```
PATCH /api/modelServing/v1/modelDeployments/{deploymentId}
```

### Delete Deployment
```
DELETE /api/modelServing/v1/modelDeployments/{deploymentId}
```

### Start Deployment
```
POST /api/modelServing/v1/modelDeployments/{deploymentId}/start
```

### Stop Deployment
```
POST /api/modelServing/v1/modelDeployments/{deploymentId}/stop
```

### Get Deployment Logs
```
GET /api/modelServing/v1/modelDeployments/{deploymentId}/logs/{logSuffix}
```

### Get Deployment Credentials
```
GET /api/modelServing/v1/modelDeployments/{deploymentId}/credentials
```

---

## Registered Models (Model Registry)

### List Registered Models
```
GET /api/registeredmodels/v2
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `offset` | int | Pagination offset |
| `limit` | int | Results per page |
| `name` | string | Filter by name |

### Register Model
```
POST /api/registeredmodels/v2
```

**Request Body:**
```json
{
  "name": "fraud-classifier",
  "description": "Random forest fraud classifier",
  "source": {
    "type": "experiment",
    "experimentId": "exp-123",
    "runId": "run-456"
  }
}
```

### Get Registered Model
```
GET /api/registeredmodels/v1/{modelName}
```

### Update Registered Model
```
PATCH /api/registeredmodels/v1/{modelName}
```

---

## Model Versions

### List Model Versions
```
GET /api/registeredmodels/v1/{modelName}/versions
```

### Create Model Version
```
POST /api/registeredmodels/v1/{modelName}/versions
```

### Get Model Version
```
GET /api/registeredmodels/v1/{modelName}/versions/{version}
```

### Get Model APIs for Version
```
GET /api/registeredmodels/v1/{modelName}/versions/{version}/modelapis
```

Returns list of Model APIs deployed from this version.

---

## Calling Model APIs

### Synchronous Request
```python
import requests

model_url = "https://your-domino.com/models/model-api-456/latest/model"

response = requests.post(
    model_url,
    auth=("MODEL_ACCESS_TOKEN", "MODEL_ACCESS_TOKEN"),
    json={"data": {"features": [1.0, 2.0, 3.0, 4.0]}}
)

prediction = response.json()
print(f"Prediction: {prediction['result']}")
```

### Asynchronous Request
```python
# Submit async request
response = requests.post(
    f"{base_url}/api/modelApis/async/v1/{model_api_id}",
    headers={"Authorization": f"Bearer {model_access_token}"},
    json={"parameters": {"input_file": "s3://bucket/data.csv"}}
)
prediction_id = response.json()["predictionId"]

# Poll for results
import time
while True:
    status = requests.get(
        f"{base_url}/api/modelApis/async/v1/{model_api_id}/{prediction_id}",
        headers={"Authorization": f"Bearer {model_access_token}"}
    ).json()

    if status["status"] == "COMPLETED":
        print(f"Result: {status['result']}")
        break
    elif status["status"] == "FAILED":
        print(f"Error: {status['error']}")
        break
    time.sleep(5)
```

---

## Python SDK Examples

### Deploy Model
```python
from domino import Domino

domino = Domino("owner/project-name")

# Publish model API
model = domino.model_publish(
    file="model.py",
    function="predict",
    environment_id="env-789",
    name="my-classifier",
    description="Classification model"
)
print(f"Model ID: {model['id']}")
print(f"Model URL: {model['url']}")
```

### List Models
```python
models = domino.models_list()
for m in models:
    print(f"{m['name']}: {m['status']}")
```

---

## Complete Workflow

```python
# 1. Train model in job
run = domino.runs_start(command="python train.py")
domino.runs_wait(run['runId'])

# 2. Register model (if using MLflow)
# Model automatically registered during training

# 3. Deploy as API
model_api = requests.post(
    f"{base_url}/api/modelServing/v1/modelApis",
    headers=headers,
    json={
        "projectId": project_id,
        "name": "production-model",
        "modelFile": "serve.py",
        "modelFunction": "predict",
        "environmentId": env_id,
        "hardwareTierId": "medium"
    }
).json()

# 4. Test endpoint
test_response = requests.post(
    model_api['url'],
    auth=(access_token, access_token),
    json={"data": {"features": [1, 2, 3]}}
)
print(f"Test prediction: {test_response.json()}")
```
