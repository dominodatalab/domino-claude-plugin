# Domino Jobs API

## Overview
The Jobs API allows you to start, monitor, and manage batch job executions in Domino.

## Authentication
```python
import requests

headers = {"X-Domino-Api-Key": "YOUR_API_KEY"}
base_url = "https://your-domino.com"
```

---

## Endpoints

### List Jobs
```
GET /api/jobs/beta/jobs
```

Get jobs for a project.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `projectId` | string | **Required** - Filter by project |
| `offset` | int | Pagination offset |
| `limit` | int | Results per page |
| `status` | string | Filter by status |

**Status Values:**
- `Pending`
- `Running`
- `Succeeded`
- `Failed`
- `Stopped`

**Example:**
```python
response = requests.get(
    f"{base_url}/api/jobs/beta/jobs",
    headers=headers,
    params={
        "projectId": "project-123",
        "status": "Running",
        "limit": 50
    }
)
jobs = response.json()
```

**Response:**
```json
{
  "data": [
    {
      "id": "job-456",
      "projectId": "project-123",
      "status": "Running",
      "command": "python train.py",
      "startedAt": "2024-01-15T10:00:00Z",
      "hardwareTierId": "medium",
      "environmentId": "env-789"
    }
  ],
  "offset": 0,
  "limit": 50,
  "totalCount": 1
}
```

---

### Get Job Details
```
GET /api/jobs/beta/jobs/{jobId}
```

Get detailed information about a specific job.

**Example:**
```python
job_id = "job-456"
response = requests.get(
    f"{base_url}/api/jobs/beta/jobs/{job_id}",
    headers=headers
)
job = response.json()

print(f"Status: {job['status']}")
print(f"Started: {job['startedAt']}")
print(f"Command: {job['command']}")
```

**Response:**
```json
{
  "id": "job-456",
  "projectId": "project-123",
  "status": "Succeeded",
  "command": "python train.py --epochs 100",
  "hardwareTierId": "gpu-small",
  "environmentId": "env-789",
  "startedAt": "2024-01-15T10:00:00Z",
  "endedAt": "2024-01-15T12:30:00Z",
  "commitId": "abc123def456",
  "outputCommitId": "def456abc789"
}
```

---

### Get Job Logs
```
GET /api/jobs/beta/jobs/{jobId}/logs
```

Retrieve execution logs for a job.

**Example:**
```python
job_id = "job-456"
response = requests.get(
    f"{base_url}/api/jobs/beta/jobs/{job_id}/logs",
    headers=headers
)
logs = response.text
print(logs)
```

---

### Start Job
```
POST /api/jobs/v1/jobs
```

Start a new job execution.

**Request Body:**
```json
{
  "projectId": "project-123",
  "commandToRun": "python train.py --epochs 100",
  "hardwareTierId": "gpu-small",
  "environmentId": "env-789",
  "commitId": "abc123",
  "title": "Training Run",
  "isDirectHardwareTierId": false
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `projectId` | string | Yes | Project to run in |
| `commandToRun` | string | Yes | Command to execute |
| `hardwareTierId` | string | Yes | Hardware tier ID or name |
| `environmentId` | string | No | Environment ID |
| `commitId` | string | No | Git commit to use |
| `title` | string | No | Job title |

**Example:**
```python
response = requests.post(
    f"{base_url}/api/jobs/v1/jobs",
    headers=headers,
    json={
        "projectId": "project-123",
        "commandToRun": "python train.py --epochs 100 --lr 0.001",
        "hardwareTierId": "gpu-small",
        "environmentId": "env-789",
        "title": "Hyperparameter Experiment"
    }
)
job = response.json()
print(f"Started job: {job['id']}")
```

**Response:**
```json
{
  "id": "job-789",
  "status": "Pending",
  "projectId": "project-123",
  "command": "python train.py --epochs 100 --lr 0.001"
}
```

---

### Stop Job
To stop a running job, use the python-domino library:

```python
from domino import Domino

domino = Domino("owner/project")
domino.runs_stop(run_id="job-789")
```

---

## Job Tags

### Add Tag to Job
```
POST /api/jobs/v1/jobs/{jobId}/tags
```

**Request Body:**
```json
{
  "name": "production"
}
```

**Example:**
```python
response = requests.post(
    f"{base_url}/api/jobs/v1/jobs/{job_id}/tags",
    headers=headers,
    json={"name": "best-model"}
)
```

### Remove Tag from Job
```
DELETE /api/jobs/v1/jobs/{jobId}/tags/{tagId}
```

---

## Job Goals

### List Linked Goals
```
GET /api/jobs/v1/goals
```

Get goals linked to jobs.

### Link Goal to Job
```
POST /api/jobs/v1/goals
```

**Request Body:**
```json
{
  "jobId": "job-456",
  "goalId": "goal-123"
}
```

### Unlink Goal
```
DELETE /api/jobs/v1/goals/{goalId}
```

---

## Python SDK Examples

### Start and Monitor Job
```python
from domino import Domino

domino = Domino("owner/project-name")

# Start a job
run = domino.runs_start(
    command="python train.py --epochs 100",
    hardware_tier_name="gpu-small",
    environment_id="env-789"
)
print(f"Started run: {run['runId']}")

# Check status
status = domino.runs_status(run['runId'])
print(f"Status: {status['status']}")

# Wait for completion
result = domino.runs_wait(run['runId'])
print(f"Final status: {result['status']}")

# Get logs
logs = domino.runs_get_logs(run['runId'])
print(logs)
```

### Run Multiple Jobs
```python
from domino import Domino

domino = Domino("owner/project-name")

# Parameter sweep
learning_rates = [0.01, 0.001, 0.0001]
jobs = []

for lr in learning_rates:
    run = domino.runs_start(
        command=f"python train.py --lr {lr}",
        hardware_tier_name="gpu-small"
    )
    jobs.append(run['runId'])
    print(f"Started job for lr={lr}: {run['runId']}")

# Wait for all jobs
for job_id in jobs:
    result = domino.runs_wait(job_id)
    print(f"Job {job_id}: {result['status']}")
```

### Start Job with Specific Commit
```python
run = domino.runs_start(
    command="python train.py",
    hardware_tier_name="medium",
    commit_id="abc123def456"  # Use specific code version
)
```

---

## Polling for Job Completion

```python
import time

def wait_for_job(job_id, timeout=3600, poll_interval=30):
    """Wait for job to complete with timeout."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(
            f"{base_url}/api/jobs/beta/jobs/{job_id}",
            headers=headers
        )
        job = response.json()
        status = job['status']

        if status in ['Succeeded', 'Failed', 'Stopped']:
            return job

        print(f"Job {job_id}: {status}")
        time.sleep(poll_interval)

    raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")

# Usage
job = wait_for_job("job-456")
print(f"Job completed: {job['status']}")
```
