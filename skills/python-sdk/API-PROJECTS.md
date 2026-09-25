# Domino Projects API

## Overview
The Projects API allows you to create, manage, and configure Domino projects programmatically.

## Authentication

https://docs.domino.ai/cloud/reference/api/domino-api-authentication

See [SKILL.md](SKILL.md#authentication). Do not use API keys.

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

Project routes use both `/api/projects/...` and `/v4/projects/...` (settings, git attach, notification preferences). Confirm paths in cluster swagger.

---

## Collaborator and settings permissions

| Route | Typical permission | Who can call |
|-------|-------------------|--------------|
| `GET /v4/projects/{projectId}/collaborators` (optional `?getUsers=true`) | Project membership | Any project member; least-privilege way to list people on the project |
| `GET /v4/projects/{projectId}/projectSettingsCollaborators` | `ManageCollaborators` | Project owner / admin only |
| `GET /v4/projects/{projectId}/settings` | Read project settings | Any project member; use for defaults (e.g. hardware tier) without admin collaborators route |
| `PATCH /v4/projects/{projectId}/notificationPreference` | `ManageCollaborators` + change settings | Project admin; not available to regular contributors |

If `projectSettingsCollaborators` returns 403, try `GET .../collaborators?getUsers=true` or `GET .../settings` depending on whether you need admin collaborator editing vs read-only defaults.

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

## Project settings (prefetch defaults)

Scheduled jobs and some automation require an explicit hardware tier even when the UI would use the project default. Prefetch defaults before create:

```
GET /v4/projects/{projectId}/settings
```

Readable by any project member. Use the response to fill `hardwareTierIdentifier` / tier fields on `POST /v4/projects/{projectId}/scheduledjobs`, or call `POST /v4/jobs/{projectId}/resolveJobDefaults` where your cluster documents it.

---

## Git Repositories

Two paths attach a git repo to a project; they are aliases of the same operation. Prefer the catalog path.

### List Repositories
```
GET /api/projects/v1/projects/{projectId}/repositories
```

Get all imported Git repositories in a project.

### Add Repository (preferred)
```
POST /api/projects/v1/projects/{projectId}/repositories
```

Body fields (confirm in swagger):
```json
{
  "uri": "https://github.com/org/repo.git",
  "ref": "main",
  "credentialId": "cred-id"
}
```

### Add Repository (alternate path)
```
POST /v4/projects/{projectId}/gitRepositories
```

Same operation on the older project-scoped path; useful when your automation already targets `/v4/projects/...`.

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

## Run notification preferences (admin)

Update how run notifications are delivered for a collaborator. Requires project admin (`ManageCollaborators` / change project settings). Regular members should use read-only `GET /v4/projects/{projectId}/settings` instead of guessing this route.

```
PATCH /v4/projects/{projectId}/notificationPreference
```

A 403 usually means the caller is not project admin; list roles via collaborators routes above before retrying.

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
