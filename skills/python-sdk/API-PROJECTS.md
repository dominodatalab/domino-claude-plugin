# Domino Projects API

## Overview
The Projects API allows you to create, manage, and configure Domino projects programmatically.

## Authentication
```python
import requests

headers = {"X-Domino-Api-Key": "YOUR_API_KEY"}
base_url = "https://your-domino.com"
```

---

## Endpoints

### List Projects
```
GET /api/projects/beta/projects
```

Get projects visible to the authenticated user.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `offset` | int | Pagination offset (default: 0) |
| `limit` | int | Results per page (default: 10) |
| `name` | string | Filter by project name |
| `ownerId` | string | Filter by owner ID |

**Example:**
```python
response = requests.get(
    f"{base_url}/api/projects/beta/projects",
    headers=headers,
    params={"limit": 20, "name": "ml-project"}
)
projects = response.json()
```

**Response:**
```json
{
  "data": [
    {
      "id": "project-123",
      "name": "ml-project",
      "description": "Machine learning project",
      "ownerId": "user-456",
      "visibility": "Private",
      "createdAt": "2024-01-15T10:00:00Z"
    }
  ],
  "offset": 0,
  "limit": 20,
  "totalCount": 1
}
```

---

### Create Project
```
POST /api/projects/beta/projects
```

Create a new project.

**Request Body:**
```json
{
  "name": "my-new-project",
  "description": "Project description",
  "visibility": "Private",
  "ownerId": "user-id"
}
```

**Example:**
```python
response = requests.post(
    f"{base_url}/api/projects/beta/projects",
    headers=headers,
    json={
        "name": "fraud-detection",
        "description": "Fraud detection model",
        "visibility": "Private"
    }
)
project = response.json()
print(f"Created project: {project['id']}")
```

---

### Get Project by ID
```
GET /api/projects/v1/projects/{projectId}
```

**Example:**
```python
project_id = "project-123"
response = requests.get(
    f"{base_url}/api/projects/v1/projects/{project_id}",
    headers=headers
)
project = response.json()
```

---

### Archive Project
```
DELETE /api/projects/beta/projects/{projectId}
```

Archives a project (soft delete).

**Example:**
```python
project_id = "project-123"
response = requests.delete(
    f"{base_url}/api/projects/beta/projects/{project_id}",
    headers=headers
)
```

---

### Copy Project
```
POST /api/projects/v1/projects/{projectId}/copy-project
```

Create a copy of an existing project.

**Request Body:**
```json
{
  "name": "copied-project",
  "description": "Copy of original project"
}
```

---

### Update Project Status
```
PUT /api/projects/v1/projects/{projectId}/status
```

Update project status (active, complete, etc.).

---

## Collaborators

### Add Collaborator
```
POST /api/projects/v1/projects/{projectId}/collaborators
```

**Request Body:**
```json
{
  "userId": "user-id",
  "role": "Contributor"
}
```

**Roles:**
- `Owner`
- `Admin`
- `Contributor`
- `LauncherUser`
- `ResultsConsumer`

**Example:**
```python
response = requests.post(
    f"{base_url}/api/projects/v1/projects/{project_id}/collaborators",
    headers=headers,
    json={
        "userId": "user-789",
        "role": "Contributor"
    }
)
```

### Remove Collaborator
```
DELETE /api/projects/v1/projects/{projectId}/collaborators/{collaboratorId}
```

---

## Git Repositories

### List Repositories
```
GET /api/projects/v1/projects/{projectId}/repositories
```

Get all imported Git repositories in a project.

### Add Repository
```
POST /api/projects/v1/projects/{projectId}/repositories
```

**Request Body:**
```json
{
  "uri": "https://github.com/org/repo.git",
  "ref": "main",
  "credentialId": "cred-id"
}
```

### Remove Repository
```
DELETE /api/projects/v1/projects/{projectId}/repositories/{repositoryId}
```

---

## Project Goals

### List Goals
```
GET /api/projects/v1/projects/{projectId}/goals
```

### Add Goal
```
POST /api/projects/v1/projects/{projectId}/goals
```

**Request Body:**
```json
{
  "title": "Achieve 95% accuracy",
  "description": "Model should reach 95% test accuracy"
}
```

### Update Goal
```
PATCH /api/projects/v1/projects/{projectId}/goals/{goalId}
```

**Request Body:**
```json
{
  "status": "Complete"
}
```

### Delete Goal
```
DELETE /api/projects/v1/projects/{projectId}/goals/{goalId}
```

---

## Shared Datasets

### List Shared Datasets
```
GET /api/projects/v1/projects/{projectId}/shared-datasets
```

Get datasets shared with this project.

### Link Dataset
```
POST /api/projects/v1/projects/{projectId}/shared-datasets
```

**Request Body:**
```json
{
  "datasetId": "dataset-id"
}
```

### Unlink Dataset
```
DELETE /api/projects/v1/projects/{projectId}/shared-datasets/{datasetId}
```

---

## Project Files

### Get File Content
```
GET /api/projects/v1/projects/{projectId}/files/{commitId}/{path}/content
```

Returns the contents of a file at a specific commit.

**Example:**
```python
response = requests.get(
    f"{base_url}/api/projects/v1/projects/{project_id}/files/HEAD/train.py/content",
    headers=headers
)
file_content = response.text
```

---

## Result Settings

### Get Result Settings
```
GET /api/projects/beta/projects/{projectId}/results-settings
```

### Update Result Settings
```
PUT /api/projects/beta/projects/{projectId}/results-settings
```

---

## Python SDK Examples

```python
from domino import Domino

# Initialize client
domino = Domino("owner/project-name")

# Get project info
info = domino.project_info()
print(f"Project: {info['name']}")
print(f"ID: {info['id']}")

# Create project (v4 API)
domino = Domino()
project = domino.project_create(
    project_name="new-project",
    owner_name="username"
)
```
