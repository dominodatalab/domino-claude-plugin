# Domino REST API Reference

Complete reference for Domino Platform REST API endpoints.

## Authentication

Full detail: [SKILL.md](SKILL.md#authentication) and https://docs.domino.ai/cloud/reference/api/domino-api-authentication

**In-run, preferred (5.4.0+ with JWT credential propagation):**

```bash
curl "$DOMINO_API_PROXY/v4/users/self"
```

**In-run, when proxy unset (access-token + platform host):**

```python
import os
import requests

base_url = (os.environ.get("DOMINO_USER_HOST") or os.environ.get("DOMINO_API_HOST") or "").rstrip("/")
token = requests.get("http://localhost:8899/access-token").text.strip()
headers = {"Authorization": f"Bearer {token}"}
```

**Combined setup for examples in this file:**

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

**Outside a run:** not in a Domino container — use the deployment HTTPS URL and Bearer PAT or service account token (see [SKILL.md](SKILL.md#outside-a-run-laptop-ci-cron-outside-domino)).

## Base URL

In-run: `DOMINO_API_PROXY` for platform `/v4/…` and `/api/…` routes. OpenAPI: `$DOMINO_API_PROXY/assets/public-api.json`.

---

## Projects API

### List Projects
```
GET /api/projects/beta/projects
```
Get projects visible to user.

**Query Parameters:**
- `offset` (int): Pagination offset
- `limit` (int): Number of results
- `name` (string): Filter by name
- `ownerId` (string): Filter by owner

**Response:** Array of project objects

### Create Project
```
POST /api/projects/beta/projects
```
Create a new project.

**Request Body:**
```json
{
  "name": "my-project",
  "description": "Project description",
  "visibility": "Private",
  "ownerId": "user-id"
}
```

### Get Project
```
GET /api/projects/v1/projects/{projectId}
```

### Archive Project
```
DELETE /api/projects/beta/projects/{projectId}
```

### Copy Project
```
POST /api/projects/v1/projects/{projectId}/copy-project
```

### Manage Collaborators
```
POST /api/projects/v1/projects/{projectId}/collaborators
DELETE /api/projects/v1/projects/{projectId}/collaborators/{collaboratorId}
```

### Git Repositories
```
GET /api/projects/v1/projects/{projectId}/repositories
POST /api/projects/v1/projects/{projectId}/repositories
DELETE /api/projects/v1/projects/{projectId}/repositories/{repositoryId}
```

### Project Goals
```
GET /api/projects/v1/projects/{projectId}/goals
POST /api/projects/v1/projects/{projectId}/goals
PATCH /api/projects/v1/projects/{projectId}/goals/{goalId}
DELETE /api/projects/v1/projects/{projectId}/goals/{goalId}
```

### Shared Datasets
```
GET /api/projects/v1/projects/{projectId}/shared-datasets
POST /api/projects/v1/projects/{projectId}/shared-datasets
DELETE /api/projects/v1/projects/{projectId}/shared-datasets/{datasetId}
```

---

## Jobs API

### List Jobs
```
GET /api/jobs/beta/jobs
```
**Query Parameters:**
- `projectId` (string): Required - Filter by project
- `offset` (int): Pagination offset
- `limit` (int): Number of results

### Get Job Details
```
GET /api/jobs/beta/jobs/{jobId}
```

### Get Job Logs
```
GET /api/jobs/beta/jobs/{jobId}/logs
```

### Start Job
```
POST /api/jobs/v1/jobs
```
**Request Body:**
```json
{
  "projectId": "project-id",
  "commandToRun": "python train.py --epochs 100",
  "hardwareTierId": "small",
  "environmentId": "env-id",
  "commitId": "optional-commit-hash"
}
```

### Job Tags
```
POST /api/jobs/v1/jobs/{jobId}/tags
DELETE /api/jobs/v1/jobs/{jobId}/tags/{tagId}
```

### Job Goals
```
GET /api/jobs/v1/goals
POST /api/jobs/v1/goals
DELETE /api/jobs/v1/goals/{goalId}
```

---

## Workspaces API

### Create Workspace Session
```
POST /api/projects/v1/projects/{projectId}/workspaces/{workspaceId}/sessions
```
**Request Body:**
```json
{
  "hardwareTierId": "medium",
  "environmentId": "env-id",
  "workspaceType": "JupyterLab"
}
```

---

## Datasets API

### List Datasets
```
GET /api/datasetrw/v2/datasets
```
**Query Parameters:**
- `projectId` (string): Filter by project
- `offset` (int): Pagination offset
- `limit` (int): Number of results

### Create Dataset
```
POST /api/datasetrw/v1/datasets
```
**Request Body:**
```json
{
  "name": "training-data",
  "description": "Training dataset",
  "projectId": "project-id"
}
```

### Get Dataset
```
GET /api/datasetrw/v1/datasets/{datasetId}
```

### Update Dataset
```
PATCH /api/datasetrw/v1/datasets/{datasetId}
```

### Delete Dataset
```
DELETE /api/datasetrw/v1/datasets/{datasetId}
```

### Dataset Snapshots
```
GET /api/datasetrw/v1/datasets/{datasetId}/snapshots
POST /api/datasetrw/v1/datasets/{datasetId}/snapshots
GET /api/datasetrw/v1/snapshots/{snapshotId}
```

### Dataset Tags
```
POST /api/datasetrw/v1/datasets/{datasetId}/tags
DELETE /api/datasetrw/v1/datasets/{datasetId}/tags/{tagName}
```

### Dataset Grants (Permissions)
```
GET /api/datasetrw/v1/datasets/{datasetId}/grants
POST /api/datasetrw/v1/datasets/{datasetId}/grants
DELETE /api/datasetrw/v1/datasets/{datasetId}/grants
```

---

## Environments API

### List Environments
```
GET /api/environments/beta/environments
```

### Create Environment
```
POST /api/environments/beta/environments
```
**Request Body:**
```json
{
  "name": "my-environment",
  "description": "Custom environment",
  "baseEnvironmentId": "base-env-id"
}
```

### Get Environment
```
GET /api/environments/v1/environments/{environmentId}
```

### Archive Environment
```
DELETE /api/environments/v1/environments/{environmentId}
```

### Environment Revisions
```
POST /api/environments/beta/environments/{environmentId}/revisions
PATCH /api/environments/beta/environments/{environmentId}/revisions/{revisionId}
```

---

## Model APIs

### List Model APIs
```
GET /api/modelServing/v1/modelApis
```

### Create Model API
```
POST /api/modelServing/v1/modelApis
```
**Request Body:**
```json
{
  "projectId": "project-id",
  "name": "my-model-api",
  "description": "Prediction API",
  "modelFile": "model.py",
  "modelFunction": "predict",
  "environmentId": "env-id"
}
```

### Get Model API
```
GET /api/modelServing/v1/modelApis/{modelApiId}
```

### Update Model API
```
PUT /api/modelServing/v1/modelApis/{modelApiId}
```

### Delete Model API
```
DELETE /api/modelServing/v1/modelApis/{modelApiId}
```

### Model API Versions
```
GET /api/modelServing/v1/modelApis/{modelApiId}/versions
POST /api/modelServing/v1/modelApis/{modelApiId}/versions
GET /api/modelServing/v1/modelApis/{modelApiId}/versions/{versionId}
```

### Model API Logs
```
GET /api/modelServing/v1/modelApis/{modelApiId}/versions/{versionId}/buildLogs
GET /api/modelServing/v1/modelApis/{modelApiId}/versions/{versionId}/instanceLogs
```

---

## Model Deployments API

### List Deployments
```
GET /api/modelServing/v1/modelDeployments
```

### Create Deployment
```
POST /api/modelServing/v1/modelDeployments
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

### Start/Stop Deployment
```
POST /api/modelServing/v1/modelDeployments/{deploymentId}/start
POST /api/modelServing/v1/modelDeployments/{deploymentId}/stop
```

### Deployment Logs
```
GET /api/modelServing/v1/modelDeployments/{deploymentId}/logs/{logSuffix}
```

### Deployment Credentials
```
GET /api/modelServing/v1/modelDeployments/{deploymentId}/credentials
```

---

## Registered Models API

### List Registered Models
```
GET /api/registeredmodels/v2
```

### Register Model
```
POST /api/registeredmodels/v2
```
**Request Body:**
```json
{
  "name": "my-model",
  "description": "Classification model",
  "source": {
    "type": "experiment",
    "experimentId": "exp-id",
    "runId": "run-id"
  }
}
```

### Get Model
```
GET /api/registeredmodels/v1/{modelName}
```

### Update Model
```
PATCH /api/registeredmodels/v1/{modelName}
```

### Model Versions
```
GET /api/registeredmodels/v1/{modelName}/versions
POST /api/registeredmodels/v1/{modelName}/versions
GET /api/registeredmodels/v1/{modelName}/versions/{version}
```

---

## Apps API

### List Apps
```
GET /api/apps/beta/apps
```
**Query Parameters:**
- `projectId` (string): Filter by project
- `status` (string): Filter by status
- `offset` (int): Pagination offset
- `limit` (int): Number of results

### Create App
```
POST /api/apps/beta/apps
```
**Request Body:**
```json
{
  "projectId": "project-id",
  "name": "my-app",
  "description": "Dashboard app",
  "hardwareTierId": "small",
  "environmentId": "env-id"
}
```

### Get App
```
GET /api/apps/beta/apps/{appId}
```

### Update App
```
PATCH /api/apps/beta/apps/{appId}
```

### Delete App
```
DELETE /api/apps/beta/apps/{appId}
```

### App Versions
```
GET /api/apps/beta/apps/{appId}/versions
POST /api/apps/beta/apps/{appId}/versions
GET /api/apps/beta/apps/{appId}/versions/{versionId}
PATCH /api/apps/beta/apps/{appId}/versions/{versionId}
```

### App Instances
```
GET /api/apps/beta/apps/{appId}/versions/{versionId}/instances
GET /api/apps/beta/apps/{appId}/versions/{versionId}/instances/{instanceId}
DELETE /api/apps/beta/apps/{appId}/versions/{versionId}/instances/{instanceId}
GET /api/apps/beta/apps/{appId}/versions/{versionId}/instances/{instanceId}/logs
```

### App Thumbnail
```
GET /api/apps/beta/apps/{appId}/thumbnail
POST /api/apps/beta/apps/{appId}/thumbnail
DELETE /api/apps/beta/apps/{appId}/thumbnail
```

---

## Hardware Tiers API

### List Hardware Tiers
```
GET /api/hardwaretiers/v1/hardwaretiers
```

### Create Hardware Tier
```
POST /api/hardwaretiers/v1/hardwaretiers
```

### Get Hardware Tier
```
GET /api/hardwaretiers/v1/hardwaretiers/{hardwareTierId}
```

### Update Hardware Tier
```
PUT /api/hardwaretiers/v1/hardwaretiers
```

### Archive Hardware Tier
```
DELETE /api/hardwaretiers/v1/hardwaretiers/{hardwareTierId}
```

---

## Data Sources API

### List Data Sources
```
GET /api/datasource/v1/datasources
```

### Create Data Source
```
POST /api/datasource/v1/datasources
```

### Get Data Source
```
GET /api/datasource/v1/datasources/{dataSourceId}
```

### Update Data Source
```
PATCH /api/datasource/v1/datasources/{dataSourceId}
```

### Delete Data Source
```
DELETE /api/datasource/v1/datasources/{dataSourceId}
```

### Data Source Audit
```
GET /api/datasource/v1/audit
```

---

## AI Gateway API

### List Endpoints
```
GET /api/aigateway/v1/endpoints
```

### Create Endpoint
```
POST /api/aigateway/v1/endpoints
```
**Request Body:**
```json
{
  "name": "openai-gpt4",
  "provider": "openai",
  "model": "gpt-4",
  "providerApiKey": "sk-..."
}
```

### Get Endpoint
```
GET /api/aigateway/v1/endpoints/{endpointName}
```

### Update Endpoint
```
PATCH /api/aigateway/v1/endpoints/{endpointName}
```

### Delete Endpoint
```
DELETE /api/aigateway/v1/endpoints/{endpointName}
```

### Endpoint Permissions
```
GET /api/aigateway/v1/endpoints/{endpointName}/permissions
PATCH /api/aigateway/v1/endpoints/{endpointName}/permissions
```

### AI Gateway Audit
```
GET /api/aigateway/v1/audit
```

---

## Users API

### Get Current User
```
GET /api/users/v1/self
```

### List Users
```
GET /api/users/v1/users
```

### User Git Credentials
```
GET /api/users/beta/credentials/{userId}
PUT /api/users/v1/user/{userId}/tokenCredentials/{credentialId}
```

---

## Organizations API

### List Organizations
```
GET /api/organizations/v1/organizations
```

### Create Organization
```
POST /api/organizations/v1/organizations
```

### Get Organization
```
GET /api/organizations/v1/organizations/{organizationId}
```

### Manage Members
```
PUT /api/organizations/v1/organizations/{organizationId}/user
DELETE /api/organizations/v1/organizations/{organizationId}/user
```

---

## Service Accounts API

### List Service Accounts
```
GET /api/serviceAccounts/v1/serviceAccounts
```

### Create Service Account
```
POST /api/serviceAccounts/v1/serviceAccounts
```

### Manage Tokens
```
GET /api/serviceAccounts/v1/serviceAccounts/{serviceAccountId}/tokens
POST /api/serviceAccounts/v1/serviceAccounts/{serviceAccountId}/tokens
```

---

## Cost API

### Cost Allocation
```
GET /api/cost/v1/allocation
GET /api/cost/v1/allocation/summary
```
**Query Parameters:**
- `startTime` (string): ISO 8601 timestamp
- `endTime` (string): ISO 8601 timestamp
- `aggregateBy` (string): user, project, organization

### Asset Costs
```
GET /api/cost/v1/asset
```

### Billing Tags
```
GET /api/cost/v1/billingtags
POST /api/cost/v1/billingtags
```

### Billing Settings
```
GET /api/cost/v1/billingtagSettings
PUT /api/cost/v1/billingtagSettings
GET /api/cost/v1/billingtagSettings/mode
PUT /api/cost/v1/billingtagSettings/mode
```

---

## Project Files API

### Get File Content
```
GET /api/projects/v1/projects/{projectId}/files/{commitId}/{path}/content
```

---

## Deployment Targets API (Admin)

### List Deployment Target Types
```
GET /api/admin/v1/deploymentTargetTypes
GET /api/admin/v1/deploymentTargetTypes/{typeId}
```

### Deployment Targets
```
GET /api/admin/v1/deploymentTargets
POST /api/admin/v1/deploymentTargets
GET /api/admin/v1/deploymentTargets/{targetId}
PATCH /api/admin/v1/deploymentTargets/{targetId}
DELETE /api/admin/v1/deploymentTargets/{targetId}
```

### Resource Configurations
```
GET /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations
POST /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations
GET /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations/{configId}
PATCH /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations/{configId}
DELETE /api/admin/v1/deploymentTargets/{targetId}/resourceConfigurations/{configId}
```

---

## Audit Events API

### Get Audit Events
```
GET /api/audittrail/v1/auditevents
```
**Query Parameters:**
- `startTime` (string): Filter start
- `endTime` (string): Filter end
- `eventType` (string): Filter by type (use `event` parameter name per swagger)

---

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async work started; see Async responses below) |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 500 | Internal Server Error |

## Error response body

Many platform routes return a structured error envelope (Domino API Standard):

```json
{
  "message": "Human-readable summary",
  "errors": [
    {
      "code": "MachineReadableCode",
      "message": "Detail",
      "details": {}
    }
  ]
}
```

Prefer branching on `errors[].code` when present. A bare 500 with no structured body may be a backend bug or scale failure; do not assume retry will help.

## Async responses

Standard pattern: `202 Accepted` plus a `Location` header for poll URL. Domino job start often returns `200`/`201` with a job or run id in the JSON body instead. Read the response body for an id before looking for `Location`.

Long-running operations (policy compute, some deployment stops) need polling a status field; do not treat HTTP 200 alone as completion.

## Deprecation headers

Check `Deprecation` and `Sunset` response headers on routes you automate. Confirm paths and fields against cluster swagger; product docs may lag the deployment you are on.

## Pagination

Most list endpoints expose `offset`, `limit`, and `totalCount` with a `data` array (or an envelope alias such as `modelProducts`).

Gotchas agents hit in production:

| Issue | Where | Mitigation |
|-------|-------|------------|
| Hard cap near 100 rows | Dataset list v2, some project lists | Page with offset; re-filter client-side if server ignores filters |
| `totalCount` unreliable | Some list endpoints with broken offset | Stop when a page returns fewer than `limit` rows |
| Server ignores query filters | Dataset v2 `projectIdsToInclude` | Filter client-side after fetch |
| Mixed envelope keys | `data` vs domain-specific keys | Normalize with a small list extractor |

```json
{
  "offset": 0,
  "limit": 10,
  "totalCount": 100,
  "data": [...]
}
```

## Path conventions

| Prefix | When to use |
|--------|-------------|
| `/api/...` | Newer versioned routes (projects beta/v1, jobs v1, users v1, etc.) when swagger lists them for your workflow |
| `/v4/...` | Older or project-scoped routes (settings, scheduled jobs, git attach) still used in automation |

Field names are **not** interchangeable across routes. Example: `POST /api/jobs/v1/jobs` uses `runCommand`; `POST /v4/projects/{projectId}/scheduledjobs` uses `command`; `POST /v4/jobs/{projectId}/resolveJobDefaults` uses `commandToRun`. Confirm in swagger for the exact path you call.

## Documentation Reference

Before writing or verifying any API call, use cluster swagger for paths and field names. Use https://docs.domino.ai for workflow context.

**OpenAPI JSON in-run:** `curl "$DOMINO_API_PROXY/assets/public-api.json"`

**Product docs:**
- [Domino API authentication](https://docs.domino.ai/cloud/reference/api/domino-api-authentication)
- [API discovery](https://docs.domino.ai/llms.txt)
