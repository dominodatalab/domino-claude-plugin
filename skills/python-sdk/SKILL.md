---
name: domino-python-sdk
description: Programmatically interact with Domino using python-domino SDK and REST APIs. Covers authentication, running jobs, managing projects, file operations, model deployment, and automation. Use when automating Domino workflows, integrating with CI/CD, or building custom tooling around Domino.
---

# Domino Python SDK Skill

## Description
This skill helps users work with the Domino Python SDK (python-domino) and REST APIs to programmatically interact with Domino.

## Activation
Activate this skill when users want to:
- Use the Domino Python SDK
- Make API calls to Domino
- Automate Domino workflows
- Integrate Domino with external systems
- Query Domino programmatically

## Overview

Domino provides two main programmatic interfaces:
- **python-domino**: Python SDK for common operations
- **REST API**: Full HTTP API for all Domino features

## Installation

### python-domino
```bash
# Install from PyPI
pip install dominodatalab

# Or install with extras
pip install "dominodatalab[data]"
```

### In Domino Environment
Add to requirements.txt:
```
dominodatalab>=1.4.0
```

Or Dockerfile:
```dockerfile
RUN pip install dominodatalab
```

## Authentication

Canonical guide: https://docs.domino.ai/cloud/reference/api/domino-api-authentication

**Do not use API keys** (`X-Domino-Api-Key`, `DOMINO_USER_API_KEY`, `api_key=`). Use PAT or service account tokens only when calling from **outside** a run.

### In-run (workspace, job, app backend)

Domino injects `DOMINO_USER_HOST` / `DOMINO_API_HOST` (same base; prefer `DOMINO_USER_HOST`) and, when JWT credential propagation is enabled, `DOMINO_API_PROXY` (typically `http://localhost:8899`).

| Pattern | When | Code |
|---------|------|------|
| **API proxy (preferred)** | `DOMINO_API_PROXY` is set (Domino **5.4.0+** in runs with JWT credential propagation configured) | Call `{DOMINO_API_PROXY}{path}` with **no** `Authorization` header. The JWT sidecar adds the **starting user** access JWT on the forwarded request. |
| **Access token + platform host** | Older deployments, or you intentionally call `DOMINO_USER_HOST` / `DOMINO_API_HOST` instead of the proxy URL | Fetch a short-lived JWT, then Bearer on the platform base. |

**API proxy (preferred on 5.4.0+):**

```python
import os
import requests

base_url = os.environ["DOMINO_API_PROXY"].rstrip("/")
headers = {}

response = requests.get(f"{base_url}/v4/users/self")
```

```bash
curl "$DOMINO_API_PROXY/v4/users/self"
```

The proxy is not guaranteed on every deployment or run type. If `DOMINO_API_PROXY` is missing, use the access-token pattern or PAT from outside the cluster.

**Access token + `DOMINO_USER_HOST` (legacy-friendly in-run):** use the [In-run setup block](#in-run-setup-block-for-examples-in-this-skill) below; it covers both proxy and access-token paths.

**Before Domino 5.4.0:** JWT file propagation (`DOMINO_TOKEN_FILE`) was used before the API proxy; legacy behavior may still exist if admins enable `EnableLegacyJwtTooling`. Prefer migrating to the proxy pattern on supported versions.

### Outside a run (laptop, CI, cron outside Domino)

Your code is **not** executing inside a Domino workspace, job, or app container. Domino does **not** inject `DOMINO_API_PROXY`, `DOMINO_USER_HOST`, or an access-token sidecar. You must supply both:

1. **Base URL** — the deployment URL users open in the browser (HTTPS), for example `https://yourcompany.engineering.domino.tech`. Not `http://127.0.0.1:8763` and not values copied from an in-run environment.
2. **Credential** — `Authorization: Bearer` with a token you store securely (secret manager, CI variable, not committed to git):
   - **Personal Access Token (PAT)** when the automation acts as you. Create under Account settings or `POST /api/pat/v1/tokens` while already authenticated.
   - **Service account token** when a pipeline or integration runs without a human user. An admin provisions the service account and token.

```python
import requests

deployment_url = "https://yourcompany.engineering.domino.tech"
pat = "..."  # from your secret store; never hardcode in shared repos

response = requests.get(
    f"{deployment_url.rstrip('/')}/v4/users/self",
    headers={"Authorization": f"Bearer {pat}"},
)
```

See https://docs.domino.ai/cloud/reference/api/domino-api-authentication .

### In-run setup block (for examples in this skill)

Use inside a workspace, job, or app only:

```python
import os
import requests

if os.environ.get("DOMINO_API_PROXY"):
    base_url = os.environ["DOMINO_API_PROXY"].rstrip("/")
    headers = {}
else:
    base_url = (os.environ.get("DOMINO_USER_HOST") or os.environ.get("DOMINO_API_HOST") or "").rstrip("/")
    token = requests.get("http://localhost:8899/access-token").text.strip()
    headers = {"Authorization": f"Bearer {token}"}
```

### python-domino inside Domino

```python
from domino import Domino

domino = Domino("owner/project-name")
```

Configure the SDK with host + Bearer token per the product auth page. Never pass `api_key=`.

## Common Operations

### Projects

```python
from domino import Domino

domino = Domino()

# Create project
project = domino.project_create(
    project_name="my-new-project",
    owner_name="username"
)

# Get project info
info = domino.project_info()
print(f"Project: {info['name']}")
print(f"ID: {info['id']}")
```

### Jobs (Runs)

```python
# Start a job
run = domino.runs_start(
    command="python train.py --epochs 100",
    hardware_tier_name="medium",
    environment_id="env-id"
)
print(f"Run ID: {run['runId']}")

# Start job with different commit
run = domino.runs_start(
    command="python train.py",
    commit_id="abc123"
)

# Check status
status = domino.runs_status(run['runId'])
print(f"Status: {status['status']}")

# Wait for completion
domino.runs_wait(run['runId'])

# Get logs
logs = domino.runs_get_logs(run['runId'])
print(logs)

# Stop a run
domino.runs_stop(run['runId'])
```

### Workspaces

```python
# Start workspace
workspace = domino.workspace_start(
    hardware_tier_name="medium",
    environment_id="env-id",
    workspace_type="JupyterLab"
)
print(f"Workspace ID: {workspace['workspaceId']}")

# Stop workspace
domino.workspace_stop(workspace['workspaceId'])
```

### Files

```python
# Upload file
domino.files_upload(
    path="local/file.csv",
    dest_path="/mnt/code/data/"
)

# Download file
domino.files_download(
    path="/mnt/code/results/output.csv",
    dest_path="local/output.csv"
)

# List files
files = domino.files_list("/mnt/code/")
for f in files:
    print(f['path'])
```

### Datasets

```python
# Create dataset
dataset = domino.datasets_create(
    name="training-data",
    description="Training dataset"
)

# List datasets
datasets = domino.datasets_list()

# Create snapshot
snapshot = domino.datasets_snapshot(
    dataset_name="training-data",
    tag="v1.0"
)
```

### Environments

```python
# List environments
environments = domino.environments_list()
for env in environments:
    print(f"{env['name']}: {env['id']}")

# Get environment details
env = domino.environment_get("env-id")
```

### Model APIs

```python
# Publish model
model = domino.model_publish(
    file="model.py",
    function="predict",
    environment_id="env-id",
    name="my-classifier",
    description="Classification model"
)
print(f"Model ID: {model['id']}")

# List models
models = domino.models_list()

# Get model info
model_info = domino.model_get("model-id")
```

## REST API

Prefer `/api/...` when swagger documents that path for your operation. Use `/v4/...` when that is what your cluster swagger shows (many project settings and scheduled-job flows).

Use the [Authentication](#authentication) setup (`base_url`, `headers`) for examples below.

```python
response = requests.get(f"{base_url}/api/projects/beta/projects", headers=headers or None)
projects = response.json()
```

### Common Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v4/projects` | GET | List projects |
| `/v4/projects/{id}/runs` | POST | Start a run |
| `/v4/projects/{id}/runs/{runId}` | GET | Get run status |
| `/v4/projects/{id}/files` | GET | List files |
| `/v4/gateway/runs/{runId}/logs` | GET | Get run logs |
| `/v4/models` | GET | List models |
| `/v4/models/{id}/latest/model` | POST | Call model |

## Domino Data API

Separate SDK for data access:

```python
from domino_data.data_sources import DataSourceClient

# Initialize client
client = DataSourceClient()

# List data sources
sources = client.list_data_sources()

# Query data source
df = client.get_datasource("my-datasource").query(
    "SELECT * FROM customers WHERE region = 'US'"
)
```

## Automation Examples

### CI/CD Integration
```python
# trigger_training.py - Call from CI/CD pipeline
from domino import Domino
import sys

domino = Domino("team/ml-project")

# Start training job
run = domino.runs_start(
    command="python train.py",
    hardware_tier_name="gpu-large"
)

# Wait for completion
result = domino.runs_wait(run['runId'])

if result['status'] != 'Succeeded':
    print(f"Training failed: {result['status']}")
    sys.exit(1)

print("Training completed successfully!")
```

### Batch Job Scheduler
```python
# Run multiple experiments
from domino import Domino
import itertools

domino = Domino("team/experiments")

# Parameter grid
params = {
    "learning_rate": [0.01, 0.001, 0.0001],
    "batch_size": [32, 64, 128]
}

# Generate combinations
combinations = list(itertools.product(*params.values()))
param_names = list(params.keys())

# Submit all experiments
runs = []
for combo in combinations:
    param_str = " ".join(
        f"--{name}={value}"
        for name, value in zip(param_names, combo)
    )
    run = domino.runs_start(
        command=f"python experiment.py {param_str}",
        hardware_tier_name="gpu-small"
    )
    runs.append(run['runId'])
    print(f"Started run {run['runId']} with {param_str}")

# Wait for all to complete
for run_id in runs:
    result = domino.runs_wait(run_id)
    print(f"Run {run_id}: {result['status']}")
```

### Model Deployment Pipeline
```python
from domino import Domino

domino = Domino("team/model-deployment")

# 1. Train model
train_run = domino.runs_start(command="python train.py")
domino.runs_wait(train_run['runId'])

# 2. Evaluate model
eval_run = domino.runs_start(command="python evaluate.py")
domino.runs_wait(eval_run['runId'])

# 3. Deploy if evaluation passes
# (Check evaluation results first)
model = domino.model_publish(
    file="serve.py",
    function="predict",
    name="production-model"
)

print(f"Model deployed: {model['id']}")
```

## Error Handling

```python
from domino import Domino
from domino.exceptions import DominoException

try:
    domino = Domino("team/project")
    run = domino.runs_start(command="python train.py")
except DominoException as e:
    print(f"Domino error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

### 1. Follow [Authentication](#authentication)
Proxy without a header when `DOMINO_API_PROXY` is set; otherwise access-token + platform host; PAT/SA only outside a run.

### 2. Handle Rate Limits
```python
import time
from domino.exceptions import DominoException

def api_call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except DominoException as e:
            if "rate limit" in str(e).lower():
                time.sleep(2 ** attempt)
            else:
                raise
    raise Exception("Max retries exceeded")
```

### 3. Log API Calls
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_run(command):
    logger.info(f"Starting run: {command}")
    run = domino.runs_start(command=command)
    logger.info(f"Run ID: {run['runId']}")
    return run
```

## Detailed API Reference

For comprehensive REST API documentation, see these specialized guides:

| Guide | Description |
|-------|-------------|
| [API-PROJECTS.md](API-PROJECTS.md) | Projects, collaborators, Git repos, goals |
| [API-JOBS.md](API-JOBS.md) | Jobs, scheduled jobs, logs, tags |
| [API-DATASETS.md](API-DATASETS.md) | Datasets, snapshots, tags, grants |
| [API-MODELS.md](API-MODELS.md) | Model APIs, deployments, registry |
| [API-ENVIRONMENTS.md](API-ENVIRONMENTS.md) | Environments, revisions, Dockerfile |
| [API-APPS.md](API-APPS.md) | Apps, versions, instances, logs |
| [API-ADMIN.md](API-ADMIN.md) | Users, orgs, hardware tiers, data sources |
| [API-REFERENCE.md](API-REFERENCE.md) | Complete endpoint reference |

## Documentation Reference

Before writing or verifying any API call, use cluster swagger for paths and field names. Use https://docs.domino.ai for workflow context.

**OpenAPI JSON in-run:** `curl "$DOMINO_API_PROXY/assets/public-api.json"`

**Product docs:**
- [Domino API authentication](https://docs.domino.ai/cloud/reference/api/domino-api-authentication)
- [API discovery for agents](https://docs.domino.ai/llms.txt)
- [python-domino Library](https://docs.domino.ai/cloud/reference/python-sdk/python-wrapper-for-domino-api)
- [GitHub Repository](https://github.com/dominodatalab/python-domino)
